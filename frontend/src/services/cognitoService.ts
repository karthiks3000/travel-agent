/**
 * AWS Cognito service implementation
 * Based on requirements 2.2, 3.1, and 10.1
 */

import {
  signUp,
  signIn,
  signOut,
  getCurrentUser,
  fetchUserAttributes,
  confirmSignUp,
  resendSignUpCode,
  resetPassword,
  confirmResetPassword,
  fetchAuthSession,
  AuthError,
} from 'aws-amplify/auth';

import type {
  CognitoService,
  CognitoUser,
  SignUpParams,
  SignInParams,
  SignUpResult,
  SignInResult,
  ConfirmSignUpParams,
  ResetPasswordParams,
  ConfirmResetPasswordParams,
  AuthTokens,
  AuthErrorType,
} from '../types/auth';

/**
 * Implementation of CognitoService interface
 */
class CognitoServiceImpl implements CognitoService {
  /**
   * Sign up a new user
   */
  async signUp(params: SignUpParams): Promise<SignUpResult> {
    try {
      const { email, password, name } = params;
      
      const result = await signUp({
        username: email,
        password,
        options: {
          userAttributes: {
            email,
            given_name: name, // Map frontend 'name' to Cognito 'given_name'
          },
        },
      });

      return {
        isSignUpComplete: result.isSignUpComplete,
        nextStep: {
          signUpStep: result.nextStep.signUpStep,
          additionalInfo: (result.nextStep as any).additionalInfo,
        },
        userId: result.userId,
      };
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Sign in an existing user
   */
  async signIn(params: SignInParams): Promise<SignInResult> {
    try {
      const { email, password } = params;
      
      const result = await signIn({
        username: email,
        password,
      });

      return {
        isSignedIn: result.isSignedIn,
        nextStep: {
          signInStep: result.nextStep.signInStep,
          additionalInfo: (result.nextStep as any).additionalInfo,
        },
      };
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Sign out the current user
   */
  async signOut(): Promise<void> {
    try {
      await signOut();
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Get the current authenticated user
   */
  async getCurrentUser(): Promise<CognitoUser | null> {
    try {
      const user = await getCurrentUser();
      
      if (!user) {
        return null;
      }

      // Fetch user attributes separately to get complete user data
      const userAttributes = await fetchUserAttributes();

      return {
        userId: user.userId,
        username: user.username,
        signInDetails: user.signInDetails ? {
          loginId: user.signInDetails.loginId || '',
          authFlowType: user.signInDetails.authFlowType || '',
        } : undefined,
        attributes: {
          email: userAttributes.email || '',
          email_verified: userAttributes.email_verified,
          name: userAttributes.given_name || userAttributes.name || '',
          ...userAttributes,
        },
      };
    } catch (error) {
      // If user is not authenticated, return null instead of throwing
      if (this.isNotAuthenticatedError(error)) {
        return null;
      }
      throw this.handleAuthError(error);
    }
  }

  /**
   * Confirm user sign up with verification code
   */
  async confirmSignUp(params: ConfirmSignUpParams): Promise<void> {
    try {
      const { username, confirmationCode } = params;
      
      await confirmSignUp({
        username,
        confirmationCode,
      });
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Resend confirmation code for sign up
   */
  async resendConfirmationCode(username: string): Promise<void> {
    try {
      await resendSignUpCode({
        username,
      });
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Initiate password reset
   */
  async resetPassword(params: ResetPasswordParams): Promise<void> {
    try {
      const { username } = params;
      
      await resetPassword({
        username,
      });
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Confirm password reset with verification code
   */
  async confirmResetPassword(params: ConfirmResetPasswordParams): Promise<void> {
    try {
      const { username, confirmationCode, newPassword } = params;
      
      await confirmResetPassword({
        username,
        confirmationCode,
        newPassword,
      });
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Refresh authentication tokens
   */
  async refreshTokens(): Promise<AuthTokens> {
    try {
      const session = await fetchAuthSession({ forceRefresh: true });
      
      if (!session.tokens) {
        throw new Error('No tokens available');
      }

      return {
        accessToken: session.tokens.accessToken.toString(),
        idToken: session.tokens.idToken?.toString() || '',
        refreshToken: (session.tokens as any).refreshToken?.toString() || '',
      };
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Get current authentication tokens
   */
  async getTokens(): Promise<AuthTokens | null> {
    try {
      const session = await fetchAuthSession();
      
      if (!session.tokens) {
        return null;
      }

      return {
        accessToken: session.tokens.accessToken.toString(),
        idToken: session.tokens.idToken?.toString() || '',
        refreshToken: (session.tokens as any).refreshToken?.toString() || '',
      };
    } catch (error) {
      // If user is not authenticated, return null instead of throwing
      if (this.isNotAuthenticatedError(error)) {
        return null;
      }
      throw this.handleAuthError(error);
    }
  }

  /**
   * Handle and normalize authentication errors
   */
  private handleAuthError(error: any): Error {
    if (error instanceof AuthError) {
      const errorType = this.mapErrorToType(error.name);
      return new Error(`${errorType}: ${error.message}`);
    }
    
    if (error instanceof Error) {
      return error;
    }
    
    return new Error('An unknown authentication error occurred');
  }

  /**
   * Check if error indicates user is not authenticated
   */
  private isNotAuthenticatedError(error: any): boolean {
    if (error instanceof AuthError) {
      return error.name === 'UserUnAuthenticatedException' || 
             error.name === 'NotAuthorizedException';
    }
    return false;
  }

  /**
   * Map Cognito error names to our error types
   */
  private mapErrorToType(errorName: string): AuthErrorType {
    const errorMap: Record<string, AuthErrorType> = {
      'UserNotFoundException': 'UserNotFoundException',
      'NotAuthorizedException': 'NotAuthorizedException',
      'UserNotConfirmedException': 'UserNotConfirmedException',
      'CodeMismatchException': 'CodeMismatchException',
      'ExpiredCodeException': 'ExpiredCodeException',
      'InvalidParameterException': 'InvalidParameterException',
      'LimitExceededException': 'LimitExceededException',
      'TooManyRequestsException': 'TooManyRequestsException',
      'NetworkError': 'NetworkError',
    };

    return errorMap[errorName] || 'UnknownError';
  }
}

// Export singleton instance
export const cognitoService = new CognitoServiceImpl();

// Export class for testing
export { CognitoServiceImpl };
