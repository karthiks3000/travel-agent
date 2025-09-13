"""
Flight search implementation supporting both local Nova Act and AgentCore Browser Tool
"""
import os
from nova_act import NovaAct
from models.flight_models import FlightResult, FlightSearchResults, FlightSearchParams
from typing import Optional, List
from datetime import datetime

class FlightSearcher:
    """Flight search supporting both local Nova Act and AgentCore Browser Tool"""
    
    def __init__(self, use_agentcore_browser=False, region="us-east-1"):
        self.api_key = os.getenv('NOVA_ACT_API_KEY')
        if not self.api_key:
            raise ValueError("NOVA_ACT_API_KEY environment variable is required")
        self.use_agentcore_browser = use_agentcore_browser
        self.region = region
        
        # Ensure Playwright modules are installed automatically
        os.environ['NOVA_ACT_SKIP_PLAYWRIGHT_INSTALL'] = 'false'
    
    def search_flights(self, origin: str, destination: str, departure_date: str, 
                      return_date: Optional[str] = None, passengers: int = 1) -> FlightSearchResults:
        """
        Search for flights using Nova Act browser automation
        
        Args:
            origin: Origin airport code or city (e.g., 'JFK' or 'New York')
            destination: Destination airport code or city (e.g., 'CDG' or 'Paris')
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date for round-trip (optional)
            passengers: Number of passengers (1-9)
            
        Returns:
            FlightSearchResults with structured flight data
        """
        
        print(f"🔍 Searching flights: {origin} → {destination} on {departure_date}")
        if self.use_agentcore_browser:
            print(f"   Using AgentCore Browser Tool (region: {self.region})")
        else:
            print(f"   Using local browser")
            
        if return_date:
            print(f"   Return: {return_date} | Passengers: {passengers}")
        
        # Call directly - no threading needed
        if self.use_agentcore_browser:
            return self._search_with_agentcore_browser(origin, destination, departure_date, return_date, passengers)
        else:
            return self._search_with_local_browser(origin, destination, departure_date, return_date, passengers)
    
    def _search_with_local_browser(self, origin: str, destination: str, departure_date: str,
                                 return_date: Optional[str] = None, passengers: int = 1) -> FlightSearchResults:
        """Search using local browser (original implementation)"""
        try:
            with NovaAct(
                starting_page="https://www.google.com/travel/flights",
                headless=False,
                user_agent="TravelAgent/1.0 (NovaAct)",
                nova_act_api_key=self.api_key,
                ignore_https_errors=True
            ) as nova:
                return self._execute_flight_search(nova, origin, destination, departure_date, return_date, passengers)
                    
        except Exception as nova_error:
            print(f"⚠️  Local Nova Act session error: {str(nova_error)}")
            return FlightSearchResults(
                outbound_flights=[],
                return_flights=[],
                search_metadata={"error": str(nova_error), "timestamp": datetime.now().isoformat()}
            )
    
    def _search_with_agentcore_browser(self, origin: str, destination: str, departure_date: str,
                                     return_date: Optional[str] = None, passengers: int = 1) -> FlightSearchResults:
        """Search using AgentCore Browser Tool"""
        try:
            from bedrock_agentcore.tools.browser_client import browser_session
            
            print("🌐 Creating AgentCore browser session...")
            with browser_session(self.region) as client:
                ws_url, headers = client.generate_ws_headers()
                print("✅ AgentCore browser session established")
                
                with NovaAct(
                    cdp_endpoint_url=ws_url,
                    cdp_headers=headers,
                    preview={"playwright_actuation": True},
                    nova_act_api_key=self.api_key,
                    ignore_https_errors=True,  # SSL fix for AgentCore
                    starting_page="https://www.google.com/travel/flights"
                ) as nova:
                    return self._execute_flight_search(nova, origin, destination, departure_date, return_date, passengers)
                    
        except ImportError:
            print("❌ bedrock_agentcore not installed. Run: pip install bedrock-agentcore")
            return FlightSearchResults(
                outbound_flights=[],
                return_flights=[],
                search_metadata={"error": "bedrock_agentcore not available", "timestamp": datetime.now().isoformat()}
            )
        except Exception as e:
            print(f"❌ AgentCore browser error: {str(e)}")
            return FlightSearchResults(
                outbound_flights=[],
                return_flights=[],
                search_metadata={"error": str(e), "timestamp": datetime.now().isoformat()}
            )
    
    def _execute_flight_search(self, nova, origin: str, destination: str, departure_date: str,
                             return_date: Optional[str] = None, passengers: int = 1) -> FlightSearchResults:
        """Common flight search logic used by both local and AgentCore browsers"""
        try:
            # Step 1: Set trip type
            if not return_date:
                nova.act("Click on the Round Trip field and change it to One way")
            
            # Step 2: Set origin airport  
            nova.act(f"Set the origin airport to be '{origin}'")
            
            # Step 3: Set destination airport
            nova.act(f"Set the destination to be '{destination}'")

            # Step 4: Set departure date
            nova.act(f"Click on the departure date field")
            nova.act(f"Navigate to the correct month and select {departure_date}")

            # Step 5: Set return date if round-trip
            if return_date:
                nova.act(f"Click on the return date field")
                nova.act(f"Navigate to the correct month and select {return_date}")
            
            # Step 6: Set number of passengers  
            if passengers > 1:
                nova.act(f"Click on the passengers dropdown")
                nova.act(f"Set the number of passengers to {passengers}")
            
            # Step 7: Execute search
            nova.act("Click the Search button to start the flight search")
            
            # Step 8: Wait for results page
            nova.act("Wait for the flight search results page to load completely")
            
            # Step 9: Extract flight information
            result = nova.act(
                f"""Look at the flight search results page and extract flight information from each flight card.
                
                For each visible flight option (up to 10), find and extract:
                
                1. AIRLINE: Look for the airline logo and name (e.g., 'Air France', 'Delta', 'United')
                2. DEPARTURE TIME: Find the departure time, usually on the left (e.g., '10:30 AM', '2:15 PM')  
                3. ARRIVAL TIME: Find the arrival time, usually on the right (e.g., '6:45 PM', '10:30 PM')
                4. PRICE: Look for the dollar amount price (e.g., $542, $798) - extract just the number
                5. DURATION: Find the total flight time (e.g., '7h 15m', '8h 45m')
                6. STOPS: Count the stops - look for 'nonstop' (0 stops), '1 stop', '2 stops', etc.
                7. STOP DETAILS: If there are stops, note the connecting airport (e.g., 'via LHR', 'via AMS')
                
                Return this data structured as:
                - airline: The airline name
                - departure_time: Departure time 
                - arrival_time: Arrival time
                - departure_airport: '{origin}'
                - arrival_airport: '{destination}' 
                - price: Price as number (without $ symbol)
                - duration: Flight duration string
                - stops: Number of stops as integer (0, 1, 2, etc.)
                - stop_details: Stop airport info or null if nonstop
                - booking_class: 'Economy'""",
                schema=FlightSearchResults.model_json_schema()
            )
            
            if result.matches_schema:
                flights_data = FlightSearchResults.model_validate(result.parsed_response)
                print(f"✅ Successfully extracted {len(flights_data.outbound_flights)} flight options")
                return flights_data
            else:
                print("⚠️  Schema validation failed, attempting manual parse...")
                return self._parse_manual_response(result.response)
        
        except Exception as search_error:
            print(f"❌ Flight search operation failed: {str(search_error)}")
            return FlightSearchResults(
                outbound_flights=[],
                return_flights=[],
                search_metadata={"error": str(search_error), "timestamp": datetime.now().isoformat()}
            )
    
    def _parse_manual_response(self, response: str) -> FlightSearchResults:
        """Fallback manual parsing if schema validation fails"""
        print(f"Raw response: {response}")
        
        return FlightSearchResults(
            outbound_flights=[],
            return_flights=[], 
            search_metadata={
                "error": "Schema validation failed",
                "raw_response": response[:500],  # First 500 chars for debugging
                "timestamp": datetime.now().isoformat()
            }
        )

