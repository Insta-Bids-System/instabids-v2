"""
Iris - Design Inspiration Assistant Agent (UNIFIED MEMORY COMPLIANT)
Uses Claude Opus 4 for intelligent conversations about home design and inspiration
ALL data flows through unified_conversation_memory system ONLY
"""
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from anthropic import Anthropic
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class IrisMessage(BaseModel):
    """Message format for Iris conversations"""
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class IrisRequest(BaseModel):
    """Request format for Iris API"""
    message: str = Field(..., description="User's message")
    user_id: str = Field(..., description="User ID for unified memory")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for unified memory")
    tenant_id: Optional[str] = Field(default=None, description="Tenant ID for unified memory")
    board_context: Optional[dict] = Field(default=None, description="Current board context")

class IrisResponse(BaseModel):
    """Response format from Iris"""
    response: str = Field(..., description="Iris's response")
    suggestions: list[str] = Field(default_factory=list, description="Quick action suggestions")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class UnifiedMemoryManager:
    """Manages all memory operations through IrisContextAdapter (CORRECT PATTERN)"""
    
    def __init__(self):
        # ✅ CORRECT: Use adapter system instead of direct database access
        from adapters.iris_context import IrisContextAdapter
        self.adapter = IrisContextAdapter()
    
    async def ensure_conversation_exists(self, tenant_id: str, conversation_id: str, 
                                       user_id: str, conversation_type: str = "design_inspiration"):
        """Ensure conversation exists in unified_conversations table"""
        try:
            # Check if conversation exists
            existing = self.db.client.table("unified_conversations").select("id").eq("id", conversation_id).execute()
            
            if not existing.data:
                # Create conversation record
                self.db.client.table("unified_conversations").insert({
                    "id": conversation_id,
                    "tenant_id": tenant_id,
                    "created_by": user_id,
                    "conversation_type": conversation_type,
                    "entity_id": user_id,
                    "entity_type": "user",
                    "title": "Design Inspiration Session",
                    "status": "active",
                    "metadata": {"agent": "iris", "purpose": "design_assistance"},
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "last_message_at": datetime.now().isoformat()
                }).execute()
                logger.info(f"Created conversation {conversation_id} in unified system")
        except Exception as e:
            logger.error(f"Failed to ensure conversation exists: {e}")

    async def save_to_unified_memory(self, tenant_id: str, conversation_id: str, 
                                   memory_type: str, memory_key: str, memory_value: dict,
                                   importance_score: int = 5):
        """Save data to unified_conversation_memory table"""
        try:
            self.db.client.table("unified_conversation_memory").insert({
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "conversation_id": conversation_id,
                "memory_scope": "conversation",
                "memory_type": memory_type,
                "memory_key": memory_key,
                "memory_value": memory_value,
                "importance_score": importance_score,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }).execute()
            logger.info(f"Saved {memory_type} to unified memory")
        except Exception as e:
            logger.error(f"Failed to save to unified memory: {e}")
    
    async def load_from_unified_memory(self, user_id: str, project_id: str = None) -> dict:
        """Load data using IrisContextAdapter (CORRECT PATTERN)"""
        try:
            # ✅ CORRECT: Use adapter instead of direct database queries
            return self.adapter.get_inspiration_context(user_id=user_id, project_id=project_id)
        except Exception as e:
            logger.error(f"Failed to load from adapter: {e}")
            return {}
    
    async def save_conversation_message(self, tenant_id: str, conversation_id: str,
                                      role: str, content: str, metadata: dict = None):
        """Save conversation message to unified memory"""
        await self.save_to_unified_memory(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            memory_type="conversation_message",
            memory_key=f"message_{datetime.now().timestamp()}",
            memory_value={
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat()
            },
            importance_score=7
        )
    
    async def save_user_preference(self, tenant_id: str, conversation_id: str,
                                 preference_type: str, preference_data: dict):
        """Save user preferences to unified memory"""
        await self.save_to_unified_memory(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            memory_type="preference",
            memory_key=preference_type,
            memory_value=preference_data,
            importance_score=8
        )
    
    async def save_design_analysis(self, tenant_id: str, conversation_id: str,
                                 analysis_data: dict):
        """Save design analysis to unified memory"""
        await self.save_to_unified_memory(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            memory_type="design_analysis",
            memory_key=f"analysis_{datetime.now().timestamp()}",
            memory_value=analysis_data,
            importance_score=6
        )

