"""
Unified response models for Travel Orchestrator Agent
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Literal
from enum import Enum
from datetime import datetime

# Import specialist agent response models using relative imports within common
from .flight_models import FlightResult
from .accommodation_models import AccommodationAgentResponse, PropertyResult
from .food_models import RestaurantSearchResults, RestaurantResult
from .travel_models import ComprehensiveTravelPlan
from .itinerary_models import TravelItinerary, AttractionResult


class ResponseType(str, Enum):
    """Types of responses the orchestrator can provide"""
    CONVERSATION = "conversation"      # Simple Q&A, validation errors, clarifications
    FLIGHTS = "flights"               # Flight search results only
    ACCOMMODATIONS = "accommodations" # Accommodation search results only
    RESTAURANTS = "restaurants"       # Restaurant search results only
    ATTRACTIONS = "attractions"       # Attraction search results only
    MIXED_RESULTS = "mixed_results"   # Multiple component types (flights + hotels, etc.)
    ITINERARY = "itinerary"          # Complete travel plan with multiple components


class ResponseStatus(str, Enum):
    """Status indicators for the orchestrator agent's current state"""
    # Information gathering
    REQUESTING_INFO = "requesting_info"           # Agent needs more details
    VALIDATING = "validating"                     # Checking provided info
    
    # Processing states  
    THINKING = "thinking"                         # Agent is analyzing
    CALLING_TOOLS = "calling_tools"               # Executing specialist agents
    TOOL_IN_PROGRESS = "tool_in_progress"         # Individual tool running
    PROCESSING_RESULTS = "processing_results"     # Combining results
    
    # Completion states
    PARTIAL_RESULTS = "partial_results"           # Some tools succeeded
    COMPLETE_SUCCESS = "complete_success"         # All requested data found
    COMPLETE_WITH_RECOMMENDATIONS = "complete_with_recommendations" # Results + suggestions
    
    # Error states
    TOOL_ERROR = "tool_error"                     # Specialist agent failed
    VALIDATION_ERROR = "validation_error"         # Invalid input provided
    SYSTEM_ERROR = "system_error"                 # General system failure


class ToolProgress(BaseModel):
    """Progress tracking for individual tools"""
    tool_id: str = Field(..., description="Internal tool identifier")
    display_name: str = Field(..., description="User-friendly tool name")
    description: str = Field(..., description="Detailed description of what the tool is doing")
    status: Literal["pending", "active", "completed", "failed"] = Field(..., description="Current tool status")
    result_preview: Optional[str] = Field(None, description="Brief preview of results if completed")
    error_message: Optional[str] = Field(None, description="Error details if status is failed")


class TravelOrchestratorResponse(BaseModel):
    """
    Unified response model for Travel Orchestrator Agent
    
    This single model handles all response scenarios, providing a consistent
    JSON structure for frontend applications while leveraging structured data
    from specialist agents.
    """
    
    # Core response metadata
    response_type: ResponseType = Field(..., description="Type of response for frontend rendering logic")
    message: str = Field(..., description="Human-readable message explaining the response")
    success: bool = Field(default=True, description="Whether the operation was successful")
    error_message: Optional[str] = Field(None, description="Error details if success=False")
    
    # NEW STATUS FIELDS
    response_status: ResponseStatus = Field(
        ResponseStatus.COMPLETE_SUCCESS, 
        description="Current agent status for frontend handling"
    )
    is_final_response: bool = Field(
        default=False, 
        description="Whether this completes the user's request"
    )
    next_expected_input_friendly: Optional[str] = Field(
        None, 
        description="User-friendly description of what agent needs from user next"
    )
    overall_progress_message: str = Field(
        ..., 
        description="Overall status message for user display"
    )
    
    # PROGRESS TRACKING
    tool_progress: List[ToolProgress] = Field(
        default_factory=list,
        description="Progress tracking for all tools being executed"
    )
    
    # Enhanced structured data - supports multiple results and new components
    flight_results: Optional[List[FlightResult]] = Field(
        None, 
        description="Flight search results (1-10 options based on user request)"
    )
    accommodation_results: Optional[List[PropertyResult]] = Field(
        None, 
        description="Accommodation search results (1-10 options based on user request)"
    )
    restaurant_results: Optional[List[RestaurantResult]] = Field(
        None, 
        description="Restaurant search results from Google Places API"
    )
    attraction_results: Optional[List[AttractionResult]] = Field(
        None, 
        description="Attraction search results from Google Places API"
    )
    
    # Complete travel planning
    itinerary: Optional[TravelItinerary] = Field(
        None, 
        description="Complete day-by-day travel itinerary when response_type is 'itinerary'"
    )
    
    # Additional response metadata
    processing_time_seconds: Optional[float] = Field(
        None, 
        description="Time taken to process the request"
    )
    estimated_costs: Optional[Dict[str, float]] = Field(
        None, 
        description="Estimated costs breakdown (flights, accommodations, etc.)"
    )
    recommendations: Optional[Dict[str, Any]] = Field(
        None, 
        description="AI-generated recommendations and advice"
    )
    session_metadata: Optional[Dict[str, str]] = Field(
        None, 
        description="Session information for context tracking"
    )
    
    def get_response_summary(self) -> str:
        """Get a brief summary of the response for logging"""
        components = []
        
        if self.flight_results:
            components.append(f"{len(self.flight_results)} flights")
        
        if self.accommodation_results:
            components.append(f"{len(self.accommodation_results)} accommodations")
        
        if self.restaurant_results:
            components.append(f"{len(self.restaurant_results)} restaurants")
        
        if self.attraction_results:
            components.append(f"{len(self.attraction_results)} attractions")
        
        if self.itinerary:
            components.append("complete itinerary")
        
        component_str = ", ".join(components) if components else "conversation only"
        return f"{self.response_type.value} response with {component_str} (status: {self.response_status.value})"
    
    def get_total_estimated_cost(self) -> Optional[float]:
        """Calculate total estimated cost across all components"""
        if not self.estimated_costs:
            return None
        
        return sum(self.estimated_costs.values())
    
    def has_results(self) -> bool:
        """Check if response contains any structured results"""
        return any([
            self.flight_results is not None,
            self.accommodation_results is not None,
            self.restaurant_results is not None,
            self.itinerary is not None
        ])
    
    def get_completed_tools_count(self) -> int:
        """Get count of completed tools"""
        return len([tool for tool in self.tool_progress if tool.status == "completed"])
    
    def get_failed_tools_count(self) -> int:
        """Get count of failed tools"""
        return len([tool for tool in self.tool_progress if tool.status == "failed"])
    
    def has_active_tools(self) -> bool:
        """Check if any tools are currently active"""
        return any(tool.status == "active" for tool in self.tool_progress)


