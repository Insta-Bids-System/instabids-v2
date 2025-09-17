"""
Unified Conversation API - Single API for all agent conversation operations
Replaces fragmented conversation storage with unified 5-table system

As per UNIFIED_CONVERSATION_MIGRATION_PLAN.md
"""

from datetime import datetime
from typing import Any, List, Optional, Dict
import json
import uuid

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from database import SupabaseDB
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize database
db = SupabaseDB()

# Helper function to ensure valid UUID format
def ensure_uuid(value: Optional[str]) -> str:
    """Convert string to valid UUID, return default UUID if invalid"""
    if not value:
        return "00000000-0000-0000-0000-000000000000"
    
    try:
        # If it's already a valid UUID, return it
        uuid.UUID(value)
        return value
    except ValueError:
        # If not a valid UUID, create a deterministic UUID from the string
        # This ensures the same string always generates the same UUID
        import hashlib
        namespace_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
        return str(uuid.uuid5(namespace_uuid, value))

# Pydantic models for unified conversation system
class CreateConversationRequest(BaseModel):
    user_id: str
    agent_type: str  # "CIA", "COIA", "IRIS", etc.
    title: Optional[str] = None
    context_type: Optional[str] = "general"  # "project", "property", "general"
    context_id: Optional[str] = None
    contractor_lead_id: Optional[str] = None  # Permanent contractor identifier
    metadata: Optional[Dict[str, Any]] = None

class SendMessageRequest(BaseModel):
    conversation_id: str
    sender_type: str  # "user", "agent"
    sender_id: Optional[str] = None  # User ID for users, None for agents
    agent_type: Optional[str] = None  # "CIA", "COIA", etc. for agents
    content: str
    content_type: Optional[str] = "text"
    images: Optional[List[str]] = None  # Base64 encoded images
    metadata: Optional[Dict[str, Any]] = None

class StoreMemoryRequest(BaseModel):
    conversation_id: str
    memory_type: str  # "preference", "fact", "project_detail"
    key: str
    value: Any
    confidence: Optional[float] = 1.0

