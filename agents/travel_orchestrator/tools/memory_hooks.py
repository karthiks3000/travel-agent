"""
Memory hooks for AgentCore short-term memory integration
"""
import logging
import uuid
import json
import re
from typing import List, Dict, Any
from datetime import datetime

from strands.hooks import AgentInitializedEvent, HookProvider, HookRegistry, MessageAddedEvent
from bedrock_agentcore.memory import MemoryClient

logger = logging.getLogger("travel-orchestrator-memory")


class TravelMemoryHook(HookProvider):
    """
    Simplified memory hook that stores all meaningful messages including tool results
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
        logger.info(f"✅ Initialized TravelMemoryHook with memory_id: {memory_id}")
    
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """
        Load recent conversation history when agent starts
        """
        try:
            # Get session info from agent state
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")
            
            if not actor_id or not session_id:
                logger.warning("Missing actor_id or session_id in agent state")
                return
            
            logger.info(f"Loading conversation history for actor_id: {actor_id}, session_id: {session_id}")
            
            # Get recent conversation turns
            recent_turns = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=actor_id,
                session_id=session_id,
                k=6,  # Last 6 turns (3 conversations)
                branch_name="main"
            )
            
            if recent_turns:
                # Format conversation history for context
                context_messages = []
                for turn in recent_turns:
                    for message in turn:
                        role = message['role'].lower()
                        content = message['content']['text']
                        context_messages.append(f"{role.title()}: {content}")
                
                if context_messages:
                    # Create formatted context
                    context = "\n".join(context_messages[-6:])  # Keep last 6 messages
                    logger.info(f"Context from memory (filtered): {context[:200]}...")
                    
                    # Add context to agent's system prompt
                    conversation_context = f"""

PREVIOUS CONVERSATION CONTEXT:
{context}

Continue the conversation naturally based on this context. Reference previous discussions when relevant."""
                    
                    # Handle case where system_prompt might be None
                    if event.agent.system_prompt is None:
                        event.agent.system_prompt = conversation_context
                    else:
                        event.agent.system_prompt += conversation_context
                    logger.info(f"✅ Loaded {len(context_messages)} conversation messages")
                else:
                    logger.info("✨ No conversation context found - starting fresh")
            else:
                logger.info("No previous conversation history found - this is a new conversation")
                
        except Exception as e:
            logger.error(f"Failed to load conversation history: {e}")
            # Continue without memory context rather than failing
    
    def on_message_added(self, event: MessageAddedEvent):
        """
        Store all meaningful messages in memory (including tool results)
        """
        try:
            messages = event.agent.messages
            
            # Get session info from agent state
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")
            
            if not actor_id or not session_id or not messages:
                logger.warning("Missing required info for memory storage")
                return
            
            latest_message = messages[-1]
            role = latest_message.get("role", "")
            content = latest_message.get("content", "")
            
            # Always store user messages
            if role == "user":
                self._store_message(actor_id, session_id, content, role)
                return
            
            # For assistant messages, store if meaningful
            if role == "assistant":
                # Skip if only thinking (no actual content)
                if self._is_thinking_only(content):
                    logger.info("🔇 Skipping thinking-only message")
                    return
                
                # Store everything else (tool results, final responses, questions)
                self._store_message(actor_id, session_id, content, role)
                
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
    
    def _is_thinking_only(self, content: Any) -> bool:
        """
        Check if message contains only thinking blocks with no meaningful content
        
        Args:
            content: Message content
            
        Returns:
            True if message is thinking-only, False otherwise
        """
        try:
            # Convert to string for analysis
            content_str = json.dumps(content) if isinstance(content, (dict, list)) else str(content)
            
            # Check if contains thinking blocks
            if "<thinking>" in content_str and "</thinking>" in content_str:
                # Remove thinking blocks and see what's left
                thinking_removed = re.sub(r'<thinking>.*?</thinking>', '', content_str, flags=re.DOTALL).strip()
                
                # If nothing meaningful left, it's thinking-only
                if not thinking_removed or thinking_removed in ["[]", "{}", '""', "null"]:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking thinking-only content: {e}")
            return False
    
    def _store_message(self, actor_id: str, session_id: str, content: Any, role: str):
        """
        Store message in memory with proper size handling
        
        Args:
            actor_id: Actor identifier
            session_id: Session identifier  
            content: Message content
            role: Message role (user/assistant)
        """
        try:
            # Convert content to string for storage
            if isinstance(content, (dict, list)):
                content_str = json.dumps(content)
            else:
                content_str = str(content)
            
            # Check byte size (9KB limit per message)
            content_bytes = content_str.encode('utf-8')
            
            # Convert role to valid AgentCore Memory format
            valid_role = role.upper() if role.lower() in ['user', 'assistant'] else 'OTHER'
            
            if len(content_bytes) <= 9000:  # 9KB limit with buffer
                # Store as single message
                self.memory_client.create_event(
                    memory_id=self.memory_id,
                    actor_id=actor_id,
                    session_id=session_id,
                    messages=[(content_str, valid_role)]
                )
                logger.info(f"✅ Stored {role} message ({len(content_bytes)} bytes)")
                
            else:
                # Split into chunks and store as separate events
                chunk_size = 8500  # Leave buffer for safety
                chunk_count = 0
                
                for i in range(0, len(content_str), chunk_size):
                    chunk = content_str[i:i + chunk_size]
                    chunk_count += 1
                    
                    # Store each chunk as a separate event with valid role
                    self.memory_client.create_event(
                        memory_id=self.memory_id,
                        actor_id=actor_id,
                        session_id=session_id,
                        messages=[(chunk, valid_role)]
                    )
                
                logger.info(f"✅ Stored {role} message in {chunk_count} separate events ({len(content_bytes)} bytes total)")
                
        except Exception as e:
            logger.error(f"Failed to store message in memory: {e}")
    
    def register_hooks(self, registry: HookRegistry) -> None:
        """
        Register memory hooks with the agent
        
        Args:
            registry: HookRegistry to register callbacks with
        """
        registry.add_callback(MessageAddedEvent, self.on_message_added)
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        logger.info("✅ Registered memory hooks: MessageAddedEvent, AgentInitializedEvent")


def create_shared_memory(region: str = "us-east-1", memory_name: str | None = None) -> str:
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
            poll_interval=600  # Check status every 60 seconds
        )
        
        memory_id = memory['id']
        print(f"✅ Memory created successfully with ID: {memory_id}")
        return memory_id
        
    except Exception as e:
        print(f"❌ Failed to create memory: {str(e)}")
        raise e


def generate_session_ids() -> str:
    """
    Generate session ID for the travel planning system
        
    Returns:
        session_id string
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
