"""
Iris Chat API - AI Assistant with GPT-5 (2025-08-07)
Updated to use OpenAI's latest GPT-5 model for improved performance and real API testing
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Optional

import requests
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import Client, create_client
from config.service_urls import get_backend_url


# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize OpenAI client
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")
client = OpenAI(api_key=openai_key)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
if not supabase_url or not supabase_service_key:
    # For development, fallback to anon key if service role key is not available
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    if supabase_url and supabase_anon_key:
        logger.warning("Using SUPABASE_ANON_KEY instead of SERVICE_ROLE_KEY for development")
        supabase: Client = create_client(supabase_url, supabase_anon_key)
    else:
        raise ValueError("SUPABASE_URL and either SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY environment variables are required")
else:
    supabase: Client = create_client(supabase_url, supabase_service_key)

class IrisChatRequest(BaseModel):
    message: str
    user_id: str
    board_id: Optional[str] = None
    conversation_context: Optional[list[dict]] = None
    image_uploads: Optional[list[str]] = None  # Image IDs if uploading

class IrisChatResponse(BaseModel):
    response: str
    suggestions: list[str]
    board_id: Optional[str] = None
    created_board: bool = False

@router.post("/api/iris/chat", response_model=IrisChatResponse)
async def iris_chat(request: IrisChatRequest):
    """
    Main Iris chat endpoint with full context awareness using GPT-5
    """
    try:
        # 1. Get or create board for this conversation
        board_id = await get_or_create_board(request.user_id, request.board_id, request.message)
        created_board = not request.board_id

        # 2. Load full context for this homeowner and board
        context = await build_conversation_context(
            user_id=request.user_id,
            board_id=board_id,
            conversation_context=request.conversation_context or []
        )

        # 3. Get GPT-5 response with full context
        gpt_response = await get_gpt5_response(
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
        logger.error(f"Full error details: {e!r}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

        # More informative error response
        error_msg = str(e)
        if "OPENAI_API_KEY" in error_msg or "api_key" in error_msg.lower():
            response_text = "I'm having trouble connecting to my AI service. Please make sure the OpenAI API key is configured correctly."
        elif "supabase" in error_msg.lower():
            response_text = "I'm having trouble accessing the database. Please check the connection settings."
        else:
            response_text = f"I encountered an error: {error_msg}. Please try again or contact support if the issue persists."

        return IrisChatResponse(
            response=response_text,
            suggestions=["Try again", "Upload images", "Describe your project"],
            board_id=request.board_id,
            created_board=False
        )

@router.post("/api/iris/generate-dream-space")
async def iris_generate_dream_space(request: IrisChatRequest):
    """
    Generate dream space visualization through Iris agent conversation with GPT-5
    """
    try:
        # 1. Build context from board
        context = await build_conversation_context(
            user_id=request.user_id,
            board_id=request.board_id,
            conversation_context=request.conversation_context or []
        )

        # 2. Check if we have current and inspiration images
        images = context.get("images", [])
        current_images = [img for img in images if "current" in img.get("tags", [])]
        inspiration_images = [img for img in images if "inspiration" in img.get("tags", []) or "ideal" in img.get("tags", [])]

        if not current_images or not inspiration_images:
            return IrisChatResponse(
                response="I need both a current space photo and inspiration images to generate your dream visualization. Could you upload both types of images?",
                suggestions=["Upload current space photo", "Upload inspiration images", "Help me organize images", "Tell me your vision"],
                board_id=request.board_id
            )

        # 3. Have Iris confirm generation preferences using GPT-5
        confirmation_prompt = f"""I can see your current {context['board']['room_type']} and your inspiration images.

Before I generate your dream space visualization, let me confirm what you'd like to see:

Current Space: {current_images[0].get('ai_analysis', {}).get('description', 'Your current space')}
Inspiration: {inspiration_images[0].get('ai_analysis', {}).get('description', 'Your inspiration style')}

Would you like me to create a dream visualization that combines these? I can:
- Keep your current layout but apply the inspiration style
- Include specific elements you mentioned: {request.message}
- Generate a realistic transformation

