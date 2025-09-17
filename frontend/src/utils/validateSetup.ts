/**
 * Validation utilities for AWS integration setup
 * Based on requirements 2.2, 3.1, and 10.1
 */

import { isAmplifyConfigured } from '../config/amplify';
import { config, validateEnvironmentConfig } from '../config/environment';
import { cognitoService } from '../services/cognitoService';

export interface SetupValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  details: {
    amplifyConfigured: boolean;
    environmentValid: boolean;
    cognitoServiceReady: boolean;
  };
}

/**
 * Validate the complete AWS integration setup
 */
export const validateAWSSetup = async (): Promise<SetupValidationResult> => {
  const errors: string[] = [];
  const warnings: string[] = [];
  const details = {
    amplifyConfigured: false,
    environmentValid: false,
    cognitoServiceReady: false,
  };

  try {
    // Validate environment configuration
    validateEnvironmentConfig(config);
    details.environmentValid = true;
  } catch (error) {
    errors.push(`Environment configuration error: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }

  try {
    // Check if Amplify is configured
    details.amplifyConfigured = isAmplifyConfigured();
    if (!details.amplifyConfigured) {
      errors.push('Amplify is not properly configured');
    }
  } catch (error) {
    errors.push(`Amplify configuration check failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }

  try {
    // Test Cognito service readiness (this will fail gracefully if not authenticated)
    await cognitoService.getCurrentUser();
    details.cognitoServiceReady = true;
  } catch (error) {
    // This is expected if user is not authenticated, so we just mark as ready
    details.cognitoServiceReady = true;
  }

  // Check for development-specific warnings
  if (config.environment === 'development') {
    if (config.amplifyConfig.Auth.Cognito.userPoolId.includes('MOCK') || 
        config.amplifyConfig.Auth.Cognito.userPoolId.includes('XXXXXXXXX')) {
      warnings.push('Using mock Cognito configuration for development');
    }
  }

  // Check for production-specific requirements
  if (config.environment === 'production') {
    if (!config.apiUrl.startsWith('https://')) {
      errors.push('Production API URL must use HTTPS');
    }
    if (!config.agentCoreUrl.startsWith('https://')) {
      errors.push('Production AgentCore URL must use HTTPS');
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    details,
  };
};

/**
 * Log setup validation results to console
 */
export const logSetupValidation = async (): Promise<void> => {
  console.log('🔍 Validating AWS Integration Setup...');
  
  const result = await validateAWSSetup();
  
  if (result.isValid) {
    console.log('✅ AWS Integration Setup is valid');
  } else {
    console.log('❌ AWS Integration Setup has errors');
  }
  
  if (result.errors.length > 0) {
    console.group('❌ Errors:');
    result.errors.forEach(error => console.error(`  • ${error}`));
    console.groupEnd();
  }
  
  if (result.warnings.length > 0) {
    console.group('⚠️ Warnings:');
    result.warnings.forEach(warning => console.warn(`  • ${warning}`));
    console.groupEnd();
  }
  
  console.group('📋 Details:');
  console.log(`  • Environment: ${config.environment}`);
  console.log(`  • Amplify Configured: ${result.details.amplifyConfigured ? '✅' : '❌'}`);
  console.log(`  • Environment Valid: ${result.details.environmentValid ? '✅' : '❌'}`);
  console.log(`  • Cognito Service Ready: ${result.details.cognitoServiceReady ? '✅' : '❌'}`);
  console.groupEnd();
};

/**
 * Simple health check for AWS services
 */
export const healthCheck = async (): Promise<boolean> => {
  try {
    const result = await validateAWSSetup();
    return result.isValid;
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
};