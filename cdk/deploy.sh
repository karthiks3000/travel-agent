#!/bin/bash

# Travel Agent CDK Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default environment
ENVIRONMENT=${1:-dev}

echo -e "${GREEN}🚀 Deploying Travel Agent CDK Infrastructure${NC}"
echo -e "${YELLOW}Environment: ${ENVIRONMENT}${NC}"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS CLI not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo -e "${RED}❌ AWS CDK CLI not found. Please install it with 'npm install -g aws-cdk'${NC}"
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    npm install
fi

# Build the project
echo -e "${YELLOW}🔨 Building CDK project...${NC}"
npm run build

# Check if CDK is bootstrapped
echo -e "${YELLOW}🔍 Checking CDK bootstrap status...${NC}"
if ! cdk list > /dev/null 2>&1; then
    echo -e "${YELLOW}⚡ Bootstrapping CDK...${NC}"
    cdk bootstrap
fi

# Deploy the stack
echo -e "${YELLOW}🚀 Deploying stack...${NC}"
cdk deploy --context environment=${ENVIRONMENT} --require-approval never

# Check deployment status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo -e "${GREEN}📋 Stack outputs:${NC}"
    aws cloudformation describe-stacks \
        --stack-name "TravelAgentStack-${ENVIRONMENT}" \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
        --output table 2>/dev/null || echo "Use 'aws cloudformation describe-stacks' to view outputs"
else
    echo -e "${RED}❌ Deployment failed!${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 CDK deployment complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Copy the Cognito outputs to your frontend amplify_outputs.json"
echo -e "2. Test the authentication flow in your React application"
echo -e "3. Deploy additional environments as needed"