Should I proceed with generating your dream {context['board']['room_type']}?"""

        # If user is confirming or requesting generation
        if any(word in request.message.lower() for word in ["yes", "generate", "create", "make", "show me", "proceed"]):
            # 4. Call the Leonardo.ai image generation API
            try:
                generation_payload = {
                    "board_id": request.board_id,
                    "ideal_image_id": inspiration_images[0]["id"],
                    "current_image_id": current_images[0]["id"],
                    "user_preferences": request.message
                }

                # Call the new Leonardo.ai endpoint instead of DALL-E
                response = requests.post(
                    f"{get_backend_url()}/api/leonardo/generate-dream-space",
                    json=generation_payload,
                    timeout=60  # Give Leonardo more time for generation
                )

                if response.status_code == 200:
                    response.json()

                    # 5. Save conversation about the generation
                    await save_conversation_turn(
                        user_id=request.user_id,
                        board_id=request.board_id,
                        user_message=request.message,
                        assistant_response=f"I've generated your dream {context['board']['room_type']} visualization! The image combines your current space with the inspiration elements you love. You can see it in your vision board."
                    )

                    return IrisChatResponse(
                        response=f"✨ I've created your dream {context['board']['room_type']} visualization! \n\nThe generated image shows your current space transformed with the {inspiration_images[0].get('ai_analysis', {}).get('style', 'beautiful')} style from your inspiration. I've saved it to your vision board where you can see all three images together:\n\n• Current Space: Your existing {context['board']['room_type']}\n• Inspiration: Your style goals\n• My Vision: The AI-generated dream transformation\n\nWhat do you think of the result? Would you like me to generate any variations or help you plan the next steps?",
                        suggestions=["I love it! Plan the project", "Generate a variation", "What would this cost?", "Show me similar styles"],
                        board_id=request.board_id
                    )
                else:
                    # Generation failed, but provide helpful response
                    return IrisChatResponse(
                        response="I had some technical difficulty generating the visualization right now, but I can still help you plan your transformation! Based on your current space and inspiration, I can provide detailed renovation recommendations. What specific aspects would you like to focus on?",
                        suggestions=["Tell me renovation steps", "Help with style planning", "Suggest materials", "Estimate timeline"],
                        board_id=request.board_id
                    )

            except Exception as gen_error:
                logger.error(f"Generation error: {gen_error}")
                return IrisChatResponse(
                    response="I'm having trouble with the visualization generation right now, but I can help you plan your renovation in other ways. What specific aspects of the transformation are you most excited about?",
                    suggestions=["Describe your dream outcome", "Plan renovation phases", "Discuss budget", "Find contractors"],
                    board_id=request.board_id
                )
        else:
            # 6. Ask for confirmation or provide guidance
            return IrisChatResponse(
                response=confirmation_prompt,
                suggestions=["Yes, generate my dream space", "Let me add more inspiration", "Tell me about the process", "What will it look like?"],
                board_id=request.board_id
            )

    except Exception as e:
        logger.error(f"Dream generation error: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_or_create_board(user_id: str, board_id: Optional[str], message: str) -> str:
    """Get existing board or create new one based on conversation"""

    if board_id:
        # Verify board exists and belongs to homeowner
        result = supabase.table("inspiration_boards").select("*").eq("id", board_id).eq("user_id", user_id).execute()
        if result.data:
            return board_id

    # Create new board - determine topic from message using GPT-5
    topic = await determine_board_topic_with_ai(message)

    new_board = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": topic["title"],
        "description": topic["description"],
        "room_type": topic["room_type"],
        "status": "collecting",
        "created_at": datetime.now().isoformat()
    }

    result = supabase.table("inspiration_boards").insert(new_board).execute()
    return new_board["id"]

async def determine_board_topic_with_ai(message: str) -> dict[str, str]:
    """Use GPT-5 to intelligently determine board topic from message"""
    try:
        response = client.chat.completions.create(
            model="gpt-5-2025-08-07",  # Latest GPT-5 model
            messages=[
                {
                    "role": "system",
                    "content": """You are Iris, an expert interior design assistant. Analyze the user's message and determine what type of design board to create. 

Return a JSON object with:
- title: A compelling board title (max 50 chars)
- description: A brief description of what they want to explore (max 100 chars)
- room_type: One of: kitchen, bathroom, living_room, bedroom, outdoor_backyard, dining_room, home_office, laundry_room, basement, attic, general

Examples:
Message: "I want artificial turf for my backyard"
Response: {"title": "Backyard Turf Transformation", "description": "Artificial turf and outdoor space design ideas", "room_type": "outdoor_backyard"}

