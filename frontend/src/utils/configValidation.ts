/**
 * Configuration validation utility for travel agent frontend
 */

import { config, isDevelopment } from '../config/environment';
import { isAmplifyConfigured } from '../config/amplify';

export interface ValidationResult {
  isValid: boolean;
  issues: string[];
  warnings: string[];
}

/**
 * Validate the complete application configuration
 */
export const validateConfiguration = (): ValidationResult => {
  const issues: string[] = [];
  const warnings: string[] = [];

  // Check environment configuration
  if (!config) {
    issues.push('Environment configuration is not loaded');
    return { isValid: false, issues, warnings };
  }

  // Check Cognito configuration
  const { userPoolId, userPoolClientId } = config.amplifyConfig.Auth.Cognito;
  
  if (isDevelopment()) {
    // In development, check if we have mock values (which is OK)
    if (userPoolId.includes('XXXXXXXXX') || userPoolId === 'us-east-1_DEVMOCKPOOL') {
      warnings.push('Using mock Cognito configuration - deploy CDK stack and run generate-amplify-config.sh for real values');
    }
  } else {
    // In non-development, require real values
    if (!userPoolId || userPoolId.includes('XXXXXXXXX') || userPoolId.includes('MOCK')) {
      issues.push('Invalid or missing VITE_COGNITO_USER_POOL_ID');
    }
    
    if (!userPoolClientId || userPoolClientId.includes('XXXXXXXXX') || userPoolClientId.includes('MOCK')) {
      issues.push('Invalid or missing VITE_COGNITO_USER_POOL_CLIENT_ID');
    }
  }

  // Check API URLs
  if (!config.apiUrl) {
    issues.push('API URL is not configured');
  }

  if (!config.agentCoreUrl) {
    issues.push('AgentCore URL is not configured');
  }

  // Check production HTTPS requirement
  if (config.environment === 'production') {
    if (!config.apiUrl.startsWith('https://')) {
      issues.push('Production API URL must use HTTPS');
    }
    
    if (!config.agentCoreUrl.startsWith('https://')) {
      issues.push('Production AgentCore URL must use HTTPS');
    }
  }

  return {
    isValid: issues.length === 0,
    issues,
    warnings
  };
};

/**
 * Check if Amplify is properly initialized
 */
export const checkAmplifyStatus = (): { configured: boolean; message: string } => {
  try {
    const configured = isAmplifyConfigured();
    return {
      configured,
      message: configured 
        ? '✅ Amplify is properly configured'
        : '❌ Amplify is not configured - call configureAmplify() first'
    };
  } catch (error) {
    return {
      configured: false,
      message: `❌ Error checking Amplify status: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
};

/**
 * Print configuration validation results to console
 */
export const logValidationResults = (): ValidationResult => {
  const result = validateConfiguration();
  const amplifyStatus = checkAmplifyStatus();

  console.log('\n🔍 Configuration Validation Results:');
  console.log('=====================================');
  
  console.log(`Environment: ${config.environment}`);
  console.log(`${amplifyStatus.message}`);
  
  if (result.warnings.length > 0) {
    console.log('\n⚠️  Warnings:');
    result.warnings.forEach(warning => console.log(`  - ${warning}`));
  }
  
  if (result.issues.length > 0) {
    console.log('\n❌ Issues:');
    result.issues.forEach(issue => console.log(`  - ${issue}`));
  } else {
    console.log('\n✅ No critical issues found');
  }
  
  console.log('=====================================\n');
  
  return result;
};
