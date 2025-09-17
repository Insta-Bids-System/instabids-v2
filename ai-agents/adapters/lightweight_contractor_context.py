"""
Lightweight Contractor Context Adapter for COIA Memory
Provides only essential conversation context without expensive queries
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from supabase import Client, create_client
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger(__name__)

class LightweightContractorContextAdapter:
    """Lightweight context adapter for COIA conversations - essential data only"""
    
    def __init__(self):
        """Initialize with Supabase connection"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase not available - context will be limited")
            self.supabase = None
        else:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Lightweight contractor context adapter initialized")

    def get_conversation_context(
        self, 
        contractor_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get lightweight context for COIA conversations - essential data only"""
        
        context = {
            # Core contractor data
            "contractor_profile": self._get_contractor_profile(contractor_id),
            
            # Conversation history only
            "conversation_history": self._get_conversation_history(contractor_id, session_id),
            
            # Essential metadata
            "privacy_level": "contractor_side_filtered",
            "adapter_version": "lightweight_1.0"
        }
        
        logger.info(f"Retrieved lightweight contractor context for contractor {contractor_id}")
        return context

    def _get_contractor_profile(self, contractor_id: str) -> Dict[str, Any]:
        """Get basic contractor profile information"""
        if not self.supabase:
            return {"contractor_id": contractor_id, "profile_available": False}
            
        try:
            # Try contractors table first
            result = self.supabase.table("contractors").select("*").eq("id", contractor_id).execute()
            
            if result.data:
                contractor = result.data[0]
                return {
                    "contractor_id": contractor_id,
                    "company_name": contractor.get("company_name"),
                    "rating": contractor.get("rating"),
                    "verified": contractor.get("verified", False),
                    "tier": contractor.get("tier", 3),
                    "total_jobs": contractor.get("total_jobs", 0),
                    "profile_available": True
                }
            else:
                # Try contractor_leads table
                result = self.supabase.table("contractor_leads").select("*").eq("id", contractor_id).execute()
                
                if result.data:
                    lead = result.data[0]
                    return {
                        "contractor_id": contractor_id,
                        "company_name": lead.get("company_name"),
                        "contact_name": lead.get("contact_name"),
                        "specialties": lead.get("specialties", []),
                        "years_in_business": lead.get("years_in_business"),
                        "profile_available": True
                    }
                    
        except Exception as e:
            logger.error(f"Error getting contractor profile: {e}")
            
        return {"contractor_id": contractor_id, "profile_available": False}

    def _get_conversation_history(self, contractor_id: str, session_id: Optional[str]) -> list:
        """Get contractor's conversation history with privacy filtering"""
        if not self.supabase:
            return []
            
        try:
            query = self.supabase.table("unified_conversations").select("*").eq("created_by", contractor_id).eq("metadata->>agent_type", "COIA")
            
            if session_id:
                query = query.eq("metadata->>session_id", session_id)
                
            result = query.order("created_at", desc=True).limit(5).execute()
            
            conversations = []
            for conv in result.data or []:
                metadata = conv.get("metadata", {})
                state = metadata.get("state", {})
                conversations.append({
                    "thread_id": metadata.get("session_id", conv["id"]),
                    "created_at": conv["created_at"],
                    "summary": self._extract_conversation_summary(state),
                    "privacy_filtered": True
                })
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []

    def _extract_conversation_summary(self, state_data: Dict[str, Any]) -> str:
        """Extract a summary from conversation state"""
        if not state_data:
            return "No summary available"
            
        current_stage = state_data.get("current_stage", "unknown")
        message_count = len(state_data.get("messages", []))
        
        return f"Stage: {current_stage}, Messages: {message_count}"
    
    def save_conversation(self, contractor_id: str, session_id: str, conversation_data: Dict[str, Any]) -> bool:
        """Save conversation to unified_conversations table"""
        if not self.supabase:
            return False
            
        try:
            # Prepare conversation record
            record = {
                "id": str(uuid.uuid4()) if not conversation_data.get("id") else conversation_data["id"],
                "created_by": contractor_id,
                "conversation_type": "contractor_chat",  # Required field
                "metadata": {
                    "session_id": session_id,
                    "agent_type": "COIA",
                    "state": conversation_data.get("state", {}),
                    "current_mode": conversation_data.get("current_mode", "conversation"),
                    "contractor_profile": conversation_data.get("contractor_profile", {})
                },
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upsert conversation
            result = self.supabase.table("unified_conversations").upsert(record).execute()
            
            if result.data:
                logger.info(f"Saved conversation for contractor {contractor_id}, session {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return False