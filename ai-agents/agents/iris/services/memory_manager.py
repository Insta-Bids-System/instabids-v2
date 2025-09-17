"""
IRIS Memory Manager Service
Handles all memory persistence and context management across the 3 memory systems
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from ..models.database import MemoryEntry, ConversationMessage, MemoryType

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages all IRIS memory systems: session, context, and cross-session memory"""
    
    def __init__(self):
        self.db = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            from database import db
            self.db = db
            logger.info("Memory manager database connection initialized")
        except ImportError as e:
            logger.error(f"Failed to initialize database: {e}")
    
    # SESSION MEMORY (unified_conversation_messages)
    def save_conversation_message(
        self, 
        conversation_id: str, 
        sender: str, 
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Save message to unified conversation history"""
        if not self.db:
            logger.error("Database not initialized")
            return False
        
        try:
            result = self.db.client.table('unified_conversation_messages').insert({
                'conversation_id': conversation_id,
                'sender': sender,
                'content': content,
                'message_type': message_type,
                'metadata': metadata or {},
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error saving conversation message: {e}")
            return False
    
    def get_conversation_history(
        self, 
        conversation_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history from session memory"""
        if not self.db:
            return []
        
        try:
            result = self.db.client.table('unified_conversation_messages').select('*').eq(
                'conversation_id', conversation_id
            ).order('created_at', desc=False).limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    # CONTEXT MEMORY (unified_conversation_memory)
    def save_context_memory(
        self,
        conversation_id: str,
        memory_type: MemoryType,
        memory_key: str,
        memory_value: Dict[str, Any]
    ) -> bool:
        """Save context memory entry"""
        if not self.db:
            logger.error("Database not initialized")
            return False
        
        try:
            result = self.db.client.table('unified_conversation_memory').insert({
                'conversation_id': conversation_id,
                'memory_type': memory_type.value,
                'memory_key': memory_key,
                'memory_value': memory_value,
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error saving context memory: {e}")
            return False
    
    def get_context_memory(
        self,
        conversation_id: str,
        memory_type: Optional[MemoryType] = None
    ) -> List[Dict[str, Any]]:
        """Get context memory entries"""
        if not self.db:
            return []
        
        try:
            query = self.db.client.table('unified_conversation_memory').select('*').eq(
                'conversation_id', conversation_id
            )
            
            if memory_type:
                query = query.eq('memory_type', memory_type.value)
            
            result = query.order('created_at', desc=True).execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting context memory: {e}")
            return []
    
    def save_image_analysis_memory(
        self,
        conversation_id: str,
        session_id: str,
        image_analysis: Dict[str, Any],
        image_paths: List[str]
    ) -> bool:
        """Save image analysis results to context memory"""
        memory_value = {
            'session_id': session_id,
            'analysis_results': image_analysis,
            'image_paths': image_paths,
            'analyzed_at': datetime.utcnow().isoformat()
        }
        
        return self.save_context_memory(
            conversation_id=conversation_id,
            memory_type=MemoryType.IMAGE_ANALYSIS,
            memory_key=f"image_analysis_{session_id}",
            memory_value=memory_value
        )
    
    # CROSS-SESSION MEMORY (multiple tables)
    def get_user_inspiration_boards(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's inspiration boards from cross-session memory"""
        if not self.db:
            return []
        
        try:
            result = self.db.client.table('inspiration_boards').select('*').eq(
                'user_id', user_id
            ).order('updated_at', desc=True).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting inspiration boards: {e}")
            return []
    
    def get_user_property_photos(
        self, 
        user_id: str, 
        room_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get user's property photos from cross-session memory"""
        if not self.db:
            return []
        
        try:
            query = self.db.client.table('property_photos').select('*').eq('user_id', user_id)
            
            if room_type:
                query = query.eq('room_type', room_type)
            
            result = query.order('created_at', desc=True).execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting property photos: {e}")
            return []
    
    def get_user_conversations(self, user_id: str) -> List[str]:
        """Get all conversation IDs for a user"""
        if not self.db:
            return []
        
        try:
            result = self.db.client.table("unified_conversations").select("id").eq(
                "created_by", user_id
            ).execute()
            return [conv["id"] for conv in result.data or []]
        except Exception as e:
            logger.error(f"Error getting user conversations: {e}")
            return []
    
    def get_complete_context(self, user_id: str, conversation_id: str) -> Dict[str, Any]:
        """Get complete context for IRIS including all memory systems"""
        context = {
            'session_memory': self.get_conversation_history(conversation_id),
            'context_memory': self.get_context_memory(conversation_id),
            'cross_session_memory': {
                'inspiration_boards': self.get_user_inspiration_boards(user_id),
                'property_photos': self.get_user_property_photos(user_id),
                'user_conversations': self.get_user_conversations(user_id)
            },
            'memory_stats': {
                'session_messages': len(self.get_conversation_history(conversation_id)),
                'context_entries': len(self.get_context_memory(conversation_id)),
                'inspiration_boards': len(self.get_user_inspiration_boards(user_id)),
                'property_photos': len(self.get_user_property_photos(user_id))
            }
        }
        
        logger.info(f"Retrieved complete context for user {user_id}: {context['memory_stats']}")
        return context
    
    def create_or_get_conversation_id(self, user_id: str, session_id: str) -> str:
        """Create new conversation or get existing one"""
        if not self.db:
            return str(uuid.uuid4())
        
        try:
            # Try to find existing conversation for this session
            result = self.db.client.table('unified_conversations').select('id').eq(
                'created_by', user_id
            ).eq('session_id', session_id).limit(1).execute()
            
            if result.data:
                return result.data[0]['id']
            
            # Create new conversation
            conversation_id = str(uuid.uuid4())
            self.db.client.table('unified_conversations').insert({
                'id': conversation_id,
                'created_by': user_id,
                'session_id': session_id,
                'conversation_type': 'iris_design_consultation',
                'entity_type': 'inspiration',
                'title': f'IRIS Design Session {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                'metadata': {'agent': 'iris', 'session_id': session_id},
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
            logger.info(f"Created new conversation: {conversation_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error creating/getting conversation ID: {e}")
            return str(uuid.uuid4())
    
    def update_board_context(
        self,
        board_id: str,
        status: Optional[str] = None,
        room_type: Optional[str] = None,
        title: Optional[str] = None
    ) -> bool:
        """Update inspiration board context"""
        if not self.db:
            return False
        
        try:
            updates = {'updated_at': datetime.utcnow().isoformat()}
            
            if status:
                updates['status'] = status
            if room_type:
                updates['room_type'] = room_type
            if title:
                updates['title'] = title
            
            result = self.db.client.table('inspiration_boards').update(updates).eq(
                'id', board_id
            ).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating board context: {e}")
            return False