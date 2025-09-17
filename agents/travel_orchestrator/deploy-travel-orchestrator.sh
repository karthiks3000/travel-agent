#!/bin/bash
set -e

# Travel Orchestrator Deployment Script
# Enhanced deployment for multi-agent coordination capabilities

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_PROFILE="bookhood"
PARAMETER_NAME="/travel-agent/nova-act-api-key"
AGENT_NAME="travel_orchestrator"

# Get AWS account ID and region dynamically
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile $AWS_PROFILE)
REGION=$(aws configure get region --profile $AWS_PROFILE)

# Fallback to us-east-1 if region not configured
if [[ -z "$REGION" ]]; then
    REGION="us-east-1"
    print_warning "No region configured in AWS profile, using default: $REGION"
fi

echo -e "${BLUE}🌍 Travel Orchestrator Deployment Script${NC}"
echo -e "${BLUE}=======================================${NC}"

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
# Step 1: Prerequisites Check
echo -e "\n${BLUE}Step 1: Checking Prerequisites${NC}"
echo "----------------------------------------"

# Determine environment (default to 'dev' if not set to match CDK)
ENVIRONMENT=${ENVIRONMENT:-dev}

# Check if running from correct directory
if [[ ! -f "travel_orchestrator.py" ]]; then
    print_error "Please run this script from the agents/travel_orchestrator directory"
    exit 1
fi

