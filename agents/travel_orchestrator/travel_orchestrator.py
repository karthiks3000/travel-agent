"""
Travel Orchestrator Agent - Main conversational interface for travel planning
"""
import os
import json
from datetime import datetime
from typing import List, Optional

import boto3
import logging
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from strands.hooks import HookRegistry
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from tools.flight_search_tool import search_flights_direct
from tools.accommodation_search_tool import search_accommodations_direct
from tools.memory_hooks import TravelMemoryHook, generate_session_ids

# Import new unified response models from centralized common location
from common.models.orchestrator_models import (
    TravelOrchestratorResponse, ResponseType, ResponseStatus, create_tool_progress
)
from common.models.flight_models import FlightResult
from common.models.accommodation_models import PropertyResult
from common.models.food_models import RestaurantResult
from common.models.itinerary_models import AttractionResult
from tools.itinerary_generator import generate_comprehensive_itinerary, TripComponents

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("travel-orchestrator")


def get_parameter(name):
    """Get parameter from AWS Systems Manager Parameter Store"""
    try:
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(Name=name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Failed to retrieve parameter {name}: {str(e)}")
        return None


def extract_user_id_from_context(context) -> str:
    """
    Extract user ID from JWT token context using the 'sub' claim
    
    Args:
        context: AgentCore runtime context containing JWT claims
        
    Returns:
        User identifier from JWT 'sub' claim, or 'anonymous' if not available
    """
    if not context:
        logger.warning("No context provided - using anonymous user")
        return "anonymous"
    
    # Extract user ID from JWT 'sub' claim
    user_id = getattr(context, 'sub', None)
    if user_id:
        logger.info(f"✅ Extracted user_id from JWT context: {user_id}")
        return user_id
    
    logger.warning("No user identity found in JWT context - using anonymous")
    return "anonymous"


class TravelOrchestratorAgent(Agent):
    def __init__(self, memory_id: Optional[str] = None, session_id: Optional[str] = None, 
                 actor_id: Optional[str] = None, region: str = "us-east-1"):
        """
        Initialize Travel Orchestrator Agent with Gateway integration and memory
        
        Args:
            memory_id: AgentCore Memory resource ID (created if not provided)
            session_id: Shared session ID for the conversation
            actor_id: User identifier for personalization and actor scoping
            region: AWS region for AgentCore services
        """
        # Get current date for system prompt
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Store session info for tools
        self.session_id = session_id
        self.actor_id = actor_id
        self.region = region
        
        logger.info(f"Initializing Travel Orchestrator - Session: {session_id}, Actor: {actor_id}")
        
        # Initialize Nova Act API key as environment variable for tools
        self._initialize_nova_act_api_key()
        
        # Initialize Amadeus API credentials as environment variables for tools
        self._initialize_amadeus_credentials()
        
        # Initialize memory if enabled
        memory_hooks = None
        if memory_id:
            try:
                memory_client = MemoryClient(region_name=region)
                memory_hooks = TravelMemoryHook(memory_client, memory_id)
                logger.info(f"✅ Memory integration enabled with memory_id: {memory_id}")
            except Exception as e:
                logger.error(f"Failed to initialize memory: {e}")
                memory_hooks = None
        
        # Initialize Gateway tools via MCP client (GitHub example pattern)
        gateway_tools = self._initialize_gateway_tools(region)
        
        # Combine direct tools with Gateway tools and new enhanced tools
        all_tools = (
            [
                self.search_flights,
                self.search_accommodations,
            ]
            + gateway_tools  # Add Google Maps tools from Gateway
        )
        
        # Initialize agent state for memory hooks
        agent_state = {
            "actor_id": actor_id,
            "session_id": session_id,
            "agent_type": "travel_orchestrator"
        }
        
        # Configure model with increased max_tokens to prevent truncation
        model = BedrockModel(
            model_id="us.amazon.nova-premier-v1:0",
            max_tokens=10000,  # Increased from default ~4096 to handle large JSON responses
            temperature=0.7,
            top_p=0.9
        )
        
        super().__init__(
            model=model,
            tools=all_tools,
            system_prompt=self._build_system_prompt(current_datetime, current_date),
            hooks=[memory_hooks] if memory_hooks else [],
            state=agent_state
        )
    
    def _initialize_gateway_tools(self, region: str = "us-east-1") -> List:
        """
        Initialize Gateway tools via MCP client automatic discovery (GitHub example pattern)
        
        Args:
            region: AWS region
            
        Returns:
            List of discovered tools from Gateway
        """
        try:
            # Get Gateway configuration from Parameter Store
            gateway_url = get_parameter('/travel-agent/gateway-url')
            gateway_client_id = get_parameter('/travel-agent/gateway-client-id')
            gateway_client_secret = get_parameter('/travel-agent/gateway-client-secret')
            
            if not all([gateway_url, gateway_client_id, gateway_client_secret]):
                logger.warning("⚠️  Gateway configuration not found in Parameter Store - Gateway tools disabled")
                logger.warning("Deploy Gateway first with: ./deploy-travel-orchestrator.sh")
                return []
            
            # Get access token for Gateway
            from gateway_utils import get_token
            user_pool_id = get_parameter('/travel-agent/gateway-user-pool-id')
            
            if not user_pool_id:
                logger.warning("⚠️  Could not determine user pool ID for Gateway authentication")
                return []
            
            scope_string = "travel-agent-gateway/gateway:read travel-agent-gateway/gateway:write"
            
            # Ensure all parameters are strings before passing to get_token
            if not isinstance(user_pool_id, str) or not isinstance(gateway_client_id, str) or not isinstance(gateway_client_secret, str):
                logger.warning("⚠️  Invalid Gateway configuration types")
                return []
                
            token_response = get_token(user_pool_id, gateway_client_id, gateway_client_secret, scope_string, region)
            access_token = token_response['access_token']
            
            logger.info("✅ Gateway authentication successful")
            
            # Create MCP transport function
            def create_gateway_transport():
                # Ensure gateway_url is a string
                if not isinstance(gateway_url, str):
                    raise ValueError("Gateway URL is not a valid string")
                return streamablehttp_client(
                    gateway_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
            
            # Initialize MCP client and start session (GitHub pattern)
            self.mcp_client = MCPClient(create_gateway_transport)
            
            try:
                self.mcp_client.start()  # Start persistent session
                logger.info("✅ MCP client session started")
                
                gateway_tools = self.mcp_client.list_tools_sync()
                logger.info(f"✅ Discovered {len(gateway_tools)} Google Maps tools from Gateway")
                
                # Log discovered tool names
                for tool in gateway_tools:
                    if hasattr(tool, 'name'):
                        logger.info(f"  - {tool.name}")
                
                return gateway_tools
                
            except Exception as e:
                logger.error(f"❌ Failed to start MCP client session: {e}")
                return []
            
        except Exception as e:
            logger.warning(f"⚠️  Gateway tool discovery failed: {e}")
            logger.warning("Continuing with direct tools only - Google Maps features will be limited")
            return []
    
    
    def _initialize_nova_act_api_key(self):
        """
        Initialize Nova Act API key as environment variable for tools to use
        
        Fetches from Parameter Store or existing environment variable and sets 
        NOVA_ACT_API_KEY environment variable for tools to access
        """
        try:
            # Check if already set in environment
            existing_key = os.getenv('NOVA_ACT_API_KEY')
            if existing_key:
                logger.info("✅ Nova Act API key already available in environment")
                return
            
            # Try to get from Parameter Store first
            try:
                nova_act_api_key = get_parameter('/travel-agent/nova-act-api-key')
                if nova_act_api_key:
                    os.environ['NOVA_ACT_API_KEY'] = nova_act_api_key
                    logger.info("✅ Nova Act API key loaded from Parameter Store and set in environment")
                    return
            except Exception as e:
                logger.warning(f"⚠️  Could not retrieve Nova Act API key from Parameter Store: {e}")
            
            # Log warning if no key available
            logger.warning("⚠️  Nova Act API key not available - browser automation tools may fail")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Nova Act API key: {e}")
    
    def _initialize_amadeus_credentials(self):
        """
        Initialize Amadeus API credentials as environment variables for tools to use
        
        Fetches from Parameter Store or existing environment variables and sets 
        AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET, AMADEUS_HOSTNAME environment variables
        for the flight search tool to access
        """
        try:
            # Check if already set in environment
            existing_client_id = os.getenv('AMADEUS_CLIENT_ID')
            existing_client_secret = os.getenv('AMADEUS_CLIENT_SECRET')
            
            if existing_client_id and existing_client_secret:
                logger.info("✅ Amadeus API credentials already available in environment")
                return
            
            # Try to get from Parameter Store first
            try:
                amadeus_client_id = get_parameter('/travel-agent/amadeus-client-id')
                amadeus_client_secret = get_parameter('/travel-agent/amadeus-client-secret')
                amadeus_hostname = get_parameter('/travel-agent/amadeus-hostname')
                
                if amadeus_client_id and amadeus_client_secret:
                    os.environ['AMADEUS_CLIENT_ID'] = amadeus_client_id
                    os.environ['AMADEUS_CLIENT_SECRET'] = amadeus_client_secret
                    os.environ['AMADEUS_HOSTNAME'] = amadeus_hostname or 'test'  # Default to 'test'
                    logger.info("✅ Amadeus API credentials loaded from Parameter Store and set in environment")
                    logger.info(f"✅ Using Amadeus hostname: {amadeus_hostname or 'test'}")
                    return
                else:
                    logger.warning("⚠️  Incomplete Amadeus credentials found in Parameter Store")
                    
            except Exception as e:
                logger.warning(f"⚠️  Could not retrieve Amadeus credentials from Parameter Store: {e}")
            
            # Log warning if no credentials available
            logger.warning("⚠️  Amadeus API credentials not available - flight search tools may fail")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Amadeus API credentials: {e}")
    
    def _validate_flight_params(self, origin: str, destination: str, departure_date: str, 
                               return_date: Optional[str] = None, passengers: int = 1) -> List[str]:
        """
        Validate flight search parameters
        
        Returns:
            List of error messages (empty if all parameters are valid)
        """
        missing_params = []
        
        # Required parameters
        if not origin or origin.strip() == "":
            missing_params.append("origin")
        if not destination or destination.strip() == "":
            missing_params.append("destination")
        if not departure_date or departure_date.strip() == "":
            missing_params.append("departure_date")
        
        # Validate same origin/destination
        if origin and destination and origin.strip().lower() == destination.strip().lower():
            missing_params.append("origin and destination cannot be the same")
        
        # Validate passenger count
        if passengers < 1 or passengers > 9:
            missing_params.append(f"passengers must be between 1-9 (got {passengers})")
        
        # Validate dates are not in the past
        try:
            today = datetime.now().date()
            
            if departure_date and departure_date != "":
                dep_date = datetime.strptime(departure_date, "%Y-%m-%d").date()
                if dep_date < today:
                    missing_params.append(f"departure_date (cannot be in past: {departure_date})")
            
            if return_date and return_date != "":
                ret_date = datetime.strptime(return_date, "%Y-%m-%d").date()
                if ret_date < today:
                    missing_params.append(f"return_date (cannot be in past: {return_date})")
                elif departure_date and ret_date <= dep_date:
                    missing_params.append("return_date (must be after departure_date)")
        except ValueError as e:
            missing_params.append(f"invalid date format: {str(e)}")
        
        return missing_params
    
    def _validate_accommodation_params(self, destination: str, departure_date: str, return_date: str, 
                                     passengers: int = 2, rooms: int = 1) -> List[str]:
        """
        Validate accommodation search parameters
        
        Returns:
            List of error messages (empty if all parameters are valid)
        """
        missing_params = []
        
        # Required parameters
        if not destination or destination.strip() == "":
            missing_params.append("destination")
        if not departure_date or departure_date.strip() == "":
            missing_params.append("departure_date")
        if not return_date or return_date.strip() == "":
            missing_params.append("return_date")
        
        # Validate guest/room counts
        if passengers < 1 or passengers > 30:
            missing_params.append(f"passengers must be between 1-30 (got {passengers})")
        if rooms < 1 or rooms > 8:
            missing_params.append(f"rooms must be between 1-8 (got {rooms})")
        
        # Validate dates are not in the past
        try:
            today = datetime.now().date()
            
            if departure_date and departure_date != "":
                dep_date = datetime.strptime(departure_date, "%Y-%m-%d").date()
                if dep_date < today:
                    missing_params.append(f"departure_date (cannot be in past: {departure_date})")
            
            if return_date and return_date != "":
                ret_date = datetime.strptime(return_date, "%Y-%m-%d").date()
                if ret_date < today:
                    missing_params.append(f"return_date (cannot be in past: {return_date})")
                elif departure_date and ret_date <= dep_date:
                    missing_params.append("return_date (must be after departure_date)")
        except ValueError as e:
            missing_params.append(f"invalid date format: {str(e)}")
        
        return missing_params
    

    def _build_system_prompt(self, current_datetime: str, current_date: str) -> str:
        """Build enhanced system prompt for comprehensive travel orchestration with JSON response format"""
        return f"""You are an Expert Travel Planning Agent. Current date: {current_datetime}

YOUR ROLE: Create comprehensive travel plans by coordinating flight searches, accommodation searches, and Google Places API for restaurants and attractions.

**CRITICAL: ALWAYS RESPOND IN JSON FORMAT USING TravelOrchestratorResponse**

AVAILABLE TOOLS:
- search_flights: Find flight options (returns multiple results based on request)
- search_accommodations: Find accommodation options (returns multiple results based on request)  
- searchPlacesByText: Google Places text search - USE THIS DIRECTLY for restaurants and attractions
- searchNearbyPlaces: Google Places nearby search - USE THIS for locations around specific points  
- getPlaceDetails: Get detailed information about specific places - USE THIS for place details

**IMPORTANT: For restaurants and attractions, call the Google Places tools directly. Do NOT use wrapper functions.**

REQUEST TYPE DETECTION - Listen carefully to what users want:

1. **SPECIFIC BEST OPTIONS**: "best flight", "cheapest hotel", "top-rated restaurant"
   → Call appropriate tools and return 1 result
   → response_type: "flights", "accommodations", "restaurants", or "attractions"

2. **MULTIPLE OPTIONS**: "show me 5 flights", "give me hotel options under $200", "find 3 Italian restaurants"
   → Call appropriate tools and return multiple results (2-10)
   → response_type: "flights", "accommodations", "restaurants", or "attractions"

3. **MIXED REQUESTS**: "flights and hotels to Paris", "restaurants and attractions in Rome"
   → Call multiple tools and return multiple component types
   → response_type: "mixed_results"

4. **COMPREHENSIVE PLANNING**: "plan my trip", "create itinerary", "7-day vacation plan"
   → Call multiple tools and create the itinerary
   → response_type: "itinerary"

INTELLIGENT GOOGLE PLACES API USAGE:

For Restaurant Searches:
- Call searchPlacesByText with query like "Italian restaurants in Paris"
- Use type="restaurant" parameter
- Apply price filters: minprice/maxprice (0=Free, 1=Inexpensive, 2=Moderate, 3=Expensive, 4=Very Expensive)
- Parse results and format into RestaurantResult objects with all required fields
- Return in restaurant_results array

For Attraction Searches:
- Call searchPlacesByText with query like "museums in Paris" or "attractions in Rome"  
- Use type="tourist_attraction" parameter
- Parse results and format into AttractionResult objects with all required fields
- Estimate visit_duration_estimate based on place types (museums=120min, parks=60min, etc.)
- Return in attraction_results array

GOOGLE PLACES RESPONSE FORMATTING:
When you call Google Places APIs, format the responses into our Pydantic models:

RestaurantResult format:
{{
  "name": "Restaurant Name",
  "address": "Full Address", 
  "rating": 4.5,
  "user_rating_count": 1250,
  "price_level": "PRICE_LEVEL_MODERATE",
  "phone_number": "+33123456789",
  "website_uri": "https://restaurant.com",
  "is_open_now": true,
  "types": ["restaurant", "french_restaurant"],
  "place_id": "ChIJxxxxxx"
}}

AttractionResult format:
{{
  "name": "Attraction Name",
  "place_id": "ChIJxxxxxx", 
  "formatted_address": "Full Address",
  "rating": 4.8,
  "user_ratings_total": 25000,
  "price_level": 2,
  "types": ["tourist_attraction", "museum"],
  "opening_hours": {{"open_now": true}},
  "website": "https://attraction.com",
  "visit_duration_estimate": 120
}}

PARAMETER REQUIREMENTS:

search_flights:
- origin: REQUIRED - Must be a city name or airport code
- destination: REQUIRED - Must be a city name or airport code
- departure_date: REQUIRED - Must be in YYYY-MM-DD format
- return_date: OPTIONAL - Must be in YYYY-MM-DD format, after departure_date
- passengers: OPTIONAL - Defaults to 1, must be 1-9

search_accommodations:
- destination: REQUIRED - Must be a city name
- departure_date: REQUIRED - Check-in date in YYYY-MM-DD format
- return_date: REQUIRED - Check-out date in YYYY-MM-DD format, after departure_date
- passengers: OPTIONAL - Defaults to 2, must be 1-30 (number of guests)
- rooms: OPTIONAL - Defaults to 1, must be 1-8
- platform_preference: OPTIONAL - "airbnb", "booking", or "both". use booking when user specifies hotels or resorts. use airbnb when user is looking for rentals. use both when the user hasnt specified a preference for type of accomodation

DIRECT GOOGLE PLACES API USAGE EXAMPLES:

For "find vegan restaurants in Paris":
1. Call searchPlacesByText with:
   - query: "vegan restaurants in Paris"
   - type: "restaurant" 
   - maxResultCount: 5
2. Wait for complete response
3. Format results into TravelOrchestratorResponse


For "find museums in Rome":
1. Call searchPlacesByText with:
   - query: "museums in Rome"
   - type: "tourist_attraction"
   - maxResultCount: 5
2. Wait for complete response  
3. Format results into TravelOrchestratorResponse


**CRITICAL: Always wait for Google Places API responses before returning to user.**

TOOL CALLING RULES:
1. **ONLY call tools when you have ALL required parameters with valid values**
2. **Origin/destination MUST be actual city names or airport codes** (not generic terms)
3. **Dates MUST be in proper YYYY-MM-DD format** (not relative terms like "next week")
4. **If any required parameter is missing or invalid, ask the user for clarification**
5. **Use conversation context to fill in missing details when possible**

RESPONSE FORMATS:

Single Component (flights only):
{{
  "response_type": "flights",
  "message": "Found 5 flight options for your NYC to Paris trip.",
  "flight_results": [FlightResult, FlightResult, ...],
  "estimated_costs": {{"flights": 890}},
  "success": true
}}

Mixed Components:
{{
  "response_type": "mixed_results", 
  "message": "Found flights, hotels, and restaurants for your Paris trip.",
  "flight_results": [FlightResult, ...],
  "accommodation_results": [PropertyResult, ...],
  "restaurant_results": [RestaurantResult, ...],
  "success": true
}}

Full Itinerary:
{{
  "response_type": "itinerary",
  "message": "Created your complete 7-day Paris itinerary.",
  "itinerary": {{
    "trip_title": "7-Day Paris Adventure",
    "daily_itineraries": [
      {{
        "day_number": 1,
        "date": "2024-06-15",
        "location": "Paris",
        "daily_summary": "Arrival and Eiffel Tower visit",
        "activities": [
          {{
            "time_slot": {{"start_time": "09:00", "end_time": "11:30"}},
            "activity_type": "flight",
            "title": "Arrive in Paris",
            "activity_details": {{/* FlightResult */}},
            "notes": "Land at CDG, allow time for customs"
          }},
          {{
            "time_slot": {{"start_time": "12:30", "duration_minutes": 90}},
            "activity_type": "restaurant", 
            "title": "Lunch at Café de Flore",
            "activity_details": {{/* RestaurantResult */}},
            "notes": "Classic Parisian bistro experience"
          }}
        ]
      }}
    ]
  }},
  "success": true
}}

CONVERSATION FLOW:
- If missing required parameters, ask specific questions
- Use context from previous messages to fill gaps
- Validate dates (no past dates except today: {current_date})
- Provide helpful travel planning advice

Always be a professional travel planner - knowledgeable, helpful, and detail-oriented.

REMEMBER: Always respond in JSON using the following schema - {TravelOrchestratorResponse.model_json_schema()}"""


    @tool
    def search_flights(self, origin: str, destination: str, departure_date: str, 
                      return_date: Optional[str] = None, passengers: int = 1) -> TravelOrchestratorResponse:
        """
        Search for flights using direct browser automation tools
        
        Args:
            origin: Origin airport IATA code (e.g., 'JFK', 'BOM')
            destination: Destination airport IATA code (e.g., 'LAX', 'HYD') 
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date for round-trip (optional)
            passengers: Number of passengers (1-9)
        
        Returns:
            TravelOrchestratorResponse with structured flight results and progress tracking
        """
        # Validate parameters using dedicated validation method
        validation_errors = self._validate_flight_params(origin, destination, departure_date, return_date, passengers)
        
        # Return validation error if parameters are invalid
        if validation_errors:
            validation_progress = create_tool_progress("search_flights", {"origin": origin, "destination": destination}, "failed")
            validation_progress.error_message = f"Missing required parameters: {', '.join(validation_errors)}"
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.VALIDATION_ERROR,
                message=f"I need more information to search for flights. Missing: {', '.join(validation_errors)}",
                overall_progress_message="Flight search needs more details",
                is_final_response=False,
                next_expected_input_friendly=f"Please provide: {', '.join(validation_errors)}",
                tool_progress=[validation_progress],
                success=False,
                error_message=f"Missing parameters: {', '.join(validation_errors)}",
                processing_time_seconds=0,
                flight_results=None,
                accommodation_results=None,
                restaurant_results=None,
                attraction_results=None,
                itinerary=None,
                estimated_costs=None,
                recommendations=None,
                session_metadata=None
            )
        
        print(f"✈️  Direct flight search: {origin} → {destination} on {departure_date}")
        if return_date:
            print(f"   Return: {return_date} | Passengers: {passengers}")
        
        try:
            # Call the direct flight search tool
            return search_flights_direct(origin, destination, departure_date, return_date, passengers)
            
        except Exception as e:
            print(f"❌ Direct flight search failed: {str(e)}")
            
            # Create error response
            flight_progress = create_tool_progress("search_flights", {"origin": origin, "destination": destination}, "failed")
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
                processing_time_seconds=0,
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

    @tool
    def search_accommodations(self, destination: str, departure_date: str, return_date: str, 
                            passengers: int = 2, rooms: int = 1, platform_preference: str = "both") -> TravelOrchestratorResponse:
        """
        Search for accommodations using standardized parameters
        
        Args:
            destination: Destination city or location (e.g., 'Paris, France', 'Manhattan, NYC')
            departure_date: Check-in date in YYYY-MM-DD format (same as flight departure)
            return_date: Check-out date in YYYY-MM-DD format (same as flight return)
            passengers: Number of guests/passengers (1-30)
            rooms: Number of rooms (1-8)
            platform_preference: "airbnb", "booking", or "both"
        
        Returns:
            TravelOrchestratorResponse with structured accommodation results and progress tracking
        """
        # Validate parameters using dedicated validation method
        validation_errors = self._validate_accommodation_params(destination, departure_date, return_date, passengers, rooms)
        
        # Return validation error if parameters are invalid
        if validation_errors:
            validation_progress = create_tool_progress("search_accommodations", {"destination": destination}, "failed")
            validation_progress.error_message = f"Missing required parameters: {', '.join(validation_errors)}"
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.VALIDATION_ERROR,
                message=f"I need more information to search for accommodations. Missing: {', '.join(validation_errors)}",
                overall_progress_message="Accommodation search needs more details",
                is_final_response=False,
                next_expected_input_friendly=f"Please provide: {', '.join(validation_errors)}",
                tool_progress=[validation_progress],
                success=False,
                error_message=f"Missing parameters: {', '.join(validation_errors)}",
                processing_time_seconds=0,
                flight_results=None,
                accommodation_results=None,
                restaurant_results=None,
                attraction_results=None,
                itinerary=None,
                estimated_costs=None,
                recommendations=None,
                session_metadata=None
            )
        
        print(f"🏨 Direct accommodation search: {destination} | {departure_date} to {return_date} | {passengers} guests, {rooms} rooms")
        
        try:
            # Map standardized parameters to accommodation search function
            return search_accommodations_direct(destination, departure_date, return_date, passengers, rooms, platform_preference)
            
        except Exception as e:
            print(f"❌ Direct accommodation search failed: {str(e)}")
            
            # Create error response
            accommodation_progress = create_tool_progress("search_accommodations", {"destination": destination}, "failed")
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
                processing_time_seconds=0,
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


