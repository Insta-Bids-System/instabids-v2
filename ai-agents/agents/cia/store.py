"""
CIA Store - Clean database operations for CIA agent
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class CIAStore:
    """Handles all database operations for CIA agent"""
    
    def __init__(self):
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.warning("Supabase credentials not found, using mock mode")
            self.supabase = None
        else:
            self.supabase: Client = create_client(url, key)
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Load user's conversation history and preferences
        Returns context for system prompt
        """
        if not self.supabase:
            return {"new_user": True}
            
        try:
            # Get user's most recent conversation
            result = self.supabase.table("unified_conversations").select("*").eq(
                "created_by", user_id
            ).order("updated_at", desc=True).limit(1).execute()
            
            if result.data:
                conversation = result.data[0]
                
                # Get recent messages for context
                messages = self.supabase.table("unified_messages").select("*").eq(
                    "conversation_id", conversation["id"]
                ).order("created_at", desc=True).limit(10).execute()
                
                return {
                    "conversation_id": conversation["id"],
                    "last_summary": conversation.get("metadata", {}).get("summary", ""),
                    "recent_messages": messages.data if messages.data else [],
                    "created_at": conversation["created_at"]
                }
            
            return {"new_user": True}
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {"error": str(e)}
    
    async def get_other_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get user's other active projects for multi-project awareness
        """
        if not self.supabase:
            return []
            
        try:
            # Get active bid cards for this user
            result = self.supabase.table("bid_cards").select(
                "id, bid_card_number, project_type, status, created_at"
            ).eq(
                "user_id", user_id
            ).in_("status", ["generated", "collecting_bids", "bids_complete"]).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting other projects: {e}")
            return []
    
    async def save_conversation_turn(
        self, 
        conversation_id: str,
        user_message: str,
        agent_response: str,
        extracted_data: Dict[str, Any],
        user_id: str,
        session_id: str
    ):
        """Save conversation turn to unified_messages table"""
        if not self.supabase:
            logger.info("Mock mode: Would save conversation turn")
            return
            
        try:
            timestamp = datetime.now().isoformat()
            
            # Save user message
            self.supabase.table("unified_messages").insert({
                "conversation_id": conversation_id,
                "sender_type": "user",
                "content": user_message,
                "created_at": timestamp
            }).execute()
            
            # Save agent response with extracted data
            self.supabase.table("unified_messages").insert({
                "conversation_id": conversation_id,
                "sender_type": "assistant", 
                "content": agent_response,
                "metadata": {
                    "extracted_data": extracted_data,
                    "session_id": session_id,
                    "extraction_timestamp": timestamp
                },
                "created_at": timestamp
            }).execute()
            
            # Update conversation updated_at
            self.supabase.table("unified_conversations").update({
                "updated_at": timestamp,
                "metadata": {
                    "last_extracted_data": extracted_data,
                    "total_fields_extracted": len([v for v in extracted_data.values() if v])
                }
            }).eq("id", conversation_id).execute()
            
            logger.info(f"Saved conversation turn with {len(extracted_data)} extracted fields")
            
        except Exception as e:
            logger.error(f"Error saving conversation turn: {e}")
    
    async def ensure_conversation_exists(
        self, 
        user_id: str, 
        session_id: str
    ) -> str:
        """
        Ensure a conversation exists for this session
        Returns conversation_id
        """
        if not self.supabase:
            import uuid
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"mock-conversation-{session_id}"))
            
        try:
            import uuid
            
            # Check if conversation exists for this session
            result = self.supabase.table("unified_conversations").select("id").eq(
                "session_id", session_id
            ).execute()
            
            if result.data:
                return result.data[0]["id"]
            
            # Ensure user_id is a valid UUID or None
            if user_id:
                try:
                    uuid.UUID(user_id)
                except:
                    # If not a valid UUID, set to None for anonymous users
                    user_id = None
            
            # Create new conversation with a valid UUID
            conversation_id = str(uuid.uuid4())
            new_conversation = self.supabase.table("unified_conversations").insert({
                "id": conversation_id,
                "user_id": user_id,
                "session_id": session_id,
                "agent_type": "CIA",
                "title": "Project Discussion",
                "metadata": {
                    "agent": "CIA",
                    "version": "2.0_clean"
                },
                "created_at": datetime.now().isoformat()
            }).execute()
            
            if new_conversation.data:
                logger.info(f"Created new conversation: {conversation_id}")
                return conversation_id
            
            # Return a valid UUID as fallback
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"fallback-{session_id}"))
            
        except Exception as e:
            logger.error(f"Error ensuring conversation: {e}")
            import uuid
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"error-{session_id}"))
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's saved preferences from previous conversations
        Used for personalization
        """
        if not self.supabase:
            return {}
            
        try:
            # Get from user_memories table
            result = self.supabase.table("user_memories").select("*").eq(
                "user_id", user_id
            ).execute()
            
            if result.data:
                preferences = {}
                for memory in result.data:
                    key = memory.get("memory_key", "")
                    value = memory.get("memory_value", {})
                    
                    if "budget" in key:
                        preferences["typical_budget"] = value
                    elif "timeline" in key:
                        preferences["timeline_preference"] = value
                    elif "contractor" in key:
                        preferences["contractor_preference"] = value
                
                return preferences
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}