# AI Travel Agent - Technical Architecture

## System Architecture Overview

The AI Travel Agent uses a simplified, direct architecture leveraging AgentCore Runtime's native capabilities for intelligent travel planning.

```
┌─────────────────────────────────────────┐
│           Frontend                      │
│      React + TypeScript                 │
│      TailwindCSS + Aceternity UI        │
│                                         │
│   ┌─────────────────────────────────┐   │
│   │    HTTP Streaming Connection    │   │◄─────────┐
│   │    (Real-time Updates)          │   │          │
│   └─────────────────────────────────────┘   │          │
└─────────────────────────────────────────┘          │
                     │                                 │
                     ▼                                 │
┌─────────────────────────────────────────────────────┐│
│      Travel Orchestrator Agent                     ││
│         (Main AgentCore Runtime)                    ││
│  ┌─────────────────┐  ┌─────────────────────────┐  ││
│  │   Cognito JWT   │  │   Orchestration Logic   │  ││
│  │  Authentication │◄─┤   + Memory Integration  │  ││
│  │                 │  │   + Result Synthesis    │  ││
│  └─────────────────┘  └─────────────────────────┘  ││
└─────────────────────────────────────────────────────┘│
                     │ (Parallel Agent Calls)          │
                     ▼                                 │
┌─────────────┬─────────────┬─────────────┬───────────┐│
│ Flight      │ Airbnb      │ Booking.com │ Food      ││
│ Agent       │ Agent       │ Agent       │ Agent     ││
│(AgentCore)  │(AgentCore)  │(AgentCore)  │(AgentCore)││
│             │             │             │           ││
│┌───────────┐│┌───────────┐│┌───────────┐│┌─────────┐││
││ Nova Act  │││ Nova Act  │││ Nova Act  │││ Yelp    │││
││ Browser   │││ Browser   │││ Browser   │││ Fusion  │││
││(G.Flights)│││(Airbnb)   │││(Booking)  │││ API     │││
│└───────────┘│└───────────┘│└───────────┘│└─────────┘││
└─────────────┴─────────────┴─────────────┴───────────┘│
                                                      │
┌─────────────────────────────────────────────────────┘
│         Built-in Observability & Monitoring  
│  ┌──────────────────────────────────────────────┐
│  │  • AgentCore Observability (All Agents)     │
│  │  • Cross-Agent Trace Correlation            │
│  │  • Individual Agent Performance Metrics     │
│  │  • Built-in Rate Limiting (100 RPS each)    │
│  └──────────────────────────────────────────────┘
```

## Core Components

### 1. Frontend Application
**Technology**: React 18 + TypeScript + TailwindCSS + Aceternity UI

**Responsibilities**:
- Chat-based user interface for travel requests
- Real-time status updates during agent execution
- Source attribution display for recommendations
- Responsive design for mobile and desktop
- Authentication flow integration

**Key Features**:
```typescript
interface TravelRequest {
  destination: string;
  dates: { start: Date; end: Date };
  partySize: number;
  ages: number[];
  budget: number;
  preferences: string[];
}

interface TravelResponse {
  itinerary: Itinerary;
  sources: SourceAttribution[];
  confidence: number;
  alternatives: Alternative[];
}
```

### 2. AgentCore Runtime Direct Integration
**Technology**: Strands Agents SDK + AgentCore Runtime + BedrockAgentCoreApp

**Architecture Pattern**: Direct HTTP invocation with streaming responses

**Request Flow**:
```python
from strands import Agent
from bedrock_agentcore import BedrockAgentCoreApp

agent = Agent()
app = BedrockAgentCoreApp()

@app.entrypoint
async def agent_invocation(payload):
    """Direct entry point for travel planning requests"""
    
    # 1. Extract user context from JWT (handled by AgentCore)
    user_id = payload.get("user_id")  # From JWT claims
    travel_request = payload.get("prompt")
    
    # 2. Initialize travel planner with memory
    travel_agent = TravelPlannerAgent(
        user_id=user_id,
        memory=AgentCoreMemory(user_id=user_id)
    )
    
    # 3. Stream responses in real-time
    stream = travel_agent.stream_async(travel_request)
    async for event in stream:
        yield event  # Real-time streaming to client
```

