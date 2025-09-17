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
   * Invoke the travel orchestrator agent
   */
  async invokeAgent(request: AgentCoreRequest): Promise<AgentCoreResponse> {
    const { sessionId, message, authToken, metadata } = request;

    const payload = {
      sessionId,
      message,
      metadata: {
        ...metadata,
        timestamp: new Date().toISOString(),
      },
    };

    return this.makeRequest('/api/v1/invoke', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
      },
      body: JSON.stringify(payload),
    });
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
  private async makeRequest(endpoint: string, options: RequestInit): Promise<AgentCoreResponse> {
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
   * Validate AgentCore response structure
   */
  private isValidAgentCoreResponse(data: any): data is AgentCoreResponse {
    return (
      typeof data === 'object' &&
      data !== null &&
      typeof data.message === 'string' &&
      typeof data.sessionId === 'string'
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