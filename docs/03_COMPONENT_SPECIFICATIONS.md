# AI Travel Agent - Component Specifications

## Overview

This document provides detailed technical specifications for each major component of the AI Travel Agent system. These specifications serve as implementation guides for developers building each component.

## Frontend Components

### 1. Chat Interface System

**Location**: `frontend/src/components/chat/`

**Core Components**:
```typescript
interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'agent';
  timestamp: Date;
  sources?: SourceAttribution[];
  metadata?: {
    searchStatus?: 'searching' | 'completed' | 'failed';
    platforms?: string[];
    resultCount?: number;
  };
}

interface SourceAttribution {
  platform: string;
  url?: string;
  timestamp: Date;
  dataType: 'flight' | 'accommodation' | 'activity' | 'restaurant';
}
```

**ChatInterface Component**:
```typescript
interface ChatInterfaceProps {
  userId: string;
  conversationId?: string;
  initialMessages?: ChatMessage[];
  onMessageSend?: (message: string) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  userId,
  conversationId,
  initialMessages = [],
  onMessageSend
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [isTyping, setIsTyping] = useState(false);
  const [currentSearch, setCurrentSearch] = useState<SearchStatus | null>(null);
  
  // Real-time message handling with WebSocket
  const { sendMessage, isConnected } = useWebSocket({
    url: `wss://api.travel-agent.com/chat/${conversationId}`,
    onMessage: handleIncomingMessage,
    onError: handleConnectionError
  });
  
  // Auto-scroll to bottom on new messages
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  return (
    <div className="flex flex-col h-full bg-gray-50">
      <ChatHeader conversationId={conversationId} />
      <ChatMessages 
        messages={messages}
        isTyping={isTyping}
        currentSearch={currentSearch}
      />
      <ChatInput 
        onSend={handleSendMessage}
        disabled={!isConnected}
        placeholder="Ask me about your travel plans..."
      />
    </div>
  );
};
```

**ChatMessages Component**:
```typescript
const ChatMessages: React.FC<{
  messages: ChatMessage[];
  isTyping: boolean;
  currentSearch: SearchStatus | null;
}> = ({ messages, isTyping, currentSearch }) => {
  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
      {messages.map((message) => (
        <MessageBubble 
          key={message.id}
          message={message}
          showSources={message.role === 'agent'}
        />
      ))}
      
      {/* Real-time search status */}
      {currentSearch && (
        <SearchStatusIndicator 
          platforms={currentSearch.platforms}
          progress={currentSearch.progress}
          estimatedTime={currentSearch.estimatedTime}
        />
      )}
      
      {/* Typing indicator */}
      {isTyping && <TypingIndicator />}
      
      <div ref={messagesEndRef} />
    </div>
  );
};
```

### 2. Authentication System

**Location**: `frontend/src/auth/`

**Authentication Hook**:
```typescript
interface AuthUser {
  id: string;
  email: string;
  name: string;
  preferences?: UserPreferences;
  subscription?: {
    tier: 'free' | 'premium';
    expiresAt?: Date;
  };
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshToken: () => Promise<void>;
}

export const useAuth = (): AuthContextValue => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    // Initialize auth from stored tokens
    initializeAuth();
  }, []);
  
  const signIn = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await Auth.signIn(email, password);
      const userData = await fetchUserProfile(response.accessToken);
      setUser(userData);
      
      // Store tokens securely
      TokenStorage.setTokens({
        accessToken: response.accessToken,
        refreshToken: response.refreshToken,
        expiresAt: response.expiresAt
      });
    } catch (error) {
      throw new AuthError(error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    signIn,
    signUp,
    signOut,
    refreshToken
  };
};
```

### 3. Itinerary Builder

**Location**: `frontend/src/components/itinerary/`

**Data Models**:
```typescript
interface Itinerary {
  id: string;
  destination: string;
  startDate: Date;
  endDate: Date;
  travelers: number;
  budget: number;
  days: ItineraryDay[];
  metadata: {
    createdAt: Date;
    lastModified: Date;
    version: number;
  };
}

interface ItineraryDay {
  date: Date;
  accommodation: Accommodation | null;
  activities: Activity[];
  meals: Restaurant[];
  transportation: Transportation[];
  notes: string;
  estimatedCost: number;
}

interface Activity {
  id: string;
  name: string;
  category: 'sightseeing' | 'entertainment' | 'culture' | 'outdoor';
  location: Location;
  duration: number; // minutes
  cost: number;
  rating: number;
  timeSlot: {
    start: string; // HH:mm format
    end: string;
  };
  bookingUrl?: string;
  source: string;
}
```

**Interactive Itinerary Component**:
```typescript
const InteractiveItinerary: React.FC<{
  itinerary: Itinerary;
  onUpdate: (updatedItinerary: Itinerary) => void;
  isEditable?: boolean;
}> = ({ itinerary, onUpdate, isEditable = true }) => {
  const [draggedItem, setDraggedItem] = useState<DragItem | null>(null);
  const [showAlternatives, setShowAlternatives] = useState(false);
  
  const handleDragEnd = useCallback((result: DropResult) => {
    if (!result.destination) return;
    
    // Handle reordering within same day or moving between days
    const updatedItinerary = reorderActivities(
      itinerary,
      result.source,
      result.destination
    );
    
    onUpdate(updatedItinerary);
  }, [itinerary, onUpdate]);
  
  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <div className="space-y-6">
        <ItineraryHeader 
          itinerary={itinerary}
          onExport={() => exportItinerary(itinerary)}
          onShare={() => shareItinerary(itinerary)}
        />
        
        {itinerary.days.map((day, dayIndex) => (
          <Droppable 
            key={day.date.toISOString()}
            droppableId={`day-${dayIndex}`}
          >
            {(provided) => (
              <DayCard
                ref={provided.innerRef}
                {...provided.droppableProps}
                day={day}
                dayIndex={dayIndex}
                isEditable={isEditable}
                onActivityReplace={(activityIndex) =>
                  handleActivityReplace(dayIndex, activityIndex)
                }
                onAddActivity={() => handleAddActivity(dayIndex)}
                onTimeSlotChange={(activityIndex, timeSlot) =>
                  handleTimeSlotChange(dayIndex, activityIndex, timeSlot)
                }
              />
            )}
          </Droppable>
        ))}
      </div>
    </DragDropContext>
  );
};
```

## Backend Components

### 1. Single Agent Implementation

**Location**: `agents/travel_orchestrator/`

**Travel Orchestrator Agent** - `travel_orchestrator.py`
```python
from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from strands.models.bedrock import BedrockModel
from typing import Optional