**Direct Invocation**:
```bash
# Frontend directly calls AgentCore Runtime endpoint
curl -X POST "https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/{agent_arn}/invocations" \
  -H "Authorization: Bearer {cognito_jwt_token}" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Plan a trip to Paris for 2 people in June"}'
```

### 3. Multi-Agent System (Specialized AgentCore Runtime Instances)

**MVP Agent Architecture**: 5 specialized micro-agents for parallel execution

**1. Travel Orchestrator Agent** (Main AgentCore Runtime)
```python
from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp
import asyncio
import httpx

app = BedrockAgentCoreApp()

class TravelOrchestratorAgent(Agent):
    def __init__(self, user_id: str):
        super().__init__(
            model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            memory=AgentCoreMemory(user_id=user_id)
        )
        self.user_id = user_id
        self.specialist_agents = {
            "flights": "arn:aws:bedrock-agentcore:us-east-1:123456789:agent-runtime/flight-agent",
            "airbnb": "arn:aws:bedrock-agentcore:us-east-1:123456789:agent-runtime/airbnb-agent", 
            "booking": "arn:aws:bedrock-agentcore:us-east-1:123456789:agent-runtime/booking-agent",
            "food": "arn:aws:bedrock-agentcore:us-east-1:123456789:agent-runtime/food-agent"
        }
    
    @tool
    async def comprehensive_travel_search(self, destination: str, dates: dict, 
                                        travelers: int, budget: float) -> dict:
        """Orchestrate parallel search across all specialized agents"""
        
        # Prepare search parameters
        search_params = {
            "destination": destination,
            "dates": dates,
            "travelers": travelers,
            "budget": budget
        }
        
        # Execute parallel agent calls
        tasks = []
        
        # Flight search
        tasks.append(self._invoke_specialist_agent("flights", search_params))
        
        # Parallel accommodation searches (Airbnb + Booking.com)
        tasks.append(self._invoke_specialist_agent("airbnb", search_params))
        tasks.append(self._invoke_specialist_agent("booking", search_params))
        
        # Food recommendations
        tasks.append(self._invoke_specialist_agent("food", search_params))
        
        # Wait for all agents to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Synthesize results from all agents
        return self._synthesize_multi_agent_results(results, search_params)
    
    async def _invoke_specialist_agent(self, agent_type: str, params: dict):
        """Invoke a specialist agent and return results"""
        agent_arn = self.specialist_agents[agent_type]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/{agent_arn}/invocations",
                headers={
                    "Authorization": f"Bearer {self._get_agent_token()}",
                    "Content-Type": "application/json"
                },
                json={"prompt": f"Search {agent_type}", "params": params},
                timeout=60.0
            )
            return {"agent": agent_type, "results": response.json()}

@app.entrypoint
async def orchestrator_invocation(payload):
    """Main orchestrator entry point"""
    user_id = payload.get("user_id")
    travel_request = payload.get("prompt")
    
    orchestrator = TravelOrchestratorAgent(user_id=user_id)
    
    # Stream orchestrated responses
    stream = orchestrator.stream_async(travel_request)
    async for event in stream:
        yield event
```

