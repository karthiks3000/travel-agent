"""
Agent invocation tools for calling specialist agents via AgentCore Runtime
"""
import os
import json
import re
import ast
import boto3
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from common.models.travel_models import TravelInformation
from common.models.flight_models import FlightSearchResults
from common.models.accommodation_models import AccommodationAgentResponse
from common.models.food_models import RestaurantSearchResults
from common.models.orchestrator_models import AgentResponseParser


class AgentInvoker:
    """Handles invocation of specialist agents via AgentCore Runtime"""
    
    def __init__(self, flight_agent_arn: str, accommodation_agent_arn: str, food_agent_arn: str, region: str = 'us-east-1'):
        from botocore.config import Config
        
        # Configure client with increased timeouts for browser automation agents
        config = Config(
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            read_timeout=400,  # 3 minutes for browser automation
            connect_timeout=60,  # 1 minute connection timeout
            max_pool_connections=10,
            region_name=region
        )
        
        self.agentcore_client = boto3.client('bedrock-agentcore', config=config)
        
        # Store specialist agent ARNs passed from main class
        self.specialist_agents = {
            "flights": flight_agent_arn,
            "accommodations": accommodation_agent_arn, 
            "restaurants": food_agent_arn
        }
        
        print("🔧 AgentInvoker initialized with enhanced timeout configuration:")
        print(f"   • Read timeout: 400 seconds (for browser automation)")
        print(f"   • Connect timeout: 60 seconds")
        print(f"   • Max retry attempts: 3")
        print(f"   • Region: {region}")
        print("🎯 Specialist agent ARNs loaded:")
        print(f"   • Flight agent: {flight_agent_arn}")
        print(f"   • Accommodation agent: {accommodation_agent_arn}")
        print(f"   • Food agent: {food_agent_arn}")
    
    def invoke_flight_agent(self, travel_request: str, session_id: str) -> Optional[FlightSearchResults]:
        """
        Invoke flight specialist agent and return structured FlightSearchResults
        
        Args:
            travel_request: Natural language travel request
            session_id: Session ID for context preservation
            
        Returns:
            FlightSearchResults if successful, None otherwise
        """
        start_time = datetime.now()
        
        try:
            # Prepare payload for flight agent
            payload = json.dumps({
                "prompt": f"Help with this flight search request: {travel_request}"
            }).encode()
            
            # Invoke the flight agent (now returns Pydantic objects directly)
            response = self.agentcore_client.invoke_agent_runtime(
                agentRuntimeArn=self.specialist_agents["flights"],
                runtimeSessionId=session_id,
                payload=payload
            )

            print(f'✈️  Flight agent response received ({response.get("contentType", "unknown")})')
            
            # Process response - expect direct Pydantic object
            result_data = self._process_sync_response(response)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            print(f"✈️  Flight agent processing time: {processing_time:.2f}s")
            
            # Agent now returns FlightSearchResults directly
            if isinstance(result_data, FlightSearchResults):
                print(f"✅ Flight agent returned FlightSearchResults object")
                return result_data
            elif isinstance(result_data, dict) and "error" not in result_data:
                # Fallback: try to create FlightSearchResults from dict
                try:
                    flight_results = FlightSearchResults(**result_data)
                    print(f"✅ Created FlightSearchResults from response dict")
                    return flight_results
                except Exception as e:
                    print(f"❌ Failed to create FlightSearchResults from dict: {e}")
            else:
                print(f"❌ Flight agent returned error or invalid format: {result_data}")
            
            return None
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"❌ Flight agent invocation failed after {processing_time:.2f}s: {str(e)}")
            return None
    
    def invoke_accommodation_agent(self, travel_request: str, session_id: str) -> Optional[AccommodationAgentResponse]:
        """
        Invoke accommodation specialist agent and return structured AccommodationAgentResponse
        
        Args:
            travel_request: Natural language travel request
            session_id: Session ID for context preservation
            
        Returns:
            AccommodationAgentResponse if successful, None otherwise
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
            
            print(f'🏨 Accommodation agent response received ({response.get("contentType", "unknown")})')
            
            # Process response - expect direct Pydantic object
            result_data = self._process_sync_response(response)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            print(f"🏨 Accommodation agent processing time: {processing_time:.2f}s")
            
            # Agent now returns AccommodationAgentResponse directly
            if isinstance(result_data, AccommodationAgentResponse):
                print(f"✅ Accommodation agent returned AccommodationAgentResponse object")
                return result_data
            elif isinstance(result_data, dict) and "error" not in result_data:
                # Fallback: try to create AccommodationAgentResponse from dict
                try:
                    accommodation_results = AccommodationAgentResponse(**result_data)
                    print(f"✅ Created AccommodationAgentResponse from response dict")
                    return accommodation_results
                except Exception as e:
                    print(f"❌ Failed to create AccommodationAgentResponse from dict: {e}")
            else:
                print(f"❌ Accommodation agent returned error or invalid format: {result_data}")
            
            return None
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"❌ Accommodation agent invocation failed after {processing_time:.2f}s: {str(e)}")
            return None
    
    def invoke_food_agent(self, travel_request: str, session_id: str) -> Optional[RestaurantSearchResults]:
        """
        Invoke food/restaurant specialist agent and return structured RestaurantSearchResults
        
        Args:
            travel_request: Natural language travel request
            session_id: Session ID for context preservation
            
        Returns:
            RestaurantSearchResults if successful, None otherwise
        """
        start_time = datetime.now()
        
        try:
            # Prepare payload for food agent
            payload = json.dumps({
                "prompt": f"Help with this restaurant search request: {travel_request}"
            }).encode()
            
            # Invoke the food agent (now returns Pydantic objects directly)
            response = self.agentcore_client.invoke_agent_runtime(
                agentRuntimeArn=self.specialist_agents["restaurants"],
                runtimeSessionId=session_id,
                payload=payload
            )

            print(f'🍽️  Restaurant agent response received ({response.get("contentType", "unknown")})')
            
            # Process response - expect direct Pydantic object
            result_data = self._process_sync_response(response)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            print(f"🍽️  Restaurant agent processing time: {processing_time:.2f}s")
            
            # Agent now returns RestaurantSearchResults directly
            if isinstance(result_data, RestaurantSearchResults):
                print(f"✅ Restaurant agent returned RestaurantSearchResults object")
                return result_data
            elif isinstance(result_data, dict) and "error" not in result_data:
                # Fallback: try to create RestaurantSearchResults from dict
                try:
                    restaurant_results = RestaurantSearchResults(**result_data)
                    print(f"✅ Created RestaurantSearchResults from response dict")
                    return restaurant_results
                except Exception as e:
                    print(f"❌ Failed to create RestaurantSearchResults from dict: {e}")
            else:
                print(f"❌ Restaurant agent returned error or invalid format: {result_data}")
            
            return None
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"❌ Restaurant agent invocation failed after {processing_time:.2f}s: {str(e)}")
            return None
    
    def invoke_parallel_agents(self, travel_request: str, session_id: str, 
                             agent_types: list = None) -> Dict[str, Any]:
        """
        Invoke multiple specialist agents in parallel and return structured responses
        
        Args:
            travel_request: Natural language travel request
            session_id: Session ID for context preservation
            agent_types: List of agent types to invoke (flights, accommodations, restaurants)
            
        Returns:
            Dict with keys 'flights', 'accommodations', 'restaurants' containing Pydantic models or None
        """
        if agent_types is None:
            agent_types = ["flights", "accommodations", "restaurants"]
        
        import concurrent.futures
        import threading
        
        results = {}
        
        # Use ThreadPoolExecutor for concurrent execution of sync methods
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_agent = {}
            
            if "flights" in agent_types:
                future = executor.submit(self.invoke_flight_agent, travel_request, f"{session_id}-flights")
                future_to_agent[future] = "flights"
            
            if "accommodations" in agent_types:
                future = executor.submit(self.invoke_accommodation_agent, travel_request, f"{session_id}-accommodations")
                future_to_agent[future] = "accommodations"
            
            if "restaurants" in agent_types:
                future = executor.submit(self.invoke_food_agent, travel_request, f"{session_id}-restaurants")
                future_to_agent[future] = "restaurants"
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    result = future.result()
                    results[agent_name] = result
                    if result:
                        print(f"✅ {agent_name} agent completed successfully")
                    else:
                        print(f"❌ {agent_name} agent returned no results")
                except Exception as e:
                    print(f"❌ {agent_name} agent failed with exception: {e}")
                    results[agent_name] = None
        
        return results
    
    def _process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process AgentCore Runtime response based on AWS documentation pattern
        Fix for streaming duplication by taking only final chunk
        """
        try:
            # Check for AgentCore body format first (preferred)
            if 'body' in response and 'output' in response['body']:
                print('calling _parse_agentcore_body_format')
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
                    print(final_chunk)
                    try:
                        return json.loads(final_chunk)
                    except json.JSONDecodeError:
                        # Try to extract JSON from AgentResult string format
                        extracted_json = self._extract_json_from_agent_result(final_chunk)
                        if extracted_json:
                            return extracted_json
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
    
    def _extract_json_from_agent_result(self, agent_result_string: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from AgentResult string format: AgentResult(..., message={'content': [{'text': '{JSON}'}]}, ...)
        
        Args:
            agent_result_string: String representation of AgentResult object
            
        Returns:
            Parsed JSON dictionary or None if extraction fails
        """
        try:
            print(f"🔧 Attempting to extract JSON from AgentResult string ({len(agent_result_string)} chars)")
            
            # Look for the pattern: content': [{'text': '
            content_pattern = r"content['\"]:\s*\[\s*\{\s*['\"]text['\"]:\s*['\"](.+?)['\"]"
            match = re.search(content_pattern, agent_result_string, re.DOTALL)
            
            if match:
                json_text = match.group(1)
                print(f"✅ Found JSON text in content[0]['text'] ({len(json_text)} chars)")
                
                # The JSON might have escaped quotes, so we need to unescape them
                json_text = json_text.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                
                try:
                    parsed_json = json.loads(json_text)
                    print(f"✅ Successfully parsed JSON from AgentResult")
                    return parsed_json
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse extracted JSON: {e}")
                    return None
            else:
                print("❌ Could not find content[0]['text'] pattern in AgentResult string")
                return None
                
        except Exception as e:
            print(f"❌ Error extracting JSON from AgentResult: {e}")
            return None
    
    def _process_sync_response(self, response: Dict[str, Any]) -> Any:
        """
        Process AgentCore Runtime response for sync agents that return Pydantic objects
        
        The agents now return Pydantic objects directly from their entrypoints.
        AgentCore Runtime serializes these objects for transport.
        This method deserializes them back to the original data structure.
        
        Args:
            response: AgentCore Runtime response dictionary
            
        Returns:
            Deserialized data structure that can be used to recreate Pydantic objects
        """
        try:
            # Use existing response processing to extract the serialized data
            # The agents return Pydantic objects, AgentCore serializes them, 
            # and we get the serialized data back
            extracted_data = self._process_response(response)
            
            # The extracted data should be the serialized Pydantic object
            if isinstance(extracted_data, dict) and "error" not in extracted_data:
                print(f"✅ Extracted serialized Pydantic object data")
                return extracted_data
            else:
                print(f"❌ No valid data extracted from sync response")
                return extracted_data
            
        except Exception as e:
            print(f"❌ Error processing sync response: {str(e)}")
            return {"error": f"Failed to process sync response: {str(e)}"}
    
    def _process_response_clean(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process AgentCore Runtime response expecting clean JSON from structured output agents
        """
        try:
            # Handle streaming response - should be clean JSON now
            if "text/event-stream" in response.get("contentType", ""):
                content_chunks = []
                for line in response["response"].iter_lines(chunk_size=10):
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            chunk = line[6:]
                            content_chunks.append(chunk)
                
                # Take the final chunk
                if content_chunks:
                    final_chunk = content_chunks[-1]
                    print(f"✅ Using clean streaming chunk ({len(final_chunk)} chars)")
                    try:
                        # Should be clean JSON from structured output
                        return json.loads(final_chunk)
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse clean JSON: {e}")
                        return {"error": f"Invalid JSON from structured output: {e}"}
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
            print(f"⚠️  Error processing clean response: {str(e)}")
            return {"error": f"Failed to process clean response: {str(e)}"}


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