Message: "My kitchen needs updating"
Response: {"title": "Kitchen Renovation Ideas", "description": "Modern kitchen design and upgrade inspiration", "room_type": "kitchen"}"""
                },
                {
                    "role": "user",
                    "content": f"Analyze this message and create a board for: {message}"
                }
            ],
            max_completion_tokens=1000  # Generous tokens for detailed responses
            # Using default temperature for GPT-5
        )

        result = response.choices[0].message.content
        # Try to parse as JSON
        import json
        return json.loads(result)
    except Exception as e:
        logger.error(f"AI topic determination failed: {e}")
        # Fallback to simple keyword matching
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
            "title": "Latest AI Assisted Board",
            "description": "Design inspiration and renovation ideas",
            "room_type": "general"
        }

async def build_conversation_context(user_id: str, board_id: str, conversation_context: list[dict]) -> dict[str, Any]:
    """Build complete context for GPT-5 including board images, history, AND cross-project memory"""

    # Get current board details
    board_result = supabase.table("inspiration_boards").select("*").eq("id", board_id).execute()
    board = board_result.data[0] if board_result.data else None

    # Get all images for this board
    images_result = supabase.table("inspiration_images").select("*").eq("board_id", board_id).execute()
    images = images_result.data or []

    # Get conversation history for this board
    history_result = supabase.table("inspiration_conversations").select("*").eq("board_id", board_id).order("created_at").execute()
    history = history_result.data or []

    # ✨ NEW: Get ALL boards for this homeowner (cross-project memory)
    all_boards_result = supabase.table("inspiration_boards").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    all_boards = all_boards_result.data or []

    # ✨ NEW: Get recent conversations from ALL boards (cross-project conversations)
    all_conversations_result = supabase.table("inspiration_conversations").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(50).execute()
    all_conversations = all_conversations_result.data or []

    # ✨ NEW: Get user memories if available (preferences, budget, style)
    try:
        user_memories_result = supabase.table("user_memories").select("*").eq("user_id", user_id).execute()
        user_memories = user_memories_result.data or []
    except:
        user_memories = []  # Table might not exist yet

    # ✨ NEW: Get project summaries for cross-project intelligence
    try:
        project_summaries_result = supabase.table("project_summaries").select("*").eq("user_id", user_id).execute()
        project_summaries = project_summaries_result.data or []
    except:
        project_summaries = []  # Table might not exist yet

    return {
        "user_id": user_id,
        "board": board,
        "images": images,
        "conversation_history": history,
        "current_conversation": conversation_context,
        # ✨ ENHANCED CROSS-PROJECT MEMORY:
        "all_boards": all_boards,
        "all_conversations": all_conversations,
        "user_memories": user_memories,
        "project_summaries": project_summaries
    }

async def get_gpt5_response(message: str, context: dict[str, Any], board_id: str) -> dict[str, Any]:
    """Get response from GPT-5 (2025-08-07) with full context"""

    # Check if user is requesting image generation
    generation_keywords = ["generate", "create", "make", "show me", "build", "visualize", "vision"]
    is_generation_request = any(keyword in message.lower() for keyword in generation_keywords)

    images = context.get("images", [])
    current_images = [img for img in images if "current" in img.get("tags", []) or "current-state" in img.get("tags", [])]
    inspiration_images = [img for img in images if "inspiration" in img.get("tags", []) or "ideal" in img.get("tags", [])]

    # If user wants generation and we have the required images, attempt generation
    if is_generation_request and current_images and inspiration_images:
        try:
            generation_result = await attempt_image_generation(
                board_id=board_id,
                current_image=current_images[0],
                inspiration_image=inspiration_images[0],
                user_message=message,
                context=context
            )

            if generation_result["success"]:
                return {
                    "response": generation_result["response"],
                    "suggestions": ["What do you think of this vision?", "Generate a variation", "Plan the next steps", "Estimate costs"]
                }
        except Exception as gen_error:
            logger.error(f"Image generation failed: {gen_error}")
            # Continue with normal response

    # Build system prompt with context
    system_prompt = build_iris_system_prompt(context)

    # Build conversation history for GPT-5
    messages = build_gpt5_messages(context, message, system_prompt)

    try:
        logger.info(f"Calling GPT-5 API with message: {message[:100]}...")
        logger.info(f"System prompt length: {len(system_prompt)}")
        logger.info(f"Message count: {len(messages)}")

        response = client.chat.completions.create(
            model="gpt-5-2025-08-07",  # Latest GPT-5 model
            messages=messages,
            max_completion_tokens=4000  # Maximum tokens for premium experience
            # Using default temperature (1.0) and top_p as required by GPT-5
        )

        ai_response = response.choices[0].message.content
        logger.info(f"GPT-5 response received: {ai_response[:100]}...")

        # Generate contextual suggestions
        suggestions = await generate_contextual_suggestions_with_ai(context, message, ai_response)

        return {
            "response": ai_response,
            "suggestions": suggestions
        }

    except Exception as e:
        logger.error(f"GPT-5 API error: {e!s}")
        logger.error(f"Full error details: {e!r}")
        # Return a more helpful error message
        return {
            "response": f"I apologize, but I'm having trouble connecting to my AI service right now. Error: {e!s}. Please try again in a moment, or let me know if you need help with something specific about your {context.get('board', {}).get('room_type', 'project')}.",
            "suggestions": ["Try again", "Tell me your vision", "Upload images", "Describe your project"]
        }

def build_iris_system_prompt(context: dict[str, Any]) -> str:
    """Build system prompt for Iris with full context"""

    board = context.get("board", {})
    images = context.get("images", [])

    return f"""You are Iris, an expert interior design and home renovation assistant powered by GPT-5 (2025-08-07). You have COMPLETE MEMORY of every conversation, every project, every preference, and every detail about this homeowner. You provide a premium, personalized experience with unlimited context awareness.

