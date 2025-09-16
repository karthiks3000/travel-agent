"""
Flight Agent - Bedrock AgentCore implementation with Nova Act browser automation
"""
import os
import sys
import boto3
import json
from datetime import datetime, timedelta
from strands import Agent, tool
from typing import Optional, Dict, Any
from bedrock_agentcore import BedrockAgentCoreApp

from common.browser_wrapper import BrowserWrapper
from common.models.flight_models import FlightSearchResults, FlightResult
from common.models.base_models import ValidationError

# Module-level browser wrapper - initialized by FlightAgent
browser_wrapper = None


def get_parameter(name):
    """Get parameter from AWS Systems Manager Parameter Store"""
    try:
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(Name=name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Failed to retrieve parameter {name}: {str(e)}")
        return None


@tool
def validate_inputs(origin: str, destination: str, departure_date: str, 
                   return_date: Optional[str] = None, passengers: int = 1) -> Dict[str, Any]:
    """
    Validate flight search inputs
    
    Args:
        origin: Origin airport code or city (e.g., 'JFK', 'New York')
        destination: Destination airport code or city (e.g., 'LAX', 'Los Angeles') 
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date for round-trip (optional)
        passengers: Number of passengers (1-9)
        
    Returns:
        Dictionary with validation result: {"valid": bool, "error": str or None}
    """
    try:
        print("Validating inputs")
        # Get current date
        today = datetime.now().date()
        
        # Validate passengers
        if passengers < 1 or passengers > 9:
            return {"valid": False, "error": f"Invalid passenger count: {passengers}. Must be between 1-9."}
        
        # Validate origin and destination are different
        if origin.strip().lower() == destination.strip().lower():
            return {"valid": False, "error": "Origin and destination cannot be the same."}
        
        if origin.strip() == '' or destination.strip() == '':
            return {"valid": False, "error": "Origin and destination are both required"}
        
        # Parse and validate departure date
        try:
            if departure_date.lower() == "tomorrow":
                dep_date = today + timedelta(days=1)
            elif departure_date.lower() == "today":
                dep_date = today
            else:
                dep_date = datetime.strptime(departure_date, "%Y-%m-%d").date()
        except ValueError:
            return {"valid": False, "error": f"Invalid departure date format: {departure_date}. Use YYYY-MM-DD format."}
        
        # Check if departure date is in the past
        if dep_date < today:
            return {"valid": False, "error": f"Past date: {dep_date}. Departure date must be today or in the future."}
        
        # Parse and validate return date if provided
        if return_date:
            try:
                if return_date.lower() == "tomorrow":
                    ret_date = today + timedelta(days=1)
                elif return_date.lower() == "today":
                    ret_date = today
                else:
                    ret_date = datetime.strptime(return_date, "%Y-%m-%d").date()
            except ValueError:
                return {"valid": False, "error": f"Invalid return date format: {return_date}. Use YYYY-MM-DD format."}
            
            # Check if return date is in the past
            if ret_date < today:
                return {"valid": False, "error": f"Past date: {ret_date}. Return date must be today or in the future."}
            
            # Check if return date is after departure date
            if ret_date <= dep_date:
                return {"valid": False, "error": f"Return date ({ret_date}) must be after departure date ({dep_date})."}
        
        return {"valid": True, "error": None}
        
    except Exception as e:
        return {"valid": False, "error": f"Validation error: {str(e)}"}


@tool
def search_google_flights(origin: str, destination: str, departure_date: str, 
                         return_date: Optional[str] = None, passengers: int = 1) -> Dict[str, Any]:
    """
    Search Google Flights using Nova Act browser automation
    
    Args:
        origin: Origin airport code or city (e.g., 'JFK', 'New York')
        destination: Destination airport code or city (e.g., 'LAX', 'Los Angeles') 
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date for round-trip (optional)
        passengers: Number of passengers (1-9)
        
    Returns:
        Dictionary with flight search results
    """
    print(f"🔍 Searching flights: {origin} → {destination} on {departure_date}")
    if return_date:
        print(f"   Return: {return_date} | Passengers: {passengers}")
    
    try:
        if return_date:
            instructions = [
                f"find the best flights from {origin} to {destination} departing on {departure_date} and returning on {return_date}.",
                "once you have identified the best outbound flight, select it to view the return flight options and then choose the best return flight."
            ]
        else:
            instructions = [
                f"find the best one-way flight from {origin} to {destination} departing on {departure_date}",
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

Return the selected flight details in the proper schema format."""
        
        # Use module-level browser wrapper
        result = browser_wrapper.execute_instructions(
            starting_page="https://www.google.com/travel/flights",
            instructions=instructions,
            extraction_instruction=extraction_instruction,
            result_schema=FlightSearchResults.model_json_schema()
        )
        
        # Add recommendation field for agent to customize
        result_with_recommendation = {
            "success": True,
            "search_params": {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "passengers": passengers
            },
            **result,
            "recommendation": "Raw flight search results - agent should provide personalized booking advice"
        }
        
        return result_with_recommendation
        
    except Exception as e:
        print(f"❌ Flight search failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "search_params": {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "passengers": passengers
            },
            "best_outbound_flight": None,
            "best_return_flight": None,
            "search_metadata": {"error": str(e)},
            "recommendation": "Flight search failed. Please check your search parameters and try again."
        }


class FlightAgent(Agent):
    def __init__(self):
        global browser_wrapper
        
        # Get current date and time for system prompt
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        
        # Try environment variable first, then Parameter Store
        nova_act_api_key = os.getenv('NOVA_ACT_API_KEY') or \
                          get_parameter('/travel-agent/nova-act-api-key')
        
        if not nova_act_api_key:
            raise ValueError("Nova Act API key not found in environment or Parameter Store")
        
        # Initialize module-level browser wrapper with configuration
        use_agentcore = os.getenv('USE_AGENTCORE_BROWSER', 'true').lower() == 'true'
        region = os.getenv('AGENTCORE_REGION', 'us-east-1')
        
        browser_wrapper = BrowserWrapper(
            api_key=nova_act_api_key,
            use_agentcore_browser=use_agentcore,
            region=region
        )
        
        super().__init__(
            model="amazon.nova-pro-v1:0",
            tools=[validate_inputs, search_google_flights],
            system_prompt=f"""You are a flight search specialist that finds the BEST flights based on cost and convenience. Current date and time: {current_datetime}

CRITICAL: You MUST return ONLY valid JSON responses using the FlightSearchResults schema. Never return natural language text.

Your process:
1. Understand natural language flight requests 
2. Extract key details: origin, destination, dates, passenger count, preferences
3. ALWAYS call validate_inputs tool first with the extracted parameters
4. If validation fails (valid: false), return JSON error response with the validation error
5. Only if validation passes (valid: true), proceed to call search_google_flights
6. When search tool returns results, update the recommendation field with personalized advice
7. Return ONLY the updated JSON structure - no additional text or formatting

CRITICAL WORKFLOW:
1. Call validate_inputs(origin, destination, departure_date, return_date, passengers)
2. If validation result shows "valid": false, return the EXACT SAME JSON format as validate_inputs tool:
   {{"valid": false, "error": "[validation error message from tool]"}}
3. If validation result shows "valid": true, proceed with search_google_flights using the same parameters and return FlightSearchResults format

VALIDATION ERROR RESPONSE FORMAT:
When validation fails, return the exact same format as the validate_inputs tool:
{{"valid": false, "error": "specific error message"}}

Do NOT return FlightSearchResults format for validation errors - use the validation format above.

FLIGHT SELECTION BEHAVIOR:
- The tool automatically selects the BEST flights (not multiple options)
- One-way: Returns single best outbound flight
- Round-trip: Returns best outbound flight AND best return flight
- Selection prioritizes cheapest price with preference for direct flights

RECOMMENDATION GUIDELINES:
After calling search_google_flights, you MUST update the recommendation field with:
- Explain why the selected flight(s) are the best choice based on selection criteria
- Provide booking advice and timing recommendations
- Mention key benefits (price, convenience, direct vs connecting)
- Suggest booking tips or alternative options if needed

CRITICAL RESPONSE FORMAT:
You must return ONLY a valid JSON object matching FlightSearchResults schema:
{{
  "best_outbound_flight": {{...}},
  "best_return_flight": {{...}} or null,
  "search_metadata": {{...}},
  "recommendation": "Your personalized advice about the selected best flight(s)"
}}

For date validation errors, return the error JSON format specified above.
NO additional text, formatting, or explanations outside the JSON structure."""
        )


def parse_agent_response(result) -> FlightSearchResults:
    """Parse agent response and return FlightSearchResults object"""
    try:
        # Get content from the agent result
        content = result.message.get('content')
        
        # Handle different content types - it might be a list of messages
        if isinstance(content, list) and len(content) > 0:
            # Extract the text content from the list
            content_text = content[0].get('text', '') if isinstance(content[0], dict) else str(content[0])
        elif isinstance(content, str):
            content_text = content
        else:
            content_text = str(content)
            
        # Parse JSON string to dictionary
        response_data = json.loads(content_text)
        
        # Check if this is a validation error response
        if 'valid' in response_data and not response_data.get('valid', True):
            # This is a validation error - create ValidationError object
            validation_error = ValidationError(
                valid=False,
                error=response_data.get('error', 'Validation failed')
            )
            
            return FlightSearchResults(
                best_outbound_flight=None,
                best_return_flight=None,
                search_metadata={"validation_error": response_data.get('error', 'Validation failed')},
                recommendation=f"Validation Error: {response_data.get('error', 'Please check your input parameters and try again.')}",
                validation_error=validation_error
            )
            
        # Create FlightSearchResults object from successful response
        # Handle validation errors where flight data might be null
        best_outbound = None
        if response_data.get('best_outbound_flight') and response_data['best_outbound_flight'] is not None:
            try:
                best_outbound = FlightResult(**response_data['best_outbound_flight'])
            except Exception as e:
                print(f"Error creating outbound flight object: {e}")
                best_outbound = None
                
        best_return = None
        if response_data.get('best_return_flight') and response_data['best_return_flight'] is not None:
            try:
                best_return = FlightResult(**response_data['best_return_flight'])
            except Exception as e:
                print(f"Error creating return flight object: {e}")
                best_return = None
        
        flight_results = FlightSearchResults(
            best_outbound_flight=best_outbound,
            best_return_flight=best_return,
            search_metadata=response_data.get('search_metadata', {}),
            recommendation=response_data.get('recommendation', "No recommendation provided")
        )
        
        return flight_results
            
    except json.JSONDecodeError as e:
        # Handle JSON parsing errors
        return FlightSearchResults(
            best_outbound_flight=None,
            best_return_flight=None,
            search_metadata={"error": f"Failed to parse JSON response: {str(e)}"},
            recommendation="There was an error processing the search results. Please try again."
        )
    except Exception as e:
        # Handle any other errors - include more debugging info
        return FlightSearchResults(
            best_outbound_flight=None,
            best_return_flight=None,
            search_metadata={
                "error": str(e),
                "content_type": str(type(result.message.get('content'))),
                "content_preview": str(result.message.get('content'))[:200] if result.message.get('content') else "None"
            },
            recommendation="An unexpected error occurred. Please try again."
        )


# Bedrock AgentCore integration
app = BedrockAgentCoreApp()
agent = FlightAgent()

@app.entrypoint
def flight_agent_invocation(payload):
    """Flight agent entry point for AgentCore Runtime"""
    if "prompt" not in payload:
        return {"error": "Missing 'prompt' in payload"}

    result = agent(payload["prompt"])
    
    # Use the response parsing function
    return parse_agent_response(result)


if __name__ == "__main__":
    app.run()
