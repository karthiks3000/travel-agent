# Travel Orchestrator Agent

The Travel Orchestrator Agent is the main conversational interface for comprehensive travel planning. It coordinates multiple specialist agents (flights, accommodations, restaurants) to create personalized travel plans through intelligent conversation management and parallel agent orchestration.

## Architecture Overview

The Travel Orchestrator Agent follows a sophisticated multi-agent architecture:

```
User Request → Travel Orchestrator → [Flight Agent, Accommodation Agent, Food Agent] → Synthesized Plan
```

### Key Components

1. **Conversation Management**: Intelligent information gathering with context awareness
2. **Validation System**: Tool-based validation ensures complete information before delegation
3. **Agent Orchestration**: Parallel invocation of specialist agents via AgentCore Runtime
4. **Plan Synthesis**: Combines results from multiple agents into coherent travel plans
5. **Memory Integration**: AgentCore Memory for user preferences and context preservation

## Features

### 🧠 Intelligent Information Gathering
- Progressive disclosure of travel requirements
- Context-aware clarifying questions
- Automatic inference of missing information (passengers = guests, etc.)
- Date validation with past date rejection

### 🔄 Multi-Agent Orchestration  
- Parallel execution of specialist agents
- Natural language delegation to specialist agents
- Graceful handling of agent failures
- Real-time streaming responses

### 📊 Plan Synthesis
- Cost estimation across all travel components
- Intelligent recommendations (cheapest flights, best-rated hotels)
- Confidence scoring based on agent success rates
- Comprehensive travel plan generation

### 💾 AgentCore Memory Integration
- **Short-term Memory**: Conversation context preservation across turns
- **Session Management**: Consistent session_id shared across all agents
- **Actor Isolation**: Each agent has unique actor_id within shared session
- **Automatic Memory Hooks**: Load context on initialization, save messages automatically
- **Cross-Agent Context**: All specialist agents access shared conversation history
- **Memory Expiry**: Conversations automatically expire after 7 days

## Agent Tools

### Core Validation Tool
```python
@tool
def validate_travel_information(travel_info_dict: dict) -> ValidationResult:
    """Validates travel information completeness before agent delegation"""
```

### Specialist Agent Integration Tools
```python
@tool  
def search_flights(travel_request: str, session_id: str = None) -> AgentSearchResult:
    """Delegates to flight specialist agent"""

@tool
def search_accommodations(travel_request: str, session_id: str = None) -> AgentSearchResult:
    """Delegates to accommodation specialist agent"""

@tool
def search_restaurants(travel_request: str, session_id: str = None) -> AgentSearchResult:
    """Delegates to food specialist agent"""
```

### Comprehensive Planning Tool
```python
@tool
def plan_comprehensive_trip(travel_info_dict: dict, session_id: str = None) -> ComprehensiveTravelPlan:
    """Orchestrates all agents for complete travel planning"""
```

## Conversation Flow Examples

### Initial Request
```
User: "Plan a trip to Paris"

Orchestrator: "I'd love to help plan your Paris trip! To find the best options, I need:
- What city will you be departing from?
- What are your travel dates?  
- How many people will be traveling?"
```

### Progressive Information Gathering
```
User: "From NYC, sometime in June, 2 people"

Orchestrator: "Great! NYC to Paris for 2 people in June. I need specific dates to search:
- What's your preferred departure date in June?
- How many nights will you be staying in Paris?"
```

### Complete Information Processing
```
User: "June 15th departure, staying 5 nights"

Orchestrator: "Perfect! Let me search for:
✈️  Flights: NYC to Paris June 15-20 for 2 passengers
🏨 Accommodations: Paris hotels/Airbnb June 15-20 for 2 guests  
🍽️  Restaurants: Paris dining recommendations

[Initiates parallel agent searches...]"
```

## Required Information by Agent

### Flight Agent Requirements
- ✅ **origin**: Departure city/airport
- ✅ **destination**: Destination city  
- ✅ **departure_date**: Specific departure date
- ✅ **passengers**: Number of passengers
- ✅ **return_date**: For round-trip flights

### Accommodation Agent Requirements  
- ✅ **destination**: Destination city
- ✅ **check_in**: Check-in date
- ✅ **check_out**: Check-out date
- ✅ **guests**: Number of guests

### Restaurant Agent Requirements
- ✅ **destination**: Destination city (minimum)
- ⚠️ **dietary_restrictions**: Optional but recommended

## Environment Variables

```bash
# Specialist Agent ARNs
FLIGHT_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:account:agent-runtime/flight-agent
ACCOMMODATION_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:account:agent-runtime/accommodation-agent
FOOD_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:account:agent-runtime/food-agent

# AWS Configuration
AGENTCORE_REGION=us-east-1
```

