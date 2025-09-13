# Inter-Agent Communication Specifications

## Overview

This document specifies how the Travel Orchestrator Agent communicates with specialized micro-agents to achieve true parallel execution and fault isolation.

## Agent Communication Architecture

### Agent Topology
```
Travel Orchestrator Agent (Main)
├── Flight Specialist Agent (Google Flights API)
├── Airbnb Specialist Agent (Nova Act Browser)
├── Booking.com Specialist Agent (Nova Act Browser)  
└── Food Specialist Agent (Yelp Fusion API)
```

### Communication Pattern
- **Protocol**: HTTP POST to AgentCore Runtime endpoints
- **Authentication**: AgentCore workload access tokens
- **Response Format**: Structured JSON with success/error handling
- **Timeout**: 45 seconds per agent call
- **Concurrency**: All specialist agents invoked in parallel

## Standardized Communication Protocol

### 1. Request Format

**Universal Request Structure**:
```json
{
  "prompt": "Search [agent_type] with the provided parameters",
  "search_params": {
    "destination": "Paris, France",
    "check_in": "2024-06-15",
    "check_out": "2024-06-22",
    "travelers": 2,
    "budget": 3000,
    "user_preferences": {
      "dietary_restrictions": ["vegetarian"],
      "accommodation_type": ["apartment", "hotel"]
    }
  },
  "metadata": {
    "request_id": "req_12345",
    "orchestrator_session_id": "orch_67890",
    "timeout_seconds": 45
  }
}
```

### 2. Response Format

**Universal Response Structure**:
```json
{
  "success": true,
  "platform": "airbnb",
  "data": {
    "properties": [...],
    "price_range": {"min": 89, "max": 250},
    "results_summary": "Found 18 properties matching criteria"
  },
  "metadata": {
    "search_method": "nova_act_browser",
    "source": "Airbnb",
    "results_count": 18,
    "search_duration_ms": 12500,
    "agent_version": "1.0.0"
  },
  "agent_info": {
    "agent_type": "airbnb_specialist",
    "model_used": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "session_id": "airbnb_session_98765"
  }
}
```

**Error Response Structure**:
```json
{
  "success": false,
  "platform": "booking_com",
  "error": {
    "code": "BROWSER_TIMEOUT",
    "message": "Nova Act browser session timed out",
    "details": {
      "timeout_seconds": 45,
      "last_action": "set_check_in_date",
      "recoverable": true
    }
  },
  "metadata": {
    "search_method": "nova_act_browser",
    "source": "Booking.com",
    "search_duration_ms": 45000,
    "agent_version": "1.0.0"
  }
}
```

## Agent-Specific Communication Contracts

### 1. Flight Specialist Agent Communication

**Request Parameters**:
```python
FlightSearchParams = {
    "origin": str,              # IATA code or city name
    "destination": str,         # IATA code or city name
    "departure_date": str,      # YYYY-MM-DD format
    "return_date": Optional[str], # YYYY-MM-DD format
    "travelers": int,           # Number of passengers
    "cabin_class": str = "economy"
}
```

**Expected Response Data**:
```python
FlightSearchResponse = {
    "flights": [
        {
            "airline": "Air France",
            "departure_time": "2024-06-15T22:30:00Z",
            "arrival_time": "2024-06-16T11:45:00Z",
            "duration": "7h 15m",
            "price": 542.0,
            "stops": 0,
            "booking_url": "https://..."
        }
    ],
    "metadata": {
        "search_method": "nova_act_browser",
        "source": "Google Flights",
        "results_count": 15,
        "price_range": {"min": 485, "max": 892}
    }
}
```

**Note**: Flight search uses Nova Act browser automation since Google Flights does not provide a public API.

### 2. Airbnb Specialist Agent Communication

**Request Parameters**:
```python
AirbnbSearchParams = {
    "location": str,           # City, neighborhood, or address
    "check_in": str,           # YYYY-MM-DD format
    "check_out": str,          # YYYY-MM-DD format
    "guests": int,             # Number of guests
    "budget": Optional[float], # Total budget for accommodation
    "property_type": Optional[str] = "entire_place"
}
```

