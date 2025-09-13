# Flight Agent - Nova Act Implementation

A simple flight search agent using Nova Act browser automation to search Google Flights.

## Setup

### Prerequisites
- Python 3.10 or higher
- Nova Act API key (get from https://nova.amazon.com/act)

### Installation

```bash
# Navigate to flight agent directory
cd agents/flight-agent

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

### Basic Flight Search

```python
from flight_search import FlightSearcher

# Create searcher instance
searcher = FlightSearcher()

# Search for flights
results = searcher.search_flights(
    origin="JFK",           # New York JFK
    destination="CDG",      # Paris Charles de Gaulle
    departure_date="2024-06-15",
    passengers=2
)

# Display results
for i, flight in enumerate(results.outbound_flights[:5], 1):
    print(f"{i}. {flight.airline}")
    print(f"   {flight.departure_airport} {flight.departure_time} → {flight.arrival_airport} {flight.arrival_time}")
    print(f"   Duration: {flight.duration} | Price: ${flight.price} | Stops: {flight.stops}")
```

### Round-trip Search

```python
# Search round-trip flights
results = searcher.search_flights(
    origin="JFK",
    destination="CDG",
    departure_date="2024-06-15",
    return_date="2024-06-22",  # Add return date
    passengers=2
)
```

### Command Line Usage

```bash
# Run the example search
python flight_search.py
```

## Testing

### Run Unit Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_flight_search.py::TestFlightSearcher::test_successful_flight_search -v
```

### Run Integration Tests (requires API key)
```bash
# Run integration tests with real API key
export NOVA_ACT_API_KEY="your_api_key"
pytest tests/test_flight_search.py::TestFlightSearchIntegration -v -m integration
```

## Project Structure

```
agents/flight-agent/
├── flight_search.py              # Main flight search implementation
├── models/
│   └── flight_models.py          # Pydantic data models
├── tests/
│   └── test_flight_search.py     # Test suite
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

## How It Works

1. **Nova Act Browser Automation**: Opens Google Flights in a headless Chrome browser
2. **Step-by-Step Navigation**: Breaks down the search into small, reliable steps
3. **Structured Data Extraction**: Uses Pydantic schemas to extract flight data with validation
4. **Error Handling**: Gracefully handles browser failures and parsing errors

## Key Features

- ✅ **Reliable Automation**: Uses Nova Act's proven browser automation patterns
- ✅ **Structured Data**: Pydantic models ensure data quality and type safety  
- ✅ **Comprehensive Testing**: Unit tests and integration tests included
- ✅ **Error Resilience**: Handles browser failures and unexpected page layouts
- ✅ **Schema Validation**: Ensures extracted flight data matches expected format

## Next Steps

This implementation is designed to be iteratively enhanced:

1. **Current**: Standalone Nova Act flight search
2. **Next**: Integrate with Strands Agents framework
3. **Future**: Deploy as AgentCore Runtime specialist agent
4. **Integration**: Connect with multi-agent orchestrator system

## Troubleshooting

### Common Issues

**API Key Error**
```
ValueError: NOVA_ACT_API_KEY environment variable is required
```
Solution: Set your Nova Act API key: `export NOVA_ACT_API_KEY="your_key"`

**SSL Certificate Error**
```
SSL Certificate verification failed for https://www.google.com/travel/flights
```
Solution: The code includes `ignore_https_errors=True` to handle SSL issues. If problems persist, ensure your SSL certificates are up to date:
```bash
# On macOS with Homebrew
brew update && brew upgrade openssl
```

**Asyncio Loop Conflict**
```
playwright._impl._errors.Error: It looks like you are using Playwright Sync API inside the asyncio loop.
```
Solution: The implementation automatically handles this by running Nova Act in a separate thread using `ThreadPoolExecutor`. This isolates Nova Act's synchronous Playwright API from any existing asyncio event loops.

**Chrome Installation Issues**
```
Error: Browser not found
```
Solution: Install Chrome: `playwright install chrome`

**Headless Mode Debugging**
For debugging browser automation, set `headless=False` in `flight_search.py` to see the browser in action:
```python
with NovaAct(
    starting_page="https://www.google.com/travel/flights",
    headless=False,  # Change to False for debugging
    # ... other parameters
) as nova:
```

### Getting Help

- Nova Act issues: https://github.com/aws/nova-act/issues
- Contact: nova-act@amazon.com
