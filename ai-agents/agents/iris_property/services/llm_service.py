"""
IRIS LLM Service - OpenAI GPT Integration
Provides intelligent conversational responses for IRIS
"""

import os
import logging
from typing import Dict, Any, List, Optional
import openai
from datetime import datetime

logger = logging.getLogger(__name__)

class IRISLLMService:
    """Handles all LLM interactions for IRIS using OpenAI GPT"""
    
    def __init__(self):
        """Initialize with OpenAI API"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY not found - IRIS will not have AI capabilities")
            self.client = None
        else:
            openai.api_key = api_key
            self.client = openai
            logger.info("IRIS LLM Service initialized with OpenAI")
    
    def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        property_context: Dict[str, Any] = None,
        image_analysis: Dict[str, Any] = None
    ) -> str:
        """Generate intelligent response using GPT-4"""
        
        if not self.client:
            return "I'm currently offline. Please check back later."
        
        try:
            # Initialize OpenAI client with proper format
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Build system prompt with IRIS personality and memory awareness
            system_prompt = """You are IRIS, a helpful property maintenance assistant with persistent memory.
            You help homeowners document property issues, track maintenance needs, and connect with contractors.
            
            CRITICAL INSTRUCTIONS:
            1. When asked to LIST or VIEW existing tasks, use ONLY the specific tasks provided in the context
            2. DO NOT make up, invent, or hallucinate any tasks when listing - use only what is explicitly provided
            3. Quote the EXACT descriptions from the existing tasks when referring to them
            4. If context shows "Black mold in shower corners", say exactly that - don't change it to generic descriptions
            5. ALWAYS be helpful with creating NEW tasks when the user asks for it (e.g., "create a task", "add a repair", "track an issue")
            6. When the user wants to CREATE a task, assist them - DO NOT refuse task creation requests
            7. Always reference the actual task descriptions, severity levels, and room locations from the provided data
            
            Be friendly and professional. Help users both view existing tasks AND create new ones as needed."""
            
            # Build context message
            context_parts = []
            
            if property_context:
                stats = property_context.get('property_stats', {})
                if stats:
                    context_parts.append(f"Property has {stats.get('total_rooms', 0)} rooms documented, "
                                       f"{stats.get('total_photos', 0)} photos, "
                                       f"{stats.get('total_tasks', 0)} tasks")
                
                # Add detailed room information for better context recall
                rooms = property_context.get('rooms_with_descriptions', [])
                if rooms:
                    room_details = []
                    for room in rooms[:5]:  # Limit to top 5 rooms for context
                        room_type = room.get('room_type', 'unknown')
                        description = room.get('description', '')
                        if description:
                            room_details.append(f"{room_type}: {description}")
                    if room_details:
                        context_parts.append(f"Room details: {'; '.join(room_details)}")
                
                # Add ALL task details - be extremely explicit
                tasks = property_context.get('property_tasks', [])
                if tasks:
                    # Filter out the duplicate test question tasks and only show real maintenance tasks
                    real_tasks = [task for task in tasks if task.get('description', '') and 
                                 'What maintenance tasks do I currently have pending' not in task.get('description', '')]
                    
                    if real_tasks:
                        context_parts.append(f"EXISTING PROPERTY MAINTENANCE TASKS (Use these exact descriptions):")
                        task_details = []
                        for i, task in enumerate(real_tasks, 1):
                            description = task.get('description', '').strip()
                            task_type = task.get('task_type', '').strip()  
                            severity = task.get('severity', '').strip()
                            room_name = task.get('room_name', '').strip()
                            
                            if description and description != 'None':
                                # Add room location to the description to ensure it's mentioned
                                task_detail = f"Task {i}: '{description}'"
                                if room_name and room_name != 'None' and 'Room' in room_name:
                                    room_simple = room_name.replace(' Room', '')
                                    task_detail += f" (in {room_simple})"
                                if task_type and task_type != 'None':
                                    task_detail += f" - {task_type} work"  # Add "electrical work" etc
                                if severity and severity != 'None':
                                    task_detail += f" - {severity} priority"
                                task_details.append(task_detail)
                        
                        if task_details:
                            context_parts.append("; ".join(task_details))
            
            if image_analysis:
                if image_analysis.get('room_type'):
                    context_parts.append(f"User uploaded photo of: {image_analysis['room_type']}")
                if image_analysis.get('detected_issues'):
                    issues = ', '.join(image_analysis['detected_issues'][:3])
                    context_parts.append(f"Detected issues: {issues}")
            
            # Build messages for API
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            if context_parts:
                messages.append({
                    "role": "system", 
                    "content": f"Context: {'. '.join(context_parts)}"
                })
            
            # Add conversation history (last 5 messages)
            if conversation_history:
                logger.info(f"Adding {len(conversation_history)} messages to OpenAI context")
                for i, msg in enumerate(conversation_history[-10:]):  # Increased to 10 messages
                    role = "user" if msg.get('sender_type') == 'user' else "assistant"
                    content = msg.get('content', '')
                    messages.append({
                        "role": role,
                        "content": content
                    })
                    logger.debug(f"Added message {i}: {role} - {content[:50]}...")
            
            # Add current message
            messages.append({"role": "user", "content": user_message})
            
            # Call OpenAI with proper client
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Fast, cost-effective model
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return "I'm having trouble processing that request. Could you please try again?"
    
    def analyze_image_with_context(
        self,
        image_base64: str,
        user_message: str,
        room_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze property photo using GPT-4 Vision"""
        
        if not self.client:
            return {
                "success": False,
                "error": "Vision analysis not available"
            }
        
        try:
            # Initialize OpenAI client with proper format
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            prompt = f"""Analyze this property photo and identify:
            1. What room or area is shown
            2. Any maintenance issues or damage
            3. Estimated repair priority (low/medium/high)
            4. Suggested contractor types needed
            
            User context: {user_message}
            {f'Expected room: {room_type}' if room_type else ''}
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",  # Vision-capable model (gpt-4o-mini doesn't support vision)
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse response into structured data
            return {
                "success": True,
                "analysis": analysis_text,
                "room_type": room_type or "unknown",
                "detected_issues": self._extract_issues(analysis_text),
                "priority": self._extract_priority(analysis_text),
                "contractor_suggestions": self._extract_contractors(analysis_text)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_issues(self, text: str) -> List[str]:
        """Extract maintenance issues from analysis text"""
        issues = []
        
        # Simple extraction - look for common issue keywords
        issue_keywords = ['damage', 'repair', 'broken', 'leak', 'crack', 'stain', 
                         'mold', 'wear', 'outdated', 'needs', 'should', 'recommend']
        
        lines = text.lower().split('\n')
        for line in lines:
            if any(keyword in line for keyword in issue_keywords):
                # Clean up and add to issues
                issue = line.strip('- •*').strip()
                if len(issue) > 10 and len(issue) < 200:  # Reasonable length
                    issues.append(issue)
        
        return issues[:5]  # Return top 5 issues
    
    def _extract_priority(self, text: str) -> str:
        """Extract priority level from analysis"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['urgent', 'immediate', 'critical', 'high priority']):
            return 'high'
        elif any(word in text_lower for word in ['moderate', 'medium', 'should address']):
            return 'medium'
        else:
            return 'low'
    
    def _extract_contractors(self, text: str) -> List[str]:
        """Extract contractor types from analysis"""
        contractors = []
        
        contractor_types = [
            'plumber', 'electrician', 'roofer', 'painter', 'contractor',
            'hvac', 'carpenter', 'handyman', 'flooring', 'landscaper'
        ]
        
        text_lower = text.lower()
        for contractor in contractor_types:
            if contractor in text_lower:
                contractors.append(contractor.title())
        
        return contractors[:3]  # Return top 3 contractor types