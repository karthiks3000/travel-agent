# Design Document

## Overview

The Travel Agent Frontend is a React-based web application that provides users with an intuitive interface to interact with the travel orchestrator agent. The application features a modern, responsive design built with React 18, TypeScript, Tailwind CSS, and Aceternity UI components. Users can authenticate via AWS Cognito, engage in conversations with the travel agent through a split-panel chat interface, and view structured travel results in dedicated panels.

The application follows a single-page application (SPA) architecture with client-side routing, deployed as static assets on AWS S3 with CloudFront distribution for global content delivery.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   CloudFront    │    │    S3 Bucket     │    │   AWS Cognito       │
│   Distribution  │────│   Static Assets  │    │   User Pool         │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
         │                                               │
         │                                               │
         ▼                                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    React Frontend Application                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │  Landing Page   │  │  Auth Pages     │  │  Chat Interface     │ │
│  │  - Hero Section │  │  - Sign Up      │  │  - Split Layout     │ │
│  │  - Features     │  │  - Sign In      │  │  - Chat Panel       │ │
│  │  - CTA Buttons  │  │  - Cognito      │  │  - Results Panel    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
         │
         │ HTTPS API Calls
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AgentCore API                                  │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │              Travel Orchestrator Agent                          │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │ │
│  │  │Flight Agent │  │Hotel Agent  │  │  Restaurant Agent       │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Frontend Architecture Layers

1. **Presentation Layer**: React components with Aceternity UI and Tailwind CSS
2. **State Management Layer**: Zustand for global state, React Context for authentication
3. **Service Layer**: API clients for AgentCore and AWS Cognito integration
4. **Routing Layer**: React Router for client-side navigation
5. **Infrastructure Layer**: AWS S3 + CloudFront deployment via CDK

## Components and Interfaces

### Aceternity UI Component Library Integration

The application leverages Aceternity UI components for modern, animated interfaces:

#### Core Aceternity Components Used:
- **HeroParallax**: Landing page hero section with parallax scrolling
- **TextGenerateEffect**: Animated text reveals for marketing copy
- **BackgroundGradient**: Gradient backgrounds for sections
- **HoverEffect**: Interactive hover animations for cards
- **FloatingNav**: Sticky navigation with smooth transitions
- **Input**: Enhanced form inputs with floating labels and animations
- **Button**: Animated buttons with hover effects and loading states
- **Card**: Container components with subtle shadows and animations
- **Tabs**: Animated tab switching for result views
- **Table**: Enhanced tables with sorting and filtering
- **Badge**: Status indicators with color coding
- **Avatar**: User profile images with fallbacks
- **ScrollArea**: Custom scrollbars with smooth scrolling
- **Skeleton**: Loading placeholders with shimmer effects
- **Loader**: Animated loading spinners
- **Toast**: Notification system with slide animations

#### Custom Component Extensions:
- All Aceternity components will be wrapped in custom components for consistent theming
- Custom props added for travel-specific functionality
- Consistent color scheme and typography applied across all components

### Core Components

#### 1. Landing Page (`/`)
- **Purpose**: Marketing page to introduce the travel agent and drive user registration
- **Aceternity UI Components**:
  - `HeroParallax`: Main hero section with parallax scrolling effect
  - `TextGenerateEffect`: Animated text reveal for value proposition
  - `BackgroundGradient`: Gradient background for sections
  - `HoverEffect`: Interactive cards for features
  - `Button`: Primary and secondary CTA buttons
  - `FloatingNav`: Sticky navigation bar
- **Custom Components**:
  - `HeroSection`: Combines HeroParallax with TextGenerateEffect
  - `FeaturesGrid`: Grid layout using HoverEffect cards
  - `CTASection`: Call-to-action with animated buttons
  - `Footer`: Links and company information

