/**
 * AgentCore API client service
 * Based on requirements 10.1, 10.2, 10.3, and 10.5
 */

import { getAgentCoreUrl } from '../config/amplify';
import type { AgentCoreClient, AgentCoreRequest, AgentCoreResponse } from '../types/chat';

/**
 * AgentCore client implementation
 */
class AgentCoreClientImpl implements AgentCoreClient {
  private baseUrl: string;
  private maxRetries: number = 3;
  private retryDelay: number = 1000; // 1 second base delay

  constructor() {
    this.baseUrl = getAgentCoreUrl();
  }

  /**
   * Invoke the travel orchestrator agent with streaming support
   */
  async invokeAgent(
    request: AgentCoreRequest,
    onStreamChunk?: (chunk: string, isThinking: boolean) => void
  ): Promise<AgentCoreResponse> {
    const { sessionId, message, authToken } = request;

    const payload = {
      prompt: message,
    };

    return this.makeRequest('', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'Authorization': `Bearer ${authToken}`,
        'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': sessionId,
      },
      body: JSON.stringify(payload),
    }, onStreamChunk);
  }

  /**
   * Health check for AgentCore service
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      return response.ok;
    } catch (error) {
      console.warn('AgentCore health check failed:', error);
      return false;
    }
  }

  /**
   * Make HTTP request with retry logic and exponential backoff
   */
  private async makeRequest(
    endpoint: string, 
    options: RequestInit,
    onStreamChunk?: (chunk: string, isThinking: boolean) => void
  ): Promise<AgentCoreResponse> {
    const url = `${this.baseUrl}${endpoint}`;
    let lastError: Error = new Error('Unknown error');

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        const response = await fetch(url, {
          ...options,
          // Add timeout
          signal: AbortSignal.timeout(30000), // 30 second timeout
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const contentType = response.headers.get('content-type') || '';
        
        // Handle streaming response
        if (contentType.includes('text/event-stream')) {
          return this.handleStreamingResponse(response, onStreamChunk);
        }
        
        // Handle JSON response
        if (contentType.includes('application/json')) {
          const data = await response.json();
          
          // Validate response structure
          if (!this.isValidAgentCoreResponse(data)) {
            throw new Error('Invalid response format from AgentCore');
          }
          
          return data;
        }
        
        // Fallback: try to parse as JSON
        const data = await response.json();
        
        // Validate response structure
        if (!this.isValidAgentCoreResponse(data)) {
          throw new Error('Invalid response format from AgentCore');
        }
        
        return data;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
        
        // Don't retry on authentication errors or client errors (4xx)
        if (error instanceof Error && error.message.includes('HTTP 4')) {
          throw lastError;
        }

        // Don't retry on the last attempt
        if (attempt === this.maxRetries) {
          break;
        }

        // Calculate exponential backoff delay
        const delay = this.retryDelay * Math.pow(2, attempt);
        console.warn(`AgentCore request failed (attempt ${attempt + 1}/${this.maxRetries + 1}), retrying in ${delay}ms:`, lastError.message);
        
        await this.sleep(delay);
      }
    }

    throw new Error(`AgentCore request failed after ${this.maxRetries + 1} attempts: ${lastError.message}`);
  }

  /**
   * Handle streaming response from AgentCore with real-time callbacks
   */
  private async handleStreamingResponse(
    response: Response,
    onStreamChunk?: (chunk: string, isThinking: boolean) => void
  ): Promise<AgentCoreResponse> {
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is not readable');
    }

    const decoder = new TextDecoder();
    const allContent: string[] = [];
    let sessionId = '';
    let currentThinkingContent = '';
    let isInThinkingBlock = false;
    let finalMessage = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6); // Remove 'data: ' prefix
            if (data.trim() && data !== '[DONE]') {
              try {
                const parsed = JSON.parse(data);
                
                // Extract session ID
                if (parsed.sessionId && !sessionId) {
                  sessionId = parsed.sessionId;
                }
                
                // Handle contentBlockDelta events (real-time text chunks)
                if (parsed.event?.contentBlockDelta?.delta?.text) {
                  const textChunk = parsed.event.contentBlockDelta.delta.text;
                  allContent.push(textChunk);
                  
                  // Check if we're entering/exiting thinking block
                  if (textChunk.includes('<thinking>')) {
                    isInThinkingBlock = true;
                    currentThinkingContent += textChunk;
                  } else if (textChunk.includes('</thinking>')) {
                    isInThinkingBlock = false;
                    currentThinkingContent = '';
                  } else if (isInThinkingBlock) {
                    // Accumulating thinking content (not displayed)
                    currentThinkingContent += textChunk;
                  } else {
                    // This is non-thinking content, show it to user
                    if (onStreamChunk && textChunk.trim()) {
                      onStreamChunk(textChunk, false);
                    }
                  }
                }
                
                // Handle final message with structured content
                if (parsed.message?.content) {
                  const content = parsed.message.content;
                  if (Array.isArray(content) && content[0]?.text) {
                    finalMessage = content[0].text;
                  }
                }
                
                } catch {
                // If it's not JSON, treat as plain text
                console.warn('Non-JSON data in stream:', data);
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }

    // Process final content and extract results
    const fullText = finalMessage || allContent.join('');
    
    // Remove thinking tags from final message
    const cleanedMessage = this.removeThinkingTags(fullText);
    
    // Try to extract structured results from final response
    const extractedResults = this.extractStructuredResults(fullText);
    
    // Construct response from streamed content
    const response_data: AgentCoreResponse = {
      message: cleanedMessage,
      sessionId: sessionId || `travel-session-${Date.now()}-${crypto.randomUUID().substr(0, 8)}`,
      resultType: extractedResults?.type as 'flights' | 'accommodations' | 'restaurants' | 'itinerary' | undefined,
      resultData: extractedResults?.data as any,
    };

    if (!this.isValidAgentCoreResponse(response_data)) {
      throw new Error('Invalid streaming response format from AgentCore');
    }

    return response_data;
  }

  /**
   * Remove thinking tags from message content
   */
  private removeThinkingTags(text: string): string {
    return text.replace(/<thinking>[\s\S]*?<\/thinking>/g, '').trim();
  }

  /**
   * Extract structured results from agent response for ResultsPanel
   */
  private extractStructuredResults(text: string): { type: string; data: Record<string, unknown> } | null {
    try {
      // Look for restaurant data pattern
      if (text.includes('restaurants') && (text.includes('Address:') || text.includes('Rating:'))) {
        const restaurants: Record<string, unknown>[] = [];
        
        // Parse restaurant data from the text
        const restaurantMatches = text.match(/\*\*([^*]+)\*\*[\s\S]*?- \*\*Address:\*\* ([^\n]+)[\s\S]*?- \*\*Rating:\*\* ([^\n]+)[\s\S]*?- \*\*Price Level:\*\* ([^\n]+)[\s\S]*?- \*\*Phone Number:\*\* ([^\n]+)/g);
        
        if (restaurantMatches) {
          restaurantMatches.forEach(match => {
            const name = match.match(/\*\*([^*]+)\*\*/)?.[1];
            const address = match.match(/\*\*Address:\*\* ([^\n]+)/)?.[1];
            const rating = match.match(/\*\*Rating:\*\* ([^\n]+)/)?.[1];
            const priceLevel = match.match(/\*\*Price Level:\*\* ([^\n]+)/)?.[1];
            const phone = match.match(/\*\*Phone Number:\*\* ([^\n]+)/)?.[1];
            
            if (name) {
              restaurants.push({
                name: name.trim(),
                address: address?.trim() || '',
                rating: parseFloat(rating || '0') || 0,
                price_level: priceLevel?.trim() || '',
                phone_number: phone?.trim() || '',
                is_open_now: true // Default assumption
              });
            }
          });
        }
        
        if (restaurants.length > 0) {
          return {
            type: 'restaurants',
            data: {
              restaurants,
              recommendation: text.substring(0, 200) + '...',
              timestamp: new Date().toISOString(),
              type: 'restaurants'
            }
          };
        }
      }
      
      // Look for flight data patterns (similar logic for other result types)
      // Look for accommodation data patterns
      
      return null;
    } catch (e) {
      console.warn('Failed to extract structured results:', e);
      return null;
    }
  }

  /**
   * Validate AgentCore response structure
   */
  private isValidAgentCoreResponse(data: unknown): data is AgentCoreResponse {
    return (
      typeof data === 'object' &&
      data !== null &&
      typeof (data as Record<string, unknown>).message === 'string' &&
      typeof (data as Record<string, unknown>).sessionId === 'string'
    );
  }

  /**
   * Sleep utility for retry delays
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Export singleton instance
export const agentCoreClient = new AgentCoreClientImpl();

// Export class for testing
export { AgentCoreClientImpl };