**2. Flight Specialist Agent** (Dedicated AgentCore Runtime with Nova Act)
```python
# flight_agent.py
from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp
from nova_act import NovaAct

app = BedrockAgentCoreApp()

class FlightSpecialistAgent(Agent):
    def __init__(self):
        super().__init__(
            model="anthropic.claude-3-5-sonnet-20241022-v2:0"  # More capable model for browser tasks
        )
    
    @tool
    def search_flights(self, origin: str, destination: str, 
                      departure_date: str, return_date: str = None) -> dict:
        """Search flights using Nova Act browser automation"""
        
        with NovaAct(starting_page="https://www.google.com/travel/flights") as nova:
            nova.act(f"Search for flights from {origin} to {destination}")
            nova.act(f"Set departure date to {departure_date}")
            if return_date:
                nova.act(f"Set return date to {return_date}")
            
            result = nova.act(
                "Extract first 20 flight options with prices, airlines, times, and durations",
                schema=FlightSearchResults.model_json_schema()
            )
            
            return {
                "platform": "google_flights",
                "flights": result.parsed_response.flights if result.matches_schema else [],
                "metadata": {"search_method": "nova_act", "source": "Google Flights"}
            }

@app.entrypoint
async def flight_agent_invocation(payload):
    agent = FlightSpecialistAgent()
    stream = agent.stream_async(payload["prompt"])
    async for event in stream:
        yield event
```

**3. Airbnb Specialist Agent** (Dedicated AgentCore Runtime with Nova Act)
```python
# airbnb_agent.py
from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp
from nova_act import NovaAct

app = BedrockAgentCoreApp()

class AirbnbSpecialistAgent(Agent):
    def __init__(self):
        super().__init__(
            model="anthropic.claude-3-5-sonnet-20241022-v2:0"  # More capable for browser tasks
        )
    
    @tool
    def search_airbnb(self, location: str, check_in: str, check_out: str, guests: int) -> dict:
        """Search Airbnb using Nova Act browser automation"""
        
        with NovaAct(starting_page="https://www.airbnb.com") as nova:
            nova.act(f"Search for accommodations in {location}")
            nova.act(f"Set check-in date to {check_in}")
            nova.act(f"Set check-out date to {check_out}")
            nova.act(f"Set number of guests to {guests}")
            
            result = nova.act(
                "Extract first 20 property listings with titles, prices, ratings, and amenities",
                schema=PropertySearchResults.model_json_schema()
            )
            
            return {
                "platform": "airbnb",
                "properties": result.parsed_response.listings if result.matches_schema else [],
                "metadata": {"search_method": "nova_act", "source": "Airbnb"}
            }

@app.entrypoint 
async def airbnb_agent_invocation(payload):
    agent = AirbnbSpecialistAgent()
    stream = agent.stream_async(payload["prompt"])
    async for event in stream:
        yield event
```

**4. Booking.com Specialist Agent** (Dedicated AgentCore Runtime with Nova Act)
```python
# booking_agent.py  
from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp
from nova_act import NovaAct

app = BedrockAgentCoreApp()

class BookingSpecialistAgent(Agent):
    def __init__(self):
        super().__init__(
            model="anthropic.claude-3-5-sonnet-20241022-v2:0"  # More capable for browser tasks
        )
    
    @tool
    def search_booking(self, location: str, check_in: str, check_out: str, guests: int) -> dict:
        """Search Booking.com using Nova Act browser automation"""
        
        with NovaAct(starting_page="https://www.booking.com") as nova:
            nova.act(f"Search for accommodations in {location}")
            nova.act(f"Set check-in date to {check_in}")
            nova.act(f"Set check-out date to {check_out}")
            nova.act(f"Set number of guests to {guests}")
            
            result = nova.act(
                "Extract first 20 hotel listings with names, prices, ratings, and amenities",
                schema=HotelSearchResults.model_json_schema()
            )
            
            return {
                "platform": "booking_com",
                "hotels": result.parsed_response.listings if result.matches_schema else [],
                "metadata": {"search_method": "nova_act", "source": "Booking.com"}
            }

@app.entrypoint
async def booking_agent_invocation(payload):
    agent = BookingSpecialistAgent()
    stream = agent.stream_async(payload["prompt"])
    async for event in stream:
        yield event
```

