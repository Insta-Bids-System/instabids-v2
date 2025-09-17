"""
IRIS API Routes
Clean FastAPI routes that delegate to the main agent orchestrator
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
import uuid

from ..models.requests import (
    UnifiedChatRequest, 
    ContextRequest, 
    BidCardUpdateRequest,
    RepairItemRequest,
    ToolSuggestionRequest
)
from ..models.responses import IRISResponse, ContextResponse

logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/api/iris", tags=["IRIS"])

# Import agent at module level to avoid circular imports
_iris_agent = None

def get_iris_agent():
    """Lazy import of IRIS agent to avoid circular imports"""
    global _iris_agent
    if _iris_agent is None:
        from ..agent import IRISAgent
        _iris_agent = IRISAgent()
    return _iris_agent

@router.post("/unified-chat", response_model=IRISResponse)
async def unified_chat(request: UnifiedChatRequest, background_tasks: BackgroundTasks):
    """
    Main IRIS conversation endpoint
    Handles all chat interactions including image uploads and design consultation
    """
    try:
        logger.info(f"IRIS chat request from user {request.user_id}")
        
        agent = get_iris_agent()
        response = await agent.handle_unified_chat(request)
        
        # Add background tasks if needed (e.g., analytics, notifications)
        background_tasks.add_task(log_conversation_metrics, request, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in unified chat: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/context/{user_id}", response_model=ContextResponse)
async def get_user_context(user_id: str, project_id: Optional[str] = None):
    """
    Get comprehensive user context for IRIS
    Includes inspiration boards, project context, design preferences, etc.
    """
    try:
        logger.info(f"Context request for user {user_id}")
        
        agent = get_iris_agent()
        context = await agent.get_user_context(user_id, project_id)
        
        return context
        
    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving context: {str(e)}")

@router.post("/suggest-tool/{tool_name}")
async def suggest_tool(tool_name: str, request: ToolSuggestionRequest):
    """
    Get tool-specific suggestions and guidance
    Provides contextual help for IRIS capabilities
    """
    try:
        logger.info(f"Tool suggestion request: {tool_name}")
        
        agent = get_iris_agent()
        suggestions = await agent.get_tool_suggestions(tool_name, request.context)
        
        return {"tool_name": tool_name, "suggestions": suggestions, "success": True}
        
    except Exception as e:
        logger.error(f"Error getting tool suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")

# Potential Bid Card endpoints (delegated to action system)
@router.get("/potential-bid-cards/{user_id}")
async def get_potential_bid_cards(user_id: str):
    """Get user's potential bid cards"""
    try:
        logger.info(f"Getting potential bid cards for user {user_id}")
        
        agent = get_iris_agent()
        bid_cards = await agent.get_user_potential_bid_cards(user_id)
        
        return {"success": True, "bid_cards": bid_cards}
        
    except Exception as e:
        logger.error(f"Error getting potential bid cards: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving bid cards: {str(e)}")