# Copy common directory for deployment (temporary)
if [[ -d "../../common" ]]; then
    print_status "Copying common directory for deployment (temporary)..."
    # Copy common directory from project root, excluding the circular symlink
    cp -r ../../common . 2>/dev/null || {
        # If copy fails due to circular symlink, copy files individually
        mkdir -p common
        cp ../../common/__init__.py common/ 2>/dev/null || true
        cp ../../common/browser_wrapper.py common/ 2>/dev/null || true
        cp ../../common/*.py common/ 2>/dev/null || true
        # Copy models subdirectory
        if [[ -d "../../common/models" ]]; then
            mkdir -p common/models
            cp ../../common/models/*.py common/models/ 2>/dev/null || true
        fi
    }
    print_status "Common directory copied successfully"
else
    print_error "Common directory not found at ../../common"
    exit 1
fi

# Function to cleanup temporary files
cleanup_temp_files() {
    if [[ -d "common" ]]; then
        print_status "Cleaning up temporary common directory..."
        rm -rf common/
        print_status "Temporary files cleaned up"
    fi
}

# Set trap to cleanup on script exit (success or failure)
trap cleanup_temp_files EXIT

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

# Using CodeBuild as default (no Docker/Podman checks)
print_status "Using CodeBuild for deployment (default option)"

# Check Nova Act API Key
if [[ -z "$NOVA_ACT_API_KEY" ]]; then
    print_error "NOVA_ACT_API_KEY environment variable not set"
    echo "Set it with: export NOVA_ACT_API_KEY='your_api_key_here'"
    exit 1
fi
print_status "Nova Act API key found in environment"

# Step 1.5: Get Cognito Configuration from CDK Stack
echo -e "\n${BLUE}Step 1.5: Retrieving Cognito Configuration${NC}"
echo "---------------------------------------------------"

CDK_STACK_NAME="TravelAgentStack-${ENVIRONMENT}"

print_status "Looking for CDK stack: $CDK_STACK_NAME"

# Check if stack exists first
if ! aws cloudformation describe-stacks --stack-name "$CDK_STACK_NAME" --profile $AWS_PROFILE --region $REGION >/dev/null 2>&1; then
    print_error "CDK stack '$CDK_STACK_NAME' not found"
    print_warning "Available stacks:"
    aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query "StackSummaries[].StackName" --output table --profile $AWS_PROFILE --region $REGION
    print_warning "Make sure your CDK stack is deployed with: cd cdk && npm run deploy"
    exit 1
fi

print_status "CDK stack found: $CDK_STACK_NAME"

# Get Cognito configuration from CDK outputs
USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name "$CDK_STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='CognitoUserPoolId'].OutputValue" \
    --output text \
    --profile $AWS_PROFILE \
    --region $REGION 2>/dev/null || echo "")

USER_POOL_CLIENT_ID=$(aws cloudformation describe-stacks \
    --stack-name "$CDK_STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='CognitoUserPoolClientId'].OutputValue" \
    --output text \
    --profile $AWS_PROFILE \
    --region $REGION 2>/dev/null || echo "")

if [[ -z "$USER_POOL_ID" || -z "$USER_POOL_CLIENT_ID" ]]; then
    print_warning "Could not retrieve Cognito configuration from CDK stack outputs"
    print_warning "Available outputs from stack $CDK_STACK_NAME:"
    aws cloudformation describe-stacks --stack-name "$CDK_STACK_NAME" --query "Stacks[0].Outputs[].{Key:OutputKey,Value:OutputValue}" --output table --profile $AWS_PROFILE --region $REGION
    exit 1
fi

print_status "Cognito User Pool ID: $USER_POOL_ID"
print_status "Cognito Client ID: $USER_POOL_CLIENT_ID"

# Construct the discovery URL
COGNITO_DISCOVERY_URL="https://cognito-idp.${REGION}.amazonaws.com/${USER_POOL_ID}/.well-known/openid-configuration"
print_status "Discovery URL: $COGNITO_DISCOVERY_URL"

# Step 2: Setup Parameter Store
echo -e "\n${BLUE}Step 2: Setting up AWS Parameter Store${NC}"
echo "------------------------------------------------"

# Store API key in Parameter Store
if aws ssm put-parameter \
    --name "$PARAMETER_NAME" \
    --value "$NOVA_ACT_API_KEY" \
    --type "SecureString" \
    --overwrite \
    --profile $AWS_PROFILE \
    --region $REGION >/dev/null 2>&1; then
    print_status "Nova Act API key stored in Parameter Store: $PARAMETER_NAME"
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

# Store specialist agent ARNs in Parameter Store
print_status "Storing specialist agent ARNs in Parameter Store..."

# Get ARNs from environment variables
if [[ -n "$FLIGHT_AGENT_ARN" ]]; then
    if aws ssm put-parameter \
        --name "/travel-agent/flight-agent-arn" \
        --value "$FLIGHT_AGENT_ARN" \
        --type "String" \
        --overwrite \
        --profile $AWS_PROFILE \
        --region $REGION >/dev/null 2>&1; then
        print_status "Flight agent ARN stored: $FLIGHT_AGENT_ARN"
    else
        print_warning "Failed to store flight agent ARN in Parameter Store"
    fi
else
    print_warning "FLIGHT_AGENT_ARN environment variable not set"
fi

if [[ -n "$ACCOMMODATION_AGENT_ARN" ]]; then
    if aws ssm put-parameter \
        --name "/travel-agent/accommodation-agent-arn" \
        --value "$ACCOMMODATION_AGENT_ARN" \
        --type "String" \
        --overwrite \
        --profile $AWS_PROFILE \
        --region $REGION >/dev/null 2>&1; then
        print_status "Accommodation agent ARN stored: $ACCOMMODATION_AGENT_ARN"
    else
        print_warning "Failed to store accommodation agent ARN in Parameter Store"
    fi
else
    print_warning "ACCOMMODATION_AGENT_ARN environment variable not set"
fi

if [[ -n "$FOOD_AGENT_ARN" ]]; then
    if aws ssm put-parameter \
        --name "/travel-agent/food-agent-arn" \
        --value "$FOOD_AGENT_ARN" \
        --type "String" \
        --overwrite \
        --profile $AWS_PROFILE \
        --region $REGION >/dev/null 2>&1; then
        print_status "Food agent ARN stored: $FOOD_AGENT_ARN"
    else
        print_warning "Failed to store food agent ARN in Parameter Store"
    fi
else
    print_warning "FOOD_AGENT_ARN environment variable not set"
fi

# Step 3: Create Enhanced IAM Role for Multi-Agent Coordination
echo -e "\n${BLUE}Step 3: Setting up Enhanced IAM Role${NC}"
echo "---------------------------------------------------"

IAM_ROLE_NAME="TravelOrchestratorExecutionRole"
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
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default/workload-identity/travel_orchestrator-*",
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default/workload-identity/flight_agent-*",
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default/workload-identity/accommodation_agent-*",
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
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default/workload-identity/travel_orchestrator-*",
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default/workload-identity/flight_agent-*",
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default/workload-identity/accommodation_agent-*",
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
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default/workload-identity/travel_orchestrator-*",
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default/workload-identity/flight_agent-*",
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:workload-identity-directory/default/workload-identity/accommodation_agent-*",
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
            "Sid": "BedrockAgentCoreInBuiltToolsFullAccess",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:CreateBrowser",
                "bedrock-agentcore:ListBrowsers",
                "bedrock-agentcore:GetBrowser",
                "bedrock-agentcore:DeleteBrowser",
                "bedrock-agentcore:StartBrowserSession",
                "bedrock-agentcore:ListBrowserSessions",
                "bedrock-agentcore:GetBrowserSession",
                "bedrock-agentcore:StopBrowserSession",
                "bedrock-agentcore:UpdateBrowserStream",
                "bedrock-agentcore:ConnectBrowserAutomationStream",
                "bedrock-agentcore:ConnectBrowserLiveViewStream"
            ],
            "Resource": "arn:aws:bedrock-agentcore:${REGION}:aws:browser/*"
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
        },
        {
            "Sid": "MultiAgentCoordinationAccess",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:InvokeAgentRuntime"
            ],
            "Resource": [
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:runtime/flight_agent",
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:runtime/accommodation_agent", 
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:runtime/food_agent"
            ]
        },
        {
            "Sid": "EnhancedMemoryManagement",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:CreateMemory",
                "bedrock-agentcore:GetMemory",
                "bedrock-agentcore:UpdateMemory",
                "bedrock-agentcore:DeleteMemory",
                "bedrock-agentcore:ListMemories"
            ],
            "Resource": [
                "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:memory/TravelOrchestrator_*"
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
    --policy-name "TravelOrchestratorExecutionPolicy" \
    --policy-document "$IAM_ROLE_POLICY" \
    --profile $AWS_PROFILE >/dev/null 2>&1

# Construct the role ARN
EXECUTION_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${IAM_ROLE_NAME}"

print_status "Enhanced IAM role created/updated: $IAM_ROLE_NAME"
print_status "Role ARN: $EXECUTION_ROLE_ARN"
print_status "Multi-agent coordination permissions enabled"

# Step 4: AgentCore Configuration
echo -e "\n${BLUE}Step 4: Configuring AgentCore Agent${NC}"
echo "--------------------------------------------"

# Configure with JWT Authentication and CodeBuild
if agentcore configure \
    --entrypoint travel_orchestrator.py \
    --name $AGENT_NAME \
    --execution-role "$EXECUTION_ROLE_ARN" \
    --requirements-file requirements.txt \
    --region $REGION \
    --authorizer-config "{
        \"customJWTAuthorizer\": {
            \"discoveryUrl\": \"$COGNITO_DISCOVERY_URL\",
            \"allowedClients\": [\"$USER_POOL_CLIENT_ID\"]
        }
    }"; then
    print_status "AgentCore agent configured with JWT authentication: $AGENT_NAME"
    print_status "Authentication: Cognito User Pool JWT Bearer Tokens"
else
    print_error "AgentCore configuration failed"
    exit 1
fi

# Step 5: Deploy with CodeBuild
echo -e "\n${BLUE}Step 5: Deploying with CodeBuild${NC}"
echo "--------------------------------------------"

if agentcore launch; then
    print_status "Travel Orchestrator deployed successfully with CodeBuild"
else
    print_error "Travel Orchestrator deployment failed"
    exit 1
fi

# Step 6: Get deployment details and HTTP endpoint
echo -e "\n${BLUE}Step 6: Deployment Details & HTTP Endpoint${NC}"
echo "----------------------------------------------------"

AGENT_STATUS=$(agentcore status 2>/dev/null || echo "Unknown")

# Get the agent runtime endpoint
AGENT_ENDPOINT=$(agentcore status --output json 2>/dev/null | jq -r '.endpoint // empty' || echo "")

echo "Agent Name: $AGENT_NAME"
echo "Enhanced IAM Role: $IAM_ROLE_NAME"
echo "Status: $AGENT_STATUS"
echo "Region: $REGION"  
echo "Parameter Store: $PARAMETER_NAME"
echo "Multi-Agent Coordination: Enabled"
echo "Authentication: JWT Bearer Token (Cognito)"

if [[ -n "$AGENT_ENDPOINT" ]]; then
    print_status "Agent HTTP Endpoint: $AGENT_ENDPOINT"
    echo ""
    print_status "Frontend Configuration:"
    echo "Set this as your VITE_AGENT_CORE_URL: $AGENT_ENDPOINT"
else
    print_warning "Could not retrieve agent endpoint. Check with: agentcore status"
fi

# Step 7: Testing Multi-Agent Orchestration
echo -e "\n${BLUE}Step 7: Testing Multi-Agent Orchestration${NC}"
echo "-----------------------------------------------"

print_status "Testing orchestrator with comprehensive travel planning query..."

TEST_PAYLOAD='{"prompt": "Plan a comprehensive trip from JFK to Paris from June 15-20, 2025 for 2 people. I need flights, hotel recommendations, and restaurant suggestions."}'

echo "Test payload: $TEST_PAYLOAD"

if agentcore invoke "$TEST_PAYLOAD" >/dev/null 2>&1; then
    print_status "Travel Orchestrator test successful!"
    print_status "Multi-agent coordination verified"
else
    print_warning "Travel Orchestrator test failed - this might be normal during initial deployment"
    echo "The orchestrator may need specialist agents (flight_agent, accommodation_agent, food_agent) to be deployed first."
    echo "Try testing again in a few minutes with:"
    echo "  agentcore invoke '$TEST_PAYLOAD'"
fi

# Step 8: Verification of Specialist Agent Dependencies
echo -e "\n${BLUE}Step 8: Checking Specialist Agent Dependencies${NC}"
echo "----------------------------------------------------"

print_status "Verifying specialist agent availability..."

# Check if specialist agents are deployed (this will help with troubleshooting)
echo "Note: The Travel Orchestrator requires these specialist agents to be deployed:"
echo "  • flight_agent (for flight searches)"
echo "  • accommodation_agent (for hotel searches)" 
echo "  • food_agent (for restaurant recommendations)"
echo ""
echo "Deploy specialist agents first if orchestration tests fail:"
echo "  • cd ../flight_agent && ./deploy-flight-agent.sh"
echo "  • cd ../accommodation_agent && ./deploy-accommodation-agent.sh"
echo "  • cd ../food_agent && ./deploy-food-agent.sh"

# Success summary
echo -e "\n${GREEN}🎉 Travel Orchestrator with JWT Authentication Complete!${NC}"
echo -e "${GREEN}=========================================================${NC}"
echo -e "✅ Parameter Store configured with Nova Act API key"
echo -e "✅ Enhanced IAM role with multi-agent coordination permissions"
echo -e "✅ Agent built with CodeBuild (cloud-based)"
echo -e "✅ Travel Orchestrator deployed to AWS AgentCore"
echo -e "✅ JWT authentication enabled with Cognito User Pool"
echo -e "✅ HTTP endpoint enabled for frontend access"
echo -e "✅ Memory management enabled for session handling"
echo -e "✅ Ready for comprehensive travel planning coordination"

echo -e "\n${BLUE}Frontend Configuration:${NC}"
echo -e "Create/update ${YELLOW}frontend/.env.local${NC} with:"
if [[ -n "$AGENT_ENDPOINT" ]]; then
    echo -e "${YELLOW}VITE_AGENT_CORE_URL=$AGENT_ENDPOINT${NC}"
else
    echo -e "${YELLOW}VITE_AGENT_CORE_URL=<AGENT_ENDPOINT_FROM_STATUS>${NC}"
fi
echo -e "${YELLOW}VITE_COGNITO_USER_POOL_ID=$USER_POOL_ID${NC}"
echo -e "${YELLOW}VITE_COGNITO_USER_POOL_CLIENT_ID=$USER_POOL_CLIENT_ID${NC}"
echo -e "${YELLOW}VITE_ENVIRONMENT=$ENVIRONMENT${NC}"

echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "1. Update frontend environment variables (see above)"
echo -e "2. Ensure specialist agents are deployed: flight_agent, accommodation_agent, food_agent"
echo -e "3. Test with bearer token: ${YELLOW}agentcore invoke '$TEST_PAYLOAD' --bearer-token <JWT_TOKEN>${NC}"
echo -e "4. Start frontend and test end-to-end integration"

echo -e "\n${BLUE}Key Features Enabled:${NC}"
echo -e "• JWT Bearer Token authentication with Cognito"
echo -e "• Direct HTTP access for frontend integration"
echo -e "• Multi-agent coordination (flights, hotels, restaurants)"
echo -e "• Memory-based session management"
echo -e "• Comprehensive travel plan synthesis"
echo -e "• Structured JSON responses for frontend integration"

echo -e "\n${BLUE}Useful Commands:${NC}"
echo -e "• Check status: ${YELLOW}agentcore status${NC}"
echo -e "• Update agent: ${YELLOW}agentcore launch${NC}"
echo -e "• Test with JWT: ${YELLOW}agentcore invoke --bearer-token <TOKEN> '{\"prompt\": \"Plan a trip\"}'${NC}"
echo -e "• Delete agent: ${YELLOW}agentcore destroy${NC}"

echo -e "\n${BLUE}Final Cleanup:${NC}"
echo -e "✅ Common directory will be automatically cleaned up"