@router.post("/conversations/create")
async def create_conversation(request: CreateConversationRequest):
    """Create a new unified conversation"""
    try:
        supabase = db.client
        
        conversation_id = str(uuid.uuid4())
        
        # Ensure user_id is valid UUID format
        user_uuid = ensure_uuid(request.user_id)
        
        # Create conversation record matching actual database schema
        # Store contractor_lead_id in metadata for permanent tracking
        metadata = request.metadata or {}
        if request.contractor_lead_id:
            metadata["contractor_lead_id"] = request.contractor_lead_id
            
        conversation_data = {
            "id": conversation_id,
            "tenant_id": "00000000-0000-0000-0000-000000000000",  # Default tenant
            "created_by": user_uuid,
            "conversation_type": "project_setup",  # Default type
            "entity_id": user_uuid,  # Use user_id as entity_id
            "entity_type": "homeowner",  # Default entity type
            "title": request.title or f"{request.agent_type} Conversation",
            "status": "active",
            "metadata": metadata,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("unified_conversations").insert(conversation_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create conversation")
        
        # Create participant record matching actual database schema
        participant_data = {
            "id": str(uuid.uuid4()),
            "tenant_id": "00000000-0000-0000-0000-000000000000",
            "conversation_id": conversation_id,
            "participant_id": user_uuid,
            "participant_type": "user",  # or "agent"
            "role": "primary",
            "joined_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("unified_conversation_participants").insert(participant_data).execute()
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "data": result.data[0]
        }
        
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/message")
async def send_message(request: SendMessageRequest):
    """Add a message to unified conversation"""
    try:
        supabase = db.client
        
        message_id = str(uuid.uuid4())
        
        # Ensure sender_id is valid UUID format if provided
        sender_uuid = ensure_uuid(request.sender_id) if request.sender_id else None
        
        # Create message record matching database schema
        message_data = {
            "id": message_id,
            "conversation_id": request.conversation_id,
            "sender_type": request.sender_type,
            "sender_id": sender_uuid,
            "agent_type": request.agent_type,
            "content": request.content,
            "content_type": request.content_type,
            "metadata": request.metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("unified_messages").insert(message_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to send message")
        
        # Handle images if provided - save to unified_message_attachments
        if request.images:
            for i, image_data in enumerate(request.images):
                attachment_id = str(uuid.uuid4())
                attachment_data = {
                    "id": attachment_id,
                    "message_id": message_id,
                    "attachment_type": "image",
                    "file_data": image_data,  # base64 encoded
                    "metadata": {
                        "source": "user_upload",
                        "original_name": f"image_{i+1}.jpg",
                        "uploaded_at": datetime.utcnow().isoformat()
                    },
                    "created_at": datetime.utcnow().isoformat()
                }
                
                supabase.table("unified_message_attachments").insert(attachment_data).execute()
                logger.info(f"Image attachment saved: {attachment_id}")
        
        # Update conversation updated_at
        supabase.table("unified_conversations").update({
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", request.conversation_id).execute()
        
        return {
            "success": True,
            "message_id": message_id,
            "data": result.data[0]
        }
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/memory")
async def store_memory(request: StoreMemoryRequest):
    """Store memory in unified conversation system"""
    try:
        supabase = db.client
        
        memory_id = str(uuid.uuid4())
        
        # Create memory record matching actual database schema
        memory_data = {
            "id": memory_id,
            "tenant_id": "00000000-0000-0000-0000-000000000000",
            "conversation_id": request.conversation_id,
            "memory_scope": "conversation",  # Default scope
            "memory_type": request.memory_type,
            "memory_key": request.key,
            "memory_value": request.value,
            "importance_score": int(request.confidence * 10) if request.confidence else 10,  # Convert to integer score
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("unified_conversation_memory").insert(memory_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to store memory")
        
        return {
            "success": True,
            "memory_id": memory_id,
            "data": result.data[0]
        }
        
    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/health")
async def health_check():
    """Health check for unified conversation API"""
    return {
        "status": "healthy",
        "system": "unified_conversations",
        "version": "1.1"
    }

@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation with messages and attachments"""
    try:
        supabase = db.client
        
        # Get conversation
        conv_result = supabase.table("unified_conversations").select("*").eq("id", conversation_id).execute()
        if not conv_result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation = conv_result.data[0]
        
        # Get messages
        messages_result = supabase.table("unified_messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
        
        # Get attachments for each message
        messages = []
        for msg in messages_result.data:
            attachments_result = supabase.table("unified_message_attachments").select("*").eq("message_id", msg["id"]).execute()
            
            # Transform attachments to include public URLs for images
            attachments = []
            for att in attachments_result.data:
                attachment = {
                    "id": att["id"],
                    "message_id": att["message_id"],
                    "type": "image",  # Assume image type
                    "mime_type": att.get("mime_type", "image/jpeg"),
                    "file_size": att.get("file_size", 0),
                    "storage_path": att.get("storage_path", ""),
                    "created_at": att.get("created_at", ""),
                }
                
                # Generate public URL from storage path
                if att.get("storage_path"):
                    attachment["url"] = f"https://xrhgrthdcaymxuqcgrmj.supabase.co/storage/v1/object/public/project-images/{att['storage_path']}"
                
                attachments.append(attachment)
            
            msg["attachments"] = attachments
            messages.append(msg)
        
        # Get participants
        participants_result = supabase.table("unified_conversation_participants").select("*").eq("conversation_id", conversation_id).execute()
        
        # Get memory
        memory_result = supabase.table("unified_conversation_memory").select("*").eq("conversation_id", conversation_id).execute()
        
        return {
            "success": True,
            "conversation": conversation,
            "messages": messages,
            "participants": participants_result.data,
            "memory": memory_result.data
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/messages-with-attachments")
async def get_messages_with_attachments(conversation_id: str):
    """Get messages with properly formatted attachments for frontend display"""
    try:
        supabase = db.client
        
        # Get messages in chronological order
        messages_result = supabase.table("unified_messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
        
        if not messages_result.data:
            return {
                "success": True,
                "messages": []
            }
        
        # Process each message and attach its attachments
        processed_messages = []
        for msg in messages_result.data:
            # Get attachments for this message
            attachments_result = supabase.table("unified_message_attachments").select("*").eq("message_id", msg["id"]).execute()
            
            # Transform attachments for frontend consumption
            attachments = []
            for att in attachments_result.data:
                attachment = {
                    "id": att["id"],
                    "message_id": att["message_id"],
                    "type": "image",  # Default to image type
                    "name": f"image_{len(attachments) + 1}.jpg",  # Default name
                    "mime_type": att.get("mime_type", "image/jpeg"),
                    "file_size": att.get("file_size", 0),
                    "storage_path": att.get("storage_path", ""),
                    "created_at": att.get("created_at", "")
                }
                
                # Generate public URL from storage path if available
                if att.get("storage_path"):
                    attachment["url"] = f"https://xrhgrthdcaymxuqcgrmj.supabase.co/storage/v1/object/public/project-images/{att['storage_path']}"
                else:
                    attachment["url"] = ""
                
                # Include metadata if available
                if att.get("metadata"):
                    attachment["metadata"] = att["metadata"]
                
                attachments.append(attachment)
            
            # Add attachments to message
            message_with_attachments = {
                "id": msg["id"],
                "conversation_id": msg["conversation_id"],
                "sender_type": msg["sender_type"],
                "sender_id": msg.get("sender_id"),
                "agent_type": msg.get("agent_type"),
                "content": msg["content"],
                "content_type": msg.get("content_type", "text"),
                "metadata": msg.get("metadata", {}),
                "created_at": msg["created_at"],
                "attachments": attachments
            }
            
            processed_messages.append(message_with_attachments)
        
        return {
            "success": True,
            "messages": processed_messages,
            "total_messages": len(processed_messages),
            "total_attachments": sum(len(msg["attachments"]) for msg in processed_messages)
        }
        
    except Exception as e:
        logger.error(f"Error getting messages with attachments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/user/{user_id}")
async def list_user_conversations(user_id: str, limit: int = 50):
    """List conversations for a user"""
    try:
        supabase = db.client
        
        # Ensure user_id is valid UUID format
        user_uuid = ensure_uuid(user_id)
        
        # Get conversations where user is a participant
        result = supabase.table("unified_conversation_participants").select("""
            conversation_id,
            participant_type,
            role,
            joined_at,
            unified_conversations:conversation_id (
                id,
                title,
                conversation_type,
                entity_type,
                status,
                created_at,
                updated_at
            )
        """).eq("participant_id", user_uuid).order("joined_at", desc=True).limit(limit).execute()
        
        return {
            "success": True,
            "conversations": result.data
        }
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/by-contractor/{contractor_lead_id}")
async def get_conversation_by_contractor(contractor_lead_id: str):
    """Get conversation by contractor_lead_id for COIA state restoration"""
    try:
        supabase = db.client
        
        # Query by contractor_lead_id in metadata
        conversations_result = supabase.table("unified_conversations").select(
            "*"
        ).eq("contractor_lead_id", contractor_lead_id).execute()
        
        if not conversations_result.data:
            # Try searching in metadata as fallback
            conversations_result = supabase.table("unified_conversations").select(
                "*"
            ).like("metadata", f'%"{contractor_lead_id}"%').execute()
        
        if not conversations_result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        conversation = conversations_result.data[0]
        conversation_id = conversation["id"]
        
        # Get memories for this conversation
        memory_result = supabase.table("unified_conversation_memory").select("*").eq(
            "conversation_id", conversation_id
        ).execute()
        
        return {
            "success": True,
            "conversation": conversation,
            "memory": memory_result.data or []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation by contractor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class MigrateSessionRequest(BaseModel):
    anonymous_session_id: str
    authenticated_user_id: str

@router.post("/conversations/migrate-session")
async def migrate_anonymous_session(request: MigrateSessionRequest):
    """Migrate anonymous session conversations to authenticated user"""
    try:
        supabase = db.client
        
        # Ensure authenticated_user_id is valid UUID format
        authenticated_user_uuid = ensure_uuid(request.authenticated_user_id)
        
        # Find all conversations with the anonymous session ID
        conversations_result = supabase.table("unified_conversations").select("*").eq(
            "metadata->>session_id", request.anonymous_session_id
        ).execute()
        
        if not conversations_result.data:
            return {
                "success": True,
                "message": "No anonymous conversations found to migrate",
                "migrated_conversations": 0,
                "migrated_messages": 0
            }
        
        migrated_conversations = 0
        migrated_messages = 0
        
        for conversation in conversations_result.data:
            conversation_id = conversation["id"]
            
            # Update conversation to use authenticated user ID
            supabase.table("unified_conversations").update({
                "created_by": authenticated_user_uuid,
                "entity_id": authenticated_user_uuid,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", conversation_id).execute()
            
            # Update all messages in this conversation to use authenticated user ID
            messages_result = supabase.table("unified_messages").select("id").eq(
                "conversation_id", conversation_id
            ).execute()
            
            for message in messages_result.data:
                message_id = message["id"]
                supabase.table("unified_messages").update({
                    "sender_id": authenticated_user_uuid
                }).eq("id", message_id).eq("sender_type", "user").execute()
                migrated_messages += 1
            
            # Update participant record
            supabase.table("unified_conversation_participants").update({
                "participant_id": authenticated_user_uuid
            }).eq("conversation_id", conversation_id).execute()
            
            migrated_conversations += 1
            
        logger.info(f"Migrated {migrated_conversations} conversations and {migrated_messages} messages for user {request.authenticated_user_id}")
        
        return {
            "success": True,
            "message": f"Successfully migrated {migrated_conversations} conversations",
            "migrated_conversations": migrated_conversations,
            "migrated_messages": migrated_messages,
            "user_id": authenticated_user_uuid
        }
        
    except Exception as e:
        logger.error(f"Error migrating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))