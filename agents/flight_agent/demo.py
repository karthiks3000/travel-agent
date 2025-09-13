"""
Demo script for the new Strands-based Flight Agent
Shows how to use the agent with natural language requests
"""
import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from flight_agent import agent

def test_natural_language_requests():
    """Test the flight agent with various natural language requests"""
    
    print("="*60)
    print("FLIGHT AGENT - NATURAL LANGUAGE DEMO")
    print("="*60)
    
    # Test cases with natural language requests
    test_cases = [
        {
            "request": "Find me the cheapest flight from New York to Los Angeles for next Friday",
            "description": "Simple one-way search with relative date"
        },
        {
            "request": "I need round-trip flights from JFK to CDG departing June 15th and returning June 22nd for 2 passengers",
            "description": "Round-trip search with specific dates and multiple passengers"
        },
        {
            "request": "Show me flights from Miami to Tokyo tomorrow",
            "description": "International flight with relative date"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'-'*40}")
        print(f"TEST {i}: {test_case['description']}")
        print(f"Request: \"{test_case['request']}\"")
        print(f"{'-'*40}")
        
        try:
            # Use the agent's natural language processing
            response = agent(test_case["request"])
            print(f"Agent Response: {response}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")


def main():
    """Run all demo tests"""
    
    # Check for required environment variable
    if not os.getenv('NOVA_ACT_API_KEY'):
        print("❌ Error: NOVA_ACT_API_KEY environment variable is required")
        print("Please set your Nova Act API key before running the demo")
        return
    
    print("Starting Flight Agent Demo...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    test_natural_language_requests()
    
    print("\n" + "="*60)
    print("DEMO COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()
