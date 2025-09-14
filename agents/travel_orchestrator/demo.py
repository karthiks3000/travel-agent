#!/usr/bin/env python3
"""
Interactive Terminal Chat Demo for Travel Orchestrator Agent
"""
import sys
import os
import uuid
import asyncio
from datetime import datetime

from common.models.travel_models import TravelInformation, ValidationResult
from tools.validation_tools import validate_travel_requirements, validate_dates
from tools.agent_invocation import format_travel_request
from tools.memory_hooks import generate_session_ids

# Mock travel orchestrator for demo (without actual agent dependencies)
class MockTravelOrchestrator:
    def __init__(self, user_id="demo_user"):
        self.user_id = user_id
        self.id_config = generate_session_ids(user_id=user_id)
        self.session_id = self.id_config["session_id"]
        self.actor_id = self.id_config["orchestrator"]
        self.conversation_history = []
        
        print(f"🚀 Initialized Travel Orchestrator")
        print(f"   Session ID: {self.session_id}")
        print(f"   Actor ID: {self.actor_id}")
    
    def process_user_message(self, user_message: str) -> str:
        """Process user message and return orchestrator response"""
        self.conversation_history.append({"role": "user", "content": user_message, "timestamp": datetime.now()})
        
        # Extract travel information from the conversation
        travel_info = self._extract_travel_info_from_conversation()
        
        # Validate requirements
        try:
            validation_result = validate_travel_requirements(travel_info)
            
            response = self._generate_response(user_message, travel_info, validation_result)
            
            self.conversation_history.append({"role": "assistant", "content": response, "timestamp": datetime.now()})
            return response
            
        except Exception as e:
            error_response = f"I encountered an error while processing your request: {str(e)}"
            self.conversation_history.append({"role": "assistant", "content": error_response, "timestamp": datetime.now()})
            return error_response
    
    def _extract_travel_info_from_conversation(self) -> TravelInformation:
        """Extract travel information from conversation history"""
        # This is a simplified extraction for demo purposes
        # In reality, the agent would use LLM to extract this information
        
        travel_data = {}
        
        # Look for destination mentions
        for message in self.conversation_history:
            if message["role"] == "user":
                content = message["content"].lower()
                
                # Simple keyword extraction
                if "paris" in content:
                    travel_data["destination"] = "Paris, France"
                elif "tokyo" in content:
                    travel_data["destination"] = "Tokyo, Japan"
                elif "london" in content:
                    travel_data["destination"] = "London, UK"
                elif "nyc" in content or "new york" in content:
                    travel_data["origin"] = "New York, NY"
                elif "la" in content or "los angeles" in content:
                    travel_data["origin"] = "Los Angeles, CA"
                
                # Look for passenger/guest mentions
                import re
                numbers = re.findall(r'\b(\d+)\s+(?:people|passengers|guests|travelers)\b', content)
                if numbers:
                    travel_data["passengers"] = int(numbers[0])
                    travel_data["guests"] = int(numbers[0])
        
        return TravelInformation.model_validate(travel_data)
    
    def _generate_response(self, user_message: str, travel_info: TravelInformation, validation_result: ValidationResult) -> str:
        """Generate orchestrator response based on validation"""
        
        if validation_result.completeness_score == 0:
            return """I'd love to help you plan your trip! To get started, I need some basic information:

• What's your destination city?
• What city will you be departing from?
• What are your travel dates?
• How many people will be traveling?

Just let me know these details and I'll start searching for the best options!"""
        
        elif validation_result.completeness_score < 0.5:
            questions = validation_result.next_questions[:2]  # Ask max 2 questions
            question_list = "\n".join([f"• {q}" for q in questions])
            
            destination_str = f" to {travel_info.destination}" if travel_info.destination else ""
            
            return f"""Great! I'm getting the details for your trip{destination_str}.

I still need:
{question_list}

Once I have this information, I can search for flights, accommodations, and restaurants!"""
        
        elif validation_result.completeness_score >= 0.5 and not all(validation_result.can_search.values()):
            ready_agents = ", ".join(validation_result.ready_agents)
            questions = validation_result.next_questions[:2]
            question_list = "\n".join([f"• {q}" for q in questions])
            
            return f"""Perfect! I have most of the information I need.

I can already search for: {ready_agents}

Just need:
{question_list}

Should I start searching with what I have, or would you like to provide the missing details first?"""
        
        else:
            # Complete information - simulate agent searches
            travel_request = format_travel_request(travel_info)
            
            return f"""Excellent! I have all the information I need:

📝 **Trip Summary**: {travel_request}

🔄 **Starting comprehensive search...**

✈️  Searching flights: {travel_info.origin} → {travel_info.destination}
🏨 Searching accommodations: {travel_info.destination} for {travel_info.guests} guests
🍽️  Searching restaurants: {travel_info.destination} dining options

⏳ **[In production, this would invoke the actual specialist agents in parallel]**

📊 **Validation Results:**
• Completeness: {validation_result.completeness_score:.1%}
• Ready agents: {', '.join(validation_result.ready_agents)}
• Session ID: {self.session_id}

💡 **Note**: This is a demo showing the orchestrator's validation and conversation flow. In production, real specialist agents would be called to search flights, hotels, and restaurants."""