**Expected Response Data**:
```python
AirbnbSearchResponse = {
    "properties": [
        {
            "title": "Cozy Apartment in Montmartre",
            "price_per_night": 120.0,
            "rating": 4.8,
            "location": "Montmartre, Paris",
            "amenities": ["wifi", "kitchen", "heating"],
            "property_type": "entire_apartment",
            "host_info": {"superhost": true},
            "booking_url": "https://airbnb.com/rooms/12345"
        }
    ],
    "neighborhood_insights": {
        "area_highlights": ["artistic district", "great restaurants"],
        "transportation_access": ["Metro Line 12", "Bus 40"]
    }
}
```

### 3. Booking.com Specialist Agent Communication

**Request Parameters**:
```python
BookingSearchParams = {
    "location": str,           # City or specific area
    "check_in": str,           # YYYY-MM-DD format
    "check_out": str,          # YYYY-MM-DD format
    "guests": int,             # Number of guests
    "budget": Optional[float], # Total budget for accommodation
    "star_rating": Optional[int] = None  # Minimum star rating
}
```

**Expected Response Data**:
```python
BookingSearchResponse = {
    "hotels": [
        {
            "name": "Hotel des Grands Boulevards",
            "price_per_night": 185.0,
            "rating": 8.4,  # Out of 10 for Booking.com
            "location": "2nd Arrondissement, Paris",
            "amenities": ["free_wifi", "breakfast", "gym"],
            "hotel_type": "boutique_hotel",
            "star_rating": 4,
            "cancellation_policy": "free_cancellation",
            "booking_url": "https://booking.com/hotel/12345"
        }
    ],
    "location_benefits": {
        "walkability_score": 9,
        "nearby_attractions": ["Louvre Museum", "Opera Garnier"]
    }
}
```

### 4. Food Specialist Agent Communication

**Request Parameters**:
```python
FoodSearchParams = {
    "location": str,                    # City or neighborhood
    "dietary_restrictions": List[str],  # ["vegetarian", "gluten-free", etc.]
    "budget": Optional[float],          # Daily food budget
    "meal_types": List[str] = ["breakfast", "lunch", "dinner"]
}
```

**Expected Response Data**:
```python
FoodSearchResponse = {
    "restaurants": [
        {
            "name": "L'As du Fallafel",
            "rating": 4.3,
            "price_level": "$$",
            "categories": ["middle_eastern", "vegetarian_friendly"],
            "address": "34 Rue des Rosiers, Paris",
            "phone": "+33 1 48 87 63 60",
            "opening_hours": {"monday": "11:30-23:00"},
            "specialties": ["falafel", "hummus"],
            "yelp_url": "https://yelp.com/biz/l-as-du-fallafel"
        }
    ],
    "food_scene_insights": {
        "local_specialties": ["croissants", "macarons", "wine"],
        "budget_recommendations": "€25-35 per person per day"
    }
}
```

## Error Handling and Fault Tolerance

### 1. Agent Failure Scenarios

**Common Failure Types**:
```python
class AgentError(Exception):
    """Base class for agent communication errors"""
    pass

class AgentTimeoutError(AgentError):
    """Agent failed to respond within timeout"""
    pass

class AgentUnavailableError(AgentError):
    """Agent runtime is unavailable"""
    pass

class AgentDataError(AgentError):
    """Agent returned invalid or incomplete data"""
    pass

class BrowserAutomationError(AgentError):
    """Browser automation failed (Nova Act specific)"""
    pass
```

### 2. Orchestrator Error Handling

