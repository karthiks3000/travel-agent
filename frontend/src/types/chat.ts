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
  };
}

// Result types that can be returned by the agent
export type ResultType = 'flights' | 'accommodations' | 'restaurants' | 'itinerary';

// Base result data interface
export interface BaseResultData {
  type: ResultType;
  timestamp: Date;
  searchMetadata?: Record<string, any>;
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
  best_outbound_flight?: FlightResult;
  best_return_flight?: FlightResult;
  all_flights?: FlightResult[];
  search_params?: {
    origin: string;
    destination: string;
    departure_date: string;
    return_date?: string;
    passengers: number;
    cabin_class: string;
  };
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
    location_bias?: Record<string, any>;
    location_restriction?: Record<string, any>;
    price_levels?: string[];
    min_rating?: number;
    open_now?: boolean;
    included_type?: string;
    page_size?: number;
    page_token?: string;
  };
}

// Itinerary result data
export interface ItineraryItem {
  id: string;
  type: 'flight' | 'accommodation' | 'restaurant' | 'activity';
  date: string;
  time?: string;
  title: string;
  description: string;
  location?: string;
  details: FlightResult | PropertyResult | RestaurantResult | Record<string, any>;
}

export interface ItineraryData extends BaseResultData {
  type: 'itinerary';
  tripId: string;
  destination: string;
  startDate: string;
  endDate: string;
  travelers: number;
  items: ItineraryItem[];
}

// Union type for all result data
export type ResultData = 
  | FlightSearchResults 
  | AccommodationSearchResults 
  | RestaurantSearchResults 
  | ItineraryData;

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
  metadata?: Record<string, any>;
}

export interface AgentCoreResponse {
  message: string;
  sessionId: string;
  resultType?: ResultType;
  resultData?: ResultData;
  metadata?: Record<string, any>;
  error?: string;
}

// AgentCore client interface
export interface AgentCoreClient {
  invokeAgent: (request: AgentCoreRequest) => Promise<AgentCoreResponse>;
  healthCheck: () => Promise<boolean>;
}