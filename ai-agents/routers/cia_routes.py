"""
CIA Routes - Customer Interface Agent API Endpoints
Owner: Agent 1 (Frontend Flow)
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import CIA agent and related models
from agents.cia.agent import CustomerInterfaceAgent
from database_simple import db


# Create router
router = APIRouter()

# Pydantic models for request/response
class ChatMessage(BaseModel):
    message: str
    images: Optional[list[str]] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    current_phase: str
    ready_for_jaa: bool
    missing_fields: list[str]
    collected_info: Optional[dict[str, Any]] = None
    messages: Optional[list[dict[str, Any]]] = None

# Global CIA agent instance (initialized in main.py)
cia_agent: Optional[CustomerInterfaceAgent] = None

def set_cia_agent(agent: CustomerInterfaceAgent):
    """Set the CIA agent instance"""
    global cia_agent
    cia_agent = agent

@router.get("/conversation/{session_id}")
async def get_cia_conversation_history(session_id: str):
    """Get conversation history for a session"""
    try:
        # Load conversation state from database
        conversation_state = await db.load_conversation_state(session_id)

        if not conversation_state:
            return {
                "success": True,
                "messages": [],
                "session_id": session_id,
                "total_messages": 0
            }

        # Extract messages from conversation state
        state = conversation_state.get("state", {})

        # Handle case where state might be a JSON string
        if isinstance(state, str):
            import json
            try:
                state = json.loads(state)
            except:
                state = {}

        messages = state.get("messages", []) if isinstance(state, dict) else []

        # Convert to frontend-compatible format
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "id": str(len(formatted_messages) + 1),
                "role": msg.get("role", "assistant"),
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp", conversation_state.get("created_at", "")),
                "images": msg.get("images", [])
            })

        return {
            "success": True,
            "messages": formatted_messages,
            "session_id": session_id,
            "total_messages": len(formatted_messages),
            "last_updated": conversation_state.get("updated_at"),
            "project_id": state.get("collected_info", {}).get("project_id")
        }

    except Exception as e:
        print(f"Error loading conversation history: {e}")
        return {
            "success": False,
            "error": str(e),
            "messages": [],
            "session_id": session_id,
            "total_messages": 0
        }

@router.post("/chat", response_model=ChatResponse)
async def cia_chat(chat_data: ChatMessage):
    """Handle chat messages for the CIA agent with Supabase persistence"""
    if not cia_agent:
        # If agent not initialized (no API key), provide intelligent fallback
        return ChatResponse(
            response=generate_intelligent_response(chat_data.message, chat_data.images),
            session_id=chat_data.session_id or f"demo_{datetime.now().timestamp()}",
            current_phase="discovery",
            ready_for_jaa=False,
            missing_fields=["project_type", "budget", "timeline"]
        )

    try:
        # Use authenticated user ID if provided, otherwise use anonymous UUID
        user_id = chat_data.user_id or "00000000-0000-0000-0000-000000000000"
        if chat_data.user_id:
            print(f"[CIA] Using authenticated user ID: {user_id}")
        else:
            print(f"[CIA] Using anonymous user ID: {user_id}")

        # Handle project awareness
        project_id = chat_data.project_id
        bid_card_context = None
        if project_id:
            print(f"[CIA] Using project ID: {project_id}")
            # Load bid card data
            try:
                # Try to load bid card data
                bid_card_result = db.client.table("bid_cards").select("*").eq("id", project_id).execute()
                if bid_card_result.data:
                    bid_card_context = bid_card_result.data[0]
                    print(f"[CIA] Loaded bid card: {bid_card_context.get('bid_card_number')}")
                else:
                    print(f"[CIA] No bid card found for project ID: {project_id}")

                # Verify user access if authenticated
                if user_id != "00000000-0000-0000-0000-000000000000" and bid_card_context:
                    # For authenticated users, check homeowner relationship
                    homeowner_result = db.client.table("homeowners").select("id").eq("user_id", user_id).execute()
                    if homeowner_result.data:
                        user_id = homeowner_result.data[0]["id"]
                        if bid_card_context.get("user_id") != user_id:
                            raise HTTPException(status_code=403, detail="Bid card access denied")
                        print(f"[CIA] Verified bid card access for homeowner {user_id}")
            except HTTPException:
                raise
            except Exception as e:
                print(f"[CIA] Bid card loading warning: {e}")

        # Generate session ID - include project if specified
        if not chat_data.session_id:
            if project_id:
                session_id = f"project_{project_id}_{datetime.now().timestamp()}"
            else:
                session_id = f"cia_anonymous_{datetime.now().timestamp()}"
        else:
            session_id = chat_data.session_id

        # Load existing conversation state from Supabase
        existing_conversation = await db.load_conversation_state(session_id)

        # Extract state if conversation exists
        if existing_conversation:
            print(f"[CIA] Loaded existing conversation for session {session_id}")
            existing_state = existing_conversation.get("state", {})
        else:
            print(f"[CIA] Starting new conversation for session {session_id}")
            existing_state = None

        # Process images if provided
        image_urls = []
        if chat_data.images:
            for img_data in chat_data.images:
                # In production, save to Supabase storage
                # For now, we'll just pass the base64 data
                image_urls.append(img_data)

        # Enhance existing state with bid card context if available
        if existing_state and bid_card_context:
            existing_state["bid_card_context"] = bid_card_context
            existing_state["project_id"] = project_id
        elif bid_card_context:
            existing_state = {
                "bid_card_context": bid_card_context,
                "project_id": project_id
            }

        # Call the actual CIA agent with existing state
        result = await cia_agent.handle_conversation(
            user_id=user_id,
            message=chat_data.message,
            images=image_urls,
            session_id=session_id,
            existing_state=existing_state,
            project_id=project_id
        )

        # Save conversation state to Supabase
        if "state" in result:
            # Add project information to state if available
            enhanced_state = result["state"].copy()
            if project_id:
                enhanced_state["project_id"] = project_id
                enhanced_state["project_context"] = True

            await db.save_conversation_state(
                user_id=user_id,
                thread_id=session_id,
                agent_type="CIA",
                state=enhanced_state
            )
            print(f"[CIA] Saved conversation state for session {session_id}")

            # If project is specified and conversation is ready for JAA, link them
            if project_id and result.get("ready_for_jaa", False):
                try:
                    db.client.table("projects").update({
                        "cia_conversation_id": session_id,
                        "status": "in_progress"
                    }).eq("id", project_id).execute()
                    print(f"[CIA] Linked conversation {session_id} to project {project_id}")
                except Exception as e:
                    print(f"[CIA] Warning: Could not link conversation to project: {e}")

        return ChatResponse(**result)

    except Exception as e:
        import traceback
        print(f"Error in CIA chat: {e}")
        print(traceback.format_exc())
        # Fallback to intelligent response
        return ChatResponse(
            response=generate_intelligent_response(chat_data.message, chat_data.images),
            session_id=chat_data.session_id or f"demo_{datetime.now().timestamp()}",
            current_phase="discovery",
            ready_for_jaa=False,
            missing_fields=["project_type", "budget", "timeline"]
        )

def generate_intelligent_response(message: str, images: Optional[list[str]] = None) -> str:
    """Generate contextually appropriate responses without LLM"""
    message_lower = message.lower()

    # Image handling
    if images and len(images) > 0:
        image_count = len(images)
        image_response = f"I can see you've uploaded {image_count} {'photo' if image_count == 1 else 'photos'}. "

        # Analyze based on context
        if "kitchen" in message_lower:
            return image_response + "From what I can see, this kitchen space has great potential! Can you tell me what specific changes you're envisioning? Are you thinking about updating the cabinets, countertops, appliances, or going for a complete transformation?"
        elif "bathroom" in message_lower:
            return image_response + "Thanks for sharing these bathroom photos. I can see the current setup. What's your main goal with this renovation - are you looking to update fixtures, retile, or do a complete remodel?"
        else:
            return image_response + "These photos really help me understand your space. What specific improvements are you hoping to make?"

    # Project type responses
    if "kitchen" in message_lower:
        if "complete" in message_lower or "full" in message_lower:
            return "A complete kitchen renovation is an exciting project! This typically includes new cabinets, countertops, appliances, flooring, and sometimes layout changes. What's your approximate budget range for this project? Most full kitchen remodels in your area range from $25,000 to $60,000."
        elif "cabinet" in message_lower:
            return "Cabinet updates can dramatically transform your kitchen! Are you thinking about refacing the existing cabinets, painting them, or installing completely new ones? Also, what style appeals to you - modern, traditional, or transitional?"
        else:
            return "Great! Kitchen projects are very popular and can really transform your home. To help match you with the right contractors, could you tell me more about what you'd like to change? For example, are you updating cabinets, countertops, appliances, or planning a complete remodel?"

    elif "bathroom" in message_lower:
        if "master" in message_lower or "primary" in message_lower:
            return "A master bathroom renovation - excellent choice! These typically include updating fixtures, tile work, vanities, and sometimes expanding the space. What's the size of your current bathroom, and what are your must-have features?"
        elif "guest" in message_lower or "powder" in message_lower:
            return "Guest bathroom updates are great for both functionality and home value. Are you thinking about a simple refresh with new fixtures and paint, or a more comprehensive update with new tile and vanity?"
        else:
            return "Bathroom renovations are fantastic for both daily enjoyment and home value. What's motivating this project - is it style updates, fixing problems, or adding functionality? And which bathroom are we talking about - master, guest, or another?"

    elif "roof" in message_lower:
        if "leak" in message_lower or "damage" in message_lower:
            return "I understand - roof leaks need immediate attention. How severe is the damage? Are you seeing water stains inside, missing shingles, or active leaking? This will help determine if you need emergency repairs or can plan for a full replacement."
        else:
            return "Roof work is crucial for protecting your home. Are you dealing with damage that needs repair, or is it time for a full replacement? Also, do you know approximately how old your current roof is?"

    elif "budget" in message_lower:
        return "Budget planning is smart! For reference, here are typical ranges in your area:\\n• Kitchen remodels: $15,000-$60,000\\n• Bathroom remodels: $8,000-$25,000\\n• Roofing: $8,000-$20,000\\n• Flooring: $3-12 per sq ft\\n\\nWhat's your comfortable investment range for this project?"

    # Default response
    return "I understand you're interested in a home improvement project. To help match you with the best local contractors, could you tell me a bit more about what you're planning? For example, what type of project is it and what's prompting you to move forward with it now?"
