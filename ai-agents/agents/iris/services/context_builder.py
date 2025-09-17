"""
IRIS Context Builder Service
Aggregates user context from multiple sources for intelligent responses
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

from ..models.responses import ContextResponse
from .memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class ContextBuilder:
    """Builds comprehensive user context for IRIS conversations"""
    
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.db = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            from database import db
            self.db = db
            logger.info("Context builder database connection initialized")
        except ImportError as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def build_complete_context(
        self, 
        user_id: str, 
        conversation_id: str,
        project_id: Optional[str] = None
    ) -> ContextResponse:
        """Build complete user context for IRIS"""
        
        # Validate user_id format
        if not self._validate_user_id(user_id):
            logger.warning(f"Invalid user_id format: {user_id}. Using test mode.")
            user_id = "550e8400-e29b-41d4-a716-446655440001"  # Default test UUID
        
        context = ContextResponse(
            inspiration_boards=self._get_inspiration_boards(user_id),
            project_context=self._get_project_context(user_id, project_id),
            design_preferences=self._get_design_preferences(user_id),
            previous_designs=self._get_previous_designs(user_id),
            conversations_from_other_agents=self._get_conversations_from_other_agents(user_id, project_id),
            photos_from_unified_system=self._get_photos_from_unified_system(user_id, project_id),
            privacy_level="homeowner_side_access"
        )
        
        logger.info(f"Built complete context for user {user_id}")
        return context
    
    def _validate_user_id(self, user_id: str) -> bool:
        """Validate user_id is a valid UUID"""
        try:
            UUID(user_id)
            return True
        except ValueError:
            return False
    
    def _get_inspiration_boards(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's inspiration boards from unified conversation memory"""
        if not self.db:
            return []
        
        try:
            # Get user's conversations
            conv_ids = self.memory_manager.get_user_conversations(user_id)
            if not conv_ids:
                return []
            
            # Query unified_conversation_memory for inspiration-related entries
            result = self.db.client.table("unified_conversation_memory").select(
                "id, memory_key, memory_value, created_at, conversation_id"
            ).in_("conversation_id", conv_ids).eq("memory_type", "inspiration_board").execute()
            
            inspiration_data = []
            for memory in result.data or []:
                memory_value = memory.get("memory_value", {})
                inspiration_data.append({
                    "id": memory.get("id"),
                    "user_id": user_id,
                    "conversation_id": memory.get("conversation_id"),
                    "board_name": memory_value.get("board_name", "Inspiration Board"),
                    "images": memory_value.get("images", []),
                    "style_preferences": memory_value.get("style_preferences", {}),
                    "created_at": memory.get("created_at")
                })
            
            return inspiration_data
            
        except Exception as e:
            logger.error(f"Error getting inspiration boards: {e}")
            return []
    
    def _get_project_context(self, user_id: str, project_id: Optional[str]) -> Dict[str, Any]:
        """Get current project context from unified conversations"""
        if not project_id or not self.db:
            return {"project_available": False}
        
        # Validate project_id
        if not self._validate_user_id(project_id):
            logger.warning(f"Invalid project_id format: {project_id}")
            return {"project_available": False}
        
        try:
            # Find project in unified_conversations
            conv_result = self.db.client.table("unified_conversations").select(
                "id, title, metadata"
            ).eq("created_by", user_id).eq("entity_id", project_id).execute()
            
            if conv_result.data:
                conversation = conv_result.data[0]
                metadata = conversation.get("metadata", {})
                
                # Get related memory entries for this project
                memory_result = self.db.client.table("unified_conversation_memory").select(
                    "memory_value"
                ).eq("conversation_id", conversation["id"]).execute()
                
                project_data = {}
                for memory in memory_result.data or []:
                    memory_value = memory.get("memory_value", {})
                    if isinstance(memory_value, dict):
                        project_data.update(memory_value)
                
                return {
                    "project_id": project_id,
                    "project_type": metadata.get("project_type") or project_data.get("project_type"),
                    "description": metadata.get("description") or project_data.get("description"),
                    "budget_range": metadata.get("budget_range") or project_data.get("budget_range"),
                    "timeline": metadata.get("timeline") or project_data.get("timeline"),
                    "conversation_title": conversation.get("title"),
                    "project_available": True
                }
            
            # Fallback to legacy projects table if needed
            result = self.db.client.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()
            
            if result.data:
                project = result.data[0]
                return {
                    "project_id": project_id,
                    "project_type": project.get("project_type"),
                    "description": project.get("description"),
                    "budget_range": f"${project.get('budget_min', 0)}-${project.get('budget_max', 0)}",
                    "timeline": project.get("timeline"),
                    "project_available": True
                }
        except Exception as e:
            logger.error(f"Error getting project context: {e}")
        
        return {"project_available": False}
    
    def _get_design_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user's design style preferences from unified memory"""
        if not self.db:
            return {}
        
        try:
            # Get user's conversations
            conv_ids = self.memory_manager.get_user_conversations(user_id)
            if not conv_ids:
                return {}
            
            result = self.db.client.table("unified_conversation_memory").select(
                "memory_value"
            ).in_("conversation_id", conv_ids).eq("memory_type", "design_preferences").execute()
            
            preferences = {}
            for memory in result.data or []:
                memory_value = memory.get("memory_value", {})
                if isinstance(memory_value, dict):
                    preferences.update(memory_value)
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting design preferences: {e}")
            return {}
    
    def _get_previous_designs(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's previous design projects from unified memory"""
        if not self.db:
            return []
        
        try:
            # Get user's conversations
            conv_ids = self.memory_manager.get_user_conversations(user_id)
            if not conv_ids:
                return []
            
            # Query unified_conversation_memory for design-related entries
            result = self.db.client.table("unified_conversation_memory").select(
                "id, memory_key, memory_value, created_at"
            ).in_("conversation_id", conv_ids).eq("memory_type", "generated_design").limit(10).execute()
            
            designs = []
            for memory in result.data or []:
                memory_value = memory.get("memory_value", {})
                designs.append({
                    "id": memory.get("id"),
                    "user_id": user_id,
                    "design_concept": memory_value.get("design_concept", ""),
                    "images": memory_value.get("images", []),
                    "style_elements": memory_value.get("style_elements", []),
                    "created_at": memory.get("created_at")
                })
            
            return designs
        except Exception as e:
            logger.error(f"Error getting previous designs: {e}")
            return []
    
    def _get_conversations_from_other_agents(
        self, 
        user_id: str, 
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get relevant conversations from homeowner agent and messaging agent"""
        if not self.db:
            return {}
        
        try:
            conversations_data = {
                "homeowner_conversations": [],
                "messaging_conversations": [],
                "project_conversations": []
            }
            
            # Build query conditions
            query = self.db.client.table("unified_conversations").select(
                "id, conversation_type, entity_type, title, metadata, created_at"
            ).eq("created_by", user_id)
            
            if project_id and self._validate_user_id(project_id):
                query = query.eq("entity_id", project_id)
            
            result = query.execute()
            
            for conversation in result.data or []:
                conv_type = conversation.get("conversation_type", "")
                entity_type = conversation.get("entity_type", "")
                conv_data = {
                    "conversation_id": conversation.get("id"),
                    "title": conversation.get("title"),
                    "metadata": conversation.get("metadata", {}),
                    "created_at": conversation.get("created_at"),
                    "conversation_type": conv_type,
                    "entity_type": entity_type
                }
                
                # Categorize by conversation type
                if "homeowner" in conv_type.lower() or "hma" in conv_type.lower():
                    conversations_data["homeowner_conversations"].append(conv_data)
                elif "messaging" in conv_type.lower() or "cma" in conv_type.lower():
                    conversations_data["messaging_conversations"].append(conv_data)
                elif entity_type == "project":
                    conversations_data["project_conversations"].append(conv_data)
                else:
                    conversations_data["project_conversations"].append(conv_data)
            
            return conversations_data
            
        except Exception as e:
            logger.error(f"Error getting conversations from other agents: {e}")
            return {}
    
    def _get_photos_from_unified_system(
        self, 
        user_id: str, 
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get photos from the unified conversation system"""
        if not self.db:
            return {"project_photos": [], "inspiration_photos": [], "message_attachments": []}
        
        try:
            photos_data = {
                "project_photos": [],
                "inspiration_photos": [],
                "message_attachments": []
            }
            
            # Get user's conversations
            conv_ids = self.memory_manager.get_user_conversations(user_id)
            if not conv_ids:
                return photos_data
            
            # Get photos from memory entries
            memory_result = self.db.client.table("unified_conversation_memory").select(
                "memory_value"
            ).in_("conversation_id", conv_ids).eq("memory_type", "photo_reference").execute()
            
            for memory in memory_result.data or []:
                memory_value = memory.get("memory_value", {})
                if isinstance(memory_value, dict) and "images" in memory_value:
                    for image in memory_value["images"]:
                        photo_entry = {
                            "file_path": image.get("url") or image.get("path"),
                            "type": "image",
                            "metadata": image.get("metadata", {})
                        }
                        
                        # Categorize by metadata
                        metadata = image.get("metadata", {})
                        if metadata.get("category") == "inspiration":
                            photos_data["inspiration_photos"].append(photo_entry)
                        elif metadata.get("category") == "project":
                            photos_data["project_photos"].append(photo_entry)
                        else:
                            photos_data["project_photos"].append(photo_entry)
            
            return photos_data
            
        except Exception as e:
            logger.error(f"Error getting photos from unified system: {e}")
            return {"project_photos": [], "inspiration_photos": [], "message_attachments": []}
    
    def build_context_summary(self, user_id: str, conversation_id: str) -> str:
        """Build a text summary of user context for AI prompts"""
        context = self.build_complete_context(user_id, conversation_id)
        
        summary_parts = []
        
        # Inspiration boards
        if context.inspiration_boards:
            summary_parts.append(f"User has {len(context.inspiration_boards)} inspiration boards")
        
        # Project context
        if context.project_context.get("project_available"):
            project = context.project_context
            summary_parts.append(f"Current project: {project.get('project_type', 'Unknown type')}")
            if project.get("budget_range"):
                summary_parts.append(f"Budget: {project['budget_range']}")
        
        # Design preferences
        if context.design_preferences:
            prefs = list(context.design_preferences.keys())[:3]  # Top 3 preferences
            summary_parts.append(f"Design preferences: {', '.join(prefs)}")
        
        # Previous designs
        if context.previous_designs:
            summary_parts.append(f"Has {len(context.previous_designs)} previous design projects")
        
        # Photos
        photos = context.photos_from_unified_system
        total_photos = len(photos.get("project_photos", [])) + len(photos.get("inspiration_photos", []))
        if total_photos > 0:
            summary_parts.append(f"Has {total_photos} uploaded photos")
        
        return " | ".join(summary_parts) if summary_parts else "New user with no previous context"