# Bedrock AgentCore integration
app = BedrockAgentCoreApp()

# Global memory configuration
MEMORY_ID = None
MEMORY_CLIENT = None

def parse_agent_response(result) -> dict:
    """
    Parse agent response and return clean JSON for all response types
    
    Handles: flights, accommodations, restaurants, itinerary, conversation
    Returns clean JSON structure for frontend consumption
    """
    try:
        if not hasattr(result, 'message') or not result.message:
            logger.error("No message found in agent result")
            return {
                "response_type": "conversation",
                "response_status": "system_error",
                "message": "I encountered an internal error. Please try again.",
                "success": False,
                "error": "No message in agent result"
            }
        
        # Extract content from AgentResult message
        content = result.message.get('content')
        
        if isinstance(content, list) and len(content) > 0:
            # Get text from first content item
            text_content = content[0].get('text', '') if isinstance(content[0], dict) else str(content[0])
        elif isinstance(content, str):
            text_content = content
        else:
            text_content = str(content)
        
        # Remove thinking tags and extract JSON
        if '<thinking>' in text_content and '</thinking>' in text_content:
            import re
            text_content = re.sub(r'<thinking>.*?</thinking>', '', text_content, flags=re.DOTALL).strip()
        
        # Find and parse JSON in the cleaned content
        if text_content.strip().startswith('{') and text_content.strip().endswith('}'):
            try:
                json_response = json.loads(text_content.strip())
                logger.info(f"✅ Successfully parsed {json_response.get('response_type', 'unknown')} response")
                return json_response
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse JSON: {e}")
                return {
                    "response_type": "conversation",
                    "response_status": "system_error", 
                    "message": "I encountered an error processing your request. Please try again.",
                    "success": False,
                    "error": f"JSON parsing failed: {str(e)}"
                }
        else:
            # Handle non-JSON responses (fallback to conversation)
            logger.warning(f"No valid JSON found in agent response, treating as conversation")
            return {
                "response_type": "conversation",
                "response_status": "complete_success",
                "message": text_content or "I encountered an error processing your request.",
                "success": True,
                "is_final_response": True,
                "overall_progress_message": "Response completed",
                "tool_progress": []
            }
            
    except Exception as e:
        logger.error(f"❌ Error parsing agent response: {e}")
        return {
            "response_type": "conversation",
            "response_status": "system_error",
            "message": "I encountered an internal error. Please try again.",
            "success": False,
            "error": f"Response parsing failed: {str(e)}"
        }

