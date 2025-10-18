"""
Travel Orchestrator Agent - Main conversational interface for travel planning
"""
import os
import json
import threading
import time
from datetime import datetime
from typing import List, Optional
from queue import Queue, Empty

import boto3
import logging
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from tools.flight_search_tool import search_flights_direct
from tools.accommodation_search_tool import search_accommodations_direct
from tools.memory_hooks import TravelMemoryHook, generate_session_ids
from tools.streaming_hooks import StreamingProgressHook

# Import new unified response models from centralized common location
from common.models.orchestrator_models import (
    TravelOrchestratorResponse, ResponseType, ResponseStatus, create_tool_progress,
)

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
                 actor_id: Optional[str] = None, region: str = "us-east-1", 
                 streaming_hook: Optional[StreamingProgressHook] = None):
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
        
        # Collect all hooks
        all_hooks = []
        if memory_hooks:
            all_hooks.append(memory_hooks)
        if streaming_hook:
            all_hooks.append(streaming_hook)
            logger.info("✅ Streaming hook added to agent")
        
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
        
        # Configure model with increased max_tokens to prevent truncation and enable prompt caching
        # Model ID is configurable via BEDROCK_MODEL_ID environment variable
        model_id = os.getenv('BEDROCK_MODEL_ID', 'us.amazon.nova-premier-v1:0')
        logger.info(f"Using Bedrock model: {model_id}")
        
        model = BedrockModel(
            model_id=model_id,
            max_tokens=10000,  # Increased from default ~4096 to handle large JSON responses
            temperature=0.7,
            cache_prompt="default",  # Enable caching for system prompt to reduce costs (Nova uses "default")
        )
        
        super().__init__(
            model=model,
            tools=all_tools,
            system_prompt=self._build_system_prompt(current_datetime, current_date),
            hooks=all_hooks,
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
        """Build optimized system prompt for travel orchestration with clear structure and reduced verbosity"""
        return f"""You are an Expert Travel Planning Agent coordinating flights, accommodations, restaurants, and attractions.
Current date: {current_datetime} | Today: {current_date}

═══════════════════════════════════════════════════════════════════════════════
⚠️ ABSOLUTE REQUIREMENT - NO EXCEPTIONS ⚠️
═══════════════════════════════════════════════════════════════════════════════
YOU ARE A JSON API. YOUR ENTIRE RESPONSE IS THE JSON OBJECT ITSELF.

✓ START YOUR RESPONSE WITH: {{
✓ END YOUR RESPONSE WITH: }}
✓ Output ONLY the JSON object - nothing before, nothing after
✓ Use the TravelOrchestratorResponse schema (provided at end)

❌ FORBIDDEN - These patterns will cause SYSTEM FAILURE:
✗ Wrapping JSON in ```json ``` markdown code blocks
✗ Putting JSON text inside "message" field when you have structured results
✗ Starting response with explanatory text before the JSON
✗ Adding any text after the closing }}
✗ Using response_type="conversation" when you have flight_results/restaurant_results/etc

PRE-FLIGHT CHECKLIST (verify before responding):
□ Response starts with {{ (no text before)
□ Response ends with }} (no text after)
□ No markdown code blocks (no ```)
□ response_type matches data type (flights → "flights", not "conversation")
□ Structured data in proper arrays (flight_results, restaurant_results, etc)

═══════════════════════════════════════════════════════════════════════════════
🛠️ AVAILABLE TOOLS
═══════════════════════════════════════════════════════════════════════════════

1. search_flights(origin, destination, departure_date, return_date?, adults=1, children=0, 
                  infants=0, travel_class?, non_stop=false, max_price?, max_results=50)
   → Returns TravelOrchestratorResponse with flight_results array

2. search_accommodations(destination, departure_date, return_date, passengers=2, 
                         rooms=1, platform_preference="both")
   → Returns TravelOrchestratorResponse with accommodation_results array

3. searchPlacesByText(textQuery, includedType?, maxResultCount?, minRating?, 
                      priceLevels?, location?)
   → Google Places API - USE FOR: restaurants, attractions, POIs
   → YOU must parse results into RestaurantResult or AttractionResult objects

4. searchNearbyPlaces / getPlaceDetails
   → Additional Google Places tools for nearby searches and details

═══════════════════════════════════════════════════════════════════════════════
🎯 REQUEST CLASSIFICATION & RESPONSE TYPE LOGIC
═══════════════════════════════════════════════════════════════════════════════

ANALYZE USER REQUEST → CLASSIFY → SET CORRECT response_type:

┌─────────────────────────────────────────────────────────────────────────────┐
│ REQUEST TYPE              │ ACTION                │ response_type           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Single component requests │ Call 1 tool, return   │ "flights"               │
│ "best flight to Paris"    │ 1-10 results          │ "accommodations"        │
│ "hotels under $200"       │                       │ "restaurants"           │
│ "Italian restaurants"     │                       │ "attractions"           │
│ "museums in Rome"         │                       │                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Multi-component requests  │ Call 2+ tools,        │ "mixed_results"         │
│ "flights + hotels"        │ return combined data  │                         │
│ "restaurants + attractions"│                      │                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Complete trip planning    │ Call all tools,       │ "itinerary"             │
│ "plan my 5-day trip"      │ build day-by-day plan │                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Questions, clarifications,│ No tool calls needed  │ "conversation"          │
│ errors, missing params    │                       │                         │
└─────────────────────────────────────────────────────────────────────────────┘

⚠️ CRITICAL RESPONSE_TYPE VALIDATION RULES (NEVER VIOLATE):

✓ IF restaurant_results has data → response_type = "restaurants" or "mixed_results"
✓ IF attraction_results has data → response_type = "attractions" or "mixed_results"
✓ IF flight_results has data → response_type = "flights" or "mixed_results"
✓ IF accommodation_results has data → response_type = "accommodations" or "mixed_results"

✗ NEVER use response_type="conversation" when ANY structured results exist
✗ NEVER put structured data only in message field

═══════════════════════════════════════════════════════════════════════════════
🔧 GOOGLE PLACES API INTEGRATION
═══════════════════════════════════════════════════════════════════════════════

RESTAURANT SEARCHES:
→ Use searchPlacesByText(textQuery="Italian restaurants in Paris", includedType="restaurant")
→ Parse API response into RestaurantResult objects: {{name, address, rating, user_rating_count, 
  price_level, phone_number, website_uri, is_open_now, types, place_id}}
→ Store in restaurant_results array
→ Set response_type="restaurants"

ATTRACTION SEARCHES (museums, parks, landmarks, sightseeing, tourist attractions):
→ Use searchPlacesByText(textQuery="museums in Rome", includedType="tourist_attraction")
→ Parse API response into AttractionResult objects: {{name, place_id, formatted_address, 
  rating, user_ratings_total, price_level, types, opening_hours, website, visit_duration_estimate}}
→ Estimate visit_duration_estimate: museums=120min, parks=60min, landmarks=30min
→ Store in attraction_results array
→ Set response_type="attractions"

⚠️ CRITICAL: Parse Google Places results into structured Pydantic objects, NOT text in message

═══════════════════════════════════════════════════════════════════════════════
📋 RESPONSE STRUCTURE EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

SINGLE COMPONENT (choose appropriate response_type):
{{
  "response_type": "restaurants",  // or "flights", "accommodations", "attractions"
  "response_status": "complete_success",
  "message": "Found 5 Italian restaurants in Rome.",
  "restaurant_results": [{{...}}],  // Populated array for the component type
  "success": true,
  "is_final_response": true,
  "overall_progress_message": "Search completed"
}}

MIXED COMPONENTS (multiple result types):
{{
  "response_type": "mixed_results",
  "message": "Found flights, hotels, and restaurants for your Paris trip.",
  "flight_results": [{{...}}],
  "accommodation_results": [{{...}}],
  "restaurant_results": [{{...}}],
  "success": true
}}

COMPLETE ITINERARY (day-by-day plan):
{{
  "response_type": "itinerary",
  "message": "Created your 7-day Paris itinerary.",
  "itinerary": {{
    "trip_title": "7-Day Paris Adventure",
    "daily_itineraries": [
      {{
        "day_number": 1,
        "date": "2024-06-15",
        "activities": [
          {{"activity_type": "flight", "activity_details": {{...}}, ...}},
          {{"activity_type": "restaurant", "activity_details": {{...}}, ...}}
        ]
      }}
    ]
  }},
  "success": true
}}

CONVERSATION (questions, errors, clarifications - ONLY when no structured results):
{{
  "response_type": "conversation",
  "response_status": "requesting_info",
  "message": "I need more details. What's your departure city?",
  "success": true,
  "is_final_response": false
}}

❌ ANTI-PATTERN - NEVER DO THIS:
{{
  "response_type": "conversation",
  "message": "```json\\n{{ \\"response_type\\": \\"flights\\" }}\\n```"  // ❌ FORBIDDEN
}}

✓ CORRECT PATTERN - DO THIS INSTEAD:
{{
  "response_type": "flights",  // ✓ Direct JSON object
  "message": "Found 6 flights from NYC to Paris.",
  "flight_results": [...]
}}

═══════════════════════════════════════════════════════════════════════════════
⚙️ OPERATIONAL RULES
═══════════════════════════════════════════════════════════════════════════════

TOOL CALLING PREREQUISITES:
✓ Have ALL required parameters with valid values before calling any tool
✓ Dates must be YYYY-MM-DD format (not "next week" or relative terms)
✓ Airport codes must be IATA codes (JFK/LAX, not "New York"/"Los Angeles")
✓ No past dates (except today: {current_date})
✓ Return date must be after departure date
✗ If ANY required param is missing/invalid → Ask user for clarification (conversation response)

PARAMETER VALIDATION:
• search_flights: origin, destination, departure_date required | adults 1-9 total passengers
• search_accommodations: destination, departure_date, return_date required | 1-30 guests, 1-8 rooms
• searchPlacesByText: textQuery required | Use includedType for better filtering

CONVERSATION CONTEXT:
→ Use previous messages to infer missing details when reasonable
→ Don't repeatedly ask for information already provided
→ If user says "next Friday", calculate actual date from today ({current_date})

═══════════════════════════════════════════════════════════════════════════════
📄 FULL RESPONSE SCHEMA
═══════════════════════════════════════════════════════════════════════════════
{TravelOrchestratorResponse.model_json_schema()}"""


    @tool
    def search_flights(
        self, 
        origin: str, 
        destination: str, 
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        travel_class: Optional[str] = None,
        non_stop: bool = False,
        max_price: Optional[int] = None,
        max_results: int = 50
    ) -> TravelOrchestratorResponse:
        """
        Search for flights using Amadeus API with comprehensive filtering options
        
        Args:
            origin: Origin airport IATA code (e.g., 'JFK', 'LAX')
            destination: Destination airport IATA code (e.g., 'CDG', 'LHR')
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date for round-trip (optional, YYYY-MM-DD format)
            adults: Number of adult travelers (age 12+), default 1, max 9
            children: Number of child travelers (age 2-11), default 0
            infants: Number of infant travelers (under 2), default 0
            travel_class: Cabin class - "ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"
            non_stop: If True, only return direct flights with no stops
            max_price: Maximum price per traveler in USD (filters expensive options)
            max_results: Maximum number of flight offers to return (default 50)
        
        Returns:
            TravelOrchestratorResponse with all matching flight results
        """
        # Validate total passenger count
        total_passengers = adults + children + infants
        if total_passengers < 1 or total_passengers > 9:
            validation_progress = create_tool_progress("search_flights", {"origin": origin, "destination": destination}, "failed")
            validation_progress.error_message = f"Total passengers must be between 1-9 (got {total_passengers})"
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.VALIDATION_ERROR,
                message=f"Total passengers (adults + children + infants) must be between 1-9. You specified {total_passengers} total passengers.",
                overall_progress_message="Flight search needs valid passenger count",
                is_final_response=False,
                next_expected_input_friendly="Please provide valid passenger counts",
                tool_progress=[validation_progress],
                success=False,
                error_message=f"Invalid passenger count: {total_passengers}",
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
        
        # Validate infants don't exceed adults
        if infants > adults:
            validation_progress = create_tool_progress("search_flights", {"origin": origin, "destination": destination}, "failed")
            validation_progress.error_message = f"Infants ({infants}) cannot exceed adults ({adults})"
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.VALIDATION_ERROR,
                message=f"Number of infants ({infants}) cannot exceed number of adults ({adults}). Each infant must be accompanied by an adult.",
                overall_progress_message="Flight search needs valid passenger distribution",
                is_final_response=False,
                next_expected_input_friendly="Please adjust passenger counts",
                tool_progress=[validation_progress],
                success=False,
                error_message=f"Infants exceed adults: {infants} > {adults}",
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
            print(f"   Return: {return_date} | Passengers: {total_passengers} (Adults: {adults}, Children: {children}, Infants: {infants})")
        
        try:
            # Call the direct flight search tool with all new parameters
            return search_flights_direct(
                origin=origin,
                destination=destination, 
                departure_date=departure_date,
                return_date=return_date,
                adults=adults,
                children=children,
                infants=infants,
                travel_class=travel_class,
                non_stop=non_stop,
                max_price=max_price,
                max_results=max_results
            )
            
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

def format_ndjson_event(event_type: str, data: dict) -> str:
    """
    Format data as NDJSON (Newline Delimited JSON)
    
    Args:
        event_type: Type of event
        data: Data to send in the event
        
    Returns:
        NDJSON formatted string
    """
    event = {
        "type": event_type,
        "data": data
    }
    return json.dumps(event) + "\n"


def stream_agent_execution(payload, context):
    """
    Generator function that yields SSE events during agent execution
    
    Args:
        payload: Request payload containing prompt
        context: AgentCore runtime context
        
    Yields:
        SSE formatted events as strings
    """
    event_queue = Queue()
    final_result = {}
    
    try:
        region = payload.get("region", "us-east-1")
        
        # Extract session ID from AgentCore context
        session_id = None
        if context and hasattr(context, 'session_id'):
            session_id = context.session_id
            logger.info(f"✅ Extracted session ID from AgentCore context: {session_id}")
        
        # Generate session IDs if not provided
        if not session_id:
            session_id = generate_session_ids()
            logger.info(f"🆔 Generated new session ID: {session_id}")
        
        actor_id = "travel-orchestrator"
        
        # Emit initial thinking event
        yield format_ndjson_event("status", {
            "message": "Analyzing your request...",
            "status": "thinking"
        })
        
        logger.info(f'🚀 Starting streaming travel orchestration - User: {actor_id}, Session: {session_id}')
        
        # Initialize memory (optional)
        memory_id = initialize_memory(region=region)
        
        # Create and add streaming hook
        streaming_hook = StreamingProgressHook(event_queue)
        
        # Create agent instance with streaming hook
        agent = TravelOrchestratorAgent(
            memory_id=memory_id,
            session_id=session_id if isinstance(session_id, str) else str(session_id) if session_id else "anonymous",
            actor_id=actor_id,
            region=region,
            streaming_hook=streaming_hook
        )
        
        logger.info(f'📝 Processing prompt with streaming: {payload["prompt"][:100]}...')
        
        # Run agent in background thread
        def run_agent():
            try:
                final_result['data'] = agent(payload["prompt"])
                final_result['success'] = True
            except Exception as e:
                final_result['error'] = str(e)
                final_result['success'] = False
                logger.error(f"❌ Agent execution failed: {e}")
        
        agent_thread = threading.Thread(target=run_agent, daemon=True)
        agent_thread.start()
        
        # Stream events as they come in
        while agent_thread.is_alive() or not event_queue.empty():
            try:
                # Get event from queue with timeout
                event = event_queue.get(timeout=0.2)
                yield format_ndjson_event(event["event"], event["data"])
            except Empty:
                continue
        
        # Wait for agent to complete
        agent_thread.join()
        
        # Emit final response
        if final_result.get('success'):
            response = parse_agent_response(final_result['data'])
            yield format_ndjson_event("final_response", response)
            logger.info(f"✅ Streaming orchestration completed successfully")
        else:
            error_response = {
                "response_type": "conversation",
                "response_status": "system_error", 
                "message": "I encountered an internal error. Please try again.",
                "success": False,
                "error": final_result.get('error', 'Unknown error')
            }
            yield format_ndjson_event("error", error_response)
            logger.error(f"❌ Streaming orchestration failed: {final_result.get('error')}")
            
    except Exception as e:
        logger.error(f"❌ Fatal error in stream_agent_execution: {e}")
        error_response = {
            "response_type": "conversation",
            "response_status": "system_error",
            "message": "I encountered a critical error. Please try again.",
            "success": False,
            "error": str(e)
        }
        yield format_ndjson_event("error", error_response)


@app.entrypoint
def travel_orchestrator_invocation(payload, context=None):
    """Travel orchestrator entry point for AgentCore Runtime - NDJSON Streaming Response"""
    if "prompt" not in payload:
        error_response = {"error": "Missing 'prompt' in payload"}
        return format_ndjson_event("error", error_response)
    
    # Return streaming generator for all requests
    return stream_agent_execution(payload, context)


# @app.entrypoint  
# def travel_orchestrator_invocation_legacy(payload, context=None):
#     """Travel orchestrator entry point for AgentCore Runtime - Non-streaming JSON response (legacy)"""
#     if "prompt" not in payload:
#         return {"error": "Missing 'prompt' in payload"}
    
#     try:
#         region = payload.get("region", "us-east-1")
        
#         # Extract session ID from AgentCore context (from HTTP header)
#         session_id = None
#         if context and hasattr(context, 'session_id'):
#             session_id = context.session_id
#             logger.info(f"✅ Extracted session ID from AgentCore context: {session_id}")
        
#         # Generate session IDs if still not provided
#         if not session_id:
#             session_id = generate_session_ids()
#             logger.info(f"🆔 Generated new session ID: {session_id}")
#         else:
#             logger.info(f"🔄 Continuing existing session: {session_id}")

#         actor_id = "travel-orchestrator"
        
#         logger.info(f'🚀 Starting travel orchestration - User: {actor_id}, Session: {session_id}')
#         print(f'🚀 Starting travel orchestration - User: {actor_id}, Session: {session_id}')
        
#         # Initialize memory (optional - agent works without it)
#         memory_id = initialize_memory(region=region)
        
#         # Create agent instance with session-specific configuration
#         agent = TravelOrchestratorAgent(
#             memory_id=memory_id,
#             session_id=session_id if isinstance(session_id, str) else str(session_id) if session_id else "anonymous",
#             actor_id=actor_id,
#             region=region
#         )
        
#         logger.info(f'📝 Processing prompt: {payload["prompt"][:100]}...')
        
#         # Get complete response from agent (non-streaming)
#         result = agent(payload["prompt"])
        
#         logger.info(f'✅ Agent completed processing')
        
#         # Use the new parse_agent_response function to handle all response types
#         return parse_agent_response(result)
            
#     except Exception as e:
#         logger.error(f"Error in travel orchestrator: {str(e)}")
#         return {
#             "error": f"Travel orchestrator failed: {str(e)}",
#             "response_type": "conversation",
#             "response_status": "tool_error",
#             "message": "I encountered an internal error. Please try again.",
#             "success": False
#         }


if __name__ == "__main__":
    app.run()
