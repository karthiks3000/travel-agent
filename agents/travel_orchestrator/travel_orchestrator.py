"""
Travel Orchestrator Agent - Main conversational interface for travel planning
"""
import os
import sys
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


class TravelOrchestratorAgent(Agent):
    def __init__(self, memory_id: str = None, actor_id: str = None, session_id: str = None, 
                 user_id: str = None, region: str = "us-east-1"):
        """
        Initialize Travel Orchestrator Agent with memory integration
        
        Args:
            memory_id: AgentCore Memory resource ID (created if not provided)
            actor_id: Unique actor ID for this agent instance
            session_id: Shared session ID for the conversation
            user_id: User identifier for personalization
            region: AWS region for AgentCore services
        """
        # Get current date for system prompt
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Generate session and actor IDs if not provided
        if not session_id or not actor_id:
            id_config = generate_session_ids(user_id=user_id)
            session_id = session_id or id_config["session_id"]
            actor_id = actor_id or id_config["orchestrator"]
        
        # Store session info for tools
        self.session_id = session_id
        self.actor_id = actor_id
        self.user_id = user_id
        
        logger.info(f"Initializing Travel Orchestrator - Session: {session_id}, Actor: {actor_id}")
        
        # Initialize agent invoker for specialist agents
        self.agent_invoker = AgentInvoker()
        
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
            "user_id": user_id,
            "agent_type": "travel_orchestrator"
        }
        
        super().__init__(
            model="amazon.nova-pro-v1:0",
            tools=[
                self.validate_travel_information,
                self.search_flights,
                self.search_accommodations, 
                self.search_restaurants,
                self.plan_comprehensive_trip
            ],
            system_prompt=self._build_system_prompt(current_datetime, current_date),
            # hooks=[memory_hooks] if memory_hooks else [],
            state=agent_state
        )
    
    def _build_system_prompt(self, current_datetime: str, current_date: str) -> str:
        """Build comprehensive system prompt for travel orchestration"""
        return f"""You are a Travel Orchestrator Agent, the main interface for comprehensive travel planning. Current date and time: {current_datetime}

YOUR ROLE:
You coordinate multiple specialist agents (flights, accommodations, restaurants) to create personalized travel plans. You are the conversational interface that users interact with directly.

CORE WORKFLOW:

1. INFORMATION GATHERING:
   - Extract travel details from user requests
   - Use validate_travel_information tool to check completeness
   - Ask clarifying questions for missing critical information
   - Build complete TravelInformation structure progressively

2. VALIDATION BEFORE DELEGATION:
   - ALWAYS call validate_travel_information before calling search tools
   - Only proceed with searches when validation shows agents are ready
   - Handle date validation - reject past dates, today is OK
   - Infer missing information intelligently (passengers = guests, etc.)

3. AGENT ORCHESTRATION:
   - Call specialist agents with natural language requests
   - Use parallel execution when multiple agents are ready
   - Handle agent failures gracefully
   - Combine results from multiple agents

4. CONVERSATION MANAGEMENT:
   - Maintain context across multiple turns
   - Ask specific, targeted questions
   - Avoid asking for information already provided
   - Guide users through travel planning process

5. PLAN SYNTHESIS:
   - Combine results from multiple agents into coherent plans
   - Provide recommendations based on user preferences
   - Calculate estimated costs
   - Present options clearly

CRITICAL RULES:

⚠️  VALIDATION FIRST: Never call search tools without validating requirements first
⚠️  ONE QUESTION TYPE: Don't ask about flights AND hotels AND dates all at once
⚠️  CONTEXT AWARENESS: Remember what user has already told you
⚠️  DATE VALIDATION: Reject requests for past dates (before {current_date})
⚠️  PROGRESSIVE DISCLOSURE: Gather core info first, preferences later

REQUIRED INFORMATION BY AGENT:

FLIGHTS: origin, destination, departure_date, passengers
- For round-trip: also need return_date
- Validate all dates are today or future

ACCOMMODATIONS: destination, check_in, check_out, guests  
- Validate all dates are today or future
- Can infer from flight dates if missing

RESTAURANTS: destination (minimum)
- Can search once destination is known
- Include dietary restrictions if provided

CONVERSATION EXAMPLES:

User: "Plan a trip to Paris"
You: "I'd love to help plan your Paris trip! To find the best options, I need:
- What city will you be departing from?
- What are your travel dates?
- How many people will be traveling?"

User: "From NYC, June 15-20, 2 people"
You: [Extract info, validate, then search since we have complete information]
"Perfect! Let me search for flights from NYC to Paris June 15-20 for 2 people, accommodations, and restaurant recommendations."

TOOL USAGE STRATEGY:

1. validate_travel_information: Check what's missing before any searches
2. search_flights/accommodations/restaurants: Only after validation confirms readiness
3. plan_comprehensive_trip: When you have results from multiple agents to synthesize

MEMORY INTEGRATION:
- User preferences are automatically stored via AgentCore Memory
- Reference past trips: "Based on your previous Paris trip..."
- Learn preferences: "I notice you prefer mid-range hotels"
- Build user profiles over time

RESPONSE STYLE:
- Conversational and helpful
- Clear about what information you need
- Explain what you're searching for
- Present results in organized, scannable format
- Provide specific recommendations with reasoning

Remember: You're the intelligent coordinator that makes travel planning effortless by gathering the right information, calling the right agents, and presenting results in a helpful way."""

    @tool(description="Validate travel information completeness using structured data")
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

    @tool(description="Search for flights using the flight specialist agent")
    def search_flights(self, travel_request: str, session_id: str = None) -> AgentSearchResult:
        """
        Search for flights by delegating to flight specialist agent
        
        Args:
            travel_request: Natural language travel request
            session_id: Session ID for context (auto-generated if not provided)
        
        Returns:
            AgentSearchResult with flight search results
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        print(f"✈️  Searching flights: {travel_request}")
        
        # Use asyncio to run the async agent invocation
        result = asyncio.run(self.agent_invoker.invoke_flight_agent(travel_request, session_id))
        
        print(f"✅ Flight search complete: {result.result_count} options found")
        return result

    @tool(description="Search for accommodations using the accommodation specialist agent")
    def search_accommodations(self, travel_request: str, session_id: str = None) -> AgentSearchResult:
        """
        Search for accommodations by delegating to accommodation specialist agent
        
        Args:
            travel_request: Natural language travel request
            session_id: Session ID for context (auto-generated if not provided)
        
        Returns:
            AgentSearchResult with accommodation search results
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        print(f"🏨 Searching accommodations: {travel_request}")
        
        # Use asyncio to run the async agent invocation
        result = asyncio.run(self.agent_invoker.invoke_accommodation_agent(travel_request, session_id))
        
        print(f"✅ Accommodation search complete: {result.result_count} options found")
        return result

    @tool(description="Search for restaurants using the food specialist agent")
    def search_restaurants(self, travel_request: str, session_id: str = None) -> AgentSearchResult:
        """
        Search for restaurants by delegating to food specialist agent
        
        Args:
            travel_request: Natural language travel request
            session_id: Session ID for context (auto-generated if not provided)
        
        Returns:
            AgentSearchResult with restaurant search results
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        print(f"🍽️  Searching restaurants: {travel_request}")
        
        # Use asyncio to run the async agent invocation
        result = asyncio.run(self.agent_invoker.invoke_food_agent(travel_request, session_id))
        
        print(f"✅ Restaurant search complete: {result.result_count} options found")
        return result

    @tool(description="Plan comprehensive trip by orchestrating all specialist agents")
    def plan_comprehensive_trip(self, travel_info_dict: dict, session_id: str = None) -> ComprehensiveTravelPlan:
        """
        Orchestrate all specialist agents for comprehensive travel planning
        
        Args:
            travel_info_dict: Complete travel information dictionary
            session_id: Session ID for context (auto-generated if not provided)
        
        Returns:
            ComprehensiveTravelPlan with synthesized results from all agents
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        start_time = datetime.now()
        print(f"🌍 Planning comprehensive trip: {travel_info_dict}")
        
        try:
            # Parse and validate travel information
            travel_info = TravelInformation.model_validate(travel_info_dict)
            
            # Format natural language request for agents
            travel_request = format_travel_request(travel_info)
            print(f"📝 Formatted request: {travel_request}")
            
            # Execute parallel agent calls
            print("🔄 Executing parallel agent searches...")
            results = asyncio.run(
                self.agent_invoker.invoke_parallel_agents(travel_request, session_id)
            )
            
            # Create comprehensive travel plan
            plan = ComprehensiveTravelPlan(
                destination=travel_info.destination or "Unknown",
                origin=travel_info.origin or "Unknown", 
                dates={
                    "departure": str(travel_info.departure_date) if travel_info.departure_date else "TBD",
                    "return": str(travel_info.return_date) if travel_info.return_date else "TBD"
                },
                travelers=travel_info.passengers or travel_info.guests or 1,
                flight_results=results.get("flights"),
                accommodation_results=results.get("accommodations"),
                restaurant_results=results.get("restaurants"),
                agents_used=list(results.keys()),
                generation_time_seconds=(datetime.now() - start_time).total_seconds()
            )
            
            # Calculate plan metrics
            successful_agents = sum(1 for result in results.values() if result.success)
            plan.completeness_score = successful_agents / len(results) if results else 0
            plan.confidence_score = min(plan.completeness_score, 0.9)  # Cap at 0.9 for realistic confidence
            
            # Calculate estimated costs
            plan.estimated_costs = self._calculate_estimated_costs(results, travel_info)
            plan.total_estimated_cost = sum(plan.estimated_costs.values())
            
            # Generate recommendations
            plan.recommendations = self._generate_recommendations(results, travel_info)
            
            print(f"✅ Comprehensive plan generated: {plan.get_plan_summary()}")
            return plan
            
        except Exception as e:
            print(f"❌ Comprehensive planning failed: {str(e)}")
            
            # Return minimal plan with error information
            return ComprehensiveTravelPlan(
                destination=travel_info_dict.get("destination", "Unknown"),
                origin=travel_info_dict.get("origin", "Unknown"),
                dates={"departure": "TBD", "return": "TBD"},
                travelers=1,
                confidence_score=0.0,
                completeness_score=0.0,
                recommendations={"error": str(e)},
                generation_time_seconds=(datetime.now() - start_time).total_seconds()
            )

    def _calculate_estimated_costs(self, results: Dict[str, AgentSearchResult], 
                                 travel_info: TravelInformation) -> Dict[str, float]:
        """Calculate estimated costs from agent results"""
        costs = {}
        
        # Flight costs
        if results.get("flights") and results["flights"].success:
            flight_data = results["flights"].results
            if isinstance(flight_data, dict) and "flights" in flight_data:
                flights = flight_data["flights"]
                if flights and len(flights) > 0:
                    # Use average of first few flights
                    prices = [f.get("price", 0) for f in flights[:3] if isinstance(f, dict)]
                    if prices:
                        costs["flights"] = sum(prices) / len(prices)
        
        # Accommodation costs  
        if results.get("accommodations") and results["accommodations"].success:
            acc_data = results["accommodations"].results
            if isinstance(acc_data, dict):
                properties = acc_data.get("combined_results", []) or acc_data.get("airbnb_properties", [])
                if properties and len(properties) > 0:
                    # Calculate for trip duration
                    nights = 1
                    if travel_info.check_in and travel_info.check_out:
                        nights = (travel_info.check_out - travel_info.check_in).days
                    
                    # Use average of first few properties
                    nightly_prices = [p.get("price_per_night", 0) for p in properties[:3] if isinstance(p, dict)]
                    if nightly_prices:
                        avg_nightly = sum(nightly_prices) / len(nightly_prices)
                        costs["accommodations"] = avg_nightly * nights
        
        return costs

    def _generate_recommendations(self, results: Dict[str, AgentSearchResult], 
                                travel_info: TravelInformation) -> Dict[str, Any]:
        """Generate recommendations based on search results"""
        recommendations = {}
        
        # Flight recommendations
        if results.get("flights") and results["flights"].success:
            flight_data = results["flights"].results
            if isinstance(flight_data, dict) and "flights" in flight_data:
                flights = flight_data["flights"]
                if flights:
                    # Find cheapest and fastest options
                    cheapest = min(flights, key=lambda f: f.get("price", float('inf')))
                    recommendations["cheapest_flight"] = {
                        "airline": cheapest.get("airline"),
                        "price": cheapest.get("price"),
                        "reason": "Most affordable option"
                    }
        
        # Accommodation recommendations
        if results.get("accommodations") and results["accommodations"].success:
            acc_data = results["accommodations"].results
            if isinstance(acc_data, dict):
                properties = acc_data.get("combined_results", [])
                if properties:
                    # Find highest rated option
                    rated_properties = [p for p in properties if p.get("rating")]
                    if rated_properties:
                        best_rated = max(rated_properties, key=lambda p: p.get("rating", 0))
                        recommendations["best_accommodation"] = {
                            "title": best_rated.get("title"),
                            "rating": best_rated.get("rating"),
                            "price": best_rated.get("price_per_night"),
                            "reason": "Highest rated option"
                        }
        
        return recommendations


