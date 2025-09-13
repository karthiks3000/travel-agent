"""
Test suite for flight search functionality
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from .models.flight_models import FlightResult, FlightSearchResults
from .flight_search import FlightSearcher


class TestFlightSearcher:
    """Test suite for FlightSearcher class"""
    
    @pytest.fixture
    def searcher(self):
        """Create a FlightSearcher instance for testing"""
        with patch.dict(os.environ, {'NOVA_ACT_API_KEY': 'test-api-key'}):
            return FlightSearcher()
    
    @pytest.fixture  
    def mock_nova_act_success(self):
        """Mock successful Nova Act response"""
        mock_result = MagicMock()
        mock_result.matches_schema = True
        mock_result.parsed_response = {
            "outbound_flights": [
                {
                    "airline": "Air France",
                    "departure_time": "10:30 AM",
                    "arrival_time": "6:45 PM",
                    "departure_airport": "JFK",
                    "arrival_airport": "CDG",
                    "price": 542.0,
                    "duration": "7h 15m",
                    "stops": 0,
                    "stop_details": None,
                    "booking_class": "Economy"
                },
                {
                    "airline": "Delta",
                    "departure_time": "2:15 PM", 
                    "arrival_time": "10:30 PM",
                    "departure_airport": "JFK",
                    "arrival_airport": "CDG",
                    "price": 598.0,
                    "duration": "8h 15m",
                    "stops": 1,
                    "stop_details": "via AMS",
                    "booking_class": "Economy"
                }
            ],
            "return_flights": [],
            "search_metadata": {"timestamp": "2024-01-15T10:30:00"}
        }
        return mock_result
    
    @pytest.fixture
    def mock_nova_act_failure(self):
        """Mock failed Nova Act response"""
        mock_result = MagicMock()
        mock_result.matches_schema = False
        mock_result.response = "Error: Could not find flight results on the page"
        return mock_result
    
    def test_searcher_initialization_success(self):
        """Test successful initialization with API key"""
        with patch.dict(os.environ, {'NOVA_ACT_API_KEY': 'test-api-key'}):
            searcher = FlightSearcher()
            assert searcher.api_key == 'test-api-key'
    
    def test_searcher_initialization_no_api_key(self):
        """Test initialization fails without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="NOVA_ACT_API_KEY environment variable is required"):
                FlightSearcher()
    
    @patch('flight_agent.flight_search.NovaAct')
    def test_successful_flight_search(self, mock_nova_act_class, searcher, mock_nova_act_success):
        """Test successful flight search with schema validation"""
        
        # Mock NovaAct context manager
        mock_nova = MagicMock()
        mock_nova.act.return_value = mock_nova_act_success
        mock_nova_act_class.return_value.__enter__.return_value = mock_nova
        mock_nova_act_class.return_value.__exit__.return_value = None
        
        # Execute search
        results = searcher.search_flights(
            origin="JFK",
            destination="CDG",
            departure_date="2024-06-15", 
            passengers=2
        )
        
        # Verify results
        assert isinstance(results, FlightSearchResults)
        assert len(results.outbound_flights) == 2
        
        # Check first flight details
        flight1 = results.outbound_flights[0]
        assert flight1.airline == "Air France"
        assert flight1.departure_airport == "JFK"
        assert flight1.arrival_airport == "CDG"
        assert flight1.price == 542.0
        assert flight1.stops == 0
        
        # Check second flight details
        flight2 = results.outbound_flights[1]
        assert flight2.airline == "Delta"
        assert flight2.stops == 1
        assert flight2.stop_details == "via AMS"
        
        # Verify Nova Act was called correctly
        mock_nova.act.assert_any_call("Set the origin airport to be 'JFK'")
        mock_nova.act.assert_any_call("set the destination to be 'CDG' ")
        mock_nova.act.assert_any_call("Navigate to the correct month and select 2024-06-15")
        mock_nova.act.assert_any_call("Set the number of passengers to 2")
    
    @patch('flight_agent.flight_search.NovaAct')
    def test_flight_search_schema_failure(self, mock_nova_act_class, searcher, mock_nova_act_failure):
        """Test flight search when schema validation fails"""
        
        # Mock NovaAct context manager
        mock_nova = MagicMock()
        mock_nova.act.return_value = mock_nova_act_failure
        mock_nova_act_class.return_value.__enter__.return_value = mock_nova
        mock_nova_act_class.return_value.__exit__.return_value = None
        
        # Execute search
        results = searcher.search_flights("JFK", "CDG", "2024-06-15")
        
        # Should return empty results with error metadata
        assert isinstance(results, FlightSearchResults)
        assert len(results.outbound_flights) == 0
        assert "error" in results.search_metadata
        assert "Schema validation failed" in results.search_metadata["error"]
    
    @patch('flight_agent.flight_search.NovaAct')
    def test_flight_search_exception_handling(self, mock_nova_act_class, searcher):
        """Test flight search exception handling"""
        
        # Mock NovaAct to raise exception
        mock_nova_act_class.side_effect = Exception("Network error")
        
        # Execute search
        results = searcher.search_flights("JFK", "CDG", "2024-06-15")
        
        # Should return empty results with error metadata
        assert isinstance(results, FlightSearchResults)
        assert len(results.outbound_flights) == 0
        assert "error" in results.search_metadata
        # The actual implementation returns "No data extracted" when Nova Act fails to initialize
        assert "No data extracted" in results.search_metadata["error"]
    
    def test_round_trip_search_params(self, searcher):
        """Test round-trip search parameter validation"""
        
        with patch('flight_agent.flight_search.NovaAct') as mock_nova_act_class:
            mock_nova = MagicMock()
            mock_result = MagicMock()
            mock_result.matches_schema = True
            mock_result.parsed_response = {
                "outbound_flights": [],
                "return_flights": [],
                "search_metadata": {}
            }
            mock_nova.act.return_value = mock_result
            mock_nova_act_class.return_value.__enter__.return_value = mock_nova
            mock_nova_act_class.return_value.__exit__.return_value = None
            
            # Test round-trip search
            searcher.search_flights(
                origin="JFK", 
                destination="CDG",
                departure_date="2024-06-15",
                return_date="2024-06-22",
                passengers=2
            )
            
            # Verify return date was set
            mock_nova.act.assert_any_call("Navigate to the correct month and select 2024-06-22")

