"""
Accommodation Agent - Bedrock AgentCore implementation with Nova Act browser automation
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
from common.models.accommodation_models import PlatformSearchResults, AccommodationAgentResponse, PropertyResult
from common.models.base_models import ValidationError

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


@tool
def validate_inputs(location: str, check_in: str, check_out: str, guests: int = 2, rooms: int = 1) -> Dict[str, Any]:
    """
    Validate accommodation search inputs
    
    Args:
        location: Destination city or location (e.g., 'Paris, France', 'Manhattan, NYC')
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of guests (1-30)
        rooms: Number of rooms (1-8)
        
    Returns:
        Dictionary with validation result: {"valid": bool, "error": str or None}
    """
    try:
        # Get current date
        today = datetime.now().date()
        
        # Validate location is provided
        if not location or not location.strip():
            return {"valid": False, "error": "Location is required for accommodation search."}
        
        # Validate guests count
        if guests < 1 or guests > 30:
            return {"valid": False, "error": f"Invalid guest count: {guests}. Must be between 1-30."}
        
        # Validate rooms count
        if rooms < 1 or rooms > 8:
            return {"valid": False, "error": f"Invalid room count: {rooms}. Must be between 1-8."}
        
        # Parse and validate check-in date
        try:
            if check_in.lower() == "tomorrow":
                checkin_date = today + timedelta(days=1)
            elif check_in.lower() == "today":
                checkin_date = today
            else:
                checkin_date = datetime.strptime(check_in, "%Y-%m-%d").date()
        except ValueError:
            return {"valid": False, "error": f"Invalid check-in date format: {check_in}. Use YYYY-MM-DD format."}
        
        # Check if check-in date is in the past
        if checkin_date < today:
            return {"valid": False, "error": f"Past date: {checkin_date}. Check-in date must be today or in the future."}
        
        # Parse and validate check-out date
        try:
            if check_out.lower() == "tomorrow":
                checkout_date = today + timedelta(days=1)
            elif check_out.lower() == "today":
                checkout_date = today
            else:
                checkout_date = datetime.strptime(check_out, "%Y-%m-%d").date()
        except ValueError:
            return {"valid": False, "error": f"Invalid check-out date format: {check_out}. Use YYYY-MM-DD format."}
        
        # Check if check-out date is in the past
        if checkout_date < today:
            return {"valid": False, "error": f"Past date: {checkout_date}. Check-out date must be today or in the future."}
        
        # Check if check-out date is after check-in date
        if checkout_date <= checkin_date:
            return {"valid": False, "error": f"Check-out date ({checkout_date}) must be after check-in date ({checkin_date})."}
        
        return {"valid": True, "error": None}
        
    except Exception as e:
        return {"valid": False, "error": f"Validation error: {str(e)}"}


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
        PlatformSearchResults with Airbnb property listings
    """
    print(f"🏠 Searching Airbnb: {location} | {check_in} to {check_out} | {guests} guests")
    
    try:
        # Simplified instructions for Airbnb search
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
        
        # Use module-level browser wrapper
        result = browser_wrapper.execute_instructions(
            starting_page="https://www.airbnb.com",
            instructions=instructions,
            extraction_instruction=extraction_instruction,
            result_schema=PlatformSearchResults.model_json_schema()
        )
        
        # Add recommendation field for agent to customize
        result_with_recommendation = {
            "success": True,
            "search_params": {
                "location": location,
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests
            },
            **result,
            "recommendation": "Raw Airbnb search results - agent should provide personalized booking advice"
        }
        
        return result_with_recommendation
        
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
            },
            "platform": "airbnb",
            "properties": [],
            "search_successful": False,
            "search_metadata": {"error": str(e)},
            "recommendation": "Airbnb search failed. Please check your search parameters and try again."
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
        PlatformSearchResults with Booking.com property listings
    """
    print(f"🏨 Searching Booking.com: {location} | {check_in} to {check_out} | {guests} guests, {rooms} rooms")
    
    try:
        # Simplified instructions for Booking.com search
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
        
        # Use module-level browser wrapper
        result = browser_wrapper.execute_instructions(
            starting_page="https://www.booking.com",
            instructions=instructions,
            extraction_instruction=extraction_instruction,
            result_schema=PlatformSearchResults.model_json_schema()
        )
        
        # Add recommendation field for agent to customize
        result_with_recommendation = {
            "success": True,
            "search_params": {
                "location": location,
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests,
                "rooms": rooms
            },
            **result,
            "recommendation": "Raw Booking.com search results - agent should provide personalized booking advice"
        }
        
        return result_with_recommendation
        
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
            },
            "platform": "booking_com",
            "properties": [],
            "search_successful": False,
            "search_metadata": {"error": str(e)},
            "recommendation": "Booking.com search failed. Please check your search parameters and try again."
        }


@tool(description="Combine and sort accommodation results from multiple platforms")
def combine_and_sort_results(airbnb_results: Dict[str, Any], 
                           booking_results: Dict[str, Any],
                           sort_by: str = "value") -> Dict[str, Any]:
    """
    Combine and sort results from Airbnb and Booking.com platforms
    
    Args:
        airbnb_results: Results from search_airbnb tool (dictionary format)
        booking_results: Results from search_booking_com tool (dictionary format)
        sort_by: Sorting criteria ("value", "price", "rating")
        
    Returns:
        Dictionary with combined and sorted properties
    """
    try:
        # Get properties from dictionary results, handling both success and error cases
        airbnb_properties = airbnb_results.get("properties", []) if airbnb_results.get("success", False) else []
        booking_properties = booking_results.get("properties", []) if booking_results.get("success", False) else []
        
        print(f"🔄 Combining results from Airbnb ({len(airbnb_properties)}) and Booking.com ({len(booking_properties)})")
        
        # Combine all properties
        all_properties = []
        
        for prop_dict in airbnb_properties:
            if isinstance(prop_dict, dict):
                all_properties.append(PropertyResult(**prop_dict))
            else:
                all_properties.append(prop_dict)  # Already an object
                
        for prop_dict in booking_properties:
            if isinstance(prop_dict, dict):
                all_properties.append(PropertyResult(**prop_dict))
            else:
                all_properties.append(prop_dict)  # Already an object
        
        # Sort by different criteria
        if sort_by == "price":
            # Sort by price (ascending)
            sorted_properties = sorted(all_properties, key=lambda x: x.price_per_night or float('inf'))
        elif sort_by == "rating":
            # Sort by rating (descending), handle None ratings
            sorted_properties = sorted(all_properties, 
                                     key=lambda x: x.rating if x.rating is not None else 0, 
                                     reverse=True)
        else:  # sort_by == "value" (default)
            # Sort by value score: rating/price ratio, with rating weight
            def value_score(prop):
                if prop.rating is None or not prop.price_per_night or prop.price_per_night <= 0:
                    return 0
                # Higher rating and lower price = better value
                return (prop.rating * 100) / prop.price_per_night
            
            sorted_properties = sorted(all_properties, key=value_score, reverse=True)
        
        # Take top 15 results (will be further filtered by agent to 5-10)
        top_properties = sorted_properties[:15]
        
        # Create combined metadata
        combined_metadata = {
            "airbnb_count": len(airbnb_properties),
            "booking_count": len(booking_properties),
            "total_combined": len(all_properties),
            "top_selected": len(top_properties),
            "sort_criteria": sort_by,
            "airbnb_successful": airbnb_results.get("success", False),
            "booking_successful": booking_results.get("success", False)
        }
        
        # Return dictionary format to match other search functions
        return {
            "success": True,
            "search_params": {
                "combined_search": True,
                "sort_by": sort_by
            },
            "platform": "combined",
            "properties": [prop.model_dump() for prop in top_properties],
            "search_successful": True,
            "total_found": len(all_properties),
            "search_metadata": combined_metadata,
            "recommendation": "Raw combined search results - agent should provide personalized booking advice"
        }
        
    except Exception as e:
        print(f"❌ Combining results failed: {str(e)}")
        # Return error result in dictionary format
        return {
            "success": False,
            "error": str(e),
            "search_params": {
                "combined_search": True,
                "sort_by": sort_by
            },
            "platform": "combined",
            "properties": [],
            "search_successful": False,
            "search_metadata": {
                "error": str(e),
                "airbnb_count": len(airbnb_results.get("properties", [])) if airbnb_results else 0,
                "booking_count": len(booking_results.get("properties", [])) if booking_results else 0
            },
            "recommendation": "Combining search results failed. Please try searching individual platforms."
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
            tools=[validate_inputs, search_airbnb, search_booking_com, combine_and_sort_results],
            system_prompt=f"""You are an accommodation search specialist that finds the BEST accommodations from multiple platforms. Current date and time: {current_datetime}