# Tool display mapping for user-friendly progress
TOOL_DISPLAY_MAPPING = {
    "validate_travel_information": {
        "display_name": "Validating details",
        "description_template": "Checking your travel information"
    },
    "search_flights": {
        "display_name": "Finding flights", 
        "description_template": "Searching for flights from {origin} to {destination}"
    },
    "search_accommodations": {
        "display_name": "Finding accommodations",
        "description_template": "Looking for places to stay in {destination}"
    },
    "search_restaurants": {
        "display_name": "Finding restaurants",
        "description_template": "Searching for {dietary_preferences} restaurants in {destination}"
    },
    "plan_comprehensive_trip": {
        "display_name": "Creating itinerary",
        "description_template": "Combining all results into your travel plan"
    }
}


class AgentResponseParser:
    """Helper class to parse specialist agent responses into proper Pydantic models"""
    
    
    @staticmethod
    def parse_accommodation_response(raw_response: Dict[str, Any]) -> Optional[AccommodationAgentResponse]:
        """Parse accommodation agent response into AccommodationAgentResponse model"""
        try:
            if isinstance(raw_response, dict):
                # Check if it's already structured accommodation data
                if 'best_accommodations' in raw_response or 'recommendation' in raw_response:
                    return AccommodationAgentResponse.model_validate(raw_response)
                
                # Handle text responses
                if 'response_text' in raw_response:
                    return None
            
            return None
            
        except Exception as e:
            print(f"⚠️  Failed to parse accommodation response: {e}")
            return None
    
    @staticmethod
    def parse_restaurant_response(raw_response: Dict[str, Any]) -> Optional[RestaurantSearchResults]:
        """Parse food agent response into RestaurantSearchResults model"""
        try:
            if isinstance(raw_response, dict):
                # Check if it's already structured restaurant data
                if 'restaurants' in raw_response or 'recommendation' in raw_response:
                    return RestaurantSearchResults.model_validate(raw_response)
                
                # Handle text responses
                if 'response_text' in raw_response:
                    return None
            
            return None
            
        except Exception as e:
            print(f"⚠️  Failed to parse restaurant response: {e}")
            return None


def create_tool_progress(tool_id: str, travel_info: Optional[Dict[str, Any]] = None, status: Literal["pending", "active", "completed", "failed"] = "pending") -> ToolProgress:
    """Helper function to create user-friendly tool progress objects"""
    if tool_id not in TOOL_DISPLAY_MAPPING:
        return ToolProgress(
            tool_id=tool_id,
            display_name=tool_id.replace("_", " ").title(),
            description=f"Executing {tool_id}",
            status=status,
            result_preview=None,
            error_message=None
        )
    
    mapping = TOOL_DISPLAY_MAPPING[tool_id]
    
    # Format description with travel info if available
    description = mapping["description_template"]
    if travel_info:
        try:
            description = description.format(**travel_info)
        except (KeyError, ValueError):
            # Fallback if template formatting fails
            pass
    
    return ToolProgress(
        tool_id=tool_id,
        display_name=mapping["display_name"],
        description=description,
        status=status,
        result_preview=None,
        error_message=None
    )
