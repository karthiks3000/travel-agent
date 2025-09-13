"""
Standalone tools for accommodation search using Nova Act browser automation
"""
import os
import sys
from datetime import datetime
from strands import tool
from typing import Optional, Dict, Any, List

# Add common directory to path for browser wrapper import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from common.browser_wrapper import BrowserWrapper
from models.accommodation_models import PlatformSearchResults

# Create browser wrapper instance based on environment configuration
USE_AGENTCORE = os.getenv('USE_AGENTCORE_BROWSER', 'false').lower() == 'true'
REGION = os.getenv('AGENTCORE_REGION', 'us-east-1')

browser_wrapper = BrowserWrapper(
    use_agentcore_browser=USE_AGENTCORE,
    region=REGION
)


@tool(description="Search Airbnb for accommodation options using browser automation")
def search_airbnb(location: str, check_in: str, check_out: str, guests: int = 2) -> Dict[str, Any]:
    """
    Search Airbnb using Nova Act browser automation
    
    Args:
        location: Destination city or location (e.g., 'Paris, France', 'Manhattan, NYC')
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of guests (1-16)
        
    Returns:
        Dictionary with Airbnb search results
    """
    print(f"🏠 Searching Airbnb: {location} | {check_in} to {check_out} | {guests} guests")
    
    # Format instructions with actual values for Airbnb
    instructions = [
        f"Click on the location search field and enter '{location}'",
        "Wait for location suggestions to appear and select the first relevant option",
        f"Click on the check-in date field",
        f"Navigate to the calendar and select {check_in} as check-in date",
        f"Navigate to the calendar and select {check_out} as check-out date",
        f"Click on the guests field",
        f"Set the number of guests to {guests}",
        "Click the Search button to start searching for properties",
        "Wait for the search results page to load completely",
        "Apply filter for 'Entire place' if available",
        "Apply rating filter for 4.0+ stars if available"
    ]
    
    extraction_instruction = f"""Extract Airbnb property listings from the search results.
    
    For each visible property listing (up to 20), extract:
    
    1. TITLE: Property title/name
    2. PRICE_PER_NIGHT: Price per night (extract number only, no currency symbol)
    3. TOTAL_PRICE: Total price for the stay if shown
    4. RATING: Property rating (e.g., 4.8, 4.9)
    5. REVIEW_COUNT: Number of reviews
    6. PROPERTY_TYPE: Type like 'Entire apartment', 'Private room', 'Entire house'
    7. HOST_NAME: Host name if available
    8. LOCATION: Neighborhood or area within {location}
    9. AMENITIES: Key amenities like 'WiFi', 'Kitchen', 'Parking', 'Pool' (up to 5)
    10. GUESTS_CAPACITY: Maximum guests if shown
    11. BEDROOMS: Number of bedrooms if shown
    12. BATHROOMS: Number of bathrooms if shown
    
    Return structured data with platform set to 'airbnb'."""
    
    return browser_wrapper.execute_instructions(
        starting_page="https://www.airbnb.com",
        instructions=instructions,
        extraction_instruction=extraction_instruction,
        result_schema=PlatformSearchResults.model_json_schema()
    )


@tool(description="Search Booking.com for hotel and accommodation options using browser automation")
def search_booking_com(location: str, check_in: str, check_out: str, guests: int = 2, rooms: int = 1) -> Dict[str, Any]:
    """
    Search Booking.com using Nova Act browser automation
    
    Args:
        location: Destination city or location (e.g., 'Paris, France', 'Manhattan, NYC')
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of guests (1-30)
        rooms: Number of rooms (1-8)
        
    Returns:
        Dictionary with Booking.com search results
    """
    print(f"🏨 Searching Booking.com: {location} | {check_in} to {check_out} | {guests} guests, {rooms} rooms")
    
    # Format instructions with actual values for Booking.com
    instructions = [
        f"Click on the destination search field and enter '{location}'",
        "Wait for destination suggestions and select the first relevant city option",
        f"Click on the check-in date field",
        f"Navigate the calendar and select {check_in} as check-in date",
        f"Navigate the calendar and select {check_out} as check-out date", 
        f"Click on the guests and rooms selector",
        f"Set {guests} adults and {rooms} room",
        "Click the Search button to find accommodations",
        "Wait for the search results to load completely",
        "Apply price filter if available to show reasonable options",
        "Apply rating filter for 7.5+ rating if available"
    ]
    
    extraction_instruction = f"""Extract hotel and accommodation listings from Booking.com search results.
    
    For each visible property listing (up to 20), extract:
    
    1. TITLE: Hotel/property name
    2. PRICE_PER_NIGHT: Price per night (extract number only, no currency symbol)
    3. TOTAL_PRICE: Total price for the stay if displayed
    4. RATING: Property rating (e.g., 8.5, 9.2)
    5. REVIEW_COUNT: Number of reviews/scores
    6. PROPERTY_TYPE: Type like 'Hotel', 'Apartment', 'Guesthouse', 'Resort'
    7. HOST_NAME: Hotel chain or property management name
    8. LOCATION: Specific area or district within {location}
    9. AMENITIES: Key amenities like 'Free WiFi', 'Breakfast included', 'Parking', 'Pool' (up to 5)
    10. GUESTS_CAPACITY: Maximum guests if shown
    11. BEDROOMS: Number of bedrooms if shown (for apartments)
    12. BATHROOMS: Number of bathrooms if shown
    
    Return structured data with platform set to 'booking_com'."""
    
    return browser_wrapper.execute_instructions(
        starting_page="https://www.booking.com",
        instructions=instructions,
        extraction_instruction=extraction_instruction,
        result_schema=PlatformSearchResults.model_json_schema()
    )