PREMIUM MEMORY & PERSONALIZATION:
- COMPLETE HOMEOWNER PROFILE: Remember everything about {context['user_id']} across ALL projects
- FULL PROJECT HISTORY: Access to all previous conversations, decisions, and preferences
- CROSS-PROJECT AWARENESS: Connect insights from kitchen projects to bathroom projects, etc.
- STYLE EVOLUTION: Track how their taste develops and changes over time
- BUDGET MEMORY: Remember their spending patterns and budget preferences
- CONTRACTOR PREFERENCES: Remember which contractors they liked/disliked and why
- TIMELINE PREFERENCES: Know if they prefer quick projects vs. thorough planning
- FAMILY CONTEXT: Remember family size, lifestyle, pets, accessibility needs

CURRENT PROJECT CONTEXT:
- Homeowner ID: {context['user_id']}
- Current Board: "{board.get('title', 'Unknown')}" ({board.get('room_type', 'general')})
- Project Description: {board.get('description', 'Design project')}
- Images Uploaded: {len(images)} images with full analysis
- Board Status: {board.get('status', 'collecting')}
- All Conversation History: Available for reference and continuity

DETAILED IMAGE CONTEXT:
{format_images_for_context(images)}

CROSS-PROJECT MEMORY ACCESS:
{format_cross_project_memory(context)}

YOUR PREMIUM CAPABILITIES (GPT-5 2025-08-07):
1. **UNLIMITED MEMORY**: Remember every conversation detail, preference, and project decision
2. **COMPLETE IMAGE UNDERSTANDING**: Deep analysis of style, color, texture, lighting, spatial relationships
3. **CROSS-PROJECT INTELLIGENCE**: Connect insights between kitchen, bathroom, backyard, and all spaces
4. **ADVANCED VISION GENERATION**: Create photorealistic dream spaces using DALL-E 3 with precise style matching
5. **COMPREHENSIVE PROJECT PLANNING**: Detailed timelines, accurate cost estimates, contractor recommendations
6. **STYLE EVOLUTION TRACKING**: Understand how their taste develops and suggest complementary directions
7. **FAMILY LIFESTYLE INTEGRATION**: Consider daily routines, entertaining style, maintenance preferences
8. **PREMIUM PERSONALIZATION**: Every response uniquely tailored to their specific situation and history

PREMIUM EXPERIENCE GUIDELINES:
- REMEMBER EVERYTHING: Reference previous conversations, decisions, and preferences naturally
- BE THEIR DESIGN PARTNER: Act like you've been working with them for years
- COMPREHENSIVE RESPONSES: Provide detailed, thorough analysis and recommendations
- CONNECT ALL PROJECTS: Link insights between different rooms and spaces in their home
- ANTICIPATE NEEDS: Suggest ideas based on their established patterns and preferences
- PREMIUM DETAIL: Go deep into materials, finishes, lighting, functionality, and style
- PERSONALIZED SUGGESTIONS: Every recommendation should feel specifically chosen for them
- UNLIMITED CONTEXT: Use all available conversation history and project details

