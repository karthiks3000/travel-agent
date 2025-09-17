/**
 * Environment configuration for different deployment stages
 * Based on requirements 2.2, 3.1, and 10.1
 */

// Environment types
export type Environment = 'development' | 'staging' | 'production';

// Amplify configuration interface
export interface AmplifyConfig {
  Auth: {
    Cognito: {
      userPoolId: string;
      userPoolClientId: string;
      loginWith?: {
        oauth?: {
          domain: string;
          scopes: string[];
          redirectSignIn: string[];
          redirectSignOut: string[];
          responseType: string;
        };
        username?: boolean;
        email?: boolean;
        phone?: boolean;
      };
      signUpVerificationMethod?: 'code' | 'link';
      userAttributes?: {
        email: {
          required: boolean;
        };
        name?: {
          required: boolean;
        };
      };
      allowGuestAccess?: boolean;
      passwordFormat?: {
        minLength: number;
        requireLowercase: boolean;
        requireUppercase: boolean;
        requireNumbers: boolean;
        requireSpecialCharacters: boolean;
      };
    };
  };
}

// Base configuration interface
export interface EnvironmentConfig {
  environment: Environment;
  apiUrl: string;
  agentCoreUrl: string;
  amplifyConfig: AmplifyConfig;
  features: {
    enableAnalytics: boolean;
    enableErrorReporting: boolean;
    enableDebugMode: boolean;
  };
}

// Development configuration
const developmentConfig: EnvironmentConfig = {
  environment: 'development',
  apiUrl: 'http://localhost:3000/api',
  agentCoreUrl: 'http://localhost:8000',
  amplifyConfig: {
    Auth: {
      Cognito: {
        userPoolId: 'us-east-1_XXXXXXXXX', // Mock value for development
        userPoolClientId: 'XXXXXXXXXXXXXXXXXXXXXXXXXX', // Mock value for development
        loginWith: {
          email: true,
          username: false,
          phone: false,
        },
        signUpVerificationMethod: 'code',
        userAttributes: {
          email: {
            required: true,
          },
          name: {
            required: true,
          },
        },
        allowGuestAccess: false,
        passwordFormat: {
          minLength: 8,
          requireLowercase: true,
          requireUppercase: true,
          requireNumbers: true,
          requireSpecialCharacters: false,
        },
      },
    },
  },
  features: {
    enableAnalytics: false,
    enableErrorReporting: false,
    enableDebugMode: true,
  },
};

// Staging configuration
const stagingConfig: EnvironmentConfig = {
  environment: 'staging',
  apiUrl: import.meta.env.VITE_API_URL || 'https://api-staging.travelagent.com',
  agentCoreUrl: import.meta.env.VITE_AGENT_CORE_URL || 'https://agentcore-staging.travelagent.com',
  amplifyConfig: {
    Auth: {
      Cognito: {
        userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || 'us-east-1_STAGING',
        userPoolClientId: import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID || 'STAGING_CLIENT_ID',
        loginWith: {
          email: true,
          username: false,
          phone: false,
        },
        signUpVerificationMethod: 'code',
        userAttributes: {
          email: {
            required: true,
          },
          name: {
            required: true,
          },
        },
        allowGuestAccess: false,
        passwordFormat: {
          minLength: 8,
          requireLowercase: true,
          requireUppercase: true,
          requireNumbers: true,
          requireSpecialCharacters: false,
        },
      },
    },
  },
  features: {
    enableAnalytics: true,
    enableErrorReporting: true,
    enableDebugMode: false,
  },
};

// Production configuration
const productionConfig: EnvironmentConfig = {
  environment: 'production',
  apiUrl: import.meta.env.VITE_API_URL || 'https://api.travelagent.com',
  agentCoreUrl: import.meta.env.VITE_AGENT_CORE_URL || 'https://agentcore.travelagent.com',
  amplifyConfig: {
    Auth: {
      Cognito: {
        userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || '',
        userPoolClientId: import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID || '',
        loginWith: {
          email: true,
          username: false,
          phone: false,
        },
        signUpVerificationMethod: 'code',
        userAttributes: {
          email: {
            required: true,
          },
          name: {
            required: true,
          },
        },
        allowGuestAccess: false,
        passwordFormat: {
          minLength: 8,
          requireLowercase: true,
          requireUppercase: true,
          requireNumbers: true,
          requireSpecialCharacters: true,
        },
      },
    },
  },
  features: {
    enableAnalytics: true,
    enableErrorReporting: true,
    enableDebugMode: false,
  },
};

// Get current environment from environment variables
const getCurrentEnvironment = (): Environment => {
  const env = import.meta.env.VITE_ENVIRONMENT || import.meta.env.MODE || 'development';
  
  switch (env) {
    case 'staging':
      return 'staging';
    case 'production':
      return 'production';
    default:
      return 'development';
  }
};

// Get configuration based on current environment
export const getEnvironmentConfig = (): EnvironmentConfig => {
  const environment = getCurrentEnvironment();
  
  switch (environment) {
    case 'staging':
      return stagingConfig;
    case 'production':
      return productionConfig;
    default:
      return developmentConfig;
  }
};

// Export current configuration
export const config = getEnvironmentConfig();

// Validation function to ensure required environment variables are set
export const validateEnvironmentConfig = (config: EnvironmentConfig): void => {
  const { amplifyConfig, environment } = config;
  
  // In development, allow mock values
  if (environment !== 'development') {
    if (!amplifyConfig.Auth.Cognito.userPoolId || amplifyConfig.Auth.Cognito.userPoolId.includes('XXXXXXXXX')) {
      throw new Error('VITE_COGNITO_USER_POOL_ID is required and must be a valid User Pool ID');
    }
    
    if (!amplifyConfig.Auth.Cognito.userPoolClientId || amplifyConfig.Auth.Cognito.userPoolClientId.includes('XXXXXXXXX')) {
      throw new Error('VITE_COGNITO_USER_POOL_CLIENT_ID is required and must be valid Client ID');
    }
  }
  
  if (environment === 'production') {
    if (!config.apiUrl.startsWith('https://')) {
      throw new Error('Production API URL must use HTTPS');
    }
    
    if (!config.agentCoreUrl.startsWith('https://')) {
      throw new Error('Production AgentCore URL must use HTTPS');
    }
  }
};

// Helper function to check if we're in development mode
export const isDevelopment = (): boolean => {
  return config.environment === 'development';
};

// Helper function to check if we're in production mode
export const isProduction = (): boolean => {
  return config.environment === 'production';
};

// Helper function to get feature flags
export const getFeatureFlags = () => {
  return config.features;
};
