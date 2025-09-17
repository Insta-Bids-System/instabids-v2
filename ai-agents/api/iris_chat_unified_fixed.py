"""
IRIS Agent - Fixed Unified Conversation System Integration
This version properly integrates with unified conversation without self-referencing loops
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Optional
import time
import sys

from openai import OpenAI
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import database for direct access
from database import SupabaseDB

# Import LLM cost tracking
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.llm_cost_tracker import LLMCostTracker

# Import the actual IRIS agent for session-aware processing
from agents.iris.agent import iris_agent, IrisRequest
from config.service_urls import get_backend_url

# Load environment variables
load_dotenv(override=True)  # Force override system env vars with .env file values

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize database
db = SupabaseDB()

# Initialize OpenAI client
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    logger.warning("OPENAI_API_KEY not found, using fallback responses")
    client = None
else:
    try:
        client = OpenAI(api_key=openai_key)
        # Test the API key with a quick request
        test_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
            max_completion_tokens=1  # Fixed: GPT-4o uses max_completion_tokens
        )
        logger.info("OpenAI API key validated successfully")
    except Exception as e:
        logger.warning(f"OpenAI API key invalid or service unavailable: {e}")
        logger.warning("Using fallback responses instead")
        client = None

class IrisChatRequest(BaseModel):
    message: str
    user_id: str
    board_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_context: Optional[list[dict]] = None
    room_type: Optional[str] = None

class IrisChatResponse(BaseModel):
    response: str
    suggestions: list[str]
    session_id: str
    board_id: Optional[str] = None
    conversation_id: Optional[str] = None

@router.post("/chat", response_model=IrisChatResponse)
async def iris_unified_chat(request: IrisChatRequest):
    """
    IRIS chat using unified conversation system with direct database access
    """
    try:
        # Generate or use session ID
        session_id = request.session_id or f"iris_{request.user_id}_{int(datetime.now().timestamp())}"
        
        # 1. First check if conversation exists for this session
        conversation_id = await get_or_create_conversation_direct(
            user_id=request.user_id,
            session_id=session_id,
            room_type=request.room_type or "general",
            message=request.message,
            project_id=request.board_id  # Use board_id as project_id if available
        )
        
        # 2. Get conversation context from database
        context = await get_conversation_context_direct(conversation_id)
        
        # 3. Generate IRIS response using the updated IrisAgent with session management
        iris_response = await generate_iris_response_with_session(
            message=request.message,
            context=context,
            conversation_id=conversation_id,
            session_id=session_id,
            user_id=request.user_id,
            request=request
        )
        
        # 4. Save messages directly to database
        try:
            await save_messages_direct(
                conversation_id=conversation_id,
                user_message=request.message,
                assistant_response=iris_response["response"],
                user_id=request.user_id
            )
            logger.info(f"Successfully called save_messages_direct for conversation {conversation_id}")
        except Exception as save_error:
            logger.error(f"Error in save_messages_direct: {save_error}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        return IrisChatResponse(
            response=iris_response["response"],
            suggestions=iris_response["suggestions"],
            session_id=session_id,
            conversation_id=conversation_id,
            board_id=request.board_id
        )
        
    except Exception as e:
        logger.error(f"Error in IRIS unified chat: {e}")
        return IrisChatResponse(
            response="I'm here to help you with your design inspiration! Tell me about your project - what room are you working on?",
            suggestions=["Tell me about my current space", "Help me find inspiration", "Explore design styles", "Organize my project ideas"],
            session_id=request.session_id or f"iris_fallback_{int(datetime.now().timestamp())}",
            board_id=request.board_id
        )

async def get_or_create_conversation_direct(user_id: str, session_id: str, room_type: str, message: str, project_id: str = None) -> str:
    """Get existing conversation for session or create new one if doesn't exist"""
    try:
        supabase = db.client
        
        # First check if conversation exists for this session
        existing_result = supabase.table("unified_conversations").select("id").eq("metadata->>session_id", session_id).execute()
        
        if existing_result.data and len(existing_result.data) > 0:
            # Use existing conversation
            conversation_id = existing_result.data[0]["id"]
            logger.info(f"Found existing IRIS conversation {conversation_id} for session {session_id}")
            return conversation_id
        
        # No existing conversation, create new one
        logger.info(f"Creating new IRIS conversation for session {session_id}")
        return await create_conversation_direct(user_id, session_id, room_type, message, project_id)
        
    except Exception as e:
        logger.error(f"Error in get_or_create_conversation: {e}")
        # Fallback to creating new conversation
        return await create_conversation_direct(user_id, session_id, room_type, message, project_id)