CRITICAL: You MUST return ONLY valid JSON responses using the AccommodationAgentResponse schema. Never return natural language text.

Your process:
1. Understand natural language requests like "find me a place to stay in Paris for 3 nights starting tomorrow"
2. Extract key details: location, check-in/out dates, guest count, room count, preferences
3. ALWAYS call validate_inputs tool first with the extracted parameters
4. If validation fails (valid: false), return JSON error response with the validation error
5. Only if validation passes (valid: true), INTELLIGENTLY choose which platform(s) to search based on user request
6. SELECT and return only the BEST 5-10 accommodations from results
7. Return ONLY the updated JSON structure - no additional text or formatting

CRITICAL WORKFLOW:
1. Call validate_inputs(location, check_in, check_out, guests, rooms)
2. If validation result shows "valid": false, return the EXACT SAME JSON format as validate_inputs tool:
   {{"valid": false, "error": "[validation error message from tool]"}}
3. If validation result shows "valid": true, INTELLIGENTLY select platform(s) based on user request:

VALIDATION ERROR RESPONSE FORMAT:
When validation fails, return the exact same format as the validate_inputs tool:
{{"valid": false, "error": "specific error message"}}

Do NOT return AccommodationAgentResponse format for validation errors - use the validation format above.

SMART PLATFORM SELECTION:
- **Booking.com ONLY**: When user mentions "hotel", "resort", "inn", "motel", "bed and breakfast", "hostel", "spa", "casino"
- **Airbnb ONLY**: When user mentions "airbnb", "vacation rental", "apartment", "house", "villa", "condo", "room", "home", "rental"
- **BOTH platforms**: For generic requests like "accommodation", "place to stay", "lodging", "somewhere to stay" or no specific type mentioned

