"""
Base Pydantic models for common data structures across all agents
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class SearchMetadata(BaseModel):
    """Common metadata for all search results"""
    search_timestamp: datetime = Field(default_factory=datetime.now)
    search_method: str = Field(..., description="API, browser_automation, etc.")
    source_platform: str = Field(..., description="google_flights, airbnb, booking_com, etc.")
    total_results_found: Optional[int] = None
    search_duration_seconds: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None

class PriceInfo(BaseModel):
    """Standardized price information"""
    amount: float = Field(..., description="Price amount")
    currency: str = Field(default="USD", description="Currency code")
    per_unit: Optional[str] = Field(None, description="per night, per person, etc.")
    
    def __str__(self) -> str:
        unit_str = f" {self.per_unit}" if self.per_unit else ""
        return f"{self.currency} {self.amount:.2f}{unit_str}"

class Location(BaseModel):
    """Standardized location information"""
    name: str = Field(..., description="Location name")
    city: Optional[str] = None
    country: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None  # {"lat": 48.8566, "lng": 2.3522}
    
    def __str__(self) -> str:
        if self.city and self.country:
            return f"{self.name}, {self.city}, {self.country}"
        elif self.city:
            return f"{self.name}, {self.city}"
        else:
            return self.name

class Rating(BaseModel):
    """Standardized rating information"""
    score: float = Field(..., ge=0, le=10, description="Rating score")
    max_score: float = Field(default=10, description="Maximum possible score")
    review_count: Optional[int] = Field(None, description="Number of reviews")
    source: Optional[str] = Field(None, description="Rating source")
    
    def __str__(self) -> str:
        reviews_str = f" ({self.review_count} reviews)" if self.review_count else ""
        return f"{self.score:.1f}/{self.max_score}{reviews_str}"

class TripType(str, Enum):
    ONE_WAY = "one-way"
    ROUND_TRIP = "round-trip"

class TravelPace(str, Enum):
    RELAXED = "relaxed"
    MODERATE = "moderate" 
    PACKED = "packed"

class BudgetCategory(str, Enum):
    BUDGET = "budget"
    MID_RANGE = "mid-range"
    LUXURY = "luxury"

class ValidationError(BaseModel):
    """Generic validation error model for all agents"""
    valid: bool = Field(default=False, description="Whether validation passed")
    error: Optional[str] = Field(None, description="Validation error message")
    field_errors: Optional[Dict[str, str]] = Field(None, description="Field-specific error messages")
    error_code: Optional[str] = Field(None, description="Error code for programmatic handling")
    
    def __str__(self) -> str:
        if self.error:
            return self.error
        elif self.field_errors:
            return f"Validation errors: {', '.join(f'{k}: {v}' for k, v in self.field_errors.items())}"
        else:
            return "Unknown validation error"

class AgentResponseBase(BaseModel):
    """Base class for all agent responses"""
    agent_name: str = Field(..., description="Name of the agent that generated this response")
    success: bool = Field(default=True, description="Whether the agent call was successful")
    error_message: Optional[str] = Field(None, description="Error message if agent call failed")
    processing_time_seconds: Optional[float] = Field(None, description="Time taken to process the request")
    timestamp: datetime = Field(default_factory=datetime.now)
    validation_error: Optional[ValidationError] = Field(None, description="Validation error details if applicable")
