"""
Accommodation Agent - Bedrock AgentCore implementation with Nova Act browser automation
"""
import os
import sys
import boto3
from datetime import datetime
from strands import Agent, tool
from typing import Optional, Dict, Any
from bedrock_agentcore import BedrockAgentCoreApp

from common.browser_wrapper import BrowserWrapper
from models.accommodation_models import PlatformSearchResults

# Module-level browser wrapper - initialized by AccommodationAgent
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


@tool(description="Search Airbnb for accommodation options using browser automation")
def search_airbnb(location: str, check_in: str, check_out: str, guests: int = 2) -> Dict[str, Any]:
    """
    Search Airbnb using Nova Act browser automation
    
    Args:
        location: Destination city or location (e.g., 'Paris, France', 'Manhattan, NYC')
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of guests (1-16)
        
    Returns:
        Dictionary with Airbnb search results
    """
    print(f"🏠 Searching Airbnb: {location} | {check_in} to {check_out} | {guests} guests")
    
    try:
        # Format instructions with actual values for Airbnb
        instructions = [
            f"Click on the location search field and enter '{location}'",
            "Wait for location suggestions to appear and select the first relevant option",
            f"Click on the check-in date field",
            f"Navigate to the calendar and select {check_in} as check-in date",
            f"Navigate to the calendar and select {check_out} as check-out date",
            f"Click on the guests field",
            f"Set the number of adults to {guests}",
            "Click the Search button to start searching for properties",
            "Wait for the search results page to load completely",
            "Click on the Filters button if available",
            "Apply filter for 'Entire home' if available in the Type of place section",
            "Apply 'Guest favourite' filter if available in the Recommended section",
            "Click 'Show X+ places' button to apply filters if any were selected"
        ]
        
        extraction_instruction = f"""Extract Airbnb property listings from the search results page and return them in PlatformSearchResults format.
        
        For each visible property listing (up to 20), create a PropertyResult object with these exact fields:
        
        - platform: "airbnb"
        - title: Property title/description text
        - price_per_night: Numeric price per night (no currency symbols)
        - total_price: Total stay price if displayed, otherwise null
        - rating: Decimal rating (e.g., 4.85) if visible, otherwise null
        - review_count: Number of reviews as integer if visible, otherwise null
        - property_type: Property type description (e.g., "Entire apartment", "Private room")
        - host_name: Host name if displayed, otherwise null
        - location: Neighborhood/area mentioned in listing
        - amenities: Array of amenity strings visible in preview (include "Superhost" and "Guest favourite" as amenities if badges are present)
        - url: Property URL if extractable, otherwise null
        - image_url: Main property image URL if extractable, otherwise null
        - guests_capacity: Maximum guests number if shown, otherwise null
        - bedrooms: Number of bedrooms if shown, otherwise null
        - bathrooms: Number of bathrooms if shown, otherwise null
        
        Return as PlatformSearchResults with:
        - platform: "airbnb"
        - properties: array of PropertyResult objects
        - search_successful: true
        - total_found: number of properties found if displayed on page
        - search_metadata: any additional search info"""
        
        # Use module-level browser wrapper
        result = browser_wrapper.execute_instructions(
            starting_page="https://www.airbnb.com",
            instructions=instructions,
            extraction_instruction=extraction_instruction,
            result_schema=PlatformSearchResults.model_json_schema()
        )
        
        return {
            "success": True,
            "search_params": {
                "location": location,
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests
            },
            **result
        }
        
    except Exception as e:
        print(f"❌ Airbnb search failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "search_params": {
                "location": location,
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests
            }
        }


