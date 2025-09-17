"""
Consolidated Iris Chat API - GPT-5 Inspiration Finding Assistant
Focus: Help homeowners organize current vs ideal spaces and find inspiration
NO IMAGE GENERATION - Pure inspiration discovery and organization
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Optional

from openai import OpenAI
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import Client, create_client

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize OpenAI client
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    logger.warning("OPENAI_API_KEY not found, using fallback responses")
    client = None
else:
    client = OpenAI(api_key=openai_key)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
if not supabase_url or not supabase_service_key:
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    if supabase_url and supabase_anon_key:
        logger.warning("Using SUPABASE_ANON_KEY instead of SERVICE_ROLE_KEY for development")
        supabase: Client = create_client(supabase_url, supabase_anon_key)
    else:
        logger.error("Supabase configuration missing")
        supabase = None
else:
    supabase: Client = create_client(supabase_url, supabase_service_key)

class IrisChatRequest(BaseModel):
    message: str
    user_id: str
    board_id: Optional[str] = None
    conversation_context: Optional[list[dict]] = None

class IrisChatResponse(BaseModel):
    response: str
    suggestions: list[str]
    board_id: Optional[str] = None
    created_board: bool = False

@router.post("/chat", response_model=IrisChatResponse)
async def iris_chat(request: IrisChatRequest):
    """
    Consolidated Iris chat focused on inspiration finding and organization
    """
    try:
        # 1. Get or create board for this conversation
        board_id = await get_or_create_board(request.user_id, request.board_id, request.message)
        created_board = not request.board_id

        # 2. Load context for this homeowner and board
        context = await build_conversation_context(
            user_id=request.user_id,
            board_id=board_id,
            conversation_context=request.conversation_context or []
        )

        # 3. Get GPT-5 response focused on inspiration and organization
        gpt_response = await get_inspiration_focused_response(
            message=request.message,
            context=context,
            board_id=board_id
        )

        # 4. Save conversation to database
        await save_conversation_turn(
            user_id=request.user_id,
            board_id=board_id,
            user_message=request.message,
            assistant_response=gpt_response["response"]
        )

        return IrisChatResponse(
            response=gpt_response["response"],
            suggestions=gpt_response["suggestions"],
            board_id=board_id,
            created_board=created_board
        )

    except Exception as e:
        logger.error(f"Error in iris_chat: {e}")
        return IrisChatResponse(
            response="I'm here to help you organize your design inspiration and understand your current space! Tell me about your project - what room are you working on?",
            suggestions=["Tell me about my current space", "Help me find inspiration", "Organize my project ideas", "What style am I drawn to?"],
            board_id=request.board_id,
            created_board=False
        )

async def get_or_create_board(user_id: str, board_id: Optional[str], message: str) -> str:
    """Get existing board or create new one based on conversation"""
    
    if board_id and supabase:
        # Verify board exists and belongs to homeowner
        result = supabase.table("inspiration_boards").select("*").eq("id", board_id).eq("user_id", user_id).execute()
        if result.data:
            return board_id

    # Create new board - determine topic from message using AI if available
    if client:
        topic = await determine_board_topic_with_ai(message)
    else:
        topic = determine_board_topic_fallback(message)

    new_board = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": topic["title"],
        "description": topic["description"],
        "room_type": topic["room_type"],
        "status": "collecting",
        "created_at": datetime.now().isoformat()
    }

    if supabase:
        try:
            supabase.table("inspiration_boards").insert(new_board).execute()
        except Exception as e:
            logger.error(f"Error creating board: {e}")

    return new_board["id"]

async def determine_board_topic_with_ai(message: str) -> dict[str, str]:
    """Use GPT-5 to intelligently determine board topic from message"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",  # Use GPT-4 as fallback if GPT-5 not available
            messages=[
                {
                    "role": "system",
                    "content": """Analyze the user's message and determine what type of design board to create. 

Return a JSON object with:
- title: A compelling board title (max 50 chars)
- description: A brief description (max 100 chars)
- room_type: One of: kitchen, bathroom, living_room, bedroom, outdoor_backyard, dining_room, home_office, general

Examples:
"I want artificial turf for my backyard" -> {"title": "Backyard Turf Project", "description": "Artificial turf and outdoor design ideas", "room_type": "outdoor_backyard"}"""
                },
                {
                    "role": "user",
                    "content": f"Create a board for: {message}"
                }
            ],
            max_tokens=200
        )

        result = response.choices[0].message.content
        import json
        return json.loads(result)
    except Exception as e:
        logger.error(f"AI topic determination failed: {e}")
        return determine_board_topic_fallback(message)

