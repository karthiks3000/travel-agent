"""
Agent invocation tools for calling specialist agents via AgentCore Runtime
"""
import os
import json
import boto3
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from common.models.travel_models import AgentSearchResult, TravelInformation


class AgentInvoker:
    """Handles invocation of specialist agents via AgentCore Runtime"""
    
    def __init__(self):
        from botocore.config import Config
        
        # Configure client with increased timeouts for browser automation agents
        config = Config(
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            read_timeout=400,  # 3 minutes for browser automation
            connect_timeout=60,  # 1 minute connection timeout
            max_pool_connections=10
        )
        
        self.agentcore_client = boto3.client('bedrock-agentcore', config=config)
        
        # Get agent ARNs from environment variables with fallbacks
        self.specialist_agents = {
            "flights": os.getenv('FLIGHT_AGENT_ARN', 'arn:aws:bedrock-agentcore:us-east-1:123456789:agent-runtime/flight-agent'),
            "accommodations": os.getenv('ACCOMMODATION_AGENT_ARN', 'arn:aws:bedrock-agentcore:us-east-1:123456789:agent-runtime/accommodation-agent'), 
            "restaurants": os.getenv('FOOD_AGENT_ARN', 'arn:aws:bedrock-agentcore:us-east-1:123456789:agent-runtime/food-agent')
        }
        
        print("🔧 AgentInvoker initialized with enhanced timeout configuration:")
        print(f"   • Read timeout: 180 seconds (for browser automation)")
        print(f"   • Connect timeout: 60 seconds")
        print(f"   • Max retry attempts: 3")
    
    async def invoke_flight_agent(self, travel_request: str, session_id: str) -> AgentSearchResult:
        """
        Invoke flight specialist agent with natural language request
        
        Args:
            travel_request: Natural language travel request
            session_id: Session ID for context preservation
            
        Returns:
            AgentSearchResult with flight search results
        """
        start_time = datetime.now()
        
        try:
            # Prepare payload for flight agent
            payload = json.dumps({
                "prompt": f"Help with this flight search request: {travel_request}"
            }).encode()
            
            # Invoke the flight agent
            response = self.agentcore_client.invoke_agent_runtime(
                agentRuntimeArn=self.specialist_agents["flights"],
                runtimeSessionId=session_id,
                payload=payload
            )
            
            # Process response (fixed streaming logic)
            result_data = self._process_response(response)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Handle both string and dictionary responses
            if isinstance(result_data, str):
                # Text response from specialist agent
                is_successful = len(result_data.strip()) > 0 and "error" not in result_data.lower()
                results = {"response_text": result_data, "agent_response_type": "text"}
            elif isinstance(result_data, dict):
                # JSON response
                is_successful = result_data.get("success", True) and "error" not in result_data
                results = result_data
            else:
                # Unexpected format
                is_successful = False
                results = {"error": f"Unexpected response format: {type(result_data)}"}
            
            return AgentSearchResult(
                agent_name="flight_agent",
                search_type="flights",
                results=results,
                success=is_successful,
                processing_time_seconds=processing_time,
                result_count=1 if is_successful else 0
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"❌ Flight agent invocation failed: {str(e)}")
            
            return AgentSearchResult(
                agent_name="flight_agent",
                search_type="flights",
                results={},
                success=False,
                error_message=str(e),
                processing_time_seconds=processing_time
            )
    
    async def invoke_accommodation_agent(self, travel_request: str, session_id: str) -> AgentSearchResult:
        """
        Invoke accommodation specialist agent with natural language request
        """
        start_time = datetime.now()
        
        try:
            payload = json.dumps({
                "prompt": f"Help with this accommodation search request: {travel_request}"
            }).encode()
            
            response = self.agentcore_client.invoke_agent_runtime(
                agentRuntimeArn=self.specialist_agents["accommodations"],
                runtimeSessionId=session_id,
                payload=payload
            )
            
            result_data = self._process_response(response)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Handle both string and dictionary responses
            if isinstance(result_data, str):
                # Text response from specialist agent
                is_successful = len(result_data.strip()) > 0 and "error" not in result_data.lower()
                results = {"response_text": result_data, "agent_response_type": "text"}
            elif isinstance(result_data, dict):
                # JSON response
                is_successful = result_data.get("success", True) and "error" not in result_data
                results = result_data
            else:
                # Unexpected format
                is_successful = False
                results = {"error": f"Unexpected response format: {type(result_data)}"}
            
            return AgentSearchResult(
                agent_name="accommodation_agent",
                search_type="accommodations",
                results=results,
                success=is_successful,
                processing_time_seconds=processing_time,
                result_count=1 if is_successful else 0
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"❌ Accommodation agent invocation failed: {str(e)}")
            
            return AgentSearchResult(
                agent_name="accommodation_agent",
                search_type="accommodations",
                results={},
                success=False,
                error_message=str(e),
                processing_time_seconds=processing_time
            )
    
    async def invoke_food_agent(self, travel_request: str, session_id: str) -> AgentSearchResult:
        """
        Invoke food/restaurant specialist agent with natural language request
        """
        start_time = datetime.now()
        
        try:
            payload = json.dumps({
                "prompt": f"Help with this restaurant search request: {travel_request}"
            }).encode()
            
            response = self.agentcore_client.invoke_agent_runtime(
                agentRuntimeArn=self.specialist_agents["restaurants"],
                runtimeSessionId=session_id,
                payload=payload
            )
            
            result_data = self._process_response(response)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Handle both string and dictionary responses
            if isinstance(result_data, str):
                # Text response from specialist agent
                is_successful = len(result_data.strip()) > 0 and "error" not in result_data.lower()
                results = {"response_text": result_data, "agent_response_type": "text"}
            elif isinstance(result_data, dict):
                # JSON response
                is_successful = result_data.get("success", True) and "error" not in result_data
                results = result_data
            else:
                # Unexpected format
                is_successful = False
                results = {"error": f"Unexpected response format: {type(result_data)}"}
            
            return AgentSearchResult(
                agent_name="food_agent",
                search_type="restaurants",
                results=results,
                success=is_successful,
                processing_time_seconds=processing_time,
                result_count=1 if is_successful else 0
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"❌ Food agent invocation failed: {str(e)}")
            
            return AgentSearchResult(
                agent_name="food_agent",
                search_type="restaurants",
                results={},
                success=False,
                error_message=str(e),
                processing_time_seconds=processing_time
            )
    
    async def invoke_parallel_agents(self, travel_request: str, session_id: str, 
                                   agent_types: list = None) -> Dict[str, AgentSearchResult]:
        """
        Invoke multiple specialist agents in parallel
        """
        if agent_types is None:
            agent_types = ["flights", "accommodations", "restaurants"]
        
        tasks = []
        
        if "flights" in agent_types:
            tasks.append(("flights", self.invoke_flight_agent(travel_request, session_id)))
        
        if "accommodations" in agent_types:
            tasks.append(("accommodations", self.invoke_accommodation_agent(travel_request, session_id)))
        
        if "restaurants" in agent_types:
            tasks.append(("restaurants", self.invoke_food_agent(travel_request, session_id)))
        
        # Execute all tasks in parallel
        results = {}
        if tasks:
            task_names, task_coroutines = zip(*tasks)
            task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)
            
            for name, result in zip(task_names, task_results):
                if isinstance(result, Exception):
                    results[name] = AgentSearchResult(
                        agent_name=f"{name}_agent",
                        search_type=name,
                        results={},
                        success=False,
                        error_message=str(result)
                    )
                else:
                    results[name] = result
        
        return results
    
    def _process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process AgentCore Runtime response based on AWS documentation pattern
        Fix for streaming duplication by taking only final chunk
        """
        try:
            # Check for AgentCore body format first (preferred)
            if 'body' in response and 'output' in response['body']:
                return self._parse_agentcore_body_format(response['body'])
            
            # Handle streaming response (AWS docs pattern with duplication fix)
            if "text/event-stream" in response.get("contentType", ""):
                content_chunks = []
                for line in response["response"].iter_lines(chunk_size=10):
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            chunk = line[6:]
                            content_chunks.append(chunk)
                
                # CRITICAL FIX: Take only the LAST chunk to avoid duplication
                if content_chunks:
                    final_chunk = content_chunks[-1]
                    print(f"✅ Using final streaming chunk ({len(final_chunk)} chars)")
                    try:
                        return json.loads(final_chunk)
                    except json.JSONDecodeError:
                        # If final chunk is not JSON, return as text response
                        return {"success": True, "response_text": final_chunk}
                else:
                    return {"error": "No streaming chunks received"}
            
            # Handle standard JSON response
            elif response.get("contentType") == "application/json":
                content = []
                for chunk in response.get("response", []):
                    content.append(chunk.decode('utf-8'))
                return json.loads(''.join(content))
            
            else:
                return {"error": f"Unsupported content type: {response.get('contentType')}"}
                
        except Exception as e:
            print(f"⚠️  Error processing response: {str(e)}")
            return {"error": f"Failed to process response: {str(e)}"}
    
    def _parse_agentcore_body_format(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract clean text response from AgentCore Runtime body format
        """
        try:
            messages = body.get('output', {}).get('messages', [])
            if not messages:
                return {"error": "No messages in response"}
            
            message = messages[0].get('content', {})
            
            # Check if response is complete
            finish_reason = message.get('finish_reason', '')
            if finish_reason != 'end_turn':
                return {"error": f"Incomplete response: {finish_reason}"}
            
            # Extract clean text response
            response_text = message.get('message', '')
            
            if not response_text:
                return {"error": "Empty message content"}
            
            print(f"✅ Extracted clean response ({len(response_text)} characters)")
            
            return {
                "success": True,
                "response_text": response_text,
                "agent_response_type": "formatted_text"
            }
            
        except Exception as e:
            return {"error": f"Failed to extract response: {str(e)}"}


