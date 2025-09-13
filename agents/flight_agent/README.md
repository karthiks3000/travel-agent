# Flight Agent - Bedrock AgentCore Implementation

A flight search agent using Nova Act browser automation and Strands framework for intelligent flight search on Google Flights.

## Setup

### Prerequisites
- Python 3.10 or higher
- Nova Act API key (get from https://nova.amazon.com/act)
- AWS CLI configured (for deployment)

### Development Setup (Required)

Before running locally, create a symbolic link to the shared common directory:

```bash
# Navigate to flight agent directory
cd agents/flight_agent

# Create symbolic link to common directory (required for local development)
ln -sf ../../common common

# Verify the link was created
ls -la common
```

**Important**: This symbolic link is required for local development to access shared browser automation code. It will be handled automatically during AgentCore deployment.

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up Nova Act API key
export NOVA_ACT_API_KEY="your_api_key_here"
```

### Optional: Install Google Chrome
Nova Act works best with Google Chrome:
```bash
playwright install chrome
```

## Usage

### As a Strands Agent

```python
from flight_agent import agent

# Natural language flight search
response = agent("Find me the cheapest flight from New York to Los Angeles for next Friday")
print(response)

# Specific flight search request
response = agent("I need round-trip flights from JFK to CDG departing June 15th and returning June 22nd for 2 passengers")
print(response)
```

### Direct Tool Usage

```python
from flight_agent import agent

# Direct tool call
result = agent.tool.search_google_flights(
    origin="JFK",
    destination="LAX",
    departure_date="2024-06-15",
    passengers=1
)

print(f"Success: {result.get('success')}")
if result.get('outbound_flights'):
    for flight in result['outbound_flights'][:3]:
        print(f"{flight['airline']}: ${flight['price']} - {flight['duration']}")
```

### Available Tool

#### `search_google_flights(origin, destination, departure_date, return_date=None, passengers=1)`

Search Google Flights for flight options.

**Parameters:**
- `origin`: Origin airport code or city (e.g., 'JFK', 'New York')
- `destination`: Destination airport code or city (e.g., 'LAX', 'Los Angeles')
- `departure_date`: Departure date in YYYY-MM-DD format
- `return_date`: Return date for round-trip (optional)
- `passengers`: Number of passengers (1-9)

**Returns:**
```json
{
  "success": true,
  "search_params": {...},
  "outbound_flights": [
    {
      "airline": "Delta",
      "departure_time": "10:30 AM",
      "arrival_time": "2:45 PM",
      "departure_airport": "JFK",
      "arrival_airport": "LAX",
      "price": 542,
      "duration": "5h 15m",
      "stops": 0,
      "booking_class": "Economy"
    }
  ]
}
```

## Local Testing

### Test the Agent

```bash
# Run local tests
python flight_agent.py

# Run demo with natural language examples
python demo_strands.py
```

### Direct API Testing

```bash
# Test a specific flight search
python -c "
from flight_agent import agent
result = agent.tool.search_google_flights('JFK', 'LAX', '2024-06-15')
print('Success:', result.get('success', False))
"
```

## Deployment to AWS Bedrock AgentCore

### Prerequisites for Deployment
- AWS CLI configured with 'bookhood' profile
- AgentCore CLI installed
- Nova Act API key set in environment

### Deploy to AgentCore

```bash
# Set your Nova Act API key
export NOVA_ACT_API_KEY="your_api_key_here"

# Run deployment script
./deploy-flight-agent.sh
```

The deployment script will:
1. ✅ Store API key securely in AWS Parameter Store
2. ✅ Create IAM execution role with required permissions
3. ✅ Temporarily copy common directory for build
4. ✅ Deploy agent to Bedrock AgentCore using CodeBuild
5. ✅ Clean up temporary files after deployment
6. ✅ Test the deployed agent

### Test Deployed Agent

```bash
# Test the deployed agent
agentcore invoke '{"prompt": "Find me flights from JFK to LAX"}'

# Check agent status
agentcore status
```

## Architecture

The flight agent uses:
- **Nova Pro Model**: For natural language understanding and response generation
- **Nova Act Browser Automation**: For Google Flights interaction
- **Shared Browser Wrapper**: Reusable browser automation component
- **Parameter Store**: Secure API key management
- **AgentCore Runtime**: Production deployment platform

## Browser Configuration

### Local Browser (Default for Development)
```python
# Uses local Chrome installation
# Set via environment: USE_AGENTCORE_BROWSER=false
```

### AgentCore Browser (Production)
```python
# Uses AgentCore managed browser sessions
# Set via environment: USE_AGENTCORE_BROWSER=true
```

## Key Features

- ✅ **Natural Language Interface**: Understands requests like "find flights next Friday"
- ✅ **Date Intelligence**: Interprets relative dates using current date context
- ✅ **Google Flights Integration**: Platform-specific search logic
- ✅ **Structured Data**: Returns validated flight information
- ✅ **Error Handling**: Graceful failure handling and reporting
- ✅ **Deployment Ready**: Full AgentCore integration for production use

## Troubleshooting

### Common Issues

**Import Error: No module named 'common'**
```bash
# Ensure symbolic link is created
cd agents/flight_agent
ln -sf ../../common common
ls -la common  # Should show link to ../../common
```

**Agent Runtime Error in AgentCore**
- Check CloudWatch logs: `/aws/bedrock-agentcore/runtimes/flight_agent-*/`
- Verify Nova Act API key in Parameter Store
- Ensure IAM role has all required permissions

**Browser Automation Timeouts**
- Google Flights interface may have changed
- Check if basic economy dialog appears and needs handling
- Verify Nova Act API key is valid

### Development Commands

```bash
# Local testing
python flight_agent.py

# Natural language demo
python demo_strands.py

# Deploy to AgentCore
./deploy-flight-agent.sh

# Check deployment status
agentcore status

# Update deployed agent
agentcore launch

# Remove deployed agent
agentcore destroy
```

The flight agent is designed to work both as a standalone tool and as part of a larger multi-agent travel planning system.
