"""
CIA Routes - Universal Streaming Endpoint with ALL Features
Owner: Agent 1 (Frontend Flow)
Version: GPT-5 Vision Enabled
"""

import logging
import os
import json
import asyncio
from datetime import datetime
from typing import Any, Optional, List, Dict
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import requests
import re
from dotenv import load_dotenv

# Load environment variables from root .env
root_env = Path(__file__).parent.parent.parent / '.env'
if root_env.exists():
    load_dotenv(root_env, override=True)

# Import CIA agent and related models
from agents.cia.agent import CustomerInterfaceAgent
# Define OPENING_MESSAGE here since prompts.py was removed
OPENING_MESSAGE = """Hi! I'm Alex, your project assistant at InstaBids. Here's what makes us different: We eliminate the expensive lead fees and wasted sales meetings that drive up costs on other platforms. Instead, contractors and homeowners interact directly through our app using photos and conversations to create solid quotes - no sales meetings needed. This keeps all the money savings between you and your contractor, not going to corporations. Contractors save on lead costs and sales time, so they can offer you better prices.

What kind of home project brings you here today? If you have photos of the area or issue, that would be perfect to get started!"""
from database_simple import db
from services.llm_cost_tracker import LLMCostTracker
from config.service_urls import get_backend_url

logger = logging.getLogger(__name__)

def extract_exact_dates(text: str) -> dict:
    """Extract exact dates from user text for bid deadlines and project completion"""
    import datetime as dt
    from dateutil import parser
    
    text_lower = text.lower()
    dates = {}
    
    # Pattern: "bids by [date]" or "all bids by [date]"  
    bid_deadline_patterns = [
        r"(?:all )?bids? (?:in )?by (.*?)(?:[,.]|$)",
        r"need (?:all )?bids? by (.*?)(?:[,.]|$)",
        r"(?:want|need) (?:to get|to have) (?:all )?bids? by (.*?)(?:[,.]|$)",
        r"bids? (?:must be )?in by (.*?)(?:[,.]|$)"
    ]
    
    # Pattern: "done by [date]" or "finished by [date]" or "completed by [date]"
    project_deadline_patterns = [
        r"(?:done|finished|completed) by (.*?)(?:[,.]|$)",
        r"(?:must be|needs to be|has to be) (?:done|finished|completed) by (.*?)(?:[,.]|$)",
        r"(?:project|work) (?:done|finished|completed) by (.*?)(?:[,.]|$)",
        r"before (.*?)(?:[,.]|$)",
        r"by (.*?)(?:[,.]|$)" # Generic "by" pattern - less specific
    ]
    
    # Event-driven deadlines
    event_patterns = [
        r"before (?:my|our|the) (wedding|party|event|holiday|vacation|move|moving) (?:on )?(.*?)(?:[,.]|$)",
        r"for (?:my|our|the) (wedding|party|event|holiday) (?:on )?(.*?)(?:[,.]|$)"
    ]
    
    def parse_date_text(date_text: str) -> tuple[dt.date, bool, str]:
        """Parse date text and return (date, is_hard_deadline, context)"""
        date_text = date_text.strip()
        if not date_text:
            return None, False, ""
        
        # Hard deadline indicators
        hard_indicators = ["must", "has to", "needs to", "required", "deadline", "storm", "emergency"]
        is_hard = any(indicator in text_lower for indicator in hard_indicators)
        
        try:
            # Handle relative dates like "Friday", "next week", "Christmas"
            if "friday" in date_text.lower():
                # Find next Friday
                today = dt.date.today()
                days_ahead = (4 - today.weekday()) % 7  # Friday is 4
                if days_ahead == 0:  # Today is Friday
                    days_ahead = 7  # Next Friday
                return today + dt.timedelta(days=days_ahead), is_hard, date_text
            
            elif "christmas" in date_text.lower():
                current_year = dt.date.today().year
                christmas = dt.date(current_year, 12, 25)
                if christmas < dt.date.today():
                    christmas = dt.date(current_year + 1, 12, 25)
                return christmas, is_hard, "Christmas"
            
            elif "wedding" in date_text.lower():
                # Extract wedding date if mentioned
                wedding_match = re.search(r"(?:on )?([\w\s,]+?)(?:\s|$)", date_text)
                if wedding_match:
                    wedding_text = wedding_match.group(1)
                    try:
                        wedding_date = parser.parse(wedding_text).date()
                        return wedding_date, True, f"wedding on {wedding_text}"
                    except:
                        pass
                
            else:
                # Try to parse as standard date
                parsed_date = parser.parse(date_text).date()
                return parsed_date, is_hard, date_text
                
        except Exception as e:
            logger.debug(f"Could not parse date: '{date_text}' - {e}")
            
        return None, is_hard, date_text
    
    # Extract bid collection deadlines
    for pattern in bid_deadline_patterns:
        match = re.search(pattern, text_lower)
        if match:
            date_text = match.group(1)
            parsed_date, is_hard, context = parse_date_text(date_text)
            if parsed_date:
                dates["bid_collection_deadline"] = parsed_date.isoformat()
                dates["deadline_hard"] = is_hard
                dates["deadline_context"] = f"bids needed by {context}"
                break
    
    # Extract project completion deadlines  
    for pattern in project_deadline_patterns:
        match = re.search(pattern, text_lower)
        if match:
            date_text = match.group(1)
            parsed_date, is_hard, context = parse_date_text(date_text)
            if parsed_date:
                dates["project_completion_deadline"] = parsed_date.isoformat()
                if "deadline_hard" not in dates:  # Don't override bid deadline hardness
                    dates["deadline_hard"] = is_hard
                if "deadline_context" not in dates:
                    dates["deadline_context"] = f"completion by {context}"
                break
    
    # Extract event-driven deadlines
    for pattern in event_patterns:
        match = re.search(pattern, text_lower)
        if match:
            event_type = match.group(1)
            date_text = match.group(2) if len(match.groups()) > 1 else ""
            parsed_date, is_hard, context = parse_date_text(date_text)
            if parsed_date:
                dates["project_completion_deadline"] = parsed_date.isoformat()
                dates["deadline_hard"] = True  # Events are usually hard deadlines
                dates["deadline_context"] = f"before {event_type} on {context}"
                break
    
    return dates