# Bedrock AgentCore integration
app = BedrockAgentCoreApp()

# Global memory configuration
MEMORY_ID = None
MEMORY_CLIENT = None

def initialize_memory(region: str = "us-east-1") -> str:
    """Initialize shared memory resource for travel planning"""
    global MEMORY_ID, MEMORY_CLIENT
    
    if MEMORY_ID:
        return MEMORY_ID
    
    try:
        MEMORY_CLIENT = MemoryClient(region_name=region)
        memory_name = f"TravelOrchestrator_STM_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Try to get existing memory from environment
        existing_memory_id = os.getenv('TRAVEL_ORCHESTRATOR_MEMORY_ID')
        if existing_memory_id:
            MEMORY_ID = existing_memory_id
            logger.info(f"Using existing memory ID from environment: {MEMORY_ID}")
            return MEMORY_ID
        
        # Create new memory resource
        logger.info("Creating new memory resource...")
        memory = MEMORY_CLIENT.create_memory_and_wait(
            name=memory_name,
            description="Travel Orchestrator Short-term Memory",
            strategies=[],
            event_expiry_days=7,
            max_wait=300,
            poll_interval=10
        )
        
        MEMORY_ID = memory['id']
        logger.info(f"✅ Created memory with ID: {MEMORY_ID}")
        return MEMORY_ID
        
    except Exception as e:
        logger.error(f"Failed to initialize memory: {e}")
        # Continue without memory - agent will work without memory features
        return None

@app.entrypoint
async def travel_orchestrator_invocation(payload):
    """Travel orchestrator entry point for AgentCore Runtime"""
    if "prompt" not in payload:
        yield {"error": "Missing 'prompt' in payload"}
        return
    
    try:
        # Extract user context
        user_id = payload.get("user_id", "anonymous")
        session_id = payload.get("session_id")
        region = payload.get("region", "us-east-1")
        
        # Generate session IDs if not provided
        if not session_id:
            id_config = generate_session_ids(user_id=user_id)
            session_id = id_config["session_id"]
            actor_id = id_config["orchestrator"]
        else:
            # Use provided session_id and generate actor_id
            actor_id = f"travel-orchestrator-{session_id}"
        
        logger.info(f'🚀 Starting travel orchestration - User: {user_id}, Session: {session_id}, Actor: {actor_id}')
        
        # Initialize memory (optional - agent works without it)
        memory_id = initialize_memory(region)
        
        # Create agent instance with session-specific configuration
        agent = TravelOrchestratorAgent(
            memory_id=memory_id,
            actor_id=actor_id,
            session_id=session_id,
            user_id=user_id,
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
