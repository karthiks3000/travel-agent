import * as cdk from 'aws-cdk-lib';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import { Construct } from 'constructs';

export interface CognitoStackProps {
  environment: string;
}

export class CognitoStack extends Construct {
  public readonly userPool: cognito.UserPool;
  public readonly userPoolClient: cognito.UserPoolClient;

  constructor(scope: Construct, id: string, props: CognitoStackProps) {
    super(scope, id);

    // Create Cognito User Pool with security best practices
    this.userPool = new cognito.UserPool(this, 'TravelAgentUserPool', {
      userPoolName: `travel-agent-users-${props.environment}`,
      
      // Allow users to sign up themselves
      selfSignUpEnabled: true,
      
      // Use email as the sign-in method
      signInAliases: {
        email: true,
      },
      
      // Require email verification for security
      autoVerify: {
        email: true,
      },
      
      // Strong password policy as per requirements
      passwordPolicy: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: false, // Keep false for better UX
      },
      
      // Account recovery via email only for security
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
      
      // Standard attributes required for the travel agent
      standardAttributes: {
        email: {
          required: true,
          mutable: true,
        },
        givenName: {
          required: true,
          mutable: true,
        },
        familyName: {
          required: false,
          mutable: true,
        },
      },
      
      // Email configuration for verification
      email: cognito.UserPoolEmail.withCognito(),
      
      // Device tracking for enhanced security
      deviceTracking: {
        challengeRequiredOnNewDevice: true,
        deviceOnlyRememberedOnUserPrompt: false,
      },
      
      // MFA configuration (optional but recommended)
      mfa: cognito.Mfa.OPTIONAL,
      mfaSecondFactor: {
        sms: false, // Disable SMS for cost optimization
        otp: true,  // Enable TOTP apps
      },
      
      // Advanced security features
      advancedSecurityMode: cognito.AdvancedSecurityMode.ENFORCED,
      
      // Deletion protection for production
      deletionProtection: props.environment === 'prod',
      
      // Removal policy based on environment
      removalPolicy: props.environment === 'prod' 
        ? cdk.RemovalPolicy.RETAIN 
        : cdk.RemovalPolicy.DESTROY,
    });

    // Create User Pool Client for the React web application
    this.userPoolClient = new cognito.UserPoolClient(this, 'TravelAgentUserPoolClient', {
      userPool: this.userPool,
      userPoolClientName: `travel-agent-web-client-${props.environment}`,
      
      // Web application configuration
      generateSecret: false, // Must be false for web applications
      
      // Authentication flows
      authFlows: {
        userSrp: true,        // Secure Remote Password (recommended)
        userPassword: false,  // Disable for security
        adminUserPassword: false, // Disable for security
        custom: false,        // Not needed for this use case
      },
      
      // OAuth configuration for future extensibility
      oAuth: {
        flows: {
          authorizationCodeGrant: true,
          implicitCodeGrant: false, // Deprecated, use authorization code
        },
        scopes: [
          cognito.OAuthScope.EMAIL,
          cognito.OAuthScope.OPENID,
          cognito.OAuthScope.PROFILE,
        ],
        callbackUrls: this.getCallbackUrls(props.environment),
        logoutUrls: this.getLogoutUrls(props.environment),
      },
      
      // Token validity periods
      accessTokenValidity: cdk.Duration.hours(1),   // Short-lived for security
      idTokenValidity: cdk.Duration.hours(1),       // Short-lived for security
      refreshTokenValidity: cdk.Duration.days(30),  // Longer for UX
      
      // Prevent user existence errors for security
      preventUserExistenceErrors: true,
      
      // Enable token revocation
      enableTokenRevocation: true,
      
      // Supported identity providers
      supportedIdentityProviders: [
        cognito.UserPoolClientIdentityProvider.COGNITO,
      ],
    });

    // Add custom attributes for travel preferences (optional)
    this.userPool.addClient('TravelAgentMobileClient', {
      userPoolClientName: `travel-agent-mobile-client-${props.environment}`,
      generateSecret: false,
      authFlows: {
        userSrp: true,
      },
      // Mobile-specific configuration can be added here
    });

    // Create tags for resource management
    cdk.Tags.of(this.userPool).add('Environment', props.environment);
    cdk.Tags.of(this.userPool).add('Application', 'TravelAgent');
    cdk.Tags.of(this.userPool).add('Component', 'Authentication');
    
    cdk.Tags.of(this.userPoolClient).add('Environment', props.environment);
    cdk.Tags.of(this.userPoolClient).add('Application', 'TravelAgent');
    cdk.Tags.of(this.userPoolClient).add('Component', 'Authentication');
  }

  /**
   * Get callback URLs based on environment
   */
  private getCallbackUrls(environment: string): string[] {
    switch (environment) {
      case 'prod':
        return [
          'https://travel-agent.example.com/auth/callback', // Replace with actual domain
        ];
      case 'staging':
        return [
          'https://staging-travel-agent.example.com/auth/callback', // Replace with actual domain
        ];
      default: // dev and local
        return [
          'http://localhost:5173',  // Vite dev server - simplified for development
          'http://localhost:3000',  // Alternative port
        ];
    }
  }

  /**
   * Get logout URLs based on environment
   */
  private getLogoutUrls(environment: string): string[] {
    switch (environment) {
      case 'prod':
        return [
          'https://travel-agent.example.com/',
        ];
      case 'staging':
        return [
          'https://staging-travel-agent.example.com/',
        ];
      default: // dev and local
        return [
          'http://localhost:5173/',
          'http://localhost:3000/',
        ];
    }
  }
}
