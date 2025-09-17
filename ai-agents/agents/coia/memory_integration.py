"""
COIA DeepAgents Memory Integration
Integrates the DeepAgents state system with the unified conversation memory system
"""

import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Critical COIA-specific fields for memory persistence
COIA_MEMORY_FIELDS = [
    "contractor_lead_id",
    "session_id", 
    "messages",
    "todos",
    "files",
    "company_name",
    "staging_id",  # CRITICAL: ID for accessing staged profile in potential_contractors
    "research_findings",
    "contractor_profile",
    "google_business_data",
    "staging_data",
    "onboarding_progress",
    "services_preferences",
    "radius_preferences",
    "projects_found",
    "account_creation_status",
    "conversation_context"
]

class COIAMemoryIntegrator:
    """
    Integrates COIA DeepAgents state with the unified memory system.
    Ensures persistent memory across contractor sessions while preserving
    all sub-agent analysis and conversation context.
    """
    
    def __init__(self):
        self.supabase = None
    
    async def _get_supabase(self):
        """Get the Supabase client instance."""
        if self.supabase is None:
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from database_simple import get_client
                self.supabase = get_client()
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                raise
        return self.supabase
    
    def _contractor_lead_id_to_uuid(self, contractor_lead_id: str) -> str:
        """
        Convert contractor_lead_id to deterministic UUID for conversation_id.
        This ensures consistent conversation IDs across sessions.
        """
        # Create deterministic UUID based on contractor_lead_id
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # Standard namespace
        return str(uuid.uuid5(namespace, f"coia-{contractor_lead_id}"))
    
    async def save_deepagents_state(
        self,
        contractor_lead_id: str,
        state: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> bool:
        """
        Save DeepAgents state to unified memory system.
        
        Args:
            contractor_lead_id: Contractor lead identifier
            state: DeepAgents state dictionary
            session_id: Optional session identifier
            
        Returns:
            bool: Success status
        """
        try:
            supabase = await self._get_supabase()
            conversation_id = self._contractor_lead_id_to_uuid(contractor_lead_id)
            
            # CRITICAL FIX: Create conversation record if it doesn't exist
            await self._ensure_conversation_exists(supabase, conversation_id, contractor_lead_id, session_id)
            
            # Extract and structure memory data
            memory_data = await self._extract_memory_data(contractor_lead_id, state, session_id)
            
            # Save each memory field to unified_conversation_memory table
            saved_count = 0
            for memory_key, memory_value in memory_data.items():
                try:
                    # Prepare memory record
                    memory_value_str = json.dumps(memory_value) if not isinstance(memory_value, str) else memory_value
                    
                    # Check if record exists
                    existing = supabase.table('unified_conversation_memory').select('id').eq(
                        'conversation_id', conversation_id
                    ).eq('memory_key', memory_key).execute()
                    
                    if existing.data:
                        # Update existing record
                        result = supabase.table('unified_conversation_memory').update({
                            'memory_value': memory_value_str,
                            'updated_at': datetime.utcnow().isoformat()
                        }).eq('conversation_id', conversation_id).eq('memory_key', memory_key).execute()
                    else:
                        # Insert new record
                        memory_record = {
                            'conversation_id': conversation_id,
                            'memory_key': memory_key,
                            'memory_value': memory_value_str,
                            'memory_type': 'coia_state',
                            'created_at': datetime.utcnow().isoformat(),
                            'updated_at': datetime.utcnow().isoformat()
                        }
                        result = supabase.table('unified_conversation_memory').insert(memory_record).execute()
                    
                    if result.data:
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"Error saving memory key {memory_key}: {e}")
                    continue
            
            success = saved_count > 0
            if success:
                logger.info(f"✅ COIA DeepAgents state saved for contractor {contractor_lead_id} ({saved_count} fields)")
            else:
                logger.warning(f"❌ Failed to save COIA state for contractor {contractor_lead_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving COIA DeepAgents state: {e}")
            return False
    
    async def restore_deepagents_state(
        self,
        contractor_lead_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Restore DeepAgents state from unified memory system.
        
        Args:
            contractor_lead_id: Contractor lead identifier
            session_id: Optional session identifier
            
        Returns:
            Dict[str, Any]: Restored state dictionary
        """
        try:
            supabase = await self._get_supabase()
            conversation_id = self._contractor_lead_id_to_uuid(contractor_lead_id)
            
            # Query all memory records for this conversation
            result = supabase.table('unified_conversation_memory').select('*').eq(
                'conversation_id', conversation_id
            ).eq('memory_type', 'coia_state').execute()
            
            if not result.data:
                logger.info(f"No saved COIA state found for contractor {contractor_lead_id}")
                return await self._create_fresh_state(contractor_lead_id, session_id)
            
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
            
            # Convert back to DeepAgents state format
            restored_state = await self._reconstruct_deepagents_state(saved_data)
            logger.info(f"✅ COIA DeepAgents state restored for contractor {contractor_lead_id}")
            logger.info(f"   Restored: {len(saved_data)} memory fields")
            if "messages" in saved_data:
                logger.info(f"   Messages: {len(saved_data.get('messages', []))}")
            if "company_name" in saved_data:
                logger.info(f"   Company: {saved_data.get('company_name')}")
            return restored_state
                
        except Exception as e:
            logger.error(f"Error restoring COIA DeepAgents state: {e}")
            return await self._create_fresh_state(contractor_lead_id, session_id)
    
    async def _extract_memory_data(
        self,
        contractor_lead_id: str,
        state: Dict[str, Any],
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Extract critical data from DeepAgents state for memory persistence.
        """
        memory_data = {
            # Core identification
            "contractor_lead_id": contractor_lead_id,
            "session_id": session_id or str(uuid.uuid4()),
            "agent_type": "COIA_DEEPAGENTS",
            "last_updated": datetime.utcnow().isoformat(),
            
            # DeepAgents built-in state - serialize messages properly
            "messages": [msg.dict() if hasattr(msg, 'dict') else str(msg) for msg in state.get("messages", [])],
            "todos": state.get("todos", []),
            "files": state.get("files", {}),
            
            # COIA-specific onboarding data
            "company_name": state.get("company_name"),
            "staging_id": state.get("staging_id"),  # CRITICAL: Preserve staging ID
            "research_findings": state.get("research_findings", {}),
            "contractor_profile": state.get("contractor_profile", {}),
            "google_business_data": state.get("google_business_data", {}),
            "staging_data": state.get("staging_data", {}),
            "onboarding_progress": state.get("onboarding_progress", {}),
            "services_preferences": state.get("services_preferences", []),
            "radius_preferences": state.get("radius_preferences", {}),
            "projects_found": state.get("projects_found", []),
            "account_creation_status": state.get("account_creation_status", "pending"),
            
            # Conversation context
            "conversation_context": state.get("conversation_context", {}),
            "session_metadata": {
                "start_time": state.get("session_start_time"),
                "total_interactions": len(state.get("messages", [])),
                "sub_agents_used": len(state.get("sub_agent_calls", []))
            }
        }
        
        return memory_data
    
    async def _reconstruct_deepagents_state(self, saved_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reconstruct DeepAgents state from saved memory data.
        """
        state = {
            # Core DeepAgents state
            "messages": saved_data.get("messages", []),
            "todos": saved_data.get("todos", []),
            "files": saved_data.get("files", {}),
            
            # COIA-specific restored data
            "contractor_lead_id": saved_data.get("contractor_lead_id"),
            "session_id": saved_data.get("session_id"),
            "company_name": saved_data.get("company_name"),
            "staging_id": saved_data.get("staging_id"),  # CRITICAL: Restore staging ID
            "research_findings": saved_data.get("research_findings", {}),
            "contractor_profile": saved_data.get("contractor_profile", {}),
            "google_business_data": saved_data.get("google_business_data", {}),
            "staging_data": saved_data.get("staging_data", {}),
            "onboarding_progress": saved_data.get("onboarding_progress", {}),
            "services_preferences": saved_data.get("services_preferences", []),
            "radius_preferences": saved_data.get("radius_preferences", {}),
            "projects_found": saved_data.get("projects_found", []),
            "account_creation_status": saved_data.get("account_creation_status", "pending"),
            "conversation_context": saved_data.get("conversation_context", {}),
            
            # Session restoration metadata
            "session_restored": True,
            "session_restore_time": datetime.utcnow().isoformat(),
            "restored_from_memory": True
        }
        
        return state
    
    async def _create_fresh_state(
        self,
        contractor_lead_id: str,
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Create a fresh DeepAgents state for new contractor sessions.
        """
        state = {
            "messages": [],
            "todos": [],
            "files": {},
            "contractor_lead_id": contractor_lead_id,
            "session_id": session_id or str(uuid.uuid4()),
            "company_name": None,
            "staging_id": None,  # Will be populated after stage_profile
            "research_findings": {},
            "contractor_profile": {},
            "google_business_data": {},
            "staging_data": {},
            "onboarding_progress": {},
            "services_preferences": [],
            "radius_preferences": {},
            "projects_found": [],
            "account_creation_status": "pending",
            "conversation_context": {},
            "session_start_time": datetime.utcnow().isoformat(),
            "session_restored": False,
            "fresh_session": True
        }
        
        return state
    
    async def _ensure_conversation_exists(
        self, 
        supabase, 
        conversation_id: str, 
        contractor_lead_id: str, 
        session_id: Optional[str]
    ) -> None:
        """
        Ensure the conversation record exists in unified_conversations table.
        This satisfies the foreign key constraint for unified_conversation_memory.
        """
        try:
            # Check if conversation already exists
            result = supabase.table('unified_conversations').select('id').eq(
                'id', conversation_id
            ).execute()
            
            if result.data and len(result.data) > 0:
                # Conversation already exists
                return
                
            # Create new conversation record with actual schema columns
            conversation_record = {
                'id': conversation_id,
                'tenant_id': str(uuid.UUID('00000000-0000-0000-0000-000000000000')),  # Default tenant
                'created_by': str(uuid.UUID('00000000-0000-0000-0000-000000000001')),  # System user
                'conversation_type': 'COIA_DEEPAGENTS',
                'entity_id': str(uuid.UUID('00000000-0000-0000-0000-000000000002')),  # Default entity
                'entity_type': 'contractor',
                'title': f'COIA Conversation - {contractor_lead_id}',
                'status': 'active',
                'metadata': {
                    'session_id': session_id or str(uuid.uuid4()),
                    'contractor_lead_id': contractor_lead_id
                },
                'contractor_lead_id': contractor_lead_id,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'last_message_at': datetime.utcnow().isoformat()
            }
            
            result = supabase.table('unified_conversations').insert(conversation_record).execute()
            
            if result.data:
                logger.info(f"✅ Created conversation record: {conversation_id}")
            else:
                logger.warning(f"Failed to create conversation record: {conversation_id}")
                
        except Exception as e:
            logger.error(f"Error ensuring conversation exists: {e}")
            # Continue anyway - the memory system should still work

# Singleton instance for COIA memory integration
_memory_integrator: Optional[COIAMemoryIntegrator] = None

async def get_coia_memory_integrator() -> COIAMemoryIntegrator:
    """Get or create the singleton COIA memory integrator instance."""
    global _memory_integrator
    if _memory_integrator is None:
        _memory_integrator = COIAMemoryIntegrator()
    return _memory_integrator

# Convenience functions for COIA DeepAgents router integration
async def save_coia_state(
    contractor_lead_id: str,
    state: Dict[str, Any],
    session_id: Optional[str] = None
) -> bool:
    """Convenience function to save COIA state."""
    integrator = await get_coia_memory_integrator()
    return await integrator.save_deepagents_state(contractor_lead_id, state, session_id)

async def restore_coia_state(
    contractor_lead_id: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function to restore COIA state."""
    integrator = await get_coia_memory_integrator()
    return await integrator.restore_deepagents_state(contractor_lead_id, session_id)