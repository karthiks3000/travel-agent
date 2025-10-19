"""
Pydantic models for flight search data structures
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .base_models import ValidationError

class FlightResult(BaseModel):
    """Individual flight result from Google Flights"""
    airline: str = Field(..., description="Airline name (e.g., 'Air France')")
    departure_time: str = Field(..., description="Departure time in format like '10:30 AM'")
    arrival_time: str = Field(..., description="Arrival time in format like '6:45 PM'")
    departure_airport: str = Field(..., description="Departure airport code (e.g., 'JFK')")
    arrival_airport: str = Field(..., description="Arrival airport code (e.g., 'CDG')")
    price: float = Field(..., description="Flight price in USD")
    duration: str = Field(..., description="Flight duration (e.g., '7h 15m')")
    stops: int = Field(default=0, description="Number of stops (0 for non-stop)")
    stop_details: Optional[str] = Field(None, description="Stop airport details if applicable")
    booking_class: str = Field(default="Economy", description="Booking class")
    