## Deployment

### Prerequisites
- Python 3.9+
- AWS CLI configured with appropriate permissions
- AgentCore Runtime deployment environment

### Installation
```bash
pip install -r requirements.txt
```

### AgentCore Runtime Deployment
```bash
# Deploy Travel Orchestrator Agent
agentcore configure \
  --entrypoint travel_orchestrator.py \
  --name travel-orchestrator \
  --execution-role $ORCHESTRATOR_ROLE_ARN \
  --requirements-file requirements.txt \
  --memory-size 2048 \
  --model "amazon.nova-pro-v1:0" \
  --memory-config '{"strategy": "user_preferences"}' \
  --authorizer-config '{"customJWTAuthorizer":{"discoveryUrl":"'$COGNITO_DISCOVERY_URL'","allowedClients":["'$COGNITO_CLIENT_ID'"]}}'

agentcore launch
```

### Local Testing
```bash
python travel_orchestrator.py
```

## Data Models

### TravelInformation
Core travel information structure for validation:
```python
class TravelInformation(BaseModel):
    destination: Optional[str]
    origin: Optional[str] 
    departure_date: Optional[date]
    return_date: Optional[date]
    passengers: Optional[int]
    guests: Optional[int]
    # ... additional fields
```

### ValidationResult
Validation results with completeness analysis:
```python
class ValidationResult(BaseModel):
    can_search: Dict[str, bool]  # Agent readiness
    missing_info: Dict[str, List[str]]  # Missing requirements
    next_questions: List[str]  # Suggested questions
    completeness_score: float  # 0-1 completeness
```

### ComprehensiveTravelPlan
Synthesized travel plan from multiple agents:
```python
class ComprehensiveTravelPlan(BaseModel):
    destination: str
    origin: str
    dates: Dict[str, str]
    flight_results: Optional[AgentSearchResult]
    accommodation_results: Optional[AgentSearchResult]  
    restaurant_results: Optional[AgentSearchResult]
    recommendations: Dict[str, Any]
    total_estimated_cost: Optional[float]
```

## System Prompt Strategy

The orchestrator uses a comprehensive system prompt that includes:

1. **Role Definition**: Main conversational interface for travel planning
2. **Workflow Rules**: Information gathering → Validation → Delegation → Synthesis
3. **Critical Rules**: Validation-first approach, progressive disclosure
4. **Agent Requirements**: Clear requirements for each specialist agent
5. **Conversation Examples**: Concrete examples of interaction patterns
6. **Memory Integration**: Guidelines for using AgentCore Memory

## Error Handling

- **Agent Failures**: Graceful degradation with partial results
- **Validation Errors**: Clear error messages with correction guidance  
- **Date Validation**: Rejection of past dates with helpful suggestions
- **Missing Information**: Targeted questions to fill information gaps
- **Network Issues**: Retry logic and fallback responses

## Performance Characteristics

- **Parallel Execution**: All specialist agents run simultaneously
- **Streaming Responses**: Real-time updates as agents complete
- **Memory Efficiency**: Intelligent context management
- **Session Management**: Context preservation across conversations
- **Cost Optimization**: Validation prevents unnecessary agent calls

## Testing

### Unit Tests
Test individual validation and formatting functions:
```bash
python -m pytest tests/test_validation_tools.py
python -m pytest tests/test_agent_invocation.py
```

### Integration Tests  
Test end-to-end orchestration flows:
```bash
python -m pytest tests/test_orchestrator_integration.py
```

### Manual Testing
```bash
# Test with sample travel request
python test_orchestrator.py
```

## Monitoring & Observability

The agent provides comprehensive logging and metrics:
- **Agent Invocation Tracking**: Success rates, response times
- **Validation Metrics**: Completeness scores, missing information patterns
- **Conversation Analytics**: Question patterns, user interaction flows
- **Plan Generation Metrics**: Synthesis success rates, recommendation accuracy

## Future Enhancements

- [ ] **Multi-City Trip Support**: Complex itinerary planning
- [ ] **Budget Optimization**: Advanced cost analysis and recommendations
- [ ] **Activity Integration**: Events and attractions planning
- [ ] **Group Travel**: Advanced group coordination features
- [ ] **Real-time Booking**: Direct booking integration
- [ ] **Mobile Optimization**: Mobile-specific conversation flows

## Contributing

1. Follow existing code patterns and type hints
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Use Pydantic models for all data structures
5. Implement proper error handling and logging

## License

This project is part of the AI Travel Agent system. See LICENSE file for details.