def initialize_memory(region: str = "us-east-1") -> Optional[str]:
    """Initialize shared short-term memory resource for travel planning"""
    global MEMORY_ID, MEMORY_CLIENT
    
    if MEMORY_ID:
        return MEMORY_ID
    
    try:
        MEMORY_CLIENT = MemoryClient(region_name=region)
        
        # Check if memory_id exists in global variable or from SSM
        memory_id_from_ssm = get_parameter('/travel-agent/memory-resource-id')
        if memory_id_from_ssm:
            try:
                # Verify the memory resource still exists
                MEMORY_CLIENT.get_memory(memoryId=memory_id_from_ssm)
                MEMORY_ID = memory_id_from_ssm
                logger.info(f"✅ Using existing memory from SSM: {MEMORY_ID}")
                return MEMORY_ID
            except Exception as e:
                logger.warning(f"⚠️  Memory ID from SSM is invalid: {e}")
        
        # Create new memory for short-term conversation context only
        logger.info("Creating new short-term memory resource...")
        memory = MEMORY_CLIENT.create_memory_and_wait(
            name="TravelOrchestratorMemory",
            description="Travel Orchestrator short-term memory for conversation context",
            strategies=[],  # Required parameter - empty list for basic short-term memory
            event_expiry_days=1,
            max_wait=300,
            poll_interval=10
        )
        
        MEMORY_ID = memory['id']
        logger.info(f"✅ Created new short-term memory: {MEMORY_ID}")
        
        # Store in SSM for future use
        try:
            ssm = boto3.client('ssm')
            ssm.put_parameter(
                Name='/travel-agent/memory-resource-id',
                Value=MEMORY_ID,
                Type='String',
                Description='Travel orchestrator short-term memory resource ID',
                Overwrite=True
            )
            logger.info(f"✅ Stored memory ID in SSM parameter store")
        except Exception as e:
            logger.warning(f"⚠️  Could not store memory ID in SSM: {e}")
        
        return MEMORY_ID
        
    except Exception as e:
        logger.error(f"Failed to initialize memory: {e}")
        return None

