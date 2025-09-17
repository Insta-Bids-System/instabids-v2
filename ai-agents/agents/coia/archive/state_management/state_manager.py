"""
State Manager for COIA Agent - Unified Memory System Integration
Provides persistent state management across conversation turns using unified_conversation_memory
"""

import logging
import json
import asyncio
import uuid
import hashlib
from typing import Any, Dict, Optional, List
from datetime import datetime
try:
    import httpx
except ImportError:
    import requests as httpx
    # Fallback for sync operations

# Import centralized backend URL configuration
from config.service_urls import get_backend_url

BACKEND_URL = get_backend_url()

logger = logging.getLogger(__name__)

# Critical fields that must persist between conversation turns
PERSISTENT_STATE_FIELDS = [
    "messages",  # CRITICAL: Must save conversation history!
    "company_name",
    "contractor_profile", 
    "business_info",
    "research_findings",
    "specialties",
    "certifications",
    "years_in_business",
    "extraction_completed",
    "research_completed",
    "intelligence_completed",
    "website_summary",
    "online_presence",
    "service_areas",
    "project_types",
    "budget_range",
    "contact_name",
    "contact_email",
    "contact_phone",
    "business_address",
    "license_number",
    "insurance_info",
    "employee_count",
    "annual_revenue",
    "growth_trajectory",
    "competitive_advantages",
    "target_customer",
    "pricing_strategy",
    "marketing_channels",
    "recent_projects",
    "customer_reviews",
    "social_media_presence",
    "bid_history",
    "submitted_bids"
]

