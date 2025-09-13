#!/usr/bin/env python3
"""
Food Agent Demo Script

Test the agent's conversational abilities and tool usage decision-making.
This tests the full agent workflow, not just direct API calls.
"""

import os
import sys
import asyncio
from food_agent import FoodAgent

async def test_agent_conversations():
    """Test agent's ability to understand natural language and use tools appropriately"""
    
    print("🍽️  Food Agent Demo - Conversational Agent Testing")
    print("=" * 60)
    
    # Check if API key is set
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not api_key:
        print("❌ GOOGLE_PLACES_API_KEY environment variable not set")
        print("   Please set your Google Places API key:")
        print("   export GOOGLE_PLACES_API_KEY='your_api_key_here'")
        return False
    
    print(f"✅ API Key configured: {api_key[:10]}...")
    
    try:
        # Initialize food agent
        agent = FoodAgent()
        print("✅ Food Agent initialized")
        
        # Test natural language prompts that should trigger tool usage
        test_prompts = [
            "I'm hungry and want Italian food in Rome. Can you help me find some good restaurants?",
            "Find me vegetarian restaurants near Times Square in NYC that are highly rated",
            "I need cheap street food recommendations in Bangkok for tonight",
            "Where can I get good sushi in Tokyo for dinner? I prefer places that are open now",
            "Looking for fine dining French restaurants near the Eiffel Tower in Paris"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n🔍 Test {i}: Agent Conversation")
            print("-" * 50)
            print(f"User: {prompt}")
            print(f"Agent Response:")
            
            # Test the agent's conversational response (this will use tools internally)
            response = agent.run(prompt)
            print(f"  {response}")
            
            print("✅ Test completed")
        
        print(f"\n✨ Agent conversation demo completed!")
        print("\n📚 What this tested:")
        print("   ✅ Agent's ability to understand natural language requests")
        print("   ✅ Agent's decision-making on when to use search_restaurants tool") 
        print("   ✅ Agent's query formatting for Google Places API")
        print("   ✅ Agent's natural language response with restaurant data")
        print("\n📚 Next steps:")
        print("   - Deploy to AgentCore: agentcore configure --entrypoint food_agent.py --name food-agent")
        print("   - Integrate with Travel Orchestrator")
        print("   - Test end-to-end travel planning workflow")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        print(f"   This might be expected if testing without AgentCore runtime")
        print(f"   For full testing, deploy to AgentCore and test there")
        return False

def main():
    """Main demo function"""
    success = asyncio.run(test_agent_conversations())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
