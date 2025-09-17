/**
 * Chat state store using Zustand
 * Based on requirements 4.1, 9.1, and 10.1
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { agentCoreClient } from '../services/agentCoreClient';
import { useAuthStore } from './authStore';
import type { 
  ChatStore, 
  Message, 
  ResultData,
  AgentCoreRequest 
} from '../types/chat';

/**
 * Generate a unique session ID
 */
const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Generate a unique message ID
 */
const generateMessageId = (): string => {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Chat store implementation with Zustand
 * Manages conversation state and AgentCore integration
 */
export const useChatStore = create<ChatStore>()(
  subscribeWithSelector((set, get) => ({
    // State
    sessionId: generateSessionId(),
    isSessionActive: false,
    messages: [],
    currentResults: null,
    resultType: null,
    isLoading: false,
    isSending: false,
    error: null,

    // Message actions
    sendMessage: async (content: string) => {
      const { sessionId, messages } = get();
      const authStore = useAuthStore.getState();

      // Check if user is authenticated
      if (!authStore.isAuthenticated || !authStore.tokens?.accessToken) {
        set({ error: 'You must be signed in to send messages' });
        return;
      }

      // Clear any previous errors
      set({ error: null, isSending: true });

      // Add user message immediately
      const userMessage: Message = {
        id: generateMessageId(),
        content: content.trim(),
        sender: 'user',
        timestamp: new Date(),
        metadata: {
          sessionId,
        },
      };

      set({
        messages: [...messages, userMessage],
        isSessionActive: true,
      });

      try {
        // Prepare AgentCore request
        const request: AgentCoreRequest = {
          sessionId,
          message: content.trim(),
          authToken: authStore.tokens.accessToken,
          metadata: {
            userId: authStore.user?.userId,
            timestamp: new Date().toISOString(),
          },
        };

        // Call AgentCore API
        const response = await agentCoreClient.invokeAgent(request);

        // Create agent message
        const agentMessage: Message = {
          id: generateMessageId(),
          content: response.message,
          sender: 'agent',
          timestamp: new Date(),
          metadata: {
            sessionId: response.sessionId,
            resultType: response.resultType,
            resultData: response.resultData,
          },
        };

        // Update state with agent response
        const currentMessages = get().messages;
        set({
          messages: [...currentMessages, agentMessage],
          currentResults: response.resultData || null,
          resultType: response.resultType || null,
          isSending: false,
          error: null,
        });

      } catch (error) {
        // Handle API errors
        const errorMessage = error instanceof Error ? error.message : 'Failed to send message';
        
        // Add error message to chat
        const errorAgentMessage: Message = {
          id: generateMessageId(),
          content: `I'm sorry, I encountered an error: ${errorMessage}. Please try again.`,
          sender: 'agent',
          timestamp: new Date(),
          metadata: {
            sessionId,
            error: true,
          },
        };

        const currentMessages = get().messages;
        set({
          messages: [...currentMessages, errorAgentMessage],
          isSending: false,
          error: errorMessage,
        });
      }
    },

    addMessage: (messageData) => {
      const { messages } = get();
      const message: Message = {
        ...messageData,
        id: generateMessageId(),
        timestamp: new Date(),
      };

      set({
        messages: [...messages, message],
      });
    },

    // Session actions
    startNewSession: () => {
      const newSessionId = generateSessionId();
      set({
        sessionId: newSessionId,
        isSessionActive: true,
        messages: [],
        currentResults: null,
        resultType: null,
        error: null,
      });
    },

    endSession: () => {
      set({
        isSessionActive: false,
        error: null,
      });
    },

    clearSession: () => {
      const newSessionId = generateSessionId();
      set({
        sessionId: newSessionId,
        isSessionActive: false,
        messages: [],
        currentResults: null,
        resultType: null,
        isLoading: false,
        isSending: false,
        error: null,
      });
    },

    // Result actions
    setResults: (results: ResultData) => {
      set({
        currentResults: results,
        resultType: results.type,
      });
    },

    clearResults: () => {
      set({
        currentResults: null,
        resultType: null,
      });
    },

    // Error actions
    setError: (error: string | null) => {
      set({ error });
    },

    clearError: () => {
      set({ error: null });
    },

    // Loading actions
    setLoading: (loading: boolean) => {
      set({ isLoading: loading });
    },

    setSending: (sending: boolean) => {
      set({ isSending: sending });
    },
  }))
);

/**
 * Hook to get chat statistics
 */
export const useChatStats = () => {
  return useChatStore((state) => ({
    messageCount: state.messages.length,
    userMessageCount: state.messages.filter(m => m.sender === 'user').length,
    agentMessageCount: state.messages.filter(m => m.sender === 'agent').length,
    hasResults: !!state.currentResults,
    isActive: state.isSessionActive,
  }));
};

/**
 * Hook to get only messages (for performance)
 */
export const useChatMessages = () => {
  return useChatStore((state) => state.messages);
};

/**
 * Hook to get only results (for performance)
 */
export const useChatResults = () => {
  return useChatStore((state) => ({
    currentResults: state.currentResults,
    resultType: state.resultType,
  }));
};