class UnifiedStateManager:
    """
    Manages COIA state persistence using the unified conversation memory system.
    Ensures complete context preservation from first landing page visit through account creation.
    """
    
    def __init__(self):
        # No longer need API base URL or HTTP client
        # We're using direct database access now
        pass
    
    def _contractor_lead_id_to_uuid(self, contractor_lead_id: str) -> str:
        """Convert contractor_lead_id to a deterministic UUID for database storage"""
        # Create deterministic UUID from contractor_lead_id
        namespace_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
        return str(uuid.uuid5(namespace_uuid, contractor_lead_id))
    
    async def save_state(
        self, 
        contractor_lead_id: str,
        state: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> bool:
        """
        Save critical state fields to unified memory system.
        Uses contractor_lead_id as the permanent identifier.
        
        Args:
            contractor_lead_id: Permanent identifier (e.g., "landing-abc123def456")
            state: The complete UnifiedCoIAState dictionary
            conversation_id: Optional conversation ID for linking
            
        Returns:
            bool: Success status
        """
        try:
            # Convert contractor_lead_id to UUID for database
            memory_conversation_id = self._contractor_lead_id_to_uuid(contractor_lead_id)
            logger.info(f"Using UUID {memory_conversation_id} for contractor_lead_id {contractor_lead_id}")
            
            # Ensure we have a conversation record in unified_conversations table
            await self._ensure_conversation_exists(memory_conversation_id, state)
            
            # Prepare batch of memory records
            memory_records = []
            
            for field in PERSISTENT_STATE_FIELDS:
                value = state.get(field)
                if value is not None and value != "" and value != {} and value != []:
                    # Special handling for messages
                    if field == "messages":
                        # Convert LangChain messages to serializable format
                        serialized_messages = []
                        for msg in value:
                            if hasattr(msg, "content"):
                                msg_dict = {
                                    "content": msg.content,
                                    "type": "ai" if (hasattr(msg, "__class__") and "AI" in msg.__class__.__name__) else "human"
                                }
                                serialized_messages.append(msg_dict)
                        value = json.dumps(serialized_messages)
                    # Serialize other complex objects
                    elif isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    
                    memory_records.append({
                        "conversation_id": memory_conversation_id,
                        "memory_type": "coia_state",
                        "key": field,
                        "value": value,
                        "importance_score": 100
                    })
            
            # Save timestamp of last update
            memory_records.append({
                "conversation_id": memory_conversation_id,
                "memory_type": "coia_state",
                "key": "last_state_update",
                "value": datetime.utcnow().isoformat(),
                "importance_score": 50
            })
            
            # Save contractor_lead_id mapping if we have a conversation_id
            if conversation_id and conversation_id != memory_conversation_id:
                memory_records.append({
                    "conversation_id": conversation_id,
                    "memory_type": "contractor_mapping",
                    "key": "contractor_lead_id",
                    "value": contractor_lead_id,
                    "importance_score": 100
                })
            
            # Batch save to unified memory system using direct database access
            saved_count = 0
            try:
                from database import SupabaseDB
                db = SupabaseDB()
                
                for record in memory_records:
                    try:
                        # Direct database insert to unified_conversation_memory table
                        db.client.table("unified_conversation_memory").upsert({
                            "conversation_id": record["conversation_id"],
                            "memory_type": record["memory_type"],
                            "memory_key": record["key"],
                            "memory_value": record["value"],
                            "importance_score": record["importance_score"],
                            "created_at": datetime.utcnow().isoformat(),
                            "updated_at": datetime.utcnow().isoformat()
                        }).execute()
                        saved_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to save memory field {record['key']}: {e}")
            except Exception as e:
                logger.error(f"Failed to initialize database connection: {e}")
            
            logger.info(f"✅ Saved {saved_count}/{len(memory_records)} state fields for contractor {contractor_lead_id}")
            
            # Also save to contractor_leads table if we have company info
            if state.get("company_name"):
                await self._save_to_contractor_leads(contractor_lead_id, state)
            
            return saved_count > 0
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False
    
    async def restore_state(
        self,
        contractor_lead_id: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Restore saved state from unified memory system.
        
        Args:
            contractor_lead_id: Permanent identifier
            conversation_id: Optional conversation ID
            
        Returns:
            Dict containing restored state fields
        """
        try:
            restored_state = {}
            
            # Convert contractor_lead_id to UUID for database lookup
            memory_conversation_id = self._contractor_lead_id_to_uuid(contractor_lead_id)
            logger.info(f"Restoring state for UUID {memory_conversation_id} (contractor_lead_id: {contractor_lead_id})")
            
            # If we have a conversation_id, check for contractor mapping
            if conversation_id and conversation_id != contractor_lead_id:
                try:
                    from database import SupabaseDB
                    db = SupabaseDB()
                    
                    # Check if this conversation has a contractor_lead_id mapping
                    result = db.client.table("unified_conversation_memory").select("*").eq(
                        "conversation_id", conversation_id
                    ).eq("memory_key", "contractor_lead_id").execute()
                    
                    if result.data and len(result.data) > 0:
                        memory_conversation_id = result.data[0].get("memory_value")
                except Exception as e:
                    logger.warning(f"Failed to check contractor mapping: {e}")
            
            # Restore from unified_conversation_memory table
            try:
                from database import SupabaseDB
                db = SupabaseDB()
                
                # Get all memory records for this conversation
                result = db.client.table("unified_conversation_memory").select("*").eq(
                    "conversation_id", memory_conversation_id
                ).eq("memory_type", "coia_state").execute()
                
                if result.data and len(result.data) > 0:
                    for record in result.data:
                        key = record.get("memory_key")
                        value = record.get("memory_value")
                        
                        # Special handling for messages
                        if key == "messages" and value:
                            try:
                                # Deserialize messages and convert back to LangChain format
                                from langchain_core.messages import HumanMessage, AIMessage
                                serialized_messages = json.loads(value) if isinstance(value, str) else value
                                messages = []
                                for msg_dict in serialized_messages:
                                    if msg_dict.get("type") == "ai":
                                        messages.append(AIMessage(content=msg_dict.get("content", "")))
                                    else:
                                        messages.append(HumanMessage(content=msg_dict.get("content", "")))
                                restored_state[key] = messages
                            except Exception as e:
                                logger.warning(f"Failed to deserialize messages: {e}")
                        # Deserialize other JSON strings back to objects
                        elif isinstance(value, str) and value.startswith(("{", "[")):
                            try:
                                restored_state[key] = json.loads(value)
                            except json.JSONDecodeError:
                                restored_state[key] = value
                        else:
                            restored_state[key] = value
                    
                    logger.info(f"✅ Restored {len(restored_state)} state fields for contractor {contractor_lead_id}")
                    if "messages" in restored_state:
                        logger.info(f"   Restored {len(restored_state['messages'])} messages")
                    logger.info(f"   Company: {restored_state.get('company_name')}")
                    return restored_state
                else:
                    logger.info(f"No saved state found for {memory_conversation_id}")
                    return {}
                    
            except Exception as e:
                logger.error(f"Failed to restore from database: {e}")
                return {}
            
            if response.status_code == 200:
                data = response.json()
                memories = data.get("memory", [])
                
                for memory in memories:
                    if memory.get("memory_type") == "coia_state":
                        key = memory.get("memory_key")
                        value = memory.get("memory_value")
                        
                        # Deserialize JSON strings back to objects
                        if isinstance(value, str) and value.startswith(("{", "[")):
                            try:
                                value = json.loads(value)
                            except json.JSONDecodeError:
                                pass
                        
                        restored_state[key] = value
                
                if restored_state:
                    logger.info(f"✅ Restored {len(restored_state)} state fields for contractor {contractor_lead_id}")
                    logger.info(f"   Including: company_name={restored_state.get('company_name')}, "
                              f"extraction_completed={restored_state.get('extraction_completed')}")
            
            return restored_state
            
        except Exception as e:
            logger.error(f"Failed to restore state: {e}")
            return {}
    
    async def _save_to_contractor_leads(self, contractor_lead_id: str, state: Dict[str, Any]):
        """
        Also save contractor information to contractor_leads table for ecosystem integration.
        """
        try:
            from database import SupabaseDB
            db = SupabaseDB()
            
            contractor_data = {
                "id": contractor_lead_id,
                "company_name": state.get("company_name"),
                "contact_name": state.get("contact_name"),
                "phone": state.get("contact_phone"),
                "email": state.get("contact_email"),
                "website": state.get("website_url"),
                "address": state.get("business_address"),
                "business_details": state.get("business_info", {}),
                "years_in_business": state.get("years_in_business"),
                "specialties": state.get("specialties", []),
                "certifications": state.get("certifications", []),
                "license_number": state.get("license_number"),
                "insurance_verified": bool(state.get("insurance_info")),
                "employees": state.get("employee_count"),
                "service_areas": state.get("service_areas", []),
                "lead_score": state.get("lead_score", 0),
                "discovery_source": "landing_page",
                "enrichment_data": {
                    "research_findings": state.get("research_findings"),
                    "online_presence": state.get("online_presence"),
                    "competitive_advantages": state.get("competitive_advantages")
                },
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Remove None values
            contractor_data = {k: v for k, v in contractor_data.items() if v is not None}
            
            # Upsert to contractor_leads
            db.client.table("contractor_leads").upsert(contractor_data).execute()
            logger.info(f"✅ Saved contractor data to contractor_leads table: {contractor_lead_id}")
            
        except Exception as e:
            logger.warning(f"Failed to save to contractor_leads: {e}")
    
    async def create_checkpoint(
        self,
        contractor_lead_id: str,
        state: Dict[str, Any]
    ) -> bool:
        """
        Create a lightweight checkpoint for fast restoration.
        Only saves the most critical fields needed to maintain context.
        """
        try:
            checkpoint = {
                "company_name": state.get("company_name"),
                "current_mode": state.get("current_mode"),
                "extraction_completed": state.get("extraction_completed"),
                "research_completed": state.get("research_completed"),
                "intelligence_completed": state.get("intelligence_completed"),
                "contractor_created": state.get("contractor_created"),
                "checkpoint_timestamp": datetime.utcnow().isoformat()
            }
            
            from database import SupabaseDB
            db = SupabaseDB()
            
            # Direct database save for checkpoint
            db.client.table("unified_conversation_memory").upsert({
                "conversation_id": contractor_lead_id,
                "memory_type": "checkpoint",
                "memory_key": "state_checkpoint",
                "memory_value": json.dumps(checkpoint),
                "confidence": 1.0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            return False
    
    async def restore_checkpoint(self, contractor_lead_id: str) -> Dict[str, Any]:
        """
        Restore lightweight checkpoint for fast context recovery.
        """
        try:
            from database import SupabaseDB
            db = SupabaseDB()
            
            # Direct database query for checkpoint
            result = db.client.table("unified_conversation_memory").select("*").eq(
                "conversation_id", contractor_lead_id
            ).eq("memory_type", "checkpoint").eq("memory_key", "state_checkpoint").execute()
            
            if result.data and len(result.data) > 0:
                checkpoint = result.data[0].get("memory_value")
                if isinstance(checkpoint, str):
                    checkpoint = json.loads(checkpoint)
                return checkpoint
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to restore checkpoint: {e}")
            return {}
    
    async def _ensure_conversation_exists(self, conversation_uuid: str, state: Dict[str, Any]) -> str:
        """
        Ensure a conversation exists in unified_conversations table for memory storage.
        Returns the conversation_id to use for memory operations.
        """
        try:
            from database import SupabaseDB
            db = SupabaseDB()
            
            # Check if conversation already exists
            existing = db.client.table("unified_conversations").select("id").eq("id", conversation_uuid).execute()
            
            if existing.data and len(existing.data) > 0:
                logger.info(f"Conversation {conversation_uuid} already exists")
                return conversation_uuid
            
            # Create new conversation record
            conversation_data = {
                "id": conversation_uuid,
                "conversation_type": "COIA_LANDING",
                "entity_type": "contractor_lead", 
                "title": f"COIA Landing: {state.get('company_name', 'Anonymous')}",
                "status": "active",
                "contractor_lead_id": state.get('contractor_lead_id', ''),
                "metadata": {
                    "contractor_lead_id": state.get('contractor_lead_id', ''),
                    "journey_stage": "landing_page",
                    "interface": state.get("interface", "landing_page"),
                    "company_name": state.get("company_name"),
                    "research_completed": state.get("research_completed", False)
                },
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "last_message_at": datetime.utcnow().isoformat()
            }
            
            # Insert the conversation
            result = db.client.table("unified_conversations").insert(conversation_data).execute()
            logger.info(f"✅ Created conversation UUID: {conversation_uuid}")
            return conversation_uuid
                
        except Exception as e:
            logger.warning(f"Error ensuring conversation exists: {e}")
            # Still return the UUID even if creation failed - memory will work
            return conversation_uuid

    async def close(self):
        """No longer needed - using direct database access."""
        pass


# Singleton instance for use across the application
_state_manager: Optional[UnifiedStateManager] = None

async def get_state_manager() -> UnifiedStateManager:
    """Get or create the singleton state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = UnifiedStateManager()
    return _state_manager