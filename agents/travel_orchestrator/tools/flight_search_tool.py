"""
Flight Search Tool - Amadeus API integration for flight searches
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from amadeus import Client, ResponseError

from common.models.flight_models import FlightSearchResults, FlightResult
from common.models.orchestrator_models import TravelOrchestratorResponse, ResponseType, ResponseStatus, create_tool_progress


def _initialize_amadeus_client() -> Client:
    """
    Initialize Amadeus API client with credentials from environment
    
    Returns:
        Configured Amadeus Client
        
    Raises:
        ValueError: If credentials are missing
    """
    client_id = os.getenv('AMADEUS_CLIENT_ID')
    client_secret = os.getenv('AMADEUS_CLIENT_SECRET')
    hostname = os.getenv('AMADEUS_HOSTNAME', 'test')
    
    if not client_id or not client_secret:
        raise ValueError("Amadeus credentials not found. Please set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET environment variables.")
    
    return Client(
        client_id=client_id,
        client_secret=client_secret,
        hostname=hostname
    )


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


def _parse_duration(duration: str) -> str:
    """
    Convert ISO 8601 duration to readable format
    
    Args:
        duration: ISO 8601 duration string (e.g., 'PT7H15M')
        
    Returns:
        Readable duration string (e.g., '7h 15m')
    """
    try:
        # Remove 'PT' prefix
        duration = duration.replace('PT', '')
        
        hours = 0
        minutes = 0
        
        if 'H' in duration:
            hours_part, duration = duration.split('H')
            hours = int(hours_part)
        
        if 'M' in duration:
            minutes = int(duration.replace('M', ''))
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"
    except Exception:
        return duration


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
    carrier = first_segment.get('operating', first_segment.get('carrierCode', 'Unknown'))
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


def _calculate_flight_score(flight: FlightResult, prefer_daytime: bool = True) -> float:
    """
    Calculate a score for ranking flights (lower is better)
    
    Scoring factors:
    - Price (30% weight)
    - Number of stops (40% weight) 
    - Duration (20% weight)
    - Departure time preference (10% weight)
    
    Args:
        flight: FlightResult to score
        prefer_daytime: Whether to prefer daytime departures (8am-8pm)
        
    Returns:
        Flight score (lower is better)
    """
    score = 0.0
    
    # Price component (normalized, assuming max reasonable price of $2000)
    price_score = (flight.price / 2000.0) * 30
    score += price_score
    
    # Stops component (each stop adds significant score)
    stops_score = flight.stops * 15  # 0, 15, 30, 45...
    score += stops_score
    
    # Duration component (extract hours from duration string)
    try:
        duration_hours = 0
        if 'h' in flight.duration:
            duration_hours = int(flight.duration.split('h')[0].strip())
        # Assume max reasonable duration of 24 hours
        duration_score = (duration_hours / 24.0) * 20
        score += duration_score
    except Exception:
        pass
    
    # Departure time preference (daytime flights preferred)
    if prefer_daytime:
        try:
            dep_time = datetime.strptime(flight.departure_time, '%I:%M %p')
            hour = dep_time.hour
            # Score 0 for 8am-8pm, up to 10 for very early/late flights
            if 8 <= hour <= 20:
                time_score = 0
            else:
                # Distance from preferred range
                if hour < 8:
                    time_score = (8 - hour) * 1.25
                else:
                    time_score = (hour - 20) * 1.25
                time_score = min(time_score, 10)
            score += time_score
        except Exception:
            pass
    
    return score


def _select_best_flight(flight_offers: List[Dict[str, Any]], direction: str = "outbound") -> Optional[Tuple[FlightResult, float]]:
    """
    Select the best flight from available offers
    
    Args:
        flight_offers: List of flight offers from Amadeus
        direction: "outbound" or "return"
        
    Returns:
        Tuple of (FlightResult, score) or None if no flights available
    """
    if not flight_offers:
        return None
    
    best_flight = None
    best_score = float('inf')
    
    for offer in flight_offers:
        try:
            # Get the appropriate itinerary (0 for outbound, 1 for return if exists)
            itineraries = offer.get('itineraries', [])
            if not itineraries:
                continue
            
            itinerary_index = 0 if direction == "outbound" else (1 if len(itineraries) > 1 else 0)
            if itinerary_index >= len(itineraries):
                continue
                
            itinerary = itineraries[itinerary_index]
            segments = itinerary.get('segments', [])
            
            if not segments:
                continue
            
            # Get price
            price = float(offer['price']['total'])
            
            # Get booking class from traveler pricings
            booking_class = "Economy"
            traveler_pricings = offer.get('travelerPricings', [])
            if traveler_pricings:
                fare_details = traveler_pricings[0].get('fareDetailsBySegment', [])
                if fare_details:
                    booking_class = fare_details[0].get('cabin', 'Economy').title()
            
            # Parse to FlightResult
            flight = _parse_flight_segment_to_result(segments, price, booking_class)
            
            # Calculate score
            score = _calculate_flight_score(flight)
            
            # Keep track of best flight
            if score < best_score:
                best_score = score
                best_flight = flight
                
        except Exception as e:
            print(f"Warning: Error parsing flight offer: {e}")
            continue
    
    return (best_flight, best_score) if best_flight else None


def search_flights_direct(origin: str, destination: str, departure_date: str, 
                         return_date: Optional[str] = None, passengers: int = 1) -> TravelOrchestratorResponse:
    """
    Search for flights using Amadeus Flight Offers Search API
    
    Args:
        origin: Origin airport code (IATA, e.g., 'JFK', 'LAX')
        destination: Destination airport code (IATA, e.g., 'LHR', 'CDG')
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date for round-trip (optional, YYYY-MM-DD format)
        passengers: Number of passengers (1-9)
        
    Returns:
        TravelOrchestratorResponse with flight search results
    """
    start_time = datetime.now()
    print(f"✈️  Amadeus flight search: {origin} → {destination} on {departure_date}")
    if return_date:
        print(f"   Return: {return_date} | Passengers: {passengers}")
    
    # Create progress tracking
    flight_progress = create_tool_progress(
        "search_flights", 
        {"origin": origin, "destination": destination}, 
        "active"
    )
    
    try:
        # Initialize Amadeus client
        amadeus = _initialize_amadeus_client()
        
        # Prepare search parameters
        search_params = {
            'originLocationCode': origin.upper(),
            'destinationLocationCode': destination.upper(),
            'departureDate': departure_date,
            'adults': passengers,
            'max': 50,  # Get more results for better selection
            'currencyCode': 'USD'
        }
        
        # Add return date if round-trip
        if return_date:
            search_params['returnDate'] = return_date
        
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
        
        # Select best outbound flight
        outbound_result = _select_best_flight(flight_offers, "outbound")
        if not outbound_result:
            raise ValueError("Could not parse outbound flight data")
        
        best_outbound_flight, outbound_score = outbound_result
        
        # Select best return flight if round-trip
        best_return_flight = None
        if return_date:
            return_result = _select_best_flight(flight_offers, "return")
            if return_result:
                best_return_flight, return_score = return_result
        
        # Create flight list
        flight_list = [best_outbound_flight]
        if best_return_flight:
            flight_list.append(best_return_flight)
        
        # Create FlightSearchResults for legacy compatibility
        flight_search_results = FlightSearchResults(
            best_outbound_flight=best_outbound_flight,
            best_return_flight=best_return_flight,
            search_metadata={
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "passenger_count": passengers,
                "trip_type": "round_trip" if return_date else "one_way",
                "total_offers_found": len(flight_offers)
            },
            recommendation=_generate_recommendation(
                best_outbound_flight,
                best_return_flight,
                origin,
                destination,
                return_date is not None
            ),
            validation_error=None
        )
        
        # Update progress
        flight_progress.status = "completed"
        flight_progress.result_preview = f"Found flights from {origin} to {destination} starting at ${best_outbound_flight.price}"
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.FLIGHTS,
            response_status=ResponseStatus.COMPLETE_SUCCESS,
            message=flight_search_results.recommendation,
            overall_progress_message="Flight search completed successfully",
            is_final_response=True,
            tool_progress=[flight_progress],
            flight_results=flight_list,
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


def _generate_recommendation(
    outbound: FlightResult,
    return_flight: Optional[FlightResult],
    origin: str,
    destination: str,
    is_roundtrip: bool
) -> str:
    """
    Generate a personalized flight recommendation message
    
    Args:
        outbound: Outbound flight details
        return_flight: Return flight details (if applicable)
        origin: Origin airport code
        destination: Destination airport code
        is_roundtrip: Whether this is a round-trip search
        
    Returns:
        Recommendation text
    """
    recommendation = f"I found excellent flight options for your trip from {origin} to {destination}. "
    
    # Outbound flight details
    if outbound.stops == 0:
        recommendation += f"Your outbound flight is a direct {outbound.airline} flight "
    else:
        recommendation += f"Your outbound flight with {outbound.airline} has {outbound.stops} stop{'s' if outbound.stops > 1 else ''} "
    
    recommendation += f"departing at {outbound.departure_time}, arriving at {outbound.arrival_time} "
    recommendation += f"({outbound.duration}). "
    
    # Return flight details if applicable
    if return_flight:
        if return_flight.stops == 0:
            recommendation += f"Your return flight is also direct with {return_flight.airline}, "
        else:
            recommendation += f"Your return flight with {return_flight.airline} has {return_flight.stops} stop{'s' if return_flight.stops > 1 else ''}, "
        
        recommendation += f"departing at {return_flight.departure_time} and arriving at {return_flight.arrival_time} "
        recommendation += f"({return_flight.duration}). "
        
        total_price = outbound.price
        recommendation += f"The total price for this round-trip is ${total_price:.2f}. "
    else:
        recommendation += f"The price for this one-way flight is ${outbound.price:.2f}. "
    
    # Add booking advice
    if outbound.stops == 0:
        recommendation += "Direct flights offer the most convenience and save time. "
    
    recommendation += "I recommend booking soon as prices may change. These flights offer a great balance of price, convenience, and timing for your trip."
    
    return recommendation