app = BedrockAgentCoreApp()

class TravelOrchestratorAgent(Agent):
    """Single agent that handles all travel planning through integrated tools"""
    
    def __init__(self, memory_id: Optional[str] = None, session_id: Optional[str] = None, 
                 actor_id: Optional[str] = None, region: str = "us-east-1"):
        # Configure Nova Premier model for enhanced reasoning
        model = BedrockModel(
            model_id="us.amazon.nova-premier-v1:0",
            max_tokens=10000,
            temperature=0.7,
            top_p=0.9
        )
        
        # Initialize memory if enabled
        memory_hooks = None
        if memory_id:
            try:
                memory_client = MemoryClient(region_name=region)
                memory_hooks = TravelMemoryHook(memory_client, memory_id)
            except Exception as e:
                logger.error(f"Failed to initialize memory: {e}")
                memory_hooks = None
        
        # Initialize Gateway tools via MCP client
        gateway_tools = self._initialize_gateway_tools(region)
        
        # Combine direct tools with Gateway tools
        all_tools = (
            [
                self.search_flights,        # Amadeus API integration
                self.search_accommodations, # Nova Act browser automation
            ]
            + gateway_tools  # Add Google Maps tools from Gateway
        )
        
        super().__init__(
            model=model,
            tools=all_tools,
            system_prompt=self._build_system_prompt(),
            hooks=[memory_hooks] if memory_hooks else [],
            state={
                "actor_id": actor_id,
                "session_id": session_id,
                "agent_type": "travel_orchestrator"
            }
        )
    
    @tool
    def search_flights(self, origin: str, destination: str, departure_date: str, 
                      return_date: Optional[str] = None, passengers: int = 1) -> TravelOrchestratorResponse:
        """Search flights using Amadeus Flight Offers Search API"""
        validation_errors = self._validate_flight_params(origin, destination, departure_date, return_date, passengers)
        
        if validation_errors:
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.VALIDATION_ERROR,
                message=f"Missing required parameters: {', '.join(validation_errors)}",
                success=False,
                error_message=f"Missing parameters: {', '.join(validation_errors)}"
            )
        
        return search_flights_direct(origin, destination, departure_date, return_date, passengers)
    
    @tool  
    def search_accommodations(self, destination: str, departure_date: str, return_date: str,
                            passengers: int = 2, rooms: int = 1, platform_preference: str = "both") -> TravelOrchestratorResponse:
        """Search accommodations using Nova Act browser automation"""
        validation_errors = self._validate_accommodation_params(destination, departure_date, return_date, passengers, rooms)
        
        if validation_errors:
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.VALIDATION_ERROR,
                message=f"Missing required parameters: {', '.join(validation_errors)}",
                success=False,
                error_message=f"Missing parameters: {', '.join(validation_errors)}"
            )
        
        return search_accommodations_direct(destination, departure_date, return_date, passengers, rooms, platform_preference)
    
    def _initialize_gateway_tools(self, region: str = "us-east-1") -> List:
        """Initialize Gateway tools via MCP client for Google Maps integration"""
        try:
            # Get Gateway configuration from Parameter Store
            gateway_url = get_parameter('/travel-agent/gateway-url')
            gateway_client_id = get_parameter('/travel-agent/gateway-client-id')
            gateway_client_secret = get_parameter('/travel-agent/gateway-client-secret')
            
            if not all([gateway_url, gateway_client_id, gateway_client_secret]):
                logger.warning("Gateway configuration not found - Google Maps tools disabled")
                return []
            
            # Initialize MCP client and start session
            self.mcp_client = MCPClient(create_gateway_transport)
            self.mcp_client.start()
            
            gateway_tools = self.mcp_client.list_tools_sync()
            logger.info(f"Discovered {len(gateway_tools)} Google Maps tools from Gateway")
            
            return gateway_tools
                
        except Exception as e:
            logger.warning(f"Gateway tool discovery failed: {e}")
            return []

@app.entrypoint
def travel_orchestrator_invocation(payload, context=None):
    """Non-streaming JSON response entry point"""
    if "prompt" not in payload:
        return {"error": "Missing 'prompt' in payload"}
    
    try:
        # Extract session ID from AgentCore context
        session_id = context.session_id if context and hasattr(context, 'session_id') else generate_session_ids()
        actor_id = "travel-orchestrator"
        
        # Initialize memory (optional)
        memory_id = initialize_memory()
        
        # Create agent instance
        agent = TravelOrchestratorAgent(
            memory_id=memory_id,
            session_id=session_id,
            actor_id=actor_id
        )
        
        # Get complete response from agent (non-streaming)
        result = agent(payload["prompt"])
        
        # Parse and return JSON response
        return parse_agent_response(result)
            
    except Exception as e:
        logger.error(f"Error in travel orchestrator: {str(e)}")
        return {
            "error": f"Travel orchestrator failed: {str(e)}",
            "response_type": "conversation",
            "response_status": "tool_error",
            "message": "I encountered an internal error. Please try again.",
            "success": False
        }

if __name__ == "__main__":
    app.run()
```

**Integrated Tool Implementations** - `tools/`

**Flight Search Tool** - `tools/flight_search_tool.py`
```python
from amadeus import Client
from datetime import datetime
from typing import Optional

def search_flights_direct(origin: str, destination: str, departure_date: str, 
                         return_date: Optional[str] = None, passengers: int = 1) -> TravelOrchestratorResponse:
    """Search flights using Amadeus Flight Offers Search API"""
    
    start_time = datetime.now()
    print(f"✈️  Amadeus flight search: {origin} → {destination} on {departure_date}")
    
    try:
        # Initialize Amadeus client
        amadeus = Client(
            client_id=os.getenv('AMADEUS_CLIENT_ID'),
            client_secret=os.getenv('AMADEUS_CLIENT_SECRET'),
            hostname=os.getenv('AMADEUS_HOSTNAME', 'test')
        )
        
        # Prepare search parameters
        search_params = {
            'originLocationCode': origin.upper(),
            'destinationLocationCode': destination.upper(),
            'departureDate': departure_date,
            'adults': passengers,
            'max': 50,
            'currencyCode': 'USD'
        }
        
        if return_date:
            search_params['returnDate'] = return_date
        
        # Make API call
        response = amadeus.shopping.flight_offers_search.get(**search_params)
        flight_offers = response.data
        
        if not flight_offers:
            return TravelOrchestratorResponse(
                response_type=ResponseType.CONVERSATION,
                response_status=ResponseStatus.TOOL_ERROR,
                message=f"No flights found from {origin} to {destination} on {departure_date}",
                success=False,
                error_message="No flights found"
            )
        
        # Select best flights using scoring algorithm
        best_outbound_flight, outbound_score = _select_best_flight(flight_offers, "outbound")
        best_return_flight = None
        
        if return_date:
            return_result = _select_best_flight(flight_offers, "return")
            if return_result:
                best_return_flight, return_score = return_result
        
        # Create flight list
        flight_list = [best_outbound_flight]
        if best_return_flight:
            flight_list.append(best_return_flight)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.FLIGHTS,
            response_status=ResponseStatus.COMPLETE_SUCCESS,
            message=_generate_recommendation(best_outbound_flight, best_return_flight, origin, destination, return_date is not None),
            flight_results=flight_list,
            processing_time_seconds=processing_time,
            success=True
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.CONVERSATION,
            response_status=ResponseStatus.TOOL_ERROR,
            message="I encountered an error while searching for flights. Please try again.",
            success=False,
            error_message=str(e),
            processing_time_seconds=processing_time
        )
