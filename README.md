# AI Travel Agent

An intelligent travel planning assistant that helps users find and book flights, accommodations, restaurants, and attractions using a combination of real-time APIs and browser automation.

## 📐 Architecture Overview

The AI Travel Agent uses a **single orchestrator agent** architecture built on AWS Bedrock AgentCore Runtime. This design provides better reliability, performance, and maintainability compared to multi-agent systems.

![Architecture Diagram](docs/Arch%20Diagram.png)

### Key Components

```
┌─────────────────────────────────────────┐
│       Frontend (React + TypeScript)     │
│    Direct HTTP to AgentCore Runtime     │◄──── User
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│    Travel Orchestrator Agent            │
│    (Single AgentCore Runtime)           │
│  ┌─────────────────────────────────┐    │
│  │  Integrated Tools:              │    │
│  │  • Amadeus Flight Search API    │    │
│  │  • Nova Act Browser Automation  │    │
│  │  • Google Maps API (Gateway)    │    │
│  │  • Memory & Authentication      │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
            │         │         │
            ▼         ▼         ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │Flights  │ │Accommod.│ │Maps API │
    │Amadeus  │ │Nova Act │ │Gateway  │
    └─────────┘ └─────────┘ └─────────┘
```

See [`docs/Arch Diagram.png`](docs/Arch%20Diagram.png) for the complete architecture visualization.

## 🚀 Quick Start

### Prerequisites

Before you begin, ensure you have:

#### Required Tools
- **AWS Account** with appropriate permissions (IAM, CloudFormation, Bedrock, etc.)
- **AWS CLI** v2.x configured with credentials (`aws configure`)
- **Node.js** 18+ and npm
- **Python** 3.11+
- **jq** (for JSON parsing in deployment scripts)
  - macOS: `brew install jq`
  - Ubuntu: `sudo apt-get install jq`
  - CentOS: `sudo yum install jq`

#### Required API Keys