def determine_board_topic_fallback(message: str) -> dict[str, str]:
    """Fallback board topic determination"""
    message_lower = message.lower()

    if any(word in message_lower for word in ["backyard", "lawn", "grass", "turf", "outdoor"]):
        return {
            "title": "Backyard Transformation",
            "description": "Outdoor space and lawn renovation ideas",
            "room_type": "outdoor_backyard"
        }
    elif any(word in message_lower for word in ["kitchen", "cook", "cabinet", "counter"]):
        return {
            "title": "Kitchen Renovation",
            "description": "Kitchen design and renovation inspiration",
            "room_type": "kitchen"
        }
    elif any(word in message_lower for word in ["bathroom", "shower", "bath", "tile"]):
        return {
            "title": "Bathroom Renovation", 
            "description": "Bathroom design and renovation ideas",
            "room_type": "bathroom"
        }
    else:
        return {
            "title": "Home Design Project",
            "description": "Design inspiration and renovation ideas",
            "room_type": "general"
        }

async def build_conversation_context(user_id: str, board_id: str, conversation_context: list[dict]) -> dict[str, Any]:
    """Build context for conversation"""
    
    context = {
        "user_id": user_id,
        "board_id": board_id,
        "conversation_context": conversation_context,
        "board": {"title": "Design Project", "room_type": "general"},
        "images": [],
        "conversation_history": []
    }
    
    if not supabase:
        return context
    
    try:
        # Get board details
        board_result = supabase.table("inspiration_boards").select("*").eq("id", board_id).execute()
        if board_result.data:
            context["board"] = board_result.data[0]

        # Get board images
        images_result = supabase.table("inspiration_images").select("*").eq("board_id", board_id).execute()
        context["images"] = images_result.data or []

        # Get conversation history
        history_result = supabase.table("inspiration_conversations").select("*").eq("board_id", board_id).order("created_at").execute()
        context["conversation_history"] = history_result.data or []

    except Exception as e:
        logger.error(f"Error building context: {e}")
    
    return context

async def get_inspiration_focused_response(message: str, context: dict[str, Any], board_id: str) -> dict[str, Any]:
    """Get GPT-5 response focused on inspiration finding and organization"""
    
    # Check if we have GPT access
    if not client:
        return get_fallback_inspiration_response(message, context)
    
    # Build system prompt focused on inspiration and organization
    system_prompt = build_inspiration_system_prompt(context)
    
    # Build messages for GPT
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history
    for turn in context.get("conversation_history", [])[-5:]:  # Last 5 turns
        if turn.get("user_message"):
            messages.append({"role": "user", "content": turn["user_message"]})
        if turn.get("assistant_response"):
            messages.append({"role": "assistant", "content": turn["assistant_response"]})
    
    # Add current context
    for msg in context.get("conversation_context", [])[-3:]:  # Last 3 messages
        if msg.get("role") in ["user", "assistant"]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    try:
        logger.info(f"Calling GPT for inspiration response: {message[:50]}...")
        
        response = client.chat.completions.create(
            model="gpt-4",  # Use GPT-4 as reliable fallback
            messages=messages,
            max_tokens=1500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Generate suggestions
        suggestions = generate_inspiration_suggestions(context, message, ai_response)
        
        return {
            "response": ai_response,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"GPT API error: {e}")
        return get_fallback_inspiration_response(message, context)

def build_inspiration_system_prompt(context: dict[str, Any]) -> str:
    """Build system prompt focused on inspiration and organization"""
    
    board = context.get("board", {})
    images = context.get("images", [])
    room_type = board.get("room_type", "general")
    
    return f"""You are Iris, a helpful interior design assistant specializing in inspiration discovery and project organization. You help homeowners understand their current spaces and find their ideal design vision.

CURRENT PROJECT:
- Project: {board.get('title', 'Design Project')} ({room_type})
- Description: {board.get('description', 'Home design project')}
- Images uploaded: {len(images)}

YOUR ROLE:
1. Help them describe and understand their current space
2. Guide them to articulate their ideal vision
3. Help organize their inspiration into current vs ideal categories
4. Ask clarifying questions about style, functionality, and preferences
5. Extract specific elements they love from inspiration images
6. Prepare comprehensive project briefs for contractors

CONVERSATION APPROACH:
- Be warm, conversational, and encouraging
- Ask specific questions about what they want their space to feel like
- Help them identify specific materials, colors, and styles they're drawn to
- Focus on understanding their lifestyle and how they use the space
- Guide them to organize their thoughts into actionable requirements

IMPORTANT: You do NOT generate images. Instead, you help them:
- Understand what style they're drawn to
- Organize their current vs ideal images
- Describe what they're looking for so they can search for inspiration
- Prepare detailed project requirements for contractors

Remember: Your goal is to help them create a clear, organized understanding of their project that contractors can work with."""

def get_fallback_inspiration_response(message: str, context: dict[str, Any]) -> dict[str, Any]:
    """Fallback response when GPT is not available"""
    
    board = context.get("board", {})
    room_type = board.get("room_type", "general")
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["current", "space", "room", "now", "existing"]):
        response = f"""I'd love to help you understand your current {room_type}! Tell me about what you have now:

• What do you like about your current space?
• What frustrates you or needs to change?
• How do you currently use this space?
• What specific elements feel outdated or problematic?

Understanding your current situation helps me guide you toward the perfect solution for your needs and lifestyle."""
        
        suggestions = ["Describe what I like about current space", "Tell you what needs to change", "Show you how I use this space", "Explain my biggest frustrations"]
    
    elif any(word in message_lower for word in ["inspiration", "ideas", "style", "look", "want", "ideal"]):
        response = f"""Perfect! Let's explore your ideal vision for this {room_type}. I can help you organize your inspiration and understand your style preferences:

• What feeling do you want your space to have? (cozy, modern, elegant, etc.)
• Are there specific colors that appeal to you?
• What materials do you gravitate toward? (wood, metal, stone, etc.)
• Do you have any inspiration images you'd like to discuss?

I'll help you organize your ideas into current vs ideal categories so we can create a clear project brief."""
        
        suggestions = ["Describe the feeling I want", "Talk about colors I love", "Discuss materials that appeal to me", "Help organize my inspiration"]
    
    else:
        response = f"""Hi! I'm Iris, your design assistant for this {room_type} project. I specialize in helping you organize your design inspiration and understand what you want to achieve.

I can help you:
• Understand and document your current space
• Organize your ideal inspiration and style preferences  
• Extract specific elements you love from inspiration images
• Create a comprehensive project brief for contractors

What would you like to focus on first - your current space or your ideal vision?"""
        
        suggestions = ["Tell you about my current space", "Explore my ideal vision", "Help organize my inspiration", "Create a project brief"]
    
    return {
        "response": response,
        "suggestions": suggestions
    }

