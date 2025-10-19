"""
Pydantic models for accommodation search data structures
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .base_models import ValidationError

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
    validation_error: Optional[ValidationError] = Field(None, description="Validation error details if applicable")
