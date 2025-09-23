"""
Flight Agent - Nova Act Implementation

A simple flight search agent using Nova Act browser automation to search Google Flights.
"""

__version__ = "0.1.0"
__author__ = "Travel Agent Team"

from common.models.flight_models import FlightResult, FlightSearchResults
from .flight_agent import FlightAgent
__all__ = [
    "FlightAgent",
    "FlightResult", 
    "FlightSearchResults"
]