@app.entrypoint
def travel_orchestrator_invocation(payload, context=None):
    """Travel orchestrator entry point for AgentCore Runtime - Non-streaming JSON response"""
    if "prompt" not in payload:
        return {"error": "Missing 'prompt' in payload"}
    
    try:
        region = payload.get("region", "us-east-1")
        
        # Extract session ID from AgentCore context (from HTTP header)
        session_id = None
        if context and hasattr(context, 'session_id'):
            session_id = context.session_id
            logger.info(f"✅ Extracted session ID from AgentCore context: {session_id}")
        
        # Generate session IDs if still not provided
        if not session_id:
            session_id = generate_session_ids()
            logger.info(f"🆔 Generated new session ID: {session_id}")
        else:
            logger.info(f"🔄 Continuing existing session: {session_id}")

        actor_id = "travel-orchestrator"
        
        logger.info(f'🚀 Starting travel orchestration - User: {actor_id}, Session: {session_id}')
        print(f'🚀 Starting travel orchestration - User: {actor_id}, Session: {session_id}')
        
        # Initialize memory (optional - agent works without it)
        memory_id = initialize_memory(region=region)
        
        # Create agent instance with session-specific configuration
        agent = TravelOrchestratorAgent(
            memory_id=memory_id,
            session_id=session_id if isinstance(session_id, str) else str(session_id) if session_id else "anonymous",
            actor_id=actor_id,
            region=region
        )
        
        logger.info(f'📝 Processing prompt: {payload["prompt"][:100]}...')
        
        # Get complete response from agent (non-streaming)
        result = agent(payload["prompt"])
        
        logger.info(f'✅ Agent completed processing')
        
        # Use the new parse_agent_response function to handle all response types
        return parse_agent_response(result)
            
    except Exception as e:
        logger.error(f"Error in travel orchestrator: {str(e)}")
        return {
            "error": f"Travel orchestrator failed: {str(e)}",
            "response_type": "conversation",
            "response_status": "tool_error",
            "message": "I encountered an internal error. Please try again.",
            "success": False
        }


if __name__ == "__main__":
    app.run()