# Create router
router = APIRouter()

# Pydantic models for request/response
class ChatMessage(BaseModel):
    message: str
    images: Optional[list[str]] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    rfi_context: Optional[dict] = None  # For RFI-triggered conversations

class ChatResponse(BaseModel):
    response: str
    session_id: str
    current_phase: str
    ready_for_jaa: bool
    missing_fields: list[str]
    collected_info: Optional[dict[str, Any]] = None
    messages: Optional[list[dict[str, Any]]] = None

class SSEChatRequest(BaseModel):
    messages: list
    conversation_id: str
    user_id: str
    max_tokens: Optional[int] = 500
    model_preference: Optional[str] = "gpt-5"
    project_id: Optional[str] = None  # Support project context
    rfi_context: Optional[dict] = None  # Support RFI context
    images: Optional[list[str]] = None  # Support image uploads
    session_id: Optional[str] = None  # Support session tracking

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

# Global CIA agent instance (initialized in main.py)
cia_agent: Optional[CustomerInterfaceAgent] = None

# Cost tracking instance
cost_tracker = LLMCostTracker()

def set_cia_agent(agent: CustomerInterfaceAgent):
    """Set the CIA agent instance"""
    global cia_agent
    cia_agent = agent

@router.get("/opening-message")
async def get_opening_message():
    """Get the pre-loaded opening message for the chat UI"""
    return {
        "success": True,
        "message": OPENING_MESSAGE,
        "timestamp": datetime.now().isoformat()
    }

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

