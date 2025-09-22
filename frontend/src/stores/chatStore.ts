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
  ResultType,
  AgentCoreRequest 
} from '../types/chat';

/**
 * Generate a unique session ID (matches backend format and meets ≥33 char requirement)
 */
const generateSessionId = (): string => {
  // Match backend format: travel-session-YYYYMMDDHHMMSS-uuid8chars
  const now = new Date();
  const timestamp = now.toISOString().replace(/[-:T.]/g, '').substr(0, 14); // YYYYMMDDHHMMSS
  const uuidSuffix = crypto.randomUUID().substr(0, 8); // First 8 chars of UUID
  return `travel-session-${timestamp}-${uuidSuffix}`; // 38 characters total
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
    // Streaming state
    streamingMessage: null,
    isStreaming: false,
    streamingMessageId: null,

    // Message actions
    sendMessage: async (content: string) => {
      const { sessionId, messages } = get();
      const authStore = useAuthStore.getState();

      // Check if user is authenticated
      if (!authStore.isAuthenticated || !authStore.tokens?.accessToken) {
        set({ error: 'You must be signed in to send messages' });
        return;
      }

      // Clear any previous errors and start streaming
      set({ 
        error: null, 
        isSending: true,
        isStreaming: true,
        streamingMessage: '',
        streamingMessageId: generateMessageId()
      });

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

        // Call AgentCore API with JSON response (non-streaming)
        const response = await agentCoreClient.invokeAgent(request);

        // Process response based on new backend format
        let resultType: ResultType | null = null;
        let resultData: ResultData | null = null;
        const displayMessage = response.message || "No response";

        // Handle complete_success responses with results
        if (response.response_status === "complete_success" && response.response_type) {
          // Map response_type to resultType and extract appropriate data
          switch (response.response_type) {
            case "flights":
              resultType = "flights";
              if (response.flight_results) {
                resultData = {
                  ...response.flight_results,
                  type: "flights" as const,
                  timestamp: new Date()
                };
              }
              break;
            case "accommodations":
              resultType = "accommodations";
              if (response.accommodation_results) {
                resultData = {
                  ...response.accommodation_results,
                  type: "accommodations" as const,
                  timestamp: new Date()
                };
              }
              break;
            case "restaurants":
              resultType = "restaurants";
              if (response.restaurant_results) {
                resultData = {
                  ...response.restaurant_results,
                  type: "restaurants" as const,
                  timestamp: new Date()
                };
              }
              break;
            case "itinerary":
              resultType = "itinerary";
              if (response.comprehensive_plan) {
                resultData = response.comprehensive_plan;
              }
              break;
            default:
              // conversation or other types - no structured results
              break;
          }
        }

        // Create final agent message when streaming is complete
        const agentMessage: Message = {
          id: get().streamingMessageId || generateMessageId(),
          content: displayMessage,
          sender: 'agent',
          timestamp: new Date(),
          metadata: {
            sessionId: response.sessionId || sessionId,
            resultType: resultType || undefined,
            resultData: resultData || undefined,
            responseStatus: response.response_status,
            responseType: response.response_type,
          },
        };

        // Update state with final response and clear streaming
        const currentMessages = get().messages;
        
        // Debug logging
        console.log('🔍 Setting results in store:', {
          resultType,
          resultData,
          responseType: response.response_type,
          responseStatus: response.response_status
        });
        
        set({
          messages: [...currentMessages, agentMessage],
          currentResults: resultData,
          resultType: resultType,
          isSending: false,
          isStreaming: false,
          streamingMessage: null,
          streamingMessageId: null,
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
          isStreaming: false,
          streamingMessage: null,
          streamingMessageId: null,
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
  const messages = useChatStore((state) => state.messages);
  const currentResults = useChatStore((state) => state.currentResults);
  const isSessionActive = useChatStore((state) => state.isSessionActive);

  return {
    messageCount: messages.length,
    userMessageCount: messages.filter(m => m.sender === 'user').length,
    agentMessageCount: messages.filter(m => m.sender === 'agent').length,
    hasResults: !!currentResults,
    isActive: isSessionActive,
  };
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
  const currentResults = useChatStore((state) => state.currentResults);
  const resultType = useChatStore((state) => state.resultType);

  return {
    currentResults,
    resultType,
  };
};

/**
 * Hook to get streaming state (for real-time display)
 */
export const useChatStreaming = () => {
  const streamingMessage = useChatStore((state) => state.streamingMessage);
  const isStreaming = useChatStore((state) => state.isStreaming);
  const streamingMessageId = useChatStore((state) => state.streamingMessageId);

  return {
    streamingMessage,
    isStreaming,
    streamingMessageId,
  };
};
