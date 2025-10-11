# AI Travel Agent - Technical Architecture

## System Architecture Overview

The AI Travel Agent uses a **single orchestrator agent** architecture built on AWS Bedrock AgentCore Runtime with integrated tools for comprehensive travel planning.

```
┌─────────────────────────────────────────┐
│           Frontend                      │
│      React 18 + TypeScript              │
│      TailwindCSS + Aceternity UI        │
│                                         │
│   ┌─────────────────────────────────┐   │
│   │    Direct HTTP Connection to    │   │◄─────────┐
│   │    AgentCore Runtime            │   │          │
│   └─────────────────────────────────────┘   │          │
└─────────────────────────────────────────┘          │
                     │                                 │
                     ▼                                 │
┌─────────────────────────────────────────────────────┐│
│      Travel Orchestrator Agent                     ││
│         (Single AgentCore Runtime)                 ││
│  ┌─────────────────┐  ┌─────────────────────────┐  ││
│  │   Cognito JWT   │  │   Orchestration Logic   │  ││
│  │  Authentication │◄─┤   + Memory Integration  │  ││
│  │                 │  │   + Result Synthesis    │  ││
│  └─────────────────┘  └─────────────────────────┘  ││
└─────────────────────────────────────────────────────┘│
                     │ (Integrated Tools)               │
                     ▼                                 │
┌─────────────┬─────────────┬─────────────────────────┐│
│ Amadeus     │ Nova Act    │ Google Maps             ││
│ Flight API  │ Browser     │ API Gateway             ││
│             │ Automation  │                         ││
│ ┌─────────┐ │ ┌─────────┐ │ ┌─────────────────────┐ ││
│ │Real-time│ │ │ Airbnb  │ │ │   Restaurants &     │ ││
│ │Flight   │ │ │Booking  │ │ │   Attractions       │ ││
│ │Pricing  │ │ │Search   │ │ │   via MCP Client    │ ││
│ └─────────┘ │ └─────────┘ │ └─────────────────────┘ ││
└─────────────┴─────────────┴─────────────────────────┘│
                                                      │
┌─────────────────────────────────────────────────────┘
│         Built-in Observability & Monitoring  
│  ┌──────────────────────────────────────────────┐
│  │  • AgentCore Runtime Observability          │
│  │  • Tool Execution Monitoring                │
│  │  • Memory Usage & Performance Metrics       │
│  │  • Built-in Rate Limiting & Error Handling  │
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
- Authentication flow integration with Cognito

**Key Features**:
```typescript
interface TravelRequest {
  prompt: string;
  user_id?: string;
  region?: string;
}

interface TravelOrchestratorResponse {
  response_type: "flights" | "accommodations" | "restaurants" | "attractions" | "itinerary" | "mixed_results" | "conversation";
  response_status: "complete_success" | "partial_success" | "validation_error" | "tool_error" | "system_error";
  message: string;
  flight_results?: FlightResult[];
  accommodation_results?: PropertyResult[];
  restaurant_results?: RestaurantResult[];
  attraction_results?: AttractionResult[];
  itinerary?: Itinerary;
  success: boolean;
  processing_time_seconds: number;
  tool_progress: ToolProgress[];
}
```

**Direct AgentCore Integration**:
```typescript
const agentResponse = await fetch(
  `https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/${AGENT_ARN}/invocations`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${cognitoToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ prompt: userMessage })
  }
);
```

### 2. Travel Orchestrator Agent
**Technology**: Strands Agents SDK + AgentCore Runtime + BedrockAgentCoreApp

**Architecture Pattern**: Single agent with multiple integrated tools

**Agent Implementation**:
```python
from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient

class TravelOrchestratorAgent(Agent):
    def __init__(self, memory_id: Optional[str] = None, session_id: Optional[str] = None, 
                 actor_id: Optional[str] = None, region: str = "us-east-1"):
        # Configure Nova Premier model for enhanced reasoning
        model = BedrockModel(
            model_id="us.amazon.nova-premier-v1:0",
            max_tokens=10000,
            temperature=0.7
        )
        
        # Initialize with integrated tools
        super().__init__(
            model=model,
            tools=[
                self.search_flights,        # Amadeus API integration
                self.search_accommodations, # Nova Act browser automation
                # Google Maps tools auto-discovered via MCP Gateway
            ],
            hooks=[memory_hooks] if memory_id else []
        )
    
    @tool
    def search_flights(self, origin: str, destination: str, departure_date: str, 
                      return_date: Optional[str] = None, passengers: int = 1) -> TravelOrchestratorResponse:
        """Search flights using Amadeus Flight Offers Search API"""
        return search_flights_direct(origin, destination, departure_date, return_date, passengers)
    
    @tool  
    def search_accommodations(self, destination: str, departure_date: str, return_date: str,
                            passengers: int = 2, rooms: int = 1, platform_preference: str = "both") -> TravelOrchestratorResponse:
        """Search accommodations using Nova Act browser automation"""
        return search_accommodations_direct(destination, departure_date, return_date, passengers, rooms, platform_preference)

