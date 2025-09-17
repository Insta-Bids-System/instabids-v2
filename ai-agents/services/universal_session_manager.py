"""
Universal Session Manager for ALL Agents
Ensures persistent memory across all agent conversations
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp
from config.service_urls import get_backend_url

logger = logging.getLogger(__name__)


class UniversalSessionManager:
    """
    Universal session manager that ALL agents should use
    Provides consistent memory persistence across all agents
    """
    
    def __init__(self, api_base: str = f"{get_backend_url()}/api"):
        self.api_base = api_base
        self.sessions_cache = {}  # In-memory cache for performance
        
    async def get_or_create_session(
        self,
        session_id: str,
        user_id: str,
        agent_type: str,
        create_if_missing: bool = True
    ) -> Dict[str, Any]:
        """
        Get existing session or create new one
        THIS IS THE KEY METHOD ALL AGENTS MUST USE
        """
        try:
            # Check cache first
            if session_id in self.sessions_cache:
                logger.info(f"[SessionManager] Found session in cache: {session_id}")
                return self.sessions_cache[session_id]
            
            # Try to load from unified conversation system
            session_state = await self._load_from_unified_system(session_id, user_id, agent_type)
            
            if session_state:
                logger.info(f"[SessionManager] Loaded existing session: {session_id}")
                self.sessions_cache[session_id] = session_state
                return session_state
            
            if create_if_missing:
                # Create new session
                logger.info(f"[SessionManager] Creating new session: {session_id}")
                new_session = self._create_new_session(session_id, user_id, agent_type)
                await self._save_to_unified_system(new_session)
                self.sessions_cache[session_id] = new_session
                return new_session
            
            return None
            
        except Exception as e:
            logger.error(f"[SessionManager] Error getting session: {e}")
            # Return basic session on error
            return self._create_new_session(session_id, user_id, agent_type)
    
    async def update_session(
        self,
        session_id: str,
        state: Dict[str, Any],
        save_to_db: bool = True
    ) -> bool:
        """
        Update session state
        ALL AGENTS MUST CALL THIS AFTER EACH TURN
        """
        try:
            # Update timestamp
            state["updated_at"] = datetime.utcnow().isoformat()
            
            # Update cache
            self.sessions_cache[session_id] = state
            
            # Save to database
            if save_to_db:
                await self._save_to_unified_system(state)
            
            logger.info(f"[SessionManager] Updated session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"[SessionManager] Error updating session: {e}")
            return False
    
    async def add_message_to_session(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Add a message to the session
        CONVENIENCE METHOD FOR AGENTS
        """
        state = self.sessions_cache.get(session_id)
        if not state:
            logger.error(f"[SessionManager] Session not found: {session_id}")
            return None
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            message["metadata"] = metadata
        
        state["messages"].append(message)
        state["message_count"] = len(state["messages"])
        
        await self.update_session(session_id, state)
        return state
    
    def _create_new_session(
        self,
        session_id: str,
        user_id: str,
        agent_type: str
    ) -> Dict[str, Any]:
        """Create a new session structure"""
        return {
            "session_id": session_id,
            "user_id": user_id,
            "agent_type": agent_type,
            "messages": [],
            "context": {},
            "metadata": {},
            "message_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    async def _load_from_unified_system(
        self,
        session_id: str,
        user_id: str,
        agent_type: str
    ) -> Optional[Dict[str, Any]]:
        """Load session from unified conversation system"""
        try:
            async with aiohttp.ClientSession() as session:
                # First, try to find conversation by session_id
                async with session.get(
                    f"{self.api_base}/conversations/user/{user_id}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        conversations = data.get("conversations", [])
                        
                        # Find conversation with matching session_id
                        for conv in conversations:
                            if conv.get("metadata", {}).get("session_id") == session_id:
                                # Load messages for this conversation
                                conv_id = conv.get("id")
                                async with session.get(
                                    f"{self.api_base}/conversations/{conv_id}/messages"
                                ) as msg_response:
                                    if msg_response.status == 200:
                                        msg_data = await msg_response.json()
                                        
                                        # Build session state
                                        state = {
                                            "session_id": session_id,
                                            "user_id": user_id,
                                            "agent_type": agent_type,
                                            "conversation_id": conv_id,
                                            "messages": msg_data.get("messages", []),
                                            "context": conv.get("metadata", {}),
                                            "metadata": conv.get("metadata", {}),
                                            "message_count": len(msg_data.get("messages", [])),
                                            "created_at": conv.get("created_at"),
                                            "updated_at": conv.get("updated_at")
                                        }
                                        return state
            
            return None
            
        except Exception as e:
            logger.error(f"[SessionManager] Error loading from unified system: {e}")
            return None
    
    async def _save_to_unified_system(self, state: Dict[str, Any]) -> bool:
        """Save session to unified conversation system"""
        try:
            async with aiohttp.ClientSession() as session:
                # Check if conversation exists
                if "conversation_id" not in state:
                    # Create new conversation
                    async with session.post(
                        f"{self.api_base}/conversations/create",
                        json={
                            "user_id": state["user_id"],
                            "agent_type": state["agent_type"],
                            "title": f"{state['agent_type']} Session - {state['session_id']}",
                            "metadata": {
                                "session_id": state["session_id"],
                                **state.get("metadata", {})
                            }
                        }
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            state["conversation_id"] = data.get("conversation_id")
                
                # Save messages
                if state.get("conversation_id") and state.get("messages"):
                    last_message = state["messages"][-1]
                    async with session.post(
                        f"{self.api_base}/conversations/message",
                        json={
                            "conversation_id": state["conversation_id"],
                            "sender_type": last_message["role"],
                            "sender_id": state["user_id"],
                            "content": last_message["content"],
                            "metadata": last_message.get("metadata", {})
                        }
                    ) as response:
                        if response.status == 200:
                            logger.info(f"[SessionManager] Saved message to unified system")
                
                return True
                
        except Exception as e:
            logger.error(f"[SessionManager] Error saving to unified system: {e}")
            return False


# Global instance for all agents to use
universal_session_manager = UniversalSessionManager()