class TestFlightModels:
    """Test suite for flight data models"""
    
    def test_flight_result_validation(self):
        """Test FlightResult model validation"""
        
        # Valid flight result
        flight_data = {
            "airline": "Air France",
            "departure_time": "10:30 AM",
            "arrival_time": "6:45 PM", 
            "departure_airport": "JFK",
            "arrival_airport": "CDG",
            "price": 542.0,
            "duration": "7h 15m",
            "stops": 0
        }
        
        flight = FlightResult(**flight_data)
        assert flight.airline == "Air France"
        assert flight.price == 542.0
        assert flight.stops == 0
    
    def test_flight_search_results_empty(self):
        """Test FlightSearchResults with empty data"""
        
        results = FlightSearchResults()
        assert len(results.outbound_flights) == 0
        assert len(results.return_flights) == 0
        assert isinstance(results.search_metadata, dict)
    
    def test_flight_search_results_with_data(self):
        """Test FlightSearchResults with flight data"""
        
        flight_data = {
            "airline": "Air France",
            "departure_time": "10:30 AM", 
            "arrival_time": "6:45 PM",
            "departure_airport": "JFK",
            "arrival_airport": "CDG", 
            "price": 542.0,
            "duration": "7h 15m",
            "stops": 0
        }
        
        results = FlightSearchResults(
            outbound_flights=[FlightResult(**flight_data)],
            search_metadata={"test": "data"}
        )
        
        assert len(results.outbound_flights) == 1
        assert results.outbound_flights[0].airline == "Air France"
        assert results.search_metadata["test"] == "data"

# Integration test (requires actual Nova Act API key)
class TestFlightSearchIntegration:
    """Integration tests that require actual Nova Act API key"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv('NOVA_ACT_API_KEY'), reason="Requires NOVA_ACT_API_KEY")
    def test_real_flight_search(self):
        """Test actual flight search (requires API key)"""
        
        searcher = FlightSearcher()
        
        # Search for a common route
        results = searcher.search_flights(
            origin="JFK",
            destination="LAX", 
            departure_date="2024-07-01"
        )
        
        # Basic validation - should find some flights
        assert isinstance(results, FlightSearchResults)
        # Note: Don't assert specific counts as flight availability changes
        print(f"Found {len(results.outbound_flights)} flights for JFK → LAX")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
