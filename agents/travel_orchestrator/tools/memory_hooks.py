"""
Memory hooks for AgentCore short-term memory integration
"""
import logging
import uuid
from typing import List, Dict, Any
from datetime import datetime

from strands.hooks import AgentInitializedEvent, HookProvider, HookRegistry, MessageAddedEvent
from bedrock_agentcore.memory import MemoryClient

logger = logging.getLogger("travel-orchestrator-memory")


class TravelMemoryHook(HookProvider):
    """
    Memory hook for travel orchestrator agent that handles short-term conversation memory
    """
    
    def __init__(self, memory_client: MemoryClient, memory_id: str):
        """
        Initialize memory hook with client and memory resource
        
        Args:
            memory_client: AgentCore MemoryClient instance
            memory_id: ID of the memory resource to use
        """
        self.memory_client = memory_client
        self.memory_id = memory_id
        logger.info(f"Initialized TravelMemoryHook with memory_id: {memory_id}")
    
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """
        Load recent conversation history when agent starts
        
        This hook runs when an agent is initialized and loads the last few
        conversation turns to provide context for the current interaction.
        """
        try:
            # Get session info from agent state
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")
            
            if not actor_id or not session_id:
                logger.warning("Missing actor_id or session_id in agent state")
                return
            
            logger.info(f"Loading conversation history for actor_id: {actor_id}, session_id: {session_id}")
            
            # Get fewer turns to reduce context contamination
            recent_turns = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=actor_id,
                session_id=session_id,
                k=6,  # Reduced from 10 to 6 turns (3 conversations max)
                branch_name="main"
            )
            
            if recent_turns:
                # Format conversation history for context, filtering successful interactions only
                context_messages = []
                for turn in recent_turns:
                    for message in turn:
                        role = message['role'].lower()
                        content = message['content']['text']
                        
                        # Filter out failed searches and error messages
                        if not any(keyword in content.lower() for keyword in [
                            'validation error', 'tool error', 'missing required',
                            'need more information', 'i need', 'failed', 'error occurred',
                            'please provide', 'system error'
                        ]):
                            context_messages.append(f"{role.title()}: {content}")
                
                # Only keep last 6 clean messages to avoid overwhelming context
                filtered_messages = context_messages[-6:]
                
                if filtered_messages:
                    # Create formatted context
                    context = "\n".join(filtered_messages)
                    logger.info(f"Context from memory (filtered): {context[:200]}...")  # Log first 200 chars
                    
                    # Add context to agent's system prompt
                    conversation_context = f"""

PREVIOUS CONVERSATION CONTEXT (successful interactions only):
{context}

Continue the conversation naturally based on this context. Reference previous discussions when relevant."""
                    
                    event.agent.system_prompt += conversation_context
                    logger.info(f"✅ Loaded {len(filtered_messages)} clean conversation messages")
                else:
                    logger.info("✨ No clean conversation context found - starting fresh")
            else:
                logger.info("No previous conversation history found - this is a new conversation")
                
        except Exception as e:
            logger.error(f"Failed to load conversation history: {e}")
            # Continue without memory context rather than failing
    
    def on_message_added(self, event: MessageAddedEvent):
        """
        Store only conversational messages in memory, filtering out tool results
        
        This hook runs after the agent processes a message and stores ONLY
        the actual conversation between user and assistant, not tool execution metadata.
        """
        try:
            messages = event.agent.messages
            
            # Get session info from agent state
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")
            
            if not actor_id or not session_id:
                logger.warning("Missing actor_id or session_id in agent state")
                return
            
            # Get the latest message to store
            if messages and len(messages) > 0:
                latest_message = messages[-1]
                
                # FILTER: Only store conversational messages, not tool results
                if not self._is_conversational_message(latest_message):
                    logger.info("🔇 Skipping tool result storage - only storing conversational messages")
                    return
                
                # Extract conversational content only
                conversational_content = self._extract_conversational_content(latest_message)
                
                if conversational_content:
                    role = latest_message.get("role", "assistant")
                    
                    # Truncate message if too long for memory storage (9000 char limit)
                    truncated_content = self._truncate_message(conversational_content, max_length=8000)
                    
                    # Store in memory
                    self.memory_client.create_event(
                        memory_id=self.memory_id,
                        actor_id=actor_id,
                        session_id=session_id,
                        messages=[(truncated_content, role)]
                    )
                    
                    truncation_note = " [TRUNCATED]" if len(conversational_content) > 8000 else ""
                    logger.info(f"✅ Stored conversational message: {truncated_content[:100]}...{truncation_note}")
                else:
                    logger.info("🔇 No conversational content found in message")
            
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
            # Continue without storing rather than failing
    
    def _is_conversational_message(self, message: Dict[str, Any]) -> bool:
        """
        Check if a message is conversational (user/assistant) vs tool result
        
        Args:
            message: Message from agent.messages
            
        Returns:
            True if message should be stored in memory, False for tool results
        """
        try:
            role = message.get("role", "").lower()
            
            # Always store user messages
            if role == "user":
                return True
            
            # For assistant messages, check if it's a final response vs tool result
            if role == "assistant":
                content = message.get("content", "")
                content_str = str(content).lower()
                
                # Skip validation errors and tool failures that contaminate context
                if any(error_keyword in content_str for error_keyword in [
                    'validation_error', 'missing required', 'need more information',
                    'system_error', 'tool_error', 'failed to', 'error occurred',
                    'i need more information', 'please provide'
                ]):
                    logger.info("🔇 Skipping error/validation message")
                    return False
                
                # Skip tool results (they contain toolResult, toolUseId, etc.)
                if isinstance(content, dict) and any(key in str(content).lower() for key in 
                    ["toolresult", "tooluseid", "tooluse", "tool_use_id"]):
                    logger.info("🔇 Skipping tool result message")
                    return False
                
                # Skip if content is a list with tool metadata
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and any(key in str(item).lower() for key in 
                            ["toolresult", "tooluseid", "tooluse", "tool_use_id"]):
                            logger.info("🔇 Skipping tool metadata message")
                            return False
                
                # Store if it looks like a conversational response
                if isinstance(content, str) and len(content.strip()) > 0:
                    return True
                
                # Store if it's a list with text content
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "text" in item and len(item["text"].strip()) > 0:
                            return True
            
            logger.info(f"🔇 Message not identified as conversational: role={role}")
            return False
            
        except Exception as e:
            logger.error(f"Error checking if message is conversational: {e}")
            return False  # Default to not storing if unsure
    
    def _extract_conversational_content(self, message: Dict[str, Any]) -> str:
        """
        Extract only the conversational text content from a message
        
        Args:
            message: Message from agent.messages
            
        Returns:
            Clean conversational text content
        """
        try:
            content = message.get("content", "")
            
            # Handle string content directly
            if isinstance(content, str):
                clean_content = self._clean_content_for_storage(content)
                return clean_content
            
            # Handle list content - extract text fields
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        # Look for text field
                        if "text" in item:
                            text_parts.append(item["text"])
                        # Skip tool-related fields
                        elif not any(key in str(item).lower() for key in 
                            ["toolresult", "tooluseid", "tooluse", "tool_use_id"]):
                            # Include other text content
                            text_parts.append(str(item))
                
                combined_content = "\n".join(text_parts).strip()
                return self._clean_content_for_storage(combined_content)
            
            # Handle dict content
            if isinstance(content, dict):
                if "text" in content:
                    clean_content = self._clean_content_for_storage(content["text"].strip())
                    return clean_content
                elif not any(key in str(content).lower() for key in 
                    ["toolresult", "tooluseid", "tooluse", "tool_use_id"]):
                    clean_content = self._clean_content_for_storage(str(content).strip())
                    return clean_content
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting conversational content: {e}")
            return ""
    
    def _clean_content_for_storage(self, content: str) -> str:
        """
        Clean content for memory storage by removing thinking blocks, JSON responses, etc.
        
        Args:
            content: Raw content string
            
        Returns:
            Clean conversational content suitable for memory storage
        """
        import re
        import json
        
        # Remove thinking blocks completely
        cleaned = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL).strip()
        
        # If it's a JSON response, try to extract just the message field
        if cleaned.startswith('{') and cleaned.endswith('}'):
            try:
                json_data = json.loads(cleaned)
                if 'message' in json_data:
                    # Use the message field instead of the full JSON
                    cleaned = json_data['message']
                    logger.info("📝 Extracted message field from JSON response for storage")
            except json.JSONDecodeError:
                # If JSON parsing fails, keep the original cleaned content
                pass
        
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned).strip()
        
        return cleaned
    
    def _truncate_message(self, content: str, max_length: int = 8000) -> str:
        """
        Truncate message to fit AgentCore Memory limits while preserving key information
        
        Args:
            content: Original message content
            max_length: Maximum allowed length (default 8000 to stay under 9000 limit)
            
        Returns:
            Truncated message content
        """
        if len(content) <= max_length:
            return content
        
        # Keep first part and add truncation notice
        truncated = content[:max_length-100]
        
        # Try to end at a natural break point (sentence, paragraph, or line)
        for break_char in ['\n\n', '\n', '. ', '! ', '? ']:
            last_break = truncated.rfind(break_char)
            if last_break > max_length * 0.8:  # Only use break if it's not too early
                truncated = truncated[:last_break + len(break_char)]
                break
        
        truncated += "\n\n[Message truncated for memory storage - full content available in current conversation]"
        
        logger.info(f"📝 Truncated message from {len(content)} to {len(truncated)} characters")
        return truncated
    
    def register_hooks(self, registry: HookRegistry) -> None:
        """
        Register memory hooks with the agent
        
        Args:
            registry: HookRegistry to register callbacks with
        """
        registry.add_callback(MessageAddedEvent, self.on_message_added)
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        logger.info("✅ Registered memory hooks: MessageAddedEvent, AgentInitializedEvent")


