"""
BSA DeepAgents Memory Integration
Integrates the DeepAgents state system with the unified conversation memory system
"""

import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from deepagents.state import DeepAgentState

logger = logging.getLogger(__name__)

# Critical BSA-specific fields for memory persistence
BSA_MEMORY_FIELDS = [
    "contractor_id",
    "session_id", 
    "messages",
    "todos",
    "files",
    "bid_card_analysis",
    "market_research",
    "group_bidding_analysis",
    "sub_agent_calls",
    "contractor_profile",
    "current_bid_cards",
    "submission_history",
    "pricing_models",
    "trade_specialization",
    "conversation_context"
]

class BSAMemoryIntegrator:
    """
    Integrates BSA DeepAgents state with the unified memory system.
    Ensures persistent memory across contractor sessions while preserving
    all sub-agent analysis and conversation context.
    """
    
    def __init__(self):
        self.supabase = None
    
    async def _get_supabase(self):
        """Get the Supabase client instance."""
        if self.supabase is None:
            try:
                from database_simple import get_client
                self.supabase = get_client()
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                raise
        return self.supabase
    
    def _contractor_id_to_uuid(self, contractor_id: str) -> str:
        """
        Convert contractor_id to deterministic UUID for conversation_id.
        This ensures consistent conversation IDs across sessions.
        """
        # Create deterministic UUID based on contractor_id
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # Standard namespace
        return str(uuid.uuid5(namespace, f"bsa-{contractor_id}"))
    
    async def _ensure_conversation_exists(self, supabase, conversation_id: str, contractor_id: str):
        """
        Ensure that a conversation record exists in unified_conversations table.
        This is required due to foreign key constraint.
        """
        try:
            # Check if conversation already exists
            existing = supabase.table('unified_conversations').select('id').eq(
                'id', conversation_id
            ).execute()
            
            if not existing.data:
                # Create conversation record
                conversation_record = {
                    'id': conversation_id,
                    'conversation_type': 'bsa_contractor',
                    'entity_type': 'contractor',
                    'title': f'BSA Session - {contractor_id}',
                    'status': 'active',
                    'contractor_lead_id': contractor_id,
                    'metadata': {'agent_type': 'BSA', 'contractor_id': contractor_id},
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat(),
                    'last_message_at': datetime.utcnow().isoformat()
                }
                
                result = supabase.table('unified_conversations').insert(conversation_record).execute()
                if result.data:
                    logger.info(f"✅ Created conversation record for BSA contractor {contractor_id}")
                else:
                    logger.warning(f"Failed to create conversation record for contractor {contractor_id}")
                    
        except Exception as e:
            logger.error(f"Error ensuring conversation exists: {e}")
    
    def _contractor_id_to_memory_key(self, contractor_id: str, session_id: Optional[str] = None) -> str:
        """
        Create a consistent memory key for contractor state persistence.
        Uses contractor_id as the primary key for cross-session memory.
        """
        if session_id:
            return f"bsa-{contractor_id}-{session_id}"
        return f"bsa-{contractor_id}"
    
    async def save_deepagents_state(
        self,
        contractor_id: str,
        state: DeepAgentState,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Save DeepAgents state to unified memory system.
        
        Args:
            contractor_id: Contractor identifier
            state: DeepAgents state object
            session_id: Optional session identifier
            
        Returns:
            bool: Success status
        """
        try:
            supabase = await self._get_supabase()
            conversation_id = self._contractor_id_to_uuid(contractor_id)
            
            # Ensure conversation record exists first
            await self._ensure_conversation_exists(supabase, conversation_id, contractor_id)
            
            # Extract and structure memory data
            memory_data = await self._extract_memory_data(contractor_id, state, session_id)
            
            # Save each memory field to unified_conversation_memory table
            saved_count = 0
            for memory_key, memory_value in memory_data.items():
                try:
                    # Prepare memory record
                    memory_record = {
                        'conversation_id': conversation_id,
                        'memory_key': memory_key,
                        'memory_value': json.dumps(memory_value) if not isinstance(memory_value, str) else memory_value,
                        'memory_type': 'bsa_state',
                        'created_at': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat()
                    }
                    
                    # Check if record exists first
                    existing = supabase.table('unified_conversation_memory').select('id').eq(
                        'conversation_id', conversation_id
                    ).eq('memory_key', memory_key).eq('memory_type', 'bsa_state').execute()
                    
                    if existing.data:
                        # Update existing record
                        result = supabase.table('unified_conversation_memory').update(
                            memory_record
                        ).eq('id', existing.data[0]['id']).execute()
                    else:
                        # Insert new record
                        result = supabase.table('unified_conversation_memory').insert(
                            memory_record
                        ).execute()
                    
                    if result.data:
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"Error saving memory key {memory_key}: {e}")
                    continue
            
            success = saved_count > 0
            if success:
                logger.info(f"✅ BSA DeepAgents state saved for contractor {contractor_id} ({saved_count} fields)")
            else:
                logger.warning(f"❌ Failed to save BSA state for contractor {contractor_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving BSA DeepAgents state: {e}")
            return False
    
    async def restore_deepagents_state(
        self,
        contractor_id: str,
        session_id: Optional[str] = None
    ) -> DeepAgentState:
        """
        Restore DeepAgents state from unified memory system.
        
        Args:
            contractor_id: Contractor identifier
            session_id: Optional session identifier
            
        Returns:
            DeepAgentState: Restored state object
        """
        try:
            supabase = await self._get_supabase()
            conversation_id = self._contractor_id_to_uuid(contractor_id)
            
            # Query all memory records for this conversation
            result = supabase.table('unified_conversation_memory').select('*').eq(
                'conversation_id', conversation_id
            ).eq('memory_type', 'bsa_state').execute()
            
            if not result.data:
                logger.info(f"No saved BSA state found for contractor {contractor_id}")
                return await self._create_fresh_state(contractor_id, session_id)
            
            # Reconstruct state dictionary from memory records
            saved_data = {}
            for memory_record in result.data:
                memory_key = memory_record['memory_key']
                memory_value = memory_record['memory_value']
                
                # Try to parse JSON, fall back to string if not valid JSON
                try:
                    if memory_value.startswith(('{', '[', '"')) or memory_value in ('true', 'false', 'null'):
                        saved_data[memory_key] = json.loads(memory_value)
                    else:
                        saved_data[memory_key] = memory_value
                except (json.JSONDecodeError, AttributeError):
                    saved_data[memory_key] = memory_value
            
            # CRITICAL FIX: Apply token trimming to messages BEFORE reconstruction
            if "messages" in saved_data and isinstance(saved_data["messages"], list):
                original_count = len(saved_data["messages"])
                # Trim messages to prevent token overflow (150k limit leaves room for system prompts)
                saved_data["messages"] = self._trim_messages_for_token_limit(
                    saved_data["messages"], 
                    max_tokens=150000
                )
                trimmed_count = len(saved_data["messages"])
                
                if trimmed_count < original_count:
                    logger.warning(f"BSA: Trimmed restored messages from {original_count} to {trimmed_count} to prevent token overflow")
            
            # Convert back to DeepAgents state format
            restored_state = await self._reconstruct_deepagents_state(saved_data)
            logger.info(f"✅ BSA DeepAgents state restored for contractor {contractor_id}")
            logger.info(f"   Restored: {len(saved_data)} memory fields")
            if "messages" in saved_data:
                logger.info(f"   Messages: {len(saved_data.get('messages', []))} (token-limited)")
            return restored_state
                
        except Exception as e:
            logger.error(f"Error restoring BSA DeepAgents state: {e}")
            return await self._create_fresh_state(contractor_id, session_id)
    
    async def _extract_memory_data(
        self,
        contractor_id: str,
        state: DeepAgentState,
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Extract critical data from DeepAgents state for memory persistence.
        """
        memory_data = {
            # Core identification
            "contractor_id": contractor_id,
            "session_id": session_id or str(uuid.uuid4()),
            "agent_type": "BSA_DEEPAGENTS",
            "last_updated": datetime.utcnow().isoformat(),
            
            # DeepAgents built-in state (convert LangChain messages to JSON serializable)
            "messages": await self._serialize_messages(state.get("messages", [])),
            "todos": state.get("todos", []),
            "files": state.get("files", {}),
            
            # BSA-specific analysis data
            "bid_card_analysis": state.get("bid_card_analysis", {}),
            "market_research": state.get("market_research", {}),
            "group_bidding_analysis": state.get("group_bidding_analysis", {}),
            "sub_agent_calls": state.get("sub_agent_calls", []),
            
            # Contractor context
            "contractor_profile": state.get("contractor_profile", {}),
            "current_bid_cards": state.get("current_bid_cards", []),
            "submission_history": state.get("submission_history", []),
            "pricing_models": state.get("pricing_models", {}),
            "trade_specialization": state.get("trade_specialization", "general"),
            
            # Conversation context
            "conversation_context": state.get("conversation_context", {}),
            "session_metadata": {
                "start_time": state.get("session_start_time"),
                "total_interactions": len(state.get("messages", [])),
                "sub_agents_used": len(state.get("sub_agent_calls", []))
            }
        }
        
        return memory_data
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation for message content.
        OpenAI's tokenizer is approximately 4 characters per token.
        """
        return len(text) // 4
    
    def _trim_messages_for_token_limit(self, messages: List, max_tokens: int = 150000) -> List:
        """
        Trim message history to stay under token limit while preserving conversation context.
        
        Args:
            messages: List of message objects or dicts
            max_tokens: Maximum tokens to allow (default 150k, leaving room for system prompts)
            
        Returns:
            Trimmed list of messages that fit within token limit
        """
        if not messages:
            return messages
        
        # Convert and estimate tokens for all messages
        estimated_tokens = []
        total_tokens = 0
        
        for msg in messages:
            content = ""
            if hasattr(msg, 'content'):
                content = str(msg.content)
            elif isinstance(msg, dict):
                content = str(msg.get('content', ''))
            else:
                content = str(msg)
            
            tokens = self._estimate_tokens(content)
            estimated_tokens.append(tokens)
            total_tokens += tokens
        
        # If under limit, return all messages
        if total_tokens <= max_tokens:
            logger.info(f"BSA: All {len(messages)} messages fit in {total_tokens} estimated tokens")
            return messages
        
        # Need to trim - keep most recent messages that fit under limit
        trimmed_messages = []
        current_tokens = 0
        
        # Start from most recent and work backwards
        for i in range(len(messages) - 1, -1, -1):
            msg_tokens = estimated_tokens[i]
            if current_tokens + msg_tokens <= max_tokens:
                trimmed_messages.insert(0, messages[i])  # Insert at beginning to maintain order
                current_tokens += msg_tokens
            else:
                break  # Stop when we can't fit any more
        
        logger.warning(f"BSA: Trimmed {len(messages)} messages to {len(trimmed_messages)} messages "
                      f"(estimated {total_tokens} → {current_tokens} tokens)")
        
        # Always ensure we have at least the last few exchanges
        if len(trimmed_messages) < 4 and len(messages) >= 4:
            trimmed_messages = messages[-4:]  # Keep last 2 exchanges minimum
            logger.info(f"BSA: Ensured minimum context with last 4 messages")
        
        return trimmed_messages

    async def _serialize_messages(self, messages: List) -> List[Dict[str, str]]:
        """
        Convert LangChain message objects to JSON-serializable dictionaries.
        Handles HumanMessage, AIMessage, and other LangChain message types.
        Now includes token-aware trimming to prevent prompt overflow.
        """
        # First, trim messages to prevent token overflow
        trimmed_messages = self._trim_messages_for_token_limit(messages)
        
        serialized_messages = []
        
        for msg in trimmed_messages:
            try:
                # Handle LangChain message objects
                if hasattr(msg, '__class__'):
                    msg_class = msg.__class__.__name__
                    
                    if msg_class in ['HumanMessage', 'AIMessage', 'SystemMessage']:
                        serialized_messages.append({
                            "type": msg_class.replace('Message', '').lower(),
                            "content": getattr(msg, 'content', str(msg)),
                            "role": "user" if msg_class == "HumanMessage" else "assistant" if msg_class == "AIMessage" else "system"
                        })
                    else:
                        # Handle other message types by extracting content
                        content = getattr(msg, 'content', str(msg))
                        role = getattr(msg, 'type', 'user')
                        serialized_messages.append({
                            "type": role,
                            "content": content,
                            "role": role
                        })
                elif isinstance(msg, dict):
                    # Already serialized
                    serialized_messages.append(msg)
                else:
                    # Fallback for unknown types
                    serialized_messages.append({
                        "type": "unknown",
                        "content": str(msg),
                        "role": "user"
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to serialize message {type(msg)}: {e}")
                # Add a safe fallback
                serialized_messages.append({
                    "type": "error",
                    "content": f"Failed to serialize message: {str(e)}",
                    "role": "system"
                })
        
        return serialized_messages
    
    async def _reconstruct_deepagents_state(self, saved_data: Dict[str, Any]) -> DeepAgentState:
        """
        Reconstruct DeepAgents state from saved memory data.
        """
        state: DeepAgentState = {
            # Core DeepAgents state
            "messages": saved_data.get("messages", []),
            "todos": saved_data.get("todos", []),
            "files": saved_data.get("files", {}),
            
            # BSA-specific restored data
            "contractor_id": saved_data.get("contractor_id"),
            "session_id": saved_data.get("session_id"),
            "bid_card_analysis": saved_data.get("bid_card_analysis", {}),
            "market_research": saved_data.get("market_research", {}),
            "group_bidding_analysis": saved_data.get("group_bidding_analysis", {}),
            "sub_agent_calls": saved_data.get("sub_agent_calls", []),
            "contractor_profile": saved_data.get("contractor_profile", {}),
            "current_bid_cards": saved_data.get("current_bid_cards", []),
            "submission_history": saved_data.get("submission_history", []),
            "pricing_models": saved_data.get("pricing_models", {}),
            "trade_specialization": saved_data.get("trade_specialization", "general"),
            "conversation_context": saved_data.get("conversation_context", {}),
            
            # Session restoration metadata
            "session_restored": True,
            "session_restore_time": datetime.utcnow().isoformat(),
            "restored_from_memory": True
        }
        
        return state
    
    async def _create_fresh_state(
        self,
        contractor_id: str,
        session_id: Optional[str]
    ) -> DeepAgentState:
        """
        Create a fresh DeepAgents state for new contractor sessions.
        """
        state: DeepAgentState = {
            "messages": [],
            "todos": [],
            "files": {},
            "contractor_id": contractor_id,
            "session_id": session_id or str(uuid.uuid4()),
            "bid_card_analysis": {},
            "market_research": {},
            "group_bidding_analysis": {},
            "sub_agent_calls": [],
            "contractor_profile": {},
            "current_bid_cards": [],
            "submission_history": [],
            "pricing_models": {},
            "trade_specialization": "general",
            "conversation_context": {},
            "session_start_time": datetime.utcnow().isoformat(),
            "session_restored": False,
            "fresh_session": True
        }
        
        return state
    
    async def save_sub_agent_analysis(
        self,
        contractor_id: str,
        sub_agent_name: str,
        analysis_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> bool:
        """
        Save specific sub-agent analysis to memory for future reference.
        This enables sub-agents to build on previous work across sessions.
        """
        try:
            supabase = await self._get_supabase()
            conversation_id = self._contractor_id_to_uuid(contractor_id)
            memory_key = f"sub_agent_{sub_agent_name}"
            
            analysis_record = {
                "sub_agent": sub_agent_name,
                "contractor_id": contractor_id,
                "session_id": session_id,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "analysis_data": analysis_data
            }
            
            # Save to unified_conversation_memory table
            memory_record = {
                'conversation_id': conversation_id,
                'memory_key': memory_key,
                'memory_value': json.dumps(analysis_record),
                'memory_type': 'bsa_sub_agent',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Check if record exists first
            existing = supabase.table('unified_conversation_memory').select('id').eq(
                'conversation_id', conversation_id
            ).eq('memory_key', memory_key).eq('memory_type', 'bsa_sub_agent').execute()
            
            if existing.data:
                # Update existing record
                result = supabase.table('unified_conversation_memory').update(
                    memory_record
                ).eq('id', existing.data[0]['id']).execute()
            else:
                # Insert new record
                result = supabase.table('unified_conversation_memory').insert(
                    memory_record
                ).execute()
            
            success = bool(result.data)
            if success:
                logger.info(f"✅ Saved {sub_agent_name} analysis for contractor {contractor_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving sub-agent analysis: {e}")
            return False
    
    async def restore_sub_agent_analysis(
        self,
        contractor_id: str,
        sub_agent_name: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Restore previous sub-agent analysis for building on past work.
        """
        try:
            supabase = await self._get_supabase()
            conversation_id = self._contractor_id_to_uuid(contractor_id)
            memory_key = f"sub_agent_{sub_agent_name}"
            
            # Query for specific sub-agent analysis
            result = supabase.table('unified_conversation_memory').select('*').eq(
                'conversation_id', conversation_id
            ).eq('memory_key', memory_key).eq('memory_type', 'bsa_sub_agent').execute()
            
            if result.data:
                memory_record = result.data[0]
                saved_analysis = json.loads(memory_record['memory_value'])
                
                if "analysis_data" in saved_analysis:
                    logger.info(f"✅ Restored {sub_agent_name} analysis for contractor {contractor_id}")
                    return saved_analysis["analysis_data"]
            
            logger.info(f"No previous {sub_agent_name} analysis found for contractor {contractor_id}")
            return {}
                
        except Exception as e:
            logger.error(f"Error restoring sub-agent analysis: {e}")
            return {}

# Singleton instance for BSA memory integration
_memory_integrator: Optional[BSAMemoryIntegrator] = None

async def get_bsa_memory_integrator() -> BSAMemoryIntegrator:
    """Get or create the singleton BSA memory integrator instance."""
    global _memory_integrator
    if _memory_integrator is None:
        _memory_integrator = BSAMemoryIntegrator()
    return _memory_integrator

# Convenience functions for BSA DeepAgents router integration
async def save_bsa_state(
    contractor_id: str,
    state: DeepAgentState,
    session_id: Optional[str] = None
) -> bool:
    """Convenience function to save BSA state."""
    integrator = await get_bsa_memory_integrator()
    return await integrator.save_deepagents_state(contractor_id, state, session_id)

async def restore_bsa_state(
    contractor_id: str,
    session_id: Optional[str] = None
) -> DeepAgentState:
    """Convenience function to restore BSA state."""
    integrator = await get_bsa_memory_integrator()
    return await integrator.restore_deepagents_state(contractor_id, session_id)

async def save_sub_agent_work(
    contractor_id: str,
    sub_agent_name: str,
    analysis_data: Dict[str, Any],
    session_id: Optional[str] = None
) -> bool:
    """Convenience function to save sub-agent analysis."""
    integrator = await get_bsa_memory_integrator()
    return await integrator.save_sub_agent_analysis(contractor_id, sub_agent_name, analysis_data, session_id)

async def restore_sub_agent_work(
    contractor_id: str,
    sub_agent_name: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function to restore sub-agent analysis."""
    integrator = await get_bsa_memory_integrator()
    return await integrator.restore_sub_agent_analysis(contractor_id, sub_agent_name, session_id)