#### 2. Authentication Pages
- **Sign Up Page (`/signup`)**:
  - **Aceternity UI Components**:
    - `Input`: Styled form inputs with floating labels
    - `Button`: Submit and navigation buttons
    - `Card`: Container for form content
    - `Label`: Form field labels
  - **Custom Components**:
    - `SignUpForm`: Email, password, name fields with Cognito integration
    - `FormValidation`: Real-time validation feedback
    - `EmailVerification`: Email verification flow handler
- **Sign In Page (`/signin`)**:
  - **Aceternity UI Components**:
    - `Input`: Email and password inputs
    - `Button`: Sign in and forgot password buttons
    - `Card`: Form container
    - `Checkbox`: Remember me functionality
  - **Custom Components**:
    - `SignInForm`: Authentication form with Cognito integration
    - `PasswordReset`: Password reset flow

#### 3. Chat Interface (`/chat`)
- **Layout**: Split-panel design with responsive breakpoints
- **Left Panel - Chat**:
  - **Aceternity UI Components**:
    - `ScrollArea`: Scrollable message history
    - `Input`: Message input field
    - `Button`: Send button
    - `Avatar`: User and agent avatars
    - `Card`: Message bubbles
    - `Skeleton`: Loading placeholders
  - **Custom Components**:
    - `ChatPanel`: Main chat container
    - `MessageList`: Scrollable conversation history
    - `MessageBubble`: Individual message component
    - `MessageInput`: Text input with send functionality
    - `TypingIndicator`: Agent processing indicator
- **Right Panel - Results**:
  - **Aceternity UI Components**:
    - `Tabs`: Switch between result types
    - `Table`: Flight and accommodation results
    - `Card`: Individual result cards
    - `Badge`: Price, rating, and status indicators
    - `Button`: Selection and action buttons
    - `ScrollArea`: Scrollable results
    - `Skeleton`: Loading states
  - **Custom Components**:
    - `ResultsPanel`: Dynamic content container
    - `FlightResultsView`: Flight search results table
    - `AccommodationResultsView`: Hotel/Airbnb cards grid
    - `RestaurantResultsView`: Restaurant listings
    - `ItineraryView`: Timeline-based trip overview

#### 4. Modular Component Architecture

**Shared UI Components**:
- `LoadingSpinner`: Using Aceternity's `Loader` component
- `ErrorBoundary`: Custom error handling with Aceternity styling
- `Toast`: Notifications using Aceternity's toast system
- `Modal`: Dialog components for confirmations
- `SearchFilters`: Reusable filter components for results
- `PriceDisplay`: Consistent price formatting
- `RatingDisplay`: Star ratings with Aceternity styling

**Layout Components**:
- `AppLayout`: Main application wrapper
- `AuthLayout`: Authentication pages wrapper
- `ChatLayout`: Split-panel chat interface
- `ResponsiveContainer`: Mobile-responsive containers

### State Management Architecture

#### Authentication State
```typescript
interface AuthState {
  user: CognitoUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  tokens: {
    accessToken: string;
    idToken: string;
    refreshToken: string;
  } | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshTokens: () => Promise<void>;
}
```

#### Chat State
```typescript
interface ChatState {
  sessionId: string;
  messages: Message[];
  currentResults: ResultData | null;
  resultType: 'flights' | 'accommodations' | 'restaurants' | 'itinerary' | null;
  isLoading: boolean;
  sendMessage: (content: string) => Promise<void>;
  clearSession: () => void;
}

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  timestamp: Date;
  metadata?: {
    resultType?: string;
    resultData?: any;
  };
}
```

### API Integration Interfaces

#### AgentCore Client
```typescript
interface AgentCoreClient {
  invokeAgent: (params: {
    sessionId: string;
    message: string;
    authToken: string;
  }) => Promise<AgentResponse>;
}

interface AgentResponse {
  message: string;
  resultType?: 'flights' | 'accommodations' | 'restaurants' | 'itinerary';
  resultData?: FlightResults | AccommodationResults | RestaurantResults | ItineraryData;
  sessionId: string;
}
```