**Resilient Orchestration Logic**:
```python
class TravelOrchestratorAgent(Agent):
    
    async def _handle_partial_results(self, search_tasks: List[asyncio.Task]) -> List[dict]:
        """Handle scenario where some agents timeout or fail"""
        
        results = []
        
        for task in search_tasks:
            try:
                # Check if task completed
                if task.done():
                    result = await task
                    results.append(result)
                else:
                    # Task is still running, cancel it
                    task.cancel()
                    results.append({
                        "success": False,
                        "error": "Agent timeout - search cancelled",
                        "agent": "unknown"
                    })
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e),
                    "agent": "unknown"
                })
        
        return results
    
    def _synthesize_multi_agent_results(self, results: List[dict], 
                                       search_params: dict, 
                                       user_profile: UserProfile) -> dict:
        """Synthesize results even with partial failures"""
        
        # Separate successful and failed results
        successful_results = [r for r in results if r.get("success", False)]
        failed_results = [r for r in results if not r.get("success", False)]
        
        # Log failures but continue with available data
        for failure in failed_results:
            logger.warning(f"Agent {failure.get('agent', 'unknown')} failed: {failure.get('error')}")
        
        # Build response with available data
        synthesized = {
            "search_status": "partial" if failed_results else "complete",
            "successful_platforms": [r.get("platform") for r in successful_results],
            "failed_platforms": [r.get("platform") for r in failed_results],
            "recommendations": self._build_recommendations(successful_results, user_profile),
            "metadata": {
                "total_agents_called": len(results),
                "successful_agents": len(successful_results),
                "failed_agents": len(failed_results),
                "degraded_experience": len(failed_results) > 0
            }
        }
        
        # Add user-friendly messaging for failures
        if failed_results:
            synthesized["user_message"] = self._generate_failure_message(failed_results)
        
        return synthesized
    
    def _generate_failure_message(self, failures: List[dict]) -> str:
        """Generate user-friendly message for agent failures"""
        
        failed_platforms = [f.get("platform", "unknown") for f in failures]
        
        if "airbnb" in failed_platforms and "booking_com" in failed_platforms:
            return "I couldn't access accommodation platforms right now, but I found great flight and restaurant options for you."
        elif "airbnb" in failed_platforms:
            return "Airbnb search is temporarily unavailable, but I found hotels and other options."
        elif "booking_com" in failed_platforms:
            return "Hotel booking sites are temporarily unavailable, but I found Airbnb and other options."
        elif "google_flights" in failed_platforms:
            return "Flight search is temporarily unavailable, but I found great accommodation and restaurant options."
        else:
            return f"Some search platforms are temporarily unavailable, but I found options from available sources."
```

### 3. Retry and Fallback Strategies

**Agent Retry Configuration**:
```python
class AgentCommunicationConfig:
    """Configuration for inter-agent communication"""
    
    RETRY_CONFIG = {
        "max_attempts": 2,
        "backoff_factor": 1.5,
        "timeout_seconds": 45,
        "jitter": True
    }
    
    FALLBACK_STRATEGIES = {
        "airbnb": ["booking", "manual_search_suggestion"],
        "booking": ["airbnb", "manual_search_suggestion"], 
        "flights": ["manual_search_suggestion"],
        "food": ["generic_recommendations"]
    }

async def robust_agent_invocation(self, agent_type: str, params: dict) -> dict:
    """Invoke agent with retry logic and fallbacks"""
    
    config = AgentCommunicationConfig.RETRY_CONFIG
    
    for attempt in range(config["max_attempts"]):
        try:
            # Add jitter to prevent thundering herd
            if config["jitter"] and attempt > 0:
                await asyncio.sleep(random.uniform(0.1, 0.5))
            
            result = await self._call_specialist_agent(agent_type, params)
            
            if result["success"]:
                return result
            
        except asyncio.TimeoutError:
            if attempt == config["max_attempts"] - 1:
                return await self._apply_fallback_strategy(agent_type, params)
            
            # Exponential backoff with jitter
            wait_time = config["backoff_factor"] ** attempt
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            logger.error(f"Agent {agent_type} failed on attempt {attempt + 1}: {e}")
            
            if attempt == config["max_attempts"] - 1:
                return await self._apply_fallback_strategy(agent_type, params)
    
    return {"success": False, "error": "Max retry attempts exceeded"}

async def _apply_fallback_strategy(self, failed_agent: str, params: dict) -> dict:
    """Apply fallback strategy when agent fails"""
    
    fallbacks = AgentCommunicationConfig.FALLBACK_STRATEGIES.get(failed_agent, [])
    
    for fallback in fallbacks:
        if fallback == "manual_search_suggestion":
            return {
                "success": True,
                "fallback": True,
                "platform": failed_agent,
                "data": {
                    "suggestion": f"Please search {failed_agent} manually",
                    "search_url": self._generate_manual_search_url(failed_agent, params)
                }
            }
        elif fallback in self.specialist_agents:
            # Try alternative agent
            try:
                return await self._call_specialist_agent(fallback, params)
            except:
                continue
    
    return {"success": False, "error": "All fallback strategies exhausted"}
```

## Agent-Specific Communication Details

