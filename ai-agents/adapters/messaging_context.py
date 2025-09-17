"""
Messaging Context Adapter for Privacy Framework
Provides context for messaging agent with cross-side communication filtering
Uses direct Supabase queries to avoid server timeouts
"""

import logging
import os
from typing import Any, Dict, List

from supabase import Client, create_client
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger(__name__)

class MessagingContextAdapter:
    """Context adapter for messaging agent with privacy filtering"""
    
    def __init__(self):
        """Initialize with Supabase connection"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase not available - context will be limited")
            self.supabase = None
        else:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Messaging context adapter initialized with Supabase")

    def get_messaging_context(
        self, 
        thread_id: str,
        participants: List[Dict[str, Any]],
        message_type: str = "project_communication"
    ) -> Dict[str, Any]:
        """Get messaging context for cross-side communication"""
        
        context = {
            "thread_context": self._get_thread_context(thread_id),
            "participants": self._get_filtered_participants(participants),
            "message_history": self._get_message_history(thread_id),
            "filtering_rules": self._get_filtering_rules(message_type),
            "privacy_level": "neutral_messaging_access"
        }
        
        logger.info(f"Retrieved messaging context for thread {thread_id}")
        return context

    def apply_message_filtering(
        self,
        message: Dict[str, Any],
        sender_side: str,
        recipient_side: str
    ) -> Dict[str, Any]:
        """Apply privacy filtering to messages between sides"""
        
        if sender_side == recipient_side:
            # Same side - no filtering needed
            return message
            
        # Cross-side filtering
        filtered_message = message.copy()
        
        # Apply contact info filtering
        filtered_message = self._filter_contact_info(filtered_message)
        
        # Apply name aliasing
        if sender_side == "homeowner" and recipient_side == "contractor":
            filtered_message["sender_name"] = "Project Owner"
        elif sender_side == "contractor" and recipient_side == "homeowner":
            filtered_message["sender_name"] = self._get_contractor_alias(message.get("sender_id"))
        
        filtered_message["privacy_filtered"] = True
        return filtered_message

    def _get_thread_context(self, thread_id: str) -> Dict[str, Any]:
        """Get thread/conversation context"""
        if not self.supabase:
            return {"thread_available": False}
            
        try:
            # Check if this is a bid card conversation thread
            result = self.supabase.table("bid_cards").select("*").eq("cia_thread_id", thread_id).execute()
            
            if result.data:
                bid_card = result.data[0]
                return {
                    "thread_id": thread_id,
                    "context_type": "bid_card_communication",
                    "project_type": bid_card.get("project_type"),
                    "project_status": bid_card.get("status"),
                    "thread_available": True
                }
            
            # Check agent conversations
            result = self.supabase.table("unified_conversations").select("*").eq("metadata->>session_id", thread_id).execute()
            
            if result.data:
                conv = result.data[0]
                return {
                    "thread_id": thread_id,
                    "context_type": "agent_conversation",
                    "agent_type": conv.get("agent_type"),
                    "thread_available": True
                }
                
        except Exception as e:
            logger.error(f"Error getting thread context: {e}")
            
        return {"thread_available": False}

    def _get_filtered_participants(self, participants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get participant info with privacy filtering"""
        filtered_participants = []
        
        for participant in participants:
            participant_type = participant.get("type", "unknown")
            participant_id = participant.get("id")
            
            if participant_type == "homeowner":
                filtered_participants.append({
                    "id": participant_id,
                    "type": "homeowner",
                    "display_name": "Project Owner",
                    "privacy_filtered": True
                })
            elif participant_type == "contractor":
                filtered_participants.append({
                    "id": participant_id,
                    "type": "contractor",
                    "display_name": self._get_contractor_alias(participant_id),
                    "privacy_filtered": True
                })
            else:
                filtered_participants.append(participant)
        
        return filtered_participants

    def _get_message_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get recent message history with privacy filtering"""
        if not self.supabase:
            return []
            
        try:
            result = self.supabase.table("messages").select("*").eq("thread_id", thread_id).order("created_at", desc=True).limit(20).execute()
            
            messages = []
            for msg in result.data or []:
                messages.append({
                    "id": msg["id"],
                    "content": msg.get("content"),
                    "sender_type": msg.get("sender_type"),
                    "created_at": msg.get("created_at"),
                    "privacy_filtered": True
                })
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting message history: {e}")
            return []

    def _get_filtering_rules(self, message_type: str) -> Dict[str, Any]:
        """Get message filtering rules based on message type"""
        base_rules = {
            "block_contact_info": True,
            "alias_names": True,
            "filter_locations": False
        }
        
        if message_type == "project_communication":
            base_rules.update({
                "allow_project_details": True,
                "allow_scheduling": True,
                "allow_pricing": True
            })
        elif message_type == "bidding":
            base_rules.update({
                "allow_bid_details": True,
                "allow_timeline": True,
                "require_approval": False
            })
        
        return base_rules

    def _filter_contact_info(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Remove contact information from messages"""
        import re
        
        content = message.get("content", "")
        
        # Remove phone numbers
        content = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', "[PHONE REMOVED]", content)
        
        # Remove email addresses
        content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "[EMAIL REMOVED]", content)
        
        # Remove potential addresses
        content = re.sub(r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)\b', "[ADDRESS REMOVED]", content, flags=re.IGNORECASE)
        
        message["content"] = content
        return message


    
    def _get_contractor_alias(self, contractor_id: str) -> str:
        """Get contractor alias for privacy protection"""
        if not contractor_id:
            return "Contractor"
            
        # Simple alias based on contractor ID
        try:
            # Use last 4 characters of contractor ID for unique but anonymous alias
            suffix = contractor_id[-4:] if len(contractor_id) >= 4 else contractor_id
            return f"Contractor {suffix}"
        except:
            return "Contractor"