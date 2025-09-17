# Travel Agent CDK Infrastructure

This directory contains the AWS CDK infrastructure code for the Travel Agent application, including AWS Cognito authentication setup.

## Prerequisites

- Node.js 18+ installed
- AWS CLI configured with appropriate credentials
- AWS CDK CLI installed globally: `npm install -g aws-cdk`

## Setup

1. Install dependencies:
```bash
cd cdk
npm install
```

2. Bootstrap CDK (first time only):
```bash
cdk bootstrap
```

## Deployment

### Development Environment
```bash
# Deploy to development environment
cdk deploy --context environment=dev

# Or use the npm script
npm run deploy -- --context environment=dev
```

### Staging Environment
```bash
cdk deploy --context environment=staging
```

### Production Environment
```bash
cdk deploy --context environment=prod
```

## Infrastructure Components

### AWS Cognito Configuration

The CDK creates the following Cognito resources:

#### User Pool Features:
- **Self Sign-up**: Enabled for user registration
- **Email Sign-in**: Users sign in with email addresses
- **Email Verification**: Required for account security
- **Strong Password Policy**: 8+ characters with uppercase, lowercase, and digits
- **Account Recovery**: Email-only recovery for security
- **Advanced Security**: Enforced for production environments
- **MFA Support**: Optional TOTP-based multi-factor authentication
- **Device Tracking**: Enhanced security for new devices

#### User Pool Client Features:
- **Web Application Optimized**: No client secret (required for web apps)
- **Secure Authentication**: SRP (Secure Remote Password) flow only
- **OAuth 2.0 Support**: Authorization code grant flow
- **Token Management**: Short-lived access/ID tokens (1 hour), longer refresh tokens (30 days)
- **Security Features**: User existence error prevention, token revocation support

### Environment-Specific Configuration

The infrastructure adapts based on the deployment environment:

- **Development**: 
  - Callback URLs for localhost (ports 3000, 5173)
  - Resources can be destroyed
  - Basic security settings

- **Staging**: 
  - Staging domain callback URLs
  - Enhanced security settings
  - Resources can be destroyed

- **Production**: 
  - Production domain callback URLs
  - Maximum security settings
  - Deletion protection enabled
  - Resource retention policy

## Outputs

After deployment, the stack provides these outputs for frontend configuration:

- `CognitoUserPoolId`: The User Pool ID for AWS Amplify configuration
- `CognitoUserPoolClientId`: The Client ID for authentication
- `CognitoRegion`: The AWS region for Cognito services

## Frontend Integration

Use the CDK outputs to configure your frontend `amplify_outputs.json`:

```json
{
  "auth": {
    "user_pool_id": "<CognitoUserPoolId from CDK output>",
    "user_pool_client_id": "<CognitoUserPoolClientId from CDK output>",
    "aws_region": "<CognitoRegion from CDK output>"
  }
}
```

## Security Best Practices Implemented

1. **Strong Password Policy**: Enforces complex passwords
2. **Email Verification**: Prevents fake account creation
3. **Advanced Security Mode**: Detects and prevents suspicious activities
4. **SRP Authentication**: Secure password verification without sending passwords
5. **Short Token Lifetimes**: Reduces exposure window for compromised tokens
6. **Device Tracking**: Monitors and challenges new device access
7. **User Existence Protection**: Prevents user enumeration attacks
8. **Token Revocation**: Allows immediate session termination

## Useful Commands

- `npm run build`: Compile TypeScript to JavaScript
- `npm run watch`: Watch for changes and compile
- `npm run test`: Run unit tests
- `cdk deploy`: Deploy this stack to your default AWS account/region
- `cdk diff`: Compare deployed stack with current state
- `cdk synth`: Emit the synthesized CloudFormation template
- `cdk destroy`: Remove the stack (use with caution)

## Troubleshooting

### Common Issues

1. **Bootstrap Required**: If you get bootstrap errors, run `cdk bootstrap`
2. **Permissions**: Ensure your AWS credentials have sufficient permissions
3. **Region Mismatch**: Verify your AWS CLI region matches the CDK region
4. **Domain Configuration**: Update callback URLs in `cognito-stack.ts` for your domains

### Viewing Resources

After deployment, you can view the created resources in the AWS Console:
- Cognito User Pools: https://console.aws.amazon.com/cognito/users/
- CloudFormation Stacks: https://console.aws.amazon.com/cloudformation/

## Next Steps

1. Deploy the CDK stack to create Cognito resources
2. Update your frontend `amplify_outputs.json` with the CDK outputs
3. Test the authentication flow in your React application
4. Configure additional environments as needed