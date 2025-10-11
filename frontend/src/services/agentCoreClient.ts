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
   * Invoke the travel orchestrator agent with JSON response
   */
  async invokeAgent(
    request: AgentCoreRequest
  ): Promise<AgentCoreResponse> {
    const { sessionId, message, authToken } = request;

    const payload = {
      prompt: message,
    };

    return this.makeRequest('', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': `Bearer ${authToken}`,
        'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': sessionId,
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
   * Make HTTP request with retry logic and exponential backoff - JSON only
   */
  private async makeRequest(
    endpoint: string, 
    options: RequestInit
  ): Promise<AgentCoreResponse> {
    const url = `${this.baseUrl}${endpoint}`;
    let lastError: Error = new Error('Unknown error');

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        const response = await fetch(url, {
          ...options,
          // Add timeout - increased for multi-step travel planning with browser automation
          signal: AbortSignal.timeout(720000), // 12 minute timeout (under AgentCore's 15min limit)
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        // Parse JSON response
        const data = await response.json();
        
        // Convert TravelOrchestratorResponse to AgentCoreResponse format
        return this.convertToAgentCoreResponse(data);
        
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
   * Convert TravelOrchestratorResponse to AgentCoreResponse format
   */
  private convertToAgentCoreResponse(data: Record<string, unknown>): AgentCoreResponse {
    // Extract session ID from response or generate one
    const sessionId = (data.session_metadata as Record<string, unknown>)?.session_id as string || 
                     `travel-session-${Date.now()}-${crypto.randomUUID().substring(0, 8)}`;
    
    // Pass through all the new orchestrator response fields
    return {
      // Core response fields
      message: data.message as string || 'No message provided',
      sessionId,
      success: data.success as boolean ?? true,
      error: data.error as string,
      
      // New orchestrator response fields (pass through directly)
      response_type: data.response_type as 'conversation' | 'flights' | 'accommodations' | 'restaurants' | 'attractions' | 'itinerary',
      response_status: data.response_status as any, // ResponseStatus type
      overall_progress_message: data.overall_progress_message as string,
      is_final_response: data.is_final_response as boolean,
      next_expected_input_friendly: data.next_expected_input_friendly as string,
      
      // Tool progress tracking
      tool_progress: data.tool_progress as any[], // ToolProgress[] type
      
      // Structured results from specialist agents
      flight_results: data.flight_results as any,
      accommodation_results: data.accommodation_results as any,
      restaurant_results: data.restaurant_results as any,
      attraction_results: data.attraction_results as any,
      itinerary: data.itinerary as import('../types/chat').TravelItinerary,
      
      // Additional metadata
      processing_time_seconds: data.processing_time_seconds as number,
      estimated_costs: data.estimated_costs as Record<string, number>,
      recommendations: data.recommendations as Record<string, unknown>,
      session_metadata: data.session_metadata as Record<string, string>
    };
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
