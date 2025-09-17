"""
Iris - Design Inspiration Assistant Agent (ADAPTER SYSTEM COMPLIANT)
Uses Claude Opus 4 for intelligent conversations about home design and inspiration
✅ CORRECT: Uses IrisContextAdapter for all data access (NO direct database queries)
"""
import logging
import os
from datetime import datetime
from typing import Optional

from anthropic import Anthropic
from pydantic import BaseModel, Field

# ✅ CORRECT: Import adapter instead of direct database access
from adapters.iris_context import IrisContextAdapter

logger = logging.getLogger(__name__)

class IrisRequest(BaseModel):
    """Request format for Iris API"""
    message: str = Field(..., description="User's message")
    user_id: str = Field(..., description="User ID for context")
    project_id: Optional[str] = Field(default=None, description="Project ID for context")
    board_context: Optional[dict] = Field(default=None, description="Current board context")

class IrisResponse(BaseModel):
    """Response format from Iris"""
    response: str = Field(..., description="Iris's response")
    suggestions: list[str] = Field(default_factory=list, description="Quick action suggestions")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class IrisAgent:
    """
    Iris - Your personal design inspiration assistant
    ✅ CORRECT: Uses IrisContextAdapter for all data access
    ❌ NEVER queries database tables directly
    """

    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-7-sonnet-20250219"
        
        # ✅ CORRECT: Use adapter system for all data access
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

        logger.info("Iris Agent initialized with IrisContextAdapter (CORRECT PATTERN)")

    async def process_message(self, request: IrisRequest) -> IrisResponse:
        """Process a user message using adapter system (CORRECT PATTERN)"""
        try:
            # ✅ CORRECT: Get context through adapter (not direct database queries)
            context = self.context_adapter.get_inspiration_context(
                user_id=request.user_id,
                project_id=request.project_id
            )
            
            # Build enhanced context for Claude including OTHER AGENT CONVERSATIONS
            enhanced_context = self._build_context_from_adapter(context, request.board_context)
            
            # Add context from other agents if available
            other_agent_context = self._build_other_agent_context(context)
            if other_agent_context:
                enhanced_context = f"{enhanced_context}\n\n{other_agent_context}"
            
            # Prepare messages for Claude
            messages = self._prepare_claude_messages(enhanced_context, context, request.message)

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
                iris_response = self._generate_fallback_response(request.message, enhanced_context)

            # Generate suggestions
            suggestions = self._generate_suggestions(iris_response, context)

            logger.info("Iris processed message successfully through adapter system")

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

    def _build_context_from_adapter(self, adapter_context: dict, board_context: dict = None) -> str:
        """Build context string from adapter data (CORRECT PATTERN)"""
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
            context_parts.append(f"  Budget: {project_context.get('budget_range', 'Not specified')}")
            context_parts.append(f"  Timeline: {project_context.get('timeline', 'Not specified')}")

        # Process design preferences from adapter
        design_prefs = adapter_context.get("design_preferences", {})
        if design_prefs:
            context_parts.append("Design preferences:")
            if design_prefs.get("style_preferences"):
                styles = ", ".join(design_prefs["style_preferences"][:3])
                context_parts.append(f"  Styles: {styles}")
            if design_prefs.get("color_preferences"):
                colors = ", ".join(design_prefs["color_preferences"][:4])
                context_parts.append(f"  Colors: {colors}")

        # Process previous designs from adapter
        previous_designs = adapter_context.get("previous_designs", [])
        if previous_designs:
            context_parts.append(f"Previous design projects: {len(previous_designs)}")

        # Add current board context if provided
        if board_context:
            context_parts.append(f"Current session: {board_context}")

        return "\n".join(context_parts) if context_parts else "New design session"

    def _prepare_claude_messages(self, enhanced_context: str, adapter_context: dict, current_message: str) -> list[dict]:
        """Prepare messages for Claude using adapter context"""
        messages = []

        # Add context from adapter
        if enhanced_context != "New design session":
            messages.append({
                "role": "user",
                "content": f"Context from my design history:\n{enhanced_context}\n\nI'm working on home design inspiration. Please help me."
            })
            messages.append({
                "role": "assistant",
                "content": "I understand your design context and history. I'm here to help with your inspiration and design decisions. How can I assist you today?"
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
            return """I'd love to help you explore design styles! Based on your design history, I can help you identify and organize your style preferences. Popular styles include modern, farmhouse, traditional, and industrial. What catches your eye in the images you've been collecting?"""
        
        elif "budget" in message_lower or "cost" in message_lower:
            return """Let's talk about realistic budgeting for your project. I can help you understand typical cost ranges and prioritize elements to get the most impact for your investment. What type of space are you working on?"""
        
        elif "color" in message_lower:
            return """Colors can completely transform a space! I can help you create cohesive color palettes that work with your style preferences. Are you looking for something bold and dramatic, or more neutral and calming?"""
        
        else:
            return """I'm here to help you organize and understand your design inspiration! I can help identify styles, suggest color palettes, and create actionable plans from your inspiration boards. What specific aspect of your project would you like to explore?"""

    def _build_other_agent_context(self, adapter_context: dict) -> str:
        """Build context from other agent conversations"""
        other_agents = adapter_context.get("conversations_from_other_agents", {})
        
        if not other_agents:
            return ""
        
        context_parts = []
        
        # Process homeowner agent conversations (CIA)
        homeowner_convs = other_agents.get("homeowner_conversations", [])
        if homeowner_convs:
            context_parts.append("Previous project discussions with homeowner agent:")
            for conv in homeowner_convs[:2]:  # Limit to most recent 2
                if conv.get("context"):
                    for ctx in conv["context"][:3]:  # Limit context items
                        if ctx.get("type") == "project_requirements":
                            context_parts.append(f"  - Project: {ctx.get('data', {}).get('description', 'N/A')}")
                        elif ctx.get("type") == "budget_info":
                            context_parts.append(f"  - Budget: {ctx.get('data', {}).get('range', 'N/A')}")
        
        # Process messaging conversations
        messaging_convs = other_agents.get("messaging_conversations", [])
        if messaging_convs:
            context_parts.append("Contractor communication context:")
            for conv in messaging_convs[:2]:
                context_parts.append(f"  - {conv.get('title', 'Communication thread')}")
        
        # Process project conversations
        project_convs = other_agents.get("project_conversations", [])
        if project_convs:
            context_parts.append("Related project information:")
            for conv in project_convs[:2]:
                metadata = conv.get("metadata", {})
                if metadata.get("budget_range"):
                    context_parts.append(f"  - Budget: {metadata['budget_range']}")
                if metadata.get("timeline"):
                    context_parts.append(f"  - Timeline: {metadata['timeline']}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _generate_suggestions(self, response: str, adapter_context: dict) -> list[str]:
        """Generate contextual suggestions based on adapter context"""
        response_lower = response.lower()
        
        # Base suggestions on available context
        inspiration_boards = adapter_context.get("inspiration_boards", [])
        has_project = adapter_context.get("project_context", {}).get("project_available", False)
        
        if "style" in response_lower:
            return ["Show me similar styles", "What colors work with this?", "Find matching materials", "Create a mood board"]
        elif "budget" in response_lower or "cost" in response_lower:
            return ["Show price breakdown", "Prioritize by impact", "Find budget alternatives", "Get contractor quotes"]
        elif "color" in response_lower:
            return ["Show color palette", "Find matching styles", "See room examples", "Create color scheme"]
        elif inspiration_boards and has_project:
            return ["Review my boards", "Update project budget", "Create vision summary", "Find contractors"]
        elif inspiration_boards:
            return ["Organize my boards", "Identify common themes", "Create new project", "Get style analysis"]
        else:
            return ["Create inspiration board", "Tell me your style", "Upload inspiration images", "Start a project"]

    async def save_inspiration_image(self, 
                                    conversation_id: str,
                                    image_url: str,
                                    image_metadata: dict = None) -> dict:
        """Save an inspiration image to the unified system
        
        This method allows IRIS to save images properly to the unified memory system
        instead of the legacy inspiration_images table.
        
        Args:
            conversation_id: The conversation this image belongs to
            image_url: The URL of the image to save (can be temporary)
            image_metadata: Optional metadata (room_type, style, category, etc.)
            
        Returns:
            dict with success status and memory_id if successful
        """
        try:
            from services.image_persistence_service import image_service
            import uuid
            
            # Generate unique image ID
            image_id = str(uuid.uuid4())
            
            # If it's a temporary URL (e.g., OpenAI), download and store permanently
            permanent_url = image_url
            if "oaidalleapiprodscus.blob.core.windows.net" in image_url:
                logger.info("Detected temporary OpenAI URL, downloading for permanent storage")
                permanent_url = await image_service.download_and_store_image(
                    image_url=image_url,
                    image_id=image_id,
                    image_type="png"
                )
                if not permanent_url:
                    logger.error("Failed to make image permanent")
                    return {"success": False, "error": "Failed to store image permanently"}
            
            # Extract storage path from URL
            storage_path = permanent_url.split("/")[-2:] if "/" in permanent_url else permanent_url
            storage_path = "/".join(storage_path) if isinstance(storage_path, list) else storage_path
            
            # Add default metadata if not provided
            if not image_metadata:
                image_metadata = {}
            
            # Ensure metadata has required fields
            image_metadata.update({
                "category": image_metadata.get("category", "inspiration"),
                "source": "iris_agent",
                "original_url": image_url if image_url != permanent_url else None
            })
            
            # Save to unified memory system
            memory_id = await image_service.save_to_unified_memory(
                conversation_id=conversation_id,
                image_url=permanent_url,
                image_path=storage_path,
                metadata=image_metadata
            )
            
            if memory_id:
                logger.info(f"Successfully saved inspiration image to unified system: {memory_id}")
                return {
                    "success": True,
                    "memory_id": memory_id,
                    "permanent_url": permanent_url,
                    "storage_path": storage_path
                }
            else:
                logger.error("Failed to save image to unified memory")
                return {"success": False, "error": "Failed to save to unified memory"}
                
        except Exception as e:
            logger.error(f"Error saving inspiration image: {e}")
            return {"success": False, "error": str(e)}
    
    async def save_inspiration_board_to_memory(self, 
                                              conversation_id: str,
                                              user_id: str,
                                              board_data: dict) -> bool:
        """Save inspiration board to unified conversation memory
        
        Args:
            conversation_id: The conversation this board belongs to
            user_id: The user who owns this board
            board_data: Board information (name, room_type, style, images, etc.)
            
        Returns:
            bool indicating success
        """
        try:
            import uuid
            from database import SupabaseDB
            from datetime import datetime
            
            db = SupabaseDB()
            
            memory_data = {
                "id": str(uuid.uuid4()),
                "tenant_id": "00000000-0000-0000-0000-000000000000",
                "conversation_id": conversation_id,
                "memory_scope": "homeowner",
                "memory_type": "inspiration_board",
                "memory_key": f"board_{board_data.get('room_type', 'general')}",
                "memory_value": {
                    "board_name": board_data.get("name", "Inspiration Board"),
                    "room_type": board_data.get("room_type", "general"),
                    "images": board_data.get("images", []),
                    "style_preferences": board_data.get("style_preferences", {}),
                    "created_at": datetime.utcnow().isoformat(),
                    "user_id": user_id
                },
                "importance_score": 95,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = db.client.table("unified_conversation_memory").insert(memory_data).execute()
            
            if result.data:
                logger.info(f"Saved inspiration board to unified memory: {memory_data['memory_key']}")
                return True
            else:
                logger.error("Failed to save inspiration board to unified memory")
                return False
                
        except Exception as e:
            logger.error(f"Error saving inspiration board to unified memory: {e}")
            return False
    
    async def retrieve_inspiration_images(self, user_id: str, project_id: str = None) -> list:
        """Retrieve all inspiration images for a user from unified system
        
        This method properly retrieves images from the unified memory system
        through the context adapter.
        
        Args:
            user_id: The user ID to retrieve images for
            project_id: Optional project ID to filter images
            
        Returns:
            List of image data dictionaries
        """
        try:
            # Get context through adapter (includes photos)
            context = self.context_adapter.get_inspiration_context(
                user_id=user_id,
                project_id=project_id
            )
            
            # Extract photos from unified system
            photos_data = context.get("photos_from_unified_system", {})
            
            # Combine all photo types
            all_images = []
            
            # Add project photos
            for photo in photos_data.get("project_photos", []):
                all_images.append({
                    "url": photo.get("file_path"),
                    "type": "project",
                    "metadata": photo.get("metadata", {})
                })
            
            # Add inspiration photos  
            for photo in photos_data.get("inspiration_photos", []):
                all_images.append({
                    "url": photo.get("file_path"),
                    "type": "inspiration",
                    "metadata": photo.get("metadata", {})
                })
            
            # Add message attachments
            for photo in photos_data.get("message_attachments", []):
                all_images.append({
                    "url": photo.get("file_path"),
                    "type": "attachment",
                    "metadata": photo.get("metadata", {})
                })
            
            logger.info(f"Retrieved {len(all_images)} inspiration images from unified system")
            return all_images
            
        except Exception as e:
            logger.error(f"Error retrieving inspiration images: {e}")
            return []

# Create singleton instance
iris_agent = IrisAgent()