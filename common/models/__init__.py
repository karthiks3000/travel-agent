"""
Common models for travel agents - Centralized model definitions
"""

# Base models
from .base_models import (
    SearchMetadata, 
    PriceInfo, 
    Location, 
    Rating, 
    TripType, 
    TravelPace, 
    BudgetCategory,
    AgentResponseBase
)

# Travel orchestrator models
from .travel_models import (
    TravelInformation,
    ValidationResult,
    AgentSearchResult,
    ComprehensiveTravelPlan,
    ConversationContext
)

# Specialist agent response models
from .flight_models import (
    FlightResult,
    FlightSearchResults
)

from .accommodation_models import (
    PropertyResult,
    PlatformSearchResults,
    AccommodationAgentResponse
)

from .food_models import (
    RestaurantResult,
    RestaurantSearchResults,
    RestaurantSearchParams
)

# Orchestrator unified response models
from .orchestrator_models import (
    ResponseType,
    TravelOrchestratorResponse,
    AgentResponseParser
)

__all__ = [
    # Base models
    'SearchMetadata',
    'PriceInfo', 
    'Location',
    'Rating',
    'TripType',
    'TravelPace', 
    'BudgetCategory',
    'AgentResponseBase',
    
    # Travel models
    'TravelInformation',
    'ValidationResult',
    'AgentSearchResult', 
    'ComprehensiveTravelPlan',
    'ConversationContext',
    
    # Flight models
    'FlightResult',
    'FlightSearchResults',
    
    # Accommodation models
    'PropertyResult',
    'PlatformSearchResults',
    'AccommodationAgentResponse',
    
    # Food models
    'RestaurantResult',
    'RestaurantSearchResults',
    'RestaurantSearchParams',
    
    # Orchestrator models
    'ResponseType',
    'TravelOrchestratorResponse',
    'AgentResponseParser'
]
