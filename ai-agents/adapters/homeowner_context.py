"""
Homeowner Context Adapter for CIA Agent
Provides FULL DATABASE ACCESS for the homeowner-facing agent
This adapter defines ALL table access for the CIA agent
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import json

from supabase import Client, create_client
from dotenv import load_dotenv

# Load from ROOT env file
root_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(root_env_path, override=True)

logger = logging.getLogger(__name__)

class HomeownerContextAdapter:
    """
    FULL ACCESS Context Adapter for CIA (Customer Interface Agent)
    This adapter provides complete database access for the homeowner agent
    """
    
    def __init__(self):
        """Initialize with Supabase connection from root .env"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("CRITICAL: Supabase credentials not found! CIA will not function!")
            raise ValueError("Supabase credentials missing - check root .env file")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info(f"CIA Adapter initialized with FULL database access")
        logger.info(f"Supabase URL: {self.supabase_url}")
        logger.info(f"Key loaded: {self.supabase_key[:20]}...")

    # ==================== UNIFIED CONVERSATION SYSTEM ====================
    
    def get_unified_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all unified conversations for a user"""
        try:
            result = self.supabase.table("unified_conversations").select("*").eq("created_by", user_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting unified conversations: {e}")
            return []
    
    def get_unified_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation"""
        try:
            result = self.supabase.table("unified_messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting unified messages: {e}")
            return []
    
    def save_unified_message(self, message_data: Dict[str, Any]) -> Optional[str]:
        """Save a message to unified system"""
        try:
            result = self.supabase.table("unified_messages").insert(message_data).execute()
            if result.data:
                return result.data[0]["id"]
        except Exception as e:
            logger.error(f"Error saving unified message: {e}")
        return None
    
    def get_unified_memory(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation memory"""
        try:
            result = self.supabase.table("unified_conversation_memory").select("*").eq("conversation_id", conversation_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting unified memory: {e}")
            return []
    
    def save_unified_memory(self, memory_data: Dict[str, Any]) -> bool:
        """Save memory to unified system"""
        try:
            result = self.supabase.table("unified_conversation_memory").insert(memory_data).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error saving unified memory: {e}")
            return False
    
    def get_message_attachments(self, message_id: str) -> List[Dict[str, Any]]:
        """Get attachments for a message"""
        try:
            result = self.supabase.table("unified_message_attachments").select("*").eq("message_id", message_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting attachments: {e}")
            return []
    
    def save_message_attachment(self, attachment_data: Dict[str, Any]) -> Optional[str]:
        """Save attachment to unified system"""
        try:
            result = self.supabase.table("unified_message_attachments").insert(attachment_data).execute()
            if result.data:
                return result.data[0]["id"]
        except Exception as e:
            logger.error(f"Error saving attachment: {e}")
        return None

    # ==================== USER & PROJECT TABLES ====================
    
    def get_homeowner(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get homeowner profile"""
        try:
            result = self.supabase.table("homeowners").select("*").eq("user_id", user_id).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            logger.error(f"Error getting homeowner: {e}")
        return None
    
    def get_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all projects for a homeowner"""
        try:
            result = self.supabase.table("projects").select("*").eq("user_id", user_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return []
    
    def get_properties(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all properties for a homeowner"""
        try:
            # Properties table uses user_id, not user_id
            result = self.supabase.table("properties").select("*").eq("user_id", user_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting properties: {e}")
            return []
    
    def get_bid_cards(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all bid cards for a homeowner"""
        try:
            result = self.supabase.table("bid_cards").select("*").eq("user_id", user_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting bid cards: {e}")
            return []
    
    def get_bid_card(self, bid_card_id: str) -> Optional[Dict[str, Any]]:
        """Get specific bid card"""
        try:
            result = self.supabase.table("bid_cards").select("*").eq("id", bid_card_id).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            logger.error(f"Error getting bid card: {e}")
        return None
    
    def update_bid_card(self, bid_card_id: str, updates: Dict[str, Any]) -> bool:
        """Update bid card (for JAA integration)"""
        try:
            result = self.supabase.table("bid_cards").update(updates).eq("id", bid_card_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating bid card: {e}")
            return False
    
    def get_contractor_bids(self, bid_card_id: str) -> List[Dict[str, Any]]:
        """Get all bids for a bid card from bid_document JSONB field"""
        try:
            # Get bid card and extract submitted_bids from bid_document
            result = self.supabase.table("bid_cards").select("bid_document").eq("id", bid_card_id).execute()
            if not result or not result.data or not result.data[0]:
                return []
            
            # CRITICAL NULL CHECK: Ensure bid_document exists before accessing
            first_record = result.data[0]
            if not first_record or not isinstance(first_record, dict):
                return []
                
            bid_document = first_record.get("bid_document")
            
            # Handle None or empty bid_document
            if bid_document is None:
                return []
            
            # Parse if string
            if isinstance(bid_document, str):
                # Handle case where bid_document is stored as JSON string
                import json
                try:
                    bid_document = json.loads(bid_document)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse bid_document JSON for bid_card {bid_card_id}")
                    return []
            
            # Now bid_document should be a dict or we've already returned
            if not isinstance(bid_document, dict):
                return []
            
            # Safely get submitted_bids
            submitted_bids = bid_document.get("submitted_bids", [])
            
            # Parse submitted_bids if it's a JSON string
            if isinstance(submitted_bids, str):
                try:
                    submitted_bids = json.loads(submitted_bids)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse submitted_bids JSON for bid_card {bid_card_id}")
                    return []
            
            # Final validation
            return submitted_bids if isinstance(submitted_bids, list) else []
            
        except Exception as e:
            logger.error(f"Error getting contractor bids from bid_document: {e}")
            return []

    # ==================== MEMORY SYSTEM ====================
    
    def get_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all memories for a user"""
        try:
            result = self.supabase.table("user_memories").select("*").eq("user_id", user_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting user memories: {e}")
            return []
    
    def save_user_memory(self, memory_data: Dict[str, Any]) -> bool:
        """Save user memory"""
        try:
            result = self.supabase.table("user_memories").insert(memory_data).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error saving user memory: {e}")
            return False

    # ==================== RFI SYSTEM ====================
    
    def get_rfi_requests(self, bid_card_id: str) -> List[Dict[str, Any]]:
        """Get RFI requests for a bid card"""
        try:
            result = self.supabase.table("rfi_requests").select("*").eq("bid_card_id", bid_card_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting RFI requests: {e}")
            return []
    
    def get_rfi_responses(self, request_id: str) -> List[Dict[str, Any]]:
        """Get RFI responses"""
        try:
            result = self.supabase.table("rfi_responses").select("*").eq("request_id", request_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting RFI responses: {e}")
            return []
    
    def save_rfi_response(self, response_data: Dict[str, Any]) -> Optional[str]:
        """Save RFI response with images"""
        try:
            result = self.supabase.table("rfi_responses").insert(response_data).execute()
            if result.data:
                return result.data[0]["id"]
        except Exception as e:
            logger.error(f"Error saving RFI response: {e}")
        return None

    # ==================== MESSAGING SYSTEM ====================
    
    def get_messages(self, bid_card_id: str) -> List[Dict[str, Any]]:
        """Get messages for a bid card"""
        try:
            result = self.supabase.table("messages").select("*").eq("bid_card_id", bid_card_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []

    # ==================== STORAGE OPERATIONS ====================
    
    def upload_image(self, file_data: bytes, path: str, content_type: str = "image/jpeg") -> Optional[str]:
        """Upload image to Supabase Storage"""
        try:
            result = self.supabase.storage.from_("project-images").upload(
                path, file_data, {"content-type": content_type}
            )
            # Get public URL
            url = self.supabase.storage.from_("project-images").get_public_url(path)
            return url
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
        return None
    
    def get_image_url(self, path: str) -> str:
        """Get public URL for an image"""
        return self.supabase.storage.from_("project-images").get_public_url(path)

    # ==================== CONVERSATION CONTEXT SAVING ====================
    
    def save_conversation_context(
        self, 
        user_id: str, 
        conversation_data: Dict[str, Any],
        agent_type: str = "cia"
    ) -> bool:
        """
        Save conversation context to unified system
        This method is called by CIA agent to save conversation state
        """
        try:
            # Extract key data from conversation
            messages = conversation_data.get("messages", [])
            metadata = conversation_data.get("metadata", {})
            context_type = conversation_data.get("context_type", "conversation")
            
            # Save to unified_messages if messages exist
            if messages:
                for message in messages:
                    # Skip system messages
                    if message.get("role") == "system":
                        continue
                        
                    message_data = {
                        "conversation_id": metadata.get("conversation_id"),
                        "sender_type": "user" if message["role"] == "user" else "agent",
                        "sender_id": user_id if message["role"] == "user" else agent_type,
                        "agent_type": agent_type if message["role"] == "assistant" else None,
                        "content": message.get("content", ""),
                        "content_type": "text",
                        "metadata": {
                            "context_type": context_type,
                            "timestamp": message.get("metadata", {}).get("timestamp", datetime.now().isoformat())
                        }
                    }
                    
                    # Save message
                    result = self.supabase.table("unified_messages").insert(message_data).execute()
                    if not result.data:
                        logger.warning(f"Failed to save message for {message['role']}")
            
            # Save conversation metadata if needed
            if metadata.get("conversation_id"):
                # Update or create conversation record
                conv_data = {
                    "id": metadata.get("conversation_id"),
                    "user_id": user_id,
                    "agent_type": agent_type,
                    "context_type": context_type,
                    "metadata": metadata,
                    "updated_at": datetime.now().isoformat()
                }
                
                # Try to update existing conversation
                result = self.supabase.table("unified_conversations").upsert(conv_data).execute()
                if result.data:
                    logger.info(f"Saved conversation context for {metadata.get('conversation_id')}")
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving conversation context: {e}")
            return False

    # ==================== COMPREHENSIVE CONTEXT METHOD ====================
    
    def get_full_agent_context(
        self, 
        user_id: str, 
        specific_bid_card_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get COMPLETE context for CIA agent with FULL database access
        This is the main method CIA should use to get all context
        """
        
        context = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "access_level": "FULL_DATABASE_ACCESS"
        }
        
        # Get homeowner profile
        homeowner = self.get_homeowner(user_id)
        if homeowner and isinstance(homeowner, dict):
            context["homeowner"] = homeowner
            user_id = homeowner.get("id", user_id)
            
            # Get all related data
            context["projects"] = self.get_projects(user_id)
            context["properties"] = self.get_properties(user_id)  # Use user_id for properties
            # Use user_id for bid cards since that's what the table uses
            context["bid_cards"] = self.get_bid_cards(user_id)
            context["user_memories"] = self.get_user_memories(user_id)
            
            # Get contractor bids for ALL bid cards
            all_contractor_bids = []
            bid_cards_list = context.get("bid_cards", [])
            if bid_cards_list and isinstance(bid_cards_list, list):
                for bid_card in bid_cards_list:
                    if not bid_card or not isinstance(bid_card, dict):
                        continue
                    card_id = bid_card.get("id")
                    if card_id:
                        bids = self.get_contractor_bids(card_id)
                        if bids and isinstance(bids, list):
                            for bid in bids:
                                if bid and isinstance(bid, dict):
                                    bid["bid_card_id"] = card_id
                                    bid["project_type"] = bid_card.get("project_type")
                                    bid["bid_card_number"] = bid_card.get("bid_card_number")
                            all_contractor_bids.extend(bids)
            context["contractor_bids"] = all_contractor_bids
        
        # Get specific bid card context if provided (using renamed parameter)
        if specific_bid_card_id:
            context["current_bid_card"] = self.get_bid_card(specific_bid_card_id)
            # Don't overwrite all contractor bids - add specific bid card bids separately
            specific_bids = self.get_contractor_bids(specific_bid_card_id)
            if specific_bids:
                context["current_bid_card_bids"] = specific_bids
            context["rfi_requests"] = self.get_rfi_requests(specific_bid_card_id)
            context["messages"] = self.get_messages(specific_bid_card_id)
        
        # Get conversation context if provided
        if conversation_id:
            context["messages"] = self.get_unified_messages(conversation_id)
            context["memory"] = self.get_unified_memory(conversation_id)
            
            # Get attachments for all messages
            attachments = {}
            for msg in context.get("messages", []):
                msg_id = msg.get("id")
                if msg_id:
                    msg_attachments = self.get_message_attachments(msg_id)
                    if msg_attachments:
                        attachments[msg_id] = msg_attachments
            context["attachments"] = attachments
        else:
            # Get all conversations for user
            context["conversations"] = self.get_unified_conversations(user_id)
        
        logger.info(f"CIA Context loaded: {len(context)} data categories")
        return context

    # ==================== HELPER METHODS ====================
    
    def search_bid_cards(self, query: str, user_id: str) -> List[Dict[str, Any]]:
        """Search bid cards by text"""
        try:
            result = self.supabase.table("bid_cards").select("*").eq(
                "user_id", user_id
            ).ilike("bid_document", f"%{query}%").execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error searching bid cards: {e}")
            return []
    
    def get_active_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """Get only active projects"""
        try:
            result = self.supabase.table("projects").select("*").eq(
                "user_id", user_id
            ).eq("status", "active").execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting active projects: {e}")
            return []
    
    def log_agent_action(self, action: str, details: Dict[str, Any]) -> bool:
        """Log CIA agent actions for debugging"""
        try:
            log_data = {
                "agent_type": "CIA",
                "action": action,
                "details": json.dumps(details),
                "timestamp": datetime.now().isoformat()
            }
            # Could save to a logging table if needed
            logger.info(f"CIA Action: {action} - {details}")
            return True
        except Exception as e:
            logger.error(f"Error logging action: {e}")
            return False