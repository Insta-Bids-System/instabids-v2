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
from .services.conversation_manager import ConversationManager
from .services.property_context_builder import PropertyContextBuilder

# Import workflow classes
from .workflows.image_workflow import ImageWorkflow
from .workflows.consultation_workflow import ConsultationWorkflow
from .workflows.conversational_flow import ConversationalFlow

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
        self.conversation_manager = ConversationManager()
        self.property_context_builder = PropertyContextBuilder()
        
        # Workflow handlers
        self.image_workflow = ImageWorkflow()
        self.consultation_workflow = ConsultationWorkflow()
        self.conversational_flow = ConversationalFlow(property_context_builder=self.property_context_builder)
        
        # Agent metadata
        self.agent_id = "iris-agent-v2"
        self.capabilities = [
            "image_upload",
            "room_detection",
            "memory_management",
            "bid_card_integration",
            "property_consultation",
            "contractor_matching"
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
            
            # Step 2: Build user context including comprehensive property context
            property_context = await self.property_context_builder.get_complete_property_context(request.user_id)
            
            context_summary = self.context_builder.build_context_summary(
                user_id=request.user_id,
                conversation_id=conversation_id
            )
            
            # Enhance context with property intelligence
            enhanced_context = {
                'context_summary': context_summary,  # Store string summary properly
                'property_intelligence': property_context,
                'context_enhanced': True,
                'enhanced_at': datetime.utcnow().isoformat()
            }
            
            # Step 3: Get conversation state from memory
            # The request doesn't have metadata field, so we'll get state from conversation manager
            conversation_state = None
            
            # Get state from conversation manager with user-based threading
            if not conversation_state:
                conversation_state_data = await self.conversation_manager.get_conversation_state(session_id, user_id=request.user_id)
                conversation_state = conversation_state_data.get('state', 'initial')
            
            # Step 4: Route to conversational flow for ALL requests (with or without images)
            # The conversational flow handles both image uploads and text conversations
            response, workflow_data = await self.conversational_flow.handle_conversation(
                request=request,
                session_id=session_id,
                conversation_state=conversation_state
            )
            
            # Step 5: Update conversation manager with new state
            if workflow_data.get('state'):
                await self.conversation_manager.update_conversation_state(
                    session_id=session_id,
                    state=workflow_data['state'],
                    context_update=workflow_data
                )
            
            # Step 6: Add conversation history with user-based threading
            await self.conversation_manager.add_to_history(
                session_id=session_id,
                message=request.message,
                response=response.response,
                user_id=request.user_id
            )
            
            # Step 4: Save conversation to session memory
            # Add user_id to workflow_data for memory saving
            workflow_data['user_id'] = request.user_id
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
            # Removed timestamp - field doesn't exist in IRISResponse model
            
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
                property_projects=[],
                project_context={"project_available": False, "error": str(e)},
                contractor_preferences={},
                previous_projects=[],
                conversations_from_other_agents={},
                photos_from_unified_system={"property_photos": [], "message_attachments": []},
                privacy_level="error"
            )
    
    async def get_tool_suggestions(self, tool_name: str, context: Dict[str, Any]) -> List[str]:
        """Get contextual suggestions for IRIS tools and capabilities"""
        try:
            logger.info(f"Getting tool suggestions for {tool_name}")
            
            suggestions = []
            
            if tool_name == "image_upload":
                suggestions = [
                    "Upload photos of property issues that need repair",
                    "Share current photos of your space",
                    "Document areas that need maintenance or improvement",
                    "Show me problem areas that need contractor solutions"
                ]
            elif tool_name == "room_detection":
                room_suggestions = self.room_detector.get_room_suggestions()
                suggestions = [f"Help organize ideas for {room}" for room in room_suggestions[:4]]
            elif tool_name == "property_consultation":
                suggestions = [
                    "Help me identify property issues that need attention",
                    "Create a prioritized maintenance plan for my property", 
                    "Guide me through the contractor selection process",
                    "Help me prepare project details for contractors"
                ]
            elif tool_name == "bid_card_integration":
                suggestions = [
                    "Create a bid card for this property project",
                    "Track my project requests and contractor responses",
                    "Organize project details for contractor outreach",
                    "Manage multiple property improvement projects"
                ]
            else:
                suggestions = [
                    "Tell me about your property maintenance needs",
                    "Upload photos of areas needing contractor work", 
                    "What room or area needs attention?",
                    "How can I help you find the right contractors?"
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
        """Create new potential bid card from property issue analysis"""
        try:
            logger.info(f"Creating potential bid card from IRIS property analysis")
            
            # Extract required fields from request
            user_id = request.get('user_id')
            room_type = request.get('room_type', 'general')
            issue_description = request.get('issue_description', '')
            image_analysis = request.get('image_analysis', {})
            session_id = request.get('session_id', str(uuid.uuid4()))
            conversation_id = request.get('conversation_id', str(uuid.uuid4()))
            
            if not user_id:
                return {"success": False, "error": "user_id is required"}
            
            # Generate bid card data from property analysis
            from database import db
            
            # Determine primary trade from room type and analysis
            primary_trade = self._determine_trade_from_analysis(room_type, issue_description, image_analysis)
            
            # Create title based on room and issue
            title = self._generate_bid_card_title(room_type, issue_description)
            
            # Create potential bid card record
            potential_bid_card = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'homeowner_id': user_id,  # Both fields for compatibility
                'title': title,
                'primary_trade': primary_trade,
                'user_scope_notes': issue_description,
                'status': 'draft',
                'source': 'iris_property_analysis',
                'cia_conversation_id': conversation_id,
                'ai_analysis': {
                    'created_by': 'iris_agent',
                    'room_type': room_type,
                    'image_analysis': image_analysis,
                    'analysis_timestamp': datetime.utcnow().isoformat(),
                    'confidence_score': image_analysis.get('confidence_score', 0.8),
                    'auto_generated': True,
                    'property_issue_detected': True
                },
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                # Optional fields that can be updated later
                'urgency_level': self._determine_urgency_from_description(issue_description),
                'estimated_timeline': self._estimate_timeline_from_issue(issue_description),
                'zip_code': None,  # Can be filled by location services
            }
            
            # Save to database
            result = db.client.table('potential_bid_cards').insert(potential_bid_card).execute()
            
            if result.data:
                bid_card_id = result.data[0]['id']
                logger.info(f"Created potential bid card {bid_card_id} from IRIS analysis")
                
                return {
                    "success": True,
                    "bid_card_id": bid_card_id,
                    "title": title,
                    "primary_trade": primary_trade,
                    "analysis_summary": {
                        "room_type": room_type,
                        "issue_detected": True,
                        "confidence": image_analysis.get('confidence_score', 0.8),
                        "auto_generated": True
                    }
                }
            else:
                return {"success": False, "error": "Failed to create bid card in database"}
                
        except Exception as e:
            logger.error(f"Error creating potential bid card: {e}", exc_info=True)
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
            # Ensure conversation exists first
            self._ensure_conversation_exists(conversation_id, session_id, workflow_data.get('user_id', 'unknown'))
            
            memory_value = {
                "session_id": session_id,
                "user_input": user_input,
                "agent_response": agent_response,
                "workflow_data": workflow_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Save as both conversation message and context memory for persistence
            self.memory_manager.save_conversation_message(
                conversation_id=conversation_id,
                sender="user",
                content=user_input,
                message_type="text",
                metadata={"type": "user_input", "user_id": workflow_data.get('user_id')}
            )
            
            self.memory_manager.save_conversation_message(
                conversation_id=conversation_id,
                sender="assistant",
                content=agent_response,
                message_type="text",
                metadata={"workflow_data": workflow_data}
            )
            
            # Also save to context memory for cross-session retrieval
            self.memory_manager.save_context_memory(
                conversation_id=conversation_id,
                memory_type='session_conversation',
                memory_key=f"session_{session_id}",
                memory_value=memory_value
            )
            
        except Exception as e:
            logger.error(f"Error saving conversation memory: {e}")
    
    def _ensure_conversation_exists(self, conversation_id: str, session_id: str, user_id: str) -> None:
        """Ensure the conversation exists in unified_conversations table"""
        try:
            from database import db
            
            # Check if conversation exists
            result = db.client.table('unified_conversations').select('id').eq('id', conversation_id).execute()
            
            if not result.data:
                # Create the conversation
                db.client.table('unified_conversations').insert({
                    'id': conversation_id,
                    'tenant_id': user_id,
                    'created_by': user_id,
                    'conversation_type': 'iris_property_consultation',
                    'entity_type': 'property',
                    'title': f'IRIS Property Session {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                    'status': 'active',
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat(),
                    'metadata': {
                        'agent': 'iris_property',
                        'session_id': session_id
                    }
                }).execute()
                logger.info(f"Created conversation {conversation_id} for session {session_id}")
        except Exception as e:
            logger.error(f"Error ensuring conversation exists: {e}")
    
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
                "Tell me about your property project",
                "Upload photos of areas needing work", 
                "What room or area needs attention?"
            ],
            interface="homeowner",
            session_id=request.session_id,
            user_id=request.user_id,
            error_details=error_message
        )
    
    def _determine_trade_from_analysis(self, room_type: str, description: str, image_analysis: Dict) -> str:
        """Determine primary trade from room type and issue description"""
        description_lower = description.lower()
        
        # Room-specific trade mapping
        if room_type in ['backyard', 'front_yard', 'yard', 'garden']:
            if any(word in description_lower for word in ['lawn', 'grass', 'sod', 'seed']):
                return 'landscaping'
            elif any(word in description_lower for word in ['sprinkler', 'irrigation', 'water']):
                return 'irrigation'
            else:
                return 'landscaping'
        elif room_type == 'kitchen':
            if any(word in description_lower for word in ['cabinet', 'countertop']):
                return 'kitchen_remodel'
            elif any(word in description_lower for word in ['plumb', 'faucet', 'sink']):
                return 'plumbing'
            else:
                return 'kitchen_remodel'
        elif room_type == 'bathroom':
            if any(word in description_lower for word in ['tile', 'shower', 'tub']):
                return 'bathroom_remodel'
            elif any(word in description_lower for word in ['plumb', 'toilet', 'faucet']):
                return 'plumbing'
            else:
                return 'bathroom_remodel'
        else:
            # General issue analysis
            if any(word in description_lower for word in ['paint', 'wall', 'color']):
                return 'painting'
            elif any(word in description_lower for word in ['floor', 'carpet', 'hardwood']):
                return 'flooring'
            elif any(word in description_lower for word in ['electric', 'outlet', 'light']):
                return 'electrical'
            elif any(word in description_lower for word in ['plumb', 'leak', 'pipe']):
                return 'plumbing'
            else:
                return 'general_contractor'
    
    def _generate_bid_card_title(self, room_type: str, description: str) -> str:
        """Generate descriptive title for the bid card"""
        room_display = room_type.replace('_', ' ').title()
        
        # Extract key issue words
        description_lower = description.lower()
        if any(word in description_lower for word in ['lawn', 'grass', 'sod']):
            return f"{room_display} Lawn Repair"
        elif any(word in description_lower for word in ['kitchen', 'cabinet', 'countertop']):
            return f"{room_display} Kitchen Updates"
        elif any(word in description_lower for word in ['bathroom', 'tile', 'shower']):
            return f"{room_display} Bathroom Renovation"
        elif any(word in description_lower for word in ['paint', 'painting']):
            return f"{room_display} Painting Project"
        elif any(word in description_lower for word in ['floor', 'flooring']):
            return f"{room_display} Flooring Project"
        else:
            return f"{room_display} Repair & Improvement"
    
    def _determine_urgency_from_description(self, description: str) -> str:
        """Determine urgency level from issue description"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['emergency', 'urgent', 'asap', 'immediately']):
            return 'emergency'
        elif any(word in description_lower for word in ['soon', 'quickly', 'fast']):
            return 'urgent'
        elif any(word in description_lower for word in ['planning', 'future', 'eventual']):
            return 'flexible'
        else:
            return 'standard'
    
    def _estimate_timeline_from_issue(self, description: str) -> str:
        """Estimate timeline based on issue type"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['lawn', 'grass', 'landscaping', 'sod']):
            return '1-2 weeks'
        elif any(word in description_lower for word in ['paint', 'painting']):
            return '3-5 days'
        elif any(word in description_lower for word in ['kitchen', 'bathroom', 'remodel']):
            return '2-4 weeks'
        elif any(word in description_lower for word in ['floor', 'flooring']):
            return '1-2 weeks'
        else:
            return '1 week'

# Export the agent class
__all__ = ['IRISAgent']