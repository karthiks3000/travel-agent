"""
Accommodation Search Tool - Direct browser automation for accommodation searches
"""
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

from common.browser_wrapper import BrowserWrapper
from common.models.accommodation_models import AccommodationAgentResponse, PropertyResult, PlatformSearchResults
from common.models.orchestrator_models import TravelOrchestratorResponse, ResponseType, ResponseStatus, create_tool_progress


def _search_airbnb(browser_wrapper: BrowserWrapper, location: str, check_in: str, 
                  check_out: str, guests: int) -> Dict[str, Any]:
    """Search Airbnb using browser automation"""
    print(f"🏠 Searching Airbnb: {location} | {check_in} to {check_out} | {guests} guests")
    
    try:
        instructions = [
            f"find the best accommodations in {location} checking in {check_in} and checking out {check_out} for {guests} guests"
        ]
        
        extraction_instruction = f"""Extract Airbnb property listings from the search results page.

You should now see the Airbnb search results for accommodations. Extract the following information for each visible property listing (up to 10 properties):

For each property:
- platform: 'airbnb'
- title: Property title/name as displayed
- price_per_night: Nightly price as number (without $ symbol)
- total_price: Total price for the stay if shown, or null
- rating: Property rating (e.g., 4.85) or null if not shown
- review_count: Number of reviews as integer, or null
- property_type: Type like 'Entire apartment', 'Private room', etc.
- host_name: Host's name or null if not displayed
- location: Neighborhood/area description
- amenities: Array of amenities shown (e.g., ['WiFi', 'Kitchen', 'Superhost']) or null
- url: Property URL if available, or null
- image_url: Main property image URL if available, or null
- guests_capacity: Number of guests it accommodates, or null
- bedrooms: Number of bedrooms, or null
- bathrooms: Number of bathrooms, or null

Additional search information:
- search_successful: true if properties found, false if no results
- total_found: Total number of properties found (if displayed)
- search_metadata: Include location, check_in, check_out, guests from search

Return the property listings in the proper schema format. Use null (not empty strings) for any missing or unavailable fields."""
        
        result = browser_wrapper.execute_instructions(
            starting_page="https://www.airbnb.com",
            instructions=instructions,
            extraction_instruction=extraction_instruction,
            result_schema=PlatformSearchResults.model_json_schema()
        )
        
        return result
        
    except Exception as e:
        print(f"❌ Airbnb search failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "platform": "airbnb",
            "properties": [],
            "search_successful": False,
            "search_metadata": {"error": str(e)}
        }


def _search_booking_com(browser_wrapper: BrowserWrapper, location: str, check_in: str, 
                       check_out: str, guests: int, rooms: int = 1) -> Dict[str, Any]:
    """Search Booking.com using browser automation"""
    print(f"🏨 Searching Booking.com: {location} | {check_in} to {check_out} | {guests} guests, {rooms} rooms")
    
    try:
        instructions = [
            f"find the best hotels and accommodations in {location} from {check_in} to {check_out} for {guests} guests in {rooms} rooms"
        ]
        
        extraction_instruction = f"""Extract Booking.com property listings from the search results page.

You should now see the Booking.com search results for hotels and accommodations. Extract the following information for each visible property listing (up to 10 properties):

For each property:
- platform: 'booking_com'
- title: Hotel/property name as displayed
- price_per_night: Nightly price as number (without $ symbol)
- total_price: Total price for the stay if shown, or null
- rating: Property rating (e.g., 8.5) or null if not shown
- review_count: Number of reviews as integer, or null
- property_type: Type like 'Hotel', 'Apartment', 'Resort', etc.
- host_name: Hotel chain/brand name or null if not displayed
- location: District/area description
- amenities: Array of amenities shown (e.g., ['Free WiFi', 'Breakfast included', 'Pool']) or null
- url: Property URL if available, or null
- image_url: Main property image URL if available, or null
- guests_capacity: Number of guests it accommodates, or null
- bedrooms: Number of bedrooms, or null
- bathrooms: Number of bathrooms, or null

Additional search information:
- search_successful: true if properties found, false if no results
- total_found: Total number of properties found (if displayed)
- search_metadata: Include location, check_in, check_out, guests, rooms from search

Return the property listings in the proper schema format. Use null (not empty strings) for any missing or unavailable fields."""
        
        result = browser_wrapper.execute_instructions(
            starting_page="https://www.booking.com",
            instructions=instructions,
            extraction_instruction=extraction_instruction,
            result_schema=PlatformSearchResults.model_json_schema()
        )
        
        return result
        
    except Exception as e:
        print(f"❌ Booking.com search failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "platform": "booking_com",
            "properties": [],
            "search_successful": False,
            "search_metadata": {"error": str(e)}
        }


def _combine_and_sort_results(airbnb_results: Dict[str, Any], 
                             booking_results: Dict[str, Any],
                             sort_by: str = "value") -> List[PropertyResult]:
    """Combine and sort results from both platforms"""
    try:
        # Get properties from both platforms
        airbnb_properties = airbnb_results.get("properties", []) if airbnb_results.get("success", False) else []
        booking_properties = booking_results.get("properties", []) if booking_results.get("success", False) else []
        
        print(f"🔄 Combining results from Airbnb ({len(airbnb_properties)}) and Booking.com ({len(booking_properties)})")
        
        # Convert to PropertyResult objects
        all_properties = []
        
        for prop_dict in airbnb_properties:
            if isinstance(prop_dict, dict):
                all_properties.append(PropertyResult(**prop_dict))
            else:
                all_properties.append(prop_dict)
                
        for prop_dict in booking_properties:
            if isinstance(prop_dict, dict):
                all_properties.append(PropertyResult(**prop_dict))
            else:
                all_properties.append(prop_dict)
        
        # Sort by different criteria
        if sort_by == "price":
            sorted_properties = sorted(all_properties, key=lambda x: x.price_per_night or float('inf'))
        elif sort_by == "rating":
            sorted_properties = sorted(all_properties, 
                                     key=lambda x: x.rating if x.rating is not None else 0, 
                                     reverse=True)
        else:  # sort_by == "value" (default)
            def value_score(prop):
                if prop.rating is None or not prop.price_per_night or prop.price_per_night <= 0:
                    return 0
                return (prop.rating * 100) / prop.price_per_night
            
            sorted_properties = sorted(all_properties, key=value_score, reverse=True)
        
        # Return top 10 results
        return sorted_properties[:10]
        
    except Exception as e:
        print(f"❌ Combining results failed: {str(e)}")
        return []


