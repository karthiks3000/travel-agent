import os
import requests
import boto3
from datetime import datetime
from strands import Agent, tool
from typing import Optional, Dict, Any, List
from bedrock_agentcore import BedrockAgentCoreApp

from models.food_models import RestaurantSearchResults, RestaurantResult

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
        # Get current date and time for system prompt
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Try environment variable first, then Parameter Store
        self.api_key = os.getenv('GOOGLE_PLACES_API_KEY') or \
                       get_parameter('/travel-agent/google-places-api-key')
        
        if not self.api_key:
            raise ValueError("Google Places API key not found in environment or Parameter Store")
        
        super().__init__(
            model="amazon.nova-pro-v1:0",
            tools=[self.search_restaurants],
            system_prompt=f"""You are a restaurant search specialist. Current date and time: {current_datetime}

CRITICAL: You MUST return ONLY valid JSON responses using the RestaurantSearchResults schema. Never return natural language text.

Your process:
1. Understand natural language requests like "find me 5 Italian restaurants in Rome" or "show me 3 cheap sushi places near Central Park"
2. Extract key details: location, cuisine type, price preferences, dietary restrictions, timing needs, COUNT requested
3. Use search_restaurants tool to find restaurant options using Google Places Text Search API
4. When the tool returns results, you MUST update the recommendation field with personalized advice
5. Return ONLY the updated JSON structure - no additional text or formatting

For relative time references like "tonight", "lunch tomorrow", or "dinner this weekend", use today's date: {current_date}

COUNT HANDLING:
- If user specifies a number (e.g., "find me 5 restaurants"), set page_size to that exact number
- If no count specified, default to 5-10 restaurants for better user experience
- Always respect the requested count in your search

SEARCH OPTIMIZATION:
- Use location_bias for area-specific searches when users mention specific neighborhoods or landmarks
- Apply price_levels filter when users mention budget constraints ("cheap", "expensive", "fine dining")
- Use min_rating filter when users want "good" or "highly rated" restaurants (set to 4.0+)
- Use open_now filter when users need restaurants for immediate dining
- Use included_type filter for specific venue types ("cafe", "bar", "meal_takeaway")

RECOMMENDATION GUIDELINES:
After calling search_restaurants, you MUST update the recommendation field with:
- Personalized advice based on the user's specific request
- Highlight top picks from the results with reasons why
- Practical tips (best times to visit, what to order, special features)
- Context-aware suggestions (budget considerations, dietary needs, location convenience)
- If results are limited, suggest alternative searches or nearby areas

CRITICAL RESPONSE FORMAT:
You must return ONLY a valid JSON object matching RestaurantSearchResults schema:
{{
  "success": true,
  "restaurants": [...],
  "total_results": N,
  "search_metadata": {{...}},
  "next_page_token": null,
  "recommendation": "Your personalized recommendation here based on the results and user request"
}}

NO additional text, formatting, or explanations outside the JSON structure."""
        )
    
    @tool
    def search_restaurants(self, text_query: str, location_bias: Optional[Dict[str, Any]] = None,
                          price_levels: Optional[List[str]] = None, min_rating: Optional[float] = None,
                          open_now: Optional[bool] = None, included_type: Optional[str] = None,
                          page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Search restaurants using Google Places Text Search API
        
        This tool uses the Google Places Text Search (New) API to find restaurants based on natural language queries.
        The API supports rich search queries and various filtering options for precise restaurant discovery.
        
        API Documentation: https://developers.google.com/maps/documentation/places/web-service/text-search
        
        Args:
            text_query: Natural language search query for restaurants. The API responds with restaurants
                       matching the text string and any location bias. Supports rich queries like:
                       - "Italian restaurants in Rome"
                       - "Vegetarian sushi near Central Park, NYC" 
                       - "Cheap tacos in Mexico City"
                       - "Fine dining French restaurants in Paris"
                       - "Gluten-free restaurants near Times Square"
                       - "Best seafood restaurants in Boston"
                       - "24 hour diners near LAX airport"
                       
            location_bias: Optional location bias to prefer results in a specific area.
                          Format: {"circle": {"center": {"latitude": 37.7937, "longitude": -122.3965}, "radius": 500.0}}
                          or {"rectangle": {"low": {"latitude": 40.477398, "longitude": -74.259087}, 
                                          "high": {"latitude": 40.91618, "longitude": -73.70018}}}
                          
            price_levels: Optional list of price level filters. Supported values:
                         ["PRICE_LEVEL_INEXPENSIVE", "PRICE_LEVEL_MODERATE", 
                          "PRICE_LEVEL_EXPENSIVE", "PRICE_LEVEL_VERY_EXPENSIVE"]
                          
            min_rating: Optional minimum rating filter (0.0 to 5.0). Only restaurants with ratings 
                       greater than or equal to this value will be returned.
                       
            open_now: Optional filter to return only restaurants currently open for business.
            
            included_type: Optional restaurant type filter. Examples: "restaurant", "meal_takeaway", 
                          "meal_delivery", "cafe", "bar". Uses Google Places API Table A types.
                          
            page_size: Optional number of results per page (1-20). Default is 20.
        
        Returns:
            Structured dictionary containing:
            - success: Boolean indicating if the search was successful
            - restaurants: List of restaurant objects with details (name, address, rating, etc.)
            - total_results: Number of restaurants found
            - search_metadata: Additional search information
            - query: Original search query
            - next_page_token: Token for pagination (if applicable)
            
        API Features Used:
        - Text Search (New) endpoint: https://places.googleapis.com/v1/places:searchText
        - Field Mask: Specifies which place data fields to return (displayName, formattedAddress, etc.)
        - Search supports natural language understanding and location context
        - Results are ranked by relevance and can be filtered by various criteria
        
        Error Handling:
        - Returns structured error response if API call fails
        - Includes error details and maintains consistent response format
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
            if page_size:
                request_body["pageSize"] = page_size
            
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
                    types=place.get('types', []),
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
                search_metadata={"error": str(e)}
            )
            return {
                "success": False,
                "error": str(e),
                "query": text_query,
                **error_result.model_dump()
            }

app = BedrockAgentCoreApp()
agent = FoodAgent()

@app.entrypoint
async def food_agent_invocation(payload):
    """Food agent entry point for AgentCore Runtime"""
    if "prompt" not in payload:
        yield {"error": "Missing 'prompt' in payload"}
        return

    stream = agent.stream_async(payload["prompt"])
    async for event in stream:
        yield event

if __name__ == "__main__":
    app.run()