SEARCH WORKFLOW BASED ON SELECTION:
- **Single platform**: Call the appropriate search tool, use its results directly for final selection
- **Both platforms**: Call both search_airbnb AND search_booking_com, then call combine_and_sort_results to merge and rank all options

ACCOMMODATION SELECTION BEHAVIOR:
- YOU must select and return only the BEST 5-10 accommodations based on:
  * BEST VALUE (price vs quality ratio - primary factor)
  * HIGH RATINGS (prefer 4.5+ stars when available)
  * GOOD REVIEWS (prefer properties with many positive reviews)
  * USER PREFERENCES (location, property type, amenities)
- For combined results, use the combine_and_sort_results tool first, then select top options

RECOMMENDATION GUIDELINES:
After calling search tools, you MUST update the recommendation field with:
- Explain why the selected accommodations are the best choices based on selection criteria
- Provide booking advice and timing recommendations
- Mention key benefits (value, location, amenities, platform differences)
- Suggest booking tips or alternative options if needed
- Highlight differences between Airbnb vs hotel options when both platforms used

CRITICAL RESPONSE FORMAT:
You must return ONLY a valid JSON object matching AccommodationAgentResponse schema:
{{
  "best_accommodations": [{{...}}, {{...}}],
  "search_metadata": {{...}},
  "recommendation": "Your personalized advice about the selected best accommodations"
}}

For validation errors, return the error JSON format specified above.
NO additional text, formatting, or explanations outside the JSON structure."""
        )


def parse_agent_response(result) -> AccommodationAgentResponse:
    """Parse agent response and return AccommodationAgentResponse object"""
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
            
            return AccommodationAgentResponse(
                best_accommodations=[],
                search_metadata={"validation_error": response_data.get('error', 'Validation failed')},
                recommendation=f"Validation Error: {response_data.get('error', 'Please check your search parameters and try again.')}",
                validation_error=validation_error
            )
        
        # Create AccommodationAgentResponse object from successful response
        # Handle accommodation data
        best_accommodations = []
        if response_data.get('best_accommodations'):
            try:
                for accommodation_data in response_data['best_accommodations']:
                    accommodation = PropertyResult(**accommodation_data)
                    best_accommodations.append(accommodation)
            except Exception as e:
                print(f"Error creating accommodation objects: {e}")
                best_accommodations = []
        
        accommodation_results = AccommodationAgentResponse(
            best_accommodations=best_accommodations,
            search_metadata=response_data.get('search_metadata', {}),
            recommendation=response_data.get('recommendation', "No recommendation provided")
        )
        
        return accommodation_results
            
    except json.JSONDecodeError as e:
        # Handle JSON parsing errors
        return AccommodationAgentResponse(
            best_accommodations=[],
            search_metadata={"error": f"Failed to parse JSON response: {str(e)}"},
            recommendation="There was an error processing the search results. Please try again."
        )
    except Exception as e:
        # Handle any other errors - include more debugging info
        return AccommodationAgentResponse(
            best_accommodations=[],
            search_metadata={
                "error": str(e),
                "content_type": str(type(result.message.get('content'))),
                "content_preview": str(result.message.get('content'))[:200] if result.message.get('content') else "None"
            },
            recommendation="An unexpected error occurred. Please try again."
        )


# Bedrock AgentCore integration
app = BedrockAgentCoreApp()
agent = AccommodationAgent()

@app.entrypoint
def accommodation_agent_invocation(payload):
    """Accommodation agent entry point for AgentCore Runtime"""
    if "prompt" not in payload:
        return {"error": "Missing 'prompt' in payload"}

    result = agent(payload["prompt"])
    
    # Use the response parsing function
    return parse_agent_response(result)


if __name__ == "__main__":
    app.run()
