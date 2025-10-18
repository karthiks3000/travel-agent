/**
 * TypeScript interfaces for chat functionality
 * Based on requirements 4.1, 9.1, and 10.1
 */

// Message interface
export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  timestamp: Date;
  metadata?: {
    resultType?: ResultType;
    resultData?: ResultData;
    sessionId?: string;
    error?: boolean;
    responseStatus?: ResponseStatus;
    responseType?: 'conversation' | 'flights' | 'accommodations' | 'restaurants' | 'attractions' | 'itinerary';
    toolProgress?: ToolProgress[];
    overallProgressMessage?: string;
    isFinalResponse?: boolean;
  };
}

// Response status indicators
export type ResponseStatus = 
  | 'requesting_info'           // Agent needs more details
  | 'validating'                // Checking provided info
  | 'thinking'                  // Agent is analyzing
  | 'calling_tools'             // Executing specialist agents
  | 'tool_in_progress'          // Individual tool running
  | 'processing_results'        // Combining results
  | 'partial_results'           // Some tools succeeded
  | 'complete_success'          // All requested data found
  | 'complete_with_recommendations' // Results + suggestions
  | 'tool_error'                // Specialist agent failed
  | 'validation_error'          // Invalid input provided
  | 'system_error';             // General system failure

// Enhanced response types
export type ResponseType = 
  | 'conversation'      // Simple Q&A, validation errors, clarifications
  | 'flights'           // Flight search results only
  | 'accommodations'    // Accommodation search results only
  | 'restaurants'       // Restaurant search results only
  | 'attractions'       // Attraction search results only
  | 'mixed_results'     // Multiple component types
  | 'itinerary';        // Complete travel plan with multiple components

// Tool progress tracking
export interface ToolProgress {
  tool_id: string;              // Internal tool identifier
  display_name: string;         // User-friendly tool name
  description: string;          // Detailed description of what the tool is doing
  status: 'pending' | 'active' | 'completed' | 'failed';
  result_preview?: string;      // Brief preview of results if completed
  error_message?: string;       // Error details if status is failed
}

// Result types that can be returned by the agent
export type ResultType = 'flights' | 'accommodations' | 'restaurants' | 'attractions' | 'itinerary';

// Base result data interface
export interface BaseResultData {
  type: ResultType;
  timestamp: Date;
  searchMetadata?: Record<string, unknown>;
  recommendation?: string;
}

// Flight result data (aligned with backend models)
export interface FlightResult {
  airline: string;
  departure_time: string;
  arrival_time: string;
  departure_airport: string;
  arrival_airport: string;
  price: number; // USD
  duration: string;
  stops: number;
  stop_details?: string;
  booking_class: string;
}

export interface FlightSearchResults extends BaseResultData {
  type: 'flights';
  flights: FlightResult[];
  search_metadata?: Record<string, unknown>;
}

// Accommodation result data (aligned with backend models)
export interface PropertyResult {
  platform: string; // 'airbnb' | 'booking_com'
  title?: string;
  price_per_night?: number; // USD
  total_price?: number; // USD
  rating?: number;
  review_count?: number;
  property_type?: string;
  host_name?: string;
  amenities?: string[];
  location?: string;
  url?: string;
  image_url?: string;
  guests_capacity?: number;
  bedrooms?: number;
  bathrooms?: number;
}

export interface AccommodationSearchResults extends BaseResultData {
  type: 'accommodations';
  best_accommodations: PropertyResult[];
  search_params?: {
    location: string;
    check_in: string;
    check_out: string;
    guests: number;
    rooms: number;
    min_price?: number;
    max_price?: number;
    property_types: string[];
  };
}

// Restaurant result data (aligned with backend models)
export interface RestaurantResult {
  name: string;
  address: string;
  rating?: number; // 0.0 to 5.0
  user_rating_count?: number;
  price_level?: string; // 'PRICE_LEVEL_INEXPENSIVE' | 'PRICE_LEVEL_MODERATE' | etc.
  phone_number?: string;
  website_uri?: string;
  is_open_now?: boolean;
  types: string[]; // ['restaurant', 'italian_restaurant', etc.]
  place_id?: string;
}

export interface RestaurantSearchResults extends BaseResultData {
  type: 'restaurants';
  restaurants: RestaurantResult[];
  total_results: number;
  next_page_token?: string;
  search_params?: {
    text_query: string;
    location_bias?: Record<string, unknown>;
    location_restriction?: Record<string, unknown>;
    price_levels?: string[];
    min_rating?: number;
    open_now?: boolean;
    included_type?: string;
    page_size?: number;
    page_token?: string;
  };
}

// Attraction result data (new)
export interface AttractionResult {
  name: string;
  place_id: string;
  formatted_address: string;
  rating?: number;
  user_ratings_total?: number;
  price_level?: number; // 0-4
  types: string[];
  opening_hours?: Record<string, unknown>;
  website?: string;
  phone_number?: string;
  photos?: Record<string, unknown>[];
  geometry?: Record<string, unknown>;
  visit_duration_estimate?: number; // minutes
}