app = BedrockAgentCoreApp()

@app.entrypoint
def travel_orchestrator_invocation(payload, context=None):
    """Non-streaming JSON response entry point"""
    agent = TravelOrchestratorAgent(
        memory_id=initialize_memory(),
        session_id=context.session_id if context else None,
        actor_id="travel-orchestrator"
    )
    
    result = agent(payload["prompt"])
    return parse_agent_response(result)
```

### 3. Integrated Tool System

The Travel Orchestrator Agent uses **integrated tools** rather than separate agents for better reliability and performance.

**Tool Architecture**:

**1. Flight Search Tool (Amadeus API Integration)**
```python
# tools/flight_search_tool.py
from amadeus import Client

def search_flights_direct(origin: str, destination: str, departure_date: str, 
                         return_date: Optional[str] = None, passengers: int = 1) -> TravelOrchestratorResponse:
    """Search flights using Amadeus Flight Offers Search API"""
    
    # Initialize Amadeus client
    amadeus = Client(
        client_id=os.getenv('AMADEUS_CLIENT_ID'),
        client_secret=os.getenv('AMADEUS_CLIENT_SECRET'),
        hostname=os.getenv('AMADEUS_HOSTNAME', 'test')
    )
    
    # Search flights
    response = amadeus.shopping.flight_offers_search.get(
        originLocationCode=origin.upper(),
        destinationLocationCode=destination.upper(),  
        departureDate=departure_date,
        returnDate=return_date,
        adults=passengers,
        currencyCode='USD'
    )
    
    # Parse and return structured results
    return TravelOrchestratorResponse(
        response_type=ResponseType.FLIGHTS,
        flight_results=parse_amadeus_results(response.data),
        success=True
    )
```

**2. Accommodation Search Tool (Nova Act Browser Automation)**
```python
# tools/accommodation_search_tool.py
from common.browser_wrapper import BrowserWrapper

def search_accommodations_direct(location: str, check_in: str, check_out: str,
                               guests: int = 2, rooms: int = 1, 
                               platform_preference: str = "both") -> TravelOrchestratorResponse:
    """Search accommodations using Nova Act browser automation"""
    
    browser_wrapper = BrowserWrapper(
        api_key=os.getenv('NOVA_ACT_API_KEY'),
        use_agentcore_browser=True
    )
    
    # Search both platforms
    airbnb_results = search_airbnb(browser_wrapper, location, check_in, check_out, guests)
    booking_results = search_booking_com(browser_wrapper, location, check_in, check_out, guests, rooms)
    
    # Combine and rank results
    best_accommodations = combine_and_sort_results(airbnb_results, booking_results)
    
    return TravelOrchestratorResponse(
        response_type=ResponseType.ACCOMMODATIONS,
        accommodation_results=best_accommodations,
        success=True
    )
```

**3. Google Maps Integration (MCP Gateway)**
```python
# Google Maps tools auto-discovered via MCP client
def initialize_google_maps_tools():
    """Initialize Google Maps tools via AgentCore Gateway"""
    
    # Create MCP transport to Gateway
    def create_gateway_transport():
        return streamablehttp_client(
            gateway_url,
            headers={"Authorization": f"Bearer {access_token}"}
        )
    
    # Initialize MCP client
    mcp_client = MCPClient(create_gateway_transport)
    mcp_client.start()
    
    # Auto-discover Google Maps tools
    google_maps_tools = mcp_client.list_tools_sync()
    
    # Available tools: searchPlacesByText, searchNearbyPlaces, getPlaceDetails
    return google_maps_tools
```

**Single-Agent Benefits**:
- **Simplified Architecture**: No inter-agent communication complexity
- **Better Error Handling**: Single point of failure management
- **Faster Response Times**: No network overhead between agents
- **Easier Debugging**: Single execution context
- **Resource Efficiency**: Shared memory and processing
- **Consistent State**: Single agent maintains conversation context

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
| Amadeus Flight API | REST API | Real-time flight prices & schedules | 2,000 calls/month (free tier) |
| Google Maps API | REST API via Gateway | Restaurant/attraction data | Via Google Cloud quotas |
| Airbnb | Browser Automation (Nova Act) | Accommodation listings | Self-imposed: 1 req/2sec |
| Booking.com | Browser Automation (Nova Act) | Hotel listings | Self-imposed: 1 req/2sec |

**Current Implementation Notes**:
- **Flights**: Amadeus API provides real-time, accurate flight pricing and schedules
- **Restaurants/Attractions**: Google Maps API via AgentCore Gateway with MCP client
- **Accommodations**: Nova Act browser automation for platforms without public APIs
- **Authentication**: All APIs use secure credential storage via AWS Systems Manager

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

### 1. Single Agent Deployment Workflow

**Travel Orchestrator Agent Deployment** (Current Implementation)
```bash
#!/bin/bash

