import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';
import { CognitoStack } from './cognito-stack';

export interface TravelAgentStackProps extends cdk.StackProps {
  environment: string;
}

export class TravelAgentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: TravelAgentStackProps) {
    super(scope, id, props);

    // Create Cognito authentication infrastructure
    const cognitoStack = new CognitoStack(this, 'CognitoStack', {
      environment: props.environment,
    });

    // Create S3 bucket for AgentCore Gateway OpenAPI specifications
    const gatewayBucket = new s3.Bucket(this, 'GatewayOpenAPIBucket', {
      bucketName: `travel-agent-gateway-${props.environment}-${cdk.Aws.ACCOUNT_ID}-${cdk.Aws.REGION}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Be careful in production
      lifecycleRules: [
        {
          id: 'DeleteIncompleteMultipartUploads',
          enabled: true,
          abortIncompleteMultipartUploadAfter: cdk.Duration.days(7)
        }
      ]
    });

    // Output the Cognito configuration for the frontend
    new cdk.CfnOutput(this, 'CognitoUserPoolId', {
      value: cognitoStack.userPool.userPoolId,
      description: 'Cognito User Pool ID for frontend configuration',
      exportName: `TravelAgent-${props.environment}-UserPoolId`,
    });

    new cdk.CfnOutput(this, 'CognitoUserPoolClientId', {
      value: cognitoStack.userPoolClient.userPoolClientId,
      description: 'Cognito User Pool Client ID for frontend configuration',
      exportName: `TravelAgent-${props.environment}-UserPoolClientId`,
    });

    new cdk.CfnOutput(this, 'CognitoRegion', {
      value: this.region,
      description: 'AWS Region for Cognito configuration',
      exportName: `TravelAgent-${props.environment}-Region`,
    });

    // Output Gateway S3 bucket name for deployment scripts
    new cdk.CfnOutput(this, 'GatewayBucketName', {
      value: gatewayBucket.bucketName,
      description: 'S3 bucket name for Gateway OpenAPI specifications',
      exportName: `TravelAgent-${props.environment}-GatewayBucket`,
    });

  }
}
