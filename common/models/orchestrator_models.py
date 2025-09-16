"""
Unified response models for Travel Orchestrator Agent
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

# Import specialist agent response models using relative imports within common
from .flight_models import FlightSearchResults
from .accommodation_models import AccommodationAgentResponse
from .food_models import RestaurantSearchResults
from .travel_models import ComprehensiveTravelPlan


class ResponseType(str, Enum):
    """Types of responses the orchestrator can provide"""
    CONVERSATION = "conversation"      # Simple Q&A, validation errors, clarifications
    FLIGHTS = "flights"               # Flight search results only
    ACCOMMODATIONS = "accommodations" # Accommodation search results only
    RESTAURANTS = "restaurants"       # Restaurant search results only
    ITINERARY = "itinerary"          # Complete travel plan with multiple components


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
    
    # Structured data from specialist agents
    flight_results: Optional[FlightSearchResults] = Field(
        None, 
        description="Structured flight search results from flight agent"
    )
    accommodation_results: Optional[AccommodationAgentResponse] = Field(
        None, 
        description="Structured accommodation search results from accommodation agent"
    )
    restaurant_results: Optional[RestaurantSearchResults] = Field(
        None, 
        description="Structured restaurant search results from food agent"
    )
    
    # Complete travel planning
    comprehensive_plan: Optional[ComprehensiveTravelPlan] = Field(
        None, 
        description="Complete travel plan when response_type is 'itinerary'"
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
            if hasattr(self.flight_results, 'best_outbound_flight') and self.flight_results.best_outbound_flight:
                components.append("flights")
        
        if self.accommodation_results:
            if hasattr(self.accommodation_results, 'best_accommodations') and self.accommodation_results.best_accommodations:
                components.append(f"{len(self.accommodation_results.best_accommodations)} accommodations")
        
        if self.restaurant_results:
            if hasattr(self.restaurant_results, 'restaurants') and self.restaurant_results.restaurants:
                components.append(f"{len(self.restaurant_results.restaurants)} restaurants")
        
        if self.comprehensive_plan:
            components.append("comprehensive plan")
        
        component_str = ", ".join(components) if components else "conversation only"
        return f"{self.response_type.value} response with {component_str}"
    
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
            self.comprehensive_plan is not None
        ])


class AgentResponseParser:
    """Helper class to parse specialist agent responses into proper Pydantic models"""
    
    @staticmethod
    def parse_flight_response(raw_response: Dict[str, Any]) -> Optional[FlightSearchResults]:
        """Parse flight agent response into FlightSearchResults model"""
        try:
            # Handle both direct structured responses and text responses
            if isinstance(raw_response, dict):
                # Check if it's already structured flight data
                if 'best_outbound_flight' in raw_response or 'recommendation' in raw_response:
                    return FlightSearchResults.model_validate(raw_response)
                
                # Handle text responses wrapped in agent format
                if 'response_text' in raw_response:
                    # For now, return None - the text response will be handled by the orchestrator
                    return None
            
            return None
            
        except Exception as e:
            print(f"⚠️  Failed to parse flight response: {e}")
            return None
    
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
