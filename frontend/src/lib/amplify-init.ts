/**
 * Amplify initialization utility
 * This module handles the async initialization of Amplify configuration
 */

import { initializeAmplify } from '../config/amplify';

let isInitialized = false;
let initializationPromise: Promise<void> | null = null;

/**
 * Initialize Amplify configuration
 * This function ensures Amplify is only initialized once
 */
export const initAmplify = async (): Promise<void> => {
  if (isInitialized) {
    return;
  }

  if (initializationPromise) {
    return initializationPromise;
  }

  initializationPromise = (async () => {
    try {
      await initializeAmplify();
      isInitialized = true;
      console.log('✅ Amplify initialization complete');
    } catch (error) {
      console.error('❌ Amplify initialization failed:', error);
      throw error;
    }
  })();

  return initializationPromise;
};

/**
 * Check if Amplify has been initialized
 */
export const isAmplifyInitialized = (): boolean => {
  return isInitialized;
};

/**
 * Reset initialization state (useful for testing)
 */
export const resetInitialization = (): void => {
  isInitialized = false;
  initializationPromise = null;
};