@tool(description="Search both Airbnb and Booking.com and combine results for comprehensive accommodation options")
def search_accommodations(location: str, check_in: str, check_out: str, 
                         guests: int = 2, max_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Search both Airbnb and Booking.com and combine results
    
    Args:
        location: Destination city or location
        check_in: Check-in date in YYYY-MM-DD format  
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of guests
        max_price: Maximum price per night filter (optional)
        
    Returns:
        Combined accommodation search results from both platforms
    """
    print(f"🔍 Comprehensive accommodation search: {location}")
    print(f"   Dates: {check_in} to {check_out} | Guests: {guests}")
    if max_price:
        print(f"   Max price: ${max_price}/night")
    
    # Search both platforms
    try:
        print("\n📍 Searching Airbnb...")
        airbnb_results = search_airbnb(location, check_in, check_out, guests)
        
        print("\n📍 Searching Booking.com...")  
        booking_results = search_booking_com(location, check_in, check_out, guests)
        
        # Combine results
        combined_results = _combine_accommodation_results(
            airbnb_results, booking_results, max_price
        )
        
        return combined_results
        
    except Exception as e:
        print(f"❌ Combined search error: {str(e)}")
        return {
            "airbnb_properties": [],
            "booking_properties": [],
            "combined_results": [],
            "search_metadata": {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "search_params": {
                    "location": location,
                    "check_in": check_in,
                    "check_out": check_out,
                    "guests": guests
                }
            }
        }


def _combine_accommodation_results(airbnb_results: Dict[str, Any], 
                                 booking_results: Dict[str, Any], 
                                 max_price: Optional[float] = None) -> Dict[str, Any]:
    """Combine and sort results from both platforms"""
    
    # Extract properties from platform results
    airbnb_properties = []
    booking_properties = []
    
    if isinstance(airbnb_results, dict) and "properties" in airbnb_results:
        airbnb_properties = airbnb_results["properties"]
    elif isinstance(airbnb_results, dict) and "airbnb_properties" in airbnb_results:
        airbnb_properties = airbnb_results["airbnb_properties"]
        
    if isinstance(booking_results, dict) and "properties" in booking_results:
        booking_properties = booking_results["properties"]
    elif isinstance(booking_results, dict) and "booking_properties" in booking_results:
        booking_properties = booking_results["booking_properties"]
    
    # Apply price filter if specified
    if max_price:
        airbnb_properties = [p for p in airbnb_properties 
                           if isinstance(p, dict) and p.get("price_per_night", 0) <= max_price]
        booking_properties = [p for p in booking_properties
                            if isinstance(p, dict) and p.get("price_per_night", 0) <= max_price]
    
    # Combine all properties
    all_properties = airbnb_properties + booking_properties
    
    # Sort by rating (descending) then by price (ascending)
    def sort_key(prop):
        if isinstance(prop, dict):
            rating = prop.get("rating", 0) or 0
            price = prop.get("price_per_night", 999999) or 999999
            return (-rating, price)  # Negative rating for descending sort
        return (0, 999999)
    
    sorted_properties = sorted(all_properties, key=sort_key)
    
    return {
        "airbnb_properties": airbnb_properties,
        "booking_properties": booking_properties, 
        "combined_results": sorted_properties[:20],  # Top 20 results
        "search_metadata": {
            "timestamp": datetime.now().isoformat(),
            "airbnb_count": len(airbnb_properties),
            "booking_count": len(booking_properties),
            "total_found": len(all_properties),
            "filtered_count": len(sorted_properties[:20]),
            "price_filter": max_price
        }
    }

</final_file_content>

IMPORTANT: For any future changes to this file, use the final_file_content shown above as your reference. This content reflects the current state of the file, including any auto-formatting (e.g., if you used single quotes but the formatter converted them to double quotes). Always base your SEARCH/REPLACE operations on this final version to ensure accuracy.

<environment_details>
# VSCode Visible Files
agents/flight_agent/flight_agent.py

# VSCode Open Tabs
agents/flight_agent/flight_search.py
common/__init__.py
common/browser_wrapper.py
agents/flight_agent/tools.py
agents/flight_agent/flight_agent.py
agents/food_agent/food_agent.py
agents/accommodation_agent/accommodation_agent.py
agents/flight_agent/demo_strands.py
agents/food_agent/demo.py
agents/accommodation_agent/__init__.py
agents/accommodation_agent/models/__init__.py
agents/accommodation_agent/models/accommodation_models.py
agents/accommodation_agent/demo_strands.py
agents/accommodation_agent/requirements.txt
agents/accommodation_agent/README.md
integration_test.py

# Current Time
9/13/2025, 10:52:24 AM (America/New_York, UTC-4:00)

# Context Window Usage
217,649 / 1,000K tokens used (22%)

# Current Mode
ACT MODE
</environment_details>

<replace_in_file>
<path>agents/accommodation_agent/accommodation_agent.py</path>
<diff>
------- SEARCH
"""
Accommodation Agent - Strands implementation with Nova Pro and browser wrapper
"""
import os
import sys
from datetime import datetime, timedelta
from strands import Agent, tool
from typing import Optional, Dict, Any, List

# Add common directory to path for browser wrapper import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from common.browser_wrapper import BrowserWrapper
from models.accommodation_models import PropertyResult, AccommodationSearchResults, PlatformSearchResults


class AccommodationAgent(Agent):
    """Intelligent accommodation search agent using Nova Pro and browser automation"""
    
    def __init__(self, use_agentcore_browser=False, region="us-east-1"):
        super().__init__(
            model="amazon.nova-pro-v1:0"
        )
        self.browser_wrapper = BrowserWrapper(
            use_agentcore_browser=use_agentcore_browser,
            region=region
        )
    
    @tool
    def search_airbnb(self, location: str, check_in: str, check_out: str, guests: int = 2) -> Dict[str, Any]:
        """
        Search Airbnb using Nova Act browser automation
        
        Args:
            location: Destination city or location (e.g., 'Paris, France', 'Manhattan, NYC')
            check_in: Check-in date in YYYY-MM-DD format
            check_out: Check-out date in YYYY-MM-DD format
            guests: Number of guests (1-16)
            
        Returns:
            Dictionary with Airbnb search results
        """
        print(f"🏠 Searching Airbnb: {location} | {check_in} to {check_out} | {guests} guests")
        
        # Format instructions with actual values for Airbnb
        instructions = [
            f"Click on the location search field and enter '{location}'",
            "Wait for location suggestions to appear and select the first relevant option",
            f"Click on the check-in date field",
            f"Navigate to the calendar and select {check_in} as check-in date",
            f"Navigate to the calendar and select {check_out} as check-out date",
            f"Click on the guests field",
            f"Set the number of guests to {guests}",
            "Click the Search button to start searching for properties",
            "Wait for the search results page to load completely",
            "Apply filter for 'Entire place' if available",
            "Apply rating filter for 4.0+ stars if available"
        ]
        
        extraction_instruction = f"""Extract Airbnb property listings from the search results.
        
        For each visible property listing (up to 20), extract:
        
        1. TITLE: Property title/name
        2. PRICE_PER_NIGHT: Price per night (extract number only, no currency symbol)
        3. TOTAL_PRICE: Total price for the stay if shown
        4. RATING: Property rating (e.g., 4.8, 4.9)
        5. REVIEW_COUNT: Number of reviews
        6. PROPERTY_TYPE: Type like 'Entire apartment', 'Private room', 'Entire house'
        7. HOST_NAME: Host name if available
        8. LOCATION: Neighborhood or area within {location}
        9. AMENITIES: Key amenities like 'WiFi', 'Kitchen', 'Parking', 'Pool' (up to 5)
        10. GUESTS_CAPACITY: Maximum guests if shown
        11. BEDROOMS: Number of bedrooms if shown
        12. BATHROOMS: Number of bathrooms if shown
        
        Return structured data with platform set to 'airbnb'."""
        
        result = self.browser_wrapper.execute_instructions(
            starting_page="https://www.airbnb.com",
            instructions=instructions,
            extraction_instruction=extraction_instruction,
            result_schema=PlatformSearchResults.model_json_schema()
        )
        
        return result
    
    @tool
    def search_booking_com(self, location: str, check_in: str, check_out: str, guests: int = 2, rooms: int = 1) -> Dict[str, Any]:
        """
        Search Booking.com using Nova Act browser automation
        
        Args:
            location: Destination city or location (e.g., 'Paris, France', 'Manhattan, NYC')
            check_in: Check-in date in YYYY-MM-DD format
            check_out: Check-out date in YYYY-MM-DD format
            guests: Number of guests (1-30)
            rooms: Number of rooms (1-8)
            
        Returns:
            Dictionary with Booking.com search results
        """
        print(f"🏨 Searching Booking.com: {location} | {check_in} to {check_out} | {guests} guests, {rooms} rooms")
        
        # Format instructions with actual values for Booking.com
        instructions = [
            f"Click on the destination search field and enter '{location}'",
            "Wait for destination suggestions and select the first relevant city option",
            f"Click on the check-in date field",
            f"Navigate the calendar and select {check_in} as check-in date",
            f"Navigate the calendar and select {check_out} as check-out date", 
            f"Click on the guests and rooms selector",
            f"Set {guests} adults and {rooms} room",
            "Click the Search button to find accommodations",
            "Wait for the search results to load completely",
            "Apply price filter if available to show reasonable options",
            "Apply rating filter for 7.5+ rating if available"
        ]
        
        extraction_instruction = f"""Extract hotel and accommodation listings from Booking.com search results.
        
        For each visible property listing (up to 20), extract:
        
        1. TITLE: Hotel/property name
        2. PRICE_PER_NIGHT: Price per night (extract number only, no currency symbol)
        3. TOTAL_PRICE: Total price for the stay if displayed
        4. RATING: Property rating (e.g., 8.5, 9.2)
        5. REVIEW_COUNT: Number of reviews/scores
        6. PROPERTY_TYPE: Type like 'Hotel', 'Apartment', 'Guesthouse', 'Resort'
        7. HOST_NAME: Hotel chain or property management name
        8. LOCATION: Specific area or district within {location}
        9. AMENITIES: Key amenities like 'Free WiFi', 'Breakfast included', 'Parking', 'Pool' (up to 5)
        10. GUESTS_CAPACITY: Maximum guests if shown
        11. BEDROOMS: Number of bedrooms if shown (for apartments)
        12. BATHROOMS: Number of bathrooms if shown
        
        Return structured data with platform set to 'booking_com'."""
        
        result = self.browser_wrapper.execute_instructions(
            starting_page="https://www.booking.com",
            instructions=instructions,
            extraction_instruction=extraction_instruction,
            result_schema=PlatformSearchResults.model_json_schema()
        )
        
        return result
    
    @tool 
    def search_accommodations(self, location: str, check_in: str, check_out: str, 
                             guests: int = 2, max_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Search both Airbnb and Booking.com and combine results
        
        Args:
            location: Destination city or location
            check_in: Check-in date in YYYY-MM-DD format  
            check_out: Check-out date in YYYY-MM-DD format
            guests: Number of guests
            max_price: Maximum price per night filter (optional)
            
        Returns:
            Combined accommodation search results from both platforms
        """
        print(f"🔍 Comprehensive accommodation search: {location}")
        print(f"   Dates: {check_in} to {check_out} | Guests: {guests}")
        if max_price:
            print(f"   Max price: ${max_price}/night")
        
        # Search both platforms
        try:
            print("\n📍 Searching Airbnb...")
            airbnb_results = self.search_airbnb(location, check_in, check_out, guests)
            
            print("\n📍 Searching Booking.com...")  
            booking_results = self.search_booking_com(location, check_in, check_out, guests)
            
            # Combine results
            combined_results = self._combine_accommodation_results(
                airbnb_results, booking_results, max_price
            )
            
            return combined_results
            
        except Exception as e:
            print(f"❌ Combined search error: {str(e)}")
            return {
                "airbnb_properties": [],
                "booking_properties": [],
                "combined_results": [],
                "search_metadata": {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "search_params": {
                        "location": location,
                        "check_in": check_in,
                        "check_out": check_out,
                        "guests": guests
                    }
                }
            }
    
    def _combine_accommodation_results(self, airbnb_results: Dict[str, Any], 
                                     booking_results: Dict[str, Any], 
                                     max_price: Optional[float] = None) -> Dict[str, Any]:
        """Combine and sort results from both platforms"""
        
        # Extract properties from platform results
        airbnb_properties = []
        booking_properties = []
        
        if isinstance(airbnb_results, dict) and "properties" in airbnb_results:
            airbnb_properties = airbnb_results["properties"]
        elif isinstance(airbnb_results, dict) and "airbnb_properties" in airbnb_results:
            airbnb_properties = airbnb_results["airbnb_properties"]
            
        if isinstance(booking_results, dict) and "properties" in booking_results:
            booking_properties = booking_results["properties"]
        elif isinstance(booking_results, dict) and "booking_properties" in booking_results:
            booking_properties = booking_results["booking_properties"]
        
        # Apply price filter if specified
        if max_price:
            airbnb_properties = [p for p in airbnb_properties 
                               if isinstance(p, dict) and p.get("price_per_night", 0) <= max_price]
            booking_properties = [p for p in booking_properties
                                if isinstance(p, dict) and p.get("price_per_night", 0) <= max_price]
        
        # Combine all properties
        all_properties = airbnb_properties + booking_properties
        
        # Sort by rating (descending) then by price (ascending)
        def sort_key(prop):
            if isinstance(prop, dict):
                rating = prop.get("rating", 0) or 0
                price = prop.get("price_per_night", 999999) or 999999
                return (-rating, price)  # Negative rating for descending sort
            return (0, 999999)
        
        sorted_properties = sorted(all_properties, key=sort_key)
        
        return {
            "airbnb_properties": airbnb_properties,
            "booking_properties": booking_properties, 
            "combined_results": sorted_properties[:20],  # Top 20 results
            "search_metadata": {
                "timestamp": datetime.now().isoformat(),
                "airbnb_count": len(airbnb_properties),
                "booking_count": len(booking_properties),
                "total_found": len(all_properties),
                "filtered_count": len(sorted_properties[:20]),
                "price_filter": max_price
            }
        }
    
    def _parse_date_reference(self, date_text: str) -> str:
        """Parse relative date references like 'tomorrow', 'next week', etc."""
        today = datetime.now().date()
        
        if "tomorrow" in date_text.lower():
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "next week" in date_text.lower():
            return (today + timedelta(days=7)).strftime("%Y-%m-%d")
        elif "next month" in date_text.lower():
            return (today + timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            # Return as-is, assume it's already in proper format
            return date_text


def main():
    """Example usage of the accommodation agent"""
    
    print("Testing Accommodation Agent with local browser:")
    agent = AccommodationAgent(use_agentcore_browser=False)
    
    # Calculate dates for testing
    check_in = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")
    
    # Test combined search
    print(f"\nTesting combined search: Paris | {check_in} to {check_out}")
    results = agent.search_accommodations(
        location="Paris, France",
        check_in=check_in,
        check_out=check_out,
        guests=2,
        max_price=200.0
    )
    
    print("\n" + "="*60)
    print("ACCOMMODATION SEARCH RESULTS")
    print("="*60)
    
    if isinstance(results, dict):
        airbnb_count = len(results.get("airbnb_properties", []))
        booking_count = len(results.get("booking_properties", []))
        combined_count = len(results.get("combined_results", []))
        
        print(f"Airbnb properties found: {airbnb_count}")
        print(f"Booking.com properties found: {booking_count}")
        print(f"Combined top results: {combined_count}")
        
        # Show top 5 combined results
        combined_results = results.get("combined_results", [])
        for i, prop in enumerate(combined_results[:5], 1):
            if isinstance(prop, dict):
                print(f"\n{i}. {prop.get('title', 'Unknown Property')} ({prop.get('platform', '').upper()})")
                print(f"   Price: ${prop.get('price_per_night', 'N/A')}/night")
                print(f"   Rating: {prop.get('rating', 'N/A')} ({prop.get('review_count', 'N/A')} reviews)")
                print(f"   Type: {prop.get('property_type', 'N/A')}")
                print(f"   Location: {prop.get('location', 'N/A')}")
    else:
        print("Search failed or returned unexpected format")
        print("Results:", results)


if __name__ == "__main__":
    main()
=======
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
+++++++ REPLACE
</diff>
</replace_in_file>
