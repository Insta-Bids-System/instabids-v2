"""
Iris - Design Inspiration Assistant Agent WITH COST TRACKING
Uses Claude with complete token and cost monitoring
"""
import logging
import os
from datetime import datetime
from typing import Optional

from anthropic import Anthropic
from pydantic import BaseModel, Field

# Import the cost tracking system
from services.llm_cost_tracker import get_tracked_anthropic_client

# Import adapter for data access
from adapters.iris_context import IrisContextAdapter

logger = logging.getLogger(__name__)

class IrisRequest(BaseModel):
    """Request format for Iris API"""
    message: str = Field(..., description="User's message")
    user_id: str = Field(..., description="User ID for context")
    project_id: Optional[str] = Field(default=None, description="Project ID for context")
    board_context: Optional[dict] = Field(default=None, description="Current board context")
    session_id: Optional[str] = Field(default=None, description="Session ID for cost tracking")

class IrisResponse(BaseModel):
    """Response format from Iris"""
    response: str = Field(..., description="Iris's response")
    suggestions: list[str] = Field(default_factory=list, description="Quick action suggestions")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    cost_info: Optional[dict] = Field(default=None, description="Cost tracking info")

class IrisAgentTracked:
    """
    Iris Agent with COMPLETE COST TRACKING
    Tracks every token, calculates costs, stores in database
    """

    def __init__(self):
        # Initialize tracked Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Use the tracked client instead of regular Anthropic
        self.anthropic = get_tracked_anthropic_client(
            agent_name="IRIS",
            api_key=api_key,
            is_async=False  # IRIS uses sync client
        )
        
        self.model = "claude-3-7-sonnet-20250219"
        
        # Use adapter system for all data access
        self.context_adapter = IrisContextAdapter()

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

✅ IMPORTANT: You receive filtered, privacy-compliant context through the adapter system.
Always work within the context provided and respect user privacy boundaries.

Current context will be provided with each message."""

        logger.info("Iris Agent initialized with COST TRACKING enabled")

    async def process_message(self, request: IrisRequest) -> IrisResponse:
        """Process a user message with COMPLETE COST TRACKING"""
        try:
            # Get context through adapter
            context = self.context_adapter.get_inspiration_context(
                user_id=request.user_id,
                project_id=request.project_id
            )
            
            # Build enhanced context for Claude
            enhanced_context = self._build_context_from_adapter(context, request.board_context)
            
            # Add context from other agents if available
            other_agent_context = self._build_other_agent_context(context)
            if other_agent_context:
                enhanced_context = f"{enhanced_context}\n\n{other_agent_context}"
            
            # Prepare messages for Claude
            messages = self._prepare_claude_messages(enhanced_context, context, request.message)

            # Get response from Claude WITH TRACKING
            try:
                # The tracked client automatically logs tokens and costs
                response = await self.anthropic.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    temperature=0.7,
                    system=self.system_prompt,
                    messages=messages,
                    # Pass context for cost attribution
                    metadata={
                        "user_id": request.user_id,
                        "session_id": request.session_id,
                        "project_id": request.project_id
                    }
                )
                
                iris_response = response.content[0].text
                
                # Extract cost information from response
                cost_info = None
                if hasattr(response, 'usage') and response.usage:
                    cost_info = {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "model": self.model,
                        "provider": "anthropic"
                    }
                
                logger.info(f"Claude API call successful - Tokens: {cost_info}")
                
            except Exception as api_error:
                logger.warning(f"API call failed: {api_error}")
                iris_response = self._generate_fallback_response(request.message, enhanced_context)
                cost_info = {"error": str(api_error)}

            # Generate suggestions
            suggestions = self._generate_suggestions(iris_response, context)

            logger.info("Iris processed message successfully with cost tracking")

            return IrisResponse(
                response=iris_response,
                suggestions=suggestions,
                cost_info=cost_info
            )

        except Exception as e:
            logger.error(f"Error processing Iris message: {e}")
            return IrisResponse(
                response=f"I encountered an issue: {str(e)[:100]}... Let me try a different approach. What specific aspect of your project would you like to discuss?",
                suggestions=["Tell me about your project", "What style do you prefer?", "Show me your inspiration"],
                cost_info={"error": str(e)}
            )

    def _build_context_from_adapter(self, adapter_context: dict, board_context: dict = None) -> str:
        """Build context string from adapter data"""
        context_parts = []

        # Process inspiration boards from adapter
        inspiration_boards = adapter_context.get("inspiration_boards", [])
        if inspiration_boards:
            context_parts.append(f"Inspiration boards: {len(inspiration_boards)}")
            for board in inspiration_boards[:3]:  # Show first 3 boards
                title = board.get("title", "Untitled")
                room_type = board.get("room_type", "")
                context_parts.append(f"  - {title} ({room_type})")

        # Process project context from adapter
        project_context = adapter_context.get("project_context", {})
        if project_context.get("project_available"):
            context_parts.append("Current project:")
            context_parts.append(f"  Type: {project_context.get('project_type', 'Unknown')}")
            context_parts.append(f"  Stage: {project_context.get('stage', 'Unknown')}")

        # Process vision summary from adapter
        vision_summary = adapter_context.get("vision_summary", {})
        if vision_summary.get("has_vision"):
            context_parts.append(f"Vision: {vision_summary.get('summary', '')[:200]}...")

        # Add board context if provided
        if board_context:
            context_parts.append(f"\nCurrent board: {board_context.get('title', 'Untitled')}")
            if board_context.get("images"):
                context_parts.append(f"  Images: {len(board_context['images'])}")

        return "\n".join(context_parts) if context_parts else "No specific context available."

    def _build_other_agent_context(self, context: dict) -> str:
        """Build context from other agent conversations"""
        parts = []
        
        # CIA conversation context
        cia_context = context.get("cia_conversation", {})
        if cia_context.get("has_conversation"):
            parts.append("Recent CIA conversation topics:")
            for topic in cia_context.get("topics", [])[:3]:
                parts.append(f"  - {topic}")
        
        return "\n".join(parts) if parts else ""

    def _prepare_claude_messages(self, enhanced_context: str, context: dict, user_message: str) -> list:
        """Prepare messages for Claude API"""
        messages = []
        
        # Add context as system-like user message
        if enhanced_context and enhanced_context != "No specific context available.":
            messages.append({
                "role": "user",
                "content": f"Context:\n{enhanced_context}\n\nUser message: {user_message}"
            })
        else:
            messages.append({
                "role": "user",
                "content": user_message
            })
        
        return messages

    def _generate_suggestions(self, response: str, context: dict) -> list[str]:
        """Generate contextual suggestions based on response"""
        suggestions = []
        
        # Basic suggestions
        if "style" in response.lower():
            suggestions.append("Show me modern examples")
            suggestions.append("What about traditional styles?")
        
        if "budget" in response.lower():
            suggestions.append("What's a realistic budget?")
            suggestions.append("How can I save money?")
        
        if "color" in response.lower():
            suggestions.append("Show me color palettes")
            suggestions.append("What colors work together?")
        
        # Default suggestions if none generated
        if not suggestions:
            suggestions = [
                "Tell me more about this",
                "Show me examples",
                "What are my options?"
            ]
        
        return suggestions[:3]  # Return max 3 suggestions

    def _generate_fallback_response(self, message: str, context: str) -> str:
        """Generate a fallback response when API fails"""
        return (
            "I'm having trouble connecting right now, but I'd love to help with your design project. "
            "Could you tell me more about what you're envisioning? Are you looking for style ideas, "
            "color schemes, or layout suggestions?"
        )