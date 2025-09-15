"""
Pydantic models for accommodation search data structures
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PropertyResult(BaseModel):
    """Individual property result from accommodation platforms"""
    platform: str = Field(..., description="Platform name ('airbnb' or 'booking_com')")
    title: Optional[str] = Field(None, description="Property title/name")
    price_per_night: Optional[float] = Field(None, description="Price per night in USD")
    total_price: Optional[float] = Field(None, description="Total price for the stay")
    rating: Optional[float] = Field(None, description="Property rating (e.g., 4.8)")
    review_count: Optional[int] = Field(None, description="Number of reviews")
    property_type: Optional[str] = Field(None, description="Type of property (e.g., 'Entire apartment', 'Hotel room')")
    host_name: Optional[str] = Field(None, description="Host or hotel name")
    amenities: Optional[List[str]] = Field(None, description="List of amenities (can be null if not available)")
    location: Optional[str] = Field(None, description="Property location/address")
    url: Optional[str] = Field(None, description="Link to property listing")
    image_url: Optional[str] = Field(None, description="Main property image URL")
    guests_capacity: Optional[int] = Field(None, description="Maximum number of guests")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bathrooms: Optional[int] = Field(None, description="Number of bathrooms")
    
class AccommodationSearchResults(BaseModel):
    """Complete accommodation search results from multiple platforms"""
    airbnb_properties: List[PropertyResult] = Field(default_factory=list, description="Airbnb search results")
    booking_properties: List[PropertyResult] = Field(default_factory=list, description="Booking.com search results")
    combined_results: List[PropertyResult] = Field(default_factory=list, description="Combined and sorted results from all platforms")
    search_metadata: dict = Field(default_factory=dict, description="Search metadata and parameters")

class AccommodationSearchParams(BaseModel):
    """Parameters for accommodation search"""
    location: str = Field(..., description="Destination city or location")
    check_in: str = Field(..., description="Check-in date in YYYY-MM-DD format")
    check_out: str = Field(..., description="Check-out date in YYYY-MM-DD format")
    guests: int = Field(default=1, ge=1, le=16, description="Number of guests")
    rooms: int = Field(default=1, ge=1, le=8, description="Number of rooms (for hotels)")
    min_price: Optional[float] = Field(None, description="Minimum price per night")
    max_price: Optional[float] = Field(None, description="Maximum price per night")
    property_types: List[str] = Field(default_factory=list, description="Preferred property types")
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": "Paris, France",
                "check_in": "2024-06-15",
                "check_out": "2024-06-18",
                "guests": 2,
                "rooms": 1,
                "max_price": 200.0,
                "property_types": ["entire_place", "private_room"]
            }
        }

class PlatformSearchResults(BaseModel):
    """Results from a single platform search"""
    platform: str = Field(..., description="Platform name")
    properties: List[PropertyResult] = Field(default_factory=list, description="Property listings")
    search_successful: bool = Field(default=True, description="Whether search completed successfully")
    error_message: Optional[str] = Field(None, description="Error message if search failed")
    total_found: Optional[int] = Field(None, description="Total properties found (if available)")
    search_metadata: dict = Field(default_factory=dict, description="Platform-specific metadata")

class AccommodationAgentResponse(BaseModel):
    """Unified accommodation agent response - matches flight agent pattern"""
    best_accommodations: List[PropertyResult] = Field(default_factory=list, description="Top 5-10 best accommodation options selected by agent based on price, rating, and user preferences")
    search_metadata: dict = Field(default_factory=dict, description="Search parameters and metadata including any errors")
    recommendation: str = Field(..., description="Agent's personalized accommodation recommendations and booking advice")
