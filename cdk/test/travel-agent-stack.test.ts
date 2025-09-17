import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { TravelAgentStack } from '../lib/travel-agent-stack';

describe('TravelAgentStack', () => {
  let app: cdk.App;
  let stack: TravelAgentStack;
  let template: Template;

  beforeEach(() => {
    app = new cdk.App();
    stack = new TravelAgentStack(app, 'TestTravelAgentStack', {
      environment: 'test',
    });
    template = Template.fromStack(stack);
  });

  test('Creates Cognito User Pool', () => {
    template.hasResourceProperties('AWS::Cognito::UserPool', {
      UserPoolName: 'travel-agent-users-test',
      Policies: {
        PasswordPolicy: {
          MinimumLength: 8,
          RequireLowercase: true,
          RequireNumbers: true,
          RequireSymbols: false,
          RequireUppercase: true,
        },
      },
      AutoVerifiedAttributes: ['email'],
      UsernameAttributes: ['email'],
      AccountRecoverySetting: {
        RecoveryMechanisms: [
          {
            Name: 'verified_email',
            Priority: 1,
          },
        ],
      },
    });
  });

  test('Creates Cognito User Pool Client', () => {
    template.hasResourceProperties('AWS::Cognito::UserPoolClient', {
      UserPoolId: {
        Ref: expect.stringMatching(/^CognitoStack.*UserPool/),
      },
      GenerateSecret: false,
      ExplicitAuthFlows: ['ALLOW_USER_SRP_AUTH'],
      PreventUserExistenceErrors: true,
      EnableTokenRevocation: true,
    });
  });

  test('Creates required stack outputs', () => {
    template.hasOutput('CognitoUserPoolId', {
      Description: 'Cognito User Pool ID for frontend configuration',
    });

    template.hasOutput('CognitoUserPoolClientId', {
      Description: 'Cognito User Pool Client ID for frontend configuration',
    });

    template.hasOutput('CognitoRegion', {
      Description: 'AWS Region for Cognito configuration',
    });
  });

  test('Applies correct tags', () => {
    template.hasResourceProperties('AWS::Cognito::UserPool', {
      UserPoolTags: {
        Environment: 'test',
        Application: 'TravelAgent',
        Component: 'Authentication',
      },
    });
  });

  test('Configures advanced security for production', () => {
    const prodStack = new TravelAgentStack(app, 'ProdTravelAgentStack', {
      environment: 'prod',
    });
    const prodTemplate = Template.fromStack(prodStack);

    prodTemplate.hasResourceProperties('AWS::Cognito::UserPool', {
      UserPoolAddOns: {
        AdvancedSecurityMode: 'ENFORCED',
      },
      DeletionProtection: 'ACTIVE',
    });
  });

  test('Allows resource deletion for non-production environments', () => {
    template.hasResourceProperties('AWS::Cognito::UserPool', {
      DeletionProtection: 'INACTIVE',
    });
  });
});