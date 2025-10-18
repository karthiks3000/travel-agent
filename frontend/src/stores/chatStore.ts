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
  AgentCoreRequest,
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
    // Tool progress state
    thinkingMessage: null,
    toolProgress: [],

    // Message actions
    sendMessage: async (content: string) => {
      const { sessionId, messages } = get();
      const authStore = useAuthStore.getState();

      // Check if user is authenticated
      if (!authStore.isAuthenticated || !authStore.tokens?.accessToken) {
        set({ error: 'You must be signed in to send messages' });
        return;
      }

      // Clear any previous state and start streaming
      set({ 
        error: null, 
        isSending: true,
        isStreaming: true,
        streamingMessage: '',
        streamingMessageId: generateMessageId(),
        // Clear progress state
        thinkingMessage: null,
        toolProgress: []
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

        // Call AgentCore API with SSE streaming
        await agentCoreClient.invokeAgentStreaming(request, {
          onStatus: (status, message) => {
            console.log('🧠 SSE Status callback fired:', status, message);
            set({ thinkingMessage: message });
          },
          onToolStart: (tool) => {
            console.log('🔄 SSE Tool Start callback fired:', tool);
            const current = get().toolProgress;
            const updated = current.filter(t => t.tool_id !== tool.tool_id);
            updated.push(tool);
            console.log('🔄 Updated toolProgress array:', updated);
            set({ toolProgress: updated });
          },
          onToolComplete: (tool) => {
            console.log('✅ SSE Tool Complete callback fired:', tool);
            const current = get().toolProgress;
            const updated = current.map(t => 
              t.tool_id === tool.tool_id ? { ...t, ...tool } : t
            );
            console.log('✅ Updated toolProgress array:', updated);
            set({ toolProgress: updated });
          },
          onFinalResponse: (response) => {
            // Process final response and create agent message
            let resultType: ResultType | null = null;
            let resultData: ResultData | null = null;
            const displayMessage = response.message || "No response";

            // Handle responses with results
            if (response.success && response.response_type) {
              switch (response.response_type) {
                case "flights":
                  resultType = "flights";
                  if (response.flight_results) {
                    resultData = {
                      type: "flights" as const,
                      flights: response.flight_results,
                      timestamp: new Date()
                    };
                  }
                  break;
                case "accommodations":
                  resultType = "accommodations";
                  if (response.accommodation_results) {
                    resultData = {
                      type: "accommodations" as const,
                      best_accommodations: response.accommodation_results,
                      timestamp: new Date()
                    };
                  }
                  break;
                case "restaurants":
                  resultType = "restaurants";
                  if (response.restaurant_results) {
                    resultData = {
                      type: "restaurants" as const,
                      restaurants: response.restaurant_results,
                      total_results: response.restaurant_results.length,
                      timestamp: new Date()
                    };
                  }
                  break;
                case "attractions":
                  resultType = "attractions";
                  if (response.attraction_results) {
                    resultData = {
                      type: "attractions" as const,
                      attractions: response.attraction_results,
                      total_results: response.attraction_results.length,
                      timestamp: new Date()
                    };
                  }
                  break;
                case "itinerary":
                  resultType = "itinerary";
                  if (response.itinerary) {
                    resultData = {
                      type: "itinerary" as const,
                      timestamp: new Date(),
                      ...response.itinerary
                    };
                  }
                  break;
              }
            }

            // Create final agent message
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

            // Update state with final response and clear streaming/progress
            const currentMessages = get().messages;
            
            set({
              messages: [...currentMessages, agentMessage],
              currentResults: resultData,
              resultType: resultType,
              isSending: false,
              isStreaming: false,
              streamingMessage: null,
              streamingMessageId: null,
              thinkingMessage: null,
              toolProgress: [],
              error: null,
            });
          },
          onError: (errorMessage) => {
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
              thinkingMessage: null,
              toolProgress: [],
              error: errorMessage,
            });
          }
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
          thinkingMessage: null,
          toolProgress: [],
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

/**
 * Hook to get tool progress state (for ProgressPanel)
 */
export const useToolProgress = () => {
  const thinkingMessage = useChatStore((state) => state.thinkingMessage);
  const toolProgress = useChatStore((state) => state.toolProgress);
  const isSending = useChatStore((state) => state.isSending);

  const result = {
    thinkingMessage,
    toolProgress,
    isActive: isSending && (thinkingMessage !== null || toolProgress.length > 0),
  };

  console.log('🎯 useToolProgress hook result:', result);

  return result;
};