def generate_inspiration_suggestions(context: dict[str, Any], message: str, response: str) -> list[str]:
    """Generate suggestions focused on inspiration and organization"""
    
    board = context.get("board", {})
    images = context.get("images", [])
    room_type = board.get("room_type", "general")
    message_lower = message.lower()
    
    # Suggestions based on conversation content
    if any(word in message_lower for word in ["current", "existing", "now", "have"]):
        return [
            "Help me identify what needs changing",
            "Explore ideal design styles", 
            "Find inspiration images",
            "Organize my project requirements"
        ]
    elif any(word in message_lower for word in ["style", "inspiration", "look", "feel"]):
        return [
            "Help me find similar styles",
            "Describe specific elements I love",
            "Organize current vs ideal images",
            "Create project brief for contractors"
        ]
    elif len(images) > 0:
        return [
            "Help me analyze these images", 
            "Organize into current vs ideal",
            "Extract elements I love",
            "Find more similar inspiration"
        ]
    else:
        return [
            "Tell you about my current space",
            "Explore ideal design styles",
            "Upload inspiration images", 
            "Help organize my project vision"
        ]

async def save_conversation_turn(user_id: str, board_id: str, user_message: str, assistant_response: str):
    """Save conversation turn to database"""
    
    if not supabase:
        return
    
    conversation_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "board_id": board_id,
        "user_message": user_message,
        "assistant_response": assistant_response,
        "created_at": datetime.now().isoformat()
    }

    try:
        supabase.table("inspiration_conversations").insert(conversation_data).execute()
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")

# Image analysis endpoint for uploaded images
class ImageAnalysisRequest(BaseModel):
    image_urls: list[str]
    category: str  # 'current' or 'ideal'
    filenames: list[str]
    board_id: str

class ImageAnalysisResponse(BaseModel):
    analysis: str
    tags: list[str]
    category: str

