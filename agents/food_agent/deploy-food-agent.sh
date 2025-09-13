#!/bin/bash
set -e

# Food Agent Deployment Script
# Automates Parameter Store setup and AgentCore deployment

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_PROFILE="bookhood"
PARAMETER_NAME="/travel-agent/google-places-api-key"
AGENT_NAME="food_agent"

# Get AWS account ID and region dynamically
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile $AWS_PROFILE)
REGION=$(aws configure get region --profile $AWS_PROFILE)

# Fallback to us-east-1 if region not configured
if [[ -z "$REGION" ]]; then
    REGION="us-east-1"
    print_warning "No region configured in AWS profile, using default: $REGION"
fi

echo -e "${BLUE}🍽️  Food Agent Deployment Script${NC}"
echo -e "${BLUE}=================================${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Prerequisites Check
echo -e "\n${BLUE}Step 1: Checking Prerequisites${NC}"
echo "----------------------------------------"

# Check if running from correct directory
if [[ ! -f "food_agent.py" ]]; then
    print_error "Please run this script from the agents/food_agent directory"
    exit 1
fi

# Check AWS CLI with bookhood profile
if ! aws sts get-caller-identity --profile $AWS_PROFILE >/dev/null 2>&1; then
    print_error "AWS CLI not configured with profile '$AWS_PROFILE'"
    echo "Run: aws configure --profile $AWS_PROFILE"
    exit 1
fi
print_status "AWS CLI configured with profile '$AWS_PROFILE'"
print_status "Account ID: $ACCOUNT_ID | Region: $REGION"

# Check AgentCore CLI
if ! command -v agentcore >/dev/null 2>&1; then
    print_error "AgentCore CLI not installed"
    echo "Install from: https://github.com/aws/bedrock-agentcore"
    exit 1
fi
print_status "AgentCore CLI installed"

# Check Docker functionality (not just installation)
if command -v docker >/dev/null 2>&1; then
    # Test if Docker is actually running and functional
    if docker info >/dev/null 2>&1; then
        print_status "Docker is running and functional"
        
        # Check for corporate VPN/SSL certificate issues
        if [[ -n "$CURL_CA_BUNDLE" ]] || [[ -n "$REQUESTS_CA_BUNDLE" ]]; then
            print_warning "Corporate SSL certificates detected - may cause Docker build issues"
            print_warning "If build fails, will automatically fallback to CodeBuild"
        fi
        
        USE_LOCAL_BUILD=true
    else
        print_warning "Docker installed but not running properly - will use CodeBuild"
        print_warning "To fix: Start Docker service or Docker Desktop"
        USE_LOCAL_BUILD=false
    fi
else
    print_warning "Docker not found - will use CodeBuild (cloud-based building)"
    USE_LOCAL_BUILD=false
fi

# Check Google Places API Key
if [[ -z "$GOOGLE_PLACES_API_KEY" ]]; then
    print_error "GOOGLE_PLACES_API_KEY environment variable not set"
    echo "Set it with: export GOOGLE_PLACES_API_KEY='your_api_key_here'"
    exit 1
fi
print_status "Google Places API key found in environment"

# Step 2: Setup Parameter Store
echo -e "\n${BLUE}Step 2: Setting up AWS Parameter Store${NC}"
echo "------------------------------------------------"

# Store API key in Parameter Store
if aws ssm put-parameter \
    --name "$PARAMETER_NAME" \
    --value "$GOOGLE_PLACES_API_KEY" \
    --type "SecureString" \
    --overwrite \
    --profile $AWS_PROFILE \
    --region $REGION >/dev/null 2>&1; then
    print_status "API key stored in Parameter Store: $PARAMETER_NAME"
else
    print_error "Failed to store API key in Parameter Store"
    exit 1
fi

# Verify parameter was created
if aws ssm get-parameter \
    --name "$PARAMETER_NAME" \
    --profile $AWS_PROFILE \
    --region $REGION >/dev/null 2>&1; then
    print_status "Parameter Store setup verified"
else
    print_error "Parameter Store verification failed"
    exit 1
fi

# Step 3: Create Custom IAM Role with All Permissions
echo -e "\n${BLUE}Step 3: Setting up IAM Role${NC}"
echo "-------------------------------------------"

IAM_ROLE_NAME="FoodAgentExecutionRole"
IAM_TRUST_POLICY='{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock-agentcore.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}'

