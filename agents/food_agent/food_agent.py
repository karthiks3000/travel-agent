import os
import requests
import boto3
import json
from datetime import datetime
from strands import Agent, tool
from typing import Optional, Dict, Any, List
from bedrock_agentcore import BedrockAgentCoreApp

from common.models.food_models import RestaurantSearchResults, RestaurantResult
from common.models.base_models import ValidationError

def get_parameter(name):
    """Get parameter from AWS Systems Manager Parameter Store"""
    try:
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(Name=name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Failed to retrieve parameter {name}: {str(e)}")
        return None

class FoodAgent(Agent):
    def __init__(self):
        
        # Try environment variable first, then Parameter Store
        self.api_key = os.getenv('GOOGLE_PLACES_API_KEY') or \
                       get_parameter('/travel-agent/google-places-api-key')
        
        if not self.api_key:
            raise ValueError("Google Places API key not found in environment or Parameter Store")
        
        super().__init__(
            model="amazon.nova-pro-v1:0",
            tools=[self.search_restaurants],
            system_prompt=f"""You are a restaurant search specialist that finds the BEST restaurants based on ratings, reviews, and user preferences.

CRITICAL: You MUST return ONLY valid JSON responses using wrapper format with success field. Never return natural language text.

Your process:
1. Understand natural language restaurant requests 
2. Extract key details: location, cuisine, price preferences, rating preferences, count
3. Call search_restaurants tool with appropriate filters
4. When search tool returns results, update the recommendation field with personalized advice
5. Return ONLY the updated JSON structure - no additional text or formatting

Key filters for search_restaurants tool:
- page_size: exact count if user specifies number, otherwise 5-10
- price_levels: ["PRICE_LEVEL_INEXPENSIVE"] for "cheap", ["PRICE_LEVEL_EXPENSIVE"] for "fine dining"
- min_rating: 4.0+ for "good" or "highly rated"
- open_now: true for immediate dining needs

RECOMMENDATION GUIDELINES:
After calling search_restaurants, you MUST update the recommendation field with:
- Explain why the selected restaurants are the best choices based on selection criteria
- Provide dining advice and reservation recommendations
- Mention key benefits (cuisine quality, price range, ratings, location)
- Suggest booking tips or alternative options if needed

CRITICAL RESPONSE FORMAT:
You must return ONLY a valid JSON object matching the wrapper format returned by search_restaurants tool:
{{
  "success": true,
  "query": "search query",
  "restaurants": [{{...}}],
  "total_results": number,
  "search_metadata": {{...}},
  "recommendation": "Your personalized advice about the selected restaurants"
}}

NO additional text, formatting, or explanations outside the JSON structure."""
        )
    
    @tool
    def search_restaurants(self, text_query: str, location_bias: Optional[Dict[str, Any]] = None,
                          price_levels: Optional[List[str]] = None, min_rating: Optional[float] = None,
                          open_now: Optional[bool] = None, included_type: Optional[str] = None,
                          page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Search restaurants using Google Places API
        
        Args:
            text_query: Restaurant search query (e.g., "Italian restaurants in Rome")
            location_bias: Location preference (optional)
            price_levels: Price filters (INEXPENSIVE, MODERATE, EXPENSIVE, VERY_EXPENSIVE)
            min_rating: Minimum rating filter (0.0 to 5.0)
            open_now: Filter for currently open restaurants
            included_type: Venue type filter (restaurant, cafe, bar)
            page_size: Number of results (1-20)
        
        Returns:
            Restaurant search results dictionary
        """
        
        print(f"🍽️  Searching restaurants: {text_query}")
        
        try:
            # Build request headers with comprehensive field mask
            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': (
                    'places.id,places.displayName,places.formattedAddress,places.priceLevel,'
                    'places.rating,places.userRatingCount,places.nationalPhoneNumber,'
                    'places.websiteUri,places.currentOpeningHours.openNow,places.types,'
                    'nextPageToken'
                )
            }
            
            # Build request body with optional parameters
            request_body = {"textQuery": text_query}
            
            if location_bias:
                request_body["locationBias"] = location_bias
            if price_levels:
                request_body["priceLevels"] = price_levels
            if min_rating is not None:
                request_body["minRating"] = min_rating
            if open_now is not None:
                request_body["openNow"] = open_now
            if included_type:
                request_body["includedType"] = included_type
            request_body["pageSize"] = 5
            
            response = requests.post(
                "https://places.googleapis.com/v1/places:searchText",
                json=request_body,
                headers=headers
            )
            
            response.raise_for_status()
            result = response.json()
            places_data = result.get('places', [])
            
            # Transform API response to structured format
            restaurants = []
            for place in places_data:
                restaurant = RestaurantResult(
                    name=place.get('displayName', {}).get('text', 'Unknown'),
                    address=place.get('formattedAddress', ''),
                    rating=place.get('rating'),
                    user_rating_count=place.get('userRatingCount'),
                    price_level=place.get('priceLevel'),
                    phone_number=place.get('nationalPhoneNumber'),
                    website_uri=place.get('websiteUri'),
                    is_open_now=place.get('currentOpeningHours', {}).get('openNow'),
                    place_id=place.get('id')
                )
                restaurants.append(restaurant)
            
            search_results = RestaurantSearchResults(
                restaurants=restaurants,
                total_results=len(restaurants),
                search_metadata={
                    "request_params": request_body,
                    "api_version": "v1"
                },
                next_page_token=result.get('nextPageToken'),
                recommendation="Raw search results - agent should provide personalized recommendation"
            )
            
            print(f"✅ Found {len(restaurants)} restaurant options")
            
            return {
                "success": True,
                "query": text_query,
                **search_results.model_dump()
            }
            
        except Exception as e:
            print(f"❌ Restaurant search failed: {str(e)}")
            error_result = RestaurantSearchResults(
                restaurants=[],
                total_results=0,
                search_metadata={"error": str(e)},
                recommendation="Search failed. Please try again with different parameters."
            )
            return {
                "success": False,
                "error": str(e),
                "query": text_query,
                **error_result.model_dump()
            }

def parse_agent_response(result) -> RestaurantSearchResults:
    """Parse agent response and return RestaurantSearchResults object"""
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
            
            return RestaurantSearchResults(
                restaurants=[],
                total_results=0,
                search_metadata={"validation_error": response_data.get('error', 'Validation failed')},
                recommendation=f"Validation Error: {response_data.get('error', 'Please check your search parameters and try again.')}",
                validation_error=validation_error
            )
            
        # Create RestaurantSearchResults object from successful response
        if response_data.get('success', False):
            # Convert restaurant data to RestaurantResult objects
            restaurants = []
            for restaurant_data in response_data.get('restaurants', []):
                restaurant = RestaurantResult(**restaurant_data)
                restaurants.append(restaurant)
            
            # Create the RestaurantSearchResults object
            search_results = RestaurantSearchResults(
                restaurants=restaurants,
                total_results=response_data.get('total_results', 0),
                search_metadata=response_data.get('search_metadata', {}),
                next_page_token=response_data.get('next_page_token'),
                recommendation=response_data.get('recommendation', "No recommendation provided")
            )
            
            return search_results
        else:
            # Return error case as RestaurantSearchResults with empty results
            return RestaurantSearchResults(
                restaurants=[],
                total_results=0,
                search_metadata={"error": response_data.get('error', 'Unknown error')},
                recommendation="Search failed. Please try again with different parameters."
            )
            
    except json.JSONDecodeError as e:
        # Handle JSON parsing errors
        return RestaurantSearchResults(
            restaurants=[],
            total_results=0,
            search_metadata={"error": f"Failed to parse JSON response: {str(e)}"},
            recommendation="There was an error processing the search results. Please try again."
        )
    except Exception as e:
        # Handle any other errors - include more debugging info
        return RestaurantSearchResults(
            restaurants=[],
            total_results=0,
            search_metadata={
                "error": str(e),
                "content_type": str(type(result.message.get('content'))),
                "content_preview": str(result.message.get('content'))[:200] if result.message.get('content') else "None"
            },
            recommendation="An unexpected error occurred. Please try again."
        )


app = BedrockAgentCoreApp()
agent = FoodAgent()

@app.entrypoint
def food_agent_invocation(payload):
    """Food agent entry point for AgentCore Runtime"""
    if "prompt" not in payload:
        return {"error": "Missing 'prompt' in payload"}

    result = agent(payload["prompt"])
    
    # Use the response parsing function
    return parse_agent_response(result)

if __name__ == "__main__":
    app.run()
