"""
Flight Agent - Nova Act Implementation

A simple flight search agent using Nova Act browser automation to search Google Flights.
"""

__version__ = "0.1.0"
__author__ = "Travel Agent Team"

from .flight_search import FlightSearcher
from .models.flight_models import FlightResult, FlightSearchResults, FlightSearchParams

__all__ = [
    "FlightSearcher",
    "FlightResult", 
    "FlightSearchResults",
    "FlightSearchParams"
]
