"""
IRIS Image Workflow
Handles the complete image processing workflow from upload to storage
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime

from ..models.requests import UnifiedChatRequest
from ..models.responses import IRISResponse, ImageAnalysisResult
from ..services.photo_manager import PhotoManager
from ..services.memory_manager import MemoryManager
from ..services.room_detector import RoomDetector, RoomDetectionResult

logger = logging.getLogger(__name__)

class ImageWorkflow:
    """Complete image processing workflow"""
    
    def __init__(self):
        self.photo_manager = PhotoManager()
        self.memory_manager = MemoryManager()
        self.room_detector = RoomDetector()
    
    def process_image_upload(
        self, 
        request: UnifiedChatRequest,
        session_id: str,
        conversation_id: str
    ) -> Tuple[IRISResponse, Dict[str, Any]]:
        """
        Process uploaded images through complete workflow
        
        Returns:
            Tuple of (IRISResponse, workflow_data)
        """
        
        if not request.images:
            return self._create_no_images_response(), {}
        
        logger.info(f"Processing {len(request.images)} images for user {request.user_id}")
        
        # Step 1: Detect room type from message
        room_detection = self.room_detector.detect_room_from_message(request.message)
        logger.info(f"Room detection result: {room_detection.room_type} (confidence: {room_detection.confidence:.2f})")
        
        # Step 2: Generate tags based on room and message
        auto_tags = self.photo_manager.generate_image_tags(
            room_type=room_detection.room_type,
            message=request.message,
            image_count=len(request.images)
        )
        
        # Step 3: Analyze images (basic analysis for now)
        image_analysis = self.photo_manager.analyze_images_with_vision(request.images, request.message)
        image_analysis.room_type = room_detection.room_type
        image_analysis.auto_generated_tags = auto_tags
        image_analysis.confidence_score = room_detection.confidence
        
        # Step 4: Determine storage destination
        storage_results = self._store_images(
            request=request,
            session_id=session_id,
            room_detection=room_detection,
            auto_tags=auto_tags,
            image_analysis=image_analysis
        )
        
        # Step 5: Save analysis to memory
        self.memory_manager.save_image_analysis_memory(
            conversation_id=conversation_id,
            session_id=session_id,
            image_analysis=image_analysis.dict(),
            image_paths=[result.get('file_path', '') for result in storage_results]
        )
        
        # Step 6: Generate response
        response = self._generate_image_response(
            request=request,
            room_detection=room_detection,
            auto_tags=auto_tags,
            storage_results=storage_results
        )
        
        # Step 7: Create workflow data for follow-up processing
        workflow_data = {
            'images_processed': len(request.images),
            'room_detection': room_detection,
            'auto_tags': auto_tags,
            'image_analysis': image_analysis.dict(),
            'storage_results': storage_results,
            'needs_confirmation': room_detection.needs_confirmation
        }
        
        return response, workflow_data
    
    def _store_images(
        self,
        request: UnifiedChatRequest,
        session_id: str,
        room_detection: RoomDetectionResult,
        auto_tags: List[str],
        image_analysis: ImageAnalysisResult
    ) -> List[Dict[str, Any]]:
        """Store images to appropriate destination"""
        
        storage_results = []
        
        # Determine if this is inspiration or property photos
        is_inspiration = self._is_inspiration_upload(request, room_detection)
        
        for i, img in enumerate(request.images):
            filename = img.filename or f"image_{i+1}_{int(datetime.now().timestamp())}.png"
            
            if is_inspiration:
                # Store to inspiration board
                board_id = request.board_id or self._get_or_create_board(request.user_id, room_detection.room_type)
                
                image_id = self.photo_manager.store_to_inspiration_board(
                    user_id=request.user_id,
                    board_id=board_id,
                    image_data=img.data,
                    filename=filename,
                    session_id=session_id,
                    tags=auto_tags,
                    analysis_results=image_analysis.dict()
                )
                
                storage_results.append({
                    'type': 'inspiration',
                    'image_id': image_id,
                    'board_id': board_id,
                    'filename': filename
                })
                
            else:
                # Store to property photos
                room_id = self.photo_manager.get_room_id_for_user(
                    user_id=request.user_id,
                    room_type=room_detection.room_type
                )
                
                photo_id = self.photo_manager.store_to_property_photos(
                    user_id=request.user_id,
                    image_data=img.data,
                    filename=filename,
                    session_id=session_id,
                    room_id=room_id,
                    room_type=room_detection.room_type,
                    tags=auto_tags
                )
                
                storage_results.append({
                    'type': 'property',
                    'photo_id': photo_id,
                    'room_id': room_id,
                    'room_type': room_detection.room_type,
                    'filename': filename
                })
        
        return storage_results
    
    def _is_inspiration_upload(self, request: UnifiedChatRequest, room_detection: RoomDetectionResult) -> bool:
        """Determine if this is an inspiration upload vs property photos"""
        
        message_lower = request.message.lower()
        
        # Explicit board context
        if request.board_id or request.board_title:
            return True
        
        # Inspiration keywords
        inspiration_keywords = [
            'inspiration', 'inspire', 'idea', 'ideas', 'style', 'design',
            'like this', 'similar to', 'want something like', 'love this',
            'dream', 'goal', 'vision', 'mood board', 'examples'
        ]
        
        if any(keyword in message_lower for keyword in inspiration_keywords):
            return True
        
        # Property/current state keywords suggest property photos
        property_keywords = [
            'current', 'existing', 'my', 'our', 'before', 'now',
            'problem', 'issue', 'repair', 'fix', 'replace'
        ]
        
        if any(keyword in message_lower for keyword in property_keywords):
            return False
        
        # Default to inspiration for ambiguous cases
        return True
    
    def _get_or_create_board(self, user_id: str, room_type: str) -> str:
        """Get existing board or create new one"""
        
        # Try to get existing board for this room type
        existing_boards = self.memory_manager.get_user_inspiration_boards(user_id)
        
        for board in existing_boards:
            if board.get('room_type', '').lower() == room_type.lower():
                return board['id']
        
        # Create new board
        board_id = str(uuid.uuid4())
        board_title = f"{room_type.replace('_', ' ').title()} Inspiration"
        
        try:
            from database import db
            db.client.table('inspiration_boards').insert({
                'id': board_id,
                'user_id': user_id,
                'title': board_title,
                'room_type': room_type,
                'status': 'collecting',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
            
            logger.info(f"Created new inspiration board: {board_id}")
            
        except Exception as e:
            logger.error(f"Error creating inspiration board: {e}")
        
        return board_id
    
    def _generate_image_response(
        self,
        request: UnifiedChatRequest,
        room_detection: RoomDetectionResult,
        auto_tags: List[str],
        storage_results: List[Dict[str, Any]]
    ) -> IRISResponse:
        """Generate response for image upload"""
        
        image_count = len(request.images)
        room_display = room_detection.room_type.replace('_', ' ').title()
        
        # Generate main response
        if room_detection.needs_confirmation:
            confirmation_msg = self.room_detector.generate_confirmation_message(room_detection)
            response_text = (
                f"I can see you've uploaded {image_count} image{'s' if image_count > 1 else ''} "
                f"with some great design inspiration!\n\n"
                f"{confirmation_msg}\n\n"
                f"**Auto-Generated Tags**: {', '.join(auto_tags[:8])}"  # Limit to 8 tags for readability
            )
        else:
            # High confidence detection
            storage_type = "inspiration board" if storage_results and storage_results[0]['type'] == 'inspiration' else "property photos"
            
            response_text = (
                f"Perfect! I've saved {image_count} image{'s' if image_count > 1 else ''} "
                f"for your {room_display} to your {storage_type}.\n\n"
                f"**Auto-Generated Tags**: {', '.join(auto_tags[:8])}\n\n"
                f"What aspects of these images do you find most appealing? For example:\n"
                f"• The overall style and mood you want to achieve?\n"
                f"• Specific design elements that caught your eye?\n"
                f"• Colors and materials that inspire you?"
            )
        
        # Generate suggestions based on context
        suggestions = self._generate_image_suggestions(request, room_detection, storage_results)
        
        return IRISResponse(
            success=True,
            response=response_text,
            suggestions=suggestions,
            interface="homeowner",
            session_id=request.session_id,
            user_id=request.user_id,
            images_processed=image_count,
            image_analysis={
                'room_type': room_detection.room_type,
                'confidence': room_detection.confidence,
                'auto_tags': auto_tags,
                'needs_confirmation': room_detection.needs_confirmation
            }
        )
    
    def _generate_image_suggestions(
        self,
        request: UnifiedChatRequest,
        room_detection: RoomDetectionResult,
        storage_results: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate contextual suggestions after image upload"""
        
        suggestions = []
        
        if room_detection.needs_confirmation:
            # Room confirmation suggestions
            suggestions.extend([
                "Yes, that's correct",
                "Actually, it's for a different room",
                "Help me organize by room type"
            ])
        else:
            # High confidence suggestions
            room_type = room_detection.room_type
            
            if room_type == "kitchen":
                suggestions.extend([
                    "Tell me about your kitchen style preferences",
                    "What's your budget range for this project?",
                    "Show me more kitchen inspiration",
                    "Help me organize my kitchen ideas"
                ])
            elif room_type == "bathroom":
                suggestions.extend([
                    "Explore bathroom design styles",
                    "What's your timeline for this project?",
                    "Upload more bathroom inspiration",
                    "Tell me about your must-have features"
                ])
            elif room_type in ["backyard", "front_yard"]:
                suggestions.extend([
                    "Explore landscaping styles",
                    "What's your outdoor living vision?",
                    "Show me more outdoor inspiration",
                    "Tell me about your yard challenges"
                ])
            else:
                suggestions.extend([
                    "Tell me more about your design vision",
                    "What style elements do you love?",
                    "Upload more inspiration images",
                    "Help me organize my design ideas"
                ])
        
        return suggestions[:4]  # Limit to 4 suggestions
    
    def _create_no_images_response(self) -> IRISResponse:
        """Create response when no images are provided"""
        return IRISResponse(
            success=True,
            response=(
                "I'd love to help you with your design project! Feel free to upload some images "
                "of inspiration you've found or photos of your current space, and I can help you "
                "organize your ideas and develop your vision."
            ),
            suggestions=[
                "Upload inspiration images",
                "Tell me about your project goals",
                "What room are you working on?",
                "Help me get started with design planning"
            ],
            interface="homeowner"
        )