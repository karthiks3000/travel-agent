"""
Enhanced itinerary models for comprehensive travel planning
"""
from pydantic import BaseModel, Field, computed_field
from typing import Union, List, Optional
from datetime import date as date_type, datetime
from enum import Enum

# Import existing models
from .flight_models import FlightResult
from .accommodation_models import PropertyResult
from .food_models import RestaurantResult

class ActivityType(str, Enum):
    FLIGHT = "flight"
    ACCOMMODATION = "accommodation"  # check-in/check-out
    RESTAURANT = "restaurant"
    ATTRACTION = "attraction"
    TRANSPORTATION = "transportation"  # train, bus, taxi, uber
    GENERAL = "general"  # shopping, walking, free time

class TimeSlot(BaseModel):
    start_time: str = Field(
        ..., 
        description="Activity start time in 12-hour format with AM/PM (e.g., '9:00 AM', '2:30 PM', '11:45 PM')"
    )
    end_time: Optional[str] = Field(
        None, 
        description="Activity end time in 12-hour format with AM/PM (optional)"
    )
    duration_minutes: Optional[int] = Field(None, description="Estimated duration in minutes")

class AttractionResult(BaseModel):
    """Google Places attraction result"""
    name: str = Field(..., description="Attraction name")
    place_id: str = Field(..., description="Google Places ID")
    formatted_address: str = Field(..., description="Address")
    rating: Optional[float] = Field(None, description="Rating 1-5")
    user_ratings_total: Optional[int] = Field(None, description="Number of reviews")
    price_level: Optional[int] = Field(None, description="Price level 0-4")
    types: List[str] = Field(default_factory=list, description="Place types")
    opening_hours: Optional[dict] = Field(None, description="Operating hours")
    website: Optional[str] = Field(None, description="Official website")
    phone_number: Optional[str] = Field(None, description="Phone number")
    photos: Optional[List[dict]] = Field(None, description="Photo references")
    geometry: Optional[dict] = Field(None, description="Location coordinates")
    visit_duration_estimate: Optional[int] = Field(None, description="Suggested visit time in minutes")

class TransportationActivity(BaseModel):
    """For trains, buses, taxis, walking directions, etc."""
    mode: str = Field(..., description="train, bus, taxi, uber, walking, metro")
    from_location: str = Field(..., description="Starting location")
    to_location: str = Field(..., description="Destination location")
    provider: Optional[str] = Field(None, description="Company name if applicable")
    cost_estimate: Optional[float] = Field(None, description="Estimated cost in USD")
    notes: Optional[str] = Field(None, description="Additional travel notes")

class GeneralActivity(BaseModel):
    """For shopping, free time, walking tours, etc."""
    title: str = Field(..., description="Activity title")
    description: Optional[str] = Field(None, description="Activity description")
    location: Optional[str] = Field(None, description="Location if applicable")
    cost_estimate: Optional[float] = Field(None, description="Estimated cost in USD")
    notes: Optional[str] = Field(None, description="Additional notes")

class ItineraryActivity(BaseModel):
    """Single activity in a daily itinerary"""
    time_slot: TimeSlot = Field(..., description="When this activity occurs")
    activity_type: ActivityType = Field(..., description="Type of activity")
    title: str = Field(..., description="Activity title/name")
    
    # Union of all possible activity details
    activity_details: Union[
        FlightResult,
        PropertyResult, 
        RestaurantResult,
        AttractionResult,
        TransportationActivity,
        GeneralActivity
    ] = Field(..., description="Specific activity details")
    
    notes: Optional[str] = Field(None, description="Travel planner notes and recommendations")
    
    @computed_field
    @property
    def estimated_cost(self) -> Optional[float]:
        """Extract cost from activity details regardless of type"""
        details = self.activity_details
        
        # Check different price fields based on activity type
        if hasattr(details, 'price') and details.price is not None:
            return details.price  # FlightResult
        if hasattr(details, 'total_price') and details.total_price is not None:
            return details.total_price  # PropertyResult
        if hasattr(details, 'cost_estimate') and details.cost_estimate is not None:
            return details.cost_estimate  # TransportationActivity, GeneralActivity
        
        return None

class DailyItinerary(BaseModel):
    """Single day in travel itinerary"""
    day_number: int = Field(..., description="Day number in trip (1, 2, 3...)")
    date: date_type = Field(..., description="Date for this day")
    location: str = Field(..., description="Primary location/city for this day")
    daily_summary: str = Field(..., description="Brief summary of the day's activities")
    
    activities: List[ItineraryActivity] = Field(
        default_factory=list, 
        description="Chronological list of activities for the day"
    )
    
    estimated_daily_cost: Optional[float] = Field(None, description="Estimated total cost for the day")
    weather_info: Optional[str] = Field(None, description="Weather forecast if available")

class TravelItinerary(BaseModel):
    """Complete travel itinerary"""
    trip_title: str = Field(..., description="Trip title/name")
    destination: str = Field(..., description="Primary destination")
    start_date: date_type = Field(..., description="Trip start date")  
    end_date: date_type = Field(..., description="Trip end date")
    total_days: int = Field(..., description="Total number of days")
    traveler_count: int = Field(..., description="Number of travelers")
    
    daily_itineraries: List[DailyItinerary] = Field(
        default_factory=list,
        description="Day-by-day itinerary"
    )
    
    # Trip-level metadata
    total_estimated_cost: Optional[float] = Field(None, description="Total estimated trip cost")
    trip_summary: str = Field(..., description="Overall trip description")
    packing_suggestions: Optional[List[str]] = Field(None, description="Packing recommendations")
    travel_tips: Optional[List[str]] = Field(None, description="General travel advice")
    
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def get_trip_duration_days(self) -> int:
        """Calculate trip duration in days"""
        return (self.end_date - self.start_date).days + 1
    
    def get_total_estimated_cost(self) -> Optional[float]:
        """Calculate total estimated cost from daily costs"""
        daily_costs = [day.estimated_daily_cost for day in self.daily_itineraries if day.estimated_daily_cost]
        if daily_costs:
            return sum(daily_costs)
        return self.total_estimated_cost
    
    def get_activity_count_by_type(self) -> dict:
        """Get count of activities by type across all days"""
        counts = {}
        for day in self.daily_itineraries:
            for activity in day.activities:
                activity_type = activity.activity_type.value
                counts[activity_type] = counts.get(activity_type, 0) + 1
        return counts