### 1. Flight Agent Communication

**Invocation Example**:
```python
async def _invoke_flight_agent(self, params: dict) -> dict:
    """Invoke Flight Specialist Agent with proper parameters"""
    
    flight_params = {
        "origin": params.get("origin", self._get_user_default_airport()),
        "destination": params["destination"],
        "departure_date": params["check_in"],
        "return_date": params.get("check_out"),
        "travelers": params["travelers"],
        "cabin_class": params.get("cabin_preference", "economy")
    }
    
    return await self._call_specialist_agent("flights", flight_params)
```

**Success Response Processing**:
```python
def _process_flight_results(self, flight_response: dict) -> dict:
    """Process flight agent response into standardized format"""
    
    if not flight_response.get("success"):
        return {"flights": [], "error": flight_response.get("error")}
    
    flight_data = flight_response["data"]
    
    return {
        "flights": flight_data.get("flights", []),
        "price_analysis": flight_data.get("price_analysis", {}),
        "booking_recommendations": self._generate_flight_booking_advice(flight_data),
        "source_attribution": {
            "platform": "Google Flights",
            "data_freshness": "real-time",
            "last_updated": datetime.utcnow().isoformat()
        }
    }
```

### 2. Accommodation Agents Communication

**Parallel Accommodation Search**:
```python
async def _invoke_accommodation_agents(self, params: dict) -> dict:
    """Invoke both Airbnb and Booking.com agents in parallel"""
    
    accommodation_params = {
        "location": params["destination"],
        "check_in": params["check_in"], 
        "check_out": params["check_out"],
        "guests": params["travelers"],
        "budget": params.get("budget")
    }
    
    # Execute both accommodation searches simultaneously
    airbnb_task = self._call_specialist_agent("airbnb", accommodation_params)
    booking_task = self._call_specialist_agent("booking", accommodation_params)
    
    try:
        airbnb_result, booking_result = await asyncio.gather(
            airbnb_task, booking_task, 
            timeout=45.0
        )
        
        return self._combine_accommodation_results(airbnb_result, booking_result)
        
    except asyncio.TimeoutError:
        # Handle case where one or both agents timeout
        return await self._handle_accommodation_timeout(airbnb_task, booking_task)

def _combine_accommodation_results(self, airbnb_result: dict, 
                                 booking_result: dict) -> dict:
    """Combine results from both accommodation agents"""
    
    combined = {
        "accommodations": [],
        "platforms_searched": [],
        "price_comparison": {},
        "recommendation_diversity": 0
    }
    
    # Process Airbnb results
    if airbnb_result.get("success"):
        airbnb_data = airbnb_result["data"]
        combined["accommodations"].extend(airbnb_data.get("properties", []))
        combined["platforms_searched"].append("Airbnb")
        combined["price_comparison"]["airbnb"] = self._extract_price_range(airbnb_data)
    
    # Process Booking.com results  
    if booking_result.get("success"):
        booking_data = booking_result["data"]
        combined["accommodations"].extend(booking_data.get("hotels", []))
        combined["platforms_searched"].append("Booking.com")
        combined["price_comparison"]["booking_com"] = self._extract_price_range(booking_data)
    
    # Calculate diversity score
    combined["recommendation_diversity"] = len(combined["platforms_searched"]) / 2.0
    
    # Rank combined results
    combined["accommodations"] = self._rank_accommodations(
        combined["accommodations"], 
        self.memory.get_user_profile(self.user_id)
    )
    
    return combined
```

### 3. Food Agent Communication

**Restaurant Search Invocation**:
```python
async def _invoke_food_agent(self, params: dict) -> dict:
    """Invoke Food Specialist Agent with dietary considerations"""
    
    user_preferences = params.get("user_preferences", {})
    
    food_params = {
        "location": params["destination"],
        "dietary_restrictions": user_preferences.get("dietary_restrictions", []),
        "budget": self._calculate_daily_food_budget(params.get("budget")),
        "cuisine_preferences": user_preferences.get("cuisine_types", []),
        "meal_types": ["breakfast", "lunch", "dinner", "snacks"]
    }
    
    return await self._call_specialist_agent("food", food_params)

def _calculate_daily_food_budget(self, total_budget: float) -> float:
    """Calculate reasonable daily food budget from total trip budget"""
    
    if not total_budget:
        return None
    
    # Assume 25-30% of total budget goes to food
    daily_food_budget = (total_budget * 0.275) / 7  # Assume 7-day trip
    return round(daily_food_budget, 2)
```