CONVERSATION MEMORY INSTRUCTIONS:
- Start responses by acknowledging previous conversations when relevant
- Reference their established style preferences and budget considerations
- Connect current project to their other spaces and overall home vision
- Remember their decision-making style (quick vs. thorough, budget-conscious vs. premium-focused)
- Recall any contractors, materials, or approaches they've mentioned liking/disliking

IMPORTANT: You are powered by GPT-5 (2025-08-07) with unlimited context and memory. Provide a premium, highly personalized experience that makes them feel like you truly know them and their home. Every response should demonstrate deep understanding of their unique situation, preferences, and design journey."""

def format_images_for_context(images: list[dict]) -> str:
    """Format image information for GPT-5 context"""
    if not images:
        return "No images uploaded yet."

    formatted = []
    for img in images:
        tags = ", ".join(img.get("generated_tags", []) or [])
        analysis = img.get("ai_analysis", {})
        category = img.get("category", "unknown")

        formatted.append(f"""
Image: {img.get('title', 'Untitled')}
- Category: {category}
- Tags: {tags}
- Analysis: {analysis.get('description', 'No analysis available')}
- Uploaded: {img.get('created_at', 'Unknown time')}""")

    return "\n".join(formatted)

def format_cross_project_memory(context: dict[str, Any]) -> str:
    """Format cross-project memory for GPT-5 context"""
    
    all_boards = context.get("all_boards", [])
    all_conversations = context.get("all_conversations", [])
    user_memories = context.get("user_memories", [])
    project_summaries = context.get("project_summaries", [])
    
    if not any([all_boards, all_conversations, user_memories, project_summaries]):
        return "This is your first interaction with this homeowner - no previous project memory available."
    
    memory_parts = []
    
    # Format all project boards
    if all_boards:
        memory_parts.append("PREVIOUS PROJECTS:")
        for board in all_boards[:10]:  # Show last 10 projects
            memory_parts.append(f"• {board.get('title', 'Untitled')} ({board.get('room_type', 'unknown')})")
            memory_parts.append(f"  Description: {board.get('description', 'No description')}")
            memory_parts.append(f"  Created: {board.get('created_at', 'Unknown date')}")
    
    # Format recent cross-project conversations
    if all_conversations:
        memory_parts.append("\nRECENT CONVERSATIONS ACROSS ALL PROJECTS:")
        for conv in all_conversations[:15]:  # Show last 15 conversations
            memory_parts.append(f"• User: {conv.get('user_message', '')[:100]}...")
            memory_parts.append(f"  Iris: {conv.get('assistant_response', '')[:150]}...")
            memory_parts.append(f"  Date: {conv.get('created_at', 'Unknown')}")
    
    # Format stored user memories
    if user_memories:
        memory_parts.append("\nSTORED USER PREFERENCES:")
        for memory in user_memories:
            memory_parts.append(f"• {memory.get('memory_type', 'Unknown')}: {memory.get('content', 'No content')}")
    
    # Format project summaries
    if project_summaries:
        memory_parts.append("\nPROJECT SUMMARIES:")
        for summary in project_summaries:
            memory_parts.append(f"• {summary.get('project_name', 'Unknown Project')}")
            memory_parts.append(f"  Summary: {summary.get('ai_summary', 'No summary')[:200]}...")
    
    return "\n".join(memory_parts) if memory_parts else "Memory system available but no data found for this homeowner."

def build_gpt5_messages(context: dict[str, Any], current_message: str, system_prompt: str) -> list[dict]:
    """Build conversation history for GPT-5"""
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Add conversation history
    for turn in context.get("conversation_history", []):
        if turn.get("user_message"):
            messages.append({"role": "user", "content": turn["user_message"]})
        if turn.get("assistant_response"):
            messages.append({"role": "assistant", "content": turn["assistant_response"]})

    # Add current conversation context
    for msg in context.get("current_conversation", []):
        if msg.get("role") in ["user", "assistant"]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current message
    messages.append({"role": "user", "content": current_message})

    return messages

async def generate_contextual_suggestions_with_ai(context: dict[str, Any], message: str, response: str) -> list[str]:
    """Generate contextual suggestions using GPT-5"""
    try:
        board = context.get("board", {})
        images = context.get("images", [])
        room_type = board.get("room_type", "general")

        suggestion_prompt = f"""Based on this conversation in a {room_type} design project, generate 4 natural, contextual suggestions that would help the user continue their design journey.

