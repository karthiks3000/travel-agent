# Food Agent - Google Places API Integration

A simple Strands agent that searches for restaurants using Google Places Text Search API.

## Features

- **Natural Language Queries**: Search using plain English (e.g., "Italian restaurants in Rome")
- **Google Places API**: Direct integration with Google's comprehensive restaurant database
- **Strands Agent**: Built for Amazon Bedrock AgentCore Runtime
- **Simple Tool Interface**: Single `search_restaurants` tool for easy integration

## Setup

### Prerequisites

1. **Google Cloud Project** with Places API enabled
2. **API Key** for Google Places API
3. **Environment Variable**: Set `GOOGLE_PLACES_API_KEY`

### Installation

```bash
cd agents/food_agent
pip install -r requirements.txt
```

### Environment Configuration

```bash
export GOOGLE_PLACES_API_KEY="your_api_key_here"
```

## Usage

### As Conversational Agent

```python
from food_agent import FoodAgent

agent = FoodAgent()

# Natural language conversation - agent will use tools as needed
response = agent.run("I'm hungry and want Italian food in Rome. Can you help me find some good restaurants?")
print(response)
```

### Direct Tool Usage (for other agents)

```python
# Other agents can call the tool directly
results = agent.search_restaurants("Vegetarian restaurants near Times Square, NYC")
print(results)
```

### Example Queries

- `"Italian restaurants in Rome"`
- `"Cheap street food in Bangkok"`
- `"Fine dining French restaurants in Paris"`
- `"Gluten-free restaurants near Central Park"`
- `"Vegan sushi in Tokyo"`

### Response Format

```json
{
  "success": true,
  "query": "Italian restaurants in Rome",
  "places": [
    {
      "displayName": {"text": "Restaurant Name"},
      "formattedAddress": "123 Main St, Rome, Italy",
      "rating": 4.5,
      "userRatingCount": 1234,
      "priceLevel": "PRICE_LEVEL_MODERATE",
      "nationalPhoneNumber": "+39 06 123 4567",
      "websiteUri": "https://restaurant.com",
      "currentOpeningHours": {"openNow": true}
    }
  ],
  "total_results": 20
}
```

## Deployment

### Automated Deployment with Script (Recommended)

The easiest way to deploy is using the automated deployment script:

```bash
# Set your Google Places API key
export GOOGLE_PLACES_API_KEY="your_api_key_here"

# Run the deployment script
cd agents/food_agent
./deploy-food-agent.sh
```

**The script handles:**
- ✅ Parameter Store setup with API key
- ✅ IAM policy creation for Parameter Store access  
- ✅ Local build with Podman
- ✅ AgentCore configuration and deployment
- ✅ End-to-end testing

### Manual AgentCore Runtime Deployment

```bash
# 1. Store API key in Parameter Store
aws ssm put-parameter \
  --name "/travel-agent/google-places-api-key" \
  --value "$GOOGLE_PLACES_API_KEY" \
  --type "SecureString" \
  --profile bookhood

# 2. Configure agent
agentcore configure \
  --entrypoint food_agent.py \
  --name food-agent \
  --requirements-file requirements.txt \
  --memory-size 512 \
  --model "amazon.nova-pro-v1:0"

# 3. Launch agent
agentcore launch

# 4. Test deployment  
agentcore invoke '{"prompt": "Find Italian restaurants in Rome"}'
```

### IAM Requirements

Ensure your AgentCore execution role has the `FoodAgentParameterStoreAccess` policy:

```json
{
  "Version": "2012-10-17", 
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ssm:GetParameter"],
      "Resource": "arn:aws:ssm:*:*:parameter/travel-agent/*"
    }
  ]
}
```

## Integration with Travel Orchestrator

The food agent can be invoked by other agents in your multi-agent system:

```python
# In Travel Orchestrator Agent
food_results = await self._invoke_specialist_agent("food", {
    "prompt": "Find restaurants in Paris for dinner tonight"
})
```

## API Reference

### search_restaurants(text_query: str) -> dict

Search for restaurants using natural language queries.

**Parameters:**
- `text_query` (str): Natural language search query

**Returns:**
- `dict`: Restaurant search results from Google Places API

**Example:**
```python
results = agent.search_restaurants("Sushi restaurants in Tokyo")