IAM_ROLE_POLICY=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ECRImageAccess",
            "Effect": "Allow",
            "Action": [
                "ecr:BatchGetImage",
                "ecr:GetDownloadUrlForLayer"
            ],
            "Resource": [
                "arn:aws:ecr:${REGION}:${ACCOUNT_ID}:repository/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:DescribeLogStreams",
                "logs:CreateLogGroup"
            ],
            "Resource": [
                "arn:aws:logs:${REGION}:${ACCOUNT_ID}:log-group:/aws/bedrock-agentcore/runtimes/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:DescribeLogGroups"
            ],
            "Resource": [
                "arn:aws:logs:${REGION}:${ACCOUNT_ID}:log-group:*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:${REGION}:${ACCOUNT_ID}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
            ]
        },
        {
            "Sid": "ECRTokenAccess",
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "xray:PutTraceSegments",
                "xray:PutTelemetryRecords",
                "xray:GetSamplingRules",
                "xray:GetSamplingTargets"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Effect": "Allow",
            "Resource": "*",
            "Action": "cloudwatch:PutMetricData",
            "Condition": {
                "StringEquals": {
                    "cloudwatch:namespace": "bedrock-agentcore"
                }
            }
        },
        {
            "Sid": "BedrockAgentCoreRuntime",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:InvokeAgentRuntime"
            ],
            "Resource": [
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:runtime/*"
            ]
        },
        {
            "Sid": "BedrockAgentCoreMemoryCreateMemory",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:CreateMemory"
            ],
            "Resource": "*"
        },
        {
            "Sid": "BedrockAgentCoreMemory",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:CreateEvent",
                "bedrock-agentcore:GetEvent",
                "bedrock-agentcore:GetMemory",
                "bedrock-agentcore:GetMemoryRecord",
                "bedrock-agentcore:ListActors",
                "bedrock-agentcore:ListEvents",
                "bedrock-agentcore:ListMemoryRecords",
                "bedrock-agentcore:ListSessions",
                "bedrock-agentcore:DeleteEvent",
                "bedrock-agentcore:DeleteMemoryRecord",
                "bedrock-agentcore:RetrieveMemoryRecords"
            ],
            "Resource": [
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:memory/*"
            ]
        },
        {
            "Sid": "BedrockAgentCoreIdentityGetResourceApiKey",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:GetResourceApiKey"
            ],
            "Resource": [
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:token-vault/default",
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:token-vault/default/apikeycredentialprovider/*",
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default",
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default/workload-identity/food_agent-*"
            ]
        },
        {
            "Sid": "BedrockAgentCoreIdentityGetResourceOauth2Token",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:GetResourceOauth2Token"
            ],
            "Resource": [
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:token-vault/default",
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:token-vault/default/oauth2credentialprovider/*",
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default",
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default/workload-identity/food_agent-*"
            ]
        },
        {
            "Sid": "BedrockAgentCoreIdentityGetWorkloadAccessToken",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:GetWorkloadAccessToken",
                "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                "bedrock-agentcore:GetWorkloadAccessTokenForUserId"
            ],
            "Resource": [
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default",
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default/workload-identity/food_agent-*"
            ]
        },
        {
            "Sid": "BedrockModelInvocation",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:ApplyGuardrail"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/*",
                "arn:aws:bedrock:${REGION}:${ACCOUNT_ID}:*"
            ]
        },
        {
            "Sid": "ParameterStoreAccess",
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter"
            ],
            "Resource": [
                "arn:aws:ssm:*:*:parameter/travel-agent/*"
            ]
        }
    ]
}
EOF
)

# Create IAM role (ignore error if already exists)
aws iam create-role \
    --role-name $IAM_ROLE_NAME \
    --assume-role-policy-document "$IAM_TRUST_POLICY" \
    --profile $AWS_PROFILE >/dev/null 2>&1 || true

# Attach the comprehensive policy to the role
aws iam put-role-policy \
    --role-name $IAM_ROLE_NAME \
    --policy-name "FoodAgentExecutionPolicy" \
    --policy-document "$IAM_ROLE_POLICY" \
    --profile $AWS_PROFILE >/dev/null 2>&1

# Construct the role ARN
EXECUTION_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${IAM_ROLE_NAME}"

print_status "IAM role created/updated: $IAM_ROLE_NAME"
print_status "Role ARN: $EXECUTION_ROLE_ARN"

# Step 4: AgentCore Configuration
echo -e "\n${BLUE}Step 4: Configuring AgentCore Agent${NC}"
echo "--------------------------------------------"

# Configure agent (with or without container runtime based on availability)
if [[ "$USE_LOCAL_BUILD" == "true" ]]; then
    # Configure with Docker for local builds and custom execution role
    if agentcore configure \
        --entrypoint food_agent.py \
        --name $AGENT_NAME \
        --execution-role "$EXECUTION_ROLE_ARN" \
        --container-runtime docker \
        --requirements-file requirements.txt \
        --region $REGION; then
        print_status "AgentCore agent configured with Docker and custom IAM role: $AGENT_NAME"
    else
        print_error "AgentCore configuration failed"
        exit 1
    fi
else
    # Configure without container runtime for CodeBuild but with custom execution role
    if agentcore configure \
        --entrypoint food_agent.py \
        --name $AGENT_NAME \
        --execution-role "$EXECUTION_ROLE_ARN" \
        --requirements-file requirements.txt \
        --region $REGION; then
        print_status "AgentCore agent configured for CodeBuild with custom IAM role: $AGENT_NAME"
    else
        print_error "AgentCore configuration failed"
        exit 1
    fi
fi

# Step 5: Deploy (Local Build or CodeBuild with SSL fallback)
if [[ "$USE_LOCAL_BUILD" == "true" ]]; then
    echo -e "\n${BLUE}Step 5: Deploying with Local Build (Docker)${NC}"
    echo "--------------------------------------------"
    
    # Temporarily disable exit on error for Docker build attempt
    set +e
    agentcore launch --local-build
    DOCKER_BUILD_SUCCESS=$?
    set -e
    
    if [[ $DOCKER_BUILD_SUCCESS -eq 0 ]]; then
        print_status "Agent deployed successfully with local Docker build"
        ACTUAL_BUILD_METHOD="Docker"
    else
        print_warning "Docker build failed (likely SSL/VPN issues) - falling back to CodeBuild"
        echo -e "\n${BLUE}Step 5b: Fallback to CodeBuild${NC}"
        echo "--------------------------------------------"
        
        # Reconfigure without container runtime for CodeBuild but with custom execution role
        if agentcore configure \
            --entrypoint food_agent.py \
            --name $AGENT_NAME \
            --execution-role "$EXECUTION_ROLE_ARN" \
            --requirements-file requirements.txt \
            --region $REGION; then
            print_status "Reconfigured for CodeBuild with custom IAM role"
        else
            print_error "Failed to reconfigure for CodeBuild"
            exit 1
        fi
        
        # Try CodeBuild deployment
        if agentcore launch; then
            print_status "Agent deployed successfully with CodeBuild (SSL fallback)"
            ACTUAL_BUILD_METHOD="CodeBuild (SSL fallback)"
        else
            print_error "Both Docker and CodeBuild deployment failed"
            exit 1
        fi
    fi
else
    echo -e "\n${BLUE}Step 5: Deploying with CodeBuild${NC}"
    echo "--------------------------------------------"
    
    if agentcore launch; then
        print_status "Agent deployed successfully with CodeBuild"
    else
        print_error "Agent deployment failed"
        exit 1
    fi
fi

# Step 6: Get deployment details
echo -e "\n${BLUE}Step 6: Deployment Details${NC}"
echo "-----------------------------------"

AGENT_STATUS=$(agentcore status 2>/dev/null || echo "Unknown")

echo "Agent Name: $AGENT_NAME"
echo "Custom IAM Role: $IAM_ROLE_NAME"
echo "Status: $AGENT_STATUS"
echo "Region: $REGION"  
echo "Parameter Store: $PARAMETER_NAME"

# Step 7: Testing Deployment
echo -e "\n${BLUE}Step 7: Testing Deployment${NC}"
echo "-------------------------------"

print_status "Testing agent with sample query..."

TEST_PAYLOAD='{"prompt": "Find Italian restaurants in Rome"}'

if agentcore invoke "$TEST_PAYLOAD" >/dev/null 2>&1; then
    print_status "Agent test successful!"
else
    print_warning "Agent test failed - this might be normal during initial deployment"
    echo "Try testing again in a few minutes with:"
    echo "  agentcore invoke '$TEST_PAYLOAD'"
fi

# Success summary
echo -e "\n${GREEN}🎉 Food Agent Deployment Complete!${NC}"
echo -e "${GREEN}=================================${NC}"
echo -e "✅ Parameter Store configured with API key"
echo -e "✅ Custom IAM role with Parameter Store access"
if [[ "$USE_LOCAL_BUILD" == "true" ]]; then
    echo -e "✅ Agent built locally with Docker"  
else
    echo -e "✅ Agent built with CodeBuild (cloud-based)"
fi
echo -e "✅ Agent deployed to AWS AgentCore"
echo -e "✅ Ready for integration with Travel Orchestrator"

echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "1. Test deployment: ${YELLOW}agentcore invoke '$TEST_PAYLOAD'${NC}"
echo -e "2. Integrate with Travel Orchestrator"
echo -e "3. Use in multi-agent travel planning system"

echo -e "\n${BLUE}Useful Commands:${NC}"
echo -e "• Check status: ${YELLOW}agentcore status${NC}"
echo -e "• Update agent: ${YELLOW}agentcore launch${NC}"
echo -e "• Delete agent: ${YELLOW}agentcore destroy${NC}"

echo -e "\n${GREEN}Deployment completed successfully! 🚀${NC}"