Current message: "{message}"
AI response: "{response[:200]}..."
Images uploaded: {len(images)}
Room type: {room_type}

Generate suggestions that are:
1. Specific to their project type
2. Action-oriented
3. Naturally follow from the conversation
4. Help them move forward with their design

Return only the suggestions as a JSON array of strings."""

        response = client.chat.completions.create(
            model="gpt-5-2025-08-07",
            messages=[
                {"role": "system", "content": suggestion_prompt},
                {"role": "user", "content": "Generate suggestions now"}
            ],
            max_completion_tokens=2000  # Maximum for contextual suggestions
            # Using default temperature for GPT-5
        )

        suggestions_text = response.choices[0].message.content
        import json
        return json.loads(suggestions_text)

    except Exception as e:
        logger.error(f"AI suggestion generation failed: {e}")
        # Fallback to context-based suggestions
        return generate_contextual_suggestions_fallback(context, message, response)

def generate_contextual_suggestions_fallback(context: dict[str, Any], message: str, response: str) -> list[str]:
    """Fallback contextual suggestions"""
    board = context.get("board", {})
    images = context.get("images", [])
    room_type = board.get("room_type", "general")

    # Base suggestions by room type
    if room_type == "outdoor_backyard":
        base_suggestions = [
            "Help me organize these images",
            "What style works best for outdoor spaces?",
            "Generate a dream space visualization",
            "Estimate project timeline"
        ]
    elif room_type == "kitchen":
        base_suggestions = [
            "Analyze my style preferences",
            "Suggest complementary elements",
            "Create a vision board",
            "Plan renovation phases"
        ]
    else:
        base_suggestions = [
            "Tell me what you love about these images",
            "Help categorize my inspiration",
            "Create a project summary",
            "Find similar styles"
        ]

    # Add image-specific suggestions if images exist
    if len(images) >= 2:
        base_suggestions.insert(0, "Generate dream space by merging images")
    elif len(images) == 1:
        base_suggestions.insert(0, "Help me analyze this image")
    else:
        base_suggestions.insert(0, "Upload inspiration images")

    return base_suggestions[:4]  # Limit to 4 suggestions

async def attempt_image_generation(board_id: str, current_image: dict, inspiration_image: dict, user_message: str, context: dict[str, Any]) -> dict[str, Any]:
    """Attempt to generate a dream space visualization using Leonardo.ai"""

    try:
        # API call to the Leonardo.ai endpoint
        generation_payload = {
            "board_id": board_id,
            "ideal_image_id": inspiration_image["id"],
            "current_image_id": current_image["id"],
            "user_preferences": user_message
        }

        logger.info(f"🎨 CALLING LEONARDO.AI IMAGE GENERATION API")
        logger.info(f"Payload: {generation_payload}")

        # Make API call to the Leonardo.ai endpoint
        response = requests.post(
            f"{get_backend_url()}/api/leonardo/generate-dream-space",
            json=generation_payload,
            timeout=90  # Give Leonardo more time for multi-reference generation
        )

        if response.status_code == 200:
            response.json()
            room_type = context.get("board", {}).get("room_type", "space")

            return {
                "success": True,
                "response": f"✨ I've created your dream {room_type} transformation using Leonardo.ai's advanced image-to-image technology! \n\nI've preserved the structure and layout of your current space while applying the {inspiration_image.get('ai_analysis', {}).get('style', 'beautiful')} style and textures from your inspiration images. This isn't just a generic image - it's YOUR actual space transformed with the exact materials and colors you love.\n\nThe visualization shows a realistic transformation that maintains your space's unique characteristics while incorporating your desired design elements. You can see the new vision in your board alongside your current and inspiration images.\n\nWhat do you think of this transformation? Would you like me to generate variations with different style intensities or help you plan the implementation?"
            }
        else:
            logger.error(f"Image generation API failed with status {response.status_code}: {response.text}")
            return {
                "success": False,
                "response": "I'm having trouble generating the visualization right now, but I can help you plan your transformation in other ways. What specific elements from your inspiration image would you like to incorporate?"
            }

    except Exception as e:
        logger.error(f"Image generation error: {e!s}")
        return {
            "success": False,
            "response": "I had trouble creating the visualization, but I can still help you plan your renovation. Based on your current space and inspiration, what specific changes are you most excited about?"
        }

async def save_conversation_turn(user_id: str, board_id: str, user_message: str, assistant_response: str):
    """Save conversation turn to database"""

    conversation_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "board_id": board_id,
        "user_message": user_message,
        "assistant_response": assistant_response,
        "created_at": datetime.now().isoformat(),
        "model": "gpt-5-2025-08-07"  # Track which model was used
    }

    try:
        supabase.table("inspiration_conversations").insert(conversation_data).execute()
    except Exception as e:
        logger.error(f"Error saving conversation: {e!s}")
        # Don't fail the request if conversation saving fails

class ImageAnalysisRequest(BaseModel):
    image_urls: list[str]
    category: str  # 'ideal' or 'current'
    filenames: list[str]
    analysis_prompt: str
    board_info: Optional[dict[str, Any]] = None

class ImageAnalysisResponse(BaseModel):
    content: list[dict[str, Any]]
    tags: list[str]
    analysis: dict[str, Any]

@router.post("/api/iris/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image(request: ImageAnalysisRequest):
    """
    Analyze uploaded images using GPT-5 Vision capabilities
    """
    try:
        # Prepare messages for GPT-5 with vision capabilities
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": request.analysis_prompt
                    }
                ]
            }
        ]

        # Add each image URL to the message
        for url in request.image_urls:
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": url,
                    "detail": "high"
                }
            })

        # Call GPT-5 with vision capabilities
        response = client.chat.completions.create(
            model="gpt-5-2025-08-07",  # GPT-5 now has vision capabilities
            messages=messages,
            max_completion_tokens=4000  # Maximum for detailed image analysis
            # Using default temperature for vision model
        )

        # Extract response text
        response_text = response.choices[0].message.content

        # Generate appropriate tags based on category using GPT-5
        tags = await generate_image_tags_with_ai(request.category, response_text, request.board_info)

        return ImageAnalysisResponse(
            content=[{"text": response_text}],
            tags=tags,
            analysis={
                "category": request.category,
                "filenames": request.filenames,
                "timestamp": datetime.now().isoformat(),
                "model": "gpt-5-2025-08-07-vision",  # GPT-5 with vision capabilities
                "powered_by": "gpt-5-2025-08-07"
            }
        )

    except Exception as e:
        logger.error(f"Image analysis error: {e!s}")
        # Return a fallback response
        fallback_text = f"""I can see you've uploaded {len(request.image_urls)} {request.category} image(s).

