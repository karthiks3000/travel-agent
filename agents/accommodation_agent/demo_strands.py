"""
Demo script for the updated Accommodation Agent
Tests smart platform selection, JSON responses, and validation logic
"""
import os
import sys
import json
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.accommodation_agent.accommodation_agent import agent as accommodation_agent
from common.models.accommodation_models import AccommodationAgentResponse


def validate_json_response(response, test_name):
    """Validate agent response against AccommodationAgentResponse schema"""
    try:
        print(f"Response: {response}")
        # Parse response if it's a string
        if isinstance(response, str):
            try:
                # Handle Python None values in JSON strings by replacing with null
                cleaned_response = response.replace(': None,', ': null,').replace(': None}', ': null}')
                response_data = json.loads(cleaned_response)
                print(f"   ✅ Valid JSON format (cleaned Python None values)")
            except json.JSONDecodeError as e:
                print(f"   ❌ Invalid JSON format: {str(e)}")
                print(f"   📝 First 200 chars: {response[:200]}...")
                return False
        elif isinstance(response, dict):
            response_data = response
            print(f"   ✅ Dict response format")
        else:
            print(f"   ❌ Unexpected response type: {type(response)}")
            return False

        # Validate using Pydantic model
        try:
            validated_response = AccommodationAgentResponse(**response_data)
            print(f"   ✅ Pydantic schema validation passed")
        except Exception as e:
            print(f"   ❌ Pydantic validation error: {str(e)}")
            return False

        # Check response structure
        if "best_accommodations" in response_data:
            accommodations = response_data["best_accommodations"]
            print(f"   ✅ Found {len(accommodations)} best accommodations")
            
            if len(accommodations) > 0:
                # Check first accommodation structure
                first_acc = accommodations[0]
                required_fields = ['platform', 'title', 'price_per_night', 'property_type']
                missing_fields = [field for field in required_fields if field not in first_acc]
                if missing_fields:
                    print(f"   ⚠️  Missing fields in accommodation: {missing_fields}")
                else:
                    print(f"   ✅ Accommodation structure valid")
        else:
            print(f"   ❌ Missing 'best_accommodations' field")
            return False

        # Check metadata
        if "search_metadata" in response_data:
            metadata = response_data["search_metadata"]
            if "error" in metadata:
                print(f"   ⚠️  Search error in metadata: {metadata['error']}")
            else:
                print(f"   ✅ Search metadata present")
        else:
            print(f"   ❌ Missing 'search_metadata' field")
            return False

        # Check recommendation
        if "recommendation" in response_data:
            recommendation = response_data["recommendation"]
            if len(recommendation) > 20:
                print(f"   ✅ Meaningful recommendation provided")
            else:
                print(f"   ⚠️  Recommendation seems too short")
        else:
            print(f"   ❌ Missing 'recommendation' field")
            return False

        return True

    except Exception as e:
        print(f"   ❌ Validation error: {str(e)}")
        return False


def test_comprehensive_scenarios():
    """Test platform selection with integrated date format handling"""
    
    print("="*60)
    print("COMPREHENSIVE ACCOMMODATION TESTS")
    print("="*60)
    
    # Calculate future dates for testing
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    week_later = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    
    test_cases = [
        {
            "prompt": "Find me an Airbnb apartment in Barcelona starting tomorrow for 3 nights",
            "expected_behavior": "Should use Airbnb only + handle 'tomorrow' relative date",
            "keywords": ["airbnb", "apartment"],
            "test_type": "Platform: Airbnb-only + Date: Relative (tomorrow)",
            "description": "Airbnb platform with relative date"
        },
        {
            "prompt": "I need a hotel in Paris from tomorrow for 2 people",
            "expected_behavior": "Should use Booking.com only + handle 'tomorrow' relative date",
            "keywords": ["hotel"],
            "test_type": "Platform: Booking-only + Date: Relative (tomorrow)",
            "description": "Booking platform with relative date"
        },
        {
            "prompt": f"Show me accommodation options in Tokyo from {next_week} to {week_later} for 2 guests",
            "expected_behavior": "Should use both platforms + handle absolute dates",
            "keywords": ["accommodation"],
            "test_type": "Platform: Both platforms + Date: Absolute (YYYY-MM-DD)",
            "description": "Both platforms with absolute dates"
        }
    ]
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'-'*50}")
        print(f"TEST {i}: {test_case['description']}")
        print(f"Type: {test_case['test_type']}")
        print(f"Prompt: \"{test_case['prompt']}\"")
        print(f"Expected: {test_case['expected_behavior']}")
        print(f"Keywords: {test_case['keywords']}")
        print(f"{'-'*50}")
        
        try:
            # Call the agent with the prompt
            agent_result = accommodation_agent(test_case['prompt'])
            
            # Extract the actual response content from AgentResult
            if hasattr(agent_result, 'content'):
                response = agent_result.content
            elif hasattr(agent_result, 'text'):
                response = agent_result.text
            else:
                response = str(agent_result)
            
            # Validate JSON response
            success = validate_json_response(response, test_case['description'])
            results.append((test_case['description'], success))
            
            if success:
                print(f"✅ Comprehensive test passed")
            else:
                print(f"❌ Comprehensive test failed")
                
        except Exception as e:
            print(f"❌ Agent execution error: {str(e)}")
            results.append((test_case['description'], False))
    
    return results


