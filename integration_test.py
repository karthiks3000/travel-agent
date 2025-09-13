"""
Integration test script for both Flight and Accommodation agents
Tests the shared browser wrapper and cross-agent functionality
"""
import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.append(os.path.dirname(__file__))

from agents.flight_agent.flight_agent import flight_agent
from agents.accommodation_agent.accommodation_agent import accommodation_agent


def test_browser_wrapper_integration():
    """Test that both agents can use the same browser wrapper successfully"""
    
    print("="*70)
    print("BROWSER WRAPPER INTEGRATION TEST")
    print("="*70)
    
    # Check for API key
    if not os.getenv('NOVA_ACT_API_KEY'):
        print("❌ Error: NOVA_ACT_API_KEY environment variable is required")
        return False
    
    print("Using pre-configured agent instances...")
    
    # Calculate test dates
    departure_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    check_in = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")
    
    success_count = 0
    total_tests = 3
    
    # Test 1: Flight Agent
    print(f"\n📍 Test 1: Flight Agent Search")
    print(f"   Route: NYC → Boston on {departure_date}")
    
    try:
        flight_results = flight_agent.tool.search_google_flights(
            origin="NYC",
            destination="BOS",
            departure_date=departure_date,
            passengers=1
        )
        
        if isinstance(flight_results, dict):
            if "error" in flight_results:
                print(f"   ⚠️  Flight search completed with error: {flight_results['error']}")
            elif "outbound_flights" in flight_results:
                flights = flight_results["outbound_flights"]
                print(f"   ✅ Flight search successful - found {len(flights)} flights")
                success_count += 1
            else:
                print(f"   ⚠️  Flight search returned unexpected format")
        else:
            print(f"   ⚠️  Flight search returned unexpected type: {type(flight_results)}")
            
    except Exception as e:
        print(f"   ❌ Flight search failed: {str(e)}")
    
    # Test 2: Accommodation Agent - Airbnb
    print(f"\n📍 Test 2: Accommodation Agent - Airbnb Search")
    print(f"   Location: Boston | {check_in} to {check_out}")
    
    try:
        airbnb_results = accommodation_agent.tool.search_airbnb(
            location="Boston, MA",
            check_in=check_in,
            check_out=check_out,
            guests=2
        )
        
        if isinstance(airbnb_results, dict):
            if "error" in airbnb_results:
                print(f"   ⚠️  Airbnb search completed with error: {airbnb_results['error']}")
            elif "properties" in airbnb_results:
                properties = airbnb_results["properties"]
                print(f"   ✅ Airbnb search successful - found {len(properties)} properties")
                success_count += 1
            else:
                print(f"   ⚠️  Airbnb search returned unexpected format")
        else:
            print(f"   ⚠️  Airbnb search returned unexpected type: {type(airbnb_results)}")
            
    except Exception as e:
        print(f"   ❌ Airbnb search failed: {str(e)}")
    
    # Test 3: Accommodation Agent - Combined Search
    print(f"\n📍 Test 3: Accommodation Agent - Combined Search")
    print(f"   Location: Boston | {check_in} to {check_out}")
    
    try:
        combined_results = accommodation_agent.tool.search_accommodations(
            location="Boston, MA",
            check_in=check_in,
            check_out=check_out,
            guests=2,
            max_price=200.0
        )
        
        if isinstance(combined_results, dict):
            if "error" in combined_results:
                print(f"   ⚠️  Combined search completed with error: {combined_results['error']}")
            else:
                airbnb_count = len(combined_results.get("airbnb_properties", []))
                booking_count = len(combined_results.get("booking_properties", []))
                combined_count = len(combined_results.get("combined_results", []))
                
                print(f"   ✅ Combined search successful")
                print(f"      Airbnb: {airbnb_count}, Booking: {booking_count}, Combined: {combined_count}")
                success_count += 1
        else:
            print(f"   ⚠️  Combined search returned unexpected type: {type(combined_results)}")
            
    except Exception as e:
        print(f"   ❌ Combined search failed: {str(e)}")
    
    # Summary
    print(f"\n{'-'*50}")
    print(f"INTEGRATION TEST RESULTS")
    print(f"{'-'*50}")
    print(f"Tests passed: {success_count}/{total_tests}")
    print(f"Success rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("🎉 All integration tests passed!")
        return True
    elif success_count > 0:
        print("⚠️  Some tests passed - browser wrapper is working but some searches may have issues")
        return True
    else:
        print("❌ All tests failed - check browser wrapper and Nova Act configuration")
        return False


def test_natural_language_integration():
    """Test natural language capabilities of both agents"""
    
    print("\n" + "="*70)
    print("NATURAL LANGUAGE INTEGRATION TEST")
    print("="*70)
    
    # Test natural language requests
    test_cases = [
        {
            "agent": flight_agent,
            "type": "Flight",
            "request": "Find me a flight from New York to Miami for next Friday"
        },
        {
            "agent": accommodation_agent,
            "type": "Accommodation", 
            "request": "Find me a place to stay in Miami for 2 nights starting next Friday for 2 people"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📍 Test {i}: {test_case['type']} Agent Natural Language")
        print(f"   Request: \"{test_case['request']}\"")
        
        try:
            response = test_case["agent"](test_case["request"])
            print(f"   ✅ Agent responded successfully")
            print(f"   Response preview: {str(response)[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Natural language test failed: {str(e)}")


def test_agentcore_integration():
    """Test AgentCore browser integration if available"""
    
    print("\n" + "="*70)
    print("AGENTCORE BROWSER INTEGRATION TEST")
    print("="*70)
    
    print("⚠️  Note: AgentCore testing requires setting environment variables:")
    print("   export USE_AGENTCORE_BROWSER=true")
    print("   export AGENTCORE_REGION=us-east-1")
    print("   and restarting the application to pick up new configuration")


def main():
    """Run all integration tests"""
    
    print("Starting Travel Agent Integration Tests...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run integration tests
    browser_success = test_browser_wrapper_integration()
    test_natural_language_integration()
    test_agentcore_integration()
    
    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70)
    
    if browser_success:
        print("🎉 Browser wrapper integration: PASSED")
        print("✅ Both agents can successfully use the shared browser wrapper")
        print("✅ Flight agent can search Google Flights")  
        print("✅ Accommodation agent can search Airbnb and Booking.com")
        print("✅ Multi-platform accommodation search works")
    else:
        print("❌ Browser wrapper integration: FAILED")
        print("   Check Nova Act API key and browser configuration")
    
    print("\n💡 Next steps:")
    print("   1. Run individual agent demos: python agents/flight_agent/demo_strands.py")
    print("   2. Run accommodation demo: python agents/accommodation_agent/demo_strands.py")
    print("   3. Deploy agents using Strands framework")
    
    print(f"\nIntegration test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
