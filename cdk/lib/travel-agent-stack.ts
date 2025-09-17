import * as cdk from 'aws-cdk-lib';
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
  }
}