"""
IRIS Consultation Workflow  
Handles design consultation conversations and guidance
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..models.requests import UnifiedChatRequest
from ..models.responses import IRISResponse
from ..services.memory_manager import MemoryManager
from ..services.context_builder import ContextBuilder

logger = logging.getLogger(__name__)

class ConsultationWorkflow:
    """Handles property maintenance consultation and issue assessment"""
    
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.context_builder = ContextBuilder()
        
        # Property issue severity levels
        self.severity_levels = {
            'urgent': 'Immediate attention needed (safety/structural)',
            'high': 'Should be addressed soon (1-2 weeks)',
            'medium': 'Plan for within month',
            'low': 'Can be scheduled as convenient'
        }
        
        # Property consultation phases
        self.consultation_phases = {
            'assessment': 'Identifying property issues and maintenance needs',
            'prioritization': 'Ranking issues by urgency and importance',
            'estimation': 'Understanding scope and potential costs',
            'planning': 'Creating actionable repair plans',
            'contractor_prep': 'Ready for contractor bidding'
        }
    
    def process_consultation(
        self,
        request: UnifiedChatRequest,
        session_id: str,
        conversation_id: str,
        context_summary: str
    ) -> Tuple[IRISResponse, Dict[str, Any]]:
        """
        Process property maintenance consultation conversation
        
        Returns:
            Tuple of (IRISResponse, workflow_data)
        """
        
        logger.info(f"Processing consultation for user {request.user_id}")
        
        # Step 1: Analyze conversation intent
        conversation_intent = self._analyze_conversation_intent(request)
        
        # Step 2: Determine consultation phase
        current_phase = self._determine_consultation_phase(request, context_summary)
        
        # Step 3: Generate contextual response
        response = self._generate_consultation_response(
            request=request,
            conversation_intent=conversation_intent,
            current_phase=current_phase,
            context_summary=context_summary
        )
        
        # Step 4: Save consultation memory
        self._save_consultation_memory(
            conversation_id=conversation_id,
            session_id=session_id,
            intent=conversation_intent,
            phase=current_phase,
            user_input=request.message
        )
        
        # Step 5: Update board status if applicable
        if request.board_id:
            self._update_board_progress(request.board_id, conversation_intent)
        
        # Create workflow data
        workflow_data = {
            'conversation_intent': conversation_intent,
            'consultation_phase': current_phase,
            'board_status_updated': bool(request.board_id),
            'next_suggested_phase': self._get_next_phase(current_phase)
        }
        
        return response, workflow_data
    
    def _analyze_conversation_intent(self, request: UnifiedChatRequest) -> Dict[str, Any]:
        """Analyze user message to understand intent"""
        
        message_lower = request.message.lower()
        
        intent = {
            'type': 'general',
            'topics': [],
            'actions': [],
            'preferences': {},
            'questions': [],
            'urgency': 'normal'
        }
        
        # Intent type detection
        if any(word in message_lower for word in ['budget', 'cost', 'price', 'expensive', 'afford']):
            intent['type'] = 'budget_discussion'
            intent['topics'].append('budget')
        
        elif any(word in message_lower for word in ['style', 'look', 'feel', 'aesthetic', 'vibe']):
            intent['type'] = 'style_exploration'
            intent['topics'].append('style')
        
        elif any(word in message_lower for word in ['timeline', 'when', 'schedule', 'time', 'urgent']):
            intent['type'] = 'timeline_discussion'
            intent['topics'].append('timeline')
        
        elif any(word in message_lower for word in ['help', 'organize', 'plan', 'next', 'step']):
            intent['type'] = 'guidance_request'
            intent['actions'].append('provide_guidance')
        
        elif any(word in message_lower for word in ['contractor', 'professional', 'hire', 'find']):
            intent['type'] = 'contractor_readiness'
            intent['actions'].append('prepare_for_contractors')
        
        # Repair detection - HIGH PRIORITY
        repair_keywords = ['repair', 'fix', 'broken', 'damage', 'leak', 'leaking', 
                          'crack', 'cracked', 'hole', 'water damage', 'falling', 
                          'not working', 'replace', 'replacement', 'emergency']
        
        if any(word in message_lower for word in repair_keywords):
            intent['type'] = 'repair_needed'
            intent['topics'].append('repairs')
            intent['actions'].append('create_repair_bid_card')
            intent['urgency'] = 'high'
            
            # Extract specific repair details
            repairs_detected = []
            if 'water' in message_lower and ('damage' in message_lower or 'leak' in message_lower):
                repairs_detected.append({'type': 'water_damage', 'urgency': 'urgent'})
            if 'cabinet' in message_lower and any(w in message_lower for w in ['broken', 'falling', 'damage']):
                repairs_detected.append({'type': 'cabinet_repair', 'urgency': 'moderate'})
            if 'dishwasher' in message_lower and 'leak' in message_lower:
                repairs_detected.append({'type': 'appliance_leak', 'urgency': 'urgent'})
            
            intent['repairs_detected'] = repairs_detected
        
        # Topic detection
        topics = {
            'colors': ['color', 'colours', 'palette', 'scheme', 'hue'],
            'materials': ['material', 'wood', 'stone', 'metal', 'fabric', 'tile'],
            'lighting': ['light', 'lighting', 'bright', 'dark', 'lamp', 'fixture'],
            'furniture': ['furniture', 'chair', 'table', 'sofa', 'bed'],
            'layout': ['layout', 'space', 'room', 'arrangement', 'flow'],
            'storage': ['storage', 'organize', 'closet', 'cabinet', 'shelf']
        }
        
        for topic, keywords in topics.items():
            if any(keyword in message_lower for keyword in keywords):
                intent['topics'].append(topic)
        
        # Preference indicators
        if any(word in message_lower for word in ['love', 'like', 'prefer', 'want', 'need']):
            intent['preferences']['positive'] = True
        
        if any(word in message_lower for word in ['hate', 'dislike', 'don\'t want', 'avoid']):
            intent['preferences']['negative'] = True
        
        # Question indicators
        question_starters = ['how', 'what', 'where', 'when', 'why', 'which', 'who', 'can you', 'should i']
        if any(message_lower.startswith(q) or f' {q}' in message_lower for q in question_starters):
            intent['questions'].append('direct_question')
        
        if '?' in request.message:
            intent['questions'].append('has_question_mark')
        
        # Urgency detection
        if any(word in message_lower for word in ['urgent', 'asap', 'quickly', 'rush', 'emergency']):
            intent['urgency'] = 'high'
        elif any(word in message_lower for word in ['someday', 'eventually', 'future', 'thinking']):
            intent['urgency'] = 'low'
        
        return intent
    
    def _determine_consultation_phase(self, request: UnifiedChatRequest, context_summary: str) -> str:
        """Determine current phase of consultation"""
        
        message_lower = request.message.lower()
        
        # Phase indicators in message
        if any(word in message_lower for word in ['getting started', 'begin', 'first time', 'new']):
            return 'discovery'
        
        elif any(word in message_lower for word in ['options', 'styles', 'ideas', 'different', 'explore']):
            return 'exploration'
        
        elif any(word in message_lower for word in ['narrow down', 'choose', 'decide', 'final', 'specific']):
            return 'refinement'
        
        elif any(word in message_lower for word in ['plan', 'next steps', 'implementation', 'timeline']):
            return 'planning'
        
        elif any(word in message_lower for word in ['contractor', 'professional', 'hire', 'ready']):
            return 'handoff'
        
        # Context-based phase detection
        if 'no previous context' in context_summary.lower():
            return 'discovery'
        
        elif 'inspiration boards' in context_summary.lower():
            if 'design preferences' in context_summary.lower():
                return 'refinement'
            else:
                return 'exploration'
        
        elif 'budget' in context_summary.lower() and 'timeline' in context_summary.lower():
            return 'planning'
        
        # Default based on board status
        if request.board_status:
            phase_mapping = {
                'collecting': 'discovery',
                'organizing': 'exploration', 
                'refining': 'refinement',
                'ready': 'planning'
            }
            return phase_mapping.get(request.board_status, 'exploration')
        
        return 'exploration'  # Default phase
    
    def _generate_consultation_response(
        self,
        request: UnifiedChatRequest,
        conversation_intent: Dict[str, Any],
        current_phase: str,
        context_summary: str
    ) -> IRISResponse:
        """Generate appropriate consultation response"""
        
        # Check for repair detection first - highest priority
        if conversation_intent.get('type') == 'repair_needed':
            return self._generate_repair_response(request, conversation_intent)
        
        # Phase-specific response generation with context awareness
        if current_phase == 'discovery':
            response_text = self._generate_discovery_response(request, conversation_intent, context_summary)
            suggestions = self._generate_discovery_suggestions(request)
            
        elif current_phase == 'exploration':
            response_text = self._generate_exploration_response(request, conversation_intent)
            suggestions = self._generate_exploration_suggestions(request)
            
        elif current_phase == 'refinement':
            response_text = self._generate_refinement_response(request, conversation_intent)
            suggestions = self._generate_refinement_suggestions(request)
            
        elif current_phase == 'planning':
            response_text = self._generate_planning_response(request, conversation_intent)
            suggestions = self._generate_planning_suggestions(request)
            
        elif current_phase == 'handoff':
            response_text = self._generate_handoff_response(request, conversation_intent)
            suggestions = self._generate_handoff_suggestions(request)
            
        else:
            response_text = self._generate_fallback_response(request, conversation_intent)
            suggestions = ["Tell me about your project", "What style do you prefer?", "What's your budget range?", "Upload some inspiration images"]
        
        return IRISResponse(
            success=True,
            response=response_text,
            suggestions=suggestions,
            interface="homeowner",
            session_id=request.session_id,
            user_id=request.user_id,
            action_results={
                'consultation_phase': current_phase,
                'intent_type': conversation_intent['type']
            }
        )
    
    def _generate_discovery_response(self, request: UnifiedChatRequest, intent: Dict[str, Any], context_summary: str = "") -> str:
        """Generate discovery phase response with context awareness"""
        
        room_type = request.board_room_type or "space"
        
        # Check if we have previous interactions to acknowledge
        if 'Previous interactions:' in context_summary:
            # User has history - acknowledge it
            if 'likes navy blue' in context_summary.lower():
                return (
                    f"Welcome back! I remember you mentioned you love navy blue in your kitchen designs. "
                    f"Are you continuing to work on that project, or exploring something new today? "
                    f"I'm here to help you create your perfect {room_type}!"
                )
            elif 'kitchen design interest' in context_summary:
                return (
                    f"Good to see you again! I see you've been exploring kitchen design ideas. "
                    f"How can I help you continue developing your vision today?"
                )
            elif 'bathroom renovation interest' in context_summary:
                return (
                    f"Welcome back! I remember you were interested in bathroom renovations. "
                    f"Are you ready to dive deeper into planning, or would you like to explore new ideas?"
                )
            else:
                # Generic welcome back
                return (
                    f"Welcome back! I see we've talked before about your design interests. "
                    f"How can I help you with your {room_type} project today?"
                )
        
        # New user or no relevant history
        if intent['type'] == 'guidance_request':
            return (
                f"I'd love to help you get started with your {room_type} project! "
                f"The best way to begin is by understanding your vision and gathering inspiration. "
                f"Here's how we can work together:\n\n"
                f"1. **Share Your Vision**: Tell me about your goals for this space\n"
                f"2. **Upload Inspiration**: Add images of styles you love\n"
                f"3. **Define Preferences**: We'll identify your style preferences\n"
                f"4. **Set Parameters**: Discuss budget and timeline when you're ready\n\n"
                f"What aspect of your {room_type} project excites you most?"
            )
        
        elif intent['type'] == 'style_exploration':
            return (
                f"Wonderful! Let's explore your style preferences for your {room_type}. "
                f"Understanding your aesthetic is the foundation of a successful project.\n\n"
                f"When you think about your ideal {room_type}, what comes to mind? "
                f"For example:\n"
                f"• Do you prefer clean, modern lines or cozy, traditional elements?\n"
                f"• Are you drawn to neutral colors or bold statements?\n"
                f"• Do you like natural materials like wood and stone, or sleek modern finishes?\n\n"
                f"Feel free to upload any inspiration images you've found!"
            )
        
        else:
            return (
                f"I'm excited to help you create your dream {room_type}! "
                f"Every great design project starts with understanding your unique vision and preferences. "
                f"Let's begin by exploring what inspires you.\n\n"
                f"What's driving your interest in updating this space? Are you looking for:\n"
                f"• A complete style transformation?\n"
                f"• Better functionality and organization?\n" 
                f"• Addressing specific problems or challenges?\n"
                f"• Just refreshing the look and feel?\n\n"
                f"Share any inspiration images or tell me about your goals!"
            )
    
    def _generate_exploration_response(self, request: UnifiedChatRequest, intent: Dict[str, Any]) -> str:
        """Generate exploration phase response"""
        
        if intent['type'] == 'style_exploration':
            return (
                "Great! I can see you're developing your design direction. "
                "This is the perfect time to explore different options and see what resonates with you.\n\n"
                "Based on the styles you're considering, I can help you:\n"
                "• Compare different design approaches\n"
                "• Identify common elements across your inspiration\n"
                "• Explore complementary styles and ideas\n"
                "• Understand the practical implications of different choices\n\n"
                "What specific aspects would you like to explore further?"
            )
        
        elif intent['type'] == 'budget_discussion':
            return (
                "Budget planning is so important for a successful project! Understanding your investment range "
                "helps us make smart design choices from the start.\n\n"
                "Rather than focusing on exact numbers right now, let's think about your priorities:\n"
                "• What elements are absolute must-haves?\n"
                "• Where are you willing to invest for quality?\n"
                "• What areas could use more budget-friendly solutions?\n\n"
                "This approach helps create a design that maximizes your investment and aligns with your values."
            )
        
        else:
            return (
                "You're building a wonderful collection of ideas! This exploration phase is where "
                "the magic happens - seeing patterns emerge and your personal style taking shape.\n\n"
                "I notice some interesting themes in what you're sharing. Let me help you:\n"
                "• Identify the strongest patterns in your preferences\n"
                "• Explore variations on themes you love\n"
                "• Consider how different elements work together\n"
                "• Think about practical considerations\n\n"
                "What aspect of your design vision is becoming clearest to you?"
            )
    
    def _generate_refinement_response(self, request: UnifiedChatRequest, intent: Dict[str, Any]) -> str:
        """Generate refinement phase response"""
        
        return (
            "Perfect! You're moving into the refinement stage where we focus your vision and make "
            "strategic decisions. This is where your design really comes together.\n\n"
            "Let's prioritize and refine:\n"
            "• **Core Elements**: What are the 3-5 must-have features?\n"
            "• **Style Consistency**: How do we create cohesion across choices?\n"
            "• **Practical Needs**: What functional requirements are essential?\n"
            "• **Budget Alignment**: How do we maximize impact within your range?\n\n"
            "What feels like the most important decision to nail down first?"
        )
    
    def _generate_planning_response(self, request: UnifiedChatRequest, intent: Dict[str, Any]) -> str:
        """Generate planning phase response"""
        
        return (
            "Excellent! You've developed a clear vision, and now we can create an actionable plan. "
            "This is where your design becomes a real project.\n\n"
            "Let's organize your project:\n"
            "• **Phase Planning**: What makes sense to do first, second, third?\n"
            "• **Professional Needs**: Which aspects need contractors vs DIY?\n"
            "• **Timeline Realities**: How does this fit your schedule?\n"
            "• **Preparation Steps**: What can you do before professionals arrive?\n\n"
            "Are you ready to start connecting with contractors, or do you want to refine any aspects first?"
        )
    
    def _generate_handoff_response(self, request: UnifiedChatRequest, intent: Dict[str, Any]) -> str:
        """Generate handoff phase response"""
        
        return (
            "Wonderful! Your design vision is well-developed and ready for professional implementation. "
            "Let me help you prepare for working with contractors.\n\n"
            "**Your Project Summary**:\n"
            "• Clear style direction and design preferences\n"
            "• Defined scope and priorities\n"
            "• Budget framework established\n"
            "• Timeline considerations identified\n\n"
            "I can help you create a comprehensive project brief that contractors will love working with. "
            "This ensures you get accurate bids and proposals that match your vision.\n\n"
            "Would you like me to help you connect with our CIA agent to find qualified contractors?"
        )
    
    def _generate_fallback_response(self, request: UnifiedChatRequest, intent: Dict[str, Any]) -> str:
        """Generate fallback response for unclear intents"""
        
        return (
            "I'm here to help you create your ideal space! As your design assistant, I can help you "
            "organize your ideas, explore different styles, and develop a clear vision for your project.\n\n"
            "Here's how I can assist:\n"
            "• **Design Exploration**: Help you discover and refine your style preferences\n"
            "• **Idea Organization**: Turn scattered inspiration into a cohesive vision\n"
            "• **Project Planning**: Guide you from concept to contractor-ready plans\n"
            "• **Expert Advice**: Share design knowledge and practical insights\n\n"
            "What would be most helpful for you right now?"
        )
    
    def _generate_discovery_suggestions(self, request: UnifiedChatRequest) -> List[str]:
        """Generate suggestions for discovery phase"""
        return [
            "Tell me about your project goals",
            "What style elements do you love?",
            "Upload inspiration images",
            "What problems are you trying to solve?"
        ]
    
    def _generate_exploration_suggestions(self, request: UnifiedChatRequest) -> List[str]:
        """Generate suggestions for exploration phase"""
        return [
            "Show me different style options",
            "Help me organize my inspiration",
            "What's my color palette?",
            "Compare design approaches"
        ]
    
    def _generate_refinement_suggestions(self, request: UnifiedChatRequest) -> List[str]:
        """Generate suggestions for refinement phase"""
        return [
            "Help me prioritize my must-haves",
            "Create a cohesive design plan",
            "What's my budget range?",
            "Refine my style choices"
        ]
    
    def _generate_planning_suggestions(self, request: UnifiedChatRequest) -> List[str]:
        """Generate suggestions for planning phase"""
        return [
            "Create an implementation timeline",
            "What needs professional help?",
            "Prepare contractor requirements",
            "Connect with CIA agent"
        ]
    
    def _generate_repair_response(self, request: UnifiedChatRequest, intent: Dict[str, Any]) -> IRISResponse:
        """Generate response for repair detection"""
        
        repairs = intent.get('repairs_detected', [])
        
        # Build repair acknowledgment
        if repairs:
            repair_types = [r['type'].replace('_', ' ') for r in repairs]
            urgent_repairs = [r for r in repairs if r['urgency'] == 'urgent']
            
            if urgent_repairs:
                response_text = (
                    f"I understand you have urgent repair needs that require immediate attention. "
                    f"I've identified the following issues: {', '.join(repair_types)}. "
                    f"These repairs should be addressed by qualified professionals as soon as possible. "
                    f"Let me help you connect with contractors who can handle these urgent repairs. "
                    f"In the meantime, would you also like to discuss your design vision for after the repairs are complete?"
                )
            else:
                response_text = (
                    f"I see you have some repairs that need attention: {', '.join(repair_types)}. "
                    f"It's important to address these issues before moving forward with design plans. "
                    f"I can help you find qualified contractors to handle these repairs. "
                    f"Once the repairs are complete, we can focus on creating your dream space. "
                    f"Would you like to tell me more about the repairs needed?"
                )
        else:
            response_text = (
                "I understand you have repair needs that should be addressed. "
                "Getting these fixed first will give you a solid foundation for your design project. "
                "Can you tell me more about what specific repairs are needed? "
                "This will help me connect you with the right professionals."
            )
        
        # Create action to notify CIA agent about repairs
        action_results = {
            'consultation_phase': 'repair_detection',
            'intent_type': 'repair_needed',
            'repairs_detected': repairs,
            'action_taken': 'repair_bid_card_recommended'
        }
        
        suggestions = [
            "Tell me more about the damage",
            "What other repairs are needed?",
            "Connect me with repair contractors",
            "Let's also plan the design"
        ]
        
        return IRISResponse(
            success=True,
            response=response_text,
            suggestions=suggestions,
            interface="homeowner",
            session_id=request.session_id,
            user_id=request.user_id,
            action_results=action_results
        )
    
    def _generate_handoff_suggestions(self, request: UnifiedChatRequest) -> List[str]:
        """Generate suggestions for handoff phase"""
        return [
            "Connect with CIA agent",
            "Create project brief",
            "Find qualified contractors",
            "Review final design plan"
        ]
    
    def _save_consultation_memory(
        self,
        conversation_id: str,
        session_id: str,
        intent: Dict[str, Any],
        phase: str,
        user_input: str
    ) -> None:
        """Save consultation context to memory"""
        
        from ..models.database import MemoryType
        
        memory_value = {
            'session_id': session_id,
            'consultation_phase': phase,
            'user_intent': intent,
            'user_input': user_input,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.memory_manager.save_context_memory(
            conversation_id=conversation_id,
            memory_type=MemoryType.CONVERSATION_CONTEXT,
            memory_key=f"consultation_{session_id}",
            memory_value=memory_value
        )
    
    def _update_board_progress(self, board_id: str, intent: Dict[str, Any]) -> None:
        """Update inspiration board status based on conversation progress"""
        
        # Determine if board should progress
        status_triggers = {
            'organizing': ['organize', 'group', 'categorize', 'sort'],
            'refining': ['refine', 'focus', 'narrow', 'decide', 'choose'],
            'ready': ['ready', 'done', 'finished', 'contractor', 'professional']
        }
        
        current_status = None  # Would need to fetch from database
        
        # Logic to update status based on intent and current status
        # This would interact with the database to update board status
        
        logger.info(f"Board {board_id} progress evaluated based on intent: {intent['type']}")
    
    def _get_next_phase(self, current_phase: str) -> str:
        """Get the next suggested consultation phase"""
        
        phase_progression = {
            'discovery': 'exploration',
            'exploration': 'refinement',
            'refinement': 'planning',
            'planning': 'handoff',
            'handoff': 'handoff'  # Terminal state
        }
        
        return phase_progression.get(current_phase, 'exploration')