#!/usr/bin/env python3
"""
Demo script for Flight Agent - Nova Act Implementation with AgentCore Browser Tool support

Run this script to test both local browser and AgentCore browser functionality.
Make sure to set NOVA_ACT_API_KEY environment variable first.
"""

import os
import sys
from flight_search import FlightSearcher
from models.flight_models import FlightSearchResults

def demo_flight_search():
    """Demonstrate flight search functionality with both browser types"""
    
    print("🛫 Flight Agent Demo - Local Browser + AgentCore Browser")
    print("=" * 60)
    
    # Check for API key
    if not os.getenv('NOVA_ACT_API_KEY'):
        print("❌ Error: NOVA_ACT_API_KEY environment variable not set")
        print("\n📝 To get an API key:")
        print("   1. Visit: https://nova.amazon.com/act")
        print("   2. Generate your API key")  
        print("   3. Set environment variable: export NOVA_ACT_API_KEY='your_key'")
        print("   4. Run this demo again")
        return
    
    # Demo configurations - test both browser types
    demo_configs = [
        {
            "name": "Local Browser Demo",
            "use_agentcore": False,
            "region": None,
            "search": {
                "origin": "JFK",
                "destination": "CDG", 
                "departure_date": "2025-10-01",
                "passengers": 1
            }
        },
        # {
        #     "name": "AgentCore Browser Demo", 
        #     "use_agentcore": True,
        #     "region": "us-east-1",
        #     "search": {
        #         "origin": "JFK",
        #         "destination": "LAX",
        #         "departure_date": "2025-10-15",
        #         "passengers": 2
        #     }
        # }
    ]
    
    for i, config in enumerate(demo_configs, 1):
        print(f"\n🔍 Demo {i}: {config['name']}")
        print("-" * 50)
        
        try:
            # Create flight searcher with appropriate configuration
            if config['use_agentcore']:
                searcher = FlightSearcher(use_agentcore_browser=True, region=config['region'])
                print(f"✅ AgentCore Browser initialized (region: {config['region']})")
            else:
                searcher = FlightSearcher(use_agentcore_browser=False)
                print("✅ Local Browser initialized")
            
            search_params = config['search']
            
            # Execute flight search
            results = searcher.search_flights(
                origin=search_params['origin'],
                destination=search_params['destination'],
                departure_date=search_params['departure_date'],
                return_date=search_params.get('return_date'),
                passengers=search_params['passengers']
            )
            
            # Display results
            print_flight_results(results)
                
        except Exception as e:
            print(f"❌ Demo {i} failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✨ Demo completed!")
    print("\n📚 Next steps:")
    print("   - Both browser types are now available")
    print("   - Local browser: FlightSearcher(use_agentcore_browser=False)")
    print("   - AgentCore browser: FlightSearcher(use_agentcore_browser=True)")
    print("   - Run tests: pytest . -v")
    print("   - Ready for Strands Agent integration")

def print_flight_results(results: FlightSearchResults):
    """Helper function to display flight search results"""
    
    if results.outbound_flights:
        print(f"✅ Found {len(results.outbound_flights)} flight options:")
        
        for j, flight in enumerate(results.outbound_flights[:5], 1):
            print(f"\n   {j}. {flight.airline}")
            print(f"      {flight.departure_airport} {flight.departure_time} → {flight.arrival_airport} {flight.arrival_time}")
            print(f"      Duration: {flight.duration} | Stops: {flight.stops} | Price: ${flight.price:.2f}")
            
            if flight.stop_details:
                print(f"      Route: {flight.stop_details}")
        
        if len(results.outbound_flights) > 5:
            print(f"   ... and {len(results.outbound_flights) - 5} more options")
            
    else:
        print("❌ No flights found")
        if results.search_metadata.get('error'):
            print(f"   Error: {results.search_metadata['error']}")

if __name__ == "__main__":
    demo_flight_search()
