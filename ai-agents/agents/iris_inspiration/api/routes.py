"""
IRIS Inspiration API Routes
FastAPI routes for inspiration board management and design consultation
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
import uuid
import json

from ..models.requests import InspirationChatRequest, InspirationBoardRequest
from ..models.responses import IRISInspirationResponse, StyleAnalysisResult

logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/api/iris-inspiration", tags=["IRIS Inspiration"])

# Import agent at module level to avoid circular imports
_inspiration_agent = None

def get_inspiration_agent():
    """Lazy import of IRIS Inspiration agent to avoid circular imports"""
    global _inspiration_agent
    if _inspiration_agent is None:
        from ..agent import IRISInspirationAgent
        _inspiration_agent = IRISInspirationAgent()
    return _inspiration_agent

@router.post("/chat", response_model=IRISInspirationResponse)
async def inspiration_chat(request: InspirationChatRequest, background_tasks: BackgroundTasks):
    """
    Main IRIS Inspiration conversation endpoint
    Handles inspiration-focused chat with image uploads and style analysis
    """
    try:
        logger.info(f"IRIS Inspiration chat request from user {request.user_id}")
        
        agent = get_inspiration_agent()
        response = await agent.handle_conversation(request)
        
        # Add background tasks for analytics
        background_tasks.add_task(log_inspiration_metrics, request, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in inspiration chat: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/boards", response_model=Dict[str, Any])
async def create_inspiration_board(request: InspirationBoardRequest):
    """Create a new inspiration board"""
    try:
        logger.info(f"Creating inspiration board for user {request.user_id}")
        
        agent = get_inspiration_agent()
        board_id = agent.inspiration_manager.create_inspiration_board(
            user_id=request.user_id,
            title=request.title,
            room_type=request.room_type,
            description=request.description
        )
        
        return {
            "success": True, 
            "board_id": board_id,
            "message": f"Created inspiration board '{request.title}'"
        }
        
    except Exception as e:
        logger.error(f"Error creating inspiration board: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating board: {str(e)}")

@router.get("/boards/{user_id}", response_model=Dict[str, Any])
async def get_user_inspiration_boards(user_id: str):
    """Get all inspiration boards for a user"""
    try:
        logger.info(f"Getting inspiration boards for user {user_id}")
        
        agent = get_inspiration_agent()
        boards = agent.inspiration_manager.get_user_boards(user_id)
        
        return {
            "success": True, 
            "boards": boards, 
            "user_id": user_id,
            "count": len(boards)
        }
        
    except Exception as e:
        logger.error(f"Error getting inspiration boards: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting boards: {str(e)}")

@router.get("/boards/{user_id}/{board_id}", response_model=Dict[str, Any])
async def get_inspiration_board(user_id: str, board_id: str):
    """Get specific inspiration board with images"""
    try:
        logger.info(f"Getting inspiration board {board_id} for user {user_id}")
        
        agent = get_inspiration_agent()
        boards = agent.inspiration_manager.get_user_boards(user_id)
        board = next((b for b in boards if b.get('id') == board_id), None)
        
        if not board:
            raise HTTPException(status_code=404, detail="Inspiration board not found")
        
        # Get images for this board
        images = await agent._get_board_images(board_id)
        board['images'] = images
        
        return {"success": True, "board": board}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting inspiration board: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting board: {str(e)}")

@router.post("/boards/{board_id}/images", response_model=Dict[str, Any])
async def upload_inspiration_images(
    board_id: str,
    user_id: str = Form(...),
    session_id: str = Form(...),
    images: List[UploadFile] = File(...),
    message: str = Form("")
):
    """Upload images to an inspiration board"""
    try:
        logger.info(f"Uploading {len(images)} images to board {board_id}")
        
        # Process uploaded files
        image_files = []
        for image_file in images:
            # Read and encode image data
            content = await image_file.read()
            import base64
            image_data = base64.b64encode(content).decode('utf-8')
            
            image_files.append({
                'filename': image_file.filename,
                'data': f"data:{image_file.content_type};base64,{image_data}",
                'content_type': image_file.content_type
            })
        
        agent = get_inspiration_agent()
        
        # Process images using the workflow
        response = await agent.inspiration_workflow.process_inspiration_images(
            user_id=user_id,
            conversation_id=f"board_{board_id}",
            session_id=session_id,
            image_files=image_files,
            user_context={'message': message}
        )
        
        return {
            "success": response.success,
            "message": response.response,
            "images_processed": response.images_processed,
            "style_analysis": response.style_analysis
        }
        
    except Exception as e:
        logger.error(f"Error uploading inspiration images: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading images: {str(e)}")

@router.post("/style-analysis", response_model=Dict[str, Any])
async def analyze_inspiration_style(
    images: List[UploadFile] = File(...),
    message: str = Form(""),
    room_type: str = Form("general")
):
    """Analyze style from inspiration images"""
    try:
        logger.info(f"Analyzing style for {len(images)} inspiration images")
        
        # Process uploaded files
        image_files = []
        for image_file in images:
            content = await image_file.read()
            import base64
            image_data = base64.b64encode(content).decode('utf-8')
            
            image_files.append({
                'filename': image_file.filename,
                'data': f"data:{image_file.content_type};base64,{image_data}",
                'content_type': image_file.content_type
            })
        
        agent = get_inspiration_agent()
        
        # Use PhotoManager for vision analysis
        style_analysis = agent.photo_manager.analyze_inspiration_images_with_vision(
            image_files, message
        )
        
        # Generate comprehensive style insights
        style_dict = {
            'room_type': style_analysis.room_type,
            'style_summary': style_analysis.style_summary,
            'key_elements': style_analysis.key_elements,
            'description': style_analysis.description,
            'confidence_score': style_analysis.confidence_score,
            'auto_generated_tags': style_analysis.auto_generated_tags,
            'suggestions': style_analysis.suggestions
        }
        
        return {
            "success": True,
            "style_analysis": style_dict,
            "images_analyzed": len(image_files)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing inspiration style: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing style: {str(e)}")

@router.get("/context/{user_id}", response_model=Dict[str, Any])
async def get_inspiration_context(user_id: str, board_id: Optional[str] = None):
    """
    Get user's inspiration context including boards, style preferences, and design history
    """
    try:
        logger.info(f"Getting inspiration context for user {user_id}")
        
        agent = get_inspiration_agent()
        
        # Get user's inspiration boards
        boards = agent.inspiration_manager.get_user_boards(user_id)
        
        # Get style preferences from memory
        style_preferences = agent.memory_manager.get_user_style_preferences(user_id)
        
        # Get recent inspiration conversations
        conversations = agent.memory_manager.get_inspiration_conversations(user_id, limit=5)
        
        context = {
            "user_id": user_id,
            "inspiration_boards": boards,
            "style_preferences": style_preferences,
            "recent_conversations": conversations,
            "total_boards": len(boards)
        }
        
        if board_id:
            # Add specific board context
            board = next((b for b in boards if b.get('id') == board_id), None)
            if board:
                images = await agent._get_board_images(board_id)
                context["current_board"] = {**board, "images": images}
        
        return {"success": True, "context": context}
        
    except Exception as e:
        logger.error(f"Error getting inspiration context: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving context: {str(e)}")

@router.delete("/boards/{board_id}")
async def delete_inspiration_board(board_id: str, user_id: str):
    """Delete an inspiration board"""
    try:
        logger.info(f"Deleting inspiration board {board_id} for user {user_id}")
        
        agent = get_inspiration_agent()
        
        # Verify board belongs to user
        boards = agent.inspiration_manager.get_user_boards(user_id)
        board = next((b for b in boards if b.get('id') == board_id), None)
        
        if not board:
            raise HTTPException(status_code=404, detail="Inspiration board not found")
        
        # Delete board and associated images
        success = await agent._delete_inspiration_board(board_id)
        
        return {
            "success": success,
            "message": f"Deleted inspiration board '{board.get('title', board_id)}'"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting inspiration board: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting board: {str(e)}")

@router.get("/tags/suggestions")
async def get_tag_suggestions(room_type: str = "general", style: str = "contemporary"):
    """Get suggested tags for inspiration organization"""
    try:
        logger.info(f"Getting tag suggestions for {room_type} in {style} style")
        
        agent = get_inspiration_agent()
        
        tags = agent.inspiration_manager.generate_inspiration_tags(
            room_type=room_type,
            style_analysis={"primary_style": style},
            user_preferences=[]
        )
        
        return {
            "success": True,
            "tags": tags,
            "room_type": room_type,
            "style": style
        }
        
    except Exception as e:
        logger.error(f"Error getting tag suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")

@router.get("/health")
async def inspiration_health_check():
    """Health check endpoint for IRIS Inspiration agent"""
    try:
        agent = get_inspiration_agent()
        
        return {
            "status": "healthy",
            "agent": "IRIS Inspiration",
            "version": "1.0.0",
            "capabilities": [
                "inspiration_boards",
                "style_analysis", 
                "image_processing",
                "design_consultation",
                "memory_management"
            ],
            "routes": [
                "/chat",
                "/boards",
                "/style-analysis",
                "/context/{user_id}"
            ]
        }
        
    except Exception as e:
        logger.error(f"Inspiration health check failed: {e}")
        return {
            "status": "unhealthy",
            "agent": "IRIS Inspiration",
            "error": str(e)
        }

# Background task functions
async def log_inspiration_metrics(request: InspirationChatRequest, response: IRISInspirationResponse):
    """Log inspiration conversation metrics"""
    try:
        metrics = {
            'user_id': request.user_id,
            'session_id': request.session_id,
            'images_processed': getattr(response, 'images_processed', 0),
            'style_analysis_success': bool(getattr(response, 'style_analysis', None)),
            'boards_accessed': len(getattr(response, 'inspiration_items', [])),
            'success': response.success,
            'agent': 'iris_inspiration'
        }
        
        logger.info(f"Inspiration metrics: {metrics}")
        
    except Exception as e:
        logger.error(f"Error logging inspiration metrics: {e}")

# Export router for main.py integration
__all__ = ['router']