"""
Flight Search Tool - Direct browser automation for flight searches
"""
import os
from datetime import datetime
from typing import Optional, Dict, Any

from common.browser_wrapper import BrowserWrapper
from common.models.flight_models import FlightSearchResults
from common.models.orchestrator_models import TravelOrchestratorResponse, ResponseType, ResponseStatus, create_tool_progress


def search_flights_direct(origin: str, destination: str, departure_date: str, 
                         return_date: Optional[str] = None, passengers: int = 1) -> TravelOrchestratorResponse:
    """
    Search for flights using direct browser automation
    
    Args:
        origin: Origin airport code or city (e.g., 'JFK', 'New York')
        destination: Destination airport code or city (e.g., 'LAX', 'Los Angeles') 
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date for round-trip (optional)
        passengers: Number of passengers (1-9)
        
    Returns:
        TravelOrchestratorResponse with flight search results
    """
    start_time = datetime.now()
    print(f"✈️  Direct flight search: {origin} → {destination} on {departure_date}")
    if return_date:
        print(f"   Return: {return_date} | Passengers: {passengers}")
    
    # Create progress tracking
    flight_progress = create_tool_progress(
        "search_flights", 
        {"origin": origin, "destination": destination}, 
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
        if return_date:
            instructions = [
                f"find flights from {origin} to {destination} departing on {departure_date} and returning on {return_date}.",
                "once you have identified an outbound flight, select it to view the return flight options and then choose the best return flight."
            ]
        else:
            instructions = [
                "Ensure you change the trip type from Round trip to One way.",
                f"find a one-way flight from {origin} to {destination} departing on {departure_date}",
            ]
        
        extraction_instruction = f"""Extract the details of the SELECTED flights that were just clicked on.

You should now see the details of the selected flight(s). Extract the following information:

For OUTBOUND flight (the one that was clicked and selected):
- airline: The airline name (e.g., 'Delta', 'United', 'American')
- departure_time: Departure time (e.g., '10:30 AM')
- arrival_time: Arrival time (e.g., '6:45 PM') 
- departure_airport: '{origin}'
- arrival_airport: '{destination}'
- price: Price as number (without $ symbol)
- duration: Flight duration string (e.g., '7h 15m')
- stops: Number of stops as integer (0, 1, 2, etc.)
- stop_details: Stop airport info or null if nonstop
- booking_class: 'Economy'

{"For RETURN flight (if round-trip and return flight was selected):" if return_date else ""}
{"- Same format as outbound but for the return direction" if return_date else ""}

For SEARCH_METADATA (required dictionary with search parameters and context):
- origin: "{origin}"
- destination: "{destination}"
- departure_date: "{departure_date}"
- return_date: "{return_date if return_date else 'null'}"
- passenger_count: {passengers}
- trip_type: "{'round_trip' if return_date else 'one_way'}"

For RECOMMENDATION (required string):
Provide personalized advice about the selected flight(s) based on price competitiveness, convenience factors (direct vs stops), timing, and overall value. Include booking recommendations.

Return the complete flight search results in the proper schema format with all required fields populated."""
        
        # Execute browser automation
        result = browser_wrapper.execute_instructions(
            starting_page="https://www.google.com/travel/flights",
            instructions=instructions,
            extraction_instruction=extraction_instruction,
            result_schema=FlightSearchResults.model_json_schema()
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if result and not result.get("error"):
            # Create FlightSearchResults from browser automation result
            flight_results = FlightSearchResults(**result)
            
            # Update progress to completed
            flight_progress.status = "completed"
            flight_progress.result_preview = f"Found flight options from {origin} to {destination}"
            
            # Generate recommendation
            recommendation = f"Found the best flight option for your {origin} to {destination} trip. "
            if flight_results.best_outbound_flight:
                recommendation += f"Outbound flight with {flight_results.best_outbound_flight.airline} departing at ${flight_results.best_outbound_flight.price}. "
            if flight_results.best_return_flight:
                recommendation += f"Return flight also selected for complete round-trip booking. "
            recommendation += "These flights were selected based on the best combination of price and convenience."
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.FLIGHTS,
                response_status=ResponseStatus.COMPLETE_SUCCESS,
                message=recommendation,
                overall_progress_message="Flight search completed successfully",
                is_final_response=True,
                tool_progress=[flight_progress],
                flight_results=flight_results,
                processing_time_seconds=processing_time
            )
        else:
            # Browser automation failed or returned no results
            flight_progress.status = "failed"
            flight_progress.error_message = result.get("error", "No flight results found")
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.TOOL_ERROR,
                message="I searched for flights but couldn't find any results. Please check your travel details and try again.",
                overall_progress_message="Flight search completed with no results",
                is_final_response=True,
                tool_progress=[flight_progress],
                success=False,
                processing_time_seconds=processing_time,
                error_message=result.get("error", "No results found")
            )
            
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"❌ Direct flight search failed: {str(e)}")
        
        # Update progress to failed
        flight_progress.status = "failed"
        flight_progress.error_message = str(e)
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.CONVERSATION,
            response_status=ResponseStatus.TOOL_ERROR,
            message="I encountered an error while searching for flights. Please try again or provide more specific details.",
            overall_progress_message="Flight search failed due to an error",
            is_final_response=True,
            tool_progress=[flight_progress],
            success=False,
            error_message=str(e),
            processing_time_seconds=processing_time
        )
