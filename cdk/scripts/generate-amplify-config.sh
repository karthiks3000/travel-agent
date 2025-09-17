#!/bin/bash

# Generate amplify_outputs.json from CDK stack outputs

set -e

ENVIRONMENT=${1:-dev}
STACK_NAME="TravelAgentStack-${ENVIRONMENT}"
OUTPUT_FILE="../../frontend/amplify_outputs.json"

echo "🔍 Fetching CDK outputs for environment: ${ENVIRONMENT}"

# Check if frontend directory exists
if [ ! -d "../../frontend" ]; then
    echo "❌ Frontend directory not found. Please run this script from cdk/scripts/"
    exit 1
fi

# Check if stack exists
if ! aws cloudformation describe-stacks --stack-name "${STACK_NAME}" > /dev/null 2>&1; then
    echo "❌ Stack ${STACK_NAME} not found. Please deploy the CDK stack first."
    exit 1
fi

# Get stack outputs
USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --query 'Stacks[0].Outputs[?OutputKey==`CognitoUserPoolId`].OutputValue' \
    --output text)

USER_POOL_CLIENT_ID=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --query 'Stacks[0].Outputs[?OutputKey==`CognitoUserPoolClientId`].OutputValue' \
    --output text)

REGION=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --query 'Stacks[0].Outputs[?OutputKey==`CognitoRegion`].OutputValue' \
    --output text)

# Validate outputs
if [ -z "$USER_POOL_ID" ] || [ -z "$USER_POOL_CLIENT_ID" ] || [ -z "$REGION" ]; then
    echo "❌ Failed to retrieve all required outputs from CDK stack"
    exit 1
fi

# Generate amplify_outputs.json in Amplify v6 format
cat > "${OUTPUT_FILE}" << EOF
{
  "version": "1.1",
  "auth": {
    "user_pool_id": "${USER_POOL_ID}",
    "user_pool_client_id": "${USER_POOL_CLIENT_ID}",
    "aws_region": "${REGION}",
    "username_attributes": ["email"],
    "standard_required_attributes": ["email"],
    "user_verification_types": ["email"],
    "password_policy": {
      "min_length": 8,
      "require_lowercase": true,
      "require_uppercase": true,
      "require_numbers": true,
      "require_symbols": false
    },
    "unauthenticated_identities_enabled": false,
    "oauth": {
      "identity_providers": ["COGNITO"],
      "domain": "",
      "scopes": ["email", "openid", "profile"],
      "redirect_sign_in_uri": ["http://localhost:5173"],
      "redirect_sign_out_uri": ["http://localhost:5173/"],
      "response_type": "code"
    }
  }
}
EOF

echo "✅ Generated ${OUTPUT_FILE}"
echo "� Configuration:"
echo "   User Pool ID: ${USER_POOL_ID}"
echo "   Client ID: ${USER_POOL_CLIENT_ID}"
echo "   Region: ${REGION}"
echo ""
echo "🎉 Frontend is now configured for Cognito authentication!"
