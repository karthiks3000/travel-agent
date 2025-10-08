"""
Simple standalone test for Amadeus flight search integration
"""
import os
import sys
from datetime import datetime, timedelta

# Set up environment - load from .env file
from pathlib import Path
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Now import the function
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents/travel_orchestrator/tools'))
from flight_search_tool import search_flights_direct


def test_one_way_flight():
    """Test one-way flight search"""
    print("\n" + "="*60)
    print("TEST 1: One-way flight search (JFK → LAX)")
    print("="*60)
    
    # Get a date 30 days from now for testing
    future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    print(f"Searching for flights on: {future_date}")
    
    result = search_flights_direct(
        origin='JFK',
        destination='LAX',
        departure_date=future_date,
        return_date=None,
        passengers=1
    )
    
    print(f"\n✓ Result Status: {result.response_status}")
    print(f"✓ Success: {result.success}")
    print(f"✓ Message: {result.message[:200]}...")  # Truncate long messages
    
    if result.flight_results:
        print(f"\n✓ Found {len(result.flight_results)} flight(s):")
        for i, flight in enumerate(result.flight_results, 1):
            print(f"\n  Flight {i}:")
            print(f"    Airline: {flight.airline}")
            print(f"    Route: {flight.departure_airport} → {flight.arrival_airport}")
            print(f"    Departure: {flight.departure_time}")
            print(f"    Arrival: {flight.arrival_time}")
            print(f"    Duration: {flight.duration}")
            print(f"    Stops: {flight.stops}")
            if flight.stop_details:
                print(f"    Via: {flight.stop_details}")
            print(f"    Price: ${flight.price:.2f}")
            print(f"    Class: {flight.booking_class}")
    
    print(f"\n⏱  Processing time: {result.processing_time_seconds:.2f} seconds")
    return result.success


def test_round_trip_flight():
    """Test round-trip flight search"""
    print("\n" + "="*60)
    print("TEST 2: Round-trip flight search (BOS → MIA → BOS)")
    print("="*60)
    
    # Get dates 30 and 37 days from now for testing
    departure_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    return_date = (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d')
    print(f"Departure: {departure_date}, Return: {return_date}")
    
    result = search_flights_direct(
        origin='BOS',
        destination='MIA',
        departure_date=departure_date,
        return_date=return_date,
        passengers=1
    )
    
    print(f"\n✓ Result Status: {result.response_status}")
    print(f"✓ Success: {result.success}")
    print(f"✓ Message: {result.message[:200]}...")  # Truncate long messages
    
    if result.flight_results:
        print(f"\n✓ Found {len(result.flight_results)} flight(s):")
        for i, flight in enumerate(result.flight_results, 1):
            flight_type = "Outbound" if i == 1 else "Return"
            print(f"\n  {flight_type} Flight:")
            print(f"    Airline: {flight.airline}")
            print(f"    Route: {flight.departure_airport} → {flight.arrival_airport}")
            print(f"    Departure: {flight.departure_time}")
            print(f"    Arrival: {flight.arrival_time}")
            print(f"    Duration: {flight.duration}")
            print(f"    Stops: {flight.stops}")
            if flight.stop_details:
                print(f"    Via: {flight.stop_details}")
            print(f"    Price: ${flight.price:.2f}")
            print(f"    Class: {flight.booking_class}")
    
    print(f"\n⏱  Processing time: {result.processing_time_seconds:.2f} seconds")
    return result.success


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🛫 AMADEUS FLIGHT SEARCH INTEGRATION TESTS")
    print("="*60)
    
    # Check environment variables
    client_id = os.getenv('AMADEUS_CLIENT_ID')
    client_secret = os.getenv('AMADEUS_CLIENT_SECRET')
    hostname = os.getenv('AMADEUS_HOSTNAME', 'test')
    
    if not client_id:
        print("\n❌ ERROR: AMADEUS_CLIENT_ID not found in environment")
        print("Please set the environment variable and try again.")
        return False
    
    if not client_secret:
        print("\n❌ ERROR: AMADEUS_CLIENT_SECRET not found in environment")
        print("Please set the environment variable and try again.")
        return False
    
    print(f"\n✅ Amadeus credentials found")
    print(f"   Client ID: {client_id[:8]}..." if len(client_id) > 8 else client_id)
    print(f"   Environment: {hostname}")
    
    # Run tests
    try:
        test1_passed = test_one_way_flight()
    except Exception as e:
        print(f"\n❌ Test 1 failed with error: {e}")
        test1_passed = False
    
    try:
        test2_passed = test_round_trip_flight()
    except Exception as e:
        print(f"\n❌ Test 2 failed with error: {e}")
        test2_passed = False
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Test 1 (One-way JFK→LAX): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Round-trip BOS↔MIA): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Flight search integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")
    
    print("="*60 + "\n")
    
    return test1_passed and test2_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
