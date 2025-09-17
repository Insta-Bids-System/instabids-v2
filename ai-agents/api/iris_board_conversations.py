"""
IRIS Board Conversations API - Persistent Board-Specific IRIS Dialogs
Enables continuous IRIS conversations within each inspiration board
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from openai import OpenAI
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import database for direct access
from database import SupabaseDB

# Load environment variables
load_dotenv(override=True)

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
        # Test the API key
        test_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
            max_completion_tokens=1
        )
        logger.info("OpenAI API key validated successfully")
    except Exception as e:
        logger.warning(f"OpenAI API key invalid: {e}")
        logger.warning("Using fallback responses instead")
        client = None

class BoardPhotoAnalysisRequest(BaseModel):
    board_id: str
    user_id: str
    image_url: str
    category: str  # "current", "inspiration", "vision"
    user_message: Optional[str] = None

class BoardConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    triggered_by_photo: Optional[str] = None
    confidence_score: Optional[float] = None

class BoardConversationResponse(BaseModel):
    board_id: str
    messages: List[BoardConversationMessage]
    current_confidence_score: float
    bid_readiness_status: str  # "insufficient", "building", "ready"
    project_summary: Optional[Dict[str, Any]] = None

class PhotoAnalysisResponse(BaseModel):
    analysis: str
    confidence_score: float
    bid_readiness_status: str
    project_insights: Dict[str, Any]
    conversation_id: str

@router.post("/board/{board_id}/analyze-photo", response_model=PhotoAnalysisResponse)
async def analyze_board_photo(board_id: str, request: BoardPhotoAnalysisRequest):
    """
    Analyze a new photo added to an inspiration board and update the persistent conversation
    """
    try:
        logger.info(f"Analyzing photo for board {board_id}")
        
        # 1. Get existing board and conversation context
        board_info = await get_board_with_context(board_id)
        if not board_info:
            raise HTTPException(status_code=404, detail="Board not found")
        
        # 2. Get or create conversation for this board
        conversation_id = await get_or_create_board_conversation(board_id, request.user_id)
        
        # 3. Get existing conversation context
        conversation_history = await get_board_conversation_history(conversation_id)
        
        # 4. Analyze the new photo in context
        analysis_result = await analyze_photo_with_context(
            board_info=board_info,
            new_photo_url=request.image_url,
            category=request.category,
            user_message=request.user_message,
            conversation_history=conversation_history
        )
        
        # 5. Update the conversation with the analysis
        await add_message_to_board_conversation(
            conversation_id=conversation_id,
            role="assistant",
            content=analysis_result["analysis"],
            triggered_by_photo=request.image_url,
            confidence_score=analysis_result["confidence_score"]
        )
        
        # 6. Update board insights and confidence
        await update_board_insights(
            board_id=board_id,
            confidence_score=analysis_result["confidence_score"],
            project_insights=analysis_result["project_insights"]
        )
        
        return PhotoAnalysisResponse(
            analysis=analysis_result["analysis"],
            confidence_score=analysis_result["confidence_score"],
            bid_readiness_status=analysis_result["bid_readiness_status"],
            project_insights=analysis_result["project_insights"],
            conversation_id=conversation_id
        )
        
    except Exception as e:
        logger.error(f"Error analyzing board photo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/board/{board_id}/conversation", response_model=BoardConversationResponse)
async def get_board_conversation(board_id: str):
    """
    Get the complete persistent conversation for an inspiration board
    """
    try:
        # Get board info
        board_info = await get_board_with_context(board_id)
        if not board_info:
            raise HTTPException(status_code=404, detail="Board not found")
        
        # Get conversation
        conversation = await get_board_conversation_by_board_id(board_id)
        
        messages = []
        confidence_score = 0.0
        bid_readiness_status = "insufficient"
        project_summary = None
        
        if conversation:
            messages = await get_board_conversation_messages(conversation["id"])
            
            # Calculate current confidence score from latest messages
            if messages:
                latest_scores = [m.confidence_score for m in messages if m.confidence_score is not None]
                if latest_scores:
                    confidence_score = latest_scores[-1]
            
            # Determine bid readiness status
            bid_readiness_status = determine_bid_readiness(confidence_score, len(messages))
            
            # Get project summary if ready
            if confidence_score >= 0.75:
                project_summary = await generate_project_summary(board_id, messages)
        
        return BoardConversationResponse(
            board_id=board_id,
            messages=messages,
            current_confidence_score=confidence_score,
            bid_readiness_status=bid_readiness_status,
            project_summary=project_summary
        )
        
    except Exception as e:
        logger.error(f"Error getting board conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/board/{board_id}/create-bid-card")
async def create_bid_card_from_board(board_id: str):
    """
    Create a bid card from the accumulated board context when ready
    """
    try:
        # Get board conversation with high confidence
        conversation_response = await get_board_conversation(board_id)
        
        if conversation_response.current_confidence_score < 0.75:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient context for bid card creation. Current confidence: {conversation_response.current_confidence_score:.2f}, need: 0.75+"
            )
        
        # Use the existing IRIS project push system
        from api.iris_chat_unified_fixed import create_project_from_board_context
        
        project_result = await create_project_from_board_context(
            board_id=board_id,
            conversation_messages=conversation_response.messages,
            project_summary=conversation_response.project_summary
        )
        
        return {
            "success": True,
            "project_id": project_result["project_id"],
            "cia_session_id": project_result["cia_session_id"],
            "confidence_score": conversation_response.current_confidence_score,
            "message": "Bid card created successfully from board context"
        }
        
    except Exception as e:
        logger.error(f"Error creating bid card from board: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

async def get_board_with_context(board_id: str) -> Optional[Dict[str, Any]]:
    """Get board info with images and existing context"""
    try:
        # Get board info
        board_result = db.client.table("inspiration_boards").select("*").eq("id", board_id).execute()
        
        if not board_result.data:
            return None
        
        board = board_result.data[0]
        
        # Get board images
        images_result = db.client.table("inspiration_images").select("*").eq("board_id", board_id).execute()
        
        board["images"] = images_result.data if images_result.data else []
        
        return board
        
    except Exception as e:
        logger.error(f"Error getting board context: {e}")
        return None

async def get_or_create_board_conversation(board_id: str, user_id: str) -> str:
    """Get existing or create new conversation for board"""
    try:
        # Check for existing conversation
        existing = db.client.table("inspiration_conversations").select("*").eq("board_id", board_id).execute()
        
        if existing.data:
            return existing.data[0]["id"]
        
        # Create new conversation
        conversation_id = str(uuid.uuid4())
        
        conversation_data = {
            "id": conversation_id,
            "user_id": user_id,
            "board_id": board_id,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = db.client.table("inspiration_conversations").insert(conversation_data).execute()
        
        if result.data:
            return conversation_id
        else:
            raise Exception("Failed to create conversation")
            
    except Exception as e:
        logger.error(f"Error creating board conversation: {e}")
        raise

async def get_board_conversation_history(conversation_id: str) -> List[Dict[str, Any]]:
    """Get conversation message history"""
    try:
        result = db.client.table("inspiration_conversations").select("messages").eq("id", conversation_id).execute()
        
        if result.data and result.data[0]["messages"]:
            return result.data[0]["messages"]
        
        return []
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return []

async def analyze_photo_with_context(
    board_info: Dict[str, Any],
    new_photo_url: str, 
    category: str,
    user_message: Optional[str],
    conversation_history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze new photo in context of board and conversation history"""
    
    if not client:
        # Fallback response when OpenAI unavailable
        return {
            "analysis": f"I see you've added a new {category} photo to your {board_info.get('room_type', 'project')} board. This looks like it fits well with your vision.",
            "confidence_score": min(0.1 * len(conversation_history) + 0.3, 0.9),
            "bid_readiness_status": "building",
            "project_insights": {
                "room_type": board_info.get("room_type", "unknown"),
                "style_preferences": ["modern"],
                "estimated_timeline": "2-4 weeks",
                "estimated_budget_range": "$15,000-$45,000"
            }
        }
    
    try:
        # Build context for GPT analysis
        context_prompt = build_board_analysis_prompt(
            board_info=board_info,
            category=category,
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        messages = [
            {"role": "system", "content": context_prompt},
            {"role": "user", "content": f"Analyze this new {category} photo and provide insights: {new_photo_url}"}
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_completion_tokens=500,
            temperature=0.7
        )
        
        analysis_text = response.choices[0].message.content
        
        # Calculate confidence score based on context and analysis quality
        confidence_score = calculate_confidence_score(
            conversation_history=conversation_history,
            board_images_count=len(board_info.get("images", [])),
            analysis_quality=len(analysis_text.split())
        )
        
        # Extract project insights
        project_insights = extract_project_insights(analysis_text, board_info)
        
        # Determine bid readiness
        bid_readiness_status = determine_bid_readiness(confidence_score, len(conversation_history))
        
        return {
            "analysis": analysis_text,
            "confidence_score": confidence_score,
            "bid_readiness_status": bid_readiness_status,
            "project_insights": project_insights
        }
        
    except Exception as e:
        logger.error(f"Error in GPT analysis: {e}")
        # Fallback to simple analysis
        return {
            "analysis": f"I've analyzed your new {category} photo. Based on what I can see, this fits well with your {board_info.get('room_type', 'project')} vision.",
            "confidence_score": min(0.1 * len(conversation_history) + 0.2, 0.8),
            "bid_readiness_status": "building",
            "project_insights": {
                "room_type": board_info.get("room_type", "unknown"),
                "analysis_status": "basic_analysis_due_to_api_error"
            }
        }

def build_board_analysis_prompt(
    board_info: Dict[str, Any],
    category: str,
    user_message: Optional[str],
    conversation_history: List[Dict[str, Any]]
) -> str:
    """Build the context prompt for photo analysis"""
    
    prompt = f"""You are IRIS, an AI design assistant analyzing photos for an inspiration board.

BOARD CONTEXT:
- Board Title: {board_info.get('title', 'Untitled')}
- Room Type: {board_info.get('room_type', 'General')}
- Current Status: {board_info.get('status', 'collecting')}
- Total Images: {len(board_info.get('images', []))}

CONVERSATION HISTORY:
"""
    
    for i, msg in enumerate(conversation_history[-5:]):  # Last 5 messages for context
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')[:200]  # Truncate long messages
        prompt += f"- {role}: {content}\n"
    
    prompt += f"""
NEW PHOTO CATEGORY: {category}
USER MESSAGE: {user_message or 'No specific message'}

YOUR TASK:
1. Analyze this new photo in the context of the existing board and conversation
2. Provide insights about how it fits with the overall project vision
3. Comment on style, materials, colors, or functionality as relevant
4. If this is building toward a clear project direction, mention next steps
5. Be conversational and helpful, building on previous observations

Keep response under 300 words and be specific about what you observe.
"""
    
    return prompt

def calculate_confidence_score(
    conversation_history: List[Dict[str, Any]], 
    board_images_count: int, 
    analysis_quality: int
) -> float:
    """Calculate confidence score for bid readiness"""
    
    base_score = 0.0
    
    # Factor 1: Number of conversation turns (more context = higher confidence)
    conversation_factor = min(len(conversation_history) * 0.1, 0.4)  # Up to 0.4 for 4+ conversations
    
    # Factor 2: Number of images (more images = better understanding)
    image_factor = min(board_images_count * 0.05, 0.3)  # Up to 0.3 for 6+ images
    
    # Factor 3: Analysis quality (longer analysis = more insights)
    quality_factor = min(analysis_quality / 100, 0.3)  # Up to 0.3 for detailed analysis
    
    total_score = base_score + conversation_factor + image_factor + quality_factor
    
    # Cap at 0.95 (never 100% certain until human review)
    return min(total_score, 0.95)

def determine_bid_readiness(confidence_score: float, conversation_turns: int) -> str:
    """Determine if board is ready for bid card creation"""
    
    if confidence_score >= 0.75 and conversation_turns >= 3:
        return "ready"
    elif confidence_score >= 0.4 or conversation_turns >= 2:
        return "building"
    else:
        return "insufficient"

def extract_project_insights(analysis_text: str, board_info: Dict[str, Any]) -> Dict[str, Any]:
    """Extract structured insights from analysis text"""
    
    # Basic insights based on board info and analysis
    insights = {
        "room_type": board_info.get("room_type", "unknown"),
        "last_analysis_length": len(analysis_text),
        "analysis_timestamp": datetime.now().isoformat()
    }
    
    # Simple keyword extraction for style preferences
    style_keywords = ["modern", "farmhouse", "traditional", "contemporary", "rustic", "industrial", "minimalist"]
    found_styles = [style for style in style_keywords if style.lower() in analysis_text.lower()]
    if found_styles:
        insights["detected_styles"] = found_styles
    
    # Basic budget estimation based on room type
    if board_info.get("room_type") == "kitchen":
        insights["estimated_budget_range"] = "$25,000-$75,000"
        insights["estimated_timeline"] = "6-10 weeks"
    elif board_info.get("room_type") == "bathroom":
        insights["estimated_budget_range"] = "$15,000-$40,000" 
        insights["estimated_timeline"] = "4-6 weeks"
    else:
        insights["estimated_budget_range"] = "$10,000-$50,000"
        insights["estimated_timeline"] = "3-8 weeks"
    
    return insights

async def add_message_to_board_conversation(
    conversation_id: str,
    role: str,
    content: str,
    triggered_by_photo: Optional[str] = None,
    confidence_score: Optional[float] = None
):
    """Add a message to the board conversation"""
    try:
        # Get current messages
        current = db.client.table("inspiration_conversations").select("messages").eq("id", conversation_id).execute()
        
        current_messages = current.data[0]["messages"] if current.data and current.data[0]["messages"] else []
        
        # Add new message
        new_message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "triggered_by_photo": triggered_by_photo,
            "confidence_score": confidence_score
        }
        
        current_messages.append(new_message)
        
        # Update conversation
        update_result = db.client.table("inspiration_conversations").update({
            "messages": current_messages,
            "updated_at": datetime.now().isoformat()
        }).eq("id", conversation_id).execute()
        
        if not update_result.data:
            raise Exception("Failed to update conversation")
            
    except Exception as e:
        logger.error(f"Error adding message to conversation: {e}")
        raise

