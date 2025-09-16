#!/usr/bin/env python3
"""
Terminal Chat Interface for Travel Orchestrator Agent

Provides an interactive terminal-based chat interface to test the travel orchestrator
agent locally with multi-turn conversation support via AgentCore memory.
"""

import os
import sys
import json
import uuid
from datetime import datetime
from typing import Optional

# Add project root and agent directories to Python path
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'agents', 'travel_orchestrator'))

try:
    from agents.travel_orchestrator.travel_orchestrator import TravelOrchestratorAgent
    from common.models.orchestrator_models import TravelOrchestratorResponse, ResponseType
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running this from the project root directory")
    print("Available Python paths:")
    for path in sys.path[:5]:  # Show first 5 paths
        print(f"  - {path}")
    sys.exit(1)

class TravelChatInterface:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.user_id = "chat_user"
        self.conversation_history = []
        self.agent = None
        
    def initialize_agent(self) -> bool:
        """Initialize the travel orchestrator agent"""
        try:
            print("🚀 Initializing Travel Orchestrator Agent...")
            
            # Check for required environment variables
            if not os.getenv('NOVA_ACT_API_KEY'):
                print("⚠️  Warning: NOVA_ACT_API_KEY not set. Agent may not function properly.")
            
            # Initialize agent with session continuity for memory
            self.agent = TravelOrchestratorAgent(
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            print(f"✅ Agent initialized successfully")
            print(f"📝 Session ID: {self.session_id}")
            print(f"👤 User ID: {self.user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            return False
    
    def format_response(self, response) -> str:
        """Format agent response for terminal display"""
        try:
            # Handle different response types from the agent
            if hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'text'):
                content = response.text
            else:
                content = str(response)
            
            # If the response looks like structured JSON, try to parse and format it
            if isinstance(content, str) and content.strip().startswith('{'):
                try:
                    parsed = json.loads(content)
                    return self.format_structured_response(parsed)
                except json.JSONDecodeError:
                    pass
            
            return content
            
        except Exception as e:
            return f"Error formatting response: {e}"
    
    def format_structured_response(self, data: dict) -> str:
        """Format structured agent responses for better readability"""
        try:
            # Check if this is a TravelOrchestratorResponse
            if 'response_type' in data:
                response_type = data.get('response_type')
                message = data.get('message', '')
                
                formatted = f"🤖 {message}\n"
                
                # Add specific formatting based on response type
                if response_type == 'flights' and 'flight_results' in data:
                    formatted += self.format_flight_results(data['flight_results'])
                elif response_type == 'accommodations' and 'accommodation_results' in data:
                    formatted += self.format_accommodation_results(data['accommodation_results'])
                elif response_type == 'restaurants' and 'restaurant_results' in data:
                    formatted += self.format_restaurant_results(data['restaurant_results'])
                elif response_type == 'itinerary':
                    formatted += self.format_comprehensive_plan(data)
                
                # Add metadata if available
                if 'processing_time_seconds' in data:
                    formatted += f"\n⏱️  Processing time: {data['processing_time_seconds']:.2f}s"
                
                return formatted
            
            # Fallback to pretty JSON
            return json.dumps(data, indent=2, default=str)
            
        except Exception as e:
            return f"Error formatting structured response: {e}\n{json.dumps(data, indent=2, default=str)}"
    
    def format_flight_results(self, flight_data: dict) -> str:
        """Format flight search results"""
        if not flight_data:
            return "\n📄 No flight data available"
        
        formatted = "\n✈️  **Flight Results:**\n"
        
        # Handle different flight data structures
        if isinstance(flight_data, dict):
            if 'best_outbound_flight' in flight_data:
                outbound = flight_data['best_outbound_flight']
                formatted += f"   🛫 Outbound: {outbound.get('airline', 'N/A')} - ${outbound.get('price', 'N/A')}\n"
            
            if 'best_return_flight' in flight_data:
                return_flight = flight_data['best_return_flight']
                formatted += f"   🛬 Return: {return_flight.get('airline', 'N/A')} - ${return_flight.get('price', 'N/A')}\n"
            
            if 'recommendation' in flight_data:
                formatted += f"   💡 {flight_data['recommendation']}\n"
        
        return formatted
    
    def format_accommodation_results(self, acc_data: dict) -> str:
        """Format accommodation search results"""
        if not acc_data:
            return "\n📄 No accommodation data available"
        
        formatted = "\n🏨 **Accommodation Results:**\n"
        
        if isinstance(acc_data, dict):
            if 'best_accommodations' in acc_data and acc_data['best_accommodations']:
                best = acc_data['best_accommodations'][0]
                formatted += f"   🏠 {best.get('title', 'N/A')}\n"
                formatted += f"   💰 ${best.get('price_per_night', 'N/A')}/night\n"
                if 'rating' in best:
                    formatted += f"   ⭐ Rating: {best['rating']}\n"
            
            if 'recommendation' in acc_data:
                formatted += f"   💡 {acc_data['recommendation']}\n"
        
        return formatted
    
    def format_restaurant_results(self, restaurant_data: dict) -> str:
        """Format restaurant search results"""
        if not restaurant_data:
            return "\n📄 No restaurant data available"
        
        formatted = "\n🍽️  **Restaurant Results:**\n"
        
        if isinstance(restaurant_data, dict):
            if 'recommendations' in restaurant_data and restaurant_data['recommendations']:
                for i, restaurant in enumerate(restaurant_data['recommendations'][:3], 1):
                    formatted += f"   {i}. {restaurant.get('name', 'N/A')}\n"
                    if 'cuisine' in restaurant:
                        formatted += f"      🍴 {restaurant['cuisine']}\n"
                    if 'rating' in restaurant:
                        formatted += f"      ⭐ {restaurant['rating']}\n"
            
            if 'recommendation' in restaurant_data:
                formatted += f"   💡 {restaurant_data['recommendation']}\n"
        
        return formatted
    
    def format_comprehensive_plan(self, data: dict) -> str:
        """Format comprehensive travel plan"""
        formatted = "\n🌍 **Comprehensive Travel Plan:**\n"
        
        # Show individual results if available
        if 'flight_results' in data and data['flight_results']:
            formatted += self.format_flight_results(data['flight_results'])
        
        if 'accommodation_results' in data and data['accommodation_results']:
            formatted += self.format_accommodation_results(data['accommodation_results'])
        
        if 'restaurant_results' in data and data['restaurant_results']:
            formatted += self.format_restaurant_results(data['restaurant_results'])
        
        # Show cost estimates if available
        if 'estimated_costs' in data and data['estimated_costs']:
            formatted += "\n💰 **Estimated Costs:**\n"
            for category, cost in data['estimated_costs'].items():
                formatted += f"   {category.title()}: ${cost}\n"
        
        return formatted
    
    def show_help(self):
        """Display help information"""
        help_text = """
🌍 **Travel Orchestrator Chat Interface**

**Available Commands:**
   /help     - Show this help message
   /quit     - Exit the chat
   /clear    - Clear conversation history display
   /session  - Show current session information
   /status   - Show agent status

**Example Queries:**
   • "Plan a trip to Paris from NYC for 2 people next week"
   • "Find flights from San Francisco to Tokyo tomorrow" 
   • "I need a hotel in Rome for 3 nights"
   • "Show me restaurants in downtown Chicago"
   • "What's the weather like in London?" (general questions)

**Tips:**
   • The agent remembers our conversation via AgentCore Memory
   • Ask follow-up questions to refine your travel plans
   • Be specific about dates, locations, and number of travelers
   • The agent coordinates multiple specialist agents for comprehensive planning

Type your travel planning questions or commands starting with '/'
        """
        print(help_text)
    
    def show_session_info(self):
        """Display current session information"""
        print(f"\n📊 **Session Information:**")
        print(f"   Session ID: {self.session_id}")
        print(f"   User ID: {self.user_id}")
        print(f"   Messages in history: {len(self.conversation_history)}")
        print(f"   Agent initialized: {'✅ Yes' if self.agent else '❌ No'}")
    
    def clear_display(self):
        """Clear the terminal display"""
        os.system('clear' if os.name == 'posix' else 'cls')
        print("🌍 Travel Orchestrator Chat - Conversation cleared")
        print("Type /help for available commands\n")
    
    def run_chat(self):
        """Main chat loop"""
        print("=" * 60)
        print("🌍 Welcome to Travel Orchestrator Chat Interface")
        print("=" * 60)
        
        # Initialize agent
        if not self.initialize_agent():
            return
        
        print("\n💬 Chat started! Type /help for commands or start planning your trip.")
        print("   Example: 'Plan a weekend trip to Paris for 2 people'\n")
        
        try:
            while True:
                # Get user input
                try:
                    user_input = input("You: ").strip()
                except KeyboardInterrupt:
                    print("\n\n👋 Chat interrupted. Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    command = user_input.lower()
                    
                    if command in ['/quit', '/exit']:
                        print("👋 Thanks for using Travel Orchestrator Chat. Goodbye!")
                        break
                    elif command == '/help':
                        self.show_help()
                        continue
                    elif command == '/clear':
                        self.clear_display()
                        continue
                    elif command == '/session':
                        self.show_session_info()
                        continue
                    elif command == '/status':
                        print(f"🤖 Agent Status: {'✅ Ready' if self.agent else '❌ Not initialized'}")
                        continue
                    else:
                        print(f"❌ Unknown command: {user_input}. Type /help for available commands.")
                        continue
                
                # Process with agent
                print("🤔 Processing your request...")
                
                try:
                    # Call the agent
                    response = self.agent(user_input)
                    
                    # Format and display response
                    formatted_response = self.format_response(response)
                    print(f"\n🤖 Agent: {formatted_response}\n")
                    
                    # Store in conversation history
                    self.conversation_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'user': user_input,
                        'agent': formatted_response
                    })
                    
                except Exception as e:
                    print(f"❌ Error processing request: {e}")
                    print("Please try again or type /help for assistance.\n")
        
        except Exception as e:
            print(f"❌ Unexpected error in chat loop: {e}")


def main():
    """Main entry point"""
    try:
        chat = TravelChatInterface()
        chat.run_chat()
    except KeyboardInterrupt:
        print("\n\n👋 Chat terminated. Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
