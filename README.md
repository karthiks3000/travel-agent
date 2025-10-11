# AI Travel Agent

An intelligent travel planning assistant that helps users find and book flights, accommodations, restaurants, and attractions using a combination of real-time APIs and browser automation.

## 🚀 Quick Start

### Prerequisites
- AWS Account with appropriate permissions
- Node.js 18+ and npm
- Python 3.11+
- Valid API keys (see Setup section)

### 1. Deploy Infrastructure
```bash
# Deploy AWS infrastructure
cd cdk
npm install
npm run deploy
```

### 2. Configure Environment
```bash
# Set up API credentials in AWS Systems Manager Parameter Store
aws ssm put-parameter --name "/travel-agent/amadeus-client-id" --value "your-amadeus-client-id" --type "SecureString"
aws ssm put-parameter --name "/travel-agent/amadeus-client-secret" --value "your-amadeus-client-secret" --type "SecureString"
aws ssm put-parameter --name "/travel-agent/nova-act-api-key" --value "your-nova-act-api-key" --type "SecureString"
aws ssm put-parameter --name "/travel-agent/google-places-api-key" --value "google-places-api-key" --type "SecureString"

```

### 3. Deploy Travel Agent
```bash
# Deploy the travel orchestrator agent
cd agents/travel_orchestrator
./deploy-travel-orchestrator.sh
```

### 4. Deploy Frontend
```bash
# Build and deploy React frontend
cd frontend
./deploy-frontend.sh
```

## 🏗️ Architecture Overview

The AI Travel Agent uses a **single orchestrator agent** architecture built on AWS Bedrock AgentCore Runtime:

```
┌─────────────────────────────────────────┐
│           Frontend (React)              │
│    ┌─────────────────────────────────┐  │
│    │   Direct HTTP Connection to     │  │◄─── User
│    │   AgentCore Runtime             │  │
│    └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│      Travel Orchestrator Agent         │
│       (Single AgentCore Runtime)       │
│  ┌─────────────────────────────────────┐│
│  │    Integrated Tools:                ││
│  │  • Amadeus Flight Search API       ││
│  │  • Nova Act (Airbnb/Booking.com)   ││
│  │  • Google Maps API (via Gateway)   ││
│  │  • Memory & Authentication         ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

## 🔧 Core Components

### Travel Orchestrator Agent
- **Single agent** handling all travel planning tasks
- **Direct integrations** with multiple data sources
- **Real-time responses** with structured JSON output
- **Memory integration** for personalized recommendations

### Data Sources
1. **Flights**: Amadeus Flight Offers Search API (real-time pricing)
2. **Accommodations**: Nova Act browser automation (Airbnb + Booking.com)
3. **Restaurants/Attractions**: Google Maps API via AgentCore Gateway
4. **Authentication**: AWS Cognito with JWT tokens

### Frontend Application
- **React 18** with TypeScript
- **TailwindCSS** + Aceternity UI components
- **Real-time chat interface** with travel planning
- **Direct AgentCore Runtime** communication

## 📋 Key Features

✅ **Implemented**
- Flight search with real-time pricing (Amadeus API)
- Accommodation search across Airbnb and Booking.com
- Restaurant and attraction recommendations (Google Maps)
- User authentication and session management
- Responsive web interface with chat-based interaction
- Structured travel planning with itinerary generation

🚧 **In Development**
- Advanced personalization with user preferences
- Trip saving and sharing functionality
- Multi-day itinerary optimization
- Booking integration

## 🛠️ Development

### Local Development Setup

1. **Backend Development**:
```bash
cd agents/travel_orchestrator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export AMADEUS_CLIENT_ID="your-client-id"
export AMADEUS_CLIENT_SECRET="your-client-secret"
export NOVA_ACT_API_KEY="your-api-key"
export GOOGLE_PLACES_API_KEY="google-api-key"

# Test locally
python travel_orchestrator.py
```

2. **Frontend Development**:
```bash
cd frontend
npm install
npm run dev
```

3. **Infrastructure Development**:
```bash
cd cdk
npm install
npm run build
npm run deploy
```

### Testing

```bash
# Test flight search
cd agents/travel_orchestrator
python -c "
from tools.flight_search_tool import search_flights_direct
result = search_flights_direct('JFK', 'CDG', '2024-12-15', '2024-12-22', 2)
print(result.message)
"

# Test accommodation search
python -c "
from tools.accommodation_search_tool import search_accommodations_direct
result = search_accommodations_direct('Paris', '2024-12-15', '2024-12-22', 2, 1)
print(result.message)
"
```

## 📚 Documentation

- [`docs/00_PROJECT_OVERVIEW.md`](docs/00_PROJECT_OVERVIEW.md) - Project vision and goals
- [`docs/01_TECHNICAL_ARCHITECTURE.md`](docs/01_TECHNICAL_ARCHITECTURE.md) - Detailed technical architecture
- [`docs/02_IMPLEMENTATION_ROADMAP.md`](docs/02_IMPLEMENTATION_ROADMAP.md) - Development phases and milestones
- [`docs/FRONTEND_DEPLOYMENT.md`](docs/FRONTEND_DEPLOYMENT.md) - Frontend deployment guide
- [`agents/travel_orchestrator/README.md`](agents/travel_orchestrator/README.md) - Agent-specific documentation

## 🔑 Required API Keys

### Amadeus Flight Search API
- **Purpose**: Real-time flight search and pricing
- **Signup**: [developers.amadeus.com](https://developers.amadeus.com)
- **Free Tier**: 2,000 requests/month

### Nova Act API
- **Purpose**: Browser automation for accommodation search
- **Contact**: Nova Act team for API access
- **Usage**: Automated browsing of Airbnb and Booking.com

### AWS Services
- **Bedrock AgentCore Runtime**: Agent execution and memory
- **Cognito**: User authentication
- **S3 + CloudFront**: Frontend hosting
- **Systems Manager**: Secure credential storage

## 🌐 Deployment

The application is designed for AWS deployment:

1. **AgentCore Runtime**: Hosts the travel orchestrator agent
2. **S3 + CloudFront**: Hosts the React frontend
3. **Cognito**: Manages user authentication
4. **Parameter Store**: Stores API credentials securely

See individual deployment scripts in each directory for detailed instructions.

## 📈 Performance

- **Flight Search**: ~3-5 seconds (Amadeus API)
- **Accommodation Search**: ~15-30 seconds (browser automation)
- **Restaurant Search**: ~2-3 seconds (Google Maps API)
- **Overall Response**: <45 seconds for comprehensive planning

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
1. Check the documentation in the `docs/` directory
2. Review deployment scripts and logs
3. Open an issue on GitHub


