"""
Travel orchestrator models for comprehensive travel planning
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from .base_models import TripType, TravelPace, BudgetCategory, AgentResponseBase

class TravelInformation(BaseModel):
    """Complete travel information structure for validation"""
    
    # Core travel details
    destination: Optional[str] = Field(None, description="Destination city or location")
    origin: Optional[str] = Field(None, description="Departure city or airport")
    departure_date: Optional[date] = Field(None, description="Departure date")
    return_date: Optional[date] = Field(None, description="Return date for round trips")
    
    # Traveler information
    passengers: Optional[int] = Field(None, ge=1, le=20, description="Number of flight passengers")
    guests: Optional[int] = Field(None, ge=1, le=30, description="Number of accommodation guests")
    ages: Optional[List[int]] = Field(default_factory=list, description="Ages of travelers")
    
    # Trip characteristics
    trip_type: Optional[TripType] = Field(None, description="One-way or round-trip")
    travel_pace: Optional[TravelPace] = Field(None, description="Preferred travel pace")
    
    # Accommodation preferences
    check_in: Optional[date] = Field(None, description="Hotel check-in date")
    check_out: Optional[date] = Field(None, description="Hotel check-out date")
    rooms: Optional[int] = Field(None, ge=1, le=10, description="Number of rooms needed")
    
    # Budget and preferences
    budget: Optional[float] = Field(None, gt=0, description="Total trip budget in USD")
    budget_category: Optional[BudgetCategory] = Field(None, description="Budget category")
    
    # Preferences
    dietary_restrictions: List[str] = Field(default_factory=list, description="Dietary restrictions")
    accommodation_preferences: List[str] = Field(default_factory=list, description="Hotel/Airbnb preferences")
    activity_preferences: List[str] = Field(default_factory=list, description="Activity preferences")
    
    @validator('return_date')
    def return_after_departure(cls, v, values):
        if v and values.get('departure_date') and v <= values['departure_date']:
            raise ValueError('Return date must be after departure date')
        return v
    
    @validator('check_out')
    def checkout_after_checkin(cls, v, values):
        if v and values.get('check_in') and v <= values['check_in']:
            raise ValueError('Check-out date must be after check-in date')
        return v
    
    @validator('trip_type', always=True)
    def infer_trip_type(cls, v, values):
        """Infer trip type if not explicitly set"""
        if v is None:
            if values.get('return_date'):
                return TripType.ROUND_TRIP
            else:
                return TripType.ONE_WAY
        return v

class ValidationResult(BaseModel):
    """Results from travel requirements validation"""
    
    can_search: Dict[str, bool] = Field(
        default_factory=lambda: {"flights": False, "accommodations": False, "restaurants": False},
        description="Which specialist agents have sufficient information"
    )
    
    missing_info: Dict[str, List[str]] = Field(
        default_factory=lambda: {"flights": [], "accommodations": [], "restaurants": []},
        description="Missing required information by agent type"
    )
    
    next_questions: List[str] = Field(
        default_factory=list,
        description="Suggested questions to ask the user"
    )
    
    ready_agents: List[str] = Field(
        default_factory=list,
        description="Agents ready for immediate invocation"
    )
    
    completeness_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description="Overall completeness score (0-1)"
    )
    
    validation_summary: str = Field(
        default="",
        description="Human-readable validation summary"
    )

class AgentSearchResult(AgentResponseBase):
    """Generic container for agent search results"""
    search_type: str = Field(..., description="Type of search: flights, accommodations, restaurants")
    results: Dict[str, Any] = Field(default_factory=dict, description="Raw search results from agent")
    search_params: Dict[str, Any] = Field(default_factory=dict, description="Parameters used for search")
    result_count: int = Field(default=0, description="Number of results returned")

class ComprehensiveTravelPlan(BaseModel):
    """Complete travel plan synthesized from multiple agents"""
    
    # Core trip information
    destination: str = Field(..., description="Trip destination")
    origin: str = Field(..., description="Trip origin")
    dates: Dict[str, str] = Field(..., description="Travel dates")  # {"departure": "2024-06-15", "return": "2024-06-20"}
    travelers: int = Field(..., description="Number of travelers")
    
    # Search results from specialist agents
    flight_results: Optional[AgentSearchResult] = None
    accommodation_results: Optional[AgentSearchResult] = None
    restaurant_results: Optional[AgentSearchResult] = None
    
    # Orchestrator analysis and recommendations
    recommendations: Dict[str, Any] = Field(
        default_factory=dict,
        description="Orchestrator recommendations and analysis"
    )
    
    # Cost analysis
    estimated_costs: Dict[str, float] = Field(
        default_factory=dict,
        description="Estimated costs by category"
    )
    total_estimated_cost: Optional[float] = Field(None, description="Total estimated trip cost")
    
    # Plan metadata
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Plan confidence score")
    completeness_score: float = Field(0.0, ge=0.0, le=1.0, description="Plan completeness score")
    
    # Plan generation metadata
    created_at: datetime = Field(default_factory=datetime.now)
    agents_used: List[str] = Field(default_factory=list, description="List of agents that contributed to this plan")
    generation_time_seconds: Optional[float] = None
    
    def get_plan_summary(self) -> str:
        """Generate a human-readable plan summary"""
        summary_parts = [
            f"Trip to {self.destination} from {self.origin}",
            f"Dates: {self.dates.get('departure', 'TBD')} to {self.dates.get('return', 'TBD')}",
            f"Travelers: {self.travelers}"
        ]
        
        if self.total_estimated_cost:
            summary_parts.append(f"Estimated cost: ${self.total_estimated_cost:,.2f}")
        
        return " | ".join(summary_parts)
    
    def has_complete_results(self) -> bool:
        """Check if plan has results from all expected agents"""
        return all([
            self.flight_results and self.flight_results.success,
            self.accommodation_results and self.accommodation_results.success,
            self.restaurant_results and self.restaurant_results.success
        ])

class ConversationContext(BaseModel):
    """Context for managing multi-turn conversations"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="User identifier if available")
    
    # Current travel information being collected
    travel_info: TravelInformation = Field(default_factory=TravelInformation)
    
    # Conversation state
    conversation_stage: str = Field(default="initial", description="Current stage of conversation")
    questions_asked: List[str] = Field(default_factory=list, description="Questions already asked")
    clarifications_needed: List[str] = Field(default_factory=list, description="Outstanding clarifications")
    
    # Agent interaction history
    agent_calls_made: List[str] = Field(default_factory=list, description="Agents already called")
    last_validation_result: Optional[ValidationResult] = None
    
    # Generated plans
    current_plan: Optional[ComprehensiveTravelPlan] = None
    previous_plans: List[ComprehensiveTravelPlan] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def update_travel_info(self, **kwargs):
        """Update travel information and refresh timestamp"""
        for key, value in kwargs.items():
            if hasattr(self.travel_info, key):
                setattr(self.travel_info, key, value)
        self.last_updated = datetime.now()
    
    def add_agent_call(self, agent_name: str):
        """Record that an agent was called"""
        if agent_name not in self.agent_calls_made:
            self.agent_calls_made.append(agent_name)
        self.last_updated = datetime.now()