def create_shared_memory(region: str = "us-east-1", memory_name: str = None) -> str:
    """
    Create a shared memory resource for the travel planning system
    
    Args:
        region: AWS region for memory resource
        memory_name: Custom memory name (auto-generated if not provided)
        
    Returns:
        Memory ID of the created memory resource
    """
    if not memory_name:
        memory_name = f"TravelOrchestrator_STM_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    client = MemoryClient(region_name=region)
    
    try:
        print("Creating shared memory resource for travel planning...")
        
        # Create the memory resource
        memory = client.create_memory_and_wait(
            name=memory_name,
            description="Travel Orchestrator Short-term Memory for conversation context",
            strategies=[],  # No special memory strategies for short-term memory
            event_expiry_days=7,  # Memories expire after 7 days
            max_wait=300,  # Maximum time to wait for memory creation (5 minutes)
            poll_interval=10  # Check status every 10 seconds
        )
        
        memory_id = memory['id']
        print(f"✅ Memory created successfully with ID: {memory_id}")
        return memory_id
        
    except Exception as e:
        print(f"❌ Failed to create memory: {str(e)}")
        raise e


def generate_session_ids() -> Dict[str, str]:
    """
    Generate consistent session and actor IDs for the travel planning system
        
    Returns:
        session_id
    """
    conversation_start = datetime.now()
    
    # Create session ID with UUID suffix to meet AWS 33-character minimum requirement
    timestamp_suffix = conversation_start.strftime('%Y%m%d%H%M%S')
    uuid_suffix = str(uuid.uuid4())[:8]  # First 8 characters of UUID
    
    session_id = f"travel-session-{timestamp_suffix}-{uuid_suffix}"
    
    return session_id


def format_conversation_history(turns: List[List[Dict[str, Any]]]) -> str:
    """
    Format conversation history from memory into readable context
    
    Args:
        turns: List of conversation turns from AgentCore Memory
        
    Returns:
        Formatted conversation context string
    """
    context_messages = []
    
    for turn in turns:
        for message in turn:
            role = message.get('role', 'unknown').lower()
            content = message.get('content', {})
            
            # Extract text content
            if isinstance(content, dict) and 'text' in content:
                text = content['text']
            elif isinstance(content, str):
                text = content
            else:
                text = str(content)
            
            # Format as conversation line
            context_messages.append(f"{role.title()}: {text}")
    
    return "\n".join(context_messages)