1. **Amadeus Flight API**
   - Sign up at [developers.amadeus.com](https://developers.amadeus.com)
   - Free tier: 2,000 API calls/month
   - Get your Client ID and Client Secret

2. **Nova Act API**
   - Contact Nova Act team for API access
   - Used for browser automation (Airbnb, Booking.com)

3. **Google Maps Platform API**
   - Create project at [Google Cloud Console](https://console.cloud.google.com)
   - Enable these APIs:
     - Places API
     - Maps JavaScript API
     - Geocoding API
   - Create API key with restrictions

## 📋 Complete Deployment Guide

Follow these steps **in order** to deploy the complete system.

### Step 1: Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd travel-agent
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` with your credentials**
   ```bash
   # Open .env in your editor and fill in:
   # - AWS_PROFILE (your AWS CLI profile name)
   # - AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET
   # - NOVA_ACT_API_KEY
   # - GOOGLE_PLACES_API_KEY
   ```

4. **Load environment variables**
   ```bash
   source ./load-env.sh
   ```
   
   This will validate and load all required environment variables into your shell session.

### Step 2: Deploy AWS Infrastructure (CDK)

The CDK stack deploys:
- AWS Cognito (User Pool & Client) for authentication
- S3 buckets for frontend hosting and Gateway specs
- CloudFront distribution for global content delivery
- Gateway infrastructure for Google Maps integration

```bash
cd cdk

# Install dependencies
npm install

# Build the CDK project
npm run build

# Deploy the infrastructure
./deploy.sh dev  # or 'staging', 'production'

# Note: The script will output important values like:
# - CognitoUserPoolId
# - CognitoUserPoolClientId
# - FrontendBucketName
# - CloudFrontDistributionId
```

**What this creates:**
- Stack name: `TravelAgentStack-dev`
- Cognito User Pool for JWT authentication
- S3 bucket for frontend hosting
- CloudFront distribution for CDN
- S3 bucket for Gateway OpenAPI specifications

### Step 3: Configure Frontend Authentication

Generate the Amplify configuration file from CDK outputs:

```bash
cd cdk/scripts
./generate-amplify-config.sh dev

# This creates frontend/amplify_outputs.json with:
# - Cognito User Pool ID
# - Cognito Client ID
# - AWS Region
```

### Step 4: Deploy Travel Orchestrator Agent

This is the core of the system - the single agent that coordinates all travel planning.

```bash
cd agents/travel_orchestrator

# Ensure environment variables are loaded
source ../../load-env.sh

# Deploy the agent (this will take 5-10 minutes)
./deploy-travel-orchestrator.sh

# The script will:
# 1. Store API credentials in AWS Parameter Store
# 2. Set up Gateway with Google Maps integration
# 3. Create IAM execution role with required permissions
# 4. Configure JWT authentication with Cognito
# 5. Build and deploy agent to AgentCore Runtime
# 6. Output the agent HTTP endpoint URL
```

**Important:** Save the agent endpoint URL from the output - you'll need it for frontend configuration.

### Step 5: Configure Frontend Environment

After agent deployment, create the frontend environment file:

```bash
cd frontend

# Create .env.production with the agent endpoint
cat > .env.production << EOF
VITE_ENVIRONMENT=production
VITE_AGENT_CORE_URL=<AGENT_ENDPOINT_FROM_STEP_4>
VITE_COGNITO_USER_POOL_ID=<FROM_CDK_OUTPUT>
VITE_COGNITO_USER_POOL_CLIENT_ID=<FROM_CDK_OUTPUT>
VITE_COGNITO_REGION=us-east-1
EOF
```

### Step 6: Deploy Frontend

```bash
cd frontend

# Deploy frontend to S3 + CloudFront
./deploy-frontend.sh dev

# The script will:
# 1. Install dependencies
# 2. Build the React application
# 3. Upload to S3
# 4. Invalidate CloudFront cache
# 5. Output the frontend URL
```

**Your application is now live!** Access it at the CloudFront URL provided.

## 🧪 Testing & Verification

### Test Individual Components

**1. Test CDK Deployment**
```bash
aws cloudformation describe-stacks --stack-name TravelAgentStack-dev
```

**2. Test Agent Deployment**
```bash
cd agents/travel_orchestrator
agentcore status

# Or check via AWS CLI
aws ssm get-parameter --name /travel-agent/nova-act-api-key --with-decryption
```

**3. Test Frontend**
```bash
# Open your browser to the CloudFront URL
# Try signing up and signing in
# Check browser console for errors
```

### End-to-End Test

```bash
# Get a Cognito JWT token (after signing in via frontend)
# Then test the agent directly:
agentcore invoke \
  --bearer-token <YOUR_JWT_TOKEN> \
  '{"prompt": "Find flights from JFK to Paris for December 15-22, 2024"}'
```

## 🔧 Local Development

### Backend Development

```bash
cd agents/travel_orchestrator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Load environment variables
source ../../load-env.sh

# Test locally
python travel_orchestrator.py
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Create .env.development
cat > .env.development << EOF
VITE_ENVIRONMENT=development
VITE_AGENT_CORE_URL=http://localhost:8080
VITE_COGNITO_USER_POOL_ID=<FROM_CDK_OUTPUT>
VITE_COGNITO_USER_POOL_CLIENT_ID=<FROM_CDK_OUTPUT>
VITE_COGNITO_REGION=us-east-1
EOF

# Start development server
npm run dev

# Open http://localhost:5173
```

## 🏗️ Architecture Deep Dive

### Why Single Agent Architecture?

The Travel Orchestrator uses a **single agent with integrated tools** rather than multiple coordinating agents:

**Benefits:**
- ✅ Simpler architecture - no inter-agent communication
- ✅ Better error handling - single point of failure management
- ✅ Faster response times - no network overhead between agents
- ✅ Easier debugging - single execution context
- ✅ Resource efficiency - shared memory and processing
- ✅ Consistent state - single agent maintains conversation context

### Data Sources

| Service | Method | Data Type | Rate Limits |
|---------|--------|-----------|-------------|
| Amadeus API | REST API | Real-time flights | 2,000/month (free) |
| Google Maps | REST via Gateway | Restaurants/attractions | Google Cloud quotas |
| Airbnb | Browser Automation | Accommodations | Self-imposed: 1 req/2s |
| Booking.com | Browser Automation | Hotels | Self-imposed: 1 req/2s |

### Security Features

- **JWT Authentication**: Native Cognito integration with Bearer tokens
- **Isolated Execution**: Each session runs in isolated micro-VM
- **TLS 1.3 Encryption**: All communications encrypted
- **Secure Credentials**: API keys stored in AWS Parameter Store
- **Audit Trails**: Complete logging via CloudWatch

## 📚 Documentation

- [`docs/Arch Diagram.png`](docs/Arch%20Diagram.png) - **System architecture diagram (authoritative)**
- [`docs/00_PROJECT_OVERVIEW.md`](docs/00_PROJECT_OVERVIEW.md) - Project vision and goals
- [`docs/01_TECHNICAL_ARCHITECTURE.md`](docs/01_TECHNICAL_ARCHITECTURE.md) - Detailed technical architecture
- [`docs/02_IMPLEMENTATION_ROADMAP.md`](docs/02_IMPLEMENTATION_ROADMAP.md) - Development phases
- [`agents/travel_orchestrator/README.md`](agents/travel_orchestrator/README.md) - Agent documentation

## 🔑 Required API Keys Summary

### Amadeus Flight Search API
- **Purpose**: Real-time flight search and pricing
- **Signup**: [developers.amadeus.com](https://developers.amadeus.com)
- **Free Tier**: 2,000 requests/month
- **Environment Variables**: `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET`

### Nova Act API
- **Purpose**: Browser automation for accommodation search
- **Contact**: Nova Act team for API access
- **Usage**: Automated browsing of Airbnb and Booking.com
- **Environment Variable**: `NOVA_ACT_API_KEY`

### Google Maps Platform API
- **Purpose**: Restaurant and attraction recommendations
- **Setup**: [console.cloud.google.com](https://console.cloud.google.com)
- **Required APIs**: Places API, Maps JavaScript API, Geocoding API
- **Environment Variable**: `GOOGLE_PLACES_API_KEY`

### AWS Services
- **Bedrock AgentCore Runtime**: Agent execution and memory
- **Cognito**: User authentication
- **S3 + CloudFront**: Frontend hosting
- **Parameter Store**: Secure credential storage
- **Setup**: All configured automatically via CDK

## 🔍 Troubleshooting

### Common Issues

**1. CDK Deployment Fails**
```bash
# Check if CDK is bootstrapped
cdk bootstrap aws://ACCOUNT-ID/REGION

# Verify AWS credentials
aws sts get-caller-identity
```

**2. Agent Deployment Fails**
```bash
# Verify environment variables are loaded
echo $AMADEUS_CLIENT_ID
echo $NOVA_ACT_API_KEY
echo $GOOGLE_PLACES_API_KEY

# Check Parameter Store
aws ssm get-parameter --name /travel-agent/nova-act-api-key --with-decryption

# View agent logs
agentcore logs
```

**3. Frontend Can't Connect to Agent**
```bash
# Verify agent endpoint URL
agentcore status

# Check CORS configuration
# Ensure frontend domain is allowed in agent configuration

# Verify Cognito token is valid
# Check browser console for authentication errors
```

**4. Google Maps Tools Not Working**
```bash
# Verify Gateway deployment
aws ssm get-parameter --name /travel-agent/gateway-url

# Check Gateway S3 bucket
aws s3 ls s3://travel-agent-gateway-dev-<account>-<region>/
```

### Getting Help

1. Check the logs:
   ```bash
   # Agent logs
   agentcore logs
   
   # CloudWatch Logs
   aws logs tail /aws/bedrock-agentcore/runtimes/travel-orchestrator --follow
   ```

2. Review deployment outputs:
   ```bash
   # CDK outputs
   aws cloudformation describe-stacks --stack-name TravelAgentStack-dev
   
   # Agent status
   agentcore status --output json
   ```

3. Validate environment:
   ```bash
   # Show all loaded variables
   SHOW_LOADED_VARS=true source ./load-env.sh
   ```

## 📈 Performance

- **Flight Search**: ~3-5 seconds (Amadeus API)
- **Accommodation Search**: ~15-30 seconds (browser automation)
- **Restaurant Search**: ~2-3 seconds (Google Maps API)
- **Overall Response**: <45 seconds for comprehensive planning

## 💰 Cost Estimates

### Development Environment
- **AgentCore Runtime**: ~$0.10-0.15/hour (consumption-based)
- **Cognito**: Free tier (50,000 MAUs)
- **S3**: ~$0.50/month (frontend hosting)
- **CloudFront**: Free tier (1TB data transfer)
- **API Calls**: Free tiers for all APIs

### Production Scaling
- **AgentCore**: Scales automatically, pay per active session
- **CloudFront**: ~$0.085/GB after free tier
- **Cognito**: $0.0055 per MAU after free tier
- **API Costs**: Based on volume (see provider pricing)

## 🎯 Key Features

✅ **Implemented**
- Real-time flight search with pricing (Amadeus API)
- Accommodation search across Airbnb and Booking.com
- Restaurant and attraction recommendations (Google Maps)
- User authentication with Cognito JWT
- Responsive web interface with chat interaction
- Structured travel planning with itinerary generation
- Memory-based personalization
- Source attribution for all recommendations

🚧 **Future Enhancements**
- Advanced user preference learning
- Trip saving and sharing
- Multi-day itinerary optimization
- Direct booking integration
- Mobile app (React Native)

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
2. Review deployment scripts and their output
3. Check [troubleshooting section](#-troubleshooting)
4. Open an issue on GitHub

---

**Built with AWS Bedrock AgentCore Runtime** - Enterprise-grade AI agent platform