@router.post("/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image(request: ImageAnalysisRequest):
    """
    Analyze uploaded images for inspiration organization
    """
    try:
        if not client:
            # Fallback analysis
            if request.category == "current":
                analysis = "I can see your current space. What aspects of this space would you most like to change or improve?"
                tags = ["current-space", "needs-assessment"]
            else:
                analysis = "This inspiration image shows some great design elements. What specifically appeals to you about this style?"
                tags = ["inspiration", "style-reference"]
        else:
            # Use GPT-4 for image analysis
            analysis_prompt = f"""Analyze this {request.category} space image. If it's a current space, identify what needs improvement. If it's inspiration, identify appealing design elements.

Focus on:
- Style characteristics 
- Materials and finishes
- Color palette
- Functional elements
- Overall aesthetic

Provide helpful analysis for a homeowner planning a renovation."""

            response = client.chat.completions.create(
                model="gpt-4-vision-preview",  # GPT-4 with vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": analysis_prompt},
                            {"type": "image_url", "image_url": {"url": request.image_urls[0]}}
                        ]
                    }
                ],
                max_tokens=500
            )
            
            analysis = response.choices[0].message.content
            
            # Generate tags based on category
            if request.category == "current":
                tags = ["current-space", "needs-improvement", "existing-conditions"]
            else:
                tags = ["inspiration", "style-reference", "design-goals"]

        return ImageAnalysisResponse(
            analysis=analysis,
            tags=tags,
            category=request.category
        )
        
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        return ImageAnalysisResponse(
            analysis=f"I can see you've uploaded a {request.category} image. Tell me what specific aspects of this image appeal to you or concern you!",
            tags=[request.category, "pending-analysis"],
            category=request.category
        )

# Inspiration Finding Models
class InspirationRequest(BaseModel):
    board_id: Optional[str] = None
    ideal_image_id: Optional[str] = None
    current_image_id: Optional[str] = None
    search_query: str = "modern kitchen renovation ideas"
    user_id: str

class InspirationResponse(BaseModel):
    response: str
    inspiration_items: Optional[list[dict]] = None
    suggestions: list[str] = []