def main():
    """Example usage of the flight searcher"""
    
    # Test local browser
    print("Testing with local browser:")
    searcher = FlightSearcher(use_agentcore_browser=False)
    results = searcher.search_flights(
        origin="JFK",
        destination="CDG", 
        departure_date="2024-06-15",
        passengers=2
    )
    print_results(results)
    
    # Test AgentCore browser
    print("\n" + "="*50)
    print("Testing with AgentCore browser:")
    agentcore_searcher = FlightSearcher(use_agentcore_browser=True, region="us-east-1")
    agentcore_results = agentcore_searcher.search_flights(
        origin="JFK",
        destination="LAX",
        departure_date="2024-06-15", 
        passengers=1
    )
    print_results(agentcore_results)

def print_results(results: FlightSearchResults):
    """Helper function to print flight results"""
    print("\n" + "="*50)
    print("FLIGHT SEARCH RESULTS")
    print("="*50)
    
    if results.outbound_flights:
        for i, flight in enumerate(results.outbound_flights[:5], 1):
            print(f"\n{i}. {flight.airline}")
            print(f"   {flight.departure_airport} {flight.departure_time} → {flight.arrival_airport} {flight.arrival_time}")
            print(f"   Duration: {flight.duration} | Stops: {flight.stops} | Price: ${flight.price}")
            if flight.stop_details:
                print(f"   Route: {flight.stop_details}")
    else:
        print("No flights found or search failed")
        if results.search_metadata.get('error'):
            print("Error:", results.search_metadata['error'])

if __name__ == "__main__":
    main()
