"""
Pydantic models for restaurant search data structures
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .base_models import ValidationError

class RestaurantResult(BaseModel):
    """Individual restaurant result from Google Places API"""
    name: str = Field(..., description="Restaurant display name")
    address: str = Field(..., description="Formatted address of the restaurant")
    rating: Optional[float] = Field(None, description="Average user rating (0.0 to 5.0)")
    user_rating_count: Optional[int] = Field(None, description="Number of user ratings")
    price_level: Optional[str] = Field(None, description="Price level (PRICE_LEVEL_INEXPENSIVE, PRICE_LEVEL_MODERATE, etc.)")
    phone_number: Optional[str] = Field(None, description="National phone number")
    website_uri: Optional[str] = Field(None, description="Restaurant website URL")
    is_open_now: Optional[bool] = Field(None, description="Whether the restaurant is currently open")
    types: List[str] = Field(default_factory=list, description="List of place types (e.g., 'restaurant', 'italian_restaurant')")
    place_id: Optional[str] = Field(None, description="Google Places ID for the restaurant")
    
class RestaurantSearchResults(BaseModel):
    """Complete restaurant search results"""
    restaurants: List[RestaurantResult] = Field(default_factory=list, description="List of restaurant search results")
    total_results: int = Field(default=0, description="Total number of restaurants found")
    search_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional search metadata")
    next_page_token: Optional[str] = Field(None, description="Token for next page of results")
    recommendation: str = Field(..., description="Agent's personalized recommendation and advice about the restaurant results")
    validation_error: Optional[ValidationError] = Field(None, description="Validation error details if applicable")

class RestaurantSearchParams(BaseModel):
    """Parameters for restaurant search"""
    text_query: str = Field(..., description="Natural language search query for restaurants")
    location_bias: Optional[Dict[str, Any]] = Field(None, description="Location bias for search results")
    location_restriction: Optional[Dict[str, Any]] = Field(None, description="Location restriction for search results")
    price_levels: Optional[List[str]] = Field(None, description="Price level filters")
    min_rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Minimum rating filter")
    open_now: Optional[bool] = Field(None, description="Filter for currently open restaurants")
    included_type: Optional[str] = Field(None, description="Specific restaurant type filter")
    page_size: Optional[int] = Field(None, ge=1, le=20, description="Number of results per page")
    page_token: Optional[str] = Field(None, description="Page token for pagination")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text_query": "Italian restaurants in Rome",
                "price_levels": ["PRICE_LEVEL_INEXPENSIVE", "PRICE_LEVEL_MODERATE"],
                "min_rating": 4.0,
                "open_now": True,
                "page_size": 10
            }
        }
