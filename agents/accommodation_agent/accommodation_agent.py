"""
Accommodation Agent - Direct Strands Agent instantiation with standalone tools
"""
from strands import Agent
from .tools import search_airbnb, search_booking_com, search_accommodations

# Create accommodation agent with Nova Pro model and accommodation search tools
accommodation_agent = Agent(
    model="amazon.nova-pro-v1:0",
    tools=[search_airbnb, search_booking_com, search_accommodations],
    system_prompt="""You are an accommodation search specialist. You help users find places to stay by:

1. Understanding natural language requests like "find me a place to stay in Paris for 3 nights starting tomorrow"
2. Extracting key details: location, check-in/out dates, guest count, preferences, budget
3. Using search tools for Airbnb and Booking.com to find accommodation options
4. Presenting results in a clear, helpful manner focusing on what the user requested

Available tools:
- search_airbnb: Search only Airbnb properties
- search_booking_com: Search only Booking.com hotels
- search_accommodations: Search both platforms and combine results (recommended for comprehensive options)

When users ask about accommodations, extract the necessary parameters and call the appropriate search tool.
Always be helpful and provide relevant accommodation information based on user needs."""
)


def main():
    """Example usage of the accommodation agent"""
    
    print("Testing Accommodation Agent:")
    
    # Test direct tool call
    print("\n1. Testing direct tool call - Combined search:")
    result = accommodation_agent.tool.search_accommodations(
        location="Paris, France",
        check_in="2024-06-15",
        check_out="2024-06-18",
        guests=2,
        max_price=180.0
    )
    print(f"Tool result type: {type(result)}")
    
    # Test individual platform
    print("\n2. Testing Airbnb only:")
    airbnb_result = accommodation_agent.tool.search_airbnb(
        location="Barcelona, Spain",
        check_in="2024-06-20",
        check_out="2024-06-23",
        guests=2
    )
    print(f"Airbnb result type: {type(airbnb_result)}")
    
    # Test natural language
    print("\n3. Testing natural language:")
    try:
        response = accommodation_agent("Find me a place to stay in Rome for 3 nights starting June 15th for 2 people under $150 per night")
        print(f"Agent response: {response}")
    except Exception as e:
        print(f"Natural language test error: {e}")


if __name__ == "__main__":
    main()