def format_travel_request(travel_info: TravelInformation) -> str:
    """
    Format TravelInformation into a natural language request string
    """
    parts = []
    
    # Basic trip info
    if travel_info.origin and travel_info.destination:
        parts.append(f"Travel from {travel_info.origin} to {travel_info.destination}")
    elif travel_info.destination:
        parts.append(f"Travel to {travel_info.destination}")
    
    # Dates
    date_parts = []
    if travel_info.departure_date:
        date_parts.append(f"departing {travel_info.departure_date}")
    if travel_info.return_date:
        date_parts.append(f"returning {travel_info.return_date}")
    elif travel_info.check_out:
        date_parts.append(f"staying until {travel_info.check_out}")
    
    if date_parts:
        parts.append(", ".join(date_parts))
    
    # Travelers
    if travel_info.passengers:
        parts.append(f"for {travel_info.passengers} passengers")
    elif travel_info.guests:
        parts.append(f"for {travel_info.guests} guests")
    
    # Accommodation dates
    if travel_info.check_in and travel_info.check_out:
        parts.append(f"accommodation from {travel_info.check_in} to {travel_info.check_out}")
    
    # Budget
    if travel_info.budget:
        parts.append(f"budget around ${travel_info.budget:,.0f}")
    elif travel_info.budget_category:
        parts.append(f"{travel_info.budget_category.value} budget")
    
    # Preferences
    if travel_info.dietary_restrictions:
        parts.append(f"dietary requirements: {', '.join(travel_info.dietary_restrictions)}")
    
    if travel_info.accommodation_preferences:
        parts.append(f"accommodation preferences: {', '.join(travel_info.accommodation_preferences)}")
    
    return ". ".join(parts) + "."