def print_header():
    """Print chat interface header"""
    print("\n" + "="*70)
    print("🌍 TRAVEL ORCHESTRATOR AGENT - INTERACTIVE DEMO")
    print("="*70)
    print("💬 Type your travel requests and see how the orchestrator responds")
    print("🔧 Features: Validation, conversation flow, memory integration")
    print("📝 Commands: 'quit' or 'exit' to end, 'reset' to start over")
    print("="*70)

def print_conversation_stats(orchestrator):
    """Print conversation statistics"""
    total_messages = len(orchestrator.conversation_history)
    user_messages = len([m for m in orchestrator.conversation_history if m["role"] == "user"])
    assistant_messages = len([m for m in orchestrator.conversation_history if m["role"] == "assistant"])
    
    print(f"\n📊 **Conversation Stats**:")
    print(f"   • Total messages: {total_messages}")
    print(f"   • User messages: {user_messages}")
    print(f"   • Assistant messages: {assistant_messages}")
    print(f"   • Session ID: {orchestrator.session_id}")

def main():
    """Interactive chat demo"""
    print_header()
    
    # Initialize the mock orchestrator
    orchestrator = MockTravelOrchestrator()
    
    print(f"🤖 **Travel Orchestrator**: Hello! I'm your AI travel planning assistant.")
    print(f"    I can help you plan trips by coordinating flights, accommodations, and restaurants.")
    print(f"    What kind of trip are you planning?\n")
    
    while True:
        try:
            # Get user input
            user_input = input("👤 **You**: ").strip()
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print(f"\n🤖 **Travel Orchestrator**: Thanks for testing the travel orchestrator! Safe travels! 🛫")
                print_conversation_stats(orchestrator)
                break
            elif user_input.lower() in ['reset', 'restart']:
                orchestrator = MockTravelOrchestrator()
                print(f"\n🤖 **Travel Orchestrator**: Let's start planning a new trip! What can I help you with?")
                continue
            elif user_input.lower() in ['help', '?']:
                print(f"\n🤖 **Travel Orchestrator**: Here are some example requests you can try:")
                print(f"   • 'Plan a trip to Paris'")
                print(f"   • 'Find flights from NYC to Tokyo in December'")
                print(f"   • 'I want to go to London for 5 days with 2 people'")
                print(f"   • 'Book a family trip to Disney World'")
                continue
            elif not user_input:
                continue
            
            # Process the message
            print(f"\n🤖 **Travel Orchestrator**:")
            
            try:
                # Show thinking process
                print(f"   🔍 Analyzing request...")
                
                response = orchestrator.process_user_message(user_input)
                print(f"   {response}")
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                print(f"   Please try rephrasing your request.")
            
            print()  # Add spacing
            
        except KeyboardInterrupt:
            print(f"\n\n🤖 **Travel Orchestrator**: Goodbye! Thanks for testing the orchestrator!")
            print_conversation_stats(orchestrator)
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            print(f"Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    print(f"🧪 Travel Orchestrator Interactive Demo")
    print(f"📅 Demo Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Purpose: Test conversation flow and validation logic")
    
    try:
        main()
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