#### AWS Cognito Integration
```typescript
interface CognitoService {
  signUp: (email: string, password: string, attributes: UserAttributes) => Promise<SignUpResult>;
  signIn: (email: string, password: string) => Promise<AuthenticationResult>;
  signOut: () => Promise<void>;
  getCurrentUser: () => Promise<CognitoUser | null>;
  refreshTokens: (refreshToken: string) => Promise<AuthenticationResult>;
}
```

## Data Models

### Result Data Types (Aligned with Backend Models)

#### Flight Results
```typescript
// Matches backend FlightResult and FlightSearchResults models
interface FlightResult {
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

interface FlightSearchResults {
  best_outbound_flight?: FlightResult;
  best_return_flight?: FlightResult;
  search_metadata: Record<string, any>;
  recommendation: string;
}

interface FlightSearchParams {
  origin: string;
  destination: string;
  departure_date: string; // YYYY-MM-DD
  return_date?: string; // YYYY-MM-DD
  passengers: number;
  cabin_class: string;
}
```

#### Accommodation Results
```typescript
// Matches backend PropertyResult and AccommodationAgentResponse models
interface PropertyResult {
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

interface AccommodationAgentResponse {
  best_accommodations: PropertyResult[];
  search_metadata: Record<string, any>;
  recommendation: string;
}

interface AccommodationSearchParams {
  location: string;
  check_in: string; // YYYY-MM-DD
  check_out: string; // YYYY-MM-DD
  guests: number;
  rooms: number;
  min_price?: number;
  max_price?: number;
  property_types: string[];
}
```

#### Restaurant Results
```typescript
// Matches backend RestaurantResult and RestaurantSearchResults models
interface RestaurantResult {
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

interface RestaurantSearchResults {
  restaurants: RestaurantResult[];
  total_results: number;
  search_metadata: Record<string, any>;
  next_page_token?: string;
  recommendation: string;
}

interface RestaurantSearchParams {
  text_query: string;
  location_bias?: Record<string, any>;
  location_restriction?: Record<string, any>;
  price_levels?: string[];
  min_rating?: number;
  open_now?: boolean;
  included_type?: string;
  page_size?: number;
  page_token?: string;
}
```

#### Itinerary Data
```typescript
interface ItineraryData {
  tripId: string;
  destination: string;
  startDate: string;
  endDate: string;
  travelers: number;
  items: ItineraryItem[];
}

interface ItineraryItem {
  id: string;
  type: 'flight' | 'accommodation' | 'restaurant' | 'activity';
  date: string;
  time?: string;
  title: string;
  description: string;
  location?: string;
  details: Flight | Hotel | Restaurant | Activity;
}
```

## Error Handling

### Error Types and Handling Strategy

#### 1. Authentication Errors
- **Cognito Errors**: Display user-friendly messages for common scenarios
- **Token Expiry**: Automatic refresh with fallback to re-authentication
- **Network Errors**: Retry mechanism with exponential backoff

#### 2. AgentCore API Errors
- **Service Unavailable**: Display maintenance message with retry option
- **Rate Limiting**: Queue requests and show appropriate feedback
- **Invalid Responses**: Graceful degradation with error boundaries

#### 3. UI Error Boundaries
```typescript
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

// Global error boundary wraps the entire application
// Page-level error boundaries for specific sections
// Component-level error boundaries for critical components
```

### Error Recovery Mechanisms
- **Automatic Retry**: For transient network errors
- **Fallback UI**: When components fail to render
- **Session Recovery**: Restore chat state after errors
- **Offline Support**: Basic functionality when network is unavailable

## Testing Strategy

### Testing Pyramid

#### 1. Unit Tests (70%)
- **Component Testing**: React Testing Library for UI components
- **Service Testing**: Mock API calls and test business logic
- **State Management**: Test Zustand stores in isolation
- **Utility Functions**: Test helper functions and data transformations

#### 2. Integration Tests (20%)
- **Authentication Flow**: End-to-end sign up/sign in processes
- **Chat Integration**: Message sending and result display
- **API Integration**: Mock AgentCore responses and test UI updates
- **Routing**: Navigation between pages and protected routes

