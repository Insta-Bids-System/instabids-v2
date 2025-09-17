"""
IRIS Inspiration Agent
Specialized agent for design inspiration and mood board creation
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from .services.memory_manager import MemoryManager
from .services.inspiration_manager import InspirationManager
from .workflows.inspiration_workflow import InspirationImageWorkflow
from .models.requests import InspirationChatRequest
from .models.responses import IRISInspirationResponse, InspirationContextResponse

logger = logging.getLogger(__name__)

class IRISInspirationAgent:
    """
    IRIS Inspiration Agent - Specialized for design inspiration and style analysis
    
    Purpose: Handle design inspiration conversations, mood board creation,
    and style analysis for homeowner design projects
    """
    
    def __init__(self):
        """Initialize IRIS Inspiration Agent with specialized services"""
        self.agent_name = "IRIS_INSPIRATION"
        self.agent_version = "1.0.0"
        self.capabilities = [
            "inspiration_boards",
            "style_analysis",
            "image_processing", 
            "design_consultation",
            "memory_management"
        ]
        
        # Initialize services
        self.memory_manager = MemoryManager()
        self.inspiration_manager = InspirationManager()
        self.image_workflow = InspirationImageWorkflow()
        
        logger.info(f"IRIS Inspiration Agent {self.agent_version} initialized")
    
    async def handle_conversation(
        self,
        user_id: str,
        message: str,
        session_id: str,
        image_files: Optional[List[Dict[str, Any]]] = None,
        room_type: Optional[str] = None,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> IRISInspirationResponse:
        """
        Handle inspiration-focused conversations
        
        Args:
            user_id: User ID
            message: User message
            session_id: Session ID
            image_files: Optional inspiration images
            room_type: Room type for inspiration
            conversation_context: Previous conversation context
            
        Returns:
            IRISInspirationResponse with inspiration-focused response
        """
        try:
            logger.info(f"IRIS Inspiration handling conversation for user {user_id}")
            
            # Create or get conversation ID for inspiration context
            conversation_id = self.memory_manager.create_or_get_conversation_id(
                user_id=user_id,
                session_id=session_id
            )
            
            # Save user message to session memory
            await self._save_user_message(
                conversation_id=conversation_id,
                user_id=user_id,
                message=message,
                session_id=session_id
            )
            
            # Handle image uploads if provided
            if image_files:
                return await self._handle_image_upload(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    session_id=session_id,
                    message=message,
                    image_files=image_files,
                    room_type=room_type
                )
            
            # Handle text-only inspiration conversation
            return await self._handle_text_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
                session_id=session_id,
                message=message,
                room_type=room_type,
                conversation_context=conversation_context
            )
            
        except Exception as e:
            logger.error(f"Error in IRIS Inspiration conversation: {e}")
            return IRISInspirationResponse(
                success=False,
                response="I apologize, but I encountered an issue processing your design inspiration request. Please try again.",
                error=str(e)
            )
    
    async def _handle_image_upload(
        self,
        user_id: str,
        conversation_id: str,
        session_id: str,
        message: str,
        image_files: List[Dict[str, Any]],
        room_type: Optional[str] = None
    ) -> IRISInspirationResponse:
        """Handle inspiration image uploads"""
        try:
            logger.info(f"Processing {len(image_files)} inspiration images")
            
            # Get user context for personalized analysis
            user_context = self.memory_manager.get_complete_inspiration_context(
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            # Process images through inspiration workflow
            result = await self.image_workflow.process_inspiration_images(
                user_id=user_id,
                conversation_id=conversation_id,
                session_id=session_id,
                image_files=image_files,
                room_type=room_type,
                user_context=user_context
            )
            
            # Save agent response to memory
            await self._save_agent_response(
                conversation_id=conversation_id,
                response=result.response,
                metadata={
                    'images_processed': result.images_processed,
                    'board_id': result.board_id,
                    'style_analysis': result.style_analysis
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling inspiration images: {e}")
            return IRISInspirationResponse(
                success=False,
                response="I had trouble analyzing your inspiration images. Please try uploading them again.",
                error=str(e)
            )
    
    async def _handle_text_conversation(
        self,
        user_id: str,
        conversation_id: str,
        session_id: str,
        message: str,
        room_type: Optional[str] = None,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> IRISInspirationResponse:
        """Handle text-only inspiration conversations"""
        try:
            # Get complete inspiration context
            inspiration_context = self.memory_manager.get_complete_inspiration_context(
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            # Determine user intent
            intent = self._analyze_user_intent(message, inspiration_context)
            
            # Generate response based on intent
            response = await self._generate_inspiration_response(
                user_id=user_id,
                message=message,
                intent=intent,
                inspiration_context=inspiration_context,
                room_type=room_type
            )
            
            # Save agent response
            await self._save_agent_response(
                conversation_id=conversation_id,
                response=response.response,
                metadata={
                    'intent': intent,
                    'room_type': room_type,
                    'suggestions_provided': len(response.suggestions)
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling text conversation: {e}")
            return IRISInspirationResponse(
                success=False,
                response="I'm having trouble understanding your design inspiration needs. Could you tell me more about what you're looking for?",
                error=str(e)
            )
    
    def _analyze_user_intent(
        self, 
        message: str, 
        inspiration_context: Dict[str, Any]
    ) -> str:
        """Analyze user intent from message"""
        message_lower = message.lower()
        
        # Intent patterns
        if any(word in message_lower for word in ['help', 'idea', 'inspiration', 'style']):
            return 'seeking_inspiration'
        elif any(word in message_lower for word in ['board', 'collection', 'save']):
            return 'board_management'
        elif any(word in message_lower for word in ['color', 'palette', 'scheme']):
            return 'color_guidance'
        elif any(word in message_lower for word in ['room', 'space', 'kitchen', 'bathroom', 'bedroom']):
            return 'room_specific'
        elif any(word in message_lower for word in ['budget', 'cost', 'price', 'expensive']):
            return 'budget_conscious'
        else:
            return 'general_conversation'
    
    async def _generate_inspiration_response(
        self,
        user_id: str,
        message: str,
        intent: str,
        inspiration_context: Dict[str, Any],
        room_type: Optional[str] = None
    ) -> IRISInspirationResponse:
        """Generate inspiration-focused response"""
        
        # Get user's inspiration history
        boards = inspiration_context.get('inspiration_boards', [])
        style_prefs = inspiration_context.get('style_preferences', {})
        
        # Generate personalized response based on intent
        if intent == 'seeking_inspiration':
            response_text = self._generate_inspiration_seeking_response(message, style_prefs, room_type)
            suggestions = self._generate_inspiration_suggestions(style_prefs, room_type)
            
        elif intent == 'board_management':
            response_text = self._generate_board_management_response(message, boards)
            suggestions = self._generate_board_suggestions(boards, user_id)
            
        elif intent == 'color_guidance':
            response_text = self._generate_color_guidance_response(message, style_prefs)
            suggestions = self._generate_color_suggestions(style_prefs)
            
        elif intent == 'room_specific':
            response_text = self._generate_room_specific_response(message, room_type, style_prefs)
            suggestions = self._generate_room_suggestions(room_type, style_prefs)
            
        else:  # general_conversation
            response_text = self._generate_general_response(message, inspiration_context)
            suggestions = self._generate_general_suggestions()
        
        return IRISInspirationResponse(
            success=True,
            response=response_text,
            suggestions=suggestions,
            session_id=None,  # Will be set by caller
            user_id=user_id,
            style_analysis=style_prefs
        )
    
    def _generate_inspiration_seeking_response(
        self, 
        message: str, 
        style_prefs: Dict[str, Any], 
        room_type: Optional[str]
    ) -> str:
        """Generate response for inspiration seeking"""
        if style_prefs and 'preferences' in style_prefs:
            preferred_style = style_prefs['preferences'].get('primary_style', 'contemporary')
            return f"Based on your {preferred_style} style preferences, I'd love to help you explore more design inspiration! What specific aspect are you looking to develop?"
        elif room_type:
            return f"I'm excited to help you find inspiration for your {room_type}! What kind of feeling or atmosphere are you hoping to create?"
        else:
            return "I'm here to help you discover amazing design inspiration! What room or style are you most interested in exploring?"
    
    def _generate_board_management_response(self, message: str, boards: List[Dict[str, Any]]) -> str:
        """Generate response for board management"""
        if not boards:
            return "You don't have any inspiration boards yet! I can help you create your first one. What room would you like to start with?"
        else:
            board_count = len(boards)
            return f"You have {board_count} inspiration board{'s' if board_count != 1 else ''}. Would you like to add to an existing board or create a new one?"
    
    def _generate_color_guidance_response(self, message: str, style_prefs: Dict[str, Any]) -> str:
        """Generate response for color guidance"""
        if style_prefs and 'preferences' in style_prefs:
            return "Color is such an important part of design! Based on your style preferences, I can suggest colors that would work beautifully. What space are you planning colors for?"
        else:
            return "I'd love to help you with color choices! Color can completely transform a space. Tell me about the room and the mood you want to create."
    
    def _generate_room_specific_response(
        self, 
        message: str, 
        room_type: Optional[str], 
        style_prefs: Dict[str, Any]
    ) -> str:
        """Generate response for room-specific questions"""
        room = room_type or self._extract_room_from_message(message)
        
        if room and style_prefs:
            return f"Perfect! I can help you create a beautiful {room} that matches your design style. What's your main goal for this space?"
        elif room:
            return f"Great choice focusing on your {room}! Each room has unique design considerations. What's most important to you - functionality, aesthetics, or both?"
        else:
            return "I'd love to help with your room design! Which space are you working on, and what's your vision for it?"
    
    def _generate_general_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate general conversation response"""
        return "I'm here to help with all your design inspiration needs! Whether you want to explore styles, create mood boards, or get color advice, just let me know what interests you most."
    
    def _generate_inspiration_suggestions(
        self, 
        style_prefs: Dict[str, Any], 
        room_type: Optional[str]
    ) -> List[str]:
        """Generate inspiration-focused suggestions"""
        suggestions = []
        
        if room_type:
            suggestions.append(f"Upload inspiration images for your {room_type}")
            suggestions.append(f"Explore {room_type} design styles")
            
        if style_prefs and 'preferences' in style_prefs:
            primary_style = style_prefs['preferences'].get('primary_style', 'contemporary')
            suggestions.append(f"Find more {primary_style} design ideas")
        else:
            suggestions.append("Take a style quiz to discover your preferences")
            
        suggestions.append("Browse trending design ideas")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _generate_board_suggestions(self, boards: List[Dict[str, Any]], user_id: str) -> List[str]:
        """Generate board management suggestions"""
        suggestions = []
        
        if not boards:
            suggestions.extend([
                "Create your first inspiration board",
                "Upload some favorite design images",
                "Tell me about your dream room"
            ])
        else:
            suggestions.extend([
                "Add images to an existing board",
                "Create a new room inspiration board",
                "Review and organize your saved inspiration"
            ])
        
        return suggestions[:3]
    
    def _generate_color_suggestions(self, style_prefs: Dict[str, Any]) -> List[str]:
        """Generate color-focused suggestions"""
        return [
            "Explore color palettes for your style",
            "Learn about color psychology in design",
            "Create a custom color scheme"
        ]
    
    def _generate_room_suggestions(
        self, 
        room_type: Optional[str], 
        style_prefs: Dict[str, Any]
    ) -> List[str]:
        """Generate room-specific suggestions"""
        suggestions = []
        
        if room_type:
            suggestions.append(f"See trending {room_type} designs")
            suggestions.append(f"Upload your current {room_type} photos")
            suggestions.append(f"Explore {room_type} layouts and ideas")
        else:
            suggestions.extend([
                "Choose a room to focus on",
                "Upload inspiration images",
                "Explore different room types"
            ])
        
        return suggestions[:3]
    
    def _generate_general_suggestions(self) -> List[str]:
        """Generate general suggestions"""
        return [
            "Upload inspiration images to get started",
            "Tell me about your design style preferences",
            "Explore room-specific design ideas"
        ]
    
    def _extract_room_from_message(self, message: str) -> Optional[str]:
        """Extract room type from message"""
        message_lower = message.lower()
        
        room_keywords = {
            'kitchen': ['kitchen', 'cook'],
            'bathroom': ['bathroom', 'bath', 'shower'],
            'bedroom': ['bedroom', 'sleep'],
            'living_room': ['living', 'family', 'lounge'],
            'dining_room': ['dining', 'eat']
        }
        
        for room_type, keywords in room_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return room_type
        
        return None
    
    async def _save_user_message(
        self,
        conversation_id: str,
        user_id: str,
        message: str,
        session_id: str
    ) -> None:
        """Save user message to memory"""
        try:
            self.memory_manager.save_conversation_message(
                conversation_id=conversation_id,
                sender='user',
                content=message,
                message_type='text',
                metadata={'user_id': user_id, 'session_id': session_id}
            )
        except Exception as e:
            logger.error(f"Error saving user message: {e}")
    
    async def _save_agent_response(
        self,
        conversation_id: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save agent response to memory"""
        try:
            self.memory_manager.save_conversation_message(
                conversation_id=conversation_id,
                sender='agent',
                content=response,
                message_type='text',
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"Error saving agent response: {e}")
    
    def get_user_context(self, user_id: str) -> InspirationContextResponse:
        """Get user's inspiration context"""
        try:
            boards = self.memory_manager.get_user_inspiration_boards(user_id)
            style_prefs = self.memory_manager.get_style_preferences(user_id)
            
            return InspirationContextResponse(
                inspiration_boards=boards,
                style_preferences=style_prefs,
                favorite_colors=style_prefs.get('color_preferences', []),
                design_history=[],  # Would be populated from memory
                room_types=[board.get('room_type') for board in boards if board.get('room_type')]
            )
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return InspirationContextResponse()
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            'name': self.agent_name,
            'version': self.agent_version,
            'purpose': 'Design inspiration and mood board creation',
            'capabilities': [
                'Style analysis from inspiration images',
                'Mood board creation and management', 
                'Design style recommendations',
                'Color palette suggestions',
                'Room-specific inspiration guidance'
            ],
            'supported_rooms': [
                'kitchen', 'bathroom', 'bedroom', 
                'living_room', 'dining_room', 'office'
            ]
        }