# Prerequisites setup
echo "Setting up Travel Agent Single-Agent System..."

# Install required packages
pip install boto3 strands amazon-bedrock-agentcore

# Set up AWS credentials and region
export AWS_DEFAULT_REGION=us-east-1

# Deploy infrastructure first
cd cdk
npm install
npm run deploy

# Deploy the single travel orchestrator agent
cd ../agents/travel_orchestrator
./deploy-travel-orchestrator.sh

echo "Travel Orchestrator Agent deployed successfully!"

# Test end-to-end system
echo "Testing travel orchestrator..."
python -c "
from travel_orchestrator import travel_orchestrator_invocation
result = travel_orchestrator_invocation({'prompt': 'Find flights from JFK to CDG on Dec 15, 2024'})
print('Test result:', result)
"
```

**Manual Deployment via AgentCore CLI** (Alternative)
```bash
# If using AgentCore CLI (experimental)
agentcore configure \
  --entrypoint travel_orchestrator.py \
  --name travel-orchestrator \
  --execution-role $TRAVEL_ORCHESTRATOR_ROLE_ARN \
  --requirements-file requirements.txt \
  --memory-size 4096 \
  --model "us.amazon.nova-premier-v1:0" \
  --memory-config '{"strategy": "user_preferences"}' \
  --authorizer-config '{"customJWTAuthorizer":{"discoveryUrl":"'$COGNITO_DISCOVERY_URL'","allowedClients":["'$COGNITO_CLIENT_ID'"]}}'

agentcore launch
```

### 2. Infrastructure Deployment via CDK

**CDK Stack for Supporting Infrastructure**
```typescript
export class TravelAgentStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps) {
    super(scope, id, props);
    
    // 1. Deploy Cognito for authentication
    const cognitoStack = new CognitoStack(this, 'CognitoStack', {
      environment: props.environment,
    });
    
    // 2. Deploy frontend hosting (S3 + CloudFront)
    const frontendBucket = new s3.Bucket(this, 'FrontendBucket', {
      bucketName: `travel-agent-frontend-${props.environment}-${cdk.Aws.ACCOUNT_ID}-${cdk.Aws.REGION}`,
      // ... bucket configuration
    });
    
    const distribution = new cloudfront.Distribution(this, 'FrontendDistribution', {
      // ... CloudFront configuration
    });
    
    // 3. Create S3 bucket for Gateway OpenAPI specifications
    const gatewayBucket = new s3.Bucket(this, 'GatewayOpenAPIBucket', {
      bucketName: `travel-agent-gateway-${props.environment}-${cdk.Aws.ACCOUNT_ID}-${cdk.Aws.REGION}`,
      // ... gateway bucket configuration
    });
    
    // 4. Output configuration for manual agent deployment
    new CfnOutput(this, 'CognitoUserPoolId', {
      value: cognitoStack.userPool.userPoolId,
      exportName: `TravelAgent-${props.environment}-UserPoolId`,
    });
    
    new CfnOutput(this, 'CognitoUserPoolClientId', {
      value: cognitoStack.userPoolClient.userPoolClientId,
      exportName: `TravelAgent-${props.environment}-UserPoolClientId`,
    });
  }
}
```

### 3. Current Resource Requirements

**Single Travel Orchestrator Agent**:
- **Memory**: 4GB (increased for Nova Premier model)
- **Model**: Amazon Nova Premier v1.0 
- **Browser Tools**: Enabled for accommodation search
- **Memory**: AgentCore Memory enabled for personalization
- **Estimated Cost**: ~$0.10-0.15/hour (consumption-based pricing)

**Supporting Infrastructure**:
- **S3 Buckets**: Frontend hosting + Gateway specs
- **CloudFront**: Global content delivery
- **Cognito**: User authentication
- **Parameter Store**: Secure credential storage
- **Gateway**: Google Maps API integration

### 4. Deployment Benefits
- **Simplified Architecture**: Single agent deployment eliminates complexity
- **Built-in Features**: Authentication, memory, browser tools, observability included  
- **Easy Testing**: Direct Python execution for local testing
- **Rapid Iteration**: Quick development and testing cycles
- **Production Ready**: Enterprise security and scaling via AgentCore Runtime
- **Cost Effective**: Single agent reduces resource overhead

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
