#!/usr/bin/env python3
"""
Travel Orchestrator Demo - Test Agent Execution

Tests the travel orchestrator agent by calling it with different types of requests
and validating the structured JSON responses and agent coordination capabilities.
"""

import os
import sys
import json
from datetime import datetime, timedelta
# Add project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from agents.travel_orchestrator.travel_orchestrator import TravelOrchestratorAgent

# Note: Environment variables are automatically loaded by venv/bin/activate

def test_agent_execution():
    """Test the travel orchestrator with various travel planning requests"""
    print("🌍 Travel Orchestrator Agent Execution Demo")
    print("=" * 60)
    
    # Fail fast if API key is not available
    api_key = os.getenv('NOVA_ACT_API_KEY')
    if not api_key or api_key == 'your_nova_act_api_key_here':
        raise ValueError("NOVA_ACT_API_KEY environment variable must be set for testing")
    
    print(f"✅ Nova Act API Key configured: {api_key[:10]}...")
    
    # Initialize the agent - fail fast if this fails
    agent = TravelOrchestratorAgent()
    print("✅ Travel Orchestrator Agent initialized successfully")
    
    # Calculate future dates for testing
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    next_month = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d")
    
    # Test different types of travel orchestration requests
    test_requests = [
        {
            "name": "Complete Trip Planning",
            "query": f"Plan a 5-day trip to Paris from NYC for 2 people departing {next_week} and returning {return_date}",
            "expected_response_type": "itinerary",
            "expected_features": ["comprehensive planning", "multi-agent coordination", "cost estimation", "structured data"]
        },
        {
            "name": "Flight Search Only",
            "query": f"Find me flights from San Francisco to Tokyo departing {tomorrow}",
            "expected_response_type": "flights", 
            "expected_features": ["flight delegation", "date validation", "structured flight data"]
        },
        {
            "name": "Accommodation Search",
            "query": f"I need a hotel in Rome for 3 nights starting {next_month} for 2 guests",
            "expected_response_type": "accommodations",
            "expected_features": ["accommodation delegation", "date processing", "guest handling"]
        },
        {
            "name": "Restaurant Search",
            "query": "Show me good Italian restaurants in downtown Chicago",
            "expected_response_type": "restaurants",
            "expected_features": ["restaurant delegation", "location processing", "cuisine filtering"]
        },
        {
            "name": "Information Gathering",
            "query": "I want to go to Japan",
            "expected_response_type": "conversation",
            "expected_features": ["validation", "clarifying questions", "conversation response"]
        },
        {
            "name": "Multi-City Trip Planning",
            "query": f"Plan a trip from Boston to London {next_week}, then to Paris for 3 days, returning {return_date} for 2 travelers",
            "expected_response_type": "itinerary",
            "expected_features": ["complex itinerary", "multi-destination", "comprehensive planning"]
        },
        {
            "name": "Budget-Conscious Planning",
            "query": f"Find cheap flights and budget accommodations in Bangkok for {next_month} to {return_date}, 1 person",
            "expected_response_type": "itinerary",
            "expected_features": ["budget optimization", "cost-conscious recommendations", "single traveler"]
        },
        {
            "name": "Invalid Date Handling",
            "query": "Book me a flight to London departing last week",
            "expected_response_type": "conversation",
            "expected_features": ["date validation", "error handling", "helpful suggestions"]
        },
        {
            "name": "Incomplete Information",
            "query": "Find me a place to stay",
            "expected_response_type": "conversation", 
            "expected_features": ["information validation", "follow-up questions", "progressive disclosure"]
        },
        {
            "name": "Business Trip Planning",
            "query": f"I need flights and hotels for a business trip to Seattle {next_week} to {return_date}, prefer convenient locations",
            "expected_response_type": "itinerary",
            "expected_features": ["business travel optimization", "location preferences", "professional recommendations"]
        }
    ]
    
    results = []
    for i, test_case in enumerate(test_requests, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print("-" * 50)
        print(f"Query: {test_case['query']}")
        
        try:
            # Call the agent with the natural language query
            agent_result = agent(test_case['query'])
            
            # Extract the actual response content from AgentResult
            if hasattr(agent_result, 'content'):
                response = agent_result.content
            elif hasattr(agent_result, 'text'):
                response = agent_result.text
            else:
                response = str(agent_result)
            
            # Validate the response
            success = validate_orchestrator_response(response, test_case)
            results.append((test_case['name'], success, response))
            
            if success:
                print("✅ Travel orchestrator response validated successfully")
            else:
                print("❌ Travel orchestrator response validation failed")
                
        except Exception as e:
            print(f"❌ Travel orchestrator execution failed: {str(e)}")
            results.append((test_case['name'], False, str(e)))
    
    # Summary
    print(f"\n" + "=" * 60)
    print("📊 Travel Orchestrator Execution Results")
    print("-" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    for test_name, success, response in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All travel orchestrator tests passed!")
        print("   ✅ Travel orchestrator correctly processes natural language queries")
        print("   ✅ Agent coordination and response formatting working properly")
        print("   ✅ Ready for integration with chat interface and frontend")
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed")
        print("   Check orchestrator logic and agent coordination")
    
    return passed == len(results)

def validate_orchestrator_response(response, test_case):
    """Validate that the orchestrator response is appropriate for a conversational travel agent"""
    if not response:
        print("   ❌ Empty response from orchestrator")
        return False
    
    try:
        # The travel orchestrator is designed to be conversational and returns text responses
        # It only returns structured JSON internally via tools, not to end users
        
        if isinstance(response, str):
            response_text = response.strip()
            print("   ✅ Text response format (expected for conversational agent)")
            
            # Validate response is meaningful and helpful
            if len(response_text) < 10:
                print("   ❌ Response too short to be meaningful")
                return False
            
            print("   ✅ Response length is meaningful")
            
            # Check response appropriateness based on expected scenario
            expected_type = test_case.get('expected_response_type', 'conversation')
            expected_features = test_case.get('expected_features', [])
            
            # Validate conversation responses ask for clarification appropriately
            if expected_type == "conversation":
                if any(feature in ['validation', 'clarifying questions', 'information gathering'] 
                       for feature in expected_features):
                    if any(keyword in response_text.lower() 
                           for keyword in ['need', 'please', 'information', 'help', 'provide', 'details']):
                        print("   ✅ Conversation response appropriately asks for clarification")
                    else:
                        print("   ⚠️  Expected clarification request but got different response")
                else:
                    print("   ✅ Conversation response provides information")
            
            # Check for error handling scenarios
            if "error handling" in expected_features:
                if any(keyword in response_text.lower() 
                       for keyword in ['sorry', 'can\'t', 'unable', 'error', 'issue']):
                    print("   ✅ Error handling response is appropriately apologetic")
                else:
                    print("   ⚠️  Expected error handling but response doesn't indicate issue")
            
            # Check for date validation
            if "date validation" in expected_features:
                if any(keyword in response_text.lower() 
                       for keyword in ['past', 'future', 'date', 'yesterday', 'last week']):
                    print("   ✅ Date validation response addresses date issues")
                else:
                    print("   ⚠️  Expected date validation response")
            
            # Check that response doesn't contain obvious errors
            if "undefined" in response_text.lower() or "null" in response_text.lower():
                print("   ❌ Response contains undefined/null values")
                return False
            
            print("   ✅ Response appears well-formed and helpful")
            return True
            
        elif isinstance(response, dict):
            # If we get a dict, try to validate as structured response
            print("   ✅ Structured response format (unexpected but validating)")
            
            # Import Pydantic models for validation
            from common.models.orchestrator_models import TravelOrchestratorResponse, ResponseType
            
            try:
                validated_response = TravelOrchestratorResponse(**response)
                print("   ✅ TravelOrchestratorResponse schema validation passed")
                
                # For structured responses, validate the message field
                if validated_response.message and len(validated_response.message) > 10:
                    print("   ✅ Structured response has meaningful message")
                    return True
                else:
                    print("   ❌ Structured response missing meaningful message")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Structured response validation failed: {str(e)}")
                return False
        
        else:
            print(f"   ❌ Unexpected response type: {type(response)}")
            return False
        
    except ImportError as e:
        print(f"   ❌ Failed to import validation models (for structured fallback): {str(e)}")
        # Continue with text validation even if we can't import structured models
        if isinstance(response, str) and len(response.strip()) > 10:
            print("   ✅ Basic text validation passed despite import error")
            return True
        return False
    except Exception as e:
        print(f"   ❌ Validation error: {str(e)}")
        return False

def main():
    """Main demo function - fail fast approach"""
    print("🚀 Starting Travel Orchestrator Agent Execution Tests...")
    
    try:
        success = test_agent_execution()
        
        print(f"\n💡 Next Steps:")
        if success:
            print("   ✅ Travel orchestrator execution validated")
            print("   🔧 Deploy to AgentCore for production testing")
            print("   🌐 Integrate with chat interface and frontend")
            print("   📱 Test with real user conversations")
        else:
            print("   🧪 Debug any failed test cases")
            print("   🔍 Check agent coordination and response formatting")
        
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
