"""
IRIS Inspiration Memory Manager Service
Handles memory persistence for inspiration boards and design preferences
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages memory for IRIS Inspiration agent: session and inspiration context"""
    
    def __init__(self):
        self.db = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            from database import db
            self.db = db
            logger.info("Inspiration memory manager database connection initialized")
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
                'id': str(uuid.uuid4()),
                'conversation_id': conversation_id,
                'sender_type': 'user' if sender == 'user' else 'agent',
                'sender_id': metadata.get('user_id') if sender == 'user' else None,
                'agent_type': 'IRIS_INSPIRATION',
                'content': content,
                'content_type': message_type,
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
    
    # INSPIRATION CONTEXT MEMORY
    def save_style_preferences(
        self,
        conversation_id: str,
        user_id: str,
        style_preferences: Dict[str, Any]
    ) -> bool:
        """Save learned style preferences to memory"""
        if not self.db:
            return False
        
        try:
            result = self.db.client.table('unified_conversation_memory').insert({
                'conversation_id': conversation_id,
                'memory_type': 'style_preferences',
                'memory_key': f"style_prefs_{user_id}",
                'memory_value': {
                    'user_id': user_id,
                    'preferences': style_preferences,
                    'learned_at': datetime.utcnow().isoformat()
                },
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error saving style preferences: {e}")
            return False
    
    def get_style_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user's learned style preferences"""
        if not self.db:
            return {}
        
        try:
            result = self.db.client.table('unified_conversation_memory').select('*').eq(
                'memory_type', 'style_preferences'
            ).like('memory_key', f'%{user_id}%').order('created_at', desc=True).limit(1).execute()
            
            if result.data:
                return result.data[0].get('memory_value', {}).get('preferences', {})
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting style preferences: {e}")
            return {}
    
    def save_inspiration_analysis(
        self,
        conversation_id: str,
        session_id: str,
        board_id: str,
        analysis_results: Dict[str, Any],
        image_urls: List[str]
    ) -> bool:
        """Save inspiration image analysis results to memory"""
        memory_value = {
            'session_id': session_id,
            'board_id': board_id,
            'analysis_results': analysis_results,
            'image_urls': image_urls,
            'analyzed_at': datetime.utcnow().isoformat()
        }
        
        return self.save_context_memory(
            conversation_id=conversation_id,
            memory_type='inspiration_analysis',
            memory_key=f"inspiration_{session_id}",
            memory_value=memory_value
        )
    
    def save_context_memory(
        self,
        conversation_id: str,
        memory_type: str,
        memory_key: str,
        memory_value: Dict[str, Any]
    ) -> bool:
        """Save context memory entry"""
        if not self.db:
            return False
        
        try:
            result = self.db.client.table('unified_conversation_memory').insert({
                'conversation_id': conversation_id,
                'memory_type': memory_type,
                'memory_key': memory_key,
                'memory_value': memory_value,
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error saving context memory: {e}")
            return False
    
    # INSPIRATION BOARDS ACCESS
    def get_user_inspiration_boards(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's inspiration boards"""
        if not self.db:
            return []
        
        try:
            result = self.db.client.table('inspiration_boards').select('*').eq(
                'user_id', user_id
            ).order('updated_at', desc=True).execute()
            
            boards = []
            for board in result.data or []:
                boards.append({
                    'id': board.get('id'),
                    'title': board.get('title'),
                    'room_type': board.get('room_type'),
                    'status': board.get('status'),
                    'description': board.get('description'),
                    'ai_insights': board.get('ai_insights', {}),
                    'created_at': board.get('created_at'),
                    'updated_at': board.get('updated_at')
                })
            
            return boards
            
        except Exception as e:
            logger.error(f"Error getting inspiration boards: {e}")
            return []
    
    def get_board_images(self, board_id: str) -> List[Dict[str, Any]]:
        """Get images for a specific board"""
        if not self.db:
            return []
        
        try:
            result = self.db.client.table('inspiration_images').select('*').eq(
                'board_id', board_id
            ).order('created_at', desc=True).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting board images: {e}")
            return []
    
    def get_complete_inspiration_context(self, user_id: str, conversation_id: str) -> Dict[str, Any]:
        """Get complete inspiration context for user"""
        context = {
            'session_memory': self.get_conversation_history(conversation_id),
            'inspiration_boards': self.get_user_inspiration_boards(user_id),
            'style_preferences': self.get_style_preferences(user_id),
            'design_history': self._get_design_history(user_id),
            'room_preferences': self._get_room_preferences(user_id),
            'memory_stats': {
                'total_boards': len(self.get_user_inspiration_boards(user_id)),
                'session_messages': len(self.get_conversation_history(conversation_id)),
                'has_style_prefs': bool(self.get_style_preferences(user_id))
            }
        }
        
        logger.info(f"Retrieved inspiration context for user {user_id}: {context['memory_stats']}")
        return context
    
    def create_or_get_conversation_id(self, user_id: str, session_id: str) -> str:
        """Create new conversation or get existing one for inspiration"""
        if not self.db:
            return str(uuid.uuid4())
        
        try:
            # Try to find existing inspiration conversation for this session
            result = self.db.client.table('unified_conversations').select('id').eq(
                'created_by', user_id
            ).eq('session_id', session_id).eq('entity_type', 'inspiration').limit(1).execute()
            
            if result.data:
                return result.data[0]['id']
            
            # Create new inspiration conversation
            conversation_id = str(uuid.uuid4())
            self.db.client.table('unified_conversations').insert({
                'id': conversation_id,
                'created_by': user_id,
                'session_id': session_id,
                'conversation_type': 'iris_inspiration',
                'entity_type': 'inspiration',
                'title': f'Design Inspiration Session {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                'metadata': {'agent': 'iris_inspiration', 'session_id': session_id},
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
            logger.info(f"Created new inspiration conversation: {conversation_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error creating/getting inspiration conversation ID: {e}")
            return str(uuid.uuid4())
    
    def _get_design_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's design exploration history"""
        try:
            result = self.db.client.table('unified_conversation_memory').select('*').eq(
                'memory_type', 'inspiration_analysis'
            ).order('created_at', desc=True).limit(20).execute()
            
            # Filter for this user's sessions
            user_history = []
            for entry in result.data or []:
                memory_value = entry.get('memory_value', {})
                if memory_value.get('user_id') == user_id:
                    user_history.append(memory_value)
            
            return user_history[:10]  # Return last 10 design explorations
            
        except Exception as e:
            logger.error(f"Error getting design history: {e}")
            return []
    
    def _get_room_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user's room-specific preferences"""
        boards = self.get_user_inspiration_boards(user_id)
        room_prefs = {}
        
        for board in boards:
            room_type = board.get('room_type')
            if room_type and room_type not in room_prefs:
                room_prefs[room_type] = {
                    'boards_count': 1,
                    'last_updated': board.get('updated_at'),
                    'preferred_styles': board.get('ai_insights', {}).get('style_preferences', [])
                }
            elif room_type:
                room_prefs[room_type]['boards_count'] += 1
        
        return room_prefs