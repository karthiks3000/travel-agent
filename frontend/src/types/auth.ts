/**
 * TypeScript interfaces for AWS Cognito authentication
 * Based on requirements 2.2, 3.1, and 10.1
 */

// Core authentication interfaces
export interface CognitoUser {
  userId: string;
  username: string;
  signInDetails?: {
    loginId: string;
    authFlowType: string;
  };
  attributes: {
    email: string;
    email_verified?: string;
    name?: string;
    [key: string]: string | undefined;
  };
}

export interface AuthTokens {
  accessToken: string;
  idToken: string;
  refreshToken: string;
}

export interface AuthState {
  user: CognitoUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  tokens: AuthTokens | null;
  error: string | null;
}

// Authentication service interfaces
export interface SignUpParams {
  email: string;
  password: string;
  name: string;
}

export interface SignInParams {
  email: string;
  password: string;
}

export interface SignUpResult {
  isSignUpComplete: boolean;
  nextStep: {
    signUpStep: string;
    additionalInfo?: Record<string, any>;
  };
  userId?: string;
}

export interface SignInResult {
  isSignedIn: boolean;
  nextStep: {
    signInStep: string;
    additionalInfo?: Record<string, any>;
  };
}

export interface ConfirmSignUpParams {
  username: string;
  confirmationCode: string;
}

export interface ResetPasswordParams {
  username: string;
}

export interface ConfirmResetPasswordParams {
  username: string;
  confirmationCode: string;
  newPassword: string;
}

// Cognito service interface
export interface CognitoService {
  signUp: (params: SignUpParams) => Promise<SignUpResult>;
  signIn: (params: SignInParams) => Promise<SignInResult>;
  signOut: () => Promise<void>;
  getCurrentUser: () => Promise<CognitoUser | null>;
  confirmSignUp: (params: ConfirmSignUpParams) => Promise<void>;
  resendConfirmationCode: (username: string) => Promise<void>;
  resetPassword: (params: ResetPasswordParams) => Promise<void>;
  confirmResetPassword: (params: ConfirmResetPasswordParams) => Promise<void>;
  refreshTokens: () => Promise<AuthTokens>;
  getTokens: () => Promise<AuthTokens | null>;
}

// Authentication store interface for Zustand
export interface AuthStore extends AuthState {
  // Actions
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name: string) => Promise<void>;
  signOut: () => Promise<void>;
  confirmSignUp: (username: string, confirmationCode: string) => Promise<void>;
  resendConfirmationCode: (username: string) => Promise<void>;
  resetPassword: (username: string) => Promise<void>;
  confirmResetPassword: (username: string, confirmationCode: string, newPassword: string) => Promise<void>;
  refreshTokens: () => Promise<void>;
  checkAuthState: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

// Error types for better error handling
export interface AuthError {
  name: string;
  message: string;
  code?: string;
}

export type AuthErrorType = 
  | 'UserNotFoundException'
  | 'NotAuthorizedException'
  | 'UserNotConfirmedException'
  | 'CodeMismatchException'
  | 'ExpiredCodeException'
  | 'InvalidParameterException'
  | 'LimitExceededException'
  | 'TooManyRequestsException'
  | 'NetworkError'
  | 'UnknownError';

// Form validation interfaces
export interface FormValidation {
  isValid: boolean;
  errors: Record<string, string>;
}

export interface SignUpFormData {
  email: string;
  password: string;
  confirmPassword: string;
  name: string;
}

export interface SignInFormData {
  email: string;
  password: string;
  rememberMe: boolean;
}

