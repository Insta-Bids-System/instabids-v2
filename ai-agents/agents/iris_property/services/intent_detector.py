"""
IRIS Intent Detection Service
Uses LLM to intelligently understand user intentions and room/area references
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class UserIntent:
    """Structure for detected user intent"""
    intent_type: str  # 'create_room', 'create_task', 'view_tasks', 'general_question', etc.
    room_area: Optional[str] = None  # Any room/area name the user mentioned
    confidence: float = 0.0
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}

class IRISIntentDetector:
    """Intelligent intent detection using LLM"""
    
    def __init__(self):
        """Initialize with OpenAI API"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found - Intent detection will not work")
            self.client = None
        else:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            logger.info("IRIS Intent Detector initialized")
    
    async def detect_intent(
        self,
        user_message: str,
        existing_rooms: List[Dict[str, Any]] = None,
        conversation_context: List[Dict[str, str]] = None
    ) -> UserIntent:
        """
        Intelligently detect user intent and extract room/area information
        """
        
        if not self.client:
            return UserIntent(intent_type='general_question', confidence=0.1)
        
        try:
            # Build context about existing rooms
            existing_rooms_context = ""
            if existing_rooms:
                room_names = [room.get('name', room.get('room_type', 'unknown')) for room in existing_rooms]
                existing_rooms_context = f"User already has these rooms documented: {', '.join(room_names)}"
            else:
                existing_rooms_context = "User has no documented rooms yet"
            
            # Build conversation context
            recent_context = ""
            if conversation_context:
                recent_messages = conversation_context[-3:]  # Last 3 exchanges
                context_parts = []
                for msg in recent_messages:
                    role = msg.get('sender_type', 'unknown')
                    content = msg.get('content', '')[:100]  # Truncate long messages
                    context_parts.append(f"{role}: {content}")
                recent_context = f"Recent conversation: {'; '.join(context_parts)}"
            
            # Create the intelligent system prompt
            system_prompt = f"""You are an intelligent intent detector for a property maintenance assistant.
            
Analyze the user's message and determine their intent. Return ONLY a valid JSON object with this structure:
{{
    "intent_type": "one of: create_room, create_task, view_tasks, room_confirmation, upload_photo, general_question",
    "room_area": "exact room/area name mentioned (any name the user says - roof, attic, master bedroom, pool deck, etc.) or null",
    "confidence": 0.0-1.0,
    "details": {{
        "task_description": "if creating task, what needs to be done",
        "urgency": "low/medium/high/critical if mentioned", 
        "confirmation": "yes/no if user is confirming something"
    }}
}}

CONTEXT:
{existing_rooms_context}
{recent_context}

INTENT DETECTION RULES:
1. "create_room" - User wants to document a new room/area (e.g., "make a roof room", "add the garage", "document my pool area")
2. "create_task" - User wants to track a maintenance issue (e.g., "fix the leak", "repair the roof", "document this problem")  
3. "room_confirmation" - User is confirming a room type (e.g., "yes it's the kitchen", "that's my bathroom")
4. "view_tasks" - User wants to see existing tasks (e.g., "show my tasks", "what repairs do I have")
5. "upload_photo" - User mentions uploading/sharing photos
6. "general_question" - Everything else

ROOM/AREA DETECTION:
- Extract ANY room or area name the user mentions (kitchen, roof, master bedroom, pool deck, front porch, etc.)
- Don't limit to predefined lists - use any area name the user says
- Be flexible with variations (e.g., "living room" = "living room", "main bedroom" = "master bedroom")"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Message to analyze: {user_message}"}
            ]
            
            # Use lower temperature for more consistent JSON output
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=200,
                temperature=0.2,  # Lower temperature for more consistent responses
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            
            intent = UserIntent(
                intent_type=result.get('intent_type', 'general_question'),
                room_area=result.get('room_area'),
                confidence=float(result.get('confidence', 0.5)),
                details=result.get('details', {})
            )
            
            logger.info(f"Detected intent: {intent.intent_type}, room: {intent.room_area}, confidence: {intent.confidence}")
            return intent
            
        except Exception as e:
            logger.error(f"Error in intent detection: {e}")
            # Fallback to simple detection
            return self._simple_fallback_detection(user_message)
    
    def _simple_fallback_detection(self, user_message: str) -> UserIntent:
        """Simple fallback when LLM is unavailable"""
        
        message_lower = user_message.lower()
        
        # Simple keyword-based fallback
        if any(word in message_lower for word in ['create', 'make', 'add', 'new']) and 'room' in message_lower:
            return UserIntent(
                intent_type='create_room',
                confidence=0.6,
                details={'fallback': True}
            )
        elif any(word in message_lower for word in ['task', 'fix', 'repair', 'leak', 'broken']):
            return UserIntent(
                intent_type='create_task', 
                confidence=0.6,
                details={'fallback': True}
            )
        else:
            return UserIntent(
                intent_type='general_question',
                confidence=0.3,
                details={'fallback': True}
            )