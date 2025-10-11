# Travel Orchestrator Agent

The Travel Orchestrator Agent is a **single, intelligent agent** that provides comprehensive travel planning through integrated tools and data sources. It combines flight search, accommodation search, and restaurant recommendations into a unified conversational interface.

## Architecture Overview

The Travel Orchestrator Agent uses a **single-agent architecture** with integrated tools:

```
User Request → Travel Orchestrator Agent → [Amadeus API, Nova Act Browser, Google Maps API] → Synthesized Plan
```

### Key Components

1. **Conversation Management**: Intelligent information gathering with context awareness
2. **Integrated Tools**: Direct integration with travel data sources
3. **Parameter Validation**: Ensures complete information before tool execution
4. **Result Synthesis**: Combines results from multiple data sources into coherent travel plans
5. **Memory Integration**: AgentCore Memory for user preferences and context preservation

## Features

### 🧠 Intelligent Information Gathering
- Progressive disclosure of travel requirements
- Context-aware clarifying questions
- Automatic inference of missing information (passengers = guests, etc.)
- Date validation with past date rejection
- Parameter mapping between different tools

### 🔄 Integrated Tool Execution
- **Flight Search**: Real-time Amadeus API integration
- **Accommodation Search**: Nova Act browser automation for Airbnb & Booking.com
- **Restaurant Search**: Google Maps API via AgentCore Gateway
- Graceful error handling for tool failures
- Real-time JSON responses with structured data

### 📊 Plan Synthesis
- Cost estimation across all travel components
- Intelligent recommendations (best value flights, highest-rated accommodations)
- Confidence scoring based on tool success rates
- Comprehensive travel plan generation with itineraries

### 💾 AgentCore Memory Integration
- **Short-term Memory**: Conversation context preservation across turns
- **Session Management**: User-specific session tracking
- **Automatic Memory Hooks**: Load context on initialization, save messages automatically
- **User Preferences**: Learning and applying travel preferences over time
- **Memory Expiry**: Conversations automatically expire after 1 day (configurable)

## Integrated Tools

### Flight Search Tool
```python
@tool
def search_flights(self, origin: str, destination: str, departure_date: str, 
                  return_date: Optional[str] = None, passengers: int = 1) -> TravelOrchestratorResponse:
    """Search flights using Amadeus Flight Offers Search API"""
    return search_flights_direct(origin, destination, departure_date, return_date, passengers)
```

### Accommodation Search Tool
```python
@tool
def search_accommodations(self, destination: str, departure_date: str, return_date: str,
                         passengers: int = 2, rooms: int = 1, 
                         platform_preference: str = "both") -> TravelOrchestratorResponse:
    """Search accommodations using Nova Act browser automation"""
    return search_accommodations_direct(destination, departure_date, return_date, passengers, rooms, platform_preference)
```

### Google Maps Integration (Auto-discovered via MCP Gateway)
```python
# Google Maps tools are automatically discovered via MCP client:
# - searchPlacesByText: Text-based place search for restaurants/attractions
# - searchNearbyPlaces: Location-based search around specific points
# - getPlaceDetails: Detailed information about specific places
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

## Required Information by Tool

### Flight Search Tool Requirements
- ✅ **origin**: Departure city/airport (IATA codes preferred)
- ✅ **destination**: Destination city/airport (IATA codes preferred)
- ✅ **departure_date**: Specific departure date (YYYY-MM-DD format)
- ✅ **passengers**: Number of passengers (1-9)
- ⚠️ **return_date**: For round-trip flights (YYYY-MM-DD format)

### Accommodation Search Tool Requirements  
- ✅ **destination**: Destination city or location
- ✅ **departure_date**: Check-in date (YYYY-MM-DD format) 
- ✅ **return_date**: Check-out date (YYYY-MM-DD format)
- ✅ **passengers**: Number of guests (1-30)
- ⚠️ **rooms**: Number of rooms (1-8, defaults to 1)
- ⚠️ **platform_preference**: "airbnb", "booking", or "both" (defaults to "both")

### Google Maps Tool Requirements
- ✅ **location**: Destination city (minimum)
- ⚠️ **query**: Specific search terms (e.g., "Italian restaurants in Paris")
- ⚠️ **type**: Place type filter (e.g., "restaurant", "tourist_attraction")

## Environment Variables

```bash
# API Credentials (stored in AWS Systems Manager Parameter Store)
AMADEUS_CLIENT_ID=your-amadeus-client-id
AMADEUS_CLIENT_SECRET=your-amadeus-client-secret
AMADEUS_HOSTNAME=test  # or 'production' for live data
NOVA_ACT_API_KEY=your-nova-act-api-key

# Gateway Configuration (for Google Maps API)
GATEWAY_URL=your-gateway-url
GATEWAY_CLIENT_ID=your-gateway-client-id
GATEWAY_CLIENT_SECRET=your-gateway-client-secret

# AWS Configuration
AGENTCORE_REGION=us-east-1
USE_AGENTCORE_BROWSER=true
```

### Parameter Store Setup
```bash
# Set up API credentials in AWS Systems Manager Parameter Store
aws ssm put-parameter --name "/travel-agent/amadeus-client-id" --value "your-client-id" --type "SecureString"
aws ssm put-parameter --name "/travel-agent/amadeus-client-secret" --value "your-client-secret" --type "SecureString"
aws ssm put-parameter --name "/travel-agent/nova-act-api-key" --value "your-api-key" --type "SecureString"
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
# Deploy Travel Orchestrator Agent (manual deployment using deployment script)
./deploy-travel-orchestrator.sh