**5. Food Specialist Agent** (Dedicated AgentCore Runtime)
```python
# food_agent.py
from strands import Agent, tool  
from bedrock_agentcore import BedrockAgentCoreApp
from tools.yelp_api import YelpFusionAPI

app = BedrockAgentCoreApp()

class FoodSpecialistAgent(Agent):
    def __init__(self):
        super().__init__(
            model="anthropic.claude-3-haiku-20240307-v1:0"  # Faster model for API calls
        )
        self.yelp_api = YelpFusionAPI()
    
    @tool
    def search_restaurants(self, location: str, preferences: list = None) -> dict:
        """Search restaurants using Yelp Fusion API"""
        
        results = self.yelp_api.search_restaurants(
            location=location,
            categories="restaurants,bars,cafes",
            limit=30
        )
        
        return {
            "platform": "yelp",
            "restaurants": results,
            "metadata": {"search_method": "api", "source": "Yelp Fusion API"}
        }

@app.entrypoint
async def food_agent_invocation(payload):
    agent = FoodSpecialistAgent()
    stream = agent.stream_async(payload["prompt"])
    async for event in stream:
        yield event
```

**Multi-Agent Benefits**:
- **True Parallelization**: Airbnb and Booking.com searches run simultaneously
- **Fault Isolation**: One platform failure doesn't affect others
- **Independent Scaling**: Scale each agent based on platform demand
- **Specialized Optimization**: Different models for different complexity levels
- **Resource Efficiency**: No resource contention between search operations

### 4. Browser Automation Layer

**Technology**: Amazon Nova Act SDK + AgentCore Browser Tool

**Pattern**: Task decomposition for reliability
```python
class AccommodationSearchTool(Tool):
    def search_airbnb(self, location: str, dates: tuple) -> List[Property]:
        with NovaAct(starting_page="https://www.airbnb.com") as nova:
            # Step 1: Navigate and search
            nova.act(f"Search for accommodations in {location}")
            
            # Step 2: Set dates
            nova.act(f"Set check-in to {dates[0]} and check-out to {dates[1]}")
            
            # Step 3: Apply filters
            nova.act("Filter: entire place, $50-200/night, 4+ rating")
            
            # Step 4: Extract structured data
            result = nova.act(
                "Return first 10 listings with prices and ratings",
                schema=PropertyListSchema.model_json_schema()
            )
            
            return PropertyListSchema.model_validate(result.parsed_response)
```

### 5. Data Integration Strategy

**Multi-source approach for comprehensive coverage**:

| Platform | Access Method | Data Type | Rate Limits |
|----------|---------------|-----------|-------------|
| Google Flights | Browser Automation (Nova Act) | Flight prices, schedules | Self-imposed: 1 req/3sec |
| Yelp Fusion | REST API (Free) | Restaurant/activity data | 5K calls/day |
| Airbnb | Browser Automation (Nova Act) | Accommodation listings | Self-imposed: 1 req/2sec |
| Booking.com | Browser Automation (Nova Act) | Hotel listings | Self-imposed: 1 req/2sec |

**Note**: Google Flights does not provide a public API. Browser automation via Nova Act is the only viable method to access real-time flight data.

### 6. Memory & Personalization System

**AgentCore Memory Configuration**:
```python
memory_config = {
    "strategy": "user_preferences",
    "short_term": {
        "type": "conversation_buffer",
        "max_messages": 50
    },
    "long_term": {
        "type": "user_profile",
        "categories": ["preferences", "past_trips", "constraints"]
    }
}
```

**User Profile Schema**:
```json
{
  "user_id": "string",
  "preferences": {
    "accommodation_type": ["hotel", "airbnb", "hostel"],
    "food_restrictions": ["vegetarian", "gluten-free"],
    "activity_types": ["cultural", "outdoor", "nightlife"],
    "travel_pace": "relaxed|moderate|packed",
    "budget_category": "budget|mid-range|luxury"
  },
  "constraints": {
    "mobility_requirements": "string",
    "group_composition": "family|couple|solo|friends"
  }
}
```

## Security Architecture

### 1. Native AgentCore Authentication & Authorization
- **Amazon Cognito**: JWT Bearer Token authentication (built-in support)
- **AgentCore Identity**: Secure workload identity management
- **OAuth2 Support**: Built-in three-legged OAuth for third-party integrations
- **Custom JWT Authorizer**: Configurable token validation