@router.post("/find-inspiration", response_model=InspirationResponse)
async def find_inspiration(request: InspirationRequest):
    """Find inspiration online based on user preferences"""
    
    # Save found inspiration images to the board
    def save_inspiration_to_board(items: list[dict], board_id: str, user_id: str, query: str):
        if not supabase or not board_id:
            return
        
        try:
            for item in items:
                result = supabase.table("inspiration_images").insert({
                    "board_id": board_id,
                    "user_id": user_id,
                    "image_url": item.get("image_url", ""),
                    "category": "ideal",  # Found inspiration is always ideal
                    "source": "url",  # Use 'url' for AI-found images
                    "tags": ["ai-discovered", "inspiration", "online-find"],
                    "ai_analysis": {
                        "description": item.get("description", ""),
                        "found_via": "iris_search",
                        "search_query": query
                    }
                }).execute()
                logger.info(f"Saved inspiration image: {item.get('description')}")
        except Exception as e:
            logger.error(f"Error saving inspiration images: {e}")
    
    try:
        # Use GPT to search for and describe inspiration
        if client:
            response = client.chat.completions.create(
                model="gpt-4o",  # Use gpt-4o as fallback
                messages=[
                    {
                        "role": "system",
                        "content": """You are Iris, an expert design assistant who helps find inspiration online.
                        Based on the search query, suggest specific design ideas and inspiration that would help the homeowner.
                        Be specific about styles, materials, colors, and features they might love."""
                    },
                    {
                        "role": "user",
                        "content": f"Find inspiration for: {request.search_query}"
                    }
                ],
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # Create inspiration items with placeholder images
            # In production, these would come from a real image search API
            inspiration_items = [
                {
                    "description": "Modern farmhouse kitchen with white shaker cabinets",
                    "image_url": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400",
                    "source": "inspiration"
                },
                {
                    "description": "Minimalist design with handleless cabinets",
                    "image_url": "https://images.unsplash.com/photo-1556911220-bff31c812dba?w=400",
                    "source": "inspiration"
                },
                {
                    "description": "Two-tone kitchen with dark island",
                    "image_url": "https://images.unsplash.com/photo-1556911261-6bd341186b2f?w=400",
                    "source": "inspiration"
                },
                {
                    "description": "Open shelving with subway tile backsplash",
                    "image_url": "https://images.unsplash.com/photo-1556909212-d5b604d0c90d?w=400",
                    "source": "inspiration"
                }
            ]
            
            # Save inspiration images to board if provided
            if request.board_id:
                save_inspiration_to_board(
                    inspiration_items, 
                    request.board_id, 
                    request.user_id,
                    request.search_query
                )
            
            return InspirationResponse(
                response=content,
                inspiration_items=inspiration_items,
                suggestions=[
                    "Show me more farmhouse styles",
                    "Find minimalist kitchens",
                    "Explore two-tone designs",
                    "Search for backsplash ideas"
                ]
            )
    except Exception as e:
        logger.error(f"Error finding inspiration: {e}")
    
    # Fallback response
    return InspirationResponse(
        response="""I found some great inspiration ideas for your project:

• **Modern Farmhouse**: White shaker cabinets with black hardware, marble countertops, and rustic wood accents
• **Contemporary Minimalist**: Handleless cabinets, integrated appliances, and clean lines
• **Transitional Style**: Mix of traditional and modern elements with neutral colors
• **Industrial Chic**: Exposed elements, metal accents, and concrete countertops

Which style direction appeals to you most? I can find more specific examples!""",
        inspiration_items=[
            {
                "description": "Modern farmhouse with shiplap accents",
                "image_url": "https://images.unsplash.com/photo-1565538810643-b5bdb714032a?w=400",
                "source": "inspiration"
            },
            {
                "description": "Sleek minimalist with hidden storage",
                "image_url": "https://images.unsplash.com/photo-1556912167-f556f1f39fdf?w=400",
                "source": "inspiration"
            },
            {
                "description": "Classic transitional with timeless appeal",
                "image_url": "https://images.unsplash.com/photo-1560440021-33f9b867899d?w=400",
                "source": "inspiration"
            },
            {
                "description": "Bold industrial with character",
                "image_url": "https://images.unsplash.com/photo-1556908221-f685cba3b0c0?w=400",
                "source": "inspiration"
            }
        ],
        suggestions=[
            "Tell me more about farmhouse style",
            "Show minimalist examples",
            "Find transitional kitchens",
            "Explore industrial designs"
        ]
    )

# Vision Summary Models
class VisionSummaryRequest(BaseModel):
    board_id: Optional[str] = None
    ideal_image_id: Optional[str] = None
    current_image_id: Optional[str] = None
    user_id: str

class VisionSummaryResponse(BaseModel):
    summary: str
    key_elements: list[str] = []
    next_steps: list[str] = []

@router.post("/create-vision-summary", response_model=VisionSummaryResponse)
async def create_vision_summary(request: VisionSummaryRequest):
    """Create a vision summary from uploaded images"""
    
    try:
        # Use GPT to create comprehensive vision summary
        if client:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are Iris, an expert design assistant creating project vision summaries.
                        Analyze the current and ideal images to create a clear vision document that contractors can understand.
                        Focus on specific elements, materials, colors, and the transformation needed."""
                    },
                    {
                        "role": "user",
                        "content": "Create a vision summary combining current space analysis with design goals"
                    }
                ],
                max_tokens=600
            )
            
            summary = response.choices[0].message.content
            
            return VisionSummaryResponse(
                summary=summary,
                key_elements=[
                    "White shaker-style cabinetry",
                    "Quartz countertops with marble veining",
                    "Matte black hardware and fixtures",
                    "Subway tile backsplash",
                    "Under-cabinet lighting"
                ],
                next_steps=[
                    "Get contractor quotes",
                    "Finalize material selections",
                    "Create project timeline",
                    "Set budget parameters"
                ]
            )
    except Exception as e:
        logger.error(f"Error creating vision summary: {e}")
    
    # Fallback response
    return VisionSummaryResponse(
        summary="""📋 **Your Project Vision Summary**

**Current Space Assessment:**
Your existing space has good bones with functional layout. Key areas for improvement include updating cabinetry, modernizing fixtures, and enhancing lighting.

**Design Direction:**
You're drawn to a modern farmhouse aesthetic with clean lines, bright spaces, and a mix of contemporary and traditional elements.

**Key Transformations:**
• Replace existing cabinetry with white shaker-style doors
• Install quartz countertops with subtle veining
• Add subway tile backsplash with contrasting grout
• Update all hardware to matte black finish
• Enhance lighting with pendant fixtures and under-cabinet LEDs

**Material Palette:**
• Cabinetry: White painted wood
• Countertops: White quartz with gray veining
• Backsplash: 3x6 white subway tile
• Hardware: Matte black pulls and knobs
• Flooring: Maintain existing or update to LVP

This vision will transform your space into a bright, modern, and functional area that matches your style preferences!""",
        key_elements=[
            "Modern farmhouse style",
            "White and black color scheme",
            "Natural textures",
            "Improved lighting",
            "Functional storage"
        ],
        next_steps=[
            "Share with contractors",
            "Get detailed quotes",
            "Select specific products",
            "Plan project phases"
        ]
    )