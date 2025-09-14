"""
Flight Agent - Bedrock AgentCore implementation with Nova Act browser automation
"""
import os
import sys
import boto3
from datetime import datetime
from strands import Agent, tool
from typing import Optional, Dict, Any
from bedrock_agentcore import BedrockAgentCoreApp

from common.browser_wrapper import BrowserWrapper
from models.flight_models import FlightSearchResults

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


@tool(description="Search Google Flights for flight options using browser automation")
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
        # Format instructions with actual values
        trip_type = "One way" if not return_date else "Round Trip"
        
        instructions = [
            f"Click on the Round Trip field and change it to {trip_type}",
            f"Set the origin airport to be '{origin}'",
            f"Set the destination to be '{destination}'",
            f"If you see a dialog about excluding basic economy fares, close it",
            f"Click on the departure date field",
            f"Navigate to the correct month and select {departure_date}",
        ]
        
        if return_date:
            instructions.extend([
                f"Click on the return date field",
                f"Navigate to the correct month and select {return_date}"
            ])
            
        if passengers > 1:
            instructions.extend([
                f"Click on the passengers dropdown",
                f"Set the number of passengers to {passengers}"
            ])
            
        instructions.extend([
            "Click the Search button to start the flight search",
            "Wait for the flight search results page to load completely"
        ])
        
        extraction_instruction = f"""Look at the flight search results page and extract flight information from each flight card.
        
        For each visible flight option (up to 10), find and extract:
        
        1. AIRLINE: Look for the airline logo and name (e.g., 'Air France', 'Delta', 'United')
        2. DEPARTURE TIME: Find the departure time, usually on the left (e.g., '10:30 AM', '2:15 PM')  
        3. ARRIVAL TIME: Find the arrival time, usually on the right (e.g., '6:45 PM', '10:30 PM')
        4. PRICE: Look for the dollar amount price (e.g., $542, $798) - extract just the number
        5. DURATION: Find the total flight time (e.g., '7h 15m', '8h 45m')
        6. STOPS: Count the stops - look for 'nonstop' (0 stops), '1 stop', '2 stops', etc.
        7. STOP DETAILS: If there are stops, note the connecting airport (e.g., 'via LHR', 'via AMS')
        
        Return this data structured as:
        - airline: The airline name
        - departure_time: Departure time 
        - arrival_time: Arrival time
        - departure_airport: '{origin}'
        - arrival_airport: '{destination}' 
        - price: Price as number (without $ symbol)
        - duration: Flight duration string
        - stops: Number of stops as integer (0, 1, 2, etc.)
        - stop_details: Stop airport info or null if nonstop
        - booking_class: 'Economy'"""
        
        # Use module-level browser wrapper
        result = browser_wrapper.execute_instructions(
            starting_page="https://www.google.com/travel/flights",
            instructions=instructions,
            extraction_instruction=extraction_instruction,
            result_schema=FlightSearchResults.model_json_schema()
        )
        
        return {
            "success": True,
            "search_params": {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "passengers": passengers
            },
            **result
        }
        
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
            }
        }


class FlightAgent(Agent):
    def __init__(self):
        global browser_wrapper
        
        # Get current date and time for system prompt
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        current_date = datetime.now().strftime("%Y-%m-%d")
        
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
            tools=[search_google_flights],
            system_prompt=f"""You are a flight search specialist. Current date and time: {current_datetime}

You help users find flights by:
1. Understanding natural language requests like "find me the cheapest flight from NYC to LA next Friday"
2. Extracting key details: origin, destination, dates, passenger count, preferences
3. VALIDATING that ALL dates are TODAY or in the FUTURE before searching
4. Using the search_google_flights tool to find flight options (only for valid future dates)
5. Presenting results in a clear, helpful manner focusing on what the user requested

For relative dates like "next Friday", "tomorrow", or "next week", calculate them based on today's date: {current_date}

CRITICAL DATE VALIDATION RULES:
- Only accept flight search requests for dates that are TODAY ({current_date}) or in the FUTURE
- ALWAYS validate ALL dates (departure_date AND return_date if provided) before calling search_google_flights
- If ANY date is in the past (before {current_date}), REJECT the entire request immediately
- DO NOT call search_google_flights for any request with past dates
- Provide helpful error messages explaining why past dates cannot be searched
- Suggest alternative future dates when appropriate

Examples:
✅ VALID: "Find flights for tomorrow" (future date)
✅ VALID: "Book flights departing {current_date}" (today is acceptable)
❌ INVALID: "Find flights for last Tuesday" (past date - politely decline)
❌ INVALID: "Show me flights from yesterday" (past date - explain limitation)

When rejecting past date requests:
- Politely explain that you can only search for flights departing today or in the future
- Suggest the earliest available alternative dates
- Be helpful and understanding about the limitation

When users ask about flights, extract the necessary parameters, validate ALL dates first, then call search_google_flights only if all dates are valid.
Always be helpful and provide relevant flight information based on user needs."""
        )


# Bedrock AgentCore integration
app = BedrockAgentCoreApp()
agent = FlightAgent()

@app.entrypoint
async def flight_agent_invocation(payload):
    """Flight agent entry point for AgentCore Runtime"""
    if "prompt" not in payload:
        yield {"error": "Missing 'prompt' in payload"}
        return
    print('Starting search for prompt', payload['prompt'])
    stream = agent.stream_async(payload["prompt"])
    async for event in stream:
        yield event


if __name__ == "__main__":
    app.run()
