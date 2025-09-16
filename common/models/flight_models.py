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
    
class FlightSearchResults(BaseModel):
    """Complete flight search results with best flight selections"""
    best_outbound_flight: Optional[FlightResult] = Field(None, description="Best selected outbound flight based on cost and convenience")
    best_return_flight: Optional[FlightResult] = Field(None, description="Best selected return flight (if round-trip)")
    search_metadata: dict = Field(default_factory=dict, description="Additional search metadata")
    recommendation: str = Field(..., description="Agent's personalized flight recommendations and booking advice")
    validation_error: Optional[ValidationError] = Field(None, description="Validation error details if applicable")

class FlightSearchParams(BaseModel):
    """Parameters for flight search"""
    origin: str = Field(..., description="Origin airport code or city")
    destination: str = Field(..., description="Destination airport code or city") 
    departure_date: str = Field(..., description="Departure date in YYYY-MM-DD format")
    return_date: Optional[str] = Field(None, description="Return date in YYYY-MM-DD format for round-trip")
    passengers: int = Field(default=1, ge=1, le=9, description="Number of passengers")
    cabin_class: str = Field(default="Economy", description="Cabin class preference")
    
    class Config:
        json_schema_extra = {
            "example": {
                "origin": "JFK",
                "destination": "CDG", 
                "departure_date": "2024-06-15",
                "return_date": "2024-06-22",
                "passengers": 2,
                "cabin_class": "Economy"
            }
        }
