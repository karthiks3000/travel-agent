#!/usr/bin/env python3
"""
Flight Agent Demo - Test Agent Execution

Tests the flight agent by actually calling it with different types of requests
and validating the structured JSON responses and recommendations.
"""

import os
import sys
import json
from datetime import datetime, timedelta
# Add project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from agents.flight_agent.flight_agent import FlightAgent

# Note: Environment variables are automatically loaded by venv/bin/activate

def test_agent_execution():
    """Test the flight agent with various flight search requests"""
    print("✈️  Flight Agent Execution Demo")
    print("=" * 60)
    
    # Fail fast if API key is not available
    api_key = os.getenv('NOVA_ACT_API_KEY')
    if not api_key or api_key == 'your_nova_act_api_key_here':
        raise ValueError("NOVA_ACT_API_KEY environment variable must be set for testing")
    
    print(f"✅ Nova Act API Key configured: {api_key[:10]}...")
    
    # Initialize the agent - fail fast if this fails
    agent = FlightAgent()
    print("✅ Flight Agent initialized successfully")
    
    # Calculate future dates for testing
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    next_month = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d")
    
    # Test different types of flight requests - agent now returns best single flights
    test_requests = [
        {
            "name": "One-Way Best Flight Selection",
            "query": f"Find me the best flight from JFK to LAX departing {tomorrow}",
            "trip_type": "one-way",
            "expected_features": ["one-way search", "airport codes", "future date validation", "best flight selection"]
        },
        {
            "name": "Round-Trip Best Flight Selection", 
            "query": f"Show me the best round-trip flights from NYC to Paris departing {next_week} returning {return_date}",
            "trip_type": "round-trip",
            "expected_features": ["round-trip", "international", "specific dates", "best flight selection"]
        },
        {
            "name": "Multi-Passenger Best Flight",
            "query": f"Give me the best flight from Miami to Tokyo for 3 passengers departing {next_month}",
            "trip_type": "one-way",
            "expected_features": ["multiple passengers", "international", "best flight selection"]
        },
        {
            "name": "Past Date Validation Test",
            "query": "Find me the best flight from Boston to Seattle departing 2024-01-01",
            "trip_type": "error",
            "expected_features": ["date validation", "error handling", "past date rejection"]
        },
        {
            "name": "Relative Date Best Flight",
            "query": "Show me the best flight from Chicago to San Francisco tomorrow",
            "trip_type": "one-way", 
            "expected_features": ["relative dates", "domestic", "best flight selection"]
        }
    ]
    
    results = []
    for i, test_case in enumerate(test_requests, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print("-" * 50)
        print(f"Query: {test_case['query']}")
        
        try:
            # Call the agent with the query
            agent_result = agent(test_case['query'])
            
            # Extract the actual response content from AgentResult
            if hasattr(agent_result, 'content'):
                response = agent_result.content
            elif hasattr(agent_result, 'text'):
                response = agent_result.text
            else:
                response = str(agent_result)
            
            # Validate the response
            success = validate_agent_response(response, test_case)
            results.append((test_case['name'], success, response))
            
            if success:
                print("✅ Agent response validated successfully")
            else:
                print("❌ Agent response validation failed")
                
        except Exception as e:
            print(f"❌ Agent execution failed: {str(e)}")
            results.append((test_case['name'], False, str(e)))
    
    # Summary
    print(f"\n" + "=" * 60)
    print("📊 Agent Execution Results")
    print("-" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    for test_name, success, response in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All agent execution tests passed!")
        print("   ✅ Flight agent correctly processes natural language queries")
        print("   ✅ Date validation and JSON response formatting working properly")
        print("   ✅ Ready for integration with travel orchestrator")
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed")
        print("   Check agent logic and response formatting")
    
    return passed == len(results)

def validate_agent_response(response, test_case):
    """Validate that the agent response is valid JSON matching FlightSearchResults schema"""
    if not response:
        print("   ❌ Empty response from agent")
        return False
    
    try:
        # Import Pydantic models for validation
        from common.models.flight_models import FlightSearchResults
        
        # Parse response if it's a string
        if isinstance(response, str):
            try:
                response_data = json.loads(response)
                print("   ✅ Valid JSON format")
            except json.JSONDecodeError as e:
                print(f"   ❌ Invalid JSON format: {str(e)}")
                return False
        elif isinstance(response, dict):
            response_data = response
            print("   ✅ Dict response format")
        else:
            print(f"   ❌ Unexpected response type: {type(response)}")
            return False
        
        # Validate using Pydantic model
        try:
            validated_response = FlightSearchResults(**response_data)
            print("   ✅ Pydantic schema validation passed")
        except Exception as e:
            print(f"   ❌ Pydantic validation failed: {str(e)}")
            return False
        
        # Check if this is an error response for past dates
        if test_case['trip_type'] == "error":
            if not validated_response.best_outbound_flight and not validated_response.best_return_flight:
                print("   ✅ Past date properly rejected - no flights returned")
                if validated_response.recommendation and "future" in validated_response.recommendation.lower():
                    print("   ✅ Error recommendation suggests future dates")
                return True
            else:
                print("   ❌ Past date should have been rejected")
                return False
        
        # Validate best flight selection (for successful searches)
        trip_type = test_case.get('trip_type', 'one-way')
        
        # Check outbound flight
        if validated_response.best_outbound_flight:
            flight = validated_response.best_outbound_flight
            print(f"   ✅ Best outbound flight selected: {flight.airline} ${flight.price}")
            
            # Validate flight has required fields
            if flight.airline and flight.departure_time and flight.arrival_time and flight.price:
                print("   ✅ Outbound flight has all required fields")
            else:
                print("   ❌ Outbound flight missing required fields")
                return False
            
            # Check if it's a direct flight (preferred)
            if flight.stops == 0:
                print("   ✅ Selected direct flight (preferred)")
            else:
                print(f"   ⚠️  Selected flight has {flight.stops} stops (may be cheapest available)")
                
        else:
            print("   ❌ No best outbound flight selected")
            return False
        
        # For round-trip flights, validate return flight
        if trip_type == "round-trip":
            if validated_response.best_return_flight:
                return_flight = validated_response.best_return_flight
                print(f"   ✅ Best return flight selected: {return_flight.airline} ${return_flight.price}")
                
                # Validate return flight has required fields
                if return_flight.airline and return_flight.departure_time and return_flight.arrival_time and return_flight.price:
                    print("   ✅ Return flight has all required fields")
                else:
                    print("   ❌ Return flight missing required fields")
                    return False
            else:
                print("   ❌ Round-trip requested but no return flight selected")
                return False
        
        # Validate recommendation field
        if validated_response.recommendation and len(validated_response.recommendation) > 10:
            print("   ✅ Recommendation field present and meaningful")
        else:
            print("   ❌ Recommendation field missing or too short")
            return False
        
        # Validate search metadata
        if validated_response.search_metadata:
            print("   ✅ Search metadata present")
        else:
            print("   ❌ Search metadata missing")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Failed to import validation models: {str(e)}")
        return False
    except Exception as e:
        print(f"   ❌ Validation error: {str(e)}")
        return False

def main():
    """Main demo function - fail fast approach"""
    print("🚀 Starting Flight Agent Execution Tests...")
    
    try:
        success = test_agent_execution()
        
        print(f"\n💡 Next Steps:")
        if success:
            print("   ✅ Flight agent execution validated")
            print("   🔧 Deploy to AgentCore for production testing")
            print("   🌐 Integrate with travel orchestrator")
        else:
            print("   🧪 Debug any failed test cases")
        
        return success
        
    except ValueError as e:
        print(f"❌ Configuration Error: {str(e)}")
        print("   Set NOVA_ACT_API_KEY in your .env file")
        return False
    except ImportError as e:
        print(f"❌ Dependency Error: {str(e)}")
        print("   Install required dependencies (strands, bedrock-agentcore)")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
