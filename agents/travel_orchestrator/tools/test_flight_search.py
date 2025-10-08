"""
Test script for Amadeus flight search integration
"""
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from agents.travel_orchestrator.tools.flight_search_tool import search_flights_direct


def test_one_way_flight():
    """Test one-way flight search"""
    print("\n" + "="*60)
    print("TEST 1: One-way flight search (JFK → LAX)")
    print("="*60)
    
    # Get a date 30 days from now for testing
    future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    result = search_flights_direct(
        origin='JFK',
        destination='LAX',
        departure_date=future_date,
        return_date=None,
        passengers=1
    )
    
    print(f"\nResult Status: {result.response_status}")
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    
    if result.flight_results:
        print(f"\nFound {len(result.flight_results)} flight(s):")
        for i, flight in enumerate(result.flight_results, 1):
            print(f"\n  Flight {i}:")
            print(f"    Airline: {flight.airline}")
            print(f"    Departure: {flight.departure_time} from {flight.departure_airport}")
            print(f"    Arrival: {flight.arrival_time} at {flight.arrival_airport}")
            print(f"    Duration: {flight.duration}")
            print(f"    Stops: {flight.stops}")
            print(f"    Price: ${flight.price}")
    
    print(f"\nProcessing time: {result.processing_time_seconds:.2f} seconds")
    return result.success


def test_round_trip_flight():
    """Test round-trip flight search"""
    print("\n" + "="*60)
    print("TEST 2: Round-trip flight search (JFK → LAX → JFK)")
    print("="*60)
    
    # Get dates 30 and 37 days from now for testing
    departure_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    return_date = (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d')
    
    result = search_flights_direct(
        origin='JFK',
        destination='LAX',
        departure_date=departure_date,
        return_date=return_date,
        passengers=1
    )
    
    print(f"\nResult Status: {result.response_status}")
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    
    if result.flight_results:
        print(f"\nFound {len(result.flight_results)} flight(s):")
        for i, flight in enumerate(result.flight_results, 1):
            flight_type = "Outbound" if i == 1 else "Return"
            print(f"\n  {flight_type} Flight:")
            print(f"    Airline: {flight.airline}")
            print(f"    Departure: {flight.departure_time} from {flight.departure_airport}")
            print(f"    Arrival: {flight.arrival_time} at {flight.arrival_airport}")
            print(f"    Duration: {flight.duration}")
            print(f"    Stops: {flight.stops}")
            print(f"    Price: ${flight.price}")
    
    print(f"\nProcessing time: {result.processing_time_seconds:.2f} seconds")
    return result.success


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AMADEUS FLIGHT SEARCH INTEGRATION TESTS")
    print("="*60)
    
    # Check environment variables
    if not os.getenv('AMADEUS_CLIENT_ID'):
        print("\n❌ ERROR: AMADEUS_CLIENT_ID not found in environment")
        print("Please set the environment variable and try again.")
        return False
    
    if not os.getenv('AMADEUS_CLIENT_SECRET'):
        print("\n❌ ERROR: AMADEUS_CLIENT_SECRET not found in environment")
        print("Please set the environment variable and try again.")
        return False
    
    print(f"\n✅ Amadeus credentials found")
    print(f"   Hostname: {os.getenv('AMADEUS_HOSTNAME', 'test')}")
    
    # Run tests
    test1_passed = test_one_way_flight()
    test2_passed = test_round_trip_flight()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Test 1 (One-way): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Round-trip): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("="*60 + "\n")
    
    return test1_passed and test2_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