**Authentication Configuration**:
```python
# AgentCore native authentication setup
authorizer_config = {
    "customJWTAuthorizer": {
        "discoveryUrl": "https://cognito-idp.us-east-1.amazonaws.com/{pool_id}/.well-known/openid-configuration",
        "allowedClients": ["cognito_client_id"],
        "allowedAudiences": ["travel-agent-app"]
    }
}

# Deploy with CDK
AgentRuntime(
    name="travel-agent",
    authorizer_configuration=authorizer_config,
    execution_role=agent_execution_role
)
```

### 2. Browser Automation Security
```python
# AgentCore Browser Tool security profile
browser_security = {
    "security_profile": "travel-agent-restricted",
    "allowed_domains": [
        "airbnb.com", "booking.com", "google.com",
        "yelp.com", "tripadvisor.com"
    ],
    "session_timeout_minutes": 30,
    "observability_enabled": True,
    "prompt_injection_protection": True
}
```

### 3. Enterprise Data Protection
- **Micro-VM Isolation**: Each session runs in isolated environment
- **TLS 1.3 Encryption**: All communications encrypted
- **AgentCore Identity Vault**: Secure credential storage
- **Audit Trails**: Complete action logging via CloudWatch

## Scalability Design

### 1. Native AgentCore Scaling
- **500 Active Sessions**: Per account (adjustable via support)
- **100 RPS per Endpoint**: Built-in rate limiting
- **Auto-scaling**: Scales to thousands of sessions in seconds
- **Global Load Distribution**: Multi-region deployment support

**Scaling Quotas**:
| Resource | Limit | Adjustable |
|----------|-------|------------|
| Active Sessions | 500 (US-East), 250 (other regions) | Yes |
| Total Agents | 1000 | Yes |
| Endpoints per Agent | 10 | Yes |
| Invocations per Second | 100 per endpoint | Yes |

### 2. Performance Optimizations
```python
# Built-in parallel execution within AgentCore Runtime
@app.entrypoint  
async def agent_invocation(payload):
    """AgentCore handles concurrency automatically"""
    
    # Multiple tools can run in parallel within runtime
    travel_agent = TravelPlannerAgent(user_id=payload["user_id"])
    
    # AgentCore automatically parallelizes tool calls
    async for event in travel_agent.stream_async(payload["prompt"]):
        yield event
```

### 3. Cost Optimization
- **Consumption-based Pricing**: Pay only for active runtime sessions
- **Automatic Resource Management**: No idle compute costs
- **Built-in Caching**: AgentCore Memory provides intelligent caching
- **Model Optimization**: Dynamic model selection within Strands

## Built-in Monitoring & Observability

### 1. AgentCore Native Observability
**Zero-configuration monitoring** with comprehensive built-in features:

```python
# Automatic observability - no configuration needed
observability_features = {
    "cloudwatch_integration": True,
    "opentelemetry_compatible": True,
    "automatic_dashboards": [
        "agent_performance", 
        "trace_visualizations",
        "error_breakdowns",
        "cost_analysis"
    ],
    "built_in_metrics": [
        "session_count",
        "latency", 
        "token_usage",
        "error_rates",
        "session_duration"
    ]
}
```

**Key Built-in Metrics**:
- **Runtime Metrics**: Session lifecycle, processing latency, resource utilization
- **Memory Metrics**: Storage usage, retrieval performance, strategy effectiveness  
- **Browser Tool Metrics**: Session management, automation success rates
- **Gateway Metrics**: Tool usage, request patterns, performance bottlenecks

### 2. Custom Application Metrics
```python
# Optional: Add custom business metrics
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("travel_search")
def search_comprehensive_travel(destination: str):
    # AgentCore automatically captures span data
    with tracer.start_as_current_span("user_preference_lookup"):
        preferences = get_user_preferences()
    
    with tracer.start_as_current_span("parallel_platform_search"):
        results = execute_parallel_search(destination)
    
    return synthesize_results(results, preferences)
```

## Deployment Architecture

### 1. AgentCore Starter Toolkit Deployment Workflow