# Alternative: Direct deployment (if AgentCore CLI is available)
agentcore configure \
  --entrypoint travel_orchestrator.py \
  --name travel-orchestrator \
  --execution-role $ORCHESTRATOR_ROLE_ARN \
  --requirements-file requirements.txt \
  --memory-size 4096 \
  --model "us.amazon.nova-premier-v1:0" \
  --memory-config '{"strategy": "user_preferences"}' \
  --authorizer-config '{"customJWTAuthorizer":{"discoveryUrl":"'$COGNITO_DISCOVERY_URL'","allowedClients":["'$COGNITO_CLIENT_ID'"]}}'

agentcore launch
```

### Local Testing
```bash
python travel_orchestrator.py
```

## Data Models

### TravelOrchestratorResponse
Main response structure for all travel planning interactions:
```python
class TravelOrchestratorResponse(BaseModel):
    response_type: ResponseType  # flights, accommodations, restaurants, etc.
    response_status: ResponseStatus  # complete_success, partial_success, etc.
    message: str
    flight_results: Optional[List[FlightResult]]
    accommodation_results: Optional[List[PropertyResult]]
    restaurant_results: Optional[List[RestaurantResult]]
    attraction_results: Optional[List[AttractionResult]]
    itinerary: Optional[Itinerary]
    success: bool
    processing_time_seconds: float
    tool_progress: List[ToolProgress]
```

### FlightResult
Structured flight search results from Amadeus API:
```python
class FlightResult(BaseModel):
    airline: str
    departure_time: str
    arrival_time: str
    departure_airport: str
    arrival_airport: str
    price: float
    duration: str
    stops: int
    stop_details: Optional[str]
    booking_class: str
```

### PropertyResult
Structured accommodation results from browser automation:
```python
class PropertyResult(BaseModel):
    platform: str  # "airbnb" or "booking_com"
    title: str
    price_per_night: Optional[float]
    total_price: Optional[float]
    rating: Optional[float]
    review_count: Optional[int]
    property_type: Optional[str]
    location: Optional[str]
    amenities: Optional[List[str]]
    url: Optional[str]
```

## System Prompt Strategy

The orchestrator uses a comprehensive system prompt that includes:

1. **Role Definition**: Expert travel planning agent with comprehensive capabilities
2. **Tool Integration**: Direct tool usage guidelines for flights, accommodations, and restaurants
3. **Parameter Validation**: Complete parameter validation before tool execution
4. **Response Format**: Mandatory JSON response format using TravelOrchestratorResponse
5. **Request Type Detection**: Intelligent detection of user intent (specific vs. multiple options)
6. **Google Maps Integration**: Direct usage of Google Places API tools
7. **Memory Integration**: Guidelines for using AgentCore Memory for personalization

## Error Handling

- **Tool Failures**: Graceful degradation with partial results and clear error messages
- **Parameter Validation**: Comprehensive validation with specific error details
- **Date Validation**: Rejection of past dates with helpful suggestions
- **API Errors**: Amadeus API error handling with user-friendly messages
- **Browser Automation**: Nova Act session management and error recovery
- **Network Issues**: Retry logic and timeout handling
- **Missing Credentials**: Clear guidance for API key setup

## Performance Characteristics

- **Tool Execution**: Sequential tool execution with validation
- **JSON Responses**: Fast, structured responses without streaming
- **Memory Efficiency**: Intelligent context management with AgentCore Memory
- **Session Management**: Context preservation across conversations
- **Cost Optimization**: Parameter validation prevents unnecessary API calls
- **API Performance**: 
  - Flight Search: 3-5 seconds (Amadeus API)
  - Accommodation Search: 15-30 seconds (browser automation)
  - Restaurant Search: 2-3 seconds (Google Maps API)

## Testing

### Unit Tests
Test individual validation and formatting functions:
```bash
python -m pytest tests/test_validation_tools.py
python -m pytest tests/test_agent_invocation.py
```

### Integration Tests  
Test end-to-end tool integration:
```bash
python -m pytest tests/test_tool_integration.py
python -m pytest tests/test_amadeus_integration.py
```

### Manual Testing
```bash
# Test individual tools
python -c "
from tools.flight_search_tool import search_flights_direct
result = search_flights_direct('JFK', 'CDG', '2024-12-15', '2024-12-22', 2)
print(result.message)
"

# Test the full orchestrator
python travel_orchestrator.py
```

## Monitoring & Observability

The agent provides comprehensive logging and metrics:
- **Tool Execution Tracking**: Success rates, response times for each tool
- **Parameter Validation Metrics**: Validation success rates, common errors
- **Conversation Analytics**: Question patterns, user interaction flows
- **API Performance Metrics**: Amadeus API response times, error rates
- **Browser Automation Metrics**: Nova Act success rates, failure modes
- **Memory Usage**: AgentCore Memory utilization and performance

## Current Capabilities & Future Enhancements

### ✅ Currently Implemented
- Real-time flight search with Amadeus API
- Comprehensive accommodation search (Airbnb + Booking.com)
- Restaurant and attraction recommendations via Google Maps
- User authentication and session management
- Memory integration for personalization
- Structured JSON responses with comprehensive data

### 🚧 In Development
- Advanced personalization with user preference learning
- Enhanced itinerary generation algorithms
- Improved error handling and recovery
- Performance optimizations

### 📋 Future Enhancements
- [ ] **Multi-City Trip Support**: Complex itinerary planning
- [ ] **Budget Optimization**: Advanced cost analysis and recommendations
- [ ] **Real-time Booking**: Direct booking integration
- [ ] **Group Travel**: Advanced group coordination features
- [ ] **Mobile Optimization**: Mobile-specific conversation flows
- [ ] **Advanced Memory**: Long-term user preference learning

## Contributing

1. Follow existing code patterns and type hints
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Use Pydantic models for all data structures
5. Implement proper error handling and logging

## License

This project is part of the AI Travel Agent system. See LICENSE file for details.