@tool(description="Search Booking.com for hotel and accommodation options using browser automation")
def search_booking_com(location: str, check_in: str, check_out: str, guests: int = 2, 
                      rooms: int = 1) -> Dict[str, Any]:
    """
    Search Booking.com using Nova Act browser automation
    
    Args:
        location: Destination city or location (e.g., 'Paris, France', 'Manhattan, NYC')
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of guests (1-30)
        rooms: Number of rooms (1-8)
        
    Returns:
        Dictionary with Booking.com search results
    """
    print(f"🏨 Searching Booking.com: {location} | {check_in} to {check_out} | {guests} guests, {rooms} rooms")
    
    try:
        # Format instructions with actual values for Booking.com
        instructions = [
            f"Click on the destination search field and enter '{location}'",
            "Wait for destination suggestions and select the first relevant city option",
            f"Click on the check-in date field",
            f"Navigate the calendar and select {check_in} as check-in date",
            f"Navigate the calendar and select {check_out} as check-out date", 
            f"Click on the guests and rooms selector",
            f"Set {guests} adults and {rooms} room",
            "Click the Search button to find accommodations",
            "Wait for the search results to load completely",
        ]
        
        extraction_instruction = f"""Extract Booking.com property listings from the search results page and return them in PlatformSearchResults format.
        
        For each visible property listing (up to 20), create a PropertyResult object with these exact fields:
        
        - platform: "booking_com"
        - title: Hotel/property name text
        - price_per_night: Numeric price per night (no currency symbols)
        - total_price: Total stay price if displayed, otherwise null
        - rating: Decimal rating (e.g., 8.5, 9.2) if visible, otherwise null
        - review_count: Number of reviews as integer if visible, otherwise null
        - property_type: Property type description (e.g., "Hotel", "Apartment", "Guesthouse", "Resort")
        - host_name: Hotel chain or property management name if displayed, otherwise null
        - location: Specific area/district mentioned in listing
        - amenities: Array of amenity strings visible (e.g., "Free WiFi", "Breakfast included", "Parking", "Pool")
        - url: Property URL if extractable, otherwise null
        - image_url: Main property image URL if extractable, otherwise null
        - guests_capacity: Maximum guests number if shown, otherwise null
        - bedrooms: Number of bedrooms if shown, otherwise null
        - bathrooms: Number of bathrooms if shown, otherwise null
        
        Return as PlatformSearchResults with:
        - platform: "booking_com"
        - properties: array of PropertyResult objects
        - search_successful: true
        - total_found: number of properties found if displayed on page
        - search_metadata: any additional search info"""
        
        # Use module-level browser wrapper
        result = browser_wrapper.execute_instructions(
            starting_page="https://www.booking.com",
            instructions=instructions,
            extraction_instruction=extraction_instruction,
            result_schema=PlatformSearchResults.model_json_schema()
        )
        
        return {
            "success": True,
            "search_params": {
                "location": location,
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests,
                "rooms": rooms
            },
            **result
        }
        
    except Exception as e:
        print(f"❌ Booking.com search failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "search_params": {
                "location": location,
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests,
                "rooms": rooms
            }
        }

class AccommodationAgent(Agent):
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
            tools=[search_airbnb, search_booking_com],
            system_prompt=f"""You are an accommodation search specialist. Current date and time: {current_datetime}

You help users find places to stay by:
1. Understanding natural language requests like "find me a place to stay in Paris for 3 nights starting tomorrow"
2. Extracting key details: location, check-in/out dates, guest count, preferences, budget
3. VALIDATING that ALL dates are TODAY or in the FUTURE before searching
4. Using accommodation search tools to find options from Airbnb and Booking.com (only for valid future dates)
5. Merging and presenting results from both platforms in a unified, helpful manner
6. Sorting and filtering results based on user preferences (price, rating, location, etc.)

For relative dates like "tomorrow", "next week", or "next month", calculate them based on today's date: {current_date}

CRITICAL DATE VALIDATION RULES:
- Only accept accommodation search requests for dates that are TODAY ({current_date}) or in the FUTURE
- ALWAYS validate ALL dates (check_in AND check_out dates) before calling search tools
- If ANY date is in the past (before {current_date}), REJECT the entire request immediately
- DO NOT call search_airbnb or search_booking_com for any request with past dates
- Provide helpful error messages explaining why past dates cannot be searched
- Suggest alternative future dates when appropriate

Examples:
✅ VALID: "Find accommodation starting tomorrow" (future date)
✅ VALID: "Book a hotel checking in {current_date}" (today is acceptable)
❌ INVALID: "Find places I stayed last week" (past date - politely decline)
❌ INVALID: "Show me hotels for yesterday" (past date - explain limitation)

When rejecting past date requests:
- Politely explain that you can only search for accommodations with check-in dates of today or in the future
- Suggest the earliest available alternative dates
- Be helpful and understanding about the limitation

Available tools:
- search_airbnb: Search Airbnb for vacation rentals, apartments, and unique stays
- search_booking_com: Search Booking.com for hotels, resorts, and traditional accommodations

When users ask about accommodations:
1. Extract necessary parameters and validate ALL dates first
2. Only call search tools if all dates are valid (today or future)
3. Call BOTH search tools to get comprehensive results (when dates are valid)
4. Combine results from both platforms into a single, sorted list
5. Present the best options based on user criteria (price, rating, location preferences)
6. Highlight key differences between Airbnb and hotel options
7. Provide clear comparisons and recommendations

Always be helpful and provide relevant accommodation information from both platforms when possible."""
        )


# Bedrock AgentCore integration
app = BedrockAgentCoreApp()
agent = AccommodationAgent()

@app.entrypoint
async def accommodation_agent_invocation(payload):
    """Accommodation agent entry point for AgentCore Runtime"""
    if "prompt" not in payload:
        yield {"error": "Missing 'prompt' in payload"}
        return
    print('Starting accommodation search for prompt', payload['prompt'])
    stream = agent.stream_async(payload["prompt"])
    async for event in stream:
        yield event


if __name__ == "__main__":
    app.run()