@router.post("/potential-bid-cards")
async def create_potential_bid_card(request: Dict[str, Any]):
    """Create new potential bid card"""
    try:
        logger.info("Creating new potential bid card")
        
        agent = get_iris_agent()
        result = await agent.create_potential_bid_card(request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating potential bid card: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating bid card: {str(e)}")

@router.put("/potential-bid-cards/{card_id}")
async def update_potential_bid_card(card_id: str, request: BidCardUpdateRequest):
    """Update potential bid card fields"""
    try:
        logger.info(f"Updating potential bid card {card_id}")
        
        agent = get_iris_agent()
        result = await agent.update_potential_bid_card(card_id, request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating potential bid card: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating bid card: {str(e)}")

@router.post("/potential-bid-cards/bundle")
async def bundle_potential_bid_cards(request: Dict[str, Any]):
    """Bundle multiple potential bid cards"""
    try:
        logger.info("Bundling potential bid cards")
        
        agent = get_iris_agent()
        result = await agent.bundle_potential_bid_cards(request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error bundling bid cards: {e}")
        raise HTTPException(status_code=500, detail=f"Error bundling cards: {str(e)}")

@router.post("/potential-bid-cards/convert-to-bid-cards")
async def convert_to_bid_cards(request: Dict[str, Any]):
    """Convert potential bid cards to official bid cards"""
    try:
        logger.info("Converting potential bid cards to official bid cards")
        
        agent = get_iris_agent()
        result = await agent.convert_to_bid_cards(request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error converting bid cards: {e}")
        raise HTTPException(status_code=500, detail=f"Error converting cards: {str(e)}")

@router.get("/potential-bid-cards/{card_id}/conversations")
async def get_bid_card_conversations(card_id: str):
    """Get conversations for a potential bid card"""
    try:
        logger.info(f"Getting conversations for bid card {card_id}")
        
        agent = get_iris_agent()
        conversations = await agent.get_bid_card_conversations(card_id)
        
        return {"success": True, "conversations": conversations}
        
    except Exception as e:
        logger.error(f"Error getting bid card conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving conversations: {str(e)}")

# Repair item management endpoints
@router.post("/repair-items")
async def add_repair_item(request: RepairItemRequest):
    """Add repair item to potential bid card"""
    try:
        logger.info(f"Adding repair item to bid card {request.potential_bid_card_id}")
        
        agent = get_iris_agent()
        result = await agent.add_repair_item(request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error adding repair item: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding repair item: {str(e)}")

@router.put("/repair-items/{item_id}")
async def update_repair_item(item_id: str, request: Dict[str, Any]):
    """Update repair item"""
    try:
        logger.info(f"Updating repair item {item_id}")
        
        agent = get_iris_agent()
        result = await agent.update_repair_item(item_id, request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating repair item: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating repair item: {str(e)}")

@router.delete("/repair-items/{item_id}")
async def delete_repair_item(item_id: str, potential_bid_card_id: str):
    """Delete repair item"""
    try:
        logger.info(f"Deleting repair item {item_id}")
        
        agent = get_iris_agent()
        result = await agent.delete_repair_item(item_id, potential_bid_card_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error deleting repair item: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting repair item: {str(e)}")

@router.get("/repair-items/{potential_bid_card_id}")
async def list_repair_items(potential_bid_card_id: str):
    """List all repair items for a potential bid card"""
    try:
        logger.info(f"Listing repair items for bid card {potential_bid_card_id}")
        
        agent = get_iris_agent()
        result = await agent.list_repair_items(potential_bid_card_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing repair items: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing repair items: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for IRIS agent"""
    try:
        agent = get_iris_agent()
        status = await agent.get_health_status()
        
        return {
            "status": "healthy",
            "agent": "IRIS",
            "version": "2.0.0",
            "capabilities": [
                "image_upload",
                "design_consultation", 
                "room_detection",
                "memory_management",
                "bid_card_integration"
            ],
            "details": status
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "agent": "IRIS",
            "error": str(e)
        }

# Background task functions
async def log_conversation_metrics(request: UnifiedChatRequest, response: IRISResponse):
    """Log conversation metrics for analytics"""
    try:
        metrics = {
            'user_id': request.user_id,
            'session_id': request.session_id,
            'images_uploaded': len(request.images) if request.images else 0,
            'response_length': len(response.response),
            'suggestions_provided': len(response.suggestions) if response.suggestions else 0,
            'success': response.success,
            'timestamp': response.dict().get('timestamp')
        }
        
        # This would integrate with analytics service
        logger.info(f"Conversation metrics: {metrics}")
        
    except Exception as e:
        logger.error(f"Error logging metrics: {e}")

# Note: Exception handlers should be registered on the main FastAPI app instance
# These handlers can be added to main.py if needed for global error handling

# Export router for main.py integration
__all__ = ['router']