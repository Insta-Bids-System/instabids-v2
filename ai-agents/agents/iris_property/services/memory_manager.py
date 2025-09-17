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
        """Initialize database connection - REQUIRED for IRIS functionality"""
        try:
            from database_simple import db
            self.db = db
            
            # Test database connection by attempting a simple query
            if hasattr(self.db, 'client') and self.db.client:
                # Try to query a table to verify connection works
                test_result = self.db.client.table('unified_conversations').select('id').limit(1).execute()
                logger.info("IRIS Memory manager database connection verified and working")
            else:
                raise Exception("Database client not properly initialized")
                
        except Exception as e:
            error_msg = f"CRITICAL: IRIS cannot function without database connection. Error: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
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
            # Map to actual database columns based on database.py
            result = self.db.client.table('unified_conversation_messages').insert({
                'id': str(uuid.uuid4()),
                'conversation_id': conversation_id,
                'sender_type': 'user' if sender == 'user' else 'agent',
                'sender_id': metadata.get('user_id') if sender == 'user' else None,
                'agent_type': 'IRIS',
                'content': content,
                'content_type': message_type,  # Use content_type instead of message_type
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
        memory_type: str,  # Changed from MemoryType to str
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
                'memory_type': memory_type,  # Use string directly
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
        memory_type: Optional[str] = None  # Changed from MemoryType to str
    ) -> List[Dict[str, Any]]:
        """Get context memory entries"""
        if not self.db:
            return []
        
        try:
            query = self.db.client.table('unified_conversation_memory').select('*').eq(
                'conversation_id', conversation_id
            )
            
            if memory_type:
                query = query.eq('memory_type', memory_type)  # Use string directly
            
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
            memory_type='image_analysis',  # Use string instead of MemoryType
            memory_key=f"image_analysis_{session_id}",
            memory_value=memory_value
        )
    
    # CROSS-SESSION MEMORY (multiple tables)
    def get_user_inspiration_boards(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's inspiration boards from unified memory"""
        if not self.db:
            return []
        
        try:
            # First try unified memory
            result = self.db.client.table('unified_conversation_memory').select('*').eq(
                'tenant_id', user_id
            ).eq('memory_type', 'inspiration_board').execute()
            
            boards = []
            if result.data:
                for memory in result.data:
                    board_data = memory.get('memory_value', {})
                    boards.append(board_data)
                return boards
            
            # Fallback to inspiration_boards table if available
            try:
                result = self.db.client.table('inspiration_boards').select('*').eq(
                    'user_id', user_id
                ).order('updated_at', desc=True).execute()
                
                if result.data:
                    # Convert to expected format
                    for board in result.data:
                        boards.append({
                            'board_id': board.get('id'),
                            'title': board.get('title'),
                            'room_type': board.get('room_type'),
                            'style_preferences': board.get('ai_insights', {}).get('style_preferences', []),
                            'notes': board.get('description'),
                            'images': [],
                            'created_at': board.get('created_at'),
                            'updated_at': board.get('updated_at')
                        })
                    return boards
            except:
                pass
            
            return []
            
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
    
    # ROOM DESCRIPTION MEMORY SYSTEM
    async def save_room_description_memory(
        self,
        user_id: str,
        memory_key: str,
        memory_data: Dict[str, Any]
    ) -> bool:
        """Save room description to unified memory for persistence across sessions"""
        if not self.db:
            return False
        
        try:
            # Check if memory entry exists
            existing = self.db.client.table('unified_conversation_memory').select('*').eq(
                'tenant_id', user_id
            ).eq('memory_key', memory_key).execute()
            
            # Build memory value with history
            if existing.data:
                # Update existing entry with history
                current_data = existing.data[0].get('memory_value', {})
                history = current_data.get('history', [])
                
                # Add current to history if it exists
                if current_data.get('current'):
                    history.append({
                        'description': current_data['current'],
                        'saved_at': current_data.get('last_updated'),
                        'source': current_data.get('source', 'unknown')
                    })
                
                # Keep only last 10 history entries
                history = history[-10:]
                
                memory_value = {
                    'current': memory_data['description'],
                    'room_type': memory_data['room_type'],
                    'maintenance_notes': memory_data.get('maintenance_notes'),
                    'source': memory_data.get('source', 'user_edited'),
                    'history': history,
                    'last_updated': datetime.utcnow().isoformat()
                }
                
                # Update existing record
                result = self.db.client.table('unified_conversation_memory').update({
                    'memory_value': memory_value,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('tenant_id', user_id).eq('memory_key', memory_key).execute()
                
            else:
                # Create new entry
                memory_value = {
                    'current': memory_data['description'],
                    'room_type': memory_data['room_type'],
                    'maintenance_notes': memory_data.get('maintenance_notes'),
                    'source': memory_data.get('source', 'user_edited'),
                    'history': [],
                    'last_updated': datetime.utcnow().isoformat()
                }
                
                result = self.db.client.table('unified_conversation_memory').insert({
                    'id': str(uuid.uuid4()),
                    'tenant_id': user_id,
                    'memory_key': memory_key,
                    'memory_value': memory_value,
                    'memory_type': 'room_description',
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }).execute()
            
            logger.info(f"Room description memory saved for user {user_id}, key {memory_key}")
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error saving room description memory: {e}")
            return False
    
    async def get_room_memory(
        self,
        user_id: str,
        memory_key: str
    ) -> Dict[str, Any]:
        """Get room description memory including history"""
        if not self.db:
            return {}
        
        try:
            result = self.db.client.table('unified_conversation_memory').select('*').eq(
                'tenant_id', user_id
            ).eq('memory_key', memory_key).execute()
            
            if result.data:
                return result.data[0].get('memory_value', {})
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting room memory: {e}")
            return {}
    
    async def get_room_conversation_references(
        self,
        user_id: str,
        room_id: str
    ) -> List[Dict[str, Any]]:
        """Get all conversation references that mention this room"""
        if not self.db:
            return []
        
        try:
            # Search for room mentions in conversation messages
            result = self.db.client.table('unified_conversation_messages').select('*').eq(
                'sender', user_id
            ).ilike('content', f'%{room_id}%').order('created_at', desc=True).limit(10).execute()
            
            references = []
            for msg in result.data or []:
                references.append({
                    'conversation_id': msg.get('conversation_id'),
                    'message': msg.get('content', '')[:200],  # First 200 chars
                    'timestamp': msg.get('created_at')
                })
            
            return references
            
        except Exception as e:
            logger.error(f"Error getting room conversation references: {e}")
            return []
    
    def get_all_room_descriptions(self, user_id: str) -> Dict[str, Any]:
        """Get all room descriptions for a user for context loading"""
        if not self.db:
            return {}
        
        try:
            # Get all room description memories for user
            result = self.db.client.table('unified_conversation_memory').select('*').eq(
                'tenant_id', user_id
            ).eq('memory_type', 'room_description').execute()
            
            room_descriptions = {}
            for entry in result.data or []:
                memory_key = entry.get('memory_key', '')
                if memory_key.startswith('room_description_'):
                    room_id = memory_key.replace('room_description_', '')
                    memory_value = entry.get('memory_value', {})
                    room_descriptions[room_id] = {
                        'description': memory_value.get('current', ''),
                        'room_type': memory_value.get('room_type', ''),
                        'maintenance_notes': memory_value.get('maintenance_notes', ''),
                        'last_updated': memory_value.get('last_updated')
                    }
            
            logger.info(f"Loaded {len(room_descriptions)} room descriptions for user {user_id}")
            return room_descriptions
            
        except Exception as e:
            logger.error(f"Error getting all room descriptions: {e}")
            return {}