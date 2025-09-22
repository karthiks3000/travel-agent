/**
 * AWS Amplify configuration setup
 * Based on requirements 2.2, 3.1, and 10.1
 */

import { Amplify } from 'aws-amplify';
import { config, isDevelopment, validateEnvironmentConfig } from './environment';
import type { AmplifyConfig } from './environment';

// Type for amplify_outputs.json structure (matches generate-amplify-config.sh output)
interface AmplifyOutputs {
  version: string;
  auth: {
    user_pool_id: string;
    user_pool_client_id: string;
    aws_region: string;
    username_attributes: string[];
    standard_required_attributes: string[];
    user_verification_types: string[];
    password_policy: {
      min_length: number;
      require_lowercase: boolean;
      require_uppercase: boolean;
      require_numbers: boolean;
      require_symbols: boolean;
    };
    unauthenticated_identities_enabled: boolean;
    oauth: {
      identity_providers: string[];
      domain: string;
      scopes: string[];
      redirect_sign_in_uri: string[];
      redirect_sign_out_uri: string[];
      response_type: string;
    };
  };
  custom?: {
    agentCoreUrl?: string;
    apiUrl?: string;
  };
}

// Import amplify_outputs.json for local development
let amplifyOutputs: AmplifyOutputs | null = null;

// Function to load and validate amplify outputs
const loadAmplifyOutputs = async (): Promise<AmplifyOutputs | null> => {
  if (isDevelopment()) {
    try {
      // Dynamic import for amplify_outputs.json in development
      const outputs = await import('../../amplify_outputs.json');
      const data = outputs.default || outputs;
      
      // Basic validation
      if (!data?.auth?.user_pool_id || !data?.auth?.user_pool_client_id) {
        console.warn('amplify_outputs.json is invalid or missing required fields');
        return null;
      }
      
      return data as unknown as AmplifyOutputs;
    } catch (error) {
      console.warn('amplify_outputs.json not found, using environment configuration:', error instanceof Error ? error.message : 'Unknown error');
      return null;
    }
  }
  return null;
};

/**
 * Configure Amplify with environment-specific settings
 */
export const configureAmplify = async (): Promise<void> => {
  try {
    // Validate environment configuration
    validateEnvironmentConfig(config);

    // Load amplify outputs if in development
    amplifyOutputs = await loadAmplifyOutputs();

    // Use any type for internal Amplify configuration to avoid type compatibility issues
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let amplifyConfig: any;

    if (isDevelopment() && amplifyOutputs) {
      // Use amplify_outputs.json for local development
      amplifyConfig = {
        Auth: {
          Cognito: {
            userPoolId: amplifyOutputs.auth.user_pool_id,
            userPoolClientId: amplifyOutputs.auth.user_pool_client_id,
            loginWith: {
              email: amplifyOutputs.auth.username_attributes.includes('email'),
              username: !amplifyOutputs.auth.username_attributes.includes('email'),
            },
            signUpVerificationMethod: amplifyOutputs.auth.user_verification_types.includes('email') ? 'code' as const : 'link' as const,
            userAttributes: {
              email: {
                required: amplifyOutputs.auth.standard_required_attributes.includes('email'),
              },
            },
            allowGuestAccess: false,
            passwordFormat: {
              minLength: amplifyOutputs.auth.password_policy.min_length,
              requireLowercase: amplifyOutputs.auth.password_policy.require_lowercase,
              requireUppercase: amplifyOutputs.auth.password_policy.require_uppercase,
              requireNumbers: amplifyOutputs.auth.password_policy.require_numbers,
              requireSpecialCharacters: amplifyOutputs.auth.password_policy.require_symbols,
            },
          },
        },
      };

      console.log('🔧 Using amplify_outputs.json for development');
    } else {
      // Use environment configuration
      amplifyConfig = config.amplifyConfig;
      console.log(`🔧 Using ${config.environment} environment configuration`);
    }

    // Configure Amplify
    Amplify.configure(amplifyConfig);

    console.log('✅ Amplify configured successfully');
  } catch (error) {
    console.error('❌ Failed to configure Amplify:', error);
    throw error;
  }
};

/**
 * Get the current Amplify configuration
 */
export const getAmplifyConfig = (): AmplifyConfig => {
  return config.amplifyConfig;
};

/**
 * Get AgentCore API URL from configuration
 */
export const getAgentCoreUrl = (): string => {
  if (isDevelopment()) {
    // In development, use proxy path to avoid CORS issues
    if (amplifyOutputs?.custom?.agentCoreUrl) {
      return amplifyOutputs.custom.agentCoreUrl;
    }
    // Convert localhost URLs to use proxy
    const configUrl = config.agentCoreUrl;
    if (configUrl.startsWith('http://localhost:8080')) {
      return configUrl.replace('http://localhost:8080', '/api');
    }
    return configUrl;
  }
  return config.agentCoreUrl;
};

/**
 * Get API URL from configuration
 */
export const getApiUrl = (): string => {
  if (isDevelopment() && amplifyOutputs?.custom?.apiUrl) {
    return amplifyOutputs.custom.apiUrl;
  }
  return config.apiUrl;
};

/**
 * Check if Amplify is properly configured
 */
export const isAmplifyConfigured = (): boolean => {
  try {
    const currentConfig = Amplify.getConfig();
    return !!(currentConfig.Auth?.Cognito?.userPoolId && currentConfig.Auth?.Cognito?.userPoolClientId);
  } catch {
    return false;
  }
};

/**
 * Reset Amplify configuration (useful for testing)
 */
export const resetAmplifyConfig = (): void => {
  Amplify.configure({});
};

// Export a function to initialize Amplify configuration
export const initializeAmplify = async (): Promise<void> => {
  await configureAmplify();
};