class IrisAgent:
    """
    Iris - Your personal design inspiration assistant
    Powered by Claude Opus 4 for intelligent design conversations
    ALL DATA FLOWS THROUGH UNIFIED MEMORY SYSTEM ONLY
    """

    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-7-sonnet-20250219"
        self.memory_manager = UnifiedMemoryManager()

        # Iris's personality and expertise
        self.system_prompt = """You are Iris, a friendly and knowledgeable design inspiration assistant for InstaBids.

Your personality:
- Creative, encouraging, and helpful
- Expert in interior design, architecture, and home improvement
- Knowledgeable about design styles, trends, and practical considerations
- Budget-conscious and realistic about costs
- Helps organize scattered ideas into cohesive visions

Your capabilities:
- Analyze uploaded images to identify styles, colors, materials, and design elements
- Suggest how to organize and group inspiration images
- Identify common themes and potential conflicts in design choices
- Provide realistic budget estimates based on similar projects
- Guide users from inspiration to actionable project plans
- Help create vision summaries for contractors

CRITICAL: All conversation data and preferences are stored in the unified memory system.
When users upload images, you help them understand design elements and preferences.
Always be encouraging but honest. Help users refine their vision while keeping it achievable.

Current context will be provided with each message."""

        logger.info("Iris Agent initialized with unified memory system integration")

    async def process_message(self, request: IrisRequest) -> IrisResponse:
        """Process a user message through unified memory system"""
        try:
            # Generate conversation and tenant IDs if not provided
            conversation_id = request.conversation_id or str(uuid.uuid4())
            tenant_id = request.tenant_id or request.user_id
            
            # Ensure conversation exists in unified system
            await self.memory_manager.ensure_conversation_exists(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                user_id=request.user_id
            )
            
            # Load conversation history from unified memory
            conversation_history = await self.memory_manager.load_from_unified_memory(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                memory_type="conversation_message"
            )
            
            # Load user preferences from unified memory
            preferences = await self.memory_manager.load_from_unified_memory(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                memory_type="preference"
            )
            
            # Build context for Claude
            context = self._build_unified_context(conversation_history, preferences, request.board_context)
            
            # Prepare messages for Claude
            messages = self._prepare_claude_messages(conversation_history, context, request.message)

            # Get response from Claude
            try:
                response = self.anthropic.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    temperature=0.7,
                    system=self.system_prompt,
                    messages=messages
                )
                iris_response = response.content[0].text
                logger.info("Claude API call successful")
            except Exception as api_error:
                logger.warning(f"API call failed: {api_error}")
                iris_response = self._generate_fallback_response(request.message, context)

            # Generate suggestions
            suggestions = self._generate_suggestions(iris_response)

            # Save user message to unified memory
            await self.memory_manager.save_conversation_message(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                role="user",
                content=request.message,
                metadata={"board_context": request.board_context}
            )

            # Save assistant response to unified memory
            await self.memory_manager.save_conversation_message(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                role="assistant",
                content=iris_response,
                metadata={"suggestions": suggestions}
            )

            # Extract and save preferences if detected
            await self._extract_and_save_preferences(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                message=request.message,
                response=iris_response
            )

            logger.info("Iris processed message successfully through unified memory")

            return IrisResponse(
                response=iris_response,
                suggestions=suggestions
            )

        except Exception as e:
            logger.error(f"Error processing Iris message: {e}")
            return IrisResponse(
                response=f"I encountered an issue: {str(e)[:100]}... Let me try a different approach. What specific aspect of your project would you like to discuss?",
                suggestions=["Tell me about your project", "What style do you prefer?", "Show me your inspiration"]
            )

    def _build_unified_context(self, conversation_history: list, preferences: list, board_context: dict = None) -> str:
        """Build context from unified memory data"""
        context_parts = []

        # Add conversation context
        if conversation_history:
            context_parts.append(f"Previous conversation messages: {len(conversation_history)}")
            
            # Get recent preferences mentioned
            recent_messages = conversation_history[-5:]  # Last 5 messages
            for msg in recent_messages:
                if msg.get("memory_value", {}).get("role") == "user":
                    content = msg["memory_value"]["content"]
                    if any(keyword in content.lower() for keyword in ["style", "color", "budget", "prefer"]):
                        context_parts.append(f"User mentioned: {content[:100]}...")

        # Add saved preferences
        if preferences:
            context_parts.append(f"Saved preferences: {len(preferences)}")
            for pref in preferences[-3:]:  # Last 3 preferences
                pref_data = pref.get("memory_value", {})
                context_parts.append(f"  {pref['memory_key']}: {str(pref_data)[:50]}...")

        # Add board context
        if board_context:
            context_parts.append(f"Board context: {board_context}")

        return "\n".join(context_parts) if context_parts else "New conversation"

    def _prepare_claude_messages(self, conversation_history: list, context: str, current_message: str) -> list[dict]:
        """Prepare messages for Claude from unified memory"""
        messages = []

        # Add context
        if context != "New conversation":
            messages.append({
                "role": "user",
                "content": f"Context:\n{context}\n\nI'm working on home design inspiration. Please help me."
            })
            messages.append({
                "role": "assistant", 
                "content": "I understand your design context. How can I help you today?"
            })

        # Add recent conversation history from unified memory
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                msg_data = msg.get("memory_value", {})
                if msg_data.get("role") in ["user", "assistant"]:
                    messages.append({
                        "role": msg_data["role"],
                        "content": msg_data["content"]
                    })

        # Add current message
        messages.append({
            "role": "user",
            "content": current_message
        })

        return messages

    def _generate_fallback_response(self, message: str, context: str) -> str:
        """Generate intelligent fallback response when API unavailable"""
        message_lower = message.lower()
        
        if "style" in message_lower:
            return """I'd love to help you explore design styles! Based on what you're sharing, I can help you identify and organize your style preferences. Popular styles include modern, farmhouse, traditional, and industrial. What catches your eye in the images you've been collecting?"""
        
        elif "budget" in message_lower or "cost" in message_lower:
            return """Let's talk about realistic budgeting for your project. I can help you understand typical cost ranges and prioritize elements to get the most impact for your investment. What type of space are you working on?"""
        
        else:
            return """I'm here to help you organize and understand your design inspiration! I can help identify styles, suggest color palettes, and create actionable plans. What specific aspect of your project would you like to explore?"""

    def _generate_suggestions(self, response: str) -> list[str]:
        """Generate contextual suggestions"""
        response_lower = response.lower()
        
        if "style" in response_lower:
            return ["Show me similar styles", "What colors work with this?", "Find matching materials", "Create a mood board"]
        elif "budget" in response_lower or "cost" in response_lower:
            return ["Show price breakdown", "Prioritize by impact", "Find budget alternatives", "Get contractor quotes"]
        elif "color" in response_lower:
            return ["Show color palette", "Find matching styles", "See room examples", "Create color scheme"]
        else:
            return ["Tell me your style", "Show inspiration images", "Discuss budget range", "Create project plan"]

    async def _extract_and_save_preferences(self, tenant_id: str, conversation_id: str, 
                                          message: str, response: str):
        """Extract and save preferences to unified memory"""
        message_lower = message.lower()
        
        # Extract style preferences
        style_keywords = {
            "modern": ["modern", "contemporary", "minimalist", "clean"],
            "farmhouse": ["farmhouse", "rustic", "country", "barn"],
            "traditional": ["traditional", "classic", "timeless"],
            "industrial": ["industrial", "loft", "exposed", "metal"]
        }
        
        detected_styles = []
        for style, keywords in style_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_styles.append(style)
        
        if detected_styles:
            await self.memory_manager.save_user_preference(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                preference_type="style_preferences",
                preference_data={"styles": detected_styles, "timestamp": datetime.now().isoformat()}
            )
        
        # Extract color preferences
        color_keywords = ["white", "black", "gray", "blue", "green", "beige", "wood", "natural"]
        detected_colors = [color for color in color_keywords if color in message_lower]
        
        if detected_colors:
            await self.memory_manager.save_user_preference(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                preference_type="color_preferences", 
                preference_data={"colors": detected_colors, "timestamp": datetime.now().isoformat()}
            )
        
        # Extract budget mentions
        if any(word in message_lower for word in ["budget", "cost", "expensive", "affordable", "cheap", "price"]):
            budget_context = message[:200] if len(message) > 200 else message
            await self.memory_manager.save_user_preference(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                preference_type="budget_discussion",
                preference_data={"context": budget_context, "timestamp": datetime.now().isoformat()}
            )

# Create singleton instance
iris_agent = IrisAgent()