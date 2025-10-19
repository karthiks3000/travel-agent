"""
Airbnb Search Tool - Browser automation for Airbnb vacation rental searches
"""
import os
from datetime import datetime
from typing import List

from agents.browser_wrapper import BrowserWrapper
from agents.models.accommodation_models import PropertyResult, PlatformSearchResults
from agents.models.orchestrator_models import TravelOrchestratorResponse, ResponseType, ResponseStatus, create_tool_progress


def search_airbnb_direct(location: str, check_in: str, check_out: str, 
                        guests: int = 2) -> TravelOrchestratorResponse:
    """
    Search for Airbnb vacation rentals using browser automation
    
    Args:
        location: Destination city or location (e.g., 'Paris, France', 'Manhattan, NYC')
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of guests (1-30)
        
    Returns:
        TravelOrchestratorResponse with Airbnb search results
    """
    start_time = datetime.now()
    print(f"🏠 Airbnb search: {location} | {check_in} to {check_out} | {guests} guests")
    
    # Create progress tracking
    airbnb_progress = create_tool_progress(
        "search_airbnb", 
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
        
        # Prepare browser automation instructions
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
        
        # Execute browser automation
        result = browser_wrapper.execute_instructions(
            starting_page="https://www.airbnb.com",
            instructions=instructions,
            extraction_instruction=extraction_instruction,
            result_schema=PlatformSearchResults.model_json_schema()
        )
        
        # Check if search was successful
        if not result.get("search_successful", False):
            airbnb_progress.status = "failed"
            airbnb_progress.error_message = result.get("search_metadata", {}).get("error", "Search failed")
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.TOOL_ERROR,
                message=f"I couldn't find any Airbnb properties in {location}. Please check the location and try again.",
                overall_progress_message="Airbnb search completed with no results",
                is_final_response=True,
                tool_progress=[airbnb_progress],
                success=False,
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                error_message="No properties found",
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
        
        # Parse properties from result
        properties = result.get("properties", [])
        
        if not properties:
            airbnb_progress.status = "failed"
            airbnb_progress.error_message = "No properties found in search results"
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.TOOL_ERROR,
                message=f"I searched Airbnb but couldn't find any properties in {location} for {check_in} to {check_out}. Try different dates or a nearby location.",
                overall_progress_message="Airbnb search completed with no results",
                is_final_response=True,
                tool_progress=[airbnb_progress],
                success=False,
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                error_message="No properties found",
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
        
        # Convert to PropertyResult objects (limit to 10)
        airbnb_results: List[PropertyResult] = []
        for prop_dict in properties[:10]:
            if isinstance(prop_dict, dict):
                airbnb_results.append(PropertyResult(**prop_dict))
            else:
                airbnb_results.append(prop_dict)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Update progress to completed
        airbnb_progress.status = "completed"
        airbnb_progress.result_preview = f"Found {len(airbnb_results)} Airbnb properties in {location}"
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.ACCOMMODATIONS,
            response_status=ResponseStatus.COMPLETE_SUCCESS,
            message=f"Found {len(airbnb_results)} Airbnb vacation rentals in {location} for {check_in} to {check_out}.",
            overall_progress_message="Airbnb search completed successfully",
            is_final_response=True,
            tool_progress=[airbnb_progress],
            accommodation_results=airbnb_results,
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
            
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"❌ Airbnb search failed: {str(e)}")
        
        # Update progress to failed
        airbnb_progress.status = "failed"
        airbnb_progress.error_message = str(e)
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.CONVERSATION,
            response_status=ResponseStatus.TOOL_ERROR,
            message="I encountered an error while searching Airbnb. Please try again or provide more specific details.",
            overall_progress_message="Airbnb search failed due to an error",
            is_final_response=True,
            tool_progress=[airbnb_progress],
            success=False,
            error_message=str(e),
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