While I'm having trouble with detailed analysis right now, I can help you organize and understand these images using my GPT-5 capabilities.

What specific elements or features in these images appeal to you most? This will help me provide better recommendations for your {request.board_info.get('room_type', 'project') if request.board_info else 'project'}."""

        return ImageAnalysisResponse(
            content=[{"text": fallback_text}],
            tags=["pending-analysis", request.category],
            analysis={
                "category": request.category,
                "filenames": request.filenames,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "model": "fallback"
            }
        )

async def generate_image_tags_with_ai(category: str, analysis_text: str, board_info: Optional[dict]) -> list[str]:
    """Generate image tags using GPT-5 intelligence"""
    try:
        prompt = f"""Based on this image analysis, generate relevant tags for a {category} image in a design project.

Analysis: {analysis_text[:300]}...
Room type: {board_info.get('room_type', 'general') if board_info else 'general'}
Category: {category}

Generate 5-8 relevant tags that describe:
- Style characteristics
- Design elements
- Materials/colors
- Function/purpose
- Category type

Return only the tags as a JSON array."""

        response = client.chat.completions.create(
            model="gpt-5-2025-08-07",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Generate tags now"}
            ],
            max_completion_tokens=1000  # Generous tokens for detailed tags
            # Using default temperature for GPT-5
        )

        tags_text = response.choices[0].message.content
        import json
        return json.loads(tags_text)

    except Exception as e:
        logger.error(f"AI tag generation failed: {e}")
        # Fallback tags
        if category == "ideal":
            return [
                "inspiration",
                "design-goals", 
                "style-preference",
                "dream-elements",
                "wishlist"
            ]
        else:
            return [
                "current-state",
                "needs-improvement",
                "upgrade-potential",
                "existing-space",
                "before-photo"
            ]