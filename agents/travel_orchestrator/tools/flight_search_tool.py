"""
Flight Search Tool - Amadeus API integration for flight searches
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from amadeus import Client, ResponseError

from agents.models.flight_models import FlightResult
from agents.models.orchestrator_models import TravelOrchestratorResponse, ResponseType, ResponseStatus, create_tool_progress


def _format_time(iso_datetime: str) -> str:
    """
    Convert ISO datetime string to readable time format
    
    Args:
        iso_datetime: ISO format datetime string (e.g., '2024-11-01T10:30:00')
        
    Returns:
        Formatted time string (e.g., '10:30 AM')
    """
    try:
        dt = datetime.fromisoformat(iso_datetime.replace('Z', '+00:00'))
        return dt.strftime('%I:%M %p').lstrip('0')
    except Exception:
        return iso_datetime


def _get_stop_details(segments: List[Dict[str, Any]]) -> Optional[str]:
    """
    Extract stop airport information from flight segments
    
    Args:
        segments: List of flight segments
        
    Returns:
        Stop details string or None for direct flights
    """
    if len(segments) <= 1:
        return None
    
    # Get the intermediate airports (not first departure or last arrival)
    stops = []
    for i in range(len(segments) - 1):
        stop_airport = segments[i]['arrival']['iataCode']
        stops.append(stop_airport)
    
    return ', '.join(stops) if stops else None


def _parse_flight_segment_to_result(
    segments: List[Dict[str, Any]], 
    price: float,
    booking_class: str = "Economy"
) -> FlightResult:
    """
    Convert Amadeus flight segments to FlightResult model
    
    Args:
        segments: List of flight segments from Amadeus
        price: Total price for this flight
        booking_class: Booking class
        
    Returns:
        FlightResult object
    """
    first_segment = segments[0]
    last_segment = segments[-1]
    
    # Calculate total duration
    total_minutes = 0
    for segment in segments:
        duration = segment.get('duration', 'PT0M')
        # Parse duration to minutes
        hours = 0
        minutes = 0
        if 'H' in duration:
            hours = int(duration.split('PT')[1].split('H')[0])
        if 'M' in duration:
            minutes = int(duration.split('M')[0].split('H')[-1]) if 'H' in duration else int(duration.split('PT')[1].split('M')[0])
        total_minutes += (hours * 60 + minutes)
    
    total_duration = f"{total_minutes // 60}h {total_minutes % 60}m" if total_minutes % 60 > 0 else f"{total_minutes // 60}h"
    
    # Get airline - prefer operating carrier over marketing carrier
    carrier = first_segment.get('carrierCode', 'Unknown')
    if isinstance(carrier, dict):
        carrier = carrier.get('carrierCode', 'Unknown')
    
    return FlightResult(
        airline=carrier,
        departure_time=_format_time(first_segment['departure']['at']),
        arrival_time=_format_time(last_segment['arrival']['at']),
        departure_airport=first_segment['departure']['iataCode'],
        arrival_airport=last_segment['arrival']['iataCode'],
        price=price,
        duration=total_duration,
        stops=len(segments) - 1,
        stop_details=_get_stop_details(segments),
        booking_class=booking_class
    )


def _parse_all_flight_offers(flight_offers: List[Dict[str, Any]]) -> List[FlightResult]:
    """
    Parse all flight offers from Amadeus into FlightResult list (no filtering)
    
    Args:
        flight_offers: List of flight offers from Amadeus
        
    Returns:
        List of FlightResult objects
    """
    flight_results = []
    
    for offer in flight_offers:
        try:
            price = float(offer['price']['total'])
            
            # Get booking class from traveler pricings
            booking_class = "Economy"
            traveler_pricings = offer.get('travelerPricings', [])
            if traveler_pricings:
                fare_details = traveler_pricings[0].get('fareDetailsBySegment', [])
                if fare_details:
                    booking_class = fare_details[0].get('cabin', 'Economy').title()
            
            # Parse each itinerary (outbound and return if exists)
            for itinerary in offer.get('itineraries', []):
                segments = itinerary.get('segments', [])
                if segments:
                    flight = _parse_flight_segment_to_result(segments, price, booking_class)
                    flight_results.append(flight)
                    
        except Exception as e:
            print(f"Warning: Error parsing flight offer: {e}")
            continue
    
    return flight_results


def search_flights_direct(
    amadeus_client: Optional[Client],
    origin: str, 
    destination: str, 
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    travel_class: Optional[str] = None,
    non_stop: bool = False,
    max_price: Optional[int] = None,
    max_results: int = 250
) -> TravelOrchestratorResponse:
    """
    Search for flights using Amadeus Flight Offers Search API with comprehensive filtering
    
    Args:
        amadeus_client: Pre-initialized Amadeus client (from agent session)
        origin: Origin airport code (IATA, e.g., 'JFK', 'LAX')
        destination: Destination airport code (IATA, e.g., 'LHR', 'CDG')
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date for round-trip (optional, YYYY-MM-DD format)
        adults: Number of adult travelers (age 12+), default 1, max 9
        children: Number of child travelers (age 2-11), default 0
        infants: Number of infant travelers (under 2), default 0
        travel_class: Cabin class - "ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"
        non_stop: If True, only return direct flights with no stops
        max_price: Maximum price per traveler in USD (filters expensive options)
        max_results: Maximum number of flight offers to return (default 250)
        
    Returns:
        TravelOrchestratorResponse with all matching flight results
    """
    start_time = datetime.now()
    total_passengers = adults + children + infants
    print(f"✈️  Amadeus flight search: {origin} → {destination} on {departure_date}")
    if return_date:
        print(f"   Return: {return_date} | Passengers: {total_passengers} (Adults: {adults}, Children: {children}, Infants: {infants})")
    
    # Create progress tracking
    flight_progress = create_tool_progress(
        "search_flights", 
        {"origin": origin, "destination": destination}, 
        "active"
    )
    
    try:
        # Use provided Amadeus client (initialized once per session in agent __init__)
        if not amadeus_client:
            raise ValueError("Amadeus client not available - credentials may be missing")
        
        amadeus = amadeus_client
        
        # Prepare search parameters
        search_params = {
            'originLocationCode': origin.upper(),
            'destinationLocationCode': destination.upper(),
            'departureDate': departure_date,
            'adults': adults,
            'max': max_results,
            'currencyCode': 'USD'
        }
        
        # Add optional parameters
        if return_date:
            search_params['returnDate'] = return_date
        if children > 0:
            search_params['children'] = children
        if infants > 0:
            search_params['infants'] = infants
        if travel_class:
            search_params['travelClass'] = travel_class
        if non_stop:
            search_params['nonStop'] = True
        if max_price:
            search_params['maxPrice'] = max_price
        
        # Make API call
        print(f"🔍 Searching Amadeus API with params: {search_params}")
        response = amadeus.shopping.flight_offers_search.get(**search_params)
        
        # Parse response
        flight_offers = response.data
        
        if not flight_offers:
            flight_progress.status = "failed"
            flight_progress.error_message = "No flights found for the given route and dates"
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.TOOL_ERROR,
                message=f"I couldn't find any flights from {origin} to {destination} on {departure_date}. Please check the airport codes and dates.",
                overall_progress_message="No flights found",
                is_final_response=True,
                tool_progress=[flight_progress],
                success=False,
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                error_message="No flights found",
                next_expected_input_friendly=None,
                flight_results=None,
                accommodation_results=None,
                restaurant_results=None,
                attraction_results=None,
                itinerary=None,
                estimated_costs=None,
                recommendations=None,
                session_metadata=None
            )
        
        print(f"✅ Found {len(flight_offers)} flight offers from Amadeus")
        
        # Parse all flight offers (no filtering)
        flight_results = _parse_all_flight_offers(flight_offers)
        
        if not flight_results:
            raise ValueError("Could not parse flight data from response")
        
        
        # Update progress
        flight_progress.status = "completed"
        flight_progress.result_preview = f"Found {len(flight_results)} flight options from {origin} to {destination}"
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.FLIGHTS,
            response_status=ResponseStatus.COMPLETE_SUCCESS,
            message=flight_progress.result_preview,
            overall_progress_message="Flight search completed successfully",
            is_final_response=True,
            tool_progress=[flight_progress],
            flight_results=flight_results,
            processing_time_seconds=processing_time,
            success=True,
            error_message=None,
            next_expected_input_friendly=None,
            accommodation_results=None,
            restaurant_results=None,
            attraction_results=None,
            itinerary=None,
            estimated_costs=None,
            recommendations=None,
            session_metadata=None
        )
        
    except ResponseError as error:
        processing_time = (datetime.now() - start_time).total_seconds()
        error_message = f"Amadeus API error: {error}"
        print(f"❌ Amadeus API error: {error.response}")
        
        flight_progress.status = "failed"
        flight_progress.error_message = error_message
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.CONVERSATION,
            response_status=ResponseStatus.TOOL_ERROR,
            message="I encountered an error while searching for flights with the airline data provider. Please check your airport codes and try again.",
            overall_progress_message="Flight search failed",
            is_final_response=True,
            tool_progress=[flight_progress],
            success=False,
            error_message=error_message,
            processing_time_seconds=processing_time,
            next_expected_input_friendly=None,
            flight_results=None,
            accommodation_results=None,
            restaurant_results=None,
            attraction_results=None,
            itinerary=None,
            estimated_costs=None,
            recommendations=None,
            session_metadata=None
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        error_message = str(e)
        print(f"❌ Flight search failed: {error_message}")
        
        flight_progress.status = "failed"
        flight_progress.error_message = error_message
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.CONVERSATION,
            response_status=ResponseStatus.TOOL_ERROR,
            message="I encountered an error while searching for flights. Please try again or provide more specific details.",
            overall_progress_message="Flight search failed due to an error",
            is_final_response=True,
            tool_progress=[flight_progress],
            success=False,
            error_message=error_message,
            processing_time_seconds=processing_time,
            next_expected_input_friendly=None,
            flight_results=None,
            accommodation_results=None,
            restaurant_results=None,
            attraction_results=None,
            itinerary=None,
            estimated_costs=None,
            recommendations=None,
            session_metadata=None
        )