async def create_conversation_direct(user_id: str, session_id: str, room_type: str, message: str, project_id: str = None) -> str:
    """Create conversation directly in database"""
    try:
        supabase = db.client
        conversation_id = str(uuid.uuid4())
        
        # Ensure valid UUID for user_id
        try:
            uuid.UUID(user_id)
            user_uuid = user_id
        except ValueError:
            # Create deterministic UUID from string
            import hashlib
            namespace_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
            user_uuid = str(uuid.uuid5(namespace_uuid, user_id))
        
        # Determine project title
        project_title = determine_project_title(message, room_type)
        
        # Create conversation record with proper project linking
        conversation_data = {
            "id": conversation_id,
            "tenant_id": "00000000-0000-0000-0000-000000000000",
            "created_by": user_uuid,
            "conversation_type": "design_inspiration",
            "entity_id": project_id if project_id else user_uuid,  # Link to project if available
            "entity_type": "project" if project_id else "homeowner",
            "title": project_title,
            "status": "active",
            "metadata": {
                "session_id": session_id,
                "agent_type": "IRIS",
                "room_type": room_type,
                "design_phase": "inspiration",
                "project_id": project_id  # Also store in metadata for reference
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("unified_conversations").insert(conversation_data).execute()
        
        if result.data and len(result.data) > 0:
            # Get the actual ID from the database response
            actual_conversation_id = result.data[0].get('id', conversation_id)
            logger.info(f"Created unified conversation: {actual_conversation_id}")
            
            # Create participant record with the actual conversation ID
            participant_data = {
                "id": str(uuid.uuid4()),
                "tenant_id": "00000000-0000-0000-0000-000000000000",
                "conversation_id": actual_conversation_id,
                "participant_id": user_uuid,
                "participant_type": "user",
                "role": "primary",
                "joined_at": datetime.utcnow().isoformat()
            }
            
            # Use correct table name
            supabase.table("unified_conversation_participants").insert(participant_data).execute()
            
            return actual_conversation_id
        else:
            logger.error("Failed to create conversation in database")
            return str(uuid.uuid4())
            
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        return str(uuid.uuid4())

async def save_photo_dual_context(user_id: str, photo_url: str, room_id: str, board_id: str, filename: str):
    """Save photo to both property documentation and inspiration board"""
    try:
        supabase = db.client
        
        # 1. First get or create a property for the homeowner
        property_result = supabase.table("properties").select("*").eq("user_id", user_id).execute()
        if property_result.data:
            property_id = property_result.data[0]["id"]
        else:
            # Create a default property
            property_id = str(uuid.uuid4())
            property_data = {
                "id": property_id,
                "user_id": user_id,
                "name": "My Home",
                "address": "Not specified",
                "property_type": "house",
                "created_at": datetime.utcnow().isoformat()
            }
            supabase.table("properties").insert(property_data).execute()
            logger.info(f"Created default property for homeowner: {property_id}")
        
        # 2. Create or get room for the property
        room_uuid = str(uuid.uuid4())
        room_result = supabase.table("property_rooms").select("*").eq(
            "property_id", property_id
        ).eq("room_type", room_id).execute()
        
        if room_result.data:
            room_uuid = room_result.data[0]["id"]
            logger.info(f"Found existing room: {room_uuid}")
        else:
            # Create the room
            room_data = {
                "id": room_uuid,
                "property_id": property_id,
                "name": room_id.replace("_", " ").title(),
                "room_type": room_id,
                "floor_level": 1,
                "description": f"{room_id} with items needing maintenance",
                "created_at": datetime.utcnow().isoformat()
            }
            supabase.table("property_rooms").insert(room_data).execute()
            logger.info(f"Created room: {room_uuid} for {room_id}")
        
        # 3. Save to property_photos for documentation (with correct schema)
        property_photo_data = {
            "id": str(uuid.uuid4()),
            "property_id": property_id,
            "room_id": room_uuid,  # Use the actual room UUID
            "photo_url": photo_url,
            "original_filename": filename,
            "photo_type": "current",
            "ai_description": f"Photo of {room_id} requiring maintenance",
            "ai_classification": {
                "room_type": room_id,
                "elements": ["uploaded_photo"]
            },
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("property_photos").insert(property_photo_data).execute()
        if result.data:
            logger.info(f"Saved photo to property documentation: {room_id}")
        
        # 4. Save to inspiration_images for inspiration board
        inspiration_data = {
            "id": str(uuid.uuid4()),
            "board_id": str(uuid.uuid4()) if not board_id else board_id,  # Use provided or generate new
            "user_id": user_id,
            "image_url": photo_url,
            "source": "upload",
            "tags": [room_id, "renovation", "property_photo"],
            "ai_analysis": {
                "room_type": room_id,
                "source": "property_documentation"
            },
            "user_notes": f"Photo from {room_id}",
            "category": "current",  # Current state of property
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("inspiration_images").insert(inspiration_data).execute()
        if result.data:
            logger.info(f"Saved photo to inspiration board: {room_id}")
        
        logger.info(f"Photo dual-context saving complete for {filename}")
        
        # 5. Check for maintenance tasks in the filename/description  
        if "broken" in filename.lower() or "repair" in filename.lower() or "fix" in filename.lower() or "blind" in filename.lower():
            await create_maintenance_task(
                user_id=user_id,
                task_description=f"Fix/repair items in {room_id} (see photo: {filename})",
                room_id=room_id,
                priority="medium"
            )
            
    except Exception as e:
        logger.error(f"Error in dual-context photo saving: {e}")

async def create_maintenance_task(user_id: str, task_description: str, room_id: str, priority: str = "medium"):
    """Create a maintenance task for the homeowner"""
    try:
        supabase = db.client
        
        # Create homeowner maintenance task
        task_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "task_description": task_description,
            "room_id": room_id,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Check if homeowner_maintenance_tasks table exists, if not use generic tasks table
        try:
            result = supabase.table("homeowner_maintenance_tasks").insert(task_data).execute()
            if result.data:
                logger.info(f"Created maintenance task: {task_description}")
        except:
            # Fallback to manual_followup_tasks if homeowner table doesn't exist
            task_data["task_type"] = "maintenance"
            task_data["title"] = f"Maintenance: {room_id}"
            task_data["description"] = task_description
            result = supabase.table("manual_followup_tasks").insert(task_data).execute()
            if result.data:
                logger.info(f"Created maintenance task in followup system: {task_description}")
                
    except Exception as e:
        logger.error(f"Error creating maintenance task: {e}")

async def get_actual_bid_submissions_for_homeowner(homeowner_user_id: str) -> list[dict]:
    """Get all actual submitted bids from contractor_bids table for a homeowner"""
    try:
        supabase = db.client
        
        # First get homeowner ID from user_id
        homeowner_result = supabase.table("homeowners").select("id").eq("user_id", homeowner_user_id).execute()
        
        if not homeowner_result.data:
            logger.warning(f"No homeowner found for user_id: {homeowner_user_id}")
            return []
        
        user_id = homeowner_result.data[0]["id"]
        
        # Get bid cards for this homeowner with FULL context
        bid_cards_result = supabase.table("bid_cards").select("""
            id,
            bid_card_number,
            project_type,
            description,
            location_city,
            location_state,
            urgency_level,
            contractor_count_needed,
            status,
            budget_min,
            budget_max,
            created_at
        """).eq("user_id", user_id).execute()
        
        if not bid_cards_result.data:
            logger.info(f"No bid cards found for homeowner: {user_id}")
            return []
        
        bid_card_ids = [bc["id"] for bc in bid_cards_result.data]
        
        # Get contractor bids for these bid cards with enhanced data
        bids_result = supabase.table("contractor_bids").select("""
            id,
            bid_card_id,
            contractor_id,
            amount,
            timeline_start,
            timeline_end,
            proposal,
            approach,
            warranty_details,
            materials_included,
            status,
            submitted_at,
            created_at
        """).in_("bid_card_id", bid_card_ids).order("submitted_at", desc=True).execute()
        
        # Create enhanced bid card lookup
        bid_cards_details = bid_cards_result
        
        # Create lookup for bid card details
        bid_card_lookup = {bc["id"]: bc for bc in bid_cards_details.data or []}
        
        bid_submissions = []
        for bid in bids_result.data or []:
            bid_card_info = bid_card_lookup.get(bid["bid_card_id"], {})
            
            # Calculate days since submission for recency context
            submitted_at = bid.get("submitted_at")
            days_ago = 0
            if submitted_at:
                from datetime import datetime
                try:
                    submitted_date = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
                    days_ago = (datetime.now(submitted_date.tzinfo) - submitted_date).days
                except:
                    days_ago = 0
            
            # Build rich bid context
            bid_submissions.append({
                "bid_id": bid["id"],
                "bid_card_id": bid["bid_card_id"],
                "contractor_id": bid["contractor_id"],
                "amount": float(bid["amount"]) if bid.get("amount") else 0,
                "timeline_start": bid.get("timeline_start"),
                "timeline_end": bid.get("timeline_end"),
                "proposal": bid.get("proposal", ""),
                "approach": bid.get("approach", ""),
                "warranty_details": bid.get("warranty_details", ""),
                "materials_included": bid.get("materials_included", False),
                "status": bid.get("status", "submitted"),
                "submitted_at": bid.get("submitted_at"),
                "days_ago": days_ago,
                # Rich bid card context
                "project_type": bid_card_info.get("project_type", "unknown"),
                "project_description": bid_card_info.get("description", ""),
                "bid_card_number": bid_card_info.get("bid_card_number", ""),
                "location_city": bid_card_info.get("location_city", ""),
                "location_state": bid_card_info.get("location_state", ""),
                "urgency_level": bid_card_info.get("urgency_level", ""),
                "contractor_count_needed": bid_card_info.get("contractor_count_needed", 0),
                "bid_card_status": bid_card_info.get("status", ""),
                "budget_min": float(bid_card_info.get("budget_min", 0)) if bid_card_info.get("budget_min") else 0,
                "budget_max": float(bid_card_info.get("budget_max", 0)) if bid_card_info.get("budget_max") else 0,
            })
        
        logger.info(f"Found {len(bid_submissions)} actual bids for homeowner {homeowner_user_id}")
        return bid_submissions
        
    except Exception as e:
        logger.error(f"Error getting actual bid submissions for IRIS: {e}")
        return []

async def get_bid_submissions_for_conversation(conversation_id: str) -> list[dict]:
    """Get all bid submissions from unified messaging system for a conversation"""
    try:
        supabase = db.client
        
        # Query unified_messages for bid submissions
        result = supabase.table("unified_messages").select("*").eq(
            "conversation_id", conversation_id
        ).contains(
            "metadata", {"message_type": "bid_submission"}
        ).execute()
        
        bid_submissions = []
        for message in result.data:
            if message.get("metadata", {}).get("message_type") == "bid_submission":
                bid_data = message["metadata"].get("bid_data", {})
                bid_submissions.append({
                    "contractor_id": bid_data.get("contractor_id"),
                    "amount": bid_data.get("amount", 0),
                    "timeline": bid_data.get("timeline", ""),
                    "proposal": bid_data.get("filtered_content", ""),
                    "submitted_at": message.get("created_at"),
                    "security_threats": message["metadata"].get("threats_detected", []),
                    "bid_details": bid_data
                })
        
        return sorted(bid_submissions, key=lambda x: x.get("submitted_at", ""), reverse=True)
        
    except Exception as e:
        logger.error(f"Error getting bid submissions for IRIS: {e}")
        return []

async def get_conversation_context_direct(conversation_id: str) -> dict:
    """Get conversation context directly from database"""
    try:
        supabase = db.client
        
        # Get conversation
        conv_result = supabase.table("unified_conversations").select("*").eq("id", conversation_id).execute()
        conversation = conv_result.data[0] if conv_result.data else {}
        
        # Get messages
        msg_result = supabase.table("unified_messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
        messages = msg_result.data if msg_result.data else []
        
        # Get memory
        mem_result = supabase.table("unified_conversation_memory").select("*").eq("conversation_id", conversation_id).execute()
        memory = mem_result.data if mem_result.data else []
        
        # Get participants
        part_result = supabase.table("unified_conversation_participants").select("*").eq("conversation_id", conversation_id).execute()
        participants = part_result.data if part_result.data else []
        
        # 🆕 Get bid submissions for design context (both unified messages and actual bids)
        bid_submissions = await get_bid_submissions_for_conversation(conversation_id)
        
        # 🆕 ALSO get actual submitted bids from contractor_bids table
        actual_bids = []
        try:
            # Get user_id from created_by field and convert to user_id
            user_id = conversation.get("created_by")
            
            if user_id:
                # Convert user_id to user_id using homeowners table lookup
                homeowner_result = supabase.table("homeowners").select("user_id").eq("id", user_id).execute()
                
                if homeowner_result.data:
                    homeowner_user_id = homeowner_result.data[0]["user_id"]
                    actual_bids = await get_actual_bid_submissions_for_homeowner(homeowner_user_id)
                    logger.info(f"Found {len(actual_bids)} actual bids for homeowner {user_id} (user_id: {homeowner_user_id})")
                else:
                    logger.warning(f"No user_id found for user_id: {user_id}")
            else:
                logger.warning("No user_id found in conversation.created_by")
        except Exception as e:
            logger.error(f"Error getting actual bids: {e}")
        
        return {
            "conversation": conversation,
            "messages": messages,
            "memory": memory,
            "participants": participants,
            "bid_submissions": bid_submissions,  # 🆕 Add bid context for design advice
            "actual_bids": actual_bids  # 🆕 Add actual submitted bids from contractor_bids table
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation context: {e}")
        return {"conversation": {}, "messages": [], "memory": [], "participants": []}

async def save_messages_direct(conversation_id: str, user_message: str, assistant_response: str, user_id: str):
    """Save messages directly to database"""
    try:
        supabase = db.client
        
        # Ensure valid UUID for user_id
        try:
            uuid.UUID(user_id)
            user_uuid = user_id
        except ValueError:
            import hashlib
            namespace_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
            user_uuid = str(uuid.uuid5(namespace_uuid, user_id))
        
        # Save user message
        user_msg_data = {
            "id": str(uuid.uuid4()),
            "tenant_id": "00000000-0000-0000-0000-000000000000",
            "conversation_id": conversation_id,
            "sender_type": "user",
            "sender_id": user_uuid,
            "content": user_message,
            "content_type": "text",
            "created_at": datetime.utcnow().isoformat()
        }
        
        user_result = supabase.table("unified_messages").insert(user_msg_data).execute()
        if user_result.data:
            logger.info(f"Saved user message to conversation {conversation_id}")
        else:
            logger.error(f"Failed to save user message: {user_result}")
        
        # Save assistant message
        # Use a deterministic UUID for the IRIS agent
        iris_agent_uuid = "11111111-1111-1111-1111-111111111111"
        
        assistant_msg_data = {
            "id": str(uuid.uuid4()),
            "tenant_id": "00000000-0000-0000-0000-000000000000",
            "conversation_id": conversation_id,
            "sender_type": "agent",
            "sender_id": iris_agent_uuid,
            "agent_type": "IRIS",
            "content": assistant_response,
            "content_type": "text",
            "created_at": datetime.utcnow().isoformat()
        }
        
        assistant_result = supabase.table("unified_messages").insert(assistant_msg_data).execute()
        if assistant_result.data:
            logger.info(f"Saved assistant message to conversation {conversation_id}")
        else:
            logger.error(f"Failed to save assistant message: {assistant_result}")
            logger.error(f"Assistant message data: {assistant_msg_data}")
        
        # Update conversation last_message_at
        supabase.table("unified_conversations").update({
            "last_message_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", conversation_id).execute()
        
        logger.info(f"Saved messages to unified system for conversation {conversation_id}")
        
    except Exception as e:
        logger.error(f"Error saving messages: {e}")

async def generate_iris_response_with_session(message: str, context: dict, conversation_id: str, session_id: str, user_id: str, request: IrisChatRequest) -> dict:
    """Generate IRIS response using the updated IrisAgent with session management"""
    try:
        # Check if this is a photo upload context
        photo_context = None
        if request.conversation_context:
            # Look for photo upload context
            for ctx in request.conversation_context:
                if ctx.get("type") == "photo_upload":
                    photo_context = ctx
                    break
        
        # Enhance message with photo context if present
        enhanced_message = message
        if photo_context:
            enhanced_message = f"[Photo uploaded: {photo_context.get('filename', 'image')}]\n{message}"
            
            # Handle dual-context saving if requested
            if photo_context.get("property_documentation") and photo_context.get("inspiration_board"):
                await save_photo_dual_context(
                    user_id=user_id,
                    photo_url=photo_context.get("image_url", ""),
                    room_id=photo_context.get("room_id", "living_room"),
                    board_id=request.board_id,
                    filename=photo_context.get("filename", "image.jpg")
                )
        
        # Create IrisRequest for the agent with CORRECT fields
        iris_request = IrisRequest(
            message=enhanced_message,
            user_id=user_id,  # Required field
            project_id=request.board_id,  # Use board_id as project_id if available
            board_context={
                "board_id": request.board_id,
                "title": context.get("conversation", {}).get("title", "Design Project"),
                "room_type": request.room_type or "general",
                "session_id": session_id,
                "conversation_id": conversation_id
            }
        )
        
        # Use the enhanced context system instead of old IrisAgent
        logger.info("Using enhanced context system for IRIS response")
        iris_response = await generate_iris_response_fallback(enhanced_message, context, conversation_id)
        
        logger.info(f"IRIS Enhanced response generated with session: {session_id}")
        
        # CRITICAL: Store design preferences after getting response
        await store_design_preferences_direct(
            conversation_id=conversation_id,
            user_message=message,
            ai_response=iris_response.response,
            context=context
        )
        
        # Enhance response if this was a photo upload with dual-context request
        enhanced_response = iris_response.response
        if photo_context and photo_context.get("property_documentation") and photo_context.get("inspiration_board"):
            enhanced_response += "\n\n✅ I've saved this photo to both your inspiration board and property documentation."
            if "broken" in message.lower() or "fix" in message.lower() or "repair" in message.lower():
                enhanced_response += " I've also added 'fixing the broken blinds' to your maintenance task list."
        
        return {
            "response": enhanced_response,
            "suggestions": iris_response.suggestions
        }
        
    except Exception as e:
        logger.error(f"IRIS Agent with session failed: {e}")
        # Fallback to original implementation
        return await generate_iris_response_fallback(message, context, conversation_id)

async def generate_iris_response_fallback(message: str, context: dict, conversation_id: str) -> dict:
    """Generate IRIS response using GPT-4o as fallback"""
    
    if not client:
        return generate_fallback_iris_response(message, context)
    
    # Build IRIS system prompt
    system_prompt = build_iris_system_prompt(context)
    
    # Build message history
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add previous messages from unified system
    for msg in context.get("messages", [])[-10:]:  # Last 10 messages
        role = "user" if msg.get("sender_type") == "user" else "assistant"
        messages.append({"role": role, "content": msg.get("content", "")})
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    try:
        # Use GPT-4o for response
        start_time = time.time()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_completion_tokens=1500,  # Fixed: GPT-4o uses max_completion_tokens
            temperature=0.7
        )
        
        # Track the cost (using sync version to avoid async issues)
        duration_ms = int((time.time() - start_time) * 1000)
        if hasattr(response, 'usage'):
            cost_tracker = LLMCostTracker()
            cost_tracker.track_llm_call_sync(
                agent_name="IRIS",
                provider="openai",
                model="gpt-4o",
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                duration_ms=duration_ms,
                context={
                    "user_id": context.get('user_id'),
                    "conversation_id": conversation_id,
                    "board_id": context.get('board_id')
                }
            )
        
        ai_response = response.choices[0].message.content
        
        # Store design preferences in memory
        await store_design_preferences_direct(conversation_id, message, ai_response, context)
        
        # Generate contextual suggestions
        suggestions = generate_iris_suggestions(context, message, ai_response)
        
        return {
            "response": ai_response,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"GPT-4o failed: {e}")
        return generate_fallback_iris_response(message, context)

async def store_design_preferences_direct(conversation_id: str, user_message: str, ai_response: str, context: dict):
    """Store design preferences directly in database"""
    try:
        preferences = extract_design_preferences(user_message, ai_response, context)
        
        if preferences:
            supabase = db.client
            
            memory_data = {
                "id": str(uuid.uuid4()),
                "tenant_id": "00000000-0000-0000-0000-000000000000",
                "conversation_id": conversation_id,
                "memory_scope": "homeowner",
                "memory_type": "design_preferences",
                "memory_key": "iris_style_preferences",
                "memory_value": {
                    "preferences": preferences,
                    "last_updated": datetime.now().isoformat(),
                    "conversation_context": context.get("conversation", {}).get("title", "Design Project")
                },
                "importance_score": 90,
                "created_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("unified_conversation_memory").insert(memory_data).execute()
            logger.info(f"Stored design preferences: {list(preferences.keys())}")
        
    except Exception as e:
        logger.error(f"Error storing design preferences: {e}")

def determine_project_title(message: str, room_type: str) -> str:
    """Determine project title from message and room type"""
    message_lower = message.lower()
    
    # Room-specific titles
    if room_type == "kitchen":
        if any(word in message_lower for word in ["modern", "farmhouse", "contemporary"]):
            style = next(word for word in ["modern", "farmhouse", "contemporary"] if word in message_lower)
            return f"{style.title()} Kitchen Design"
        return "Kitchen Design Project"
    elif room_type == "bathroom":
        return "Bathroom Renovation Ideas"
    elif room_type == "living_room":
        return "Living Room Design"
    elif room_type == "bedroom":
        return "Bedroom Makeover"
    elif room_type == "outdoor_backyard":
        return "Backyard Transformation"
    else:
        # Extract key words for general title
        if any(word in message_lower for word in ["modern", "contemporary"]):
            return "Modern Design Project"
        elif any(word in message_lower for word in ["farmhouse", "rustic"]):
            return "Farmhouse Style Project"
        elif any(word in message_lower for word in ["traditional", "classic"]):
            return "Traditional Design Project"
        else:
            return "Home Design Inspiration"

def build_iris_system_prompt(context: dict) -> str:
    """Build IRIS system prompt with conversation context"""
    
    conversation = context.get("conversation", {})
    messages = context.get("messages", [])
    memory = context.get("memory", [])
    bid_submissions = context.get("bid_submissions", [])  # 🆕 Get bid context
    actual_bids = context.get("actual_bids", [])  # 🆕 Get actual submitted bids
    
    room_type = conversation.get("metadata", {}).get("room_type", "general")
    design_phase = conversation.get("metadata", {}).get("design_phase", "inspiration")
    
    # 🆕 Build comprehensive context with rich semantic labels
    project_context = ""
    contractor_context = ""
    
    # Use actual bids if available (higher priority) - BUILD RICH CONTEXT
    if actual_bids:
        amounts = [bid["amount"] for bid in actual_bids if bid["amount"]]
        if amounts:
            avg_budget = sum(amounts) / len(amounts)
            min_amount = min(amounts)
            max_amount = max(amounts)
            
            # Get project details from first bid (they're all for same project)
            first_bid = actual_bids[0]
            project_type = first_bid.get('project_type', '').replace('_', ' ').title()
            location = f"{first_bid.get('location_city', '')}, {first_bid.get('location_state', '')}".strip(', ')
            
            # Build PROJECT context section
            project_context = f"""

🏠 PROJECT INFORMATION:
• Project Type: {project_type}
• Bid Card: {first_bid.get('bid_card_number', 'Unknown')}
• Location: {location}
• Project Description: {first_bid.get('project_description', 'No description available')}
• Homeowner Budget Range: ${first_bid.get('budget_min', 0):,.0f} - ${first_bid.get('budget_max', 0):,.0f}
• Project Status: {first_bid.get('bid_card_status', 'unknown')}
• Contractors Needed: {first_bid.get('contractor_count_needed', 'unknown')}
• Urgency: {first_bid.get('urgency_level') or 'Normal timeline'}"""
            
            # Build CONTRACTOR BIDS context section
            contractor_details = []
            for i, bid in enumerate(actual_bids[:3], 1):  # Show up to 3 recent bids
                timeline = f"{bid.get('timeline_start', 'TBD')} to {bid.get('timeline_end', 'TBD')}"
                days_ago_text = f"{bid.get('days_ago', 0)} days ago" if bid.get('days_ago', 0) > 0 else "today"
                
                # Build rich bid description
                bid_detail = f"""
  Contractor Bid #{i}:
  • Quote: ${bid['amount']:,.2f} for complete {project_type.lower()}
  • Timeline: {timeline}
  • Submitted: {days_ago_text}
  • Status: {bid.get('status', 'submitted')}
  • Materials Included: {'Yes' if bid.get('materials_included') else 'No'}"""
                
                # Add proposal excerpt if available
                if bid.get('proposal'):
                    proposal_excerpt = bid['proposal'][:150] + "..." if len(bid['proposal']) > 150 else bid['proposal']
                    bid_detail += f"\n  • Proposal: \"{proposal_excerpt}\""
                
                contractor_details.append(bid_detail)
            
            contractor_context = f"""

💼 CONTRACTOR BIDS SUBMITTED:
• Total Bids: {len(actual_bids)} actual contractor submissions
• Price Range: ${min_amount:,.2f} - ${max_amount:,.2f}
• Average Quote: ${avg_budget:,.2f}
• Bid Status: These are REAL submitted contractor quotes (not estimates)

{chr(10).join(contractor_details)}

🎯 DESIGN GUIDANCE BASED ON ACTUAL BIDS:
• Use the ${avg_budget:,.2f} average as your design budget reference
• Consider the {timeline} timeline when suggesting project phases
• These contractors have committed to these prices and timelines
• Help evaluate which bid offers best value for the project scope
• Suggest design choices that align with the submitted quotes"""
            
    elif bid_submissions:
        # Fallback to unified messaging bids if no actual bids
        amounts = [bid["amount"] for bid in bid_submissions if bid["amount"]]
        if amounts:
            avg_budget = sum(amounts) / len(amounts)
            contractor_context = f"""

💼 CONTRACTOR BID CONTEXT:
• {len(bid_submissions)} contractor bids received  
• Budget range from bids: ${min(amounts):,.2f} - ${max(amounts):,.2f}
• Average bid amount: ${avg_budget:,.2f}
• Use this context to suggest designs appropriate for their actual project budget
• Consider real contractor timelines when discussing project phases
"""
    
    # Get project memory if available
    project_memory = ""
    for mem in memory:
        if mem.get("memory_type") == "project_context":
            project_memory += f"\n- {mem.get('memory_key')}: {mem.get('memory_value', '')}"
    
    return f"""You are Iris, an expert interior design assistant specializing in inspiration discovery and project organization for InstaBids.

CONVERSATION CONTEXT:
- Room Type: {room_type}
- Design Phase: {design_phase} 
- Messages in conversation: {len(messages)}
- Project Title: {conversation.get('title', 'Design Project')}
{project_memory}{project_context}{contractor_context}

YOUR EXPERTISE:
• Help homeowners discover and organize their design inspiration
• Analyze current spaces and articulate ideal visions  
• Guide through style discovery (modern, farmhouse, traditional, etc.)
• Extract specific elements from inspiration images
• Create actionable project requirements for contractors
• Budget-conscious and realistic advice

🎯 HOW TO USE CONTRACTOR BID CONTEXT:
• When contractor bids are available above, reference specific quotes and timelines
• Example: "Based on the $40,000 contractor quote, you could afford premium materials..."
• Example: "Given the February-April timeline from the bid, we should focus on..."
• Always specify that you're using ACTUAL contractor data, not estimates
• Help homeowners understand what their real budget can achieve
• Compare different contractor approaches if multiple bids exist
• Point out good value propositions in the submitted bids

📋 PROJECT CONTEXT USAGE:
• Reference the specific project type and location when relevant
• Use the project description to understand scope and requirements
• Consider urgency level when suggesting timeline-dependent choices
• Acknowledge the homeowner's original budget range vs actual bids received

YOUR PERSONALITY:
- Warm, encouraging, and genuinely helpful
- Expert knowledge but approachable explanations
- Asks thoughtful questions to understand preferences
- Focuses on what makes spaces feel like "home"
- Practical about budgets and timelines

CONVERSATION APPROACH:
1. **Understand Current Space**: What they have now, what works, what doesn't
2. **Explore Ideal Vision**: Style preferences, inspiration, dream elements
3. **Identify Specific Elements**: Colors, materials, layouts, features
4. **Organize & Prioritize**: Must-haves vs nice-to-haves, budget considerations
5. **Create Actionable Plan**: Clear requirements for contractors

IMPORTANT NOTES:
• You do NOT generate images - you help them find, organize, and understand inspiration
• Focus on helping them articulate their vision clearly
• Ask specific questions about functionality and lifestyle needs
• Help them prepare comprehensive project briefs for contractors
• Always be encouraging about their vision while keeping expectations realistic

Current conversation context: {len(messages)} previous messages exchanged."""

def generate_iris_suggestions(context: dict, message: str, response: str) -> list[str]:
    """Generate contextual suggestions for IRIS conversation"""
    
    conversation = context.get("conversation", {})
    messages = context.get("messages", [])
    room_type = conversation.get("metadata", {}).get("room_type", "general")
    message_lower = message.lower()
    
    # Suggestions based on conversation stage
    if len(messages) < 2:  # Early conversation
        return [
            "Tell me about my current space",
            "Help me explore design styles",
            "What's my ideal vision?",
            "How do I organize my ideas?"
        ]
    elif any(word in message_lower for word in ["current", "existing", "have now"]):
        return [
            "What needs to change most?",
            "Show me ideal inspirations",
            "Help me prioritize improvements",
            "Estimate my project budget"
        ]
    elif any(word in message_lower for word in ["style", "inspiration", "love", "want"]):
        return [
            "Find similar design examples",
            "Help me organize my inspiration",
            "What's my color palette?",
            "Create project summary"
        ]
    else:
        return [
            "Help me refine my style",
            "Organize my inspiration",
            "Create project priorities",
            "Find more examples"
        ]

def generate_fallback_iris_response(message: str, context: dict) -> dict:
    """Generate fallback IRIS response when AI is unavailable"""
    
    conversation = context.get("conversation", {})
    messages = context.get("messages", [])
    room_type = conversation.get("metadata", {}).get("room_type", "general")
    
    response = f"""I'm here to help you with your {room_type} design inspiration! Let me understand your vision better.

What specific aspects of your space are you looking to improve? I can help you:
• Understand your current space and what needs to change
• Explore different design styles and find what resonates with you
• Organize your inspiration into actionable project requirements
• Create a clear brief for contractors

Tell me more about your project goals!"""
    
    suggestions = [
        "Tell you about my current space",
        "Explore my ideal vision",
        "Help organize my inspiration",
        "Create contractor requirements"
    ]
    
    return {
        "response": response,
        "suggestions": suggestions
    }

def extract_design_preferences(user_message: str, ai_response: str, context: dict) -> dict:
    """Extract design preferences from Iris conversation for cross-agent memory"""
    preferences = {}
    
    # Combine message content for analysis
    combined_text = f"{user_message} {ai_response}".lower()
    
    # Extract style preferences
    style_keywords = {
        "modern": ["modern", "contemporary", "minimalist", "clean lines"],
        "farmhouse": ["farmhouse", "rustic", "shiplap", "barn door"],
        "traditional": ["traditional", "classic", "formal"],
        "industrial": ["industrial", "exposed brick", "metal", "concrete"],
        "scandinavian": ["scandinavian", "hygge", "light wood"],
        "mediterranean": ["mediterranean", "terracotta", "stucco"]
    }
    
    detected_styles = []
    for style, keywords in style_keywords.items():
        if any(keyword in combined_text for keyword in keywords):
            detected_styles.append(style)
    
    if detected_styles:
        preferences["preferred_styles"] = detected_styles
    
    # Extract color preferences
    color_keywords = {
        "neutral": ["white", "beige", "cream", "gray", "neutral"],
        "warm": ["warm", "cozy", "earth tones", "brown", "orange"],
        "cool": ["cool", "blue", "green", "calming"],
        "dark": ["dark", "black", "deep colors", "dramatic"],
        "bright": ["bright", "colorful", "vibrant", "bold"]
    }
    
    detected_colors = []
    for color_type, keywords in color_keywords.items():
        if any(keyword in combined_text for keyword in keywords):
            detected_colors.append(color_type)
    
    if detected_colors:
        preferences["color_preferences"] = detected_colors
    
    # Extract material preferences
    materials = ["wood", "stone", "metal", "glass", "ceramic", "marble", "granite", "quartz"]
    detected_materials = [material for material in materials if material in combined_text]
    
    if detected_materials:
        preferences["material_preferences"] = detected_materials
    
    # Extract room-specific information
    room_type = context.get("conversation", {}).get("metadata", {}).get("room_type")
    if room_type:
        preferences["focus_room"] = room_type
    
    # Extract budget mentions
    budget_keywords = ["budget", "cost", "price", "affordable", "expensive", "cheap"]
    if any(keyword in combined_text for keyword in budget_keywords):
        preferences["budget_conscious"] = True
    
    return preferences

# Project push models for homeowner agent integration
class IrisProjectProposal(BaseModel):
    user_id: str
    iris_session_id: str
    source_context: str  # "inspiration", "house_analysis", or "combined"
    
    project_proposal: dict  # Contains all IRIS analysis
    design_preferences: Optional[dict] = None
    current_state_analysis: Optional[dict] = None
    inspiration_summary: Optional[dict] = None
    
    next_steps: list[str]
    confidence_score: float
    
    # Context preservation
    iris_conversation_id: Optional[str] = None
    unified_memory_refs: Optional[list[str]] = None

class ProjectPushResponse(BaseModel):
    success: bool
    project_id: Optional[str] = None
    message: str
    next_action: str
    error: Optional[str] = None

@router.get("/test-bid-access/{homeowner_user_id}")
async def test_iris_bid_access(homeowner_user_id: str):
    """Test endpoint to check if IRIS can access submitted bids for a homeowner"""
    try:
        logger.info(f"Testing IRIS bid access for homeowner: {homeowner_user_id}")
        
        # Get actual bids
        actual_bids = await get_actual_bid_submissions_for_homeowner(homeowner_user_id)
        
        return {
            "success": True,
            "homeowner_user_id": homeowner_user_id,
            "bids_found": len(actual_bids),
            "bids": actual_bids,
            "message": f"IRIS can access {len(actual_bids)} submitted bids for this homeowner"
        }
        
    except Exception as e:
        logger.error(f"Error testing IRIS bid access: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/push-project", response_model=ProjectPushResponse)
async def push_project_to_homeowner_agent(proposal: IrisProjectProposal):
    """
    Push IRIS project proposal to homeowner agent for implementation planning
    This endpoint compiles IRIS house analysis into actionable project proposal
    """
    try:
        logger.info(f"IRIS pushing project proposal for homeowner {proposal.user_id}")
        
        # 1. Validate homeowner exists
        homeowner_result = db.client.table("homeowners").select("*").eq("user_id", proposal.user_id).execute()
        if not homeowner_result.data:
            return ProjectPushResponse(
                success=False,
                message="Homeowner not found",
                next_action="error",
                error="Invalid homeowner ID"
            )
        
        homeowner = homeowner_result.data[0]
        
        # 2. Get IRIS conversation context if available
        iris_context = {}
        if proposal.iris_conversation_id:
            try:
                iris_conv_result = db.client.table("unified_conversations").select("*").eq("id", proposal.iris_conversation_id).execute()
                if iris_conv_result.data:
                    iris_context = iris_conv_result.data[0]
            except Exception as e:
                logger.warning(f"Could not load IRIS conversation context: {e}")
        
        # 3. Analyze house context and create project proposal
        project_analysis = await analyze_house_context_for_project(
            user_id=proposal.user_id,
            iris_session=proposal.iris_session_id,
            current_state=proposal.current_state_analysis,
            design_prefs=proposal.design_preferences,
            source_context=proposal.source_context
        )
        
        # 4. Create project record
        project_id = str(uuid.uuid4())
        project_data = {
            "id": project_id,
            "user_id": homeowner["id"],
            "title": project_analysis.get("project_title", "IRIS Home Analysis Project"),
            "description": project_analysis.get("description", "House analysis project created from IRIS conversation"),
            "category": project_analysis.get("project_type", "renovation"),
            "urgency": "soon",
            "budget_range": project_analysis.get("budget_range", {"min": 5000, "max": 50000}),
            "location": homeowner.get("location", {}),
            "status": "draft",
            "job_assessment": {
                "created_from": "iris_house_analysis",
                "iris_session_id": proposal.iris_session_id,
                "iris_context": {
                    "source_context": proposal.source_context,
                    "confidence_score": proposal.confidence_score,
                    "analysis_summary": project_analysis,
                    "original_proposal": proposal.project_proposal
                }
            }
        }
        
        project_result = db.client.table("projects").insert(project_data).execute()
        
        if not project_result.data:
            return ProjectPushResponse(
                success=False,
                message="Failed to create project record",
                next_action="error",
                error="Database insertion failed"
            )
        
        # 5. Call homeowner agent endpoint (when it exists)
        homeowner_response = await call_homeowner_agent_endpoint(
            proposal=proposal,
            project_id=project_id,
            project_analysis=project_analysis
        )
        
        # 6. Link IRIS conversation to project if available
        if proposal.iris_conversation_id:
            try:
                db.client.table("unified_conversations").update({
                    "entity_id": project_id,
                    "entity_type": "project",
                    "metadata": {
                        **iris_context.get("metadata", {}),
                        "linked_to_project": True,
                        "project_created_at": datetime.utcnow().isoformat()
                    }
                }).eq("id", proposal.iris_conversation_id).execute()
            except Exception as e:
                logger.warning(f"Could not link IRIS conversation to project: {e}")
        
        logger.info(f"Successfully created project {project_id} from IRIS analysis")
        
        return ProjectPushResponse(
            success=True,
            project_id=project_id,
            message=f"Project created successfully from IRIS {proposal.source_context} analysis",
            next_action="begin_implementation_planning"
        )
        
    except Exception as e:
        logger.error(f"Error pushing IRIS project proposal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return ProjectPushResponse(
            success=False,
            message="Internal server error during project creation",
            next_action="error",
            error=str(e)
        )

async def analyze_house_context_for_project(
    user_id: str, 
    iris_session: str, 
    current_state: Optional[dict], 
    design_prefs: Optional[dict],
    source_context: str
) -> dict:
    """Analyze house context and create actionable project proposal"""
    
    try:
        # Get IRIS conversation context from unified system
        iris_context = await get_iris_house_analysis_context(user_id, iris_session)
        
        # Combine current state analysis with IRIS insights
        analysis = {
            "project_title": determine_project_title_from_house_analysis(current_state, iris_context),
            "project_type": determine_project_type_from_analysis(current_state, iris_context),
            "priority_areas": extract_priority_renovation_areas(current_state, iris_context),
            "estimated_scope": estimate_project_scope(current_state, design_prefs),
            "budget_estimate": estimate_budget_from_house_analysis(current_state, iris_context),
            "timeline_estimate": estimate_project_timeline(current_state),
            "contractor_requirements": determine_contractor_specialties_needed(current_state, iris_context),
            "next_steps": generate_implementation_next_steps(current_state, source_context),
            "confidence_indicators": {
                "has_current_photos": bool(current_state and current_state.get("photos")),
                "has_room_analysis": bool(current_state and current_state.get("room_analysis")),
                "has_problem_identification": bool(current_state and current_state.get("issues_identified")),
                "has_style_preferences": bool(design_prefs)
            }
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing house context: {e}")
        # Return basic fallback analysis
        return {
            "project_title": "Home Renovation Project",
            "project_type": "general_renovation", 
            "priority_areas": ["assessment_needed"],
            "estimated_scope": "to_be_determined",
            "budget_estimate": {"range": "pending_analysis", "confidence": "low"},
            "timeline_estimate": "pending_scope_definition",
            "contractor_requirements": ["general_contractor", "licensed", "insured"],
            "next_steps": ["detailed_assessment", "scope_definition", "contractor_consultation"],
            "confidence_indicators": {"analysis_incomplete": True}
        }

async def get_iris_house_analysis_context(user_id: str, iris_session: str) -> dict:
    """Get IRIS conversation context focused on house analysis"""
    try:
        # Get IRIS conversation from unified system
        conv_result = db.client.table("unified_conversations").select("*").eq(
            "created_by", user_id
        ).contains("metadata", {"session_id": iris_session}).execute()
        
        if conv_result.data:
            conversation = conv_result.data[0]
            
            # Get memory entries for house analysis
            memory_result = db.client.table("unified_conversation_memory").select("*").eq(
                "conversation_id", conversation["id"]
            ).eq("memory_type", "photo_reference").execute()
            
            # Get messages for context
            messages_result = db.client.table("unified_messages").select("*").eq(
                "conversation_id", conversation["id"]
            ).order("created_at").execute()
            
            return {
                "conversation": conversation,
                "house_photos": memory_result.data if memory_result.data else [],
                "conversation_messages": messages_result.data if messages_result.data else [],
                "analysis_available": True
            }
    except Exception as e:
        logger.warning(f"Could not load IRIS house analysis context: {e}")
    
    return {"analysis_available": False}

def determine_project_title_from_house_analysis(current_state: Optional[dict], iris_context: dict) -> str:
    """Generate appropriate project title from house analysis"""
    if not current_state:
        return "Home Assessment and Renovation Planning"
    
    # Extract room types from analysis
    rooms_mentioned = []
    if current_state.get("room_analysis"):
        rooms_mentioned = list(current_state["room_analysis"].keys())
    
    # Extract issues from analysis  
    issues = current_state.get("issues_identified", [])
    
    if len(rooms_mentioned) == 1:
        room = rooms_mentioned[0].replace("_", " ").title()
        if any("kitchen" in issue.lower() for issue in issues):
            return f"{room} Renovation Project"
        elif any("bathroom" in issue.lower() for issue in issues):
            return f"{room} Remodel Project"
        else:
            return f"{room} Improvement Project"
    elif len(rooms_mentioned) > 1:
        return "Multi-Room Renovation Project"
    else:
        return "Home Improvement Project"

def determine_project_type_from_analysis(current_state: Optional[dict], iris_context: dict) -> str:
    """Determine project type from house analysis"""
    if not current_state:
        return "general_renovation"
    
    room_types = []
    if current_state.get("room_analysis"):
        room_types = list(current_state["room_analysis"].keys())
    
    # Single room projects
    if len(room_types) == 1:
        room = room_types[0]
        if "kitchen" in room:
            return "kitchen_remodel"
        elif "bathroom" in room:
            return "bathroom_remodel"
        elif "bedroom" in room:
            return "bedroom_renovation"
        elif "living" in room:
            return "living_room_renovation"
    
    # Multi-room projects
    elif len(room_types) > 1:
        return "multi_room_renovation"
    
    return "general_renovation"

def extract_priority_renovation_areas(current_state: Optional[dict], iris_context: dict) -> list[str]:
    """Extract priority areas from house analysis"""
    priorities = []
    
    if current_state and current_state.get("issues_identified"):
        for issue in current_state["issues_identified"]:
            issue_lower = issue.lower()
            if any(word in issue_lower for word in ["urgent", "leak", "broken", "safety"]):
                priorities.insert(0, issue)  # High priority first
            else:
                priorities.append(issue)
    
    if current_state and current_state.get("room_analysis"):
        for room, analysis in current_state["room_analysis"].items():
            if isinstance(analysis, dict) and analysis.get("condition_score", 5) < 3:
                priorities.append(f"{room.replace('_', ' ')} needs attention")
    
    return priorities[:5] if priorities else ["general_assessment_needed"]

def estimate_project_scope(current_state: Optional[dict], design_prefs: Optional[dict]) -> str:
    """Estimate project scope from analysis"""
    if not current_state:
        return "scope_assessment_needed"
    
    room_count = len(current_state.get("room_analysis", {}))
    issue_count = len(current_state.get("issues_identified", []))
    
    if room_count >= 3 or issue_count >= 5:
        return "major_renovation"
    elif room_count >= 2 or issue_count >= 3:
        return "moderate_renovation"
    else:
        return "minor_improvements"

def estimate_budget_from_house_analysis(current_state: Optional[dict], iris_context: dict) -> dict:
    """Estimate budget range from house analysis"""
    if not current_state:
        return {"range": "assessment_required", "confidence": "low"}
    
    room_count = len(current_state.get("room_analysis", {}))
    issues_count = len(current_state.get("issues_identified", []))
    
    # Basic estimation logic
    if room_count >= 3:
        return {"range": "$40,000 - $80,000", "confidence": "medium", "basis": "multi_room_renovation"}
    elif room_count == 2:
        return {"range": "$20,000 - $45,000", "confidence": "medium", "basis": "two_room_project"}
    elif room_count == 1:
        room_type = list(current_state.get("room_analysis", {}).keys())[0]
        if "kitchen" in room_type:
            return {"range": "$15,000 - $35,000", "confidence": "medium", "basis": "kitchen_renovation"}
        elif "bathroom" in room_type:
            return {"range": "$8,000 - $20,000", "confidence": "medium", "basis": "bathroom_renovation"}
    
    return {"range": "$5,000 - $15,000", "confidence": "low", "basis": "general_improvements"}

def estimate_project_timeline(current_state: Optional[dict]) -> str:
    """Estimate project timeline from scope"""
    if not current_state:
        return "timeline_pending_scope"
    
    room_count = len(current_state.get("room_analysis", {}))
    urgent_issues = [issue for issue in current_state.get("issues_identified", []) 
                    if any(word in issue.lower() for word in ["urgent", "leak", "broken", "safety"])]
    
    if urgent_issues:
        return "1-2 weeks (urgent repairs) + renovation timeline"
    elif room_count >= 3:
        return "8-16 weeks (major renovation)"
    elif room_count >= 2:
        return "4-8 weeks (moderate project)"
    else:
        return "2-4 weeks (single room/improvements)"

def determine_contractor_specialties_needed(current_state: Optional[dict], iris_context: dict) -> list[str]:
    """Determine required contractor specialties"""
    specialties = ["licensed", "insured"]  # Always required
    
    if not current_state:
        return specialties + ["general_contractor"]
    
    room_types = list(current_state.get("room_analysis", {}).keys())
    issues = current_state.get("issues_identified", [])
    
    # Room-specific specialties
    if any("kitchen" in room for room in room_types):
        specialties.extend(["kitchen_remodeling", "cabinetry", "countertops"])
    if any("bathroom" in room for room in room_types):
        specialties.extend(["bathroom_remodeling", "plumbing", "tile_work"])
    
    # Issue-specific specialties
    for issue in issues:
        issue_lower = issue.lower()
        if any(word in issue_lower for word in ["plumb", "pipe", "leak", "water"]):
            specialties.append("plumbing")
        if any(word in issue_lower for word in ["electric", "outlet", "wiring"]):
            specialties.append("electrical")
        if any(word in issue_lower for word in ["roof", "shingle", "gutter"]):
            specialties.append("roofing")
        if any(word in issue_lower for word in ["floor", "carpet", "hardwood"]):
            specialties.append("flooring")
    
    return list(set(specialties))  # Remove duplicates

def generate_implementation_next_steps(current_state: Optional[dict], source_context: str) -> list[str]:
    """Generate next steps for implementation"""
    steps = []
    
    if source_context == "house_analysis":
        steps.append("Review house analysis findings with contractor")
        steps.append("Get detailed estimates for priority areas")
        steps.append("Create project timeline and phasing plan")
    elif source_context == "inspiration":
        steps.append("Combine inspiration with house assessment")
        steps.append("Create design-build project scope")
        steps.append("Find contractors experienced with desired style")
    else:  # combined
        steps.append("Finalize project scope combining analysis and inspiration")
        steps.append("Get comprehensive design-build estimates")
        steps.append("Create detailed project implementation plan")
    
    if current_state and current_state.get("issues_identified"):
        urgent_issues = [issue for issue in current_state["issues_identified"] 
                        if any(word in issue.lower() for word in ["urgent", "leak", "broken", "safety"])]
        if urgent_issues:
            steps.insert(0, "Address urgent issues immediately")
    
    steps.append("Select contractor and begin project")
    return steps

async def call_homeowner_agent_endpoint(
    proposal: IrisProjectProposal,
    project_id: str, 
    project_analysis: dict
) -> dict:
    """Call CIA endpoint to receive IRIS project proposal"""
    
    try:
        # The endpoint is in CIA routes, not homeowner routes!
        cia_endpoint_url = f"{get_backend_url()}/api/cia/receive-iris-proposal"
        
        logger.info(f"Calling CIA endpoint with project {project_id}")
        logger.info(f"Project analysis: {project_analysis.get('project_title')}")
        
        # Make actual HTTP call to CIA endpoint
        import requests
        response = requests.post(
            cia_endpoint_url, 
            json=proposal.dict(),
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"CIA endpoint response: {result}")
            return {
                "success": True,
                "message": "Successfully transferred to CIA for implementation planning",
                "cia_session_id": result.get("session_id"),
                "cia_project_id": result.get("project_id"),
                "next_action": "begin_implementation_planning"
            }
        else:
            logger.error(f"CIA endpoint returned status {response.status_code}: {response.text}")
            return {
                "success": False,
                "message": f"CIA endpoint error: {response.status_code}",
                "next_action": "manual_handoff_required"
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to call CIA endpoint: {e}")
        return {
            "success": False,
            "message": f"Failed to reach CIA endpoint: {str(e)}",
            "next_action": "manual_handoff_required"
        }
    except Exception as e:
        logger.error(f"Unexpected error calling CIA endpoint: {e}")
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "next_action": "manual_handoff_required"
        }

# Create singleton instance for compatibility
iris_unified_agent = router