def search_accommodations_direct(location: str, check_in: str, check_out: str, 
                               guests: int = 2, rooms: int = 1, 
                               platform_preference: str = "both") -> TravelOrchestratorResponse:
    """
    Search for accommodations using direct browser automation
    
    Args:
        location: Destination city or location (e.g., 'Paris, France', 'Manhattan, NYC')
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of guests (1-30)
        rooms: Number of rooms (1-8)
        platform_preference: "airbnb", "booking", or "both"
        
    Returns:
        TravelOrchestratorResponse with accommodation search results
    """
    start_time = datetime.now()
    print(f"🏨 Direct accommodation search: {location} | {check_in} to {check_out} | {guests} guests, {rooms} rooms")
    
    # Create progress tracking
    accommodation_progress = create_tool_progress(
        "search_accommodations", 
        {"destination": location}, 
        "active"
    )
    
    try:
        # Initialize browser wrapper - API key should be set by travel orchestrator
        nova_act_api_key = os.getenv('NOVA_ACT_API_KEY')
        
        if not nova_act_api_key:
            raise ValueError("Nova Act API key not found in environment. Travel orchestrator should set this.")
        
        use_agentcore = os.getenv('USE_AGENTCORE_BROWSER', 'true').lower() == 'true'
        region = os.getenv('AGENTCORE_REGION', 'us-east-1')
        
        browser_wrapper = BrowserWrapper(
            api_key=nova_act_api_key,
            use_agentcore_browser=use_agentcore,
            region=region
        )
        
        # Execute platform searches based on preference
        airbnb_results = {}
        booking_results = {}
        best_accommodations = []
        
        if platform_preference in ["airbnb", "both"]:
            airbnb_results = _search_airbnb(browser_wrapper, location, check_in, check_out, guests)
        
        if platform_preference in ["booking", "both"]:
            booking_results = _search_booking_com(browser_wrapper, location, check_in, check_out, guests, rooms)
        
        # Combine and sort results if both platforms were searched
        if platform_preference == "both" and airbnb_results and booking_results:
            best_accommodations = _combine_and_sort_results(airbnb_results, booking_results)
        elif platform_preference == "airbnb" and airbnb_results:
            # Convert Airbnb properties to PropertyResult objects
            properties = airbnb_results.get("properties", [])
            best_accommodations = [PropertyResult(**prop) if isinstance(prop, dict) else prop for prop in properties[:10]]
        elif platform_preference == "booking" and booking_results:
            # Convert Booking.com properties to PropertyResult objects
            properties = booking_results.get("properties", [])
            best_accommodations = [PropertyResult(**prop) if isinstance(prop, dict) else prop for prop in properties[:10]]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if best_accommodations:
            # Create AccommodationAgentResponse
            accommodation_results = AccommodationAgentResponse(
                best_accommodations=best_accommodations,
                search_metadata={
                    "platforms_searched": platform_preference,
                    "total_found": len(best_accommodations),
                    "airbnb_count": len(airbnb_results.get("properties", [])) if airbnb_results else 0,
                    "booking_count": len(booking_results.get("properties", [])) if booking_results else 0
                },
                recommendation=f"Found {len(best_accommodations)} excellent accommodation options in {location}. These properties were selected based on the best combination of value, ratings, and availability for your {check_in} to {check_out} stay."
            )
            
            # Update progress to completed
            accommodation_progress.status = "completed"
            accommodation_progress.result_preview = f"Found {len(best_accommodations)} accommodation options"
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.ACCOMMODATIONS,
                response_status=ResponseStatus.COMPLETE_SUCCESS,
                message=accommodation_results.recommendation,
                overall_progress_message="Accommodation search completed successfully",
                is_final_response=True,
                tool_progress=[accommodation_progress],
                accommodation_results=accommodation_results,
                processing_time_seconds=processing_time
            )
        else:
            # No results found
            accommodation_progress.status = "failed"
            accommodation_progress.error_message = "No accommodation results found"
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.TOOL_ERROR,
                message="I searched for accommodations but couldn't find any results. Please check your travel details and try again.",
                overall_progress_message="Accommodation search completed with no results",
                is_final_response=True,
                tool_progress=[accommodation_progress],
                success=False,
                processing_time_seconds=processing_time,
                error_message="No results found"
            )
            
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"❌ Direct accommodation search failed: {str(e)}")
        
        # Update progress to failed
        accommodation_progress.status = "failed"
        accommodation_progress.error_message = str(e)
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.CONVERSATION,
            response_status=ResponseStatus.TOOL_ERROR,
            message="I encountered an error while searching for accommodations. Please try again or provide more specific details.",
            overall_progress_message="Accommodation search failed due to an error",
            is_final_response=True,
            tool_progress=[accommodation_progress],
            success=False,
            error_message=str(e),
            processing_time_seconds=processing_time
        )
