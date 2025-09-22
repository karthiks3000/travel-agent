"""
Travel Orchestrator Agent - Main conversational interface for travel planning
"""
import os
import json
import asyncio
import uuid
from datetime import datetime, date
from typing import Dict, Any, List, Optional

import boto3
import logging
from strands import Agent, tool
from strands.hooks import HookRegistry
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from common.models.travel_models import (
    TravelInformation, ValidationResult, AgentSearchResult, 
    ComprehensiveTravelPlan, ConversationContext
)
from common.models.base_models import TripType, BudgetCategory
from tools.validation_tools import (
    validate_travel_requirements, validate_dates, infer_missing_dates
)
from tools.flight_search_tool import search_flights_direct
from tools.accommodation_search_tool import search_accommodations_direct
from tools.memory_hooks import TravelMemoryHook, generate_session_ids

# Import new unified response models from centralized common location
from common.models.orchestrator_models import (
    TravelOrchestratorResponse, ResponseType, ResponseStatus, 
    ToolProgress, AgentResponseParser, create_tool_progress
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
    def __init__(self, memory_id: str = None, session_id: str = None, 
                 actor_id: str = None, region: str = "us-east-1"):
        """
        Initialize Travel Orchestrator Agent with memory integration
        
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
        
        logger.info(f"Initializing Travel Orchestrator - Session: {session_id}, Actor: {actor_id}")
        
        # Initialize Nova Act API key as environment variable for tools
        self._initialize_nova_act_api_key()
        
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
        
        # Initialize agent state for memory hooks
        agent_state = {
            "actor_id": actor_id,
            "session_id": session_id,
            "agent_type": "travel_orchestrator"
        }
        
        super().__init__(
            model="us.amazon.nova-premier-v1:0",
            tools=[
                self.search_flights,
                self.search_accommodations, 
                self.search_restaurants
            ],
            system_prompt=self._build_system_prompt(current_datetime, current_date),
            hooks=[memory_hooks] if memory_hooks else [],
            state=agent_state
        )
    
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
    
    def _validate_restaurant_params(self, destination: str) -> List[str]:
        """
        Validate restaurant search parameters
        
        Returns:
            List of error messages (empty if all parameters are valid)
        """
        missing_params = []
        
        # Required parameters
        if not destination or destination.strip() == "":
            missing_params.append("destination")
        
        return missing_params

    def _build_system_prompt(self, current_datetime: str, current_date: str) -> str:
        """Build focused system prompt for travel orchestration with JSON response format"""
        return f"""You are a Travel Orchestrator Agent for travel planning. Current date: {current_datetime}

YOUR ROLE: Coordinate specialist agents (flights, accommodations, restaurants) based on what users specifically request.

**CRITICAL: YOU MUST ALWAYS RESPOND IN JSON FORMAT USING TravelOrchestratorResponse. NEVER PROVIDE PLAIN TEXT RESPONSES.**

**CRITICAL: ONLY CALL TOOLS WHEN YOU HAVE ALL REQUIRED ARGUMENTS. DO NOT CALL TOOLS WITH MISSING OR INVALID PARAMETERS.**

TOOL PARAMETER REQUIREMENTS:

search_flights:
- origin: REQUIRED - Must be a city name or airport code (e.g., "New York", "Toronto", "JFK")
- destination: REQUIRED - Must be a city name or airport code (e.g., "Paris", "London", "CDG") 
- departure_date: REQUIRED - Must be in YYYY-MM-DD format (e.g., "2024-10-15")
- return_date: OPTIONAL - Must be in YYYY-MM-DD format, after departure_date
- passengers: OPTIONAL - Defaults to 1, must be 1-9

search_accommodations:
- destination: REQUIRED - Must be a city name (e.g., "Paris", "Tokyo")
- departure_date: REQUIRED - Check-in date in YYYY-MM-DD format
- return_date: REQUIRED - Check-out date in YYYY-MM-DD format, after departure_date
- passengers: OPTIONAL - Defaults to 2, must be 1-30 (number of guests)
- rooms: OPTIONAL - Defaults to 1, must be 1-8

search_restaurants:
- destination: REQUIRED - Must be a city name (e.g., "Paris", "Tokyo")

TOOL CALLING RULES:
1. **ONLY call tools when you have ALL required parameters with valid values**
2. **Origin/destination MUST be actual city names or airport codes** (not generic terms like "there" or "home"). if not provided ask the user for the city name instead of assuming one.
3. **Dates MUST be in proper YYYY-MM-DD format** (not relative terms like "next week")
4. **If any required parameter is missing or invalid, ask the user for clarification instead of calling the tool**
5. **Use conversation context to fill in missing details when possible**

TOOL SELECTION RULES (Listen to what user asks for):
- "flights" or "flight" → search_flights ONLY (if all required params available)
- "hotels", "accommodations", "places to stay" → search_accommodations ONLY (if all required params available)
- "restaurants", "food", "dining" → search_restaurants ONLY (if destination available)
- "trip", "plan", "itinerary", "vacation", "complete travel plan" → CALL MULTIPLE TOOLS (if params available for each tool)

MULTI-TOOL EXECUTION: When users request comprehensive planning, call all relevant tools that have sufficient parameters.

PARAMETER INFERENCE: Use conversation context to infer missing parameters, but only call tools when you have complete, valid parameter sets.

MANDATORY JSON RESPONSE FORMAT - ALL responses must use TravelOrchestratorResponse structure:

When asking for information:

{{
  "response_type": "conversation",
  "response_status": "requesting_info", 
  "message": "I need your departure city and travel dates to search for flights.",
  "overall_progress_message": "Waiting for travel details",
  "is_final_response": false,
  "next_expected_input_friendly": "Please provide departure city and travel dates",
  "tool_progress": [],
  "success": true
}}


When single tool completes successfully:

{{
  "response_type": "flights",
  "response_status": "complete_success",
  "message": "Found 12 flight options for your NYC to Paris trip.",
  "overall_progress_message": "Flight search completed successfully", 
  "is_final_response": true,
  "tool_progress": [{{
    "tool_id": "search_flights",
    "display_name": "Finding flights",
    "description": "Searching for flights from NYC to Paris",
    "status": "completed",
    "result_preview": "Found 12 flight options starting at $245"
  }}],
  "flight_results": {{ ... }},
  "estimated_costs": {{"flights": 490}},
  "processing_time_seconds": 15.2,
  "success": true
}}


When multiple tools complete (comprehensive planning):

{{
  "response_type": "itinerary",
  "response_status": "complete_success",
  "message": "Created your complete travel plan with flights, accommodations, and restaurant recommendations.",
  "overall_progress_message": "Complete travel plan generated successfully", 
  "is_final_response": true,
  "tool_progress": [
    {{
      "tool_id": "search_flights",
      "display_name": "Finding flights",
      "status": "completed",
      "result_preview": "Found 8 flight options"
    }},
    {{
      "tool_id": "search_accommodations", 
      "display_name": "Finding accommodations",
      "status": "completed",
      "result_preview": "Found 15 hotel options"
    }},
    {{
      "tool_id": "search_restaurants",
      "display_name": "Finding restaurants", 
      "status": "completed",
      "result_preview": "Found 12 restaurant recommendations"
    }}
  ],
  "flight_results": {{ ... }},
  "accommodation_results": {{ ... }},
  "restaurant_results": {{ ... }},
  "processing_time_seconds": 45.8,
  "success": true
}}


When tool fails:
{{
  "response_type": "conversation",
  "response_status": "tool_error",
  "message": "I couldn't find flights for those dates. Please try different dates or check the details.",
  "overall_progress_message": "Flight search failed",
  "is_final_response": true,
  "tool_progress": [{{
    "tool_id": "search_flights", 
    "display_name": "Finding flights",
    "status": "failed",
    "error_message": "No flights available for selected dates"
  }}],
  "success": false,
  "error_message": "Flight search returned no results"
}}


CONVERSATION CONTEXT: Remember previous messages to avoid asking for information already provided.
VALIDATION: Reject past dates (before {current_date}). Today is acceptable.
REMEMBER: Always respond in JSON using TravelOrchestratorResponse format. For comprehensive requests, call multiple tools and let Strands handle concurrent execution."""


    @tool
    def search_flights(self, origin: str, destination: str, departure_date: str, 
                      return_date: Optional[str] = None, passengers: int = 1) -> TravelOrchestratorResponse:
        """
        Search for flights using direct browser automation tools
        
        Args:
            origin: Origin airport code or city (e.g., 'JFK', 'New York')
            destination: Destination airport code or city (e.g., 'LAX', 'Los Angeles') 
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
                processing_time_seconds=0
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
                processing_time_seconds=0
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
                processing_time_seconds=0
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
                processing_time_seconds=0
            )

    @tool
    def search_restaurants(self, destination: str) -> TravelOrchestratorResponse:
        """
        Search for restaurants using standardized parameters
        
        Args:
            destination: Destination city for restaurant search
        
        Returns:
            TravelOrchestratorResponse with restaurant search results or validation error
        """
        # Validate parameters using dedicated validation method
        validation_errors = self._validate_restaurant_params(destination)
        
        # Return validation error if parameters are invalid
        if validation_errors:
            validation_progress = create_tool_progress("search_restaurants", {"destination": destination}, "failed")
            validation_progress.error_message = f"Missing required parameters: {', '.join(validation_errors)}"
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.VALIDATION_ERROR,
                message=f"I need more information to search for restaurants. Missing: {', '.join(validation_errors)}",
                overall_progress_message="Restaurant search needs more details",
                is_final_response=False,
                next_expected_input_friendly=f"Please provide: {', '.join(validation_errors)}",
                tool_progress=[validation_progress],
                success=False,
                error_message=f"Missing parameters: {', '.join(validation_errors)}",
                processing_time_seconds=0
            )
        
        print(f"🍽️  Restaurant search requested for: {destination}")
        
        # Create progress tracking for this tool
        restaurant_progress = create_tool_progress(
            "search_restaurants", 
            {"destination": destination}, 
            "failed"
        )
        restaurant_progress.error_message = "Restaurant search not yet implemented in direct tool architecture"
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.CONVERSATION,
            response_status=ResponseStatus.TOOL_ERROR,
            message="Restaurant search functionality is currently being refactored. Please focus on flight and accommodation searches for now.",
            overall_progress_message="Restaurant search not yet available",
            is_final_response=True,
            tool_progress=[restaurant_progress],
            success=False,
            error_message="Restaurant search not yet implemented in direct tool architecture",
            processing_time_seconds=0
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

def initialize_memory(region: str = "us-east-1") -> str:
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
        
        # Initialize memory (optional - agent works without it)
        memory_id = initialize_memory(region=region)
        
        # Create agent instance with session-specific configuration
        agent = TravelOrchestratorAgent(
            memory_id=memory_id,
            session_id=session_id,
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
