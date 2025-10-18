"""
Streaming progress hooks for real-time tool execution updates
"""
import logging
import json
from typing import Dict, Any, Optional
from queue import Queue

from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import BeforeToolCallEvent, AfterToolCallEvent

logger = logging.getLogger("travel-orchestrator-streaming")


class StreamingProgressHook(HookProvider):
    """
    Hook that emits SSE events during tool execution for real-time progress tracking
    """
    
    def __init__(self, event_queue: Queue):
        """
        Initialize streaming progress hook
        
        Args:
            event_queue: Thread-safe queue for emitting SSE events
        """
        self.event_queue = event_queue
        
        # Map tool names to user-friendly display names
        self.tool_display_mapping = {
            "search_flights": "Searching for flights",
            "search_accommodations": "Finding accommodations",
            "searchPlacesByText": "Searching for restaurants and attractions", 
            "searchNearbyPlaces": "Finding nearby places",
            "getPlaceDetails": "Getting location details",
            # Google Maps API tools (with long generated names)
            "GoogleMapsPlacesAPI___searchPlacesByText": "Searching for restaurants and attractions",
            "GoogleMapsPlacesAPI___searchNearbyPlaces": "Finding nearby places", 
            "GoogleMapsPlacesAPI___getPlaceDetails": "Getting location details",
        }
        
        logger.info("✅ Initialized StreamingProgressHook")
    
    def register_hooks(self, registry: HookRegistry) -> None:
        """
        Register tool execution hooks with the agent
        
        Args:
            registry: HookRegistry to register callbacks with
        """
        registry.add_callback(BeforeToolCallEvent, self.on_tool_start)
        registry.add_callback(AfterToolCallEvent, self.on_tool_complete)
        logger.info("✅ Registered streaming hooks: BeforeToolCallEvent, AfterToolCallEvent")
    
    def on_tool_start(self, event: BeforeToolCallEvent) -> None:
        """
        Handle tool start event - emit SSE progress update
        
        Args:
            event: BeforeToolCallEvent containing tool information
        """
        try:
            tool_name = event.selected_tool.name if event.selected_tool else "unknown_tool"
            
            # Get display information
            display_name = self.tool_display_mapping.get(tool_name, self._humanize_tool_name(tool_name))
            description = self._get_tool_description(tool_name, event.tool_use, event.invocation_state)
            
            # Emit SSE event
            sse_event = {
                "event": "tool_start",
                "data": {
                    "tool_id": tool_name,
                    "display_name": display_name,
                    "description": description,
                    "status": "active"
                }
            }
            
            self.event_queue.put(sse_event)
            logger.info(f"🔄 Tool started: {display_name}")
            
        except Exception as e:
            logger.error(f"Error in on_tool_start: {e}")
    
    def on_tool_complete(self, event: AfterToolCallEvent) -> None:
        """
        Handle tool completion event - emit SSE progress update
        
        Args:
            event: AfterToolCallEvent containing tool results
        """
        try:
            tool_name = event.selected_tool.name if event.selected_tool else "unknown_tool"
            
            # Determine success/failure status
            status = "failed" if event.exception else "completed"
            
            # Get result preview
            preview = None
            error_message = None
            
            if event.exception:
                error_message = str(event.exception)
                logger.warning(f"❌ Tool failed: {tool_name} - {error_message}")
            else:
                preview = self._get_result_preview(tool_name, event.result)
                logger.info(f"✅ Tool completed: {tool_name}")
            
            # Emit SSE event
            sse_event = {
                "event": "tool_complete", 
                "data": {
                    "tool_id": tool_name,
                    "status": status,
                    "preview": preview,
                    "error_message": error_message
                }
            }
            
            self.event_queue.put(sse_event)
            
        except Exception as e:
            logger.error(f"Error in on_tool_complete: {e}")
    
    def _humanize_tool_name(self, tool_name: str) -> str:
        """
        Convert snake_case tool name to human-readable format
        
        Args:
            tool_name: Internal tool name
            
        Returns:
            Human-readable tool name
        """
        return tool_name.replace("_", " ").title()
    
    def _get_tool_description(self, tool_name: str, tool_use: Any, invocation_state: Dict[str, Any]) -> str:
        """
        Generate detailed description for tool execution
        
        Args:
            tool_name: Name of the tool being executed
            tool_use: Tool use parameters
            invocation_state: Tool invocation state
            
        Returns:
            Detailed description of what the tool is doing
        """
        try:
            # Extract parameters from tool_use or invocation_state
            params = {}
            
            # Try to get parameters from tool_use first
            if hasattr(tool_use, 'input') and isinstance(tool_use.input, dict):
                params.update(tool_use.input)
            
            # Fall back to invocation_state
            if not params and invocation_state:
                params.update(invocation_state)
            
            # Generate contextual descriptions based on tool and parameters
            if tool_name == "search_flights":
                origin = params.get('origin', 'departure city')
                destination = params.get('destination', 'destination city')
                return f"Looking for flights from {origin} to {destination}"
            
            elif tool_name == "search_accommodations":
                destination = params.get('destination', 'your destination')
                platform_preference = params.get('platform_preference', 'both')
                
                if platform_preference == 'booking':
                    return f"Searching hotels on Booking.com in {destination}"
                elif platform_preference == 'airbnb':
                    return f"Searching rentals on Airbnb.com in {destination}"
                else:
                    return f"Searching accommodations on Booking.com and Airbnb in {destination}"
            
            elif tool_name in ["searchPlacesByText", "GoogleMapsPlacesAPI___searchPlacesByText"]:
                query = params.get('query', '')
                textquery = params.get('textQuery', query)  # Google Places API uses textQuery
                
                # Try to determine if it's restaurants or attractions
                if any(word in textquery.lower() for word in ['restaurant', 'food', 'dining', 'cafe', 'bar']):
                    return f"Searching for restaurants: {textquery}"
                elif any(word in textquery.lower() for word in ['attraction', 'museum', 'park', 'landmark', 'tourist']):
                    return f"Finding attractions: {textquery}"
                else:
                    return f"Searching: {textquery or 'places of interest'}"
            
            elif tool_name in ["searchNearbyPlaces", "GoogleMapsPlacesAPI___searchNearbyPlaces"]:
                return "Finding nearby points of interest"
            
            elif tool_name in ["getPlaceDetails", "GoogleMapsPlacesAPI___getPlaceDetails"]:
                return "Getting detailed location information"
            
            else:
                # Generic description for unknown tools
                return f"Executing {self._humanize_tool_name(tool_name)}"
                
        except Exception as e:
            logger.warning(f"Error generating tool description: {e}")
            return f"Executing {self._humanize_tool_name(tool_name)}"
    
    def _get_result_preview(self, tool_name: str, result: Any) -> Optional[str]:
        """
        Generate preview text from tool result
        
        Args:
            tool_name: Name of the completed tool
            result: Tool execution result
            
        Returns:
            Brief preview of the results, or None if no preview available
        """
        try:
            # Handle different result types
            if not result:
                return None
            
            # Try to extract meaningful information based on tool type
            if tool_name == "search_flights":
                if hasattr(result, 'flight_results') and result.flight_results:
                    count = len(result.flight_results)
                    return f"Found {count} flight option{'s' if count != 1 else ''}"
            
            elif tool_name == "search_accommodations":
                if hasattr(result, 'accommodation_results') and result.accommodation_results:
                    count = len(result.accommodation_results)
                    return f"Found {count} accommodation option{'s' if count != 1 else ''}"
            
            elif tool_name in ["searchPlacesByText", "searchNearbyPlaces"]:
                # For Google Places API results
                if hasattr(result, 'restaurant_results') and result.restaurant_results:
                    count = len(result.restaurant_results)
                    return f"Found {count} restaurant{'s' if count != 1 else ''}"
                elif hasattr(result, 'attraction_results') and result.attraction_results:
                    count = len(result.attraction_results)
                    return f"Found {count} attraction{'s' if count != 1 else ''}"
            
            # Generic success message
            return "Completed successfully"
            
        except Exception as e:
            logger.warning(f"Error generating result preview: {e}")
            return "Completed"