async def update_board_insights(
    board_id: str, 
    confidence_score: float, 
    project_insights: Dict[str, Any]
):
    """Update board with latest insights and confidence score"""
    try:
        insights_data = {
            "confidence_score": confidence_score,
            "project_insights": project_insights,
            "last_updated": datetime.now().isoformat()
        }
        
        result = db.client.table("inspiration_boards").update({
            "ai_insights": insights_data,
            "updated_at": datetime.now().isoformat()
        }).eq("id", board_id).execute()
        
        if not result.data:
            logger.warning(f"Failed to update board insights for {board_id}")
            
    except Exception as e:
        logger.error(f"Error updating board insights: {e}")

async def get_board_conversation_by_board_id(board_id: str) -> Optional[Dict[str, Any]]:
    """Get conversation by board ID"""
    try:
        result = db.client.table("inspiration_conversations").select("*").eq("board_id", board_id).execute()
        
        if result.data:
            return result.data[0]
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting board conversation: {e}")
        return None

async def get_board_conversation_messages(conversation_id: str) -> List[BoardConversationMessage]:
    """Get conversation messages as properly formatted objects"""
    try:
        result = db.client.table("inspiration_conversations").select("messages").eq("id", conversation_id).execute()
        
        if result.data and result.data[0]["messages"]:
            messages = []
            for msg_data in result.data[0]["messages"]:
                message = BoardConversationMessage(
                    role=msg_data.get("role", "assistant"),
                    content=msg_data.get("content", ""),
                    timestamp=datetime.fromisoformat(msg_data.get("timestamp", datetime.now().isoformat())),
                    triggered_by_photo=msg_data.get("triggered_by_photo"),
                    confidence_score=msg_data.get("confidence_score")
                )
                messages.append(message)
            return messages
        
        return []
        
    except Exception as e:
        logger.error(f"Error getting conversation messages: {e}")
        return []

async def generate_project_summary(board_id: str, messages: List[BoardConversationMessage]) -> Dict[str, Any]:
    """Generate project summary when confidence is high enough"""
    try:
        # Get board info
        board_info = await get_board_with_context(board_id)
        
        if not board_info:
            return {}
        
        # Compile conversation insights
        conversation_content = ""
        latest_insights = None
        
        for msg in messages:
            if msg.role == "assistant":
                conversation_content += f"{msg.content}\n"
                if msg.confidence_score and msg.confidence_score > 0.6:
                    # This is a high-confidence analysis message
                    pass
        
        # Basic project summary
        summary = {
            "board_title": board_info.get("title", "Untitled Project"),
            "room_type": board_info.get("room_type", "General"),
            "total_images": len(board_info.get("images", [])),
            "conversation_turns": len(messages),
            "last_updated": datetime.now().isoformat()
        }
        
        # Add insights from latest board analysis
        if board_info.get("ai_insights") and board_info["ai_insights"].get("project_insights"):
            summary.update(board_info["ai_insights"]["project_insights"])
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating project summary: {e}")
        return {}