**Complete Multi-Agent Deployment Script**
```bash
#!/bin/bash

# Prerequisites setup
echo "Setting up Travel Agent Multi-Agent System..."

# Install AgentCore starter toolkit
pip install amazon-bedrock-agentcore nova-act

# Verify installation
agentcore --version

# Deploy all 5 agents in sequence

# 1. Deploy Flight Specialist Agent
echo "Deploying Flight Specialist Agent..."
cd agents/flight-agent
agentcore configure \
  --entrypoint flight_agent.py \
  --name flight-agent \
  --execution-role $FLIGHT_AGENT_ROLE_ARN \
  --requirements-file requirements-browser.txt \
  --memory-size 2048 \
  --model "anthropic.claude-3-5-sonnet-20241022-v2:0" \
  --browser-tool-enabled
agentcore launch
export FLIGHT_AGENT_ARN=$(agentcore get-runtime --name flight-agent --output json | jq -r '.agentRuntimeArn')

# 2. Deploy Food Specialist Agent  
echo "Deploying Food Specialist Agent..."
cd ../food-agent
agentcore configure \
  --entrypoint food_agent.py \
  --name food-agent \
  --execution-role $FOOD_AGENT_ROLE_ARN \
  --requirements-file requirements-yelp.txt \
  --memory-size 512 \
  --model "anthropic.claude-3-haiku-20240307-v1:0"
agentcore launch
export FOOD_AGENT_ARN=$(agentcore get-runtime --name food-agent --output json | jq -r '.agentRuntimeArn')

# 3. Deploy Airbnb Specialist Agent
echo "Deploying Airbnb Specialist Agent..."
cd ../airbnb-agent
agentcore configure \
  --entrypoint airbnb_agent.py \
  --name airbnb-agent \
  --execution-role $AIRBNB_AGENT_ROLE_ARN \
  --requirements-file requirements-browser.txt \
  --memory-size 2048 \
  --model "anthropic.claude-3-5-sonnet-20241022-v2:0" \
  --browser-tool-enabled
agentcore launch
export AIRBNB_AGENT_ARN=$(agentcore get-runtime --name airbnb-agent --output json | jq -r '.agentRuntimeArn')

# 4. Deploy Booking.com Specialist Agent
echo "Deploying Booking.com Specialist Agent..."
cd ../booking-agent
agentcore configure \
  --entrypoint booking_agent.py \
  --name booking-agent \
  --execution-role $BOOKING_AGENT_ROLE_ARN \
  --requirements-file requirements-browser.txt \
  --memory-size 2048 \
  --model "anthropic.claude-3-5-sonnet-20241022-v2:0" \
  --browser-tool-enabled
agentcore launch
export BOOKING_AGENT_ARN=$(agentcore get-runtime --name booking-agent --output json | jq -r '.agentRuntimeArn')

# 5. Deploy Travel Orchestrator Agent (with Memory and Authentication)
echo "Deploying Travel Orchestrator Agent..."
cd ../orchestrator-agent
agentcore configure \
  --entrypoint orchestrator_agent.py \
  --name travel-orchestrator \
  --execution-role $ORCHESTRATOR_ROLE_ARN \
  --requirements-file requirements.txt \
  --memory-size 2048 \
  --model "anthropic.claude-3-5-sonnet-20241022-v2:0" \
  --memory-config '{"strategy": "user_preferences"}' \
  --authorizer-config '{"customJWTAuthorizer":{"discoveryUrl":"'$COGNITO_DISCOVERY_URL'","allowedClients":["'$COGNITO_CLIENT_ID'"]}}'
agentcore launch
export ORCHESTRATOR_AGENT_ARN=$(agentcore get-runtime --name travel-orchestrator --output json | jq -r '.agentRuntimeArn')

echo "All agents deployed successfully!"
echo "Flight Agent ARN: $FLIGHT_AGENT_ARN"
echo "Food Agent ARN: $FOOD_AGENT_ARN"
echo "Airbnb Agent ARN: $AIRBNB_AGENT_ARN"
echo "Booking Agent ARN: $BOOKING_AGENT_ARN"
echo "Orchestrator Agent ARN: $ORCHESTRATOR_AGENT_ARN"

# Test end-to-end system
echo "Testing complete multi-agent system..."
agentcore invoke \
  --name travel-orchestrator \
  --bearer-token $COGNITO_ACCESS_TOKEN \
  '{"prompt": "Plan a trip to Paris for 2 people in June with a $3000 budget"}'
```

