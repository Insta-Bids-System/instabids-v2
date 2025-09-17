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
from ..services.vision_analyzer import VisionAnalyzer
from ..services.task_manager import TaskManager
from .conversational_flow import ConversationalFlow

logger = logging.getLogger(__name__)

class ImageWorkflow:
    """Complete image processing workflow"""
    
    def __init__(self):
        self.photo_manager = PhotoManager()
        self.memory_manager = MemoryManager()
        self.room_detector = RoomDetector()
        self.vision_analyzer = VisionAnalyzer()
        self.task_manager = TaskManager()
        self.conversational_flow = ConversationalFlow()
    
    async def process_image_upload(
        self, 
        request: UnifiedChatRequest,
        session_id: str,
        conversation_id: str
    ) -> Tuple[IRISResponse, Dict[str, Any]]:
        """
        Process uploaded images through conversational workflow
        
        Returns:
            Tuple of (IRISResponse, workflow_data)
        """
        
        # Use conversational flow for all image uploads
        return await self.conversational_flow.handle_conversation(
            request,
            session_id,
            conversation_state=request.metadata.get('conversation_state')
        )
        
        # Step 1: Detect room type from message
        room_detection = self.room_detector.detect_room_from_message(request.message)
        logger.info(f"Room detection result: {room_detection.room_type} (confidence: {room_detection.confidence:.2f})")
        
        # Step 2: Generate tags based on room and message
        auto_tags = self.photo_manager.generate_image_tags(
            room_type=room_detection.room_type,
            message=request.message,
            image_count=len(request.images)
        )
        
        # Step 3: Analyze images with Vision AI to detect issues
        vision_results = []
        for img in request.images:
            analysis = self.vision_analyzer.analyze_property_photo(
                image_data=img.data,
                room_type=room_detection.room_type,
                user_message=request.message
            )
            vision_results.append(analysis)
        
        # Combine analysis results
        all_issues = []
        all_tasks = []
        contractor_types = set()
        
        for result in vision_results:
            all_issues.extend(result.get('detected_issues', []))
            all_tasks.extend(result.get('recommended_tasks', []))
            contractor_types.update(result.get('contractor_types', []))
        
        image_analysis = ImageAnalysisResult(
            room_type=room_detection.room_type,
            auto_generated_tags=auto_tags,
            confidence_score=room_detection.confidence,
            detected_issues=all_issues,
            contractor_types=list(contractor_types),
            issue_count=len(all_issues)
        )
        
        # Step 4: Store images to property photos (iris_property only handles property photos)
        storage_results = self._store_property_images(
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
        
        # Step 6: Create tasks from detected issues
        created_tasks = []
        property_id = self.photo_manager._get_user_property_id(request.user_id)
        room_id = self.photo_manager.get_room_id_for_user(
            request.user_id, 
            room_detection.room_type
        )
        
        # Get photo IDs from storage results
        photo_ids = [result.get('photo_id') for result in storage_results if result.get('photo_id')]
        
        # Create a task for each detected issue
        for issue in all_issues:
            try:
                task = self.task_manager.create_task_from_image_analysis(
                    user_id=request.user_id,
                    property_id=property_id,
                    room_id=room_id,
                    room_type=room_detection.room_type,
                    image_analysis={
                        'description': issue.get('description', ''),
                        'detected_issues': issue
                    },
                    photo_ids=photo_ids
                )
                created_tasks.append(task)
            except Exception as e:
                logger.error(f"Failed to create task: {e}")
        
        # Step 7: Group tasks by contractor type for potential bid cards
        potential_bid_card_result = None
        if created_tasks:
            # Group tasks by contractor type
            grouped_tasks = {}
            for task in created_tasks:
                contractor = task.contractor_type
                if contractor not in grouped_tasks:
                    grouped_tasks[contractor] = []
                grouped_tasks[contractor].append(task)
            
            # Create potential bid cards for each contractor type
            bid_cards_created = []
            for contractor_type, tasks in grouped_tasks.items():
                try:
                    # Create a task group
                    task_ids = [task.id for task in tasks]
                    group_id = self.task_manager.create_task_group(
                        task_ids, 
                        f"{room_detection.room_type} - {contractor_type}"
                    )
                    
                    # Create potential bid card
                    from ..agent import IRISAgent
                    iris_agent = IRISAgent()
                    
                    bid_card_request = {
                        'user_id': request.user_id,
                        'room_type': room_detection.room_type,
                        'contractor_type': contractor_type,
                        'task_group_id': group_id,
                        'task_count': len(tasks),
                        'issue_description': f"{len(tasks)} {contractor_type} issues detected",
                        'session_id': session_id,
                        'conversation_id': conversation_id
                    }
                    
                    result = await iris_agent.create_potential_bid_card(bid_card_request)
                    if result and result.get('success'):
                        bid_cards_created.append(result)
                        # Link tasks to bid card
                        self.task_manager.convert_group_to_bid_card(
                            group_id, 
                            result.get('bid_card_id')
                        )
                except Exception as e:
                    logger.error(f"Failed to create bid card for {contractor_type}: {e}")
            
            if bid_cards_created:
                potential_bid_card_result = {
                    'success': True,
                    'bid_cards_created': len(bid_cards_created),
                    'contractor_types': list(grouped_tasks.keys()),
                    'total_tasks': len(created_tasks)
                }
        
        # Step 7: Generate response
        response = self._generate_image_response(
            request=request,
            room_detection=room_detection,
            auto_tags=auto_tags,
            storage_results=storage_results,
            potential_bid_card_result=potential_bid_card_result
        )
        
        # Step 8: Create workflow data for follow-up processing - FIX JSON serialization
        workflow_data = {
            'images_processed': len(request.images),
            'room_detection': room_detection.to_dict(),  # Use to_dict() method for JSON serialization
            'auto_tags': auto_tags,
            'image_analysis': image_analysis.dict(),
            'storage_results': storage_results,
            'needs_confirmation': room_detection.needs_confirmation,
            'potential_bid_card': potential_bid_card_result
        }
        
        return response, workflow_data
    
    def _store_property_images(
        self,
        request: UnifiedChatRequest,
        session_id: str,
        room_detection: RoomDetectionResult,
        auto_tags: List[str],
        image_analysis: ImageAnalysisResult
    ) -> List[Dict[str, Any]]:
        """Store images to property photos (iris_property only handles property photos)"""
        
        storage_results = []
        
        for i, img in enumerate(request.images):
            filename = img.filename or f"image_{i+1}_{int(datetime.now().timestamp())}.png"
            
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
    
    
    
    def _has_actionable_issue(self, message: str, image_analysis) -> bool:
        """
        IRIS Property agent assumes all images are property photos that may need contractor work
        Since we now have separate iris_inspiration agent, no need for decision logic
        """
        return True
    
    def _generate_image_response(
        self,
        request: UnifiedChatRequest,
        room_detection: RoomDetectionResult,
        auto_tags: List[str],
        storage_results: List[Dict[str, Any]],
        potential_bid_card_result: Optional[Dict[str, Any]] = None
    ) -> IRISResponse:
        """Generate response for image upload"""
        
        image_count = len(request.images)
        room_display = room_detection.room_type.replace('_', ' ').title()
        
        # Generate main response
        if room_detection.needs_confirmation:
            confirmation_msg = self.room_detector.generate_confirmation_message(room_detection)
            response_text = (
                f"I can see you've uploaded {image_count} image{'s' if image_count > 1 else ''} "
                f"of your {room_display}.\n\n"
                f"{confirmation_msg}\n\n"
                f"**Auto-Generated Tags**: {', '.join(auto_tags[:8])}"  # Limit to 8 tags for readability
            )
        else:
            # High confidence detection - iris_property always handles property photos
            base_response = (
                f"Perfect! I've saved {image_count} image{'s' if image_count > 1 else ''} "
                f"of your {room_display} to your property photos.\n\n"
                f"**Auto-Generated Tags**: {', '.join(auto_tags[:8])}\n\n"
            )
            
            # Add task and bid card information if created  
            if potential_bid_card_result and potential_bid_card_result.get('success'):
                task_count = potential_bid_card_result.get('total_tasks', 0)
                bid_count = potential_bid_card_result.get('bid_cards_created', 0)
                contractors = potential_bid_card_result.get('contractor_types', [])
                
                bid_card_info = (
                    f"✅ **Issues Detected**: I found {task_count} maintenance issue{'s' if task_count > 1 else ''} "
                    f"that need attention.\n\n"
                    f"📋 **Bid Cards Created**: {bid_count} project{'s' if bid_count > 1 else ''} ready for "
                    f"{', '.join(contractors)} contractor{'s' if len(contractors) > 1 else ''}.\n\n"
                )
                base_response += bid_card_info
            
            # iris_property always handles property photos - offer contractor next steps
            response_text = base_response + (
                f"Would you like me to help you with:\n"
                f"• Getting quotes from qualified contractors?\n"
                f"• Exploring your options for addressing this issue?\n"
                f"• Planning the project timeline and approach?"
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
                    "What specific issues need addressing?",
                    "Upload more photos of problem areas",
                    "Get quotes from kitchen contractors",
                    "Tell me about your repair timeline"
                ])
            elif room_type == "bathroom":
                suggestions.extend([
                    "Describe the plumbing or tile issues",
                    "Show me the water damage areas",
                    "Find qualified bathroom contractors",
                    "What's your budget for repairs?"
                ])
            elif room_type in ["backyard", "front_yard"]:
                suggestions.extend([
                    "What landscaping issues need fixing?",
                    "Show me drainage or irrigation problems",
                    "Get quotes from landscaping contractors",
                    "Describe any safety hazards"
                ])
            else:
                suggestions.extend([
                    "What maintenance issues are you seeing?",
                    "Upload photos of problem areas",
                    "Help me categorize by contractor type",
                    "Get repair quotes from contractors"
                ])
        
        return suggestions[:4]  # Limit to 4 suggestions
    
    def _create_no_images_response(self) -> IRISResponse:
        """Create response when no images are provided"""
        return IRISResponse(
            success=True,
            response=(
                "I can help you document and track maintenance issues in your property. "
                "Upload photos of any problems you're seeing - water damage, electrical issues, "
                "broken fixtures, etc. - and I'll help organize them into tasks for contractors."
            ),
            suggestions=[
                "Upload photos of problem areas",
                "Tell me about maintenance issues",
                "What room needs repairs?",
                "Help me organize repair tasks"
            ],
            interface="homeowner"
        )