```

**3. Airbnb Specialist Agent** - `airbnb_agent.py`
```python
from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp
from nova_act import NovaAct
from pydantic import BaseModel
from typing import List

app = BedrockAgentCoreApp()

class PropertyListing(BaseModel):
    title: str
    price_per_night: float
    rating: float
    location: str
    amenities: List[str]
    image_url: str = None

class AirbnbSpecialistAgent(Agent):
    """Specialized agent for Airbnb searches using Nova Act"""
    
    def __init__(self):
        super().__init__(
            model="anthropic.claude-3-5-sonnet-20241022-v2:0"  # More capable for browser tasks
        )
    
    @tool
    def search_airbnb_properties(self, location: str, check_in: str, 
                               check_out: str, guests: int = 2, 
                               budget: float = None) -> dict:
        """Search Airbnb using Nova Act browser automation"""
        
        try:
            with NovaAct(
                starting_page="https://www.airbnb.com",
                headless=True,
                user_agent="TravelAgent/1.0 (NovaAct)"
            ) as nova:
                
                # Navigation and search setup
                nova.act(f"Search for places to stay in {location}")
                nova.act(f"Set check-in date to {check_in}")  
                nova.act(f"Set check-out date to {check_out}")
                nova.act(f"Set number of guests to {guests}")
                
                # Apply budget filter if specified
                if budget:
                    max_per_night = budget / 7  # Estimate nights
                    nova.act(f"Apply price filter up to ${int(max_per_night)} per night")
                
                # Extract structured data
                result = nova.act(
                    """Extract property listings with this information:
                    - Property title
                    - Price per night (as number)
                    - Guest rating (as number out of 5)
                    - Neighborhood/area
                    - Key amenities (as array)
                    - Property image URL if visible
                    
                    Return data for the first 20 listings.""",
                    schema=PropertySearchResults.model_json_schema()
                )
                
                if result.matches_schema:
                    properties = PropertySearchResults.model_validate(result.parsed_response)
                    return {
                        "success": True,
                        "platform": "airbnb",
                        "properties": properties.listings,
                        "metadata": {
                            "search_method": "nova_act_browser",
                            "source": "Airbnb",
                            "results_count": len(properties.listings)
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to parse Airbnb results",
                        "platform": "airbnb"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Airbnb search failed: {str(e)}",
                "platform": "airbnb"
            }

@app.entrypoint
async def airbnb_agent_invocation(payload):
    """Entry point for Airbnb searches"""
    agent = AirbnbSpecialistAgent()
    search_params = payload.get("search_params", {})
    
    # Process Airbnb search request
    stream = agent.stream_async(f"""
    Search for Airbnb properties with these parameters: {search_params}
    Use the search_airbnb_properties tool to get real-time property data.
    """)
    
    async for event in stream:
        yield event

if __name__ == "__main__":
    app.run()
```

**4. Booking.com Specialist Agent** - `booking_agent.py`
```python
from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp
from nova_act import NovaAct
from pydantic import BaseModel
from typing import List

app = BedrockAgentCoreApp()

class HotelListing(BaseModel):
    name: str
    price_per_night: float
    rating: float
    location: str
    amenities: List[str]
    hotel_type: str

class BookingSpecialistAgent(Agent):
    """Specialized agent for Booking.com searches using Nova Act"""
    
    def __init__(self):
        super().__init__(
            model="anthropic.claude-3-5-sonnet-20241022-v2:0"  # More capable for browser tasks
        )
    
    @tool
    def search_booking_hotels(self, location: str, check_in: str,
                            check_out: str, guests: int = 2,
                            budget: float = None) -> dict:
        """Search Booking.com using Nova Act browser automation"""
        
        try:
            with NovaAct(
                starting_page="https://www.booking.com",
                headless=True,
                user_agent="TravelAgent/1.0 (NovaAct)"
            ) as nova:
                
                # Navigation and search setup
                nova.act(f"Search for hotels in {location}")
                nova.act(f"Set check-in date to {check_in}")
                nova.act(f"Set check-out date to {check_out}")
                nova.act(f"Set number of guests to {guests}")
                
                # Apply budget filter if specified
                if budget:
                    max_per_night = budget / 7  # Estimate nights
                    nova.act(f"Apply price filter up to ${int(max_per_night)} per night")
                
                # Extract structured data
                result = nova.act(
                    """Extract hotel listings with this information:
                    - Hotel name
                    - Price per night (as number)
                    - Guest rating (as number out of 10)
                    - Location/district
                    - Key amenities and facilities (as array)
                    - Property type (hotel, apartment, etc.)
                    
                    Return data for the first 20 listings.""",
                    schema=HotelSearchResults.model_json_schema()
                )
                
                if result.matches_schema:
                    hotels = HotelSearchResults.model_validate(result.parsed_response)
                    return {
                        "success": True,
                        "platform": "booking_com",
                        "hotels": hotels.listings,
                        "metadata": {
                            "search_method": "nova_act_browser",
                            "source": "Booking.com",
                            "results_count": len(hotels.listings)
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to parse Booking.com results",
                        "platform": "booking_com"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Booking.com search failed: {str(e)}",
                "platform": "booking_com"
            }

@app.entrypoint
async def booking_agent_invocation(payload):
    """Entry point for Booking.com searches"""
    agent = BookingSpecialistAgent()
    search_params = payload.get("search_params", {})
    
    # Process Booking.com search request
    stream = agent.stream_async(f"""
    Search for hotels on Booking.com with these parameters: {search_params}
    Use the search_booking_hotels tool to get real-time hotel data.
    """)
    
    async for event in stream:
        yield event

if __name__ == "__main__":
    app.run()
```

**5. Food Specialist Agent** - `food_agent.py`
```python
from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp
import requests
import os
from typing import List

app = BedrockAgentCoreApp()

class FoodSpecialistAgent(Agent):
    """Specialized agent for restaurant search using Yelp Fusion API"""
    
    def __init__(self):
        super().__init__(
            model="anthropic.claude-3-haiku-20240307-v1:0"  # Fast, cost-effective model
        )
        self.yelp_api_key = os.getenv('YELP_API_KEY')
        self.base_url = "https://api.yelp.com/v3"
    
    @tool
    def search_restaurants(self, location: str, dietary_restrictions: List[str] = None,
                         budget: float = None) -> dict:
        """Search restaurants using Yelp Fusion API"""
        
        try:
            # Build category filters based on dietary restrictions
            categories = "restaurants,bars,cafes"
            if dietary_restrictions:
                if "vegetarian" in dietary_restrictions:
                    categories += ",vegetarian"
                if "vegan" in dietary_restrictions:
                    categories += ",vegan"
            
            params = {
                "location": location,
                "categories": categories,
                "limit": 30,
                "sort_by": "rating"
            }
            
            # Add price filter if budget specified
            if budget:
                # Yelp price scale: 1($), 2($$), 3($$$), 4($$$$)
                price_level = 2 if budget < 2000 else 3 if budget < 5000 else 4
                params["price"] = ",".join([str(i) for i in range(1, price_level + 1)])
            
            response = requests.get(
                f"{self.base_url}/businesses/search",
                headers={"Authorization": f"Bearer {self.yelp_api_key}"},
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                businesses = response.json()["businesses"]
                return {
                    "success": True,
                    "platform": "yelp",
                    "restaurants": businesses,
                    "metadata": {
                        "search_method": "yelp_api",
                        "source": "Yelp Fusion API",
                        "results_count": len(businesses)
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Yelp API error: {response.status_code}",
                    "platform": "yelp"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Restaurant search failed: {str(e)}",
                "platform": "yelp"
            }

@app.entrypoint
async def food_agent_invocation(payload):
    """Entry point for restaurant searches"""
    agent = FoodSpecialistAgent()
    search_params = payload.get("search_params", {})
    
    # Process restaurant search request
    stream = agent.stream_async(f"""
    Search for restaurants with these parameters: {search_params}
    Use the search_restaurants tool to get restaurant data from Yelp.
    """)
    
    async for event in stream:
        yield event

if __name__ == "__main__":
    app.run()
```

**Single-Agent Implementation Benefits**:
- **Simplified Architecture**: No inter-agent communication complexity
- **Better Error Handling**: Single point of failure management
- **Faster Response Times**: No network overhead between agents
- **Easier Debugging**: Single execution context
- **Resource Efficiency**: Shared memory and processing
- **Consistent State**: Single agent maintains conversation context
- **Cost Effectiveness**: Single runtime instance reduces overhead

### 2. Search Tool Implementations

**Location**: `backend/src/tools/`

**Flight Search Tool**:
```python
from nova_act import NovaAct
from pydantic import BaseModel
from typing import List, Optional
import requests
import os

class FlightOption(BaseModel):
    departure_time: str
    arrival_time: str
    duration_minutes: int
    price_usd: float
    airline: str
    aircraft: str
    stops: int
    layover_info: Optional[List[str]] = None
    booking_url: Optional[str] = None
    cabin_class: str = "economy"

class FlightSearchResults(BaseModel):
    outbound_flights: List[FlightOption]
    return_flights: List[FlightOption] = []
    total_price_range: Dict[str, float]
    search_metadata: Dict

class FlightSearchTool:
    """Tool for searching flights using multiple sources"""
    
    def __init__(self):
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        self.cache_ttl = 3600  # 1 hour cache for flight prices
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        passengers: int = 1,
        cabin_class: str = "economy"
    ) -> FlightSearchResults:
        """
        Search for flights using Google Flights via SerpAPI
        
        Args:
            origin: IATA code or city name
            destination: IATA code or city name  
            departure_date: Date in YYYY-MM-DD format
            return_date: Return date if round trip
            passengers: Number of passengers
            cabin_class: Cabin class preference
            
        Returns:
            Flight search results
        """
        
        # Check cache first
        cache_key = self._generate_cache_key(
            origin, destination, departure_date, return_date, passengers
        )
        
        cached_results = await self._get_cached_results(cache_key)
        if cached_results:
            return FlightSearchResults(**cached_results)
        
        # Perform fresh search
        search_params = {
            "engine": "google_flights",
            "departure_id": self._resolve_airport_code(origin),
            "arrival_id": self._resolve_airport_code(destination),
            "outbound_date": departure_date,
            "return_date": return_date,
            "adults": passengers,
            "travel_class": self._map_cabin_class(cabin_class),
            "currency": "USD",
            "hl": "en",
            "api_key": self.serpapi_key
        }
        
        try:
            response = requests.get(
                "https://serpapi.com/search",
                params=search_params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            results = self._parse_flight_results(data)
            
            # Cache results
            await self._cache_results(cache_key, results.dict())
            
            return results
            
        except requests.RequestException as e:
            raise FlightSearchError(f"Flight search failed: {str(e)}")
    
    def _parse_flight_results(self, data: Dict) -> FlightSearchResults:
        """Parse SerpAPI response into structured results"""
        
        outbound_flights = []
        return_flights = []
        
        # Parse outbound flights
        if "best_flights" in data:
            for flight_data in data["best_flights"]:
                flight = self._parse_flight_option(flight_data)
                outbound_flights.append(flight)
        
        # Parse return flights if available
        if "return_flights" in data:
            for flight_data in data["return_flights"]:
                flight = self._parse_flight_option(flight_data)
                return_flights.append(flight)
        
        # Extract price range
        price_range = self._extract_price_range(data)
        
        return FlightSearchResults(
            outbound_flights=outbound_flights,
            return_flights=return_flights,
            total_price_range=price_range,
            search_metadata={
                "search_time": datetime.utcnow().isoformat(),
                "total_results": len(outbound_flights),
                "currency": "USD"
            }
        )
```

**Accommodation Search Tool (Nova Act)**:
```python
class AirbnbSearchTool:
    """Browser automation tool for Airbnb searches"""
    
    def __init__(self):
        self.base_url = "https://www.airbnb.com"
        self.rate_limiter = RateLimiter(max_calls=30, period=60)  # 30 calls per minute
    
    @rate_limiter.limit
    async def search_properties(
        self,
        location: str,
        check_in: str,
        check_out: str,
        guests: int = 2,
        price_range: Optional[Tuple[int, int]] = None
    ) -> PropertySearchResults:
        """
        Search Airbnb properties using browser automation
        
        Args:
            location: Location to search
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            guests: Number of guests
            price_range: Min/max price per night
            
        Returns:
            Property search results
        """
        
        try:
            with NovaAct(
                starting_page=self.base_url,
                headless=True,
                user_agent="TravelAgent/1.0 (NovaAct)"
            ) as nova:
                
                # Step 1: Navigate to search
                nova.act(f"Search for places to stay in {location}")
                
                # Step 2: Set dates
                nova.act(f"Set check-in date to {check_in}")
                nova.act(f"Set check-out date to {check_out}")
                
                # Step 3: Set guest count
                nova.act(f"Set number of guests to {guests}")
                
                # Step 4: Apply filters if specified
                if price_range:
                    min_price, max_price = price_range
                    nova.act(f"Set price filter from ${min_price} to ${max_price} per night")
                
                # Step 5: Extract results with schema validation
                result = nova.act(
                    """Extract property listings with the following information for each:
                    - Property title/name
                    - Price per night (as number)
                    - Overall rating (as number)
                    - Number of reviews
                    - Property type (entire place, private room, etc.)
                    - Key amenities list
                    - Neighborhood/location
                    - Image URL if visible
                    
                    Return data for first 20 listings found.""",
                    schema=PropertySearchResults.model_json_schema()
                )
                
                if result.matches_schema:
                    return PropertySearchResults.model_validate(result.parsed_response)
                else:
                    # Fallback parsing if schema validation fails
                    return self._fallback_parse_results(result.response)
                    
        except Exception as e:
            logger.error(f"Airbnb search failed: {str(e)}")
            raise AccommodationSearchError(f"Airbnb search error: {str(e)}")
    
    def _fallback_parse_results(self, raw_response: str) -> PropertySearchResults:
        """Fallback parsing when schema validation fails"""
        
        # Simple regex-based parsing as backup
        # This is a simplified example - real implementation would be more robust
        
        listings = []
        # Parse raw response using regex or other methods
        # ... implementation details ...
        
        return PropertySearchResults(
            listings=listings,
            total_found=len(listings),
            search_params={},
            metadata={
                "parsing_method": "fallback",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

### 3. Data Models and Schemas

**Location**: `backend/src/models/`

**Core Data Models**:
```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

class TravelRequestType(str, Enum):
    FLIGHT_ONLY = "flight_only"
    ACCOMMODATION_ONLY = "accommodation_only"
    COMPREHENSIVE = "comprehensive"
    ACTIVITY_PLANNING = "activity_planning"

class BudgetCategory(str, Enum):
    BUDGET = "budget"
    MID_RANGE = "mid_range"
    LUXURY = "luxury"
    UNLIMITED = "unlimited"

class TravelRequest(BaseModel):
    """User's travel request with all parameters"""
    
    destination: str = Field(..., description="Travel destination")
    origin: Optional[str] = Field(None, description="Origin location for flights")
    start_date: date = Field(..., description="Trip start date")
    end_date: date = Field(..., description="Trip end date")
    travelers: int = Field(default=1, ge=1, le=20, description="Number of travelers")
    budget_usd: Optional[float] = Field(None, ge=0, description="Total budget in USD")
    budget_category: BudgetCategory = Field(default=BudgetCategory.MID_RANGE)
    request_type: TravelRequestType = Field(default=TravelRequestType.COMPREHENSIVE)
    preferences: List[str] = Field(default_factory=list, description="User preferences")
    
    @validator('end_date')
    def end_date_after_start(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('preferences')
    def validate_preferences(cls, v):
        # Validate preference format and normalize
        normalized = []
        for pref in v:
            if isinstance(pref, str) and len(pref.strip()) > 0:
                normalized.append(pref.strip().lower())
        return normalized

class UserProfile(BaseModel):
    """Persistent user profile with preferences and history"""
    
    user_id: str = Field(..., description="Unique user identifier")
    preferences: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    past_trips: List['TripHistory'] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Preference subcategories
    accommodation_preferences: Dict[str, float] = Field(default_factory=dict)
    activity_preferences: Dict[str, float] = Field(default_factory=dict)
    dietary_restrictions: List[str] = Field(default_factory=list)
    mobility_requirements: List[str] = Field(default_factory=list)
    budget_patterns: Dict[str, float] = Field(default_factory=dict)
    
    def get_preference_weight(self, category: str, item: str) -> float:
        """Get preference weight for a specific item in a category"""
        category_prefs = getattr(self, f"{category}_preferences", {})
        return category_prefs.get(item, 0.5)  # Default neutral weight
    
    def update_preference(self, category: str, item: str, weight: float):
        """Update preference weight for an item"""
        category_attr = f"{category}_preferences"
        if hasattr(self, category_attr):
            prefs = getattr(self, category_attr)
            prefs[item] = max(0.0, min(1.0, weight))  # Clamp to [0,1]
            setattr(self, category_attr, prefs)
            self.last_updated = datetime.utcnow()

class SearchResult(BaseModel):
    """Base class for all search results"""
    
    id: str = Field(..., description="Unique result identifier")
    name: str = Field(..., description="Result name/title")
    price_usd: Optional[float] = Field(None, description="Price in USD")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Rating out of 5")
    source: str = Field(..., description="Data source platform")
    url: Optional[str] = Field(None, description="Booking/details URL")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
class FlightResult(SearchResult):
    """Flight search result"""
    
    airline: str
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    stops: int = Field(default=0)
    aircraft: Optional[str] = None
    cabin_class: str = Field(default="economy")
    
class AccommodationResult(SearchResult):
    """Accommodation search result"""
    
    property_type: str  # hotel, apartment, house, etc.
    location: str
    amenities: List[str] = Field(default_factory=list)
    capacity: int = Field(default=2)
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    cancellation_policy: Optional[str] = None

class ActivityResult(SearchResult):
    """Activity/attraction search result"""
    
    category: str  # sightseeing, entertainment, food, etc.
    duration_minutes: Optional[int] = None
    location: str
    description: Optional[str] = None
    opening_hours: Optional[Dict[str, str]] = None
    booking_required: bool = False
```

## Integration Specifications

### 1. API Gateway Configuration

**Location**: `cdk/lib/api-stack.ts`

**API Structure**:
```typescript
export class ApiStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps) {
    super(scope, id, props);
    
    // Main REST API
    const api = new RestApi(this, 'TravelAgentAPI', {
      restApiName: 'travel-agent-api',
      description: 'AI Travel Agent API',
      defaultCorsPreflightOptions: {
        allowOrigins: Cors.ALL_ORIGINS,
        allowMethods: Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'Authorization']
      }
    });
    
    // Authentication
    const authorizer = new CognitoUserPoolsAuthorizer(this, 'Authorizer', {
      cognitoUserPools: [userPool],
      identitySource: 'method.request.header.Authorization'
    });
    
    // API Resources and Methods
    this.setupChatEndpoints(api, authorizer);
    this.setupSearchEndpoints(api, authorizer);
    this.setupUserEndpoints(api, authorizer);
    this.setupItineraryEndpoints(api, authorizer);
  }
  
  private setupChatEndpoints(api: RestApi, authorizer: CognitoUserPoolsAuthorizer) {
    const chat = api.root.addResource('chat');
    
    // POST /chat - Send message to agent
    chat.addMethod('POST', new LambdaIntegration(chatHandler), {
      authorizer,
      methodResponses: [
        { statusCode: '200' },
        { statusCode: '400' },
        { statusCode: '500' }
      ]
    });
    
    // GET /chat/{conversationId}/history - Get conversation history
    const conversation = chat.addResource('{conversationId}');
    conversation.addResource('history').addMethod('GET', 
      new LambdaIntegration(historyHandler), { authorizer }
    );
  }
}
```

### 2. Lambda Handler Implementation

**Location**: `backend/src/handlers/`

**Main Chat Handler**:
```python
import json
import logging
from typing import Dict, Any
from agents.travel_planner import TravelPlannerAgent
from utils.response_formatter import format_api_response
from utils.error_handler import handle_lambda_error
from utils.auth import verify_jwt_token

logger = logging.getLogger(__name__)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for chat interactions
    
    Event structure:
    {
        "httpMethod": "POST",
        "headers": {"Authorization": "Bearer <token>"},
        "body": "{\"message\": \"Plan a trip to Paris\", \"conversationId\": \"uuid\"}"
    }
    """
    
    try:
        # Extract and validate request
        request_data = _extract_request_data(event)
        user_id = _extract_user_id(event)
        
        # Initialize agent for user
        agent = TravelPlannerAgent(
            user_id=user_id,
            session_config=_get_session_config(event)
        )
        
        # Process message with conversation context
        conversation_id = request_data.get('conversationId')
        message = request_data['message']
        
        # Handle different message types
        if _is_search_request(message):
            response = await agent.comprehensive_travel_search(**_extract_search_params(message))
        elif _is_refinement_request(message, request_data):
            response = agent.refine_recommendations(
                search_id=request_data.get('searchId'),
                feedback=request_data.get('feedback', {}),
                modifications=request_data.get('modifications')
            )
        else:
            # General conversation
            response = agent.process_message(message, conversation_id)
        
        # Format response for API
        return format_api_response(200, {
            "message": response.get("response", ""),
            "data": response.get("data", {}),
            "conversationId": conversation_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except ValidationError as e:
        return format_api_response(400, {"error": "Invalid request", "details": str(e)})
    except AuthenticationError as e:
        return format_api_response(401, {"error": "Authentication failed"})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return format_api_response(500, {"error": "Internal server error"})

def _extract_request_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and validate request data from Lambda event"""
    if not event.get('body'):
        raise ValidationError("Request body is required")
    
    try:
        return json.loads(event['body'])
    except json.JSONDecodeError:
        raise ValidationError("Invalid JSON in request body")

def _extract_user_id(event: Dict[str, Any]) -> str:
    """Extract user ID from JWT token in event"""
    auth_header = event.get('headers', {}).get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise AuthenticationError("Missing or invalid Authorization header")
    
    token = auth_header[7:]  # Remove 'Bearer ' prefix
    claims = verify_jwt_token(token)
    return claims['sub']  # User ID from Cognito
```

## Infrastructure Components

### 1. CDK Stack Definitions

**Location**: `cdk/lib/`

**Main Stack Structure**:
```typescript
export class TravelAgentStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps) {
    super(scope, id, props);
    
    // Core infrastructure stacks
    const authStack = new AuthStack(this, 'Auth', props);
    const apiStack = new ApiStack(this, 'API', {
      ...props,
      userPool: authStack.userPool
    });
    const computeStack = new ComputeStack(this, 'Compute', {
      ...props,
      api: apiStack.api
    });
    const storageStack = new StorageStack(this, 'Storage', props);
    const monitoringStack = new MonitoringStack(this, 'Monitoring', {
      ...props,
      lambda: computeStack.mainFunction
    });
  }
}
```

**Authentication Stack**:
```typescript
export class AuthStack extends Stack {
  public readonly userPool: cognito.UserPool;
  public readonly userPoolClient: cognito.UserPoolClient;
  
  constructor(scope: Construct, id: string, props: StackProps) {
    super(scope, id, props);
    
    // Cognito User Pool
    this.userPool = new cognito.UserPool(this, 'TravelAgentUsers', {
      userPoolName: 'travel-agent-users',
      selfSignUpEnabled: true,
      signInAliases: { email: true },
      autoVerify: { email: true },
      passwordPolicy: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: false
      },
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
      removalPolicy: RemovalPolicy.DESTROY // For development
    });
    
    // User Pool Client
    this.userPoolClient = new cognito.UserPoolClient(this, 'WebClient', {
      userPool: this.userPool,
      authFlows: {
        userSrp: true,
        userPassword: false // Disable less secure flow
      },
      generateSecret: false, // For web apps
      refreshTokenValidity: Duration.days(30),
      accessTokenValidity: Duration.hours(1),
      idTokenValidity: Duration.hours(1)
    });
    
    // Identity Pool for temporary AWS credentials
    const identityPool = new cognito.CfnIdentityPool(this, 'IdentityPool', {
      allowUnauthenticatedIdentities: false,
      cognitoIdentityProviders: [{
        clientId: this.userPoolClient.userPoolClientId,
        providerName: this.userPool.userPoolProviderName
      }]
    });
  }
}
```

### 2. Monitoring and Observability

**Location**: `backend/src/monitoring/`

**Metrics Collection System**:
```python
import boto3
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MetricData:
    name: str
    value: float
    unit: str
    dimensions: Dict[str, str]
    timestamp: Optional[datetime] = None

class MetricsCollector:
    """Centralized metrics collection for travel agent"""
    
    def __init__(self, namespace: str = "TravelAgent"):
        self.cloudwatch = boto3.client('cloudwatch')
        self.namespace = namespace
        self._batch_metrics = []
        self._batch_size = 20
    
    def record_search_latency(self, platform: str, duration_ms: float, success: bool):
        """Record search latency metrics"""
        self._add_metric(MetricData(
            name="SearchLatency",
            value=duration_ms,
            unit="Milliseconds",
            dimensions={
                "Platform": platform,
                "Status": "Success" if success else "Error"
            }
        ))
    
    def record_user_interaction(self, interaction_type: str, user_tier: str = "free"):
        """Record user interaction metrics"""
        self._add_metric(MetricData(
            name="UserInteraction",
            value=1,
            unit="Count",
            dimensions={
                "InteractionType": interaction_type,
                "UserTier": user_tier
            }
        ))
    
    def record_cost_metrics(self, model_id: str, tokens_used: int, cost_usd: float):
        """Record cost and token usage metrics"""
        self._add_metric(MetricData(
            name="TokensUsed",
            value=tokens_used,
            unit="Count",
            dimensions={"Model": model_id}
        ))
        
        self._add_metric(MetricData(
            name="ModelCost",
            value=cost_usd,
            unit="None",
            dimensions={"Model": model_id}
        ))
    
    def _add_metric(self, metric: MetricData):
        """Add metric to batch and flush if needed"""
        self._batch_metrics.append(metric)
        
        if len(self._batch_metrics) >= self._batch_size:
            self.flush_metrics()
    
    def flush_metrics(self):
        """Flush all batched metrics to CloudWatch"""
        if not self._batch_metrics:
            return
        
        metric_data = []
        for metric in self._batch_metrics:
            metric_data.append({
                'MetricName': metric.name,
                'Value': metric.value,
                'Unit': metric.unit,
                'Dimensions': [
                    {'Name': k, 'Value': v} 
                    for k, v in metric.dimensions.items()
                ],
                'Timestamp': metric.timestamp or datetime.utcnow()
            })
        
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metric_data
            )
            self._batch_metrics.clear()
        except Exception as e:
            logger.error(f"Failed to send metrics: {e}")
```

**Performance Monitoring Decorators**:
```python
import functools
import time
from typing import Callable, Any

def monitor_performance(metric_name: str, platform: Optional[str] = None):
    """Decorator to monitor function performance"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = True
            error = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = e
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                # Record metrics
                metrics = MetricsCollector()
                metrics.record_search_latency(
                    platform or func.__name__,
                    duration_ms,
                    success
                )
                
                if error:
                    logger.error(f"{metric_name} failed after {duration_ms:.2f}ms: {error}")
                else:
                    logger.info(f"{metric_name} completed in {duration_ms:.2f}ms")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # Similar implementation for sync functions
            pass
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

# Usage example
@monitor_performance("airbnb_search", "airbnb")
async def search_airbnb_properties(location: str, dates: tuple) -> PropertySearchResults:
    # Implementation here
    pass
```

## Security Specifications

### 1. Authentication and Authorization

**Location**: `backend/src/auth/`

**JWT Token Validation**:
```python
import jwt
import requests
from typing import Dict, Any
from functools import lru_cache

class JWTValidator:
    """JWT token validation for Cognito tokens"""
    
    def __init__(self, user_pool_id: str, region: str):
        self.user_pool_id = user_pool_id
        self.region = region
        self.issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    
    @lru_cache(maxsize=10)
    def _get_jwks(self) -> Dict[str, Any]:
        """Get JSON Web Key Set from Cognito"""
        jwks_url = f"{self.issuer}/.well-known/jwks.json"
        response = requests.get(jwks_url)
        response.raise_for_status()
        return response.json()
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and return claims
        
        Args:
            token: JWT token string
            
        Returns:
            Token claims if valid
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            # Get token header to find key ID
            header = jwt.get_unverified_header(token)
            kid = header['kid']
            
            # Find matching key in JWKS
            jwks = self._get_jwks()
            key = None
            for k in jwks['keys']:
                if k['kid'] == kid:
                    key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(k))
                    break
            
            if not key:
                raise AuthenticationError("Unable to find matching key")
            
            # Validate token
            claims = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": False  # We check token_use instead
                }
            )
            
            # Verify token use
            if claims.get('token_use') != 'access':
                raise AuthenticationError("Invalid token use")
            
            return claims
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
```

### 2. Input Validation and Sanitization

**Location**: `backend/src/validation/`

**Request Validators**:
```python
from pydantic import BaseModel, Field, validator
import re
from typing import List, Optional

class TravelSearchValidator(BaseModel):
    """Validator for travel search requests"""
    
    destination: str = Field(..., min_length=2, max_length=100)
    start_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    travelers: int = Field(default=1, ge=1, le=20)
    budget: Optional[float] = Field(None, ge=0, le=1000000)
    preferences: List[str] = Field(default_factory=list, max_items=20)
    
    @validator('destination')
    def validate_destination(cls, v):
        # Basic sanitization - remove potentially dangerous characters
        sanitized = re.sub(r'[<>\"\'&]', '', v.strip())
        if len(sanitized) < 2:
            raise ValueError('Destination too short after sanitization')
        return sanitized
    
    @validator('preferences')
    def validate_preferences(cls, v):
        # Sanitize preference strings
        sanitized = []
        for pref in v:
            clean_pref = re.sub(r'[<>\"\'&]', '', pref.strip())
            if len(clean_pref) > 0 and len(clean_pref) <= 50:
                sanitized.append(clean_pref)
        return sanitized[:20]  # Limit to 20 preferences

class PromptInjectionDetector:
    """Detect and prevent prompt injection attempts"""
    
    SUSPICIOUS_PATTERNS = [
        r'ignore\s+previous\s+instructions',
        r'system\s*:',
        r'assistant\s*:',
        r'###\s*instruction',
        r'<\s*system\s*>',
        r'jailbreak',
        r'pretend\s+you\s+are',
        r'roleplay\s+as'
    ]
    
    def __init__(self):
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.SUSPICIOUS_PATTERNS]
    
    def detect_injection(self, text: str) -> bool:
        """
        Check if text contains potential prompt injection
        
        Args:
            text: User input to check
            
        Returns:
            True if potential injection detected
        """
        text_lower = text.lower()
        
        for pattern in self.patterns:
            if pattern.search(text_lower):
                return True
        
        # Additional heuristics
        if self._has_excessive_instructions(text):
            return True
        
        if self._has_role_confusion(text):
            return True
        
        return False
    
    def _has_excessive_instructions(self, text: str) -> bool:
        """Check for excessive instruction-like language"""
        instruction_words = ['tell', 'say', 'respond', 'answer', 'act', 'pretend', 'imagine']
        word_count = sum(1 for word in instruction_words if word in text.lower())
        return word_count > 3 and len(text.split()) < 50  # High density of instruction words
    
    def _has_role_confusion(self, text: str) -> bool:
        """Check for attempts to confuse the AI's role"""
        role_patterns = [
            'you are now',
            'forget you are',
            'you must',
            'your new role'
        ]
        return any(pattern in text.lower() for pattern in role_patterns)
```

## Testing Specifications

### 1. Unit Test Framework

**Location**: `backend/tests/`

**Test Configuration**:
```python
import pytest
import asyncio
from unittest.mock import Mock, patch
from agents.travel_planner import TravelPlannerAgent
from tools.flight_search import FlightSearchTool

@pytest.fixture
def mock_bedrock_model():
    """Mock Bedrock model for testing"""
    with patch('strands_agents.models.BedrockModel') as mock:
        mock.return_value.generate.return_value = "Mocked response"
        yield mock

@pytest.fixture
def mock_memory():
    """Mock AgentCore memory for testing"""
    with patch('bedrock_agentcore.AgentCoreMemory') as mock:
        memory = Mock()
        memory.get_user_profile.return_value = None
        memory.store_user_profile.return_value = None
        mock.return_value = memory
        yield memory

@pytest.fixture
def travel_agent(mock_bedrock_model, mock_memory):
    """Create travel agent for testing"""
    return TravelPlannerAgent(user_id="test-user-123")

class TestTravelPlannerAgent:
    """Test suite for TravelPlannerAgent"""
    
    @pytest.mark.asyncio
    async def test_comprehensive_search_basic(self, travel_agent):
        """Test basic comprehensive search functionality"""
        
        # Mock search results
        with patch.object(travel_agent, 'search_tools') as mock_tools:
            mock_tools['flights'].search_flights.return_value = {
                "outbound_flights": [{"price": 300, "airline": "TestAir"}]
            }
            
            result = await travel_agent.comprehensive_travel_search(
                destination="Paris",
                start_date="2024-06-01",
                end_date="2024-06-07",
                travelers=2
            )
            
            assert "search_summary" in result
            assert result["search_summary"]["destination"] == "Paris"
            assert result["search_summary"]["travelers"] == 2
    
    def test_preference_combination(self, travel_agent):
        """Test user preference combination logic"""
        
        # Mock user profile with preferences
        user_profile = Mock()
        user_profile.accommodation_preferences = {"hotel": 0.8, "airbnb": 0.6}
        
        with patch.object(travel_agent.memory, 'get_user_profile', return_value=user_profile):
            stated_preferences = ["budget-friendly", "central location"]
            
            combined = travel_agent._combine_preferences(user_profile, stated_preferences)
            
            assert "budget-friendly" in combined["stated_preferences"]
            assert combined["accommodation_preferences"]["hotel"] == 0.8

class TestFlightSearchTool:
    """Test suite for FlightSearchTool"""
    
    @pytest.fixture
    def flight_tool(self):
        with patch.dict('os.environ', {'SERPAPI_KEY': 'test-key'}):
            return FlightSearchTool()
    
    @pytest.mark.asyncio
    async def test_flight_search_success(self, flight_tool):
        """Test successful flight search"""
        
        mock_response = {
            "best_flights": [{
                "flights": [{"departure_airport": {"id": "LAX"}}],
                "price": 299,
                "airline_logo": "airline.png"
            }]
        }
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status.return_value = None
            
            result = await flight_tool.search_flights(
                origin="LAX",
                destination="JFK", 
                departure_date="2024-06-01"
            )
            
            assert len(result.outbound_flights) > 0
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_flight_search_api_error(self, flight_tool):
        """Test flight search API error handling"""
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.raise_for_status.side_effect = requests.RequestException("API Error")
            
            with pytest.raises(FlightSearchError):
                await flight_tool.search_flights("LAX", "JFK", "2024-06-01")
```

### 2. Integration Test Suite

**Location**: `backend/tests/integration/`

**End-to-End Test**:
```python
import pytest
import json
from moto import mock_cognitoidp, mock_lambda
import boto3

@mock_cognitoidp
@mock_lambda
class TestTravelAgentAPI:
    """Integration tests for the complete API"""
    
    @pytest.fixture(autouse=True)
    def setup_aws_mocks(self):
        """Set up AWS service mocks"""
        
        # Mock Cognito
        self.cognito = boto3.client('cognito-idp', region_name='us-east-1')
        
        # Create mock user pool
        resp = self.cognito.create_user_pool(PoolName='test-pool')
        self.user_pool_id = resp['UserPool']['Id']
        
        # Mock Lambda
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    def test_chat_endpoint_authentication(self):
        """Test chat endpoint requires authentication"""
        
        event = {
            "httpMethod": "POST",
            "headers": {},
            "body": json.dumps({"message": "Plan a trip to Paris"})
        }
        
        # Should return 401 without auth header
        from handlers.chat_handler import lambda_handler
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 401
    
    def test_complete_travel_search_flow(self):
        """Test complete travel search workflow"""
        
        # Mock authenticated request
        event = {
            "httpMethod": "POST",
            "headers": {"Authorization": "Bearer valid-token"},
            "body": json.dumps({
                "message": "Find flights from NYC to Paris for 2 people in June",
                "conversationId": "test-conversation"
            }),
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "test-user-123"}
                }
            }
        }
        
        # Mock external API calls
        with patch('tools.flight_search.requests.get') as mock_flight_api:
            mock_flight_api.return_value.json.return_value = {
                "best_flights": [{"price": 500, "airline": "Air France"}]
            }
            
            from handlers.chat_handler import lambda_handler
            result = lambda_handler(event, {})
            
            assert result['statusCode'] == 200
            response_body = json.loads(result['body'])
            assert 'message' in response_body
            assert 'data' in response_body
```

This completes the comprehensive component specifications document. The documentation now covers all major aspects of the system from frontend components to backend services, infrastructure, security, and testing specifications.
