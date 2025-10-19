"""
Hotel Search Tool - Amadeus API integration for hotel searches
Two-step process: Hotel List API → Hotel Search API
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from amadeus import Client, ResponseError

from common.models.accommodation_models import PropertyResult
from common.models.orchestrator_models import TravelOrchestratorResponse, ResponseType, ResponseStatus, create_tool_progress


def _get_hotels_by_city(amadeus: Client, city_code: str, max_hotels: int = 20) -> List[str]:
    """
    Step 1: Get hotel IDs in a city using Hotel List API
    
    Args:
        amadeus: Amadeus client
        city_code: IATA city code (e.g., PAR, NYC, LON)
        max_hotels: Maximum number of hotels to return
        
    Returns:
        List of hotel IDs
    """
    try:
        print(f"🏨 Step 1: Getting hotel IDs for city code: {city_code}")
        
        # Call Hotel List API
        response = amadeus.reference_data.locations.hotels.by_city.get(
            cityCode=city_code
        )
        
        hotels = response.data
        
        if not hotels:
            print(f"⚠️  No hotels found for city code: {city_code}")
            return []
        
        # Extract hotel IDs (limit to max_hotels)
        hotel_ids = [hotel['hotelId'] for hotel in hotels[:max_hotels]]
        
        print(f"✅ Found {len(hotel_ids)} hotels in {city_code}")
        return hotel_ids
        
    except ResponseError as error:
        print(f"❌ Hotel List API error: {error}")
        raise
    except Exception as e:
        print(f"❌ Error getting hotels by city: {e}")
        raise


def _get_hotel_offers(amadeus: Client, hotel_ids: List[str], check_in: str, 
                     check_out: str, adults: int, room_quantity: int = 1) -> List[Dict[str, Any]]:
    """
    Step 2: Get hotel offers using Hotel Search API
    
    Args:
        amadeus: Amadeus client
        hotel_ids: List of hotel IDs to get offers for
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        adults: Number of adult guests
        room_quantity: Number of rooms
        
    Returns:
        List of hotel offer dictionaries
    """
    try:
        print(f"🔍 Step 2: Getting offers for {len(hotel_ids)} hotels")
        
        # Convert hotel IDs list to comma-separated string
        hotel_ids_str = ','.join(hotel_ids)
        
        # Call Hotel Search API
        response = amadeus.shopping.hotel_offers_search.get(
            hotelIds=hotel_ids_str,
            checkInDate=check_in,
            checkOutDate=check_out,
            adults=adults,
            roomQuantity=room_quantity,
            currency='USD'
        )
        
        offers = response.data
        
        if not offers:
            print(f"⚠️  No offers found for the given dates and criteria")
            return []
        
        print(f"✅ Found {len(offers)} hotel offers")
        return offers
        
    except ResponseError as error:
        print(f"❌ Hotel Search API error: {error}")
        raise
    except Exception as e:
        print(f"❌ Error getting hotel offers: {e}")
        raise


def _parse_hotel_offer_to_property(offer: Dict[str, Any]) -> Optional[PropertyResult]:
    """
    Convert Amadeus hotel offer to PropertyResult model
    
    Args:
        offer: Hotel offer dictionary from Amadeus
        
    Returns:
        PropertyResult object or None if parsing fails
    """
    try:
        # Extract hotel information
        hotel = offer.get('hotel', {})
        hotel_id = hotel.get('hotelId', '')
        hotel_name = hotel.get('name', 'Unknown Hotel')
        
        # Extract location information
        address = hotel.get('address', {})
        city_name = address.get('cityName', '')
        country_code = address.get('countryCode', '')
        location_str = f"{city_name}, {country_code}" if city_name and country_code else None
        
        # Extract first available offer
        offers_list = offer.get('offers', [])
        if not offers_list:
            return None
        
        first_offer = offers_list[0]
        
        # Extract pricing
        price_info = first_offer.get('price', {})
        total_price = float(price_info.get('total', 0))
        currency = price_info.get('currency', 'USD')
        
        # Calculate price per night
        room = first_offer.get('room', {})
        room_description = room.get('description', {}).get('text', '')
        
        # Extract room type and bed info
        room_type = room.get('typeEstimated', {}).get('category', 'Standard Room')
        beds = room.get('typeEstimated', {}).get('beds', 0)
        bed_type = room.get('typeEstimated', {}).get('bedType', '')
        
        # Combine room type with bed info
        if bed_type and beds:
            property_type = f"{room_type} - {beds} {bed_type}"
        else:
            property_type = room_type
        
        # Extract policies
        policies = first_offer.get('policies', {})
        cancellation_policy = policies.get('cancellation', {})
        is_cancellable = cancellation_policy.get('type') != 'FULL_STAY'
        
        # Build amenities list from room description
        amenities = []
        if 'wifi' in room_description.lower():
            amenities.append('WiFi')
        if 'breakfast' in room_description.lower():
            amenities.append('Breakfast')
        if 'parking' in room_description.lower():
            amenities.append('Parking')
        
        # Add cancellation info to amenities
        if is_cancellable:
            amenities.append('Free Cancellation')
        
        # Extract guest capacity
        guests_capacity = room.get('typeEstimated', {}).get('beds', 2)
        
        # Create PropertyResult
        return PropertyResult(
            platform='amadeus_hotel',
            title=hotel_name,
            price_per_night=None,  # Amadeus doesn't provide per-night, only total
            total_price=total_price,
            rating=None,  # Amadeus hotel offers don't include ratings
            review_count=None,
            property_type=property_type,
            host_name=hotel.get('chainCode', None),  # Use chain code as "host"
            amenities=amenities if amenities else None,
            location=location_str,
            url=None,  # Amadeus doesn't provide direct booking URLs
            image_url=None,  # Would need additional API call for media
            guests_capacity=guests_capacity,
            bedrooms=1,  # Typically 1 bedroom per hotel room
            bathrooms=1   # Typically 1 bathroom per hotel room
        )
        
    except Exception as e:
        print(f"❌ Error parsing hotel offer: {e}")
        return None


def search_hotels_amadeus(
    amadeus_client: Optional[Client],
    city_code: str,
    check_in: str,
    check_out: str, 
    guests: int = 2,
    rooms: int = 1,
    max_hotels: int = 20
) -> TravelOrchestratorResponse:
    """
    Search for hotels using Amadeus API (two-step process)
    
    Step 1: Get hotel IDs in the city (Hotel List API)
    Step 2: Get offers for those hotels (Hotel Search API)
    
    Args:
        amadeus_client: Pre-initialized Amadeus client (from agent session)
        city_code: IATA city code (e.g., 'PAR' for Paris, 'NYC' for New York, 'LON' for London)
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of adult guests (1-30)
        rooms: Number of rooms (1-8)
        max_hotels: Maximum number of hotels to search (default 20)
        
    Returns:
        TravelOrchestratorResponse with hotel search results
    """
    start_time = datetime.now()
    print(f"🏨 Amadeus hotel search: {city_code} | {check_in} to {check_out} | {guests} guests, {rooms} rooms")
    
    # Create progress tracking
    hotel_progress = create_tool_progress(
        "search_hotels", 
        {"city_code": city_code}, 
        "active"
    )
    
    try:
        # Use provided Amadeus client (initialized once per session in agent __init__)
        if not amadeus_client:
            raise ValueError("Amadeus client not available - credentials may be missing")
        
        amadeus = amadeus_client
        
        # Use city_code directly (uppercase for consistency)
        city_code = city_code.upper().strip()
        
        print(f"✅ Using city code: {city_code}")
        
        # Step 1: Get hotel IDs
        hotel_ids = _get_hotels_by_city(amadeus, city_code, max_hotels)
        
        if not hotel_ids:
            hotel_progress.status = "failed"
            hotel_progress.error_message = "No hotels found in this location"
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.TOOL_ERROR,
                message=f"I couldn't find any hotels with city code '{city_code}'. This location may not be available in our hotel database.",
                overall_progress_message="No hotels found",
                is_final_response=True,
                tool_progress=[hotel_progress],
                success=False,
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                error_message="No hotels found",
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
        
        # Step 2: Get offers for those hotels
        hotel_offers = _get_hotel_offers(amadeus, hotel_ids, check_in, check_out, guests, rooms)
        
        if not hotel_offers:
            hotel_progress.status = "failed"
            hotel_progress.error_message = "No available rooms for the specified dates"
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.TOOL_ERROR,
                message=f"I found hotels in {city_code}, but no rooms are available for {check_in} to {check_out}. Try different dates or check back later.",
                overall_progress_message="No available rooms",
                is_final_response=True,
                tool_progress=[hotel_progress],
                success=False,
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                error_message="No available rooms",
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
        
        # Parse hotel offers to PropertyResult objects
        hotel_results = []
        for offer in hotel_offers:
            property_result = _parse_hotel_offer_to_property(offer)
            if property_result:
                hotel_results.append(property_result)
        
        if not hotel_results:
            raise ValueError("Could not parse hotel data from response")
        
        # Update progress
        hotel_progress.status = "completed"
        hotel_progress.result_preview = f"Found {len(hotel_results)} hotel options in {city_code}"
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.ACCOMMODATIONS,
            response_status=ResponseStatus.COMPLETE_SUCCESS,
            message=f"Found {len(hotel_results)} hotels in {city_code} for {check_in} to {check_out}.",
            overall_progress_message="Hotel search completed successfully",
            is_final_response=True,
            tool_progress=[hotel_progress],
            accommodation_results=hotel_results,
            processing_time_seconds=processing_time,
            success=True,
            error_message=None,
            next_expected_input_friendly=None,
            flight_results=None,
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
        
        hotel_progress.status = "failed"
        hotel_progress.error_message = error_message
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.CONVERSATION,
            response_status=ResponseStatus.TOOL_ERROR,
            message="I encountered an error while searching for hotels with the hotel data provider. Please try again.",
            overall_progress_message="Hotel search failed",
            is_final_response=True,
            tool_progress=[hotel_progress],
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
        print(f"❌ Hotel search failed: {error_message}")
        
        hotel_progress.status = "failed"
        hotel_progress.error_message = error_message
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.CONVERSATION,
            response_status=ResponseStatus.TOOL_ERROR,
            message="I encountered an error while searching for hotels. Please try again or provide more specific details.",
            overall_progress_message="Hotel search failed due to an error",
            is_final_response=True,
            tool_progress=[hotel_progress],
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
