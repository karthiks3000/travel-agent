import os
import requests
import boto3
from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp

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
        super().__init__(model="amazon.nova-pro-v1:0")
        
        # Try environment variable first, then Parameter Store
        self.api_key = os.getenv('GOOGLE_PLACES_API_KEY') or \
                       get_parameter('/travel-agent/google-places-api-key')
        
        if not self.api_key:
            raise ValueError("Google Places API key not found in environment or Parameter Store")
    
    @tool
    def search_restaurants(self, text_query: str) -> dict:
        """
        Search restaurants using Google Places Text Search API
        
        Args:
            text_query: Natural language search query for restaurants
                       Examples: 
                       - "Italian restaurants in Rome"
                       - "Vegetarian sushi near Central Park, NYC"
                       - "Cheap tacos in Mexico City"
                       - "Fine dining French restaurants in Paris"
                       - "Gluten-free restaurants near Times Square"
        
        Returns:
            Dict with restaurant results from Google Places API
        """
        
        print(f"🍽️  Searching restaurants: {text_query}")
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': (
                    'places.displayName,places.formattedAddress,places.priceLevel,'
                    'places.rating,places.userRatingCount,places.nationalPhoneNumber,'
                    'places.websiteUri,places.currentOpeningHours.openNow'
                )
            }
            
            response = requests.post(
                "https://places.googleapis.com/v1/places:searchText",
                json={"textQuery": text_query},
                headers=headers
            )
            
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Found {len(result.get('places', []))} restaurant options")
            
            return {
                "success": True,
                "query": text_query,
                "places": result.get('places', []),
                "total_results": len(result.get('places', []))
            }
            
        except Exception as e:
            print(f"❌ Restaurant search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": text_query,
                "places": []
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
