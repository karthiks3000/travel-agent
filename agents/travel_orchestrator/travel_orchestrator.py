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
from tools.agent_invocation import AgentInvoker, format_travel_request
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
        
        # Get specialist agent ARNs from Parameter Store
        flight_agent_arn = self._get_specialist_agent_arn('FLIGHT_AGENT_ARN', '/travel-agent/flight-agent-arn')
        accommodation_agent_arn = self._get_specialist_agent_arn('ACCOMMODATION_AGENT_ARN', '/travel-agent/accommodation-agent-arn')
        food_agent_arn = self._get_specialist_agent_arn('FOOD_AGENT_ARN', '/travel-agent/food-agent-arn')
        
        # Initialize agent invoker with specialist agent ARNs
        self.agent_invoker = AgentInvoker(
            flight_agent_arn=flight_agent_arn,
            accommodation_agent_arn=accommodation_agent_arn,
            food_agent_arn=food_agent_arn,
            region=region
        )
        if self.agent_invoker:
            logger.info(f"AgentInvoker initialized")

        
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
            model="amazon.nova-pro-v1:0",
            tools=[
                self.validate_travel_information,
                self.search_flights,
                self.search_accommodations, 
                self.search_restaurants
            ],
            system_prompt=self._build_system_prompt(current_datetime, current_date),
            hooks=[memory_hooks] if memory_hooks else [],
            state=agent_state
        )
    
    def _get_specialist_agent_arn(self, env_var_name: str, ssm_parameter_name: str) -> str:
        """
        Get specialist agent ARN with fallback strategy:
        1. Try SSM Parameter Store (for deployed environment)
        2. Fall back to environment variable (for local development)  
        3. Fall back to placeholder ARN (for error handling)
        
        Args:
            env_var_name: Environment variable name (e.g., 'FLIGHT_AGENT_ARN')
            ssm_parameter_name: SSM parameter name (e.g., '/travel-agent/flight-agent-arn')
            
        Returns:
            Agent ARN string
        """
        # Try SSM Parameter Store first (for deployed environment)
        try:
            arn = get_parameter(ssm_parameter_name)
            if arn:
                logger.info(f"✅ Retrieved {env_var_name} from SSM: {arn}")
                return arn
        except Exception as e:
            logger.warning(f"⚠️  Failed to retrieve {ssm_parameter_name} from SSM: {e}")
        
        # Fall back to environment variable (for local development)
        arn = os.getenv(env_var_name)
        if arn:
            logger.info(f"✅ Retrieved {env_var_name} from environment: {arn}")
            return arn
        
        # Final fallback - placeholder ARN (will cause invocation to fail but with clear error)
        placeholder_arn = f"arn:aws:bedrock-agentcore:us-east-1:000000000000:runtime/{env_var_name.lower().replace('_', '-')}-NOT-CONFIGURED"
        logger.error(f"❌ Could not retrieve {env_var_name} from SSM or environment. Using placeholder: {placeholder_arn}")
        return placeholder_arn
    
    def _build_system_prompt(self, current_datetime: str, current_date: str) -> str:
        """Build focused system prompt for travel orchestration with JSON response format"""
        return f"""You are a Travel Orchestrator Agent for travel planning. Current date: {current_datetime}

YOUR ROLE: Coordinate specialist agents (flights, accommodations, restaurants) based on what users specifically request.

**CRITICAL: YOU MUST ALWAYS RESPOND IN JSON FORMAT USING TravelOrchestratorResponse. NEVER PROVIDE PLAIN TEXT RESPONSES.**

ALWAYS call validate_travel_information before calling search tools.

TOOL SELECTION RULES (Listen to what user asks for):
- "flights" or "flight" → search_flights ONLY
- "hotels", "accommodations", "places to stay" → search_accommodations ONLY  
- "restaurants", "food", "dining" → search_restaurants ONLY
- "trip", "plan", "itinerary", "vacation", "complete travel plan" → CALL MULTIPLE TOOLS (search_flights AND search_accommodations AND search_restaurants) - Strands will execute them concurrently
- Missing info → Ask for ONLY the missing details (not everything at once)

MULTI-TOOL EXECUTION: When users request comprehensive planning (trip, vacation, complete plan), call all relevant tools:
- search_flights for flight options
- search_accommodations for hotel/lodging options  
- search_restaurants for dining recommendations
Strands framework will handle concurrent execution automatically.

REQUIRED INFO BY TOOL:
- search_flights: origin, destination, departure_date, guests (+ return_date if round-trip)
- search_accommodations: destination, departure_date, return_date, guests
- search_restaurants: destination

MANDATORY JSON RESPONSE FORMAT - ALL responses must use TravelOrchestratorResponse structure:

When asking for information:
```json
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
```

When single tool completes successfully:
```json
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
```

When multiple tools complete (comprehensive planning):
```json
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
```

When tool fails:
```json
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
```

CONVERSATION CONTEXT: Remember previous messages to avoid asking for information already provided.
VALIDATION: Reject past dates (before {current_date}). Today is acceptable.
REMEMBER: Always respond in JSON using TravelOrchestratorResponse format. For comprehensive requests, call multiple tools and let Strands handle concurrent execution."""

    @tool
    def validate_travel_information(self, travel_info_dict: dict) -> ValidationResult:
        """
        Validate completeness of travel information for specialist agent calls
        
        Args:
            travel_info_dict: Dictionary containing extracted travel details
        
        Returns:
            ValidationResult with detailed validation analysis
        """
        print(f"🔍 Validating travel information: {travel_info_dict}")
        
        try:
            # Convert dict to TravelInformation model with validation
            travel_info = TravelInformation.model_validate(travel_info_dict)
            
            # Perform date validation
            date_errors = validate_dates(travel_info)
            if date_errors:
                return ValidationResult(
                    validation_summary=f"Date validation failed: {'; '.join(date_errors)}",
                    next_questions=[f"Please provide valid dates. {error}" for error in date_errors[:2]]
                )
            
            # Infer missing information intelligently
            travel_info = infer_missing_dates(travel_info)
            
            # Validate requirements
            result = validate_travel_requirements(travel_info)
            
            print(f"✅ Validation complete: {result.validation_summary}")
            return result
            
        except Exception as e:
            print(f"❌ Validation error: {str(e)}")
            return ValidationResult(
                validation_summary=f"Validation error: {str(e)}",
                next_questions=["Please provide your travel information in a clear format."]
            )

    @tool
    def search_flights(self, travel_request: str, session_id: str = None) -> TravelOrchestratorResponse:
        """
        Search for flights by delegating to flight specialist agent
        
        Args:
            travel_request: Natural language travel request
            session_id: Session ID for context (auto-generated if not provided)
        
        Returns:
            TravelOrchestratorResponse with structured flight results and progress tracking
        """
        if not session_id:
            session_id = self.session_id or str(uuid.uuid4())
        
        start_time = datetime.now()
        print(f"✈️  Searching flights: {travel_request}")
        
        # Create progress tracking for this tool
        flight_progress = create_tool_progress(
            "search_flights", 
            {"origin": "departure city", "destination": "destination city"}, 
            "active"
        )
        
        try:
            # Use simplified agent invocation (now returns Pydantic models directly - sync call)
            flight_results = self.agent_invoker.invoke_flight_agent(travel_request, session_id)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if flight_results:
                # Successfully got structured flight data
                print(f"✅ Flight search complete with structured FlightSearchResults")
                
                # Update progress to completed
                flight_progress.status = "completed"
                flight_progress.result_preview = f"Found {len(getattr(flight_results, 'all_flights', []))} flight options"
                
                return TravelOrchestratorResponse(
                    response_type=ResponseType.FLIGHTS,
                    response_status=ResponseStatus.COMPLETE_SUCCESS,
                    message=f"Found flight options from your request. {flight_results.recommendation if hasattr(flight_results, 'recommendation') else 'Here are the available flights.'}",
                    overall_progress_message="Flight search completed successfully",
                    is_final_response=True,
                    tool_progress=[flight_progress],
                    flight_results=flight_results,
                    processing_time_seconds=processing_time,
                    session_metadata={
                        "session_id": session_id,
                        "agent_type": "flight_specialist"
                    }
                )
            else:
                # Agent failed or returned no structured data
                flight_progress.status = "failed"
                flight_progress.error_message = "No flight results found"
                
                return TravelOrchestratorResponse(
                    response_type=ResponseType.CONVERSATION,
                    response_status=ResponseStatus.TOOL_ERROR,
                    message="I searched for flights but couldn't find any results. Please check your travel details and try again.",
                    overall_progress_message="Flight search completed with no results",
                    is_final_response=True,
                    tool_progress=[flight_progress],
                    success=False,
                    processing_time_seconds=processing_time,
                    session_metadata={
                        "session_id": session_id,
                        "agent_type": "flight_specialist",
                        "response_format": "no_results"
                    }
                )
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"❌ Flight search failed: {str(e)}")
            
            # Update progress to failed
            flight_progress.status = "failed"
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
                processing_time_seconds=processing_time
            )

    @tool
    def search_accommodations(self, travel_request: str, session_id: str = None) -> TravelOrchestratorResponse:
        """
        Search for accommodations by delegating to accommodation specialist agent
        
        Args:
            travel_request: Natural language travel request
            session_id: Session ID for context (auto-generated if not provided)
        
        Returns:
            TravelOrchestratorResponse with structured accommodation results and progress tracking
        """
        if not session_id:
            session_id = self.session_id or str(uuid.uuid4())
        
        start_time = datetime.now()
        print(f"🏨 Searching accommodations: {travel_request}")
        
        # Create progress tracking for this tool
        accommodation_progress = create_tool_progress(
            "search_accommodations", 
            {"destination": "destination city"}, 
            "active"
        )
        
        try:
            # Use simplified agent invocation (now returns Pydantic models directly - sync call)
            accommodation_results = self.agent_invoker.invoke_accommodation_agent(travel_request, session_id)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if accommodation_results:
                # Successfully got structured accommodation data
                print(f"✅ Accommodation search complete with structured AccommodationAgentResponse")
                
                # Update progress to completed
                accommodation_progress.status = "completed"
                accommodation_count = len(getattr(accommodation_results, 'best_accommodations', []))
                accommodation_progress.result_preview = f"Found {accommodation_count} accommodation options"
                
                return TravelOrchestratorResponse(
                    response_type=ResponseType.ACCOMMODATIONS,
                    response_status=ResponseStatus.COMPLETE_SUCCESS,
                    message=f"Found accommodation options from your request. {accommodation_results.recommendation if hasattr(accommodation_results, 'recommendation') else 'Here are the available accommodations.'}",
                    overall_progress_message="Accommodation search completed successfully",
                    is_final_response=True,
                    tool_progress=[accommodation_progress],
                    accommodation_results=accommodation_results,
                    processing_time_seconds=processing_time,
                    session_metadata={
                        "session_id": session_id,
                        "agent_type": "accommodation_specialist"
                    }
                )
            else:
                # Agent failed or returned no structured data
                accommodation_progress.status = "failed"
                accommodation_progress.error_message = "No accommodation results found"
                
                return TravelOrchestratorResponse(
                    response_type=ResponseType.CONVERSATION,
                    response_status=ResponseStatus.TOOL_ERROR,
                    message="I searched for accommodations but couldn't find any results. Please check your travel details and try again.",
                    overall_progress_message="Accommodation search completed with no results",
                    is_final_response=True,
                    tool_progress=[accommodation_progress],
                    success=False,
                    processing_time_seconds=processing_time,
                    session_metadata={
                        "session_id": session_id,
                        "agent_type": "accommodation_specialist",
                        "response_format": "no_results"
                    }
                )
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"❌ Accommodation search failed: {str(e)}")
            
            # Update progress to failed
            accommodation_progress.status = "failed"
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
                processing_time_seconds=processing_time
            )

    @tool
    def search_restaurants(self, travel_request: str, session_id: str = None) -> TravelOrchestratorResponse:
        """
        Search for restaurants by delegating to food specialist agent
        
        Args:
            travel_request: Natural language travel request
            session_id: Session ID for context (auto-generated if not provided)
        
        Returns:
            TravelOrchestratorResponse with structured restaurant results and progress tracking
        """
        if not session_id:
            session_id = self.session_id or str(uuid.uuid4())
        
        start_time = datetime.now()
        print(f"🍽️  Searching restaurants: {travel_request}")
        
        # Create progress tracking for this tool
        restaurant_progress = create_tool_progress(
            "search_restaurants", 
            {"destination": "destination city", "dietary_preferences": "dietary preferences"}, 
            "active"
        )
        
        try:
            # Use simplified agent invocation (now returns Pydantic models directly - sync call)
            restaurant_results = self.agent_invoker.invoke_food_agent(travel_request, session_id)

            print(f"Food Agent Results: {restaurant_results}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if restaurant_results:
                # Successfully got structured restaurant data
                print(f"✅ Restaurant search complete with structured RestaurantSearchResults")
                
                # Update progress to completed
                restaurant_progress.status = "completed"
                restaurant_count = len(getattr(restaurant_results, 'restaurants', []))
                restaurant_progress.result_preview = f"Found {restaurant_count} restaurant options"
                
                return TravelOrchestratorResponse(
                    response_type=ResponseType.RESTAURANTS,
                    response_status=ResponseStatus.COMPLETE_SUCCESS,
                    message=f"Found restaurant options from your request. {restaurant_results.recommendation if hasattr(restaurant_results, 'recommendation') else 'Here are the available restaurants.'}",
                    overall_progress_message="Restaurant search completed successfully",
                    is_final_response=True,
                    tool_progress=[restaurant_progress],
                    restaurant_results=restaurant_results,
                    processing_time_seconds=processing_time,
                    session_metadata={
                        "session_id": session_id,
                        "agent_type": "restaurant_specialist"
                    }
                )
            else:
                # Agent failed or returned no structured data
                restaurant_progress.status = "failed"
                restaurant_progress.error_message = "No restaurant results found"
                
                return TravelOrchestratorResponse(
                    response_type=ResponseType.CONVERSATION,
                    response_status=ResponseStatus.TOOL_ERROR,
                    message="I searched for restaurants but couldn't find any results. Please check your travel details and try again.",
                    overall_progress_message="Restaurant search completed with no results",
                    is_final_response=True,
                    tool_progress=[restaurant_progress],
                    success=False,
                    processing_time_seconds=processing_time,
                    session_metadata={
                        "session_id": session_id,
                        "agent_type": "restaurant_specialist",
                        "response_format": "no_results"
                    }
                )
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"❌ Restaurant search failed: {str(e)}")
            
            # Update progress to failed
            restaurant_progress.status = "failed"
            restaurant_progress.error_message = str(e)
            
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.TOOL_ERROR,
                message="I encountered an error while searching for restaurants. Please try again or provide more specific details.",
                overall_progress_message="Restaurant search failed due to an error",
                is_final_response=True,
                tool_progress=[restaurant_progress],
                success=False,
                error_message=str(e),
                processing_time_seconds=processing_time
            )



# Bedrock AgentCore integration
app = BedrockAgentCoreApp()

# Global memory configuration
MEMORY_ID = None
MEMORY_CLIENT = None

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
            event_expiry_days=30,
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
async def travel_orchestrator_invocation(payload, context=None):
    """Travel orchestrator entry point for AgentCore Runtime"""
    if "prompt" not in payload:
        yield {"error": "Missing 'prompt' in payload"}
        return
    
    try:
        region = payload.get("region", "us-east-1")
        
        # Extract session ID from AgentCore context (from HTTP header)
        session_id = None
        if context and hasattr(context, 'session_id'):
            session_id = context.session_id
            logger.info(f"✅ Extracted session ID from AgentCore context: {session_id}")
        elif context and hasattr(context, 'runtime_session_id'):
            session_id = context.runtime_session_id  
            logger.info(f"✅ Extracted runtime session ID from AgentCore context: {session_id}")
        
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
        
        # Stream responses from the orchestrator agent
        stream = agent.stream_async(payload["prompt"])
        async for event in stream:
            yield event
            
    except Exception as e:
        logger.error(f"Error in travel orchestrator: {str(e)}")
        yield {"error": f"Travel orchestrator failed: {str(e)}"}


if __name__ == "__main__":
    app.run()