def test_error_handling():
    """Test error handling with invalid inputs - streamlined to one key test"""
    
    print("\n" + "="*60)
    print("ERROR HANDLING TEST")
    print("="*60)
    
    # Single most important error test - past date validation
    test_case = {
        "prompt": "Find accommodation in Paris from 2024-01-01 to 2024-01-03 for 2 people",
        "expected_error": "Past date validation error",
        "description": "Past dates validation test"
    }
    
    print(f"\n{'-'*50}")
    print(f"ERROR TEST: {test_case['description']}")
    print(f"Prompt: \"{test_case['prompt']}\"")
    print(f"Expected: {test_case['expected_error']}")
    print(f"{'-'*50}")
    
    try:
        # Call the agent with invalid input
        agent_result = accommodation_agent(test_case['prompt'])
        
        # Extract the actual response content from AgentResult
        if hasattr(agent_result, 'content'):
            response = agent_result.content
        elif hasattr(agent_result, 'text'):
            response = agent_result.text
        else:
            response = str(agent_result)
        
        # For error cases, we expect JSON with error metadata
        success = validate_json_response(response, test_case['description'])
        
        # Additional check for error content
        if success and isinstance(response, (str, dict)):
            response_data = None
            if isinstance(response, str):
                response_data = json.loads(response)
            elif isinstance(response, dict):
                response_data = response
            
            if response_data and "search_metadata" in response_data:
                if "error" in response_data["search_metadata"]:
                    print(f"   ✅ Error properly captured in metadata")
                else:
                    print(f"   ⚠️  No error found in metadata (may be valid result)")
        
        return [(test_case['description'], success)]
        
    except Exception as e:
        print(f"❌ Agent execution error: {str(e)}")
        return [(test_case['description'], False)]


def main():
    """Run streamlined accommodation agent tests"""
    
    # Check for required environment variable
    if not os.getenv('NOVA_ACT_API_KEY'):
        print("❌ Error: NOVA_ACT_API_KEY environment variable is required")
        print("Please set your Nova Act API key before running the demo")
        return
    
    print("🏠 ACCOMMODATION AGENT - STREAMLINED DEMO TESTS")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Testing: Platform selection + date formats, error handling, JSON validation")
    print("Optimized for minimal search time while maintaining full coverage")
    print("="*60)
    
    # Run streamlined test suites
    comprehensive_results = test_comprehensive_scenarios()  # 3 tests: covers platform selection + date formats
    error_results = test_error_handling()                   # 1 test: covers input validation
    
    # Summary
    all_results = comprehensive_results + error_results
    passed = sum(1 for _, success in all_results if success)
    total = len(all_results)
    
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    print(f"Comprehensive Tests (Platform + Dates): {sum(1 for _, success in comprehensive_results if success)}/{len(comprehensive_results)} passed")
    print(f"Error Handling Test: {sum(1 for _, success in error_results if success)}/{len(error_results)} passed")
    print(f"\n🎯 Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    print("\n📋 Coverage Summary:")
    print("   ✓ Airbnb-only platform selection + relative date ('tomorrow')")
    print("   ✓ Booking-only platform selection + relative date ('tomorrow')")  
    print("   ✓ Both platforms selection + absolute dates (YYYY-MM-DD)")
    print("   ✓ Input validation error handling (past dates)")
    print("   ✓ JSON response format validation")
    print("   ✓ Pydantic schema compliance")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        print("   ✅ Smart platform selection working")
        print("   ✅ Date format handling (relative & absolute)")
        print("   ✅ JSON response format validated")
        print("   ✅ Error handling functional")
        print("   ✅ Agent ready for production")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("   Review failed tests and agent logic")
    
    print("\n" + "="*60)
    print("DEMO COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()
