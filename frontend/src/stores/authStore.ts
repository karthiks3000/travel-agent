/**
 * Authentication state store using Zustand
 * Based on requirements 2.2, 3.1, and 6.1
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { cognitoService } from '../services/cognitoService';
import type { AuthStore } from '../types/auth';

/**
 * Authentication store implementation with Zustand
 * Includes persistence for tokens and user data
 */
export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // State
      user: null,
      isAuthenticated: false,
      isLoading: false,
      tokens: null,
      error: null,

      // Actions
      signIn: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const result = await cognitoService.signIn({ email, password });
          
          if (result.isSignedIn) {
            // Get user data and tokens after successful sign in
            const [user, tokens] = await Promise.all([
              cognitoService.getCurrentUser(),
              cognitoService.getTokens(),
            ]);

            set({
              user,
              tokens,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          } else {
            // Handle additional steps (MFA, password change, etc.)
            set({
              isLoading: false,
              error: `Additional step required: ${result.nextStep.signInStep}`,
            });
          }
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Sign in failed',
            user: null,
            tokens: null,
            isAuthenticated: false,
          });
          throw error;
        }
      },

      signUp: async (email: string, password: string, name: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const result = await cognitoService.signUp({ email, password, name });
          
          if (result.isSignUpComplete) {
            // Auto sign in after successful sign up
            await get().signIn(email, password);
          } else {
            // Handle email verification step
            set({
              isLoading: false,
              error: null,
            });
          }
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Sign up failed',
          });
          throw error;
        }
      },

      signOut: async () => {
        set({ isLoading: true, error: null });
        
        try {
          await cognitoService.signOut();
          
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          // Even if sign out fails, clear local state
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false,
            error: error instanceof Error ? error.message : 'Sign out failed',
          });
        }
      },

      confirmSignUp: async (username: string, confirmationCode: string) => {
        set({ isLoading: true, error: null });
        
        try {
          await cognitoService.confirmSignUp({ username, confirmationCode });
          
          set({
            isLoading: false,
            error: null,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Confirmation failed',
          });
          throw error;
        }
      },

      resendConfirmationCode: async (username: string) => {
        set({ isLoading: true, error: null });
        
        try {
          await cognitoService.resendConfirmationCode(username);
          
          set({
            isLoading: false,
            error: null,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Failed to resend code',
          });
          throw error;
        }
      },

      resetPassword: async (username: string) => {
        set({ isLoading: true, error: null });
        
        try {
          await cognitoService.resetPassword({ username });
          
          set({
            isLoading: false,
            error: null,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Password reset failed',
          });
          throw error;
        }
      },

      confirmResetPassword: async (username: string, confirmationCode: string, newPassword: string) => {
        set({ isLoading: true, error: null });
        
        try {
          await cognitoService.confirmResetPassword({ username, confirmationCode, newPassword });
          
          set({
            isLoading: false,
            error: null,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Password reset confirmation failed',
          });
          throw error;
        }
      },

      refreshTokens: async () => {
        const { tokens } = get();
        
        if (!tokens) {
          throw new Error('No tokens available to refresh');
        }

        try {
          const newTokens = await cognitoService.refreshTokens();
          
          set({
            tokens: newTokens,
            error: null,
          });
        } catch (error) {
          // If token refresh fails, sign out the user
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            error: error instanceof Error ? error.message : 'Token refresh failed',
          });
          throw error;
        }
      },

      checkAuthState: async () => {
        set({ isLoading: true, error: null });
        
        try {
          const [user, tokens] = await Promise.all([
            cognitoService.getCurrentUser(),
            cognitoService.getTokens(),
          ]);

          if (user && tokens) {
            set({
              user,
              tokens,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          } else {
            set({
              user: null,
              tokens: null,
              isAuthenticated: false,
              isLoading: false,
              error: null,
            });
          }
        } catch (error) {
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false,
            error: error instanceof Error ? error.message : 'Auth check failed',
          });
        }
      },

      clearError: () => {
        set({ error: null });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      // Only persist user data and tokens, not loading states or errors
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
      }),
      // Rehydrate authentication state on app load
      onRehydrateStorage: () => (state) => {
        if (state?.tokens && state?.user) {
          // Verify tokens are still valid on rehydration
          state.checkAuthState?.();
        }
      },
    }
  )
);