@router.post("/stream")
async def cia_universal_stream(request: SSEChatRequest):
    """
    Universal CIA Streaming Chat Endpoint
    Features:
    - GPT-5 with vision support
    - Full project context loading
    - RFI context handling
    - Image analysis and processing  
    - Real-time SSE streaming
    - Complete CIA agent integration
    - Supabase state persistence
    """
    logger.info(f"CIA universal stream called with message: {request.messages[-1] if request.messages else 'no message'}")
    
    if not cia_agent:
        logger.error("CIA agent not initialized")
        raise HTTPException(
            status_code=503, 
            detail="CIA agent not initialized. Check OpenAI API key configuration."
        )
    
    async def generate_universal_sse_stream():
        try:
            logger.info("Starting universal SSE stream generation")
            
            # Extract user info with enhanced session handling
            if not request.user_id or request.user_id == "00000000-0000-0000-0000-000000000000":
                user_id = "00000000-0000-0000-0000-000000000000" 
                session_id = request.conversation_id or f"anon_{datetime.now().timestamp()}"
            else:
                user_id = request.user_id
                session_id = request.conversation_id or f"auth_{user_id}_{datetime.now().timestamp()}"
            
            # Extract latest message and images
            latest_message = ""
            images = []
            if request.messages:
                last_msg = request.messages[-1]
                latest_message = last_msg.get("content", "")
                # First check for images in the message
                images = last_msg.get("images", [])
            
            # If no images in message, check request level (where they're actually sent)
            if not images and request.images:
                images = request.images
                logger.info(f"Found {len(images)} images at request level")
            
            logger.info(f"Processing message: {latest_message[:100]} with {len(images)} images")
            
            # === PROJECT CONTEXT LOADING ===
            project_id = request.project_id
            bid_card_context = None
            if project_id:
                try:
                    logger.info(f"Loading project context for: {project_id}")
                    # Use async to avoid blocking
                    bid_card_result = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: db.client.table("bid_cards").select("*").eq("id", project_id).execute()
                    )
                    if bid_card_result.data:
                        bid_card_context = bid_card_result.data[0]
                        logger.info(f"Loaded bid card: {bid_card_context.get('bid_card_number')}")
                        
                        # Verify user access if authenticated
                        if user_id != "00000000-0000-0000-0000-000000000000":
                            # Use async to avoid blocking
                            homeowner_result = await asyncio.get_event_loop().run_in_executor(
                                None,
                                lambda: db.client.table("homeowners").select("id").eq("user_id", user_id).execute()
                            )
                            if homeowner_result.data:
                                user_id = homeowner_result.data[0]["id"]
                                if bid_card_context.get("user_id") != user_id:
                                    yield f"data: {json.dumps({'error': 'Bid card access denied'})}\n\n"
                                    return
                                logger.info(f"Verified bid card access for homeowner {user_id}")
                except Exception as e:
                    logger.warning(f"Project context loading error: {e}")
            
            # === RFI CONTEXT HANDLING ===
            if request.rfi_context:
                logger.info(f"RFI context detected: {request.rfi_context}")
                rfi_msg = format_rfi_context_message(request.rfi_context)
                latest_message = f"{rfi_msg}\n\n{latest_message}"
                
                # Handle RFI photo uploads
                if images and request.rfi_context.get("bid_card_id"):
                    await handle_rfi_photo_upload(
                        bid_card_id=request.rfi_context["bid_card_id"],
                        rfi_id=request.rfi_context.get("rfi_id"),
                        photos=images,
                        user_id=user_id
                    )
            
            # === IMAGE ANALYSIS INTEGRATION ===
            image_context = ""
            if images and not request.rfi_context:  # Only analyze non-RFI images
                try:
                    from agents.cia.image_integration import cia_image_integration
                    
                    # Analyze images for bid card context
                    project_context = {
                        "property_area": bid_card_context.get("project_type", "Unknown") if bid_card_context else "Unknown",
                        "user_notes": latest_message
                    }
                    
                    analysis_results = await cia_image_integration.analyze_images_with_context(
                        images, project_context
                    )
                    
                    # Format analysis for conversation context
                    image_context = cia_image_integration.format_image_context_for_conversation(analysis_results)
                    logger.info(f"Image analysis completed: {image_context}")
                    
                    # If we have a potential bid card ID, update it with image data
                    if hasattr(request, 'potential_bid_card_id') and request.potential_bid_card_id:
                        # Get the image URLs from the upload system
                        # (assuming images are already uploaded to Supabase Storage)
                        image_urls = images  # These should be URLs after upload
                        await cia_image_integration.update_potential_bid_card_with_images(
                            request.potential_bid_card_id,
                            image_urls,
                            analysis_results
                        )
                    
                except Exception as e:
                    logger.error(f"Image analysis failed: {e}")
                    image_context = f"Images uploaded ({len(images)} files) - analysis pending"
            
            # === FULL CIA AGENT INTEGRATION ===
            # Load existing conversation state
            existing_conversation = await db.load_conversation_state(session_id)
            if existing_conversation:
                # Extract state - could be nested or at top level
                if "state" in existing_conversation:
                    existing_state = existing_conversation.get("state", {})
                else:
                    existing_state = existing_conversation
                    
                logger.info(f"Loaded existing state for session {session_id}")
                logger.info(f"State type: {type(existing_state)}")
                logger.info(f"State keys: {existing_state.keys() if isinstance(existing_state, dict) else 'Not a dict'}")
                
                # Check for messages in both locations
                messages_found = False
                if isinstance(existing_state, dict) and "messages" in existing_state:
                    logger.info(f"Found {len(existing_state['messages'])} messages in state")
                    messages_found = True
                elif isinstance(existing_conversation, dict) and "messages" in existing_conversation:
                    logger.info(f"Found {len(existing_conversation['messages'])} messages at top level")
                    # Move messages to state for consistency
                    if isinstance(existing_state, dict):
                        existing_state["messages"] = existing_conversation["messages"]
                        messages_found = True
                
                if not messages_found:
                    logger.info("No messages found in loaded conversation")
            else:
                existing_state = None
                logger.info(f"Starting new conversation for session {session_id}")
            
            # Enhance state with context
            if existing_state and bid_card_context:
                existing_state["bid_card_context"] = bid_card_context
                existing_state["project_id"] = project_id
            elif bid_card_context:
                existing_state = {
                    "bid_card_context": bid_card_context,
                    "project_id": project_id
                }
            
            # === SIMPLIFIED GPT-4O STREAMING ===
            from openai import AsyncOpenAI
            skip_state_management = False  # Initialize flag
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("No OpenAI API key found")
                yield f"data: {json.dumps({'error': 'No OpenAI API key configured'})}\n\n"
                return
            
            logger.info(f"Creating OpenAI client for GPT-4o streaming")
            openai_client = AsyncOpenAI(api_key=api_key)
            
            # Prepare content for OpenAI chat completions
            input_content = []
            
            # Add text content
            input_content.append({
                "type": "text", 
                "text": latest_message
            })
            
            # Add image content if provided (OpenAI format)
            if images:
                for image_url in images:
                    # Ensure proper data URI format for OpenAI
                    if not image_url.startswith("data:"):
                        image_url = f"data:image/jpeg;base64,{image_url}"
                    input_content.append({
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    })
                logger.info(f"Added {len(images)} images to OpenAI input")
            
            # Get the proper CIA system prompt
            from agents.cia.UNIFIED_PROMPT_FINAL import UNIFIED_CIA_PROMPT
            
            # Use regular conversational prompt for GPT-4o (no JSON requirement)
            system_prompt = UNIFIED_CIA_PROMPT
            
            # Add context but NOT conversation history (since we'll add it as messages)
            enhanced_prompt = system_prompt
            
            if bid_card_context:
                enhanced_prompt += f"\n\nProject Context: Working on {bid_card_context.get('project_type', 'project')} for bid card {bid_card_context.get('bid_card_number', 'N/A')}"
            
            if image_context:
                enhanced_prompt += f"\n\nImage Analysis: {image_context}"
            
            # Stream response using GPT-4o (simplified for reliability)
            accumulated_response = ""
            model_used = "gpt-4o"
            
            logger.info("Starting GPT-4o streaming...")
            
            # Build messages array with conversation history
            messages = []
            
            # Add system message
            messages.append({
                "role": "system",
                "content": enhanced_prompt
            })
            
            # Add conversation history if available
            if existing_state and "messages" in existing_state:
                logger.info(f"Loading {len(existing_state['messages'])} messages from conversation history")
                # Log each message for debugging
                for i, msg in enumerate(existing_state["messages"], 1):
                    logger.info(f"History message {i}: role={msg.get('role')}, content_preview={msg.get('content', '')[:100]}...")
                    if msg.get("role") in ["user", "assistant"]:
                        messages.append({
                            "role": msg["role"],
                            "content": msg.get("content", "")
                        })
                logger.info(f"Total messages in array after loading history: {len(messages)}")
            else:
                logger.info("No conversation history found in state")
            
            # Add current user message
            # If we have images, use the structured content, otherwise just the text
            if images:
                messages.append({
                    "role": "user",
                    "content": input_content
                })
            else:
                messages.append({
                    "role": "user",
                    "content": latest_message
                })
            
            # Log the messages being sent to GPT-4o for debugging
            logger.info(f"Sending {len(messages)} messages to GPT-4o")
            logger.info(f"System message length: {len(messages[0]['content']) if messages else 0} chars")
            if len(messages) > 1:
                logger.info(f"Conversation has {len(messages) - 1} additional messages")
                # Log first few messages for debugging (not full content to avoid spam)
                for i, msg in enumerate(messages[1:4], 1):  # Show first 3 non-system messages
                    logger.info(f"Message {i}: {msg['role']} - {msg['content'][:50] if msg.get('content') else 'No content'}...")
            
            # ARCHITECTURAL FIX: Use CIA agent instead of direct OpenAI calls
            # This fixes the critical routing bug mentioned in the README
            logger.info("Using CIA agent for conversation handling")
            
            try:
                result = await asyncio.wait_for(
                    cia_agent.handle_conversation(
                        user_id=user_id,
                        message=latest_message,
                        session_id=session_id,
                        project_id=project_id
                    ),
                    timeout=120.0  # Timeout for GPT-4o processing
                )
                logger.info("CIA agent conversation completed successfully")
                
                # Extract the response from the result
                cia_response = result.get("response", "I'm processing your request...")
                tool_calls_data = result.get("tool_calls", [])
                bid_card_id = result.get("bid_card_id", None)
                
            except asyncio.TimeoutError:
                logger.warning("CIA agent conversation timed out after 120s")
                cia_response = "I'm still processing your request. Please try again in a moment."
                tool_calls_data = []
                bid_card_id = None
            except Exception as agent_error:
                logger.error(f"CIA agent error: {agent_error}")
                cia_response = "I encountered an issue processing your request. Let me try again."
                tool_calls_data = []
                bid_card_id = None
            
            logger.info("CIA agent result obtained successfully")
            
            # Stream the CIA agent response in chunks to simulate streaming
            response_words = cia_response.split()
            accumulated_response = ""
            
            # Send response in chunks to maintain streaming experience
            chunk_size = 5  # Send 5 words at a time
            for i in range(0, len(response_words), chunk_size):
                chunk_words = response_words[i:i+chunk_size]
                chunk_text = " ".join(chunk_words) + " "
                accumulated_response += chunk_text
                
                chunk_data = {
                    "type": "message",
                    "content": chunk_text
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
                await asyncio.sleep(0.05)  # Small delay for streaming effect
            
            # Send tool calls if any were made by the CIA agent
            if tool_calls_data:
                for tool_call in tool_calls_data:
                    tool_data = {
                        "type": "tool_call",
                        "tool_name": tool_call.get("tool_name", "unknown"),
                        "arguments": tool_call.get("arguments", {})
                    }
                    yield f"data: {json.dumps(tool_data)}\n\n"
                    logger.info(f"Sent tool call: {tool_call.get('tool_name')}")
            
            # Send bid card update if one was created
            if bid_card_id:
                bid_card_data = {
                    "type": "bid_card_update", 
                    "bid_card_id": bid_card_id
                }
                yield f"data: {json.dumps(bid_card_data)}\n\n"
                logger.info(f"Sent bid card update: {bid_card_id}")
            
            # Track costs for CIA agent usage
            logger.info("COST_TRACKING_DEBUG: About to track CIA agent costs")
            try:
                from services.llm_cost_tracker import cost_tracker
                cost_tracker.track_llm_call_sync(
                    agent_name="CIA",
                    provider="openai", 
                    model="gpt-4o",
                    input_tokens=len(latest_message) // 4,  # Rough estimate
                    output_tokens=len(cia_response) // 4,   # Rough estimate
                    duration_ms=0,
                    context={
                        "user_id": user_id,
                        "conversation_id": session_id,
                        "via_agent": True
                    }
                )
                logger.info(f"Cost tracking logged for CIA agent usage")
            except Exception as track_error:
                logger.warning(f"Cost tracking failed: {track_error}")
                
        except Exception as stream_error:
            logger.error(f"CIA streaming error: {stream_error}")
            error_data = {
                "error": f"CIA agent error: {str(stream_error)}"
            }
            yield f"data: {json.dumps(error_data)}\n\n"
        
        finally:
            logger.info("Sending [DONE] marker to complete stream")
            yield "data: [DONE]\n\n"
            logger.info("Stream completed with [DONE] marker")
    
    return StreamingResponse(
        generate_universal_sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )
