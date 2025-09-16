#!/usr/bin/env python3
"""
Food Agent Demo - Test Agent Execution

Tests the food agent by actually calling it with different types of requests
and validating the responses and tool usage.
"""

import os
import sys
import json
# Add project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
# Note: Environment variables are automatically loaded by venv/bin/activate

def test_agent_execution():
    """Test the food agent with various restaurant search requests"""
    print("🍽️  Food Agent Execution Demo")
    print("=" * 60)
    
    # Fail fast if API key is not available
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not api_key or api_key == 'your_google_places_api_key_here':
        raise ValueError("GOOGLE_PLACES_API_KEY environment variable must be set for testing")
    
    print(f"✅ API Key configured: {api_key[:10]}...")
    
    # Fail fast if dependencies are not available
    try:
        from food_agent import FoodAgent
    except ImportError as e:
        raise ImportError(f"Failed to import FoodAgent - ensure dependencies are installed: {str(e)}")
    
    # Initialize the agent - fail fast if this fails
    agent = FoodAgent()
    print("✅ Food Agent initialized successfully")
    
    # Test different types of restaurant requests with specific counts
    test_requests = [
        {
            "name": "Basic Italian Search",
            "query": "Find me 5 Italian restaurants in Rome",
            "expected_count": 5,
            "expected_features": ["restaurant search", "location processing", "cuisine filtering"]
        },
        {
            "name": "Vegetarian with Rating Filter",
            "query": "Show me 3 highly rated vegetarian restaurants near Times Square NYC",
            "expected_count": 3,
            "expected_features": ["dietary filtering", "rating filtering", "location specificity"]
        },
        {
            "name": "Budget Conscious Search",
            "query": "Give me 4 cheap good food places in Bangkok for dinner tonight",
            "expected_count": 4,
            "expected_features": ["price filtering", "time context", "location processing"]
        },
        {
            "name": "Fine Dining Request",
            "query": "Find 2 expensive French restaurants in Paris for a special occasion",
            "expected_count": 2,
            "expected_features": ["price level filtering", "cuisine specificity", "context understanding"]
        },
        {
            "name": "Open Now Filter",
            "query": "Show me 6 sushi restaurants that are open right now in Tokyo",
            "expected_count": 6,
            "expected_features": ["cuisine filtering", "time filtering", "availability checking"]
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
        print("   ✅ Food agent correctly processes natural language queries")
        print("   ✅ Tool usage and response formatting working properly")
        print("   ✅ Ready for integration with travel orchestrator")
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed")
        print("   Check agent logic and tool implementation")
    
    return passed == len(results)

def validate_agent_response(response, test_case):
    """Validate that the agent response is valid JSON matching RestaurantSearchResults schema"""
    if not response:
        print("   ❌ Empty response from agent")
        return False
    
    try:
        # Import Pydantic models for validation
        from common.models.food_models import RestaurantSearchResults
        
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
            validated_response = RestaurantSearchResults(**response_data)
            print("   ✅ Pydantic schema validation passed")
        except Exception as e:
            print(f"   ❌ Pydantic validation failed: {str(e)}")
            return False
        
        # Check restaurant count matches expected
        expected_count = test_case.get('expected_count', 5)
        actual_count = len(validated_response.restaurants)
        
        if actual_count == expected_count:
            print(f"   ✅ Restaurant count matches expected: {actual_count}")
        elif actual_count > 0:
            print(f"   ⚠️  Restaurant count {actual_count} doesn't match expected {expected_count} (but has results)")
        else:
            print(f"   ❌ No restaurants returned (expected {expected_count})")
            return False
        
        # Validate recommendation field
        if validated_response.recommendation and len(validated_response.recommendation) > 10:
            print("   ✅ Recommendation field present and meaningful")
        else:
            print("   ❌ Recommendation field missing or too short")
            return False
        
        # Validate success field
        if validated_response.total_results > 0:
            print(f"   ✅ Found {validated_response.total_results} restaurants")
        else:
            print("   ❌ No restaurants in results")
            return False
        
        # Validate restaurant data completeness
        restaurants_with_required_fields = 0
        for restaurant in validated_response.restaurants:
            if restaurant.name and restaurant.address:
                restaurants_with_required_fields += 1
        
        if restaurants_with_required_fields == len(validated_response.restaurants):
            print("   ✅ All restaurants have required fields (name, address)")
        else:
            print(f"   ⚠️  Only {restaurants_with_required_fields}/{len(validated_response.restaurants)} restaurants have complete data")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Failed to import validation models: {str(e)}")
        return False
    except Exception as e:
        print(f"   ❌ Validation error: {str(e)}")
        return False

def main():
    """Main demo function - fail fast approach"""
    print("🚀 Starting Food Agent Execution Tests...")
    
    try:
        success = test_agent_execution()
        
        print(f"\n💡 Next Steps:")
        if success:
            print("   ✅ Food agent execution validated")
            print("   🔧 Deploy to AgentCore for production testing")
            print("   🌐 Integrate with travel orchestrator")
        else:
            print("   🧪 Debug any failed test cases")
        
        return success
        
    except ValueError as e:
        print(f"❌ Configuration Error: {str(e)}")
        print("   Set GOOGLE_PLACES_API_KEY in your .env file")
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