#### 3. End-to-End Tests (10%)
- **Critical User Journeys**: Sign up → Chat → View Results
- **Cross-browser Testing**: Chrome, Firefox, Safari, Edge
- **Mobile Responsiveness**: Test on various device sizes
- **Performance Testing**: Load times and interaction responsiveness

### Testing Tools and Configuration
- **Jest**: Unit test runner with React Testing Library
- **Cypress**: End-to-end testing framework
- **MSW (Mock Service Worker)**: API mocking for tests
- **Testing Library**: Component testing utilities
- **Storybook**: Component development and visual testing

### Test Coverage Requirements
- **Minimum 80% code coverage** for critical paths
- **100% coverage** for authentication and payment flows
- **Visual regression testing** for UI components
- **Accessibility testing** with axe-core integration

## Deployment Architecture

### AWS CDK Infrastructure

#### S3 Bucket Configuration
```typescript
const websiteBucket = new s3.Bucket(this, 'TravelAgentWebsite', {
  bucketName: `travel-agent-frontend-${stage}`,
  websiteIndexDocument: 'index.html',
  websiteErrorDocument: 'index.html', // SPA routing
  publicReadAccess: false, // CloudFront only
  blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
  removalPolicy: cdk.RemovalPolicy.DESTROY,
});
```

#### CloudFront Distribution
```typescript
const distribution = new cloudfront.Distribution(this, 'Distribution', {
  defaultBehavior: {
    origin: new origins.S3Origin(websiteBucket, {
      originAccessIdentity: oai,
    }),
    viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
    cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
    compress: true,
  },
  defaultRootObject: 'index.html',
  errorResponses: [
    {
      httpStatus: 404,
      responseHttpStatus: 200,
      responsePagePath: '/index.html', // SPA routing
    },
  ],
});
```

#### AWS Cognito Configuration
```typescript
const userPool = new cognito.UserPool(this, 'TravelAgentUserPool', {
  userPoolName: `travel-agent-users-${stage}`,
  selfSignUpEnabled: true,
  signInAliases: {
    email: true,
  },
  passwordPolicy: {
    minLength: 8,
    requireLowercase: true,
    requireUppercase: true,
    requireDigits: true,
    requireSymbols: false,
  },
  accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
});

const userPoolClient = new cognito.UserPoolClient(this, 'TravelAgentUserPoolClient', {
  userPool,
  generateSecret: false, // For web applications
  authFlows: {
    userSrp: true,
    userPassword: false, // Disable for security
  },
});
```

### Build and Deployment Pipeline

#### Build Process
1. **TypeScript Compilation**: Compile TS to JS with type checking
2. **Asset Optimization**: Minify CSS/JS, optimize images
3. **Bundle Splitting**: Code splitting for optimal loading
4. **Environment Configuration**: Inject build-time environment variables

#### Deployment Steps
1. **Build Assets**: `npm run build` generates optimized static files
2. **Upload to S3**: Sync build output to S3 bucket
3. **Invalidate CloudFront**: Clear CDN cache for updated files
4. **Health Check**: Verify deployment accessibility

#### Environment Management
- **Development**: Local development with mock APIs
- **Staging**: Pre-production environment with real backend
- **Production**: Live environment with monitoring and alerts

### Performance Optimization

#### Bundle Optimization
- **Code Splitting**: Route-based and component-based splitting
- **Tree Shaking**: Remove unused code from bundles
- **Dynamic Imports**: Lazy load non-critical components
- **Asset Optimization**: Compress images and fonts

#### Caching Strategy
- **Static Assets**: Long-term caching with content hashing
- **API Responses**: Short-term caching for search results
- **Service Worker**: Offline support and background sync
- **CDN Configuration**: Optimal cache headers and compression

#### Performance Monitoring
- **Core Web Vitals**: LCP, FID, CLS tracking
- **Bundle Analysis**: Monitor bundle size growth
- **Runtime Performance**: Memory usage and rendering metrics
- **User Experience**: Real user monitoring (RUM)