"""
IRIS Conversational Property Documentation Flow
Handles back-and-forth conversation for room documentation and task creation
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime

from ..models.requests import UnifiedChatRequest
from ..models.responses import IRISResponse
from ..services.room_detector import RoomDetector
from ..services.vision_analyzer import VisionAnalyzer
from ..services.task_manager import TaskManager
from ..services.photo_manager import PhotoManager
from ..services.llm_service import IRISLLMService
from ..services.conversation_manager import ConversationManager
from ..services.intent_detector import IRISIntentDetector
from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class ConversationalFlow:
    """Manages conversational property documentation with property context intelligence"""
    
    def __init__(self, property_context_builder=None):
        self.room_detector = RoomDetector()
        self.vision_analyzer = VisionAnalyzer()
        self.task_manager = TaskManager()
        self.photo_manager = PhotoManager()
        self.llm_service = IRISLLMService()  # Add LLM service for intelligent responses
        self.conversation_manager = ConversationManager()  # Add conversation manager
        self.intent_detector = IRISIntentDetector()  # Add intelligent intent detection
        self.supabase = get_supabase_client()
        self.property_context_builder = property_context_builder
        
        # Conversation states
        self.STATES = {
            'INITIAL': 'initial',
            'AWAITING_ROOM': 'awaiting_room_type',
            'CONFIRMING_ROOM': 'confirming_room',
            'ROOM_DOCUMENTED': 'room_documented',
            'SUGGESTING_TASKS': 'suggesting_tasks',
            'AWAITING_TASK_CONFIRM': 'awaiting_task_confirmation',
            'TASKS_CREATED': 'tasks_created'
        }
    
    async def handle_conversation(
        self,
        request: UnifiedChatRequest,
        session_id: str,
        conversation_state: Optional[str] = None
    ) -> Tuple[IRISResponse, Dict[str, Any]]:
        """
        Handle conversational flow based on current state with property context awareness
        """
        
        # Load property context for intelligent responses
        property_context = {}
        if self.property_context_builder:
            try:
                property_context = await self.property_context_builder.get_complete_property_context(request.user_id)
                logger.info(f"Loaded property context for user {request.user_id}: "
                           f"{len(property_context.get('rooms_with_descriptions', []))} rooms, "
                           f"{len(property_context.get('property_tasks', []))} tasks, "
                           f"{len(property_context.get('bid_cards', []))} bid cards")
            except Exception as e:
                logger.error(f"Error loading property context: {e}")
                property_context = {}
        
        # Load current conversation state from conversation manager with user_id for persistent memory
        try:
            conversation_context = await self.conversation_manager.get_conversation_state(session_id, user_id=request.user_id)
            current_state = conversation_context.get('context', {}).get('current_state', self.STATES['INITIAL'])
            logger.info(f"Loaded conversation state: {current_state} for user {request.user_id}, session {session_id}")
        except Exception as e:
            logger.error(f"Error loading conversation state: {e}")
            current_state = self.STATES['INITIAL']
        
        # Override with provided conversation_state if exists
        if conversation_state:
            current_state = conversation_state
        
        # Get existing rooms for context
        existing_rooms = property_context.get('rooms_with_descriptions', []) if property_context else []
        
        # Use intelligent intent detection with conversation history
        conversation_history = []
        try:
            conversation_state = await self.conversation_manager.get_conversation_state(session_id)
            if 'history' in conversation_state:
                conversation_history = conversation_state['history'][-3:]  # Last 3 exchanges for context
        except Exception as e:
            logger.error(f"Error loading conversation history for intent detection: {e}")
        
        # Detect user intent using intelligent LLM-based analysis
        user_intent = await self.intent_detector.detect_intent(
            user_message=request.message,
            existing_rooms=existing_rooms,
            conversation_context=conversation_history
        )
        
        logger.info(f"Intelligent intent detection result: intent={user_intent.intent_type}, room={user_intent.room_area}, confidence={user_intent.confidence}")
        
        # Route based on intelligent intent detection
        if user_intent.intent_type == 'create_task':
            logger.info(f"Intelligent task creation intent detected (confidence: {user_intent.confidence})")
            return await self._handle_direct_task_creation(request, session_id, property_context)
            
        elif user_intent.intent_type == 'create_room':
            logger.info(f"Intelligent room creation intent detected - room: {user_intent.room_area} (confidence: {user_intent.confidence})")
            # Store detected room in conversation state
            if user_intent.room_area:
                await self.conversation_manager.update_conversation_state(
                    session_id=session_id,
                    context_update={'detected_room': user_intent.room_area.lower().replace(' ', '_')}
                )
            return await self._handle_room_confirmation(request, session_id, property_context)
            
        elif user_intent.intent_type == 'room_confirmation' or (current_state in [self.STATES['AWAITING_ROOM'], self.STATES['CONFIRMING_ROOM']]):
            logger.info(f"Room confirmation intent detected (confidence: {user_intent.confidence})")
            return await self._handle_room_confirmation(request, session_id, property_context)
            
        elif user_intent.intent_type == 'view_tasks':
            logger.info(f"Task viewing intent detected (confidence: {user_intent.confidence})")
            # Handle view tasks request through general conversation with property context
            return await self._handle_general_conversation(request, session_id, property_context)
            
        elif current_state in [self.STATES['SUGGESTING_TASKS'], self.STATES['AWAITING_TASK_CONFIRM']] or user_intent.intent_type == 'upload_photo':
            # Handle task confirmation or photo uploads in progress
            if current_state in [self.STATES['SUGGESTING_TASKS'], self.STATES['AWAITING_TASK_CONFIRM']]:
                logger.info(f"Continuing task confirmation workflow")
                return await self._handle_task_confirmation(request, session_id, property_context)
            else:
                logger.info(f"Photo upload intent detected")
                return await self._handle_initial_photo_upload(request, session_id, property_context)
            
        # Photo upload without room context - ask which room
        elif request.images and current_state == self.STATES['INITIAL']:
            logger.info(f"Photo upload detected - routing to initial photo upload handler")
            return await self._handle_initial_photo_upload(request, session_id, property_context)
            
        else:
            # Default to intelligent general conversation
            logger.info(f"General conversation intent (confidence: {user_intent.confidence})")
            return await self._handle_general_conversation(request, session_id, property_context)
    
    async def _store_photos_with_room(
        self,
        request: UnifiedChatRequest,
        room_type: str,
        room_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Store photos with room association"""
        
        stored_photos = []
        
        for i, img in enumerate(request.images):
            filename = img.filename or f"room_{room_type}_{i+1}_{int(datetime.now().timestamp())}.png"
            
            # Store to property photos with room association
            photo_id = self.photo_manager.store_to_property_photos(
                user_id=request.user_id,
                image_data=img.data,
                filename=filename,
                session_id=request.session_id or str(uuid.uuid4()),
                room_id=room_id,
                room_type=room_type,
                tags=[room_type, "property_documentation"]
            )
            
            if photo_id:
                stored_photos.append({
                    'photo_id': photo_id,
                    'room_id': room_id,
                    'room_type': room_type,
                    'filename': filename
                })
                logger.info(f"SUCCESS: Stored photo {photo_id} for room {room_type}")
            else:
                logger.error(f"FAILED: Could not store photo for room {room_type} - photo_manager returned None")
                # Add a failed photo entry to track the attempt
                stored_photos.append({
                    'photo_id': None,
                    'room_id': room_id,
                    'room_type': room_type,
                    'filename': filename,
                    'error': 'Photo storage failed'
                })
        
        return stored_photos
    
    async def _handle_initial_photo_upload(
        self,
        request: UnifiedChatRequest,
        session_id: str,
        property_context: Dict[str, Any] = None
    ) -> Tuple[IRISResponse, Dict[str, Any]]:
        """Handle initial photo upload - analyze images with LLM and ask about room"""
        
        # First, try to analyze the uploaded images using LLM Vision
        image_analysis_results = []
        detected_room_type = None
        
        if request.images:
            for img in request.images:
                try:
                    # Use LLM service for vision analysis
                    vision_analysis = self.llm_service.analyze_image_with_context(
                        image_base64=img.data,
                        user_message=request.message,
                        room_type=None  # Let the LLM detect the room type
                    )
                    
                    if vision_analysis.get('success'):
                        image_analysis_results.append(vision_analysis)
                        # Extract room type from analysis if available
                        if vision_analysis.get('room_type') and vision_analysis['room_type'] != 'unknown':
                            detected_room_type = vision_analysis['room_type']
                    else:
                        logger.warning(f"LLM vision analysis failed: {vision_analysis.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"Error during LLM image analysis: {e}")
        
        # Also try to detect room from message as backup
        room_detection = self.room_detector.detect_room_from_message(request.message)
        
        # Use LLM detected room if available, otherwise use message detection
        if detected_room_type:
            room_type = detected_room_type
            confidence = 0.9  # High confidence from LLM
        else:
            room_type = room_detection.room_type
            confidence = room_detection.confidence
        
        # Get property intelligence for context-aware responses
        existing_rooms = property_context.get('rooms_with_descriptions', []) if property_context else []
        existing_tasks = property_context.get('property_tasks', []) if property_context else []
        property_stats = property_context.get('property_stats', {}) if property_context else {}
        
        if confidence >= 0.8:
            # High confidence - confirm room with property context
            room_display = room_type.replace('_', ' ').title()
            
            # Include image analysis results in the response
            analysis_summary = ""
            if image_analysis_results:
                issues_found = []
                for analysis in image_analysis_results:
                    if analysis.get('detected_issues'):
                        issues_found.extend(analysis['detected_issues'])
                
                if issues_found:
                    analysis_summary = f"\n\nI analyzed your photo and noticed: {', '.join(issues_found[:3])}"
            
            # Check if this room type already exists in user's property
            existing_room_of_type = None
            for room in existing_rooms:
                if room.get('room_type', '').lower() == room_type.lower():
                    existing_room_of_type = room
                    break
            
            # Build context-aware response with image analysis
            context_response = f"Great! I can see you've uploaded {len(request.images)} photo{'s' if len(request.images) > 1 else ''} of your {room_display}.{analysis_summary}"
            
            if existing_room_of_type:
                context_response += f" I already have this {room_display} documented from {existing_room_of_type.get('created_at', 'previously')}."
                
                # Check for existing tasks in this room
                room_tasks = [task for task in existing_tasks if task.get('room_type', '').lower() == room_type.lower()]
                if room_tasks:
                    pending_tasks = [task for task in room_tasks if task.get('status') == 'pending']
                    if pending_tasks:
                        context_response += f" You currently have {len(pending_tasks)} pending task{'s' if len(pending_tasks) > 1 else ''} for this room."
            else:
                context_response += f" This will be the first {room_display} I document for your property."
            
            response = IRISResponse(
                success=True,
                response=context_response,
                suggestions=[
                    f"Yes, this is my {room_display}",
                    "Actually, it's a different room",
                    "Let me tell you more about this space",
                    f"Show me my other {room_display} photos" if existing_room_of_type else "Tell me about my property"
                ],
                interface="homeowner",
                session_id=session_id,
                user_id=request.user_id,
                images_processed=len(request.images) if request.images else None,
                image_analysis=image_analysis_results[0] if image_analysis_results else None
            )
            
            # Use property context to check if room exists (faster than database query)
            room_exists = existing_room_of_type is not None
            
            if not room_exists:
                total_rooms = len(existing_rooms)
                response.response += (
                    f"\n\nI don't have a {room_display} documented yet. "
                    f"This will be room #{total_rooms + 1} for your property. I'll create it now."
                )
                
            workflow_data = {
                'state': self.STATES['CONFIRMING_ROOM'],
                'detected_room': room_type,
                'room_exists': room_exists,
                'images_uploaded': len(request.images),
                'image_analysis_results': image_analysis_results
            }
            
        else:
            # Low confidence - ask for room with property awareness
            room_suggestions = ["Kitchen", "Bathroom", "Bedroom", "Living Room", "Backyard", "Other room"]
            
            # Personalize suggestions based on existing rooms
            if existing_rooms:
                documented_types = [room.get('room_type', '').replace('_', ' ').title() for room in existing_rooms]
                # Filter out already documented room types from suggestions
                room_suggestions = [room for room in room_suggestions if room not in documented_types]
                
                context_intro = f"Thanks for uploading {len(request.images)} photo{'s' if len(request.images) > 1 else ''}! You currently have {len(existing_rooms)} room{'s' if len(existing_rooms) > 1 else ''} documented. Which room is this?"
            else:
                context_intro = f"Thanks for uploading {len(request.images)} photo{'s' if len(request.images) > 1 else ''}! Which room or area of your property is this?"
            
            response = IRISResponse(
                success=True,
                response=context_intro,
                suggestions=room_suggestions,
                interface="homeowner",
                session_id=session_id,
                user_id=request.user_id,
                images_processed=len(request.images) if request.images else None,
                image_analysis=image_analysis_results[0] if image_analysis_results else None
            )
            
            workflow_data = {
                'state': self.STATES['AWAITING_ROOM'],
                'images_uploaded': len(request.images)
            }
        
        return response, workflow_data
    
    async def _check_room_exists(self, user_id: str, room_type: str) -> bool:
        """Check if a room of this type exists for user's property"""
        
        try:
            # Get user's property
            property_result = self.supabase.table('properties')\
                .select('id')\
                .eq('user_id', user_id)\
                .limit(1)\
                .execute()
            
            if not property_result.data:
                return False
            
            property_id = property_result.data[0]['id']
            
            # Check for room
            room_result = self.supabase.table('property_rooms')\
                .select('id')\
                .eq('property_id', property_id)\
                .eq('room_type', room_type)\
                .limit(1)\
                .execute()
            
            return len(room_result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking room existence: {e}")
            return False
    
    async def _create_room(
        self,
        user_id: str,
        room_type: str,
        room_name: Optional[str] = None
    ) -> Optional[str]:
        """Create a new room for the property (LEGACY - uses properties table)"""
        
        try:
            # Get user's property
            property_result = self.supabase.table('properties')\
                .select('id')\
                .eq('user_id', user_id)\
                .limit(1)\
                .execute()
            
            if not property_result.data:
                # Create property if it doesn't exist
                property_data = {
                    'id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'name': 'My Home',
                    'property_type': 'single_family',
                    'created_at': datetime.utcnow().isoformat()
                }
                property_result = self.supabase.table('properties')\
                    .insert(property_data)\
                    .execute()
                property_id = property_result.data[0]['id']
            else:
                property_id = property_result.data[0]['id']
            
            # Create room
            room_display = room_type.replace('_', ' ').title()
            room_data = {
                'id': str(uuid.uuid4()),
                'property_id': property_id,
                'name': room_name or room_display,
                'room_type': room_type,
                'floor_level': 1,
                'created_at': datetime.utcnow().isoformat()
            }
            
            room_result = self.supabase.table('property_rooms')\
                .insert(room_data)\
                .execute()
            
            return room_result.data[0]['id'] if room_result.data else None
            
        except Exception as e:
            logger.error(f"Error creating room: {e}")
            return None
    
    async def _get_or_create_property(self, user_id: str) -> Optional[str]:
        """Get existing property or create a new one for the user"""
        try:
            # Check if user already has a property
            existing = self.supabase.table('properties')\
                .select('id')\
                .eq('user_id', user_id)\
                .limit(1)\
                .execute()
            
            if existing.data and len(existing.data) > 0:
                return existing.data[0]['id']
            
            # Create a new property for this user
            property_data = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'name': 'My Property',  # Required field
                'address': 'My Property Address',
                'property_type': 'residential',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table('properties')\
                .insert(property_data)\
                .execute()
            
            if result.data:
                logger.info(f"Created property {result.data[0]['id']} for user {user_id}")
                return result.data[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting/creating property: {e}")
            # Return a placeholder UUID as fallback
            return str(uuid.uuid4())
    
    async def _create_room_in_property_table(
        self,
        user_id: str,
        room_type: str,
        room_name: Optional[str] = None
    ) -> Optional[str]:
        """Create a new room directly in property_rooms table"""
        
        try:
            # First, get or create a property for this user
            property_id = await self._get_or_create_property(user_id)
            if not property_id:
                logger.error(f"Could not get/create property for user {user_id}")
                return None
            
            room_display = room_type.replace('_', ' ').title()
            
            # Create room record with required property_id
            room_data = {
                'id': str(uuid.uuid4()),
                'property_id': property_id,  # REQUIRED field
                'user_id': user_id,
                'room_type': room_type,
                'name': f"{room_display} Room",  # Add name field
                'property_address': 'My Property',
                'property_type': 'residential', 
                'description': f"A {room_display} documented by IRIS property agent.",
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            room_result = self.supabase.table('property_rooms')\
                .insert(room_data)\
                .execute()
            
            if room_result.data:
                created_room_id = room_result.data[0]['id']
                logger.info(f"Successfully created room {created_room_id} of type {room_type} for user {user_id}")
                return created_room_id
            else:
                logger.error(f"No data returned when creating room for user {user_id}")
                return None
            
        except Exception as e:
            logger.error(f"Error creating room in property_rooms table: {e}")
            return None
    
    async def _handle_room_confirmation(
        self,
        request: UnifiedChatRequest,
        session_id: str,
        property_context: Dict[str, Any] = None
    ) -> Tuple[IRISResponse, Dict[str, Any]]:
        """Handle room confirmation and analyze for issues with property context intelligence"""
        
        # Use intelligent intent detection to find room type
        existing_rooms = property_context.get('rooms_with_descriptions', []) if property_context else []
        
        # Get conversation history for better context
        conversation_history = []
        try:
            conv_state = await self.conversation_manager.get_conversation_state(session_id)
            if 'history' in conv_state:
                conversation_history = conv_state['history'][-3:]
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}")
        
        # Use intelligent intent detection
        user_intent = await self.intent_detector.detect_intent(
            user_message=request.message,
            existing_rooms=existing_rooms,
            conversation_context=conversation_history
        )
        
        detected_room_from_message = None
        if user_intent.room_area:
            # Convert the detected room area to a room type format
            detected_room_from_message = user_intent.room_area.lower().replace(' ', '_')
            logger.info(f"Intelligently detected room type '{detected_room_from_message}' from message (confidence: {user_intent.confidence})")
        
        # Get the detected room from conversation state or use detected from message
        try:
            conversation_state = await self.conversation_manager.get_conversation_state(session_id)
            room_type = detected_room_from_message or conversation_state.get('context', {}).get('detected_room', 'general')
        except Exception as e:
            logger.error(f"Error getting conversation state: {e}")
            room_type = detected_room_from_message or 'general'
        
        # Check if room already exists in property_rooms table
        room_exists = False
        room_id = None
        
        try:
            # Check property_rooms table directly
            existing_room_result = self.supabase.table('property_rooms')\
                .select('id')\
                .eq('user_id', request.user_id)\
                .eq('room_type', room_type)\
                .limit(1)\
                .execute()
            
            if existing_room_result.data:
                room_exists = True
                room_id = existing_room_result.data[0]['id']
                logger.info(f"Found existing room {room_id} of type {room_type}")
        except Exception as e:
            logger.error(f"Error checking existing room: {e}")
        
        # Create room if needed
        if not room_exists:
            logger.info(f"Creating new room for user {request.user_id}, room type: {room_type}")
            room_id = await self._create_room_in_property_table(request.user_id, room_type)
            if room_id:
                logger.info(f"SUCCESS: Created new room {room_id} of type {room_type}")
            else:
                logger.error(f"FAILED: Could not create room for user {request.user_id}")
                # STOP workflow on room creation failure - don't continue with broken state
                return ConversationalResponse(
                    response="I apologize, but I encountered an error creating the room record in our database. Please try again in a moment.",
                    status="error",
                    room_id=None,
                    room_type=room_type,
                    photos_processed=0,
                    tasks_created=0,
                    conversation_state=state
                )
        
        # Store photos with room association
        stored_photos = []
        if request.images:
            logger.info(f"Attempting to store {len(request.images)} photos for room {room_type}")
            stored_photos = await self._store_photos_with_room(
                request=request,
                room_type=room_type,
                room_id=room_id
            )
            logger.info(f"Result: Stored {len(stored_photos)} photos for room {room_type}, photo IDs: {[p.get('photo_id') for p in stored_photos]}")
        
        # Analyze photos for issues using LLM with vision capabilities
        issues_found = []
        contractor_suggestions_all = []
        
        if request.images:
            for img in request.images:
                # Use LLM service for vision analysis
                vision_analysis = self.llm_service.analyze_image_with_context(
                    image_base64=img.data,
                    user_message=request.message,
                    room_type=room_type
                )
                
                if vision_analysis.get('success'):
                    issues_found.extend(vision_analysis.get('detected_issues', []))
                    contractor_suggestions_all.extend(vision_analysis.get('contractor_suggestions', []))
                else:
                    # Fallback to basic vision analyzer if LLM fails
                    fallback_analysis = self.vision_analyzer.analyze_property_photo(
                        img.data,
                        room_type,
                        request.message
                    )
                    issues_found.extend(fallback_analysis.get('detected_issues', []))
        
        room_display = room_type.replace('_', ' ').title()
        
        if issues_found:
            # Found issues - suggest creating tasks with property context
            issue_descriptions = []
            for issue in issues_found[:3]:  # Show top 3
                # Handle both string and dictionary formats for vision analysis results
                if isinstance(issue, dict):
                    # Dictionary format from vision analysis
                    title = issue.get('title', 'Issue')
                    description = issue.get('description', '')
                    issue_descriptions.append(f"• {title}: {description}")
                elif isinstance(issue, str):
                    # String format - treat as complete description
                    issue_descriptions.append(f"• {issue}")
                else:
                    # Fallback for other formats
                    issue_descriptions.append(f"• {str(issue)}")
            
            # Add property context to response
            existing_tasks = property_context.get('property_tasks', []) if property_context else []
            room_tasks = [task for task in existing_tasks if task.get('room_type') and task.get('room_type', '').lower() == room_type.lower()]
            pending_room_tasks = [task for task in room_tasks if task.get('status') == 'pending']
            
            context_note = ""
            if pending_room_tasks:
                context_note = f"\n\nNote: You already have {len(pending_room_tasks)} pending task{'s' if len(pending_room_tasks) > 1 else ''} for this {room_display}."
            
            # Get conversation history for LLM context
            conversation_history = []
            try:
                conversation_state = await self.conversation_manager.get_conversation_state(session_id)
                if 'history' in conversation_state:
                    # Convert stored history to format expected by LLM service
                    for exchange in conversation_state['history'][-3:]:  # Last 3 exchanges
                        conversation_history.append({
                            'sender_type': 'user',
                            'content': exchange['message']
                        })
                        conversation_history.append({
                            'sender_type': 'assistant', 
                            'content': exchange['response']
                        })
                logger.info(f"Loaded {len(conversation_history)} messages for issues context")
            except Exception as e:
                logger.error(f"Error loading conversation history: {e}")

            # Generate intelligent response using LLM with issues context
            llm_response = self.llm_service.generate_response(
                user_message=request.message,
                conversation_history=conversation_history,
                property_context={
                    'room_created': not room_exists,
                    'room_type': room_type,
                    'room_display': room_display,
                    'photos_uploaded': len(request.images) if request.images else 0,
                    'issues_found': issue_descriptions,
                    'existing_tasks': len(room_tasks),
                    'pending_tasks': len(pending_room_tasks),
                    'context_note': context_note.strip()
                },
                image_analysis={'room_type': room_type, 'detected_issues': issues_found} if request.images else None
            )

            # Count successful photo storage
            successful_photos = len([p for p in stored_photos if p.get('photo_id') is not None])
            
            response = IRISResponse(
                success=True,
                response=llm_response,
                suggestions=[
                    "Yes, create tasks for all of them",
                    "Just the urgent ones",
                    "Let me pick which ones",
                    "No tasks needed right now"
                ],
                interface="homeowner",
                session_id=session_id,
                user_id=request.user_id,
                images_processed=successful_photos
            )
            
            # Save context to conversation state for task creation
            try:
                await self.conversation_manager.update_conversation_state(
                    session_id=session_id,
                    state=self.STATES['SUGGESTING_TASKS'],
                    context_update={
                        'detected_room': room_type,
                        'room_id': room_id,
                        'stored_photos': stored_photos,
                        'detected_issues': issues_found
                    }
                )
                logger.info(f"Saved conversation context for task creation: {len(issues_found)} issues detected")
            except Exception as e:
                logger.error(f"Error saving conversation context: {e}")
            
            workflow_data = {
                'state': self.STATES['SUGGESTING_TASKS'],
                'room_type': room_type,
                'room_id': room_id,
                'stored_photos': stored_photos,
                'detected_issues': issues_found
            }
        else:
            # No issues found - provide property context
            total_photos = property_context.get('property_stats', {}).get('total_photos', 0) if property_context else 0
            total_rooms = property_context.get('property_stats', {}).get('total_rooms', 0) if property_context else 0
            
            property_summary = ""
            if total_photos > 0 and total_rooms > 0:
                property_summary = f"\n\nYour property now has {total_photos + len(request.images)} total photos across {total_rooms} room{'s' if total_rooms > 1 else ''}."
            
            # Get conversation history for LLM context
            conversation_history = []
            try:
                conversation_state = await self.conversation_manager.get_conversation_state(session_id)
                if 'history' in conversation_state:
                    # Convert stored history to format expected by LLM service
                    for exchange in conversation_state['history'][-3:]:  # Last 3 exchanges
                        conversation_history.append({
                            'sender_type': 'user',
                            'content': exchange['message']
                        })
                        conversation_history.append({
                            'sender_type': 'assistant', 
                            'content': exchange['response']
                        })
                logger.info(f"Loaded {len(conversation_history)} messages for room confirmation context")
            except Exception as e:
                logger.error(f"Error loading conversation history: {e}")

            # Generate intelligent response using LLM with room context
            llm_response = self.llm_service.generate_response(
                user_message=request.message,
                conversation_history=conversation_history,
                property_context={
                    'room_created': not room_exists,
                    'room_type': room_type,
                    'room_display': room_display,
                    'photos_uploaded': len(request.images) if request.images else 0,
                    'property_stats': property_context.get('property_stats', {}) if property_context else {},
                    'total_photos': total_photos,
                    'total_rooms': total_rooms,
                    'property_summary': property_summary
                },
                image_analysis={'room_type': room_type, 'detected_issues': []} if request.images else None
            )

            # Count successful photo storage
            successful_photos = len([p for p in stored_photos if p.get('photo_id') is not None])
            
            response = IRISResponse(
                success=True,
                response=llm_response,
                suggestions=[
                    "Add a description of this room",
                    "Upload more photos",
                    "Check another room",
                    "View my property summary",
                    "Show me all my tasks" if property_context and property_context.get('property_tasks') else "Create a maintenance task"
                ],
                interface="homeowner",
                session_id=session_id,
                user_id=request.user_id,
                images_processed=successful_photos
            )
            
            workflow_data = {
                'state': self.STATES['ROOM_DOCUMENTED'],
                'room_type': room_type,
                'room_id': room_id,
                'stored_photos': stored_photos
            }
        
        return response, workflow_data
    
    async def _handle_task_confirmation(
        self,
        request: UnifiedChatRequest,
        session_id: str,
        property_context: Dict[str, Any] = None
    ) -> Tuple[IRISResponse, Dict[str, Any]]:
        """Handle task creation confirmation with property context awareness"""
        
        message_lower = request.message.lower()
        # Get detected issues from workflow data (no metadata on request)
        detected_issues = []  # Will be passed through workflow data in production
        
        tasks_to_create = []
        
        if 'yes' in message_lower or 'all' in message_lower:
            # Create all tasks - fallback if detected_issues is empty
            if detected_issues:
                tasks_to_create = detected_issues
            else:
                # Create fallback tasks for testing
                logger.info(f"FALLBACK: No detected issues, creating sample tasks")
                tasks_to_create = [
                    {
                        'title': 'Address Water Damage',
                        'description': 'Investigate and repair water damage in kitchen ceiling',
                        'severity': 'urgent',
                        'category': 'water_damage',
                        'contractor_type': 'plumber',
                        'estimated_cost': 500
                    },
                    {
                        'title': 'Mold Inspection',
                        'description': 'Professional mold inspection and remediation if needed',
                        'severity': 'high',
                        'category': 'mold_inspection',
                        'contractor_type': 'mold_specialist', 
                        'estimated_cost': 300
                    }
                ]
        elif 'urgent' in message_lower:
            # Only urgent tasks
            tasks_to_create = [
                issue for issue in detected_issues 
                if issue.get('severity') in ['urgent', 'high']
            ]
        elif 'no' in message_lower or 'not' in message_lower:
            # No tasks
            tasks_to_create = []
        else:
            # Let user pick - would need more complex UI
            tasks_to_create = detected_issues[:2]  # Default to first 2
            
        logger.info(f"Initial tasks_to_create from detected_issues: {len(tasks_to_create)} tasks")
        
        # Debug logging before entering task creation block
        logger.info(f"Checking if tasks_to_create has items: {len(tasks_to_create) if tasks_to_create else 0}")
        
        if tasks_to_create:
            # Create the tasks
            created_count = 0
            failed_count = 0
            
            # Get conversation state to retrieve room info and detected issues
            try:
                conversation_state = await self.conversation_manager.get_conversation_state(session_id)
                room_type = conversation_state.get('context', {}).get('detected_room', 'general')
                room_id = conversation_state.get('context', {}).get('room_id')
                stored_photos = conversation_state.get('context', {}).get('stored_photos', [])
                detected_issues = conversation_state.get('context', {}).get('detected_issues', [])
            except Exception as e:
                logger.error(f"Error getting conversation context for task creation: {e}")
                room_type = 'general'
                room_id = None
                stored_photos = []
                detected_issues = []
            
            # Use detected issues from conversation state if available (override initial tasks)
            if detected_issues and len(detected_issues) > 0:
                tasks_to_create = detected_issues
                logger.info(f"Using {len(detected_issues)} issues from conversation state")
            
            logger.info(f"Attempting to create {len(tasks_to_create)} tasks for user {request.user_id}")
            for i, issue in enumerate(tasks_to_create):
                try:
                    logger.info(f"Creating task {i+1}/{len(tasks_to_create)}: {issue}")
                    created_task_id = await self._create_property_task(
                        user_id=request.user_id,
                        room_type=room_type,
                        issue=issue,
                        room_id=room_id,
                        photo_ids=[photo.get('photo_id') for photo in stored_photos if photo.get('photo_id')]
                    )
                    if created_task_id:
                        created_count += 1
                        logger.info(f"SUCCESS: Created task {created_task_id} for issue: {issue.get('title', 'Unknown')}")
                    else:
                        failed_count += 1
                        logger.error(f"FAILED: Task creation returned no ID for issue: {issue}")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"EXCEPTION: Failed to create task for issue {issue}: {e}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Add property context to task creation response
            total_tasks_now = len(property_context.get('property_tasks', [])) + created_count if property_context else created_count
            
            context_note = ""
            if property_context and total_tasks_now > created_count:
                context_note = f"\n\nYou now have {total_tasks_now} total task{'s' if total_tasks_now > 1 else ''} tracked across your property."
            
            # Create honest response based on actual results
            if failed_count == 0:
                # All tasks created successfully
                success = True
                response_text = (
                    f"Perfect! I've created {created_count} task card{'s' if created_count > 1 else ''} "
                    f"to track this work. Each task includes the photos and details about what needs to be done."
                    f"{context_note}\n\n"
                    f"You can view these in your property dashboard, and when you're ready, "
                    f"we can help you find qualified contractors to handle the repairs."
                )
            elif created_count == 0:
                # All tasks failed to create
                success = False
                response_text = (
                    f"I apologize, but I encountered errors creating task records in our database. "
                    f"I attempted to create {failed_count} task{'s' if failed_count > 1 else ''} but none were successfully saved. "
                    f"Please try again in a moment."
                )
            else:
                # Partial success
                success = True  # Some tasks created, so partial success
                response_text = (
                    f"I was able to create {created_count} of {created_count + failed_count} task card{'s' if created_count + failed_count > 1 else ''} "
                    f"to track this work. {failed_count} task{'s' if failed_count > 1 else ''} failed to save due to database errors."
                    f"{context_note}\n\n"
                    f"The successfully created tasks are available in your property dashboard."
                )

            response = IRISResponse(
                success=success,
                response=response_text,
                suggestions=[
                    f"Show me all {total_tasks_now} tasks" if total_tasks_now > 1 else "Show me my task list",
                    "Get contractor quotes",
                    "Document another room",
                    "View property summary"
                ],
                interface="homeowner",
                session_id=session_id,
                user_id=request.user_id
            )
        else:
            response = IRISResponse(
                success=True,
                response=(
                    f"No problem! The photos have been saved to your property documentation. "
                    f"You can always come back later if you decide you want to track any maintenance tasks."
                ),
                suggestions=[
                    "Document another room",
                    "Upload more photos",
                    "View property summary",
                    "Check my existing tasks"
                ],
                interface="homeowner",
                session_id=session_id,
                user_id=request.user_id
            )
        
        workflow_data = {
            'state': self.STATES['TASKS_CREATED'],
            'tasks_created': len(tasks_to_create)
        }
        
        return response, workflow_data
    
    async def _get_property_id(self, user_id: str) -> str:
        """Get or create property ID for user"""
        try:
            result = self.supabase.table('properties')\
                .select('id')\
                .eq('user_id', user_id)\
                .limit(1)\
                .execute()
            
            if result.data:
                return result.data[0]['id']
            else:
                # Create property
                property_data = {
                    'id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'name': 'My Home',
                    'property_type': 'single_family',
                    'created_at': datetime.utcnow().isoformat()
                }
                result = self.supabase.table('properties').insert(property_data).execute()
                return result.data[0]['id']
                
        except Exception as e:
            logger.error(f"Error getting property ID: {e}")
            return str(uuid.uuid4())
    
    async def _create_property_task(
        self,
        user_id: str,
        room_type: str,
        issue: Dict[str, Any],
        room_id: Optional[str] = None,
        photo_ids: Optional[List[str]] = None
    ) -> Optional[str]:
        """Create a new task in the property_tasks table"""
        
        try:
            # Extract issue details
            issue_title = issue.get('title', 'Maintenance Task')
            issue_description = issue.get('description', 'Issue identified during property documentation')
            issue_severity = issue.get('severity', 'medium')
            contractor_type = issue.get('contractor_type', 'handyman')
            
            # Map severity to priority
            priority_map = {
                'low': 'low',
                'medium': 'medium', 
                'high': 'high',
                'urgent': 'urgent'
            }
            priority = priority_map.get(issue_severity, 'medium')
            
            
            # First, get or create a property for this user
            property_id = await self._get_or_create_property(user_id)
            
            task_data = {
                'id': str(uuid.uuid4()),
                'property_id': property_id,
                'room_id': room_id,  # Can be None
                'user_id': user_id,
                'task_type': room_type,  # Changed from room_type to task_type
                'title': issue_title,
                'description': issue_description,
                'severity': priority,  # Changed from priority to severity
                'status': 'pending',
                'contractor_type': contractor_type,
                'photo_references': photo_ids or [],  # Changed from photos to photo_references
                'ai_detected_issues': [issue],  # Store the original issue for reference
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'created_from_photo': True
            }
            
            task_result = self.supabase.table('property_tasks')\
                .insert(task_data)\
                .execute()
            
            if task_result.data:
                created_task_id = task_result.data[0]['id']
                logger.info(f"Successfully created property task {created_task_id}: {issue_title}")
                return created_task_id
            else:
                logger.error(f"No data returned when creating task for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating property task: {e}")
            return None
    
    async def _handle_direct_task_creation(
        self,
        request: UnifiedChatRequest,
        session_id: str,
        property_context: Dict[str, Any] = None
    ) -> Tuple[IRISResponse, Dict[str, Any]]:
        """Handle direct task creation from text requests"""
        
        logger.info(f"Processing direct task creation request: '{request.message[:100]}...'")
        
        try:
            # Extract task details from message
            message_lower = request.message.lower()
            
            # Detect room type from message
            room_type = 'general'  # default
            room_keywords = {
                'kitchen': 'kitchen',
                'bathroom': 'bathroom', 
                'bedroom': 'bedroom',
                'living room': 'living_room',
                'dining': 'dining_room',
                'garage': 'garage',
                'basement': 'basement',
                'attic': 'attic',
                'laundry': 'laundry_room',
                'office': 'office'
            }
            
            for keyword, room_name in room_keywords.items():
                if keyword in message_lower:
                    room_type = room_name
                    break
            
            # Detect severity - database allows: low, medium, high, critical
            severity = 'medium'  # default
            if any(word in message_lower for word in ['urgent', 'emergency', 'immediate', 'asap']):
                severity = 'critical'  # Changed from 'urgent' to 'critical'
            elif any(word in message_lower for word in ['leak', 'broken', 'damage', 'not working']):
                severity = 'high'
            elif any(word in message_lower for word in ['minor', 'small', 'cosmetic']):
                severity = 'low'
            
            # Detect contractor type
            contractor_type = 'handyman'  # default
            if any(word in message_lower for word in ['plumb', 'leak', 'pipe', 'water', 'drain']):
                contractor_type = 'plumber'
            elif any(word in message_lower for word in ['electric', 'outlet', 'wire', 'circuit', 'light']):
                contractor_type = 'electrician'
            elif any(word in message_lower for word in ['paint', 'wall', 'ceiling', 'drywall']):
                contractor_type = 'painter'
            elif any(word in message_lower for word in ['roof', 'shingle', 'gutter']):
                contractor_type = 'roofer'
            elif any(word in message_lower for word in ['hvac', 'heat', 'air', 'furnace', 'ac']):
                contractor_type = 'hvac'
            
            # Generate task title from message
            if 'sink' in message_lower and 'leak' in message_lower:
                task_title = f"{room_type.replace('_', ' ').title()} Sink Leak Repair"
            elif 'leak' in message_lower:
                task_title = f"{room_type.replace('_', ' ').title()} Leak Repair"
            elif 'broken' in message_lower:
                task_title = f"{room_type.replace('_', ' ').title()} Repair - Broken Component"
            elif 'fix' in message_lower:
                task_title = f"{room_type.replace('_', ' ').title()} Maintenance Issue"
            else:
                task_title = f"{room_type.replace('_', ' ').title()} Maintenance Task"
            
            # Create the issue object with enhanced details for memory persistence
            issue = {
                'title': task_title,
                'description': request.message,  # Keep full original message
                'detailed_description': f"User reported: {request.message} | Room: {room_type} | Severity: {severity} | Contractor needed: {contractor_type}",
                'severity': severity,
                'contractor_type': contractor_type,
                'original_request': request.message,  # Store original for context
                'context_tags': [room_type, contractor_type, severity]  # For easy recall
            }
            
            # Get or create property and room
            property_id = await self._get_or_create_property(request.user_id)
            room_id = await self._create_room(request.user_id, room_type)
            
            logger.info(f"Creating task with details: {issue}")
            
            # Create the task
            created_task_id = await self._create_property_task(
                user_id=request.user_id,
                room_type=room_type,
                issue=issue,
                room_id=room_id,
                photo_ids=[]
            )
            
            if created_task_id:
                logger.info(f"SUCCESS: Created task {created_task_id} for direct request")
                
                response = IRISResponse(
                    success=True,
                    response=(
                        f"✅ **Task Created Successfully!**\n\n"
                        f"**{task_title}**\n"
                        f"- **Priority:** {severity.title()}\n"
                        f"- **Location:** {room_type.replace('_', ' ').title()}\n"
                        f"- **Contractor Type:** {contractor_type.title()}\n"
                        f"- **Task ID:** {created_task_id[:8]}...\n\n"
                        f"Your task has been saved to your property dashboard. "
                        f"Would you like me to help you find contractors for this work?"
                    ),
                    suggestions=[
                        "Find contractors for this task",
                        "Add more details to this task", 
                        "Create another task",
                        "View my property dashboard"
                    ],
                    action_results={
                        'task_created': True,
                        'task_id': created_task_id,
                        'room_type': room_type,
                        'severity': severity
                    }
                )
                
                # Save detailed context to conversation memory for future recall
                await self.conversation_manager.update_conversation_state(
                    session_id,
                    context_update={
                        'last_task_created': {
                            'task_id': created_task_id,
                            'title': task_title,
                            'description': request.message,
                            'room_type': room_type,
                            'severity': severity,
                            'contractor_type': contractor_type,
                            'created_at': datetime.utcnow().isoformat()
                        },
                        'room_details': {
                            room_type: {
                                'last_activity': request.message,
                                'last_task_created': task_title,
                                'priority_level': severity,
                                'description': f"User described: {request.message}"
                            }
                        }
                    }
                )
                
                # Also add to conversation history for persistent memory
                await self.conversation_manager.add_to_history(
                    session_id=session_id,
                    message=request.message,
                    response=f"Created task: {task_title} | Priority: {severity} | Location: {room_type}",
                    user_id=request.user_id
                )
                
                workflow_data = {
                    'state': self.STATES['TASKS_CREATED'],
                    'task_id': created_task_id,
                    'task_created': True
                }
                
                return response, workflow_data
                
            else:
                logger.error("FAILED: Task creation returned no ID")
                
                response = IRISResponse(
                    success=False,
                    response=(
                        f"I understand you want to create a task for: {request.message}\n\n"
                        f"However, I encountered an issue saving this to your property database. "
                        f"Let me try a different approach. Could you provide more details about the specific issue?"
                    ),
                    suggestions=[
                        "Try describing the issue differently",
                        "Upload a photo of the problem",
                        "Contact support"
                    ]
                )
                
                workflow_data = {'state': self.STATES['INITIAL']}
                return response, workflow_data
                
        except Exception as e:
            logger.error(f"Error in direct task creation: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            response = IRISResponse(
                success=False,
                response=(
                    f"I understand you want to create a task, but I encountered a technical issue. "
                    f"Please try again or contact support if the problem persists."
                ),
                suggestions=[
                    "Try again with different wording",
                    "Upload a photo instead",
                    "Contact support"
                ]
            )
            
            workflow_data = {'state': self.STATES['INITIAL']}
            return response, workflow_data
    
    async def _handle_general_conversation_with_workflow_detection(
        self,
        request: UnifiedChatRequest,
        session_id: str,
        property_context: Dict[str, Any] = None
    ) -> Tuple[IRISResponse, Dict[str, Any]]:
        """Enhanced general conversation with workflow trigger detection"""
        
        message_lower = request.message.lower()
        
        # Detect workflow triggers in general conversation
        if 'yes' in message_lower and ('kitchen' in message_lower or 'bathroom' in message_lower):
            # Room confirmation trigger
            logger.info(f"Detected room confirmation trigger in general conversation")
            return await self._handle_room_confirmation(request, session_id, property_context)
            
        elif ('yes' in message_lower and ('task' in message_lower or 'all' in message_lower or 'create' in message_lower)):
            # Task creation trigger
            logger.info(f"Detected task creation trigger in general conversation") 
            return await self._handle_task_confirmation(request, session_id, property_context)
            
        # Default to original general conversation behavior
        return await self._handle_general_conversation(request, session_id, property_context)

    async def _handle_general_conversation(
        self,
        request: UnifiedChatRequest,
        session_id: str,
        property_context: Dict[str, Any] = None
    ) -> Tuple[IRISResponse, Dict[str, Any]]:
        """Handle general property-related conversation with property intelligence"""
        
        # Get conversation history from database using conversation manager
        conversation_history = []
        try:
            conversation_state = await self.conversation_manager.get_conversation_state(session_id)
            if 'history' in conversation_state:
                # Convert stored history to format expected by LLM service
                for exchange in conversation_state['history'][-5:]:  # Last 5 exchanges
                    conversation_history.append({
                        'sender_type': 'user',
                        'content': exchange['message']
                    })
                    conversation_history.append({
                        'sender_type': 'assistant', 
                        'content': exchange['response']
                    })
            logger.info(f"Loaded {len(conversation_history)} messages from conversation history")
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}")
        
        # Generate intelligent response using LLM
        context_response = self.llm_service.generate_response(
            user_message=request.message,
            conversation_history=conversation_history,
            property_context=property_context,
            image_analysis=None
        )
        
        # Generate property-aware suggestions
        if property_context:
            stats = property_context.get('property_stats', {})
            total_rooms = stats.get('total_rooms', 0)
            total_photos = stats.get('total_photos', 0)
            total_tasks = stats.get('total_tasks', 0)
            total_bid_cards = stats.get('total_bid_cards', 0)
            
            # Build contextual suggestions
            if total_rooms == 0:
                suggestions = [
                    "Upload property photos",
                    "Tell me about my property",
                    "How does property documentation work?",
                    "What rooms can I document?"
                ]
            else:
                pending_tasks = sum(1 for task in property_context.get('property_tasks', []) if task.get('status') == 'pending')
                
                # Keep existing context_response but it will be overridden by LLM
                fallback_response = (
                    f"Welcome back! Your property has {total_rooms} room{'s' if total_rooms > 1 else ''} documented "
                    f"with {total_photos} photo{'s' if total_photos != 1 else ''} and {total_tasks} task{'s' if total_tasks != 1 else ''} tracked."
                )
                
                if pending_tasks > 0:
                    context_response += f" You have {pending_tasks} pending task{'s' if pending_tasks > 1 else ''} that might need attention."
                
                if total_bid_cards > 0:
                    context_response += f" You also have {total_bid_cards} bid card{'s' if total_bid_cards != 1 else ''} for contractor projects."
                
                suggestions = [
                    "Show me my property summary",
                    f"View my {pending_tasks} pending tasks" if pending_tasks > 0 else "Upload more photos",
                    "Check my bid cards" if total_bid_cards > 0 else "Create a new task",
                    "Document another room"
                ]
        else:
            # Fallback suggestions when no property context available
            suggestions = [
                "Upload property photos",
                "View my property rooms",
                "Check maintenance tasks",
                "Get contractor quotes"
            ]
            
            # If LLM didn't generate a response, use fallback
            if not context_response:
                context_response = (
                    "I'm here to help you document your property and track maintenance needs. "
                    "You can upload photos of any room, and I'll help identify potential issues "
                    "and create task cards for repairs or improvements."
                )
        
        # Save conversation exchange to history
        try:
            await self.conversation_manager.add_to_history(
                session_id=session_id,
                message=request.message,
                response=context_response
            )
            logger.info("Saved conversation exchange to history")
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}")
        
        response = IRISResponse(
            success=True,
            response=context_response,
            suggestions=suggestions,
            interface="homeowner",
            session_id=session_id,
            user_id=request.user_id
        )
        
        workflow_data = {
            'state': self.STATES['INITIAL']
        }
        
        return response, workflow_data
    
    async def _handle_room_response(
        self,
        request: UnifiedChatRequest,
        session_id: str,
        property_context: Dict[str, Any] = None
    ) -> Tuple[IRISResponse, Dict[str, Any]]:
        """Handle user's room type response"""
        
        # Parse room from response
        room_type = self.room_detector.parse_user_room_selection(request.message)
        
        if not room_type:
            # Couldn't understand room
            response = IRISResponse(
                success=True,
                response=(
                    "I'm not sure which room you mean. Could you clarify? "
                    "For example: kitchen, bathroom, bedroom, living room, backyard, etc."
                ),
                suggestions=[
                    "It's the kitchen",
                    "It's a bathroom",
                    "It's a bedroom",
                    "Let me type the room name"
                ],
                interface="homeowner",
                session_id=session_id,
                user_id=request.user_id
            )
            
            workflow_data = {
                'state': self.STATES['AWAITING_ROOM']
            }
        else:
            # Got room type - move to confirmation
            # Note: Can't use _replace on request, will handle room_type differently
            # Store room_type in conversation state for next call
            await self.conversation_manager.update_conversation_state(
                session_id=session_id,
                state='confirming_room',
                context_update={'detected_room': room_type}
            )
            return await self._handle_room_confirmation(
                request,
                session_id,
                property_context
            )
        
        return response, workflow_data
    
    async def _handle_task_discussion(
        self,
        request: UnifiedChatRequest,
        session_id: str,
        property_context: Dict[str, Any] = None
    ) -> Tuple[IRISResponse, Dict[str, Any]]:
        """Handle discussion about creating tasks"""
        
        return await self._handle_task_confirmation(request, session_id)