export interface AttractionSearchResults extends BaseResultData {
  type: 'attractions';
  attractions: AttractionResult[];
  total_results: number;
  search_params?: {
    location: string;
    attraction_types?: string[];
    max_results: number;
  };
}

// Enhanced itinerary models matching backend
export type ActivityType = 
  | 'flight' 
  | 'accommodation' 
  | 'restaurant' 
  | 'attraction' 
  | 'transportation' 
  | 'general';

export interface TimeSlot {
  start_time: string; // HH:MM format
  end_time?: string;
  duration_minutes?: number;
}

export interface TransportationActivity {
  mode: string; // 'train' | 'bus' | 'taxi' | 'uber' | 'walking' | 'metro'
  from_location: string;
  to_location: string;
  provider?: string;
  cost_estimate?: number;
  notes?: string;
}

export interface GeneralActivity {
  title: string;
  description?: string;
  location?: string;
  cost_estimate?: number;
  notes?: string;
}

export interface ItineraryActivity {
  time_slot: TimeSlot;
  activity_type: ActivityType;
  title: string;
  activity_details: FlightResult | PropertyResult | RestaurantResult | AttractionResult | TransportationActivity | GeneralActivity;
  notes?: string;
}

export interface DailyItinerary {
  day_number: number;
  date: string; // YYYY-MM-DD format
  location: string;
  daily_summary: string;
  activities: ItineraryActivity[];
  estimated_daily_cost?: number;
  weather_info?: string;
}

export interface TravelItinerary {
  trip_title: string;
  destination: string;
  start_date: string; // YYYY-MM-DD format
  end_date: string;   // YYYY-MM-DD format
  total_days: number;
  traveler_count: number;
  daily_itineraries: DailyItinerary[];
  total_estimated_cost?: number;
  trip_summary: string;
  packing_suggestions?: string[];
  travel_tips?: string[];
  created_at: string;
  last_updated: string;
}

// Union type for all result data
export type ResultData = 
  | FlightSearchResults 
  | AccommodationSearchResults 
  | RestaurantSearchResults
  | AttractionSearchResults 
  | (TravelItinerary & BaseResultData);

// Chat session interface
export interface ChatSession {
  id: string;
  createdAt: Date;
  lastActivity: Date;
  messageCount: number;
}

// Chat state interface for Zustand store
export interface ChatState {
  // Session management
  sessionId: string;
  isSessionActive: boolean;
  
  // Messages
  messages: Message[];
  
  // Results
  currentResults: ResultData | null;
  resultType: ResultType | null;
  
  // Loading states
  isLoading: boolean;
  isSending: boolean;
  
  // Streaming states
  streamingMessage: string | null;
  isStreaming: boolean;
  streamingMessageId: string | null;
  
  // Tool progress states
  thinkingMessage: string | null;
  toolProgress: ToolProgress[];
  
  // Error handling
  error: string | null;
}

// Chat store interface with actions
export interface ChatStore extends ChatState {
  // Message actions
  sendMessage: (content: string) => Promise<void>;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  
  // Session actions
  startNewSession: () => void;
  endSession: () => void;
  clearSession: () => void;
  
  // Result actions
  setResults: (results: ResultData) => void;
  clearResults: () => void;
  
  // Error actions
  setError: (error: string | null) => void;
  clearError: () => void;
  
  // Loading actions
  setLoading: (loading: boolean) => void;
  setSending: (sending: boolean) => void;
}

// AgentCore API interfaces
export interface AgentCoreRequest {
  sessionId: string;
  message: string;
  authToken: string;
  metadata?: Record<string, unknown>;
}

export interface AgentCoreResponse {
  // Core response fields
  message: string;
  sessionId?: string;
  success: boolean;
  error?: string;
  
  // Orchestrator response fields
  response_type: 'conversation' | 'flights' | 'accommodations' | 'restaurants' | 'attractions' | 'itinerary';
  response_status: ResponseStatus;
  overall_progress_message: string;
  is_final_response: boolean;
  next_expected_input_friendly?: string;
  
  // Tool progress tracking
  tool_progress: ToolProgress[];
  
  // Structured results from specialist agents
  flight_results?: FlightResult[];
  accommodation_results?: PropertyResult[];
  restaurant_results?: RestaurantResult[];
  attraction_results?: AttractionResult[];
  itinerary?: TravelItinerary;
  
  // Additional metadata
  processing_time_seconds?: number;
  estimated_costs?: Record<string, number>;
  recommendations?: Record<string, unknown>;
  session_metadata?: Record<string, string>;
}

// AgentCore client interface
export interface AgentCoreClient {
  invokeAgent: (
    request: AgentCoreRequest,
    onStreamChunk?: (chunk: string, isThinking: boolean) => void
  ) => Promise<AgentCoreResponse>;
  healthCheck: () => Promise<boolean>;
}
