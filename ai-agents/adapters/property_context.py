"""
Property Context Adapter for Unified Memory System Integration
Provides property-specific data access through the unified conversation memory system
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import uuid

from supabase import Client, create_client
from dotenv import load_dotenv

# Load from ROOT env file
root_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(root_env_path, override=True)

logger = logging.getLogger(__name__)

class PropertyContextAdapter:
    """
    Property Context Adapter for unified memory system integration
    Bridges property data with unified conversation memory architecture
    """
    
    def __init__(self):
        """Initialize with Supabase connection from root .env"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("CRITICAL: Supabase credentials not found!")
            raise ValueError("Supabase credentials missing - check root .env file")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("PropertyContextAdapter initialized with unified system access")

    def get_property_context(self, user_id: str, property_id: str) -> Dict[str, Any]:
        """
        Get complete property context through unified memory system
        Returns property photos, maintenance issues, and conversations
        """
        try:
            context = {
                "property_id": property_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "source": "unified_memory_system"
            }
            
            # Get property conversations from unified system
            property_conversations = self._get_property_conversations(user_id, property_id)
            context["property_conversations"] = property_conversations
            
            # Get property photos from unified memory
            property_photos = self._get_property_photos(property_conversations)
            context["property_photos"] = property_photos
            
            # Get maintenance issues from unified memory
            maintenance_issues = self._get_maintenance_issues(property_conversations)
            context["maintenance_issues"] = maintenance_issues
            
            # Get property basic info from legacy table
            property_info = self._get_property_info(property_id)
            context["property_info"] = property_info
            
            logger.info(f"Property context loaded: {len(property_photos)} photos, {len(maintenance_issues)} issues")
            return context
            
        except Exception as e:
            logger.error(f"Error getting property context: {e}")
            return {
                "property_id": property_id,
                "error": str(e),
                "property_photos": [],
                "maintenance_issues": [],
                "property_conversations": []
            }

    def _get_property_conversations(self, user_id: str, property_id: str) -> List[Dict[str, Any]]:
        """Get conversations related to specific property"""
        try:
            result = self.supabase.table("unified_conversations").select("*").eq(
                "created_by", user_id
            ).eq("entity_id", property_id).eq("entity_type", "property").execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting property conversations: {e}")
            return []

    def _get_property_photos(self, property_conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get property photos from unified memory system"""
        if not property_conversations:
            return []
        
        try:
            conv_ids = [conv["id"] for conv in property_conversations]
            
            # Get photo references from unified memory
            result = self.supabase.table("unified_conversation_memory").select(
                "memory_value, memory_key, created_at"
            ).in_("conversation_id", conv_ids).eq("memory_type", "photo_reference").execute()
            
            photos = []
            for memory in result.data or []:
                memory_value = memory.get("memory_value", {})
                if isinstance(memory_value, dict) and "images" in memory_value:
                    for image in memory_value["images"]:
                        metadata = image.get("metadata", {})
                        if metadata.get("category") == "property":
                            photos.append({
                                "url": image.get("url"),
                                "path": image.get("path"),
                                "metadata": metadata,
                                "memory_key": memory.get("memory_key"),
                                "created_at": memory.get("created_at"),
                                "type": "property_photo"
                            })
            
            return photos
        except Exception as e:
            logger.error(f"Error getting property photos: {e}")
            return []

    def _get_maintenance_issues(self, property_conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get maintenance issues from unified memory system"""
        if not property_conversations:
            return []
        
        try:
            conv_ids = [conv["id"] for conv in property_conversations]
            
            # Get maintenance issue memories
            result = self.supabase.table("unified_conversation_memory").select(
                "memory_value, memory_key, created_at"
            ).in_("conversation_id", conv_ids).eq("memory_type", "maintenance_issue").execute()
            
            issues = []
            for memory in result.data or []:
                memory_value = memory.get("memory_value", {})
                if isinstance(memory_value, dict):
                    issues.append({
                        "issue_type": memory_value.get("issue_type"),
                        "severity": memory_value.get("severity"),
                        "description": memory_value.get("description"),
                        "photo_reference": memory_value.get("photo_reference"),
                        "property_id": memory_value.get("property_id"),
                        "memory_key": memory.get("memory_key"),
                        "detected_at": memory.get("created_at"),
                        "type": "maintenance_issue"
                    })
            
            return issues
        except Exception as e:
            logger.error(f"Error getting maintenance issues: {e}")
            return []

    def _get_property_info(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get basic property info from properties table"""
        try:
            result = self.supabase.table("properties").select("*").eq("id", property_id).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            logger.error(f"Error getting property info: {e}")
        return None

    def create_property_conversation(self, user_id: str, property_id: str, title: str = None) -> Optional[str]:
        """Create a unified conversation for property context"""
        try:
            conversation_id = str(uuid.uuid4())
            
            conversation_data = {
                "id": conversation_id,
                "tenant_id": "00000000-0000-0000-0000-000000000000",
                "created_by": user_id,
                "conversation_type": "property_discussion",
                "entity_type": "property",
                "entity_id": property_id,
                "title": title or f"Property Discussion - {property_id}",
                "status": "active",
                "metadata": {
                    "property_id": property_id,
                    "context_type": "property"
                },
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("unified_conversations").insert(conversation_data).execute()
            
            if result.data:
                # Add participant record
                participant_data = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": "00000000-0000-0000-0000-000000000000",
                    "conversation_id": conversation_id,
                    "participant_id": user_id,
                    "participant_type": "user",
                    "role": "primary",
                    "joined_at": datetime.utcnow().isoformat()
                }
                
                self.supabase.table("unified_conversation_participants").insert(participant_data).execute()
                
                logger.info(f"Created property conversation: {conversation_id}")
                return conversation_id
            
        except Exception as e:
            logger.error(f"Error creating property conversation: {e}")
        return None

    def save_property_photo_to_unified(self, 
                                     conversation_id: str,
                                     property_id: str, 
                                     photo_url: str,
                                     photo_metadata: Dict[str, Any]) -> Optional[str]:
        """Save property photo to unified memory system"""
        try:
            memory_id = str(uuid.uuid4())
            
            # Ensure property category
            photo_metadata["category"] = "property"
            photo_metadata["property_id"] = property_id
            photo_metadata["uploaded_by"] = "property_system"
            photo_metadata["uploaded_at"] = datetime.now().isoformat()
            
            memory_data = {
                "id": memory_id,
                "tenant_id": "00000000-0000-0000-0000-000000000000",
                "conversation_id": conversation_id,
                "memory_scope": "conversation",
                "memory_type": "photo_reference",
                "memory_key": f"property_photo_{property_id}_{datetime.now().timestamp()}",
                "memory_value": {
                    "images": [{
                        "url": photo_url,
                        "path": photo_url.split("/")[-1] if "/" in photo_url else photo_url,
                        "thumbnail_url": photo_url,
                        "metadata": photo_metadata,
                        "source": "property_system"
                    }]
                },
                "importance_score": 8
            }
            
            result = self.supabase.table("unified_conversation_memory").insert(memory_data).execute()
            
            if result.data:
                logger.info(f"Property photo saved to unified memory: {memory_id}")
                return memory_id
            
        except Exception as e:
            logger.error(f"Error saving property photo to unified memory: {e}")
        return None

    def save_maintenance_issue_to_unified(self,
                                        conversation_id: str,
                                        property_id: str,
                                        issue_data: Dict[str, Any]) -> Optional[str]:
        """Save maintenance issue to unified memory system"""
        try:
            memory_id = str(uuid.uuid4())
            
            memory_data = {
                "id": memory_id,
                "tenant_id": "00000000-0000-0000-0000-000000000000",
                "conversation_id": conversation_id,
                "memory_scope": "conversation",
                "memory_type": "maintenance_issue",
                "memory_key": f"maintenance_{property_id}_{datetime.now().timestamp()}",
                "memory_value": {
                    "issue_type": issue_data.get("type"),
                    "severity": issue_data.get("severity"),
                    "description": issue_data.get("description"),
                    "photo_reference": issue_data.get("photo_url"),
                    "property_id": property_id,
                    "confidence": issue_data.get("confidence"),
                    "estimated_cost": issue_data.get("estimated_cost")
                },
                "importance_score": 7
            }
            
            result = self.supabase.table("unified_conversation_memory").insert(memory_data).execute()
            
            if result.data:
                logger.info(f"Maintenance issue saved to unified memory: {memory_id}")
                return memory_id
            
        except Exception as e:
            logger.error(f"Error saving maintenance issue to unified memory: {e}")
        return None

# Create singleton instance
property_context_adapter = PropertyContextAdapter()