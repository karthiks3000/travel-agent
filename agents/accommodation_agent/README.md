# Accommodation Agent

A multi-platform accommodation search agent using Nova Pro and browser automation to search Airbnb and Booking.com.

## Features

- **Multi-Platform Search**: Searches both Airbnb and Booking.com
- **Natural Language Processing**: Understands requests like "find me a place to stay in Paris for 3 nights starting tomorrow"
- **Intelligent Result Combination**: Combines and ranks results from multiple platforms
- **Flexible Browser Support**: Works with both local browsers and AgentCore
- **Structured Data**: Returns well-structured accommodation data

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set Nova Act API key
export NOVA_ACT_API_KEY=your_api_key_here
```

## Usage

### As a Strands Agent

```python
from agents.accommodation_agent.accommodation_agent import AccommodationAgent

# Initialize agent
agent = AccommodationAgent(use_agentcore_browser=False)

# Natural language request
response = agent.chat("Find me a place to stay in Barcelona for 3 nights starting June 15th for 2 people under $150/night")

# Direct tool call
results = agent.search_accommodations(
    location="Barcelona, Spain",
    check_in="2024-06-15",
    check_out="2024-06-18",
    guests=2,
    max_price=150.0
)
```

### Individual Platform Searches

```python
# Search only Airbnb
airbnb_results = agent.search_airbnb(
    location="Paris, France",
    check_in="2024-06-20",
    check_out="2024-06-23",
    guests=2
)

# Search only Booking.com
booking_results = agent.search_booking_com(
    location="Paris, France", 
    check_in="2024-06-20",
    check_out="2024-06-23",
    guests=2,
    rooms=1
)
```

## Available Tools

### `search_airbnb(location, check_in, check_out, guests)`
Searches Airbnb for accommodation options.

**Parameters:**
- `location`: Destination city or location
- `check_in`: Check-in date (YYYY-MM-DD)
- `check_out`: Check-out date (YYYY-MM-DD)
- `guests`: Number of guests (1-16)

### `search_booking_com(location, check_in, check_out, guests, rooms)`
Searches Booking.com for hotel and accommodation options.

**Parameters:**
- `location`: Destination city or location
- `check_in`: Check-in date (YYYY-MM-DD)
- `check_out`: Check-out date (YYYY-MM-DD)
- `guests`: Number of guests (1-30)
- `rooms`: Number of rooms (1-8)

### `search_accommodations(location, check_in, check_out, guests, max_price)`
Searches both platforms and combines results.

**Parameters:**
- `location`: Destination city or location
- `check_in`: Check-in date (YYYY-MM-DD)
- `check_out`: Check-out date (YYYY-MM-DD)
- `guests`: Number of guests
- `max_price`: Maximum price per night (optional)

## Response Format

```json
{
  "airbnb_properties": [...],
  "booking_properties": [...],
  "combined_results": [
    {
      "platform": "airbnb",
      "title": "Beautiful Apartment in City Center",
      "price_per_night": 120.0,
      "total_price": 360.0,
      "rating": 4.8,
      "review_count": 127,
      "property_type": "Entire apartment",
      "host_name": "Maria",
      "location": "City Center, Barcelona",
      "amenities": ["WiFi", "Kitchen", "Air conditioning"],
      "guests_capacity": 4,
      "bedrooms": 2,
      "bathrooms": 1
    }
  ],
  "search_metadata": {
    "timestamp": "2024-06-15T10:30:00",
    "airbnb_count": 15,
    "booking_count": 12,
    "total_found": 27
  }
}
```

## Browser Configuration

### Local Browser (Default)
```python
agent = AccommodationAgent(use_agentcore_browser=False)
```

### AgentCore Browser
```python
agent = AccommodationAgent(use_agentcore_browser=True, region="us-east-1")
```

## Demo

Run the demo script to see the agent in action:

```bash
python demo_strands.py
```

## Architecture

The accommodation agent uses:
- **Nova Pro**: For natural language understanding
- **Browser Wrapper**: Generic Nova Act session management
- **Platform-Specific Instructions**: Tailored search logic for each platform
- **Result Combination**: Intelligent merging and ranking of multi-platform results

## Supported Platforms

- ✅ **Airbnb**: Full support with property details, amenities, host info
- ✅ **Booking.com**: Full support with hotel details, ratings, amenities
- 🔄 **Future**: Easy to extend to additional platforms (VRBO, Hotels.com, etc.)

## Error Handling

The agent gracefully handles:
- Network timeouts
- Platform changes
- Invalid search parameters
- Browser automation failures
- Schema validation errors

## Testing

```bash
# Run tests
python -m pytest test_accommodation_agent.py -v

# Run demo
python demo_strands.py