### 2. Hybrid Deployment: CDK + AgentCore Integration

**CDK Stack with AgentCore Integration**
```typescript
export class TravelAgentStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps) {
    super(scope, id, props);
    
    // 1. Deploy Cognito for authentication
    const authStack = new CognitoStack(this, 'Auth');
    
    // 2. Deploy frontend hosting
    const frontendStack = new S3CloudFrontStack(this, 'Frontend');
    
    // 3. Create IAM roles for AgentCore agents
    const agentRoles = new AgentExecutionRolesStack(this, 'AgentRoles');
    
    // 4. Output configuration for AgentCore deployment
    new CfnOutput(this, 'CognitoPoolId', {
      value: authStack.userPool.userPoolId,
      description: 'Cognito User Pool ID for AgentCore authorization'
    });
    
    new CfnOutput(this, 'CognitoClientId', {
      value: authStack.userPoolClient.userPoolClientId,
      description: 'Cognito Client ID for AgentCore authorization'
    });
    
    new CfnOutput(this, 'FlightAgentRoleArn', {
      value: agentRoles.flightAgentRole.roleArn,
      description: 'Execution role for Flight Agent'
    });
    
    // Custom resource to deploy agents using AgentCore starter toolkit
    const agentDeployment = new CustomResource(this, 'AgentDeployment', {
      serviceToken: agentDeploymentLambda.functionArn,
      properties: {
        CognitoPoolId: authStack.userPool.userPoolId,
        CognitoClientId: authStack.userPoolClient.userPoolClientId,
        ExecutionRoles: {
          flight: agentRoles.flightAgentRole.roleArn,
          food: agentRoles.foodAgentRole.roleArn,
          airbnb: agentRoles.airbnbAgentRole.roleArn,
          booking: agentRoles.bookingAgentRole.roleArn,
          orchestrator: agentRoles.orchestratorRole.roleArn
        }
      }
    });
  }
}
```

### 3. Agent Resource Requirements

| Agent | Memory | Model | Browser Tools | Estimated Cost/Hour |
|-------|--------|-------|---------------|-------------------|
| Flight Agent | 2048 MB | Claude 3.5 Sonnet | Enabled | $0.08 |
| Food Agent | 512 MB | Claude 3 Haiku | Disabled | $0.02 |
| Airbnb Agent | 2048 MB | Claude 3.5 Sonnet | Enabled | $0.08 |
| Booking Agent | 2048 MB | Claude 3.5 Sonnet | Enabled | $0.08 |
| Orchestrator | 2048 MB | Claude 3.5 Sonnet | Disabled | $0.06 |

**Total Estimated Cost**: ~$0.32/hour for all 5 agents (consumption-based pricing)

### 4. Deployment Benefits
- **Simplified Operations**: Single command deployment per agent
- **Built-in Features**: Authentication, memory, browser tools, observability included
- **Easy Testing**: Built-in `agentcore invoke` for immediate testing
- **Rapid Iteration**: Quick deployment and testing cycles
- **Production Ready**: Enterprise security and scaling built-in

### 2. Environment Management
- **Development**: Single region, reduced resources
- **Staging**: Production mirror for testing
- **Production**: Multi-AZ, auto-scaling, monitoring

### 3. CI/CD Pipeline
```yaml
# GitHub Actions workflow
stages:
  - unit_tests
  - integration_tests  
  - security_scan
  - deploy_staging
  - e2e_tests
  - deploy_production
```

This architecture ensures reliability, scalability, and maintainability while leveraging cutting-edge AWS AI agent capabilities for superior travel planning.
