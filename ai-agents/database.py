"""
Supabase database connection and operations for Instabids
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Optional
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client


# Load environment variables from root .env
root_env = Path(__file__).parent.parent / '.env'
if root_env.exists():
    load_dotenv(root_env, override=True)
else:
    load_dotenv()  # Fallback to default

logger = logging.getLogger(__name__)

class SupabaseDB:
    def __init__(self):
        """Initialize Supabase client"""
        # Load from environment variables (fixed - no longer need hardcoding)
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")

        self.client: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized")

    async def save_conversation_state(
        self,
        user_id: str,
        thread_id: str,
        agent_type: str,
        state: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Save or update conversation state using unified conversation system

        Args:
            user_id: User's profile ID
            thread_id: LangGraph thread ID (session_id)
            agent_type: Type of agent (CIA, CoIA, etc.)
            state: Conversation state dictionary

        Returns:
            Saved conversation record
        """
        try:
            # Check if unified conversation already exists by session_id
            existing = self.client.table("unified_conversations").select("*").eq(
                "metadata->>session_id", thread_id
            ).execute()

            conversation_id = None
            
            if existing.data:
                # Update existing unified conversation
                conversation_id = existing.data[0]["id"]
                logger.info(f"Found existing unified conversation {conversation_id} for thread {thread_id}")
            else:
                # Create new unified conversation
                conversation_id = str(uuid.uuid4())
                
                conversation_data = {
                    "id": conversation_id,
                    "conversation_type": f"{agent_type.lower()}_chat",  # Required field
                    "title": f"{agent_type} Chat",
                    "status": "active",
                    "metadata": {
                        "session_id": thread_id,
                        "agent_type": agent_type,
                        "user_id": user_id
                    },
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                result = self.client.table("unified_conversations").insert(
                    conversation_data
                ).execute()
                
                if result.data:
                    conversation_id = result.data[0]["id"]
                    logger.info(f"Created unified conversation {conversation_id} for thread {thread_id}")
                else:
                    raise Exception("Failed to create unified conversation")
            
            # Save/update CIA state in unified conversation memory
            memory_data = {
                "state": state,
                "agent_type": agent_type,
                "saved_at": datetime.utcnow().isoformat()
            }
            
            # Check if memory entry exists
            existing_memory = self.client.table("unified_conversation_memory").select("*").eq(
                "conversation_id", conversation_id
            ).eq("memory_key", "cia_state").execute()
            
            if existing_memory.data:
                # Update existing memory
                result = self.client.table("unified_conversation_memory").update({
                    "memory_value": memory_data,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("conversation_id", conversation_id).eq("memory_key", "cia_state").execute()
                logger.info(f"Updated CIA state memory for conversation {conversation_id}")
            else:
                # Create new memory entry
                memory_entry = {
                    "id": str(uuid.uuid4()),
                    "conversation_id": conversation_id,
                    "memory_key": "cia_state",
                    "memory_value": memory_data,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                result = self.client.table("unified_conversation_memory").insert(
                    memory_entry
                ).execute()
                logger.info(f"Created CIA state memory for conversation {conversation_id}")
            
            return {
                "conversation_id": conversation_id,
                "thread_id": thread_id,
                "state": state
            }

        except Exception as e:
            logger.error(f"Error saving unified conversation state: {e!s}")
            raise

    async def load_conversation_state(
        self,
        thread_id: str
    ) -> Optional[dict[str, Any]]:
        """
        Load conversation state from the unified conversation system

        Args:
            thread_id: LangGraph thread ID (session_id)

        Returns:
            Conversation state or None if not found
        """
        try:
            # Try to find conversation by session_id in metadata
            result = self.client.table("unified_conversations").select(
                "*"
            ).eq("metadata->>session_id", thread_id).execute()

            if result.data and len(result.data) > 0:
                logger.info(f"Loaded unified conversation for thread {thread_id}")
                conversation = result.data[0]
                
                # Get conversation memory (CIA state)
                memory_result = self.client.table("unified_conversation_memory").select(
                    "*"
                ).eq("conversation_id", conversation["id"]).eq(
                    "memory_key", "cia_state"
                ).execute()
                
                # Load conversation messages
                messages_result = self.client.table("unified_messages").select(
                    "*"
                ).eq("conversation_id", conversation["id"]).order(
                    "created_at", desc=False
                ).execute()
                
                # Format messages for CIA state
                messages = []
                if messages_result.data:
                    for msg in messages_result.data:
                        if msg["sender_type"] == "user":
                            messages.append({
                                "role": "user",
                                "content": msg.get("content", "")
                            })
                        elif msg["sender_type"] == "agent":
                            messages.append({
                                "role": "assistant", 
                                "content": msg.get("content", "")
                            })
                    logger.info(f"Loaded {len(messages)} messages for thread {thread_id}")
                
                if memory_result.data:
                    # Extract the CIA state from memory
                    memory_data = memory_result.data[0]["memory_value"]
                    if isinstance(memory_data, dict) and "state" in memory_data:
                        logger.info(f"Found CIA state in unified memory for thread {thread_id}")
                        # Add messages to the state
                        if "state" in memory_data:
                            memory_data["state"]["messages"] = messages
                        else:
                            memory_data["messages"] = messages
                        return memory_data  # Return the full memory structure
                    elif isinstance(memory_data, dict):
                        # Memory data exists but no state key - add messages directly
                        memory_data["messages"] = messages
                        return memory_data
                
                # If no specific CIA state found, return basic conversation data with messages
                return {
                    "thread_id": thread_id,
                    "conversation_id": conversation["id"],
                    "state": {
                        "messages": messages
                    },
                    "messages": messages  # Also include at top level for easier access
                }
            else:
                logger.info(f"No unified conversation state found for thread {thread_id}")
                return None

        except Exception as e:
            logger.error(f"Error loading unified conversation state: {e!s}")
            # Return None instead of raising to allow new conversations
            return None

    async def get_or_create_test_user(self) -> str:
        """
        Get or create a test user for development

        Returns:
            User ID
        """
        test_email = "test@instabids.com"

        try:
            # Check if test user exists
            result = self.client.table("profiles").select("*").eq(
                "email", test_email
            ).execute()

            if result.data:
                logger.info(f"Found existing test user: {result.data[0]['id']}")
                return result.data[0]["id"]

            # Create test user directly in profiles table
            # Generate a proper UUID
            test_user_id = str(uuid.uuid4())

            profile_data = {
                "id": test_user_id,
                "email": test_email,
                "full_name": "Test User",
                "role": "homeowner",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Try to insert the test user
            result = self.client.table("profiles").insert(profile_data).execute()

            if result.data:
                logger.info(f"Created test user with ID: {test_user_id}")
                return test_user_id
            else:
                # If insert fails (maybe ID exists), try to get by ID
                result = self.client.table("profiles").select("*").eq(
                    "id", test_user_id
                ).execute()
                if result.data:
                    return test_user_id

        except Exception as e:
            logger.error(f"Error with test user: {e!s}")
            # Use a fallback test user ID (proper UUID)
            fallback_id = str(uuid.uuid4())
            logger.warning(f"Using fallback test user ID: {fallback_id}")
            return fallback_id

    async def save_unified_conversation(self, conversation_data: dict) -> bool:
        """
        Save conversation to unified_conversations table
        
        Args:
            conversation_data: Dictionary containing conversation details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create conversation record for BSA
            record = {
                "id": str(uuid.uuid4()),
                "created_by": conversation_data.get("user_id"),
                "conversation_type": conversation_data.get("agent_type", "BSA"),
                "entity_type": "contractor",
                "title": f"BSA Session - {conversation_data.get('session_id', 'unknown')}",
                "status": "active",
                "metadata": {
                    "session_id": conversation_data.get("session_id"),
                    "agent_type": conversation_data.get("agent_type", "BSA"),
                    "input_data": conversation_data.get("input_data"),
                    "response": conversation_data.get("response")
                },
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("unified_conversations").insert(record).execute()
            
            if result.data:
                conversation_id = result.data[0]['id']
                logger.info(f"✅ Saved BSA conversation to unified_conversations: {conversation_id}")
                
                # Also save individual messages to unified_conversation_messages
                messages_to_save = []
                
                # Save user message
                if conversation_data.get("input_data"):
                    messages_to_save.append({
                        "id": str(uuid.uuid4()),
                        "conversation_id": conversation_id,
                        "sender_type": "user",
                        "sender_id": conversation_data.get("user_id"),
                        "agent_type": conversation_data.get("agent_type", "BSA"),
                        "content": conversation_data.get("input_data"),
                        "content_type": "text",
                        "metadata": {},
                        "created_at": datetime.utcnow().isoformat()
                    })
                
                # Save assistant response
                if conversation_data.get("response"):
                    messages_to_save.append({
                        "id": str(uuid.uuid4()),
                        "conversation_id": conversation_id,
                        "sender_type": "agent",
                        "sender_id": None,
                        "agent_type": conversation_data.get("agent_type", "BSA"),
                        "content": conversation_data.get("response"),
                        "content_type": "text",
                        "metadata": {},
                        "created_at": datetime.utcnow().isoformat()
                    })
                
                # Save messages to unified_conversation_messages table
                if messages_to_save:
                    try:
                        msg_result = self.client.table("unified_conversation_messages").insert(messages_to_save).execute()
                        if msg_result.data:
                            logger.info(f"✅ Saved {len(messages_to_save)} messages to unified_conversation_messages")
                        else:
                            logger.warning("Failed to save messages to unified_conversation_messages")
                    except Exception as msg_error:
                        logger.error(f"Error saving messages: {msg_error}")
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error saving unified conversation: {e}")
            return False

    async def get_contractor_by_id(self, contractor_id: str) -> Optional[dict]:
        """
        Get contractor details by ID
        
        Args:
            contractor_id: Contractor UUID
            
        Returns:
            Contractor data or None if not found
        """
        try:
            # Try contractors table first
            result = self.client.table("contractors").select("*").eq("id", contractor_id).execute()
            
            if result.data:
                return result.data[0]
            
            # Try contractor_leads table
            result = self.client.table("contractor_leads").select("*").eq("id", contractor_id).execute()
            
            if result.data:
                return result.data[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting contractor {contractor_id}: {e}")
            return None

    async def get_contractor_lead_by_id(self, contractor_id: str) -> Optional[dict]:
        """
        Get contractor lead details by ID
        
        Args:
            contractor_id: Contractor UUID
            
        Returns:
            Contractor lead data or None if not found
        """
        try:
            result = self.client.table("contractor_leads").select("*").eq("id", contractor_id).execute()
            
            if result.data:
                return result.data[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting contractor lead {contractor_id}: {e}")
            return None

# Create a singleton instance
db = SupabaseDB()
