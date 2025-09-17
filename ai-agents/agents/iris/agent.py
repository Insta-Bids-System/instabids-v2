"""
IRIS Agent - Main Orchestrator
Thin orchestrator that coordinates services and workflows for IRIS functionality
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Import modular services
from .services.photo_manager import PhotoManager
from .services.memory_manager import MemoryManager
from .services.context_builder import ContextBuilder
from .services.room_detector import RoomDetector

# Import workflow classes
from .workflows.image_workflow import ImageWorkflow
from .workflows.consultation_workflow import ConsultationWorkflow

# Import models
from .models.requests import (
    UnifiedChatRequest, 
    ContextRequest, 
    BidCardUpdateRequest,
    RepairItemRequest,
    ToolSuggestionRequest
)
from .models.responses import IRISResponse, ContextResponse
from .models.database import MemoryType

logger = logging.getLogger(__name__)

class IRISAgent:
    """
    IRIS Agent - Intelligent Room & Interior Spaces Agent
    
    Modular, maintainable architecture replacing the 2,290-line monolithic agent.
    Orchestrates services and workflows for design consultation and photo management.
    """
    
    def __init__(self):
        """Initialize IRIS agent with all required services"""
        logger.info("Initializing IRIS Agent v2.0...")
        
        # Core services
        self.photo_manager = PhotoManager()
        self.memory_manager = MemoryManager()
        self.context_builder = ContextBuilder()
        self.room_detector = RoomDetector()
        
        # Workflow handlers
        self.image_workflow = ImageWorkflow()
        self.consultation_workflow = ConsultationWorkflow()
        
        # Agent metadata
        self.agent_id = "iris-agent-v2"
        self.capabilities = [
            "image_upload",
            "design_consultation", 
            "room_detection",
            "memory_management",
            "bid_card_integration",
            "inspiration_boards",
            "project_planning"
        ]
        
        logger.info("IRIS Agent v2.0 initialized successfully")
    
    async def handle_unified_chat(self, request: UnifiedChatRequest) -> IRISResponse:
        """
        Main conversation handler - orchestrates all IRIS functionality
        
        This method routes requests to appropriate workflows based on content
        """
        try:
            logger.info(f"Processing unified chat request from user {request.user_id}")
            
            # Step 1: Generate session and conversation IDs
            session_id = request.session_id or str(uuid.uuid4())
            conversation_id = str(uuid.uuid4())
            
            # Step 2: Build user context
            context_summary = self.context_builder.build_context_summary(
                user_id=request.user_id,
                conversation_id=conversation_id
            )
            
            # Step 3: Route to appropriate workflow
            if request.images and len(request.images) > 0:
                # Image upload workflow
                response, workflow_data = self.image_workflow.process_image_upload(
                    request=request,
                    session_id=session_id,
                    conversation_id=conversation_id
                )
            else:
                # Design consultation workflow
                response, workflow_data = self.consultation_workflow.process_consultation(
                    request=request,
                    session_id=session_id,
                    conversation_id=conversation_id,
                    context_summary=context_summary
                )
            
            # Step 4: Save conversation to session memory
            await self._save_conversation_memory(
                conversation_id=conversation_id,
                session_id=session_id,
                user_input=request.message,
                agent_response=response.response,
                workflow_data=workflow_data
            )
            
            # Step 5: Update response metadata
            response.session_id = session_id
            response.user_id = request.user_id
            response.timestamp = datetime.utcnow().isoformat()
            
            logger.info(f"Successfully processed chat request for user {request.user_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error in unified chat handler: {e}", exc_info=True)
            return self._create_error_response(request, str(e))
    
    async def get_user_context(self, user_id: str, project_id: Optional[str] = None) -> ContextResponse:
        """Get comprehensive user context for IRIS conversations"""
        try:
            logger.info(f"Building context for user {user_id}")
            
            conversation_id = str(uuid.uuid4())  # Generate for context building
            
            context = self.context_builder.build_complete_context(
                user_id=user_id,
                conversation_id=conversation_id,
                project_id=project_id
            )
            
            logger.info(f"Successfully built context for user {user_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error building user context: {e}", exc_info=True)
            return ContextResponse(
                inspiration_boards=[],
                project_context={"project_available": False, "error": str(e)},
                design_preferences={},
                previous_designs=[],
                conversations_from_other_agents={},
                photos_from_unified_system={"project_photos": [], "inspiration_photos": [], "message_attachments": []},
                privacy_level="error"
            )
    
    async def get_tool_suggestions(self, tool_name: str, context: Dict[str, Any]) -> List[str]:
        """Get contextual suggestions for IRIS tools and capabilities"""
        try:
            logger.info(f"Getting tool suggestions for {tool_name}")
            
            suggestions = []
            
            if tool_name == "image_upload":
                suggestions = [
                    "Upload inspiration photos for your design style",
                    "Share current photos of your space",
                    "Add examples of colors and materials you love",
                    "Show me problem areas that need solutions"
                ]
            elif tool_name == "room_detection":
                room_suggestions = self.room_detector.get_room_suggestions()
                suggestions = [f"Help organize ideas for {room}" for room in room_suggestions[:4]]
            elif tool_name == "design_consultation":
                suggestions = [
                    "Help me define my design style preferences",
                    "Create a cohesive design plan for my space", 
                    "Guide me through the design decision process",
                    "Prepare me to work with contractors"
                ]
            elif tool_name == "inspiration_boards":
                suggestions = [
                    "Organize my inspiration by room type",
                    "Create mood boards for different design styles",
                    "Compare and contrast design approaches",
                    "Prepare inspiration for contractor consultations"
                ]
            else:
                suggestions = [
                    "Tell me about your design goals",
                    "Upload some inspiration images", 
                    "What room are you working on?",
                    "How can I help with your project?"
                ]
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting tool suggestions: {e}")
            return ["How can I help you today?"]
    
    # Potential Bid Card Management (delegated from API routes)
    async def get_user_potential_bid_cards(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's potential bid cards"""
        try:
            # This would integrate with CIA agent's potential bid card system
            return []
        except Exception as e:
            logger.error(f"Error getting potential bid cards: {e}")
            return []
    
    async def create_potential_bid_card(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create new potential bid card"""
        try:
            # This would integrate with CIA agent's bid card creation
            return {"success": False, "error": "Not implemented"}
        except Exception as e:
            logger.error(f"Error creating potential bid card: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_potential_bid_card(self, card_id: str, request: BidCardUpdateRequest) -> Dict[str, Any]:
        """Update potential bid card fields"""
        try:
            # This would integrate with CIA agent's bid card updates
            return {"success": False, "error": "Not implemented"}
        except Exception as e:
            logger.error(f"Error updating potential bid card: {e}")
            return {"success": False, "error": str(e)}
    
    async def bundle_potential_bid_cards(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Bundle multiple potential bid cards"""
        try:
            # This would integrate with CIA agent's bundling system
            return {"success": False, "error": "Not implemented"}
        except Exception as e:
            logger.error(f"Error bundling bid cards: {e}")
            return {"success": False, "error": str(e)}
    
    async def convert_to_bid_cards(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Convert potential bid cards to official bid cards"""
        try:
            # This would integrate with CIA agent's conversion system
            return {"success": False, "error": "Not implemented"}
        except Exception as e:
            logger.error(f"Error converting bid cards: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_bid_card_conversations(self, card_id: str) -> List[Dict[str, Any]]:
        """Get conversations for a potential bid card"""
        try:
            # This would integrate with conversation history
            return []
        except Exception as e:
            logger.error(f"Error getting bid card conversations: {e}")
            return []
    
    # Repair Item Management
    async def add_repair_item(self, request: RepairItemRequest) -> Dict[str, Any]:
        """Add repair item to potential bid card"""
        try:
            # This would integrate with repair item system
            return {"success": False, "error": "Not implemented"}
        except Exception as e:
            logger.error(f"Error adding repair item: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_repair_item(self, item_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Update repair item"""
        try:
            # This would integrate with repair item updates
            return {"success": False, "error": "Not implemented"}
        except Exception as e:
            logger.error(f"Error updating repair item: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_repair_item(self, item_id: str, potential_bid_card_id: str) -> Dict[str, Any]:
        """Delete repair item"""
        try:
            # This would integrate with repair item deletion
            return {"success": False, "error": "Not implemented"}
        except Exception as e:
            logger.error(f"Error deleting repair item: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_repair_items(self, potential_bid_card_id: str) -> Dict[str, Any]:
        """List all repair items for a potential bid card"""
        try:
            # This would integrate with repair item listing
            return {"success": True, "repair_items": []}
        except Exception as e:
            logger.error(f"Error listing repair items: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get agent health status for monitoring"""
        try:
            status = {
                "agent_id": self.agent_id,
                "capabilities": self.capabilities,
                "services": {
                    "photo_manager": "healthy",
                    "memory_manager": "healthy", 
                    "context_builder": "healthy",
                    "room_detector": "healthy"
                },
                "workflows": {
                    "image_workflow": "healthy",
                    "consultation_workflow": "healthy"
                },
                "last_health_check": datetime.utcnow().isoformat()
            }
            
            # Test database connectivity through memory manager
            try:
                # Simple connectivity test
                test_conversations = self.memory_manager.get_user_conversations("health-check")
                status["database_connectivity"] = "healthy"
            except Exception as db_error:
                status["database_connectivity"] = f"error: {str(db_error)}"
                status["services"]["memory_manager"] = "unhealthy"
            
            return status
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                "agent_id": self.agent_id,
                "status": "unhealthy",
                "error": str(e),
                "last_health_check": datetime.utcnow().isoformat()
            }
    
    # Private helper methods
    async def _save_conversation_memory(
        self,
        conversation_id: str,
        session_id: str,
        user_input: str,
        agent_response: str,
        workflow_data: Dict[str, Any]
    ) -> None:
        """Save conversation to session memory"""
        try:
            memory_value = {
                "session_id": session_id,
                "user_input": user_input,
                "agent_response": agent_response,
                "workflow_data": workflow_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.memory_manager.save_session_memory(
                conversation_id=conversation_id,
                memory_type=MemoryType.SESSION_CONVERSATION,
                memory_key=f"conversation_{session_id}",
                memory_value=memory_value
            )
            
        except Exception as e:
            logger.error(f"Error saving conversation memory: {e}")
    
    def _create_error_response(self, request: UnifiedChatRequest, error_message: str) -> IRISResponse:
        """Create error response for failed requests"""
        return IRISResponse(
            success=False,
            response=(
                f"I apologize, but I encountered an error processing your request. "
                f"Please try again in a moment, or let me know if you need help with something else."
            ),
            suggestions=[
                "Try your request again",
                "Tell me about your design project",
                "Upload some inspiration images", 
                "What room are you working on?"
            ],
            interface="homeowner",
            session_id=request.session_id,
            user_id=request.user_id,
            error_details=error_message
        )

# Export the agent class
__all__ = ['IRISAgent']