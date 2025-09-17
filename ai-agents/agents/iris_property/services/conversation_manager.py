"""
IRIS Conversation Manager
Maintains conversation state across messages using unified memory system
"""

import logging
from typing import Dict, Any, Optional
import json
from datetime import datetime
import uuid

# Use the unified memory system like CIA agent
from database_simple import db

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages conversation state and context using persistent database storage"""
    
    def __init__(self):
        # Use unified database system instead of in-memory storage
        self.db = db
        self._verify_database_connection()
    
    def _verify_database_connection(self):
        """Verify database connection works - fail loudly if not"""
        try:
            if not (hasattr(self.db, 'client') and self.db.client):
                raise Exception("Database client not properly initialized")
                
            # Test with a simple query to verify connection works
            test_result = self.db.client.table('unified_conversations').select('id').limit(1).execute()
            logger.info("IRIS ConversationManager database connection verified")
            
        except Exception as e:
            error_msg = f"CRITICAL: IRIS ConversationManager cannot function without database. Error: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def get_conversation_state(self, session_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get current conversation state from unified memory system - user-based threading"""
        try:
            # Use the same unified memory system as CIA agent
            from database import SupabaseDB
            unified_db = SupabaseDB()
            
            # If user_id provided, create persistent user-based thread
            if user_id:
                # Get or create persistent thread for user
                thread_id = await self._get_or_create_user_thread(user_id, session_id)
            else:
                # Fallback to session-based for backward compatibility
                thread_id = session_id
            
            # Load conversation state using the same method as CIA
            conversation_state = await unified_db.load_conversation_state(
                thread_id=thread_id
            )
            
            if conversation_state and 'state' in conversation_state and 'messages' in conversation_state['state']:
                # Convert CIA message format to IRIS format
                messages = conversation_state['state']['messages']
                history = []
                current_exchange = {}
                
                for msg in messages:
                    if msg.get('role') == 'user':
                        if current_exchange.get('response'):
                            history.append(current_exchange)
                        current_exchange = {
                            'message': msg.get('content', ''),
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    elif msg.get('role') == 'assistant':
                        current_exchange['response'] = msg.get('content', '')
                
                # Add final exchange if complete
                if current_exchange.get('response'):
                    history.append(current_exchange)
                
                state = {
                    'state': 'active',
                    'context': conversation_state.get('context', {}),
                    'history': history,
                    'session_id': session_id,
                    'loaded_at': datetime.utcnow().isoformat()
                }
                logger.info(f"Loaded {len(history)} conversation exchanges from unified memory for session {session_id}")
                return state
            else:
                # Return default state if no existing conversation found
                default_state = {
                    'state': 'initial',
                    'context': {},
                    'history': [],
                    'session_id': session_id,
                    'created_at': datetime.utcnow().isoformat()
                }
                logger.info(f"Created new conversation state for session {session_id}")
                return default_state
                
        except Exception as e:
            logger.error(f"Error getting conversation state for session {session_id}: {e}")
            # Return default state on error to prevent system failure
            return {
                'state': 'initial',
                'context': {},
                'history': [],
                'session_id': session_id,
                'error': str(e)
            }
    
    async def update_conversation_state(
        self,
        session_id: str,
        state: Optional[str] = None,
        context_update: Optional[Dict[str, Any]] = None
    ):
        """Update conversation state in database"""
        try:
            # Get current state
            current_state = await self.get_conversation_state(session_id)
            
            # Update state if provided
            if state:
                current_state['state'] = state
                logger.info(f"Updated conversation state to '{state}' for session {session_id}")
            
            # Update context if provided
            if context_update:
                if 'context' not in current_state:
                    current_state['context'] = {}
                current_state['context'].update(context_update)
                logger.info(f"Updated context for session {session_id}: {list(context_update.keys())}")
            
            # Add timestamp
            current_state['updated_at'] = datetime.utcnow().isoformat()
            
            # Save to database using unified memory system
            # Note: save_conversation_state expects user_id, thread_id, agent_type, state
            # For now, use session_id as both user_id and thread_id, and 'iris' as agent_type
            await self.db.save_conversation_state(
                user_id=session_id,  # Will need to pass real user_id later
                thread_id=session_id,
                agent_type='iris',
                state=current_state
            )
            logger.info(f"Saved conversation state to database for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error updating conversation state for session {session_id}: {e}")
            raise
    
    async def _get_or_create_user_thread(self, user_id: str, session_id: str) -> str:
        """Get or create a persistent thread ID for the user"""
        try:
            # Check if user has an existing IRIS thread
            result = self.db.client.table('unified_conversations').select(
                'id'
            ).eq('created_by', user_id).in_(
                'conversation_type', ['iris_property', 'iris_property_consultation']
            ).eq('status', 'active').order(
                'updated_at.desc'
            ).limit(1).execute()
            
            if result.data and len(result.data) > 0:
                # Use existing thread
                thread_id = result.data[0]['id']
                logger.info(f"Found existing IRIS thread {thread_id} for user {user_id}")
                
                # Update last accessed time
                self.db.client.table('unified_conversations').update({
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', thread_id).execute()
                
                return thread_id
            else:
                # Create new persistent thread for user
                import uuid
                thread_id = str(uuid.uuid4())
                
                conversation_data = {
                    'id': thread_id,
                    'tenant_id': '00000000-0000-0000-0000-000000000000',
                    'created_by': user_id,
                    'conversation_type': 'iris_property',
                    'entity_type': 'user',
                    'entity_id': user_id,
                    'title': f'IRIS Property Assistant - User {user_id[:8]}',
                    'status': 'active',
                    'metadata': {
                        'user_id': user_id,
                        'initial_session_id': session_id,
                        'agent_type': 'iris'
                    },
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                self.db.client.table('unified_conversations').insert(
                    conversation_data
                ).execute()
                
                logger.info(f"Created new persistent IRIS thread {thread_id} for user {user_id}")
                return thread_id
                
        except Exception as e:
            logger.error(f"Error managing user thread: {e}")
            # Fallback to session-based thread
            return session_id
    
    async def add_to_history(self, session_id: str, message: str, response: str, user_id: str = None):
        """Add message/response pair to unified memory system - user-based threading"""
        try:
            from database import SupabaseDB
            unified_db = SupabaseDB()
            
            # Use user-based thread if user_id provided
            if user_id:
                thread_id = await self._get_or_create_user_thread(user_id, session_id)
            else:
                thread_id = session_id
            
            # Load existing conversation state from unified memory
            conversation_state = await unified_db.load_conversation_state(
                thread_id=thread_id
            )
            
            # Initialize state structure if needed
            if not conversation_state:
                conversation_state = {'state': {'messages': []}}
            elif 'state' not in conversation_state:
                conversation_state['state'] = {'messages': []}
            elif 'messages' not in conversation_state['state']:
                conversation_state['state']['messages'] = []
            
            # Add new messages to the state in CIA format
            conversation_state['state']['messages'].append({
                'role': 'user',
                'content': message
            })
            
            conversation_state['state']['messages'].append({
                'role': 'assistant',
                'content': response
            })
            
            # Save back to unified memory system
            await unified_db.save_conversation_state(
                user_id=user_id if user_id else session_id,  # Use actual user_id if available
                thread_id=thread_id,  # Use the persistent thread_id
                agent_type='iris',
                state=conversation_state['state']
            )
            
            logger.info(f"Saved message/response pair to unified memory for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error adding to unified memory for session {session_id}: {e}")
    
    async def clear_conversation(self, session_id: str):
        """Clear conversation state from database"""
        try:
            # Set state back to initial with empty context and history
            await self.update_conversation_state(
                session_id,
                state='initial',
                context_update={'history': [], 'context': {}}
            )
            logger.info(f"Cleared conversation state for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error clearing conversation for session {session_id}: {e}")
    
    async def get_context_value(self, session_id: str, key: str, default=None):
        """Get a specific context value from database"""
        try:
            state = await self.get_conversation_state(session_id)
            return state.get('context', {}).get(key, default)
        except Exception as e:
            logger.error(f"Error getting context value '{key}' for session {session_id}: {e}")
            return default