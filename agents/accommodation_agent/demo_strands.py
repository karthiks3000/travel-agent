"""
Demo script for the new Strands-based Accommodation Agent
Shows how to use the agent with natural language requests
"""
import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.accommodation_agent.accommodation_agent import accommodation_agent


def test_natural_language_requests():
    """Test the accommodation agent with various natural language requests"""
    
    print("="*60)
    print("ACCOMMODATION AGENT - NATURAL LANGUAGE DEMO")
    print("="*60)
    
    # Test cases with natural language requests
    test_cases = [
        {
            "request": "Find me a place to stay in Paris for 3 nights starting tomorrow for 2 people",
            "description": "Short stay with relative date"
        },
        {
            "request": "I need accommodation in Barcelona for June 15th to June 18th, 2 guests, under $150 per night",
            "description": "Specific dates with budget constraint"
        },
        {
            "request": "Show me Airbnb and hotel options in Tokyo for next week, 4 guests",
            "description": "Multi-platform search with relative date"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'-'*40}")
        print(f"TEST {i}: {test_case['description']}")
        print(f"Request: \"{test_case['request']}\"")
        print(f"{'-'*40}")
        
        try:
            # Use the agent's natural language processing
            response = accommodation_agent(test_case["request"])
            print(f"Agent Response: {response}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")


def test_direct_tool_calls():
    """Test the accommodation agent with direct tool calls"""
    
    print("\n" + "="*60)
    print("ACCOMMODATION AGENT - DIRECT TOOL CALL DEMO")
    print("="*60)
    
    # Calculate dates for testing (2 weeks from now)
    check_in = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")
    
    print(f"\nDirect tool call: search_accommodations")
    print(f"Location: Amsterdam, Netherlands")
    print(f"Dates: {check_in} to {check_out}")
    print(f"Guests: 2, Max price: $180/night")
    
    try:
        results = accommodation_agent.tool.search_accommodations(
            location="Amsterdam, Netherlands",
            check_in=check_in,
            check_out=check_out,
            guests=2,
            max_price=180.0
        )
        
        print("\nResults received:")
        if isinstance(results, dict):
            if "error" in results:
                print(f"❌ Error: {results['error']}")
            else:
                airbnb_count = len(results.get("airbnb_properties", []))
                booking_count = len(results.get("booking_properties", []))
                combined_count = len(results.get("combined_results", []))
                
                print(f"✅ Search completed successfully")
                print(f"   Airbnb properties: {airbnb_count}")
                print(f"   Booking.com properties: {booking_count}")
                print(f"   Combined top results: {combined_count}")
                
                # Show first few properties
                combined_results = results.get("combined_results", [])
                for i, prop in enumerate(combined_results[:3], 1):
                    if isinstance(prop, dict):
                        print(f"\n{i}. {prop.get('title', 'Unknown Property')} ({prop.get('platform', '').upper()})")
                        print(f"   Price: ${prop.get('price_per_night', 'N/A')}/night")
                        print(f"   Rating: {prop.get('rating', 'N/A')} ({prop.get('review_count', 'N/A')} reviews)")
                        print(f"   Type: {prop.get('property_type', 'N/A')}")
        else:
            print("Unexpected result type:", type(results))
            
    except Exception as e:
        print(f"❌ Tool call error: {str(e)}")


def test_individual_platforms():
    """Test individual platform searches"""
    
    print("\n" + "="*60)
    print("ACCOMMODATION AGENT - INDIVIDUAL PLATFORM TESTS")
    print("="*60)
    
    # Calculate dates for testing
    check_in = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    
    print(f"\n📍 Testing Airbnb search: Rome | {check_in} to {check_out}")
    
    try:
        airbnb_results = accommodation_agent.tool.search_airbnb(
            location="Rome, Italy",
            check_in=check_in,
            check_out=check_out,
            guests=2
        )
        
        if isinstance(airbnb_results, dict):
            if "error" in airbnb_results:
                print(f"❌ Airbnb search error: {airbnb_results['error']}")
            elif "properties" in airbnb_results:
                properties = airbnb_results["properties"]
                print(f"✅ Airbnb search successful - found {len(properties)} properties")
            else:
                print("⚠️  Airbnb search completed but with unexpected format")
        
    except Exception as e:
        print(f"❌ Airbnb search failed: {str(e)}")
    
    print(f"\n📍 Testing Booking.com search: Rome | {check_in} to {check_out}")
    
    try:
        booking_results = accommodation_agent.tool.search_booking_com(
            location="Rome, Italy",
            check_in=check_in,
            check_out=check_out,
            guests=2,
            rooms=1
        )
        
        if isinstance(booking_results, dict):
            if "error" in booking_results:
                print(f"❌ Booking.com search error: {booking_results['error']}")
            elif "properties" in booking_results:
                properties = booking_results["properties"]
                print(f"✅ Booking.com search successful - found {len(properties)} properties")
            else:
                print("⚠️  Booking.com search completed but with unexpected format")
        
    except Exception as e:
        print(f"❌ Booking.com search failed: {str(e)}")


def test_agentcore_browser():
    """Test with AgentCore browser (if available)"""
    
    print("\n" + "="*60)
    print("ACCOMMODATION AGENT - AGENTCORE BROWSER TEST")
    print("="*60)
    
    print("⚠️  Note: AgentCore test requires setting environment variables:")
    print("   export USE_AGENTCORE_BROWSER=true")
    print("   export AGENTCORE_REGION=us-east-1")
    print("   and restarting the application")


def main():
    """Run all demo tests"""
    
    # Check for required environment variable
    if not os.getenv('NOVA_ACT_API_KEY'):
        print("❌ Error: NOVA_ACT_API_KEY environment variable is required")
        print("Please set your Nova Act API key before running the demo")
        return
    
    print("Starting Accommodation Agent Demo...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the tests
    test_direct_tool_calls()
    test_individual_platforms()
    test_natural_language_requests()
    test_agentcore_browser()
    
    print("\n" + "="*60)
    print("DEMO COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()