## Performance and Monitoring

### 1. Communication Metrics

**Key Performance Indicators**:
```python
class InterAgentMetrics:
    """Metrics for inter-agent communication"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector("TravelAgent/InterAgent")
    
    def record_agent_call(self, agent_type: str, duration_ms: float, 
                         success: bool, result_count: int):
        """Record metrics for agent-to-agent calls"""
        
        self.metrics_collector.record_metric(
            name="AgentCallLatency",
            value=duration_ms,
            unit="Milliseconds",
            dimensions={
                "TargetAgent": agent_type,
                "Status": "Success" if success else "Failed"
            }
        )
        
        self.metrics_collector.record_metric(
            name="AgentResultsCount",
            value=result_count,
            unit="Count",
            dimensions={"TargetAgent": agent_type}
        )
    
    def record_parallel_search_performance(self, total_duration_ms: float,
                                         successful_agents: int, total_agents: int):
        """Record metrics for parallel search coordination"""
        
        success_rate = successful_agents / total_agents if total_agents > 0 else 0
        
        self.metrics_collector.record_metric(
            name="ParallelSearchDuration", 
            value=total_duration_ms,
            unit="Milliseconds"
        )
        
        self.metrics_collector.record_metric(
            name="ParallelSearchSuccessRate",
            value=success_rate,
            unit="Percent"
        )
```

### 2. Tracing and Observability

**Cross-Agent Tracing**:
```python
from opentelemetry import trace
from opentelemetry.propagate import inject, extract

class TracedAgentCommunication:
    """Add OpenTelemetry tracing to agent communication"""
    
    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
    
    async def traced_agent_call(self, agent_type: str, params: dict) -> dict:
        """Make agent call with distributed tracing"""
        
        with self.tracer.start_as_current_span(f"invoke_{agent_type}_agent") as span:
            # Add span attributes
            span.set_attribute("agent.type", agent_type)
            span.set_attribute("agent.destination", params.get("destination", "unknown"))
            span.set_attribute("agent.travelers", params.get("travelers", 0))
            
            # Inject trace context into request headers
            headers = {}
            inject(headers)
            
            try:
                result = await self._call_specialist_agent(agent_type, params, headers)
                
                # Record success metrics
                span.set_attribute("agent.success", True)
                span.set_attribute("agent.results_count", 
                                 len(result.get("data", {}).get("results", [])))
                
                return result
                
            except Exception as e:
                # Record error information
                span.set_attribute("agent.success", False)
                span.set_attribute("agent.error", str(e))
                span.record_exception(e)
                raise
```

### 3. Agent Health Monitoring

**Health Check System**:
```python
class AgentHealthMonitor:
    """Monitor health of all specialist agents"""
    
    def __init__(self, specialist_agents: Dict[str, str]):
        self.specialist_agents = specialist_agents
        self.health_status = {}
        self.last_health_check = {}
    
    async def check_all_agents_health(self) -> Dict[str, bool]:
        """Check health status of all specialist agents"""
        
        health_tasks = [
            self._check_agent_health(agent_type, agent_arn)
            for agent_type, agent_arn in self.specialist_agents.items()
        ]
        
        health_results = await asyncio.gather(*health_tasks, return_exceptions=True)
        
        # Update health status
        for i, agent_type in enumerate(self.specialist_agents.keys()):
            result = health_results[i]
            self.health_status[agent_type] = not isinstance(result, Exception)
            self.last_health_check[agent_type] = datetime.utcnow()
        
        return self.health_status
    
    async def _check_agent_health(self, agent_type: str, agent_arn: str) -> bool:
        """Check health of individual agent"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/{agent_arn}/invocations",
                    headers={
                        "Authorization": f"Bearer {self._get_workload_access_token()}",
                        "Content-Type": "application/json"
                    },
                    json={"prompt": "health_check"},
                    timeout=10.0
                )
                
                return response.status_code == 200
                
        except Exception:
            return False
```

This inter-agent communication specification ensures reliable, fault-tolerant coordination between all specialist agents while maintaining performance and observability.
