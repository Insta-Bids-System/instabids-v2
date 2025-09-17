"""
IRIS Agent - Unified Conversation System Integration
Design Inspiration Assistant migrated to unified conversation architecture
"""

import logging
import os
import uuid
import requests
from datetime import datetime
from typing import Any, Optional

from openai import OpenAI
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
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
    logger.warning("OPENAI_API_KEY not found, using fallback responses")
    client = None
else:
    try:
        client = OpenAI(api_key=openai_key)
        # Test the API key with a quick request
        test_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
            max_completion_tokens=1  # Fixed: GPT-4o uses max_completion_tokens
        )
        logger.info("OpenAI API key validated successfully")
    except Exception as e:
        logger.warning(f"OpenAI API key invalid or service unavailable: {e}")
        logger.warning("Using fallback responses instead")
        client = None

# Unified conversation API base URL
UNIFIED_API_BASE = get_backend_url()

class IrisChatRequest(BaseModel):
    message: str
    user_id: str
    board_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_context: Optional[list[dict]] = None
    room_type: Optional[str] = None

class IrisChatResponse(BaseModel):
    response: str
    suggestions: list[str]
    session_id: str
    board_id: Optional[str] = None
    conversation_id: Optional[str] = None

@router.post("/chat", response_model=IrisChatResponse)
async def iris_unified_chat(request: IrisChatRequest):
    """
    IRIS chat using unified conversation system
    """
    try:
        # Generate or use session ID
        session_id = request.session_id or f"iris_{request.user_id}_{int(datetime.now().timestamp())}"
        
        # 1. Create or get conversation in unified system
        conversation_id = await create_or_get_conversation(
            user_id=request.user_id,
            session_id=session_id,
            room_type=request.room_type or "general",
            message=request.message
        )
        
        # 2. Get conversation context from unified system
        context = await get_unified_conversation_context(conversation_id)
        
        # 3. Generate IRIS response using GPT-5 with GPT-4o fallback
        iris_response = await generate_iris_response(
            message=request.message,
            context=context,
            conversation_id=conversation_id
        )
        
        # 4. Save message to unified conversation system
        await save_message_to_unified_system(
            conversation_id=conversation_id,
            user_message=request.message,
            assistant_response=iris_response["response"],
            user_id=request.user_id
        )
        
        return IrisChatResponse(
            response=iris_response["response"],
            suggestions=iris_response["suggestions"],
            session_id=session_id,
            conversation_id=conversation_id,
            board_id=request.board_id
        )
        
    except Exception as e:
        logger.error(f"Error in IRIS unified chat: {e}")
        return IrisChatResponse(
            response="I'm here to help you with your design inspiration! Tell me about your project - what room are you working on?",
            suggestions=["Tell me about my current space", "Help me find inspiration", "Explore design styles", "Organize my project ideas"],
            session_id=request.session_id or f"iris_fallback_{int(datetime.now().timestamp())}",
            board_id=request.board_id
        )

async def create_or_get_conversation(user_id: str, session_id: str, room_type: str, message: str) -> str:
    """Create or get existing conversation in unified system"""
    try:
        # Determine project title from message and room type
        project_title = determine_project_title(message, room_type)
        
        # Use HTTP request to unified conversation API (correct path without /api prefix)
        conversation_request = {
            "user_id": user_id,
            "agent_type": "IRIS",
            "title": project_title,
            "context_type": "design_inspiration",
            "metadata": {
                "session_id": session_id,
                "room_type": room_type,
                "design_phase": "inspiration"
            }
        }
        
        # Make HTTP request to create conversation
        response = requests.post(
            f"{get_backend_url()}/conversations/create",
            json=conversation_request,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Created unified conversation: {result.get('conversation_id')}")
            return result.get('conversation_id', str(uuid.uuid4()))
        else:
            logger.error(f"Failed to create conversation: {response.status_code} - {response.text}")
            return str(uuid.uuid4())
            
    except Exception as e:
        logger.error(f"Error creating unified conversation: {e}")
        return str(uuid.uuid4())

def determine_project_title(message: str, room_type: str) -> str:
    """Determine project title from message and room type"""
    message_lower = message.lower()
    
    # Room-specific titles
    if room_type == "kitchen":
        if any(word in message_lower for word in ["modern", "farmhouse", "contemporary"]):
            style = next(word for word in ["modern", "farmhouse", "contemporary"] if word in message_lower)
            return f"{style.title()} Kitchen Design"
        return "Kitchen Design Project"
    elif room_type == "bathroom":
        return "Bathroom Renovation Ideas"
    elif room_type == "living_room":
        return "Living Room Design"
    elif room_type == "bedroom":
        return "Bedroom Makeover"
    elif room_type == "outdoor_backyard":
        return "Backyard Transformation"
    else:
        # Extract key words for general title
        if any(word in message_lower for word in ["modern", "contemporary"]):
            return "Modern Design Project"
        elif any(word in message_lower for word in ["farmhouse", "rustic"]):
            return "Farmhouse Style Project"
        elif any(word in message_lower for word in ["traditional", "classic"]):
            return "Traditional Design Project"
        else:
            return "Home Design Inspiration"

async def get_unified_conversation_context(conversation_id: str) -> dict:
    """Get conversation context from unified system"""
    try:
        # Use HTTP request to get conversation
        response = requests.get(
            f"{get_backend_url()}/conversations/{conversation_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "conversation": result.get("conversation", {}),
                "messages": result.get("messages", []),
                "memory": result.get("memory", []),
                "participants": result.get("participants", [])
            }
        else:
            logger.error(f"Failed to get conversation: {response.status_code}")
            return {"conversation": {}, "messages": [], "memory": [], "participants": []}
            
    except Exception as e:
        logger.error(f"Error getting unified conversation context: {e}")
        return {"conversation": {}, "messages": [], "memory": [], "participants": []}

async def generate_iris_response(message: str, context: dict, conversation_id: str) -> dict:
    """Generate IRIS response using GPT-5 with GPT-4o fallback"""
    
    if not client:
        return generate_fallback_iris_response(message, context)
    
    # Build IRIS system prompt
    system_prompt = build_iris_system_prompt(context)
    
    # Build message history
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add previous messages from unified system
    for msg in context.get("messages", [])[-10:]:  # Last 10 messages
        role = "user" if msg.get("sender_type") == "user" else "assistant"
        messages.append({"role": role, "content": msg.get("content", "")})
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    # Try GPT-5 first, fallback to GPT-4o
    try:
        # Try GPT-5 with timeout
        try:
            logger.info("Attempting GPT-5 for IRIS response...")
            response = client.chat.completions.create(
                model="gpt-5",
                messages=messages,
                max_completion_tokens=1500,  # Fixed: GPT-5 uses max_completion_tokens
                temperature=0.7,
                extra_body={
                    "reasoning_effort": "medium",
                    "verbosity": "default"
                }
            )
            logger.info("✅ GPT-5 response successful")
            
        except Exception as gpt5_error:
            logger.warning(f"GPT-5 failed: {gpt5_error}, falling back to GPT-4o")
            # Fallback to GPT-4o
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_completion_tokens=1500,  # Fixed: GPT-4o uses max_completion_tokens
                    temperature=0.7
                )
                logger.info("✅ GPT-4o fallback successful")
            except Exception as gpt4_error:
                logger.warning(f"GPT-4o also failed: {gpt4_error}, using static fallback")
                return generate_fallback_iris_response(message, context)
        
        ai_response = response.choices[0].message.content
        
        # Store design preferences in unified memory system
        await store_design_preferences_memory(conversation_id, message, ai_response, context)
        
        # Generate contextual suggestions
        suggestions = generate_iris_suggestions(context, message, ai_response)
        
        return {
            "response": ai_response,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Both GPT models failed: {e}")
        return generate_fallback_iris_response(message, context)

def build_iris_system_prompt(context: dict) -> str:
    """Build IRIS system prompt with conversation context"""
    
    conversation = context.get("conversation", {})
    messages = context.get("messages", [])
    memory = context.get("memory", [])
    
    room_type = conversation.get("metadata", {}).get("room_type", "general")
    design_phase = conversation.get("metadata", {}).get("design_phase", "inspiration")
    
    # Get project memory if available
    project_memory = ""
    for mem in memory:
        if mem.get("memory_type") == "project_context":
            project_memory += f"\\n- {mem.get('memory_key')}: {mem.get('memory_value', '')}"
    
    return f"""You are Iris, an expert interior design assistant specializing in inspiration discovery and project organization for InstaBids.

CURRENT PROJECT CONTEXT:
- Room Type: {room_type}
- Design Phase: {design_phase} 
- Messages in conversation: {len(messages)}
- Project Title: {conversation.get('title', 'Design Project')}
{project_memory}

YOUR EXPERTISE:
• Help homeowners discover and organize their design inspiration
• Analyze current spaces and articulate ideal visions  
• Guide through style discovery (modern, farmhouse, traditional, etc.)
• Extract specific elements from inspiration images
• Create actionable project requirements for contractors
• Budget-conscious and realistic advice

YOUR PERSONALITY:
- Warm, encouraging, and genuinely helpful
- Expert knowledge but approachable explanations
- Asks thoughtful questions to understand preferences
- Focuses on what makes spaces feel like "home"
- Practical about budgets and timelines

CONVERSATION APPROACH:
1. **Understand Current Space**: What they have now, what works, what doesn't
2. **Explore Ideal Vision**: Style preferences, inspiration, dream elements
3. **Identify Specific Elements**: Colors, materials, layouts, features
4. **Organize & Prioritize**: Must-haves vs nice-to-haves, budget considerations
5. **Create Actionable Plan**: Clear requirements for contractors

IMPORTANT NOTES:
• You do NOT generate images - you help them find, organize, and understand inspiration
• Focus on helping them articulate their vision clearly
• Ask specific questions about functionality and lifestyle needs
• Help them prepare comprehensive project briefs for contractors
• Always be encouraging about their vision while keeping expectations realistic

Current conversation context: {len(messages)} previous messages exchanged."""

def generate_iris_suggestions(context: dict, message: str, response: str) -> list[str]:
    """Generate contextual suggestions for IRIS conversation"""
    
    conversation = context.get("conversation", {})
    messages = context.get("messages", [])
    room_type = conversation.get("metadata", {}).get("room_type", "general")
    message_lower = message.lower()
    
    # Suggestions based on conversation stage
    if len(messages) < 2:  # Early conversation
        return [
            "Tell me about my current space",
            "Help me explore design styles",
            "What's my ideal vision?",
            "How do I organize my ideas?"
        ]
    elif any(word in message_lower for word in ["current", "existing", "have now"]):
        return [
            "What needs to change most?",
            "Show me ideal inspirations",
            "Help me prioritize improvements",
            "Estimate my project budget"
        ]
    elif any(word in message_lower for word in ["style", "inspiration", "love", "want"]):
        return [
            "Find similar design examples",
            "Help me organize my inspiration",
            "What's my color palette?",
            "Create project summary"
        ]
    elif any(word in message_lower for word in ["budget", "cost", "price"]):
        return [
            "Show budget breakdown",
            "Prioritize improvements",
            "Find cost-effective options",
            "Compare material choices"
        ]
    elif "ready" in message_lower or "start" in message_lower:
        return [
            "Create contractor brief",
            "Finalize project requirements", 
            "Connect with CIA agent",
            "Review project timeline"
        ]
    else:
        # Default suggestions based on room type
        if room_type == "kitchen":
            return [
                "Help me choose cabinet styles",
                "Explore countertop options",
                "Find backsplash inspiration", 
                "Plan my layout improvements"
            ]
        elif room_type == "bathroom":
            return [
                "Explore tile combinations",
                "Choose fixture finishes",
                "Plan storage solutions",
                "Find lighting ideas"
            ]
        else:
            return [
                "Help me refine my style",
                "Organize my inspiration",
                "Create project priorities",
                "Find more examples"
            ]

def generate_fallback_iris_response(message: str, context: dict) -> dict:
    """Generate fallback IRIS response when AI is unavailable"""
    
    conversation = context.get("conversation", {})
    messages = context.get("messages", [])
    room_type = conversation.get("metadata", {}).get("room_type", "general")
    message_lower = message.lower()
    
    # Room-specific responses
    if room_type == "kitchen" and any(word in message_lower for word in ["modern", "farmhouse", "style"]):
        response = f"""I love that you're exploring {room_type} styles! Let me help you understand what draws you to different design approaches:

**Modern Farmhouse Elements:**
• White or light-colored shaker cabinets
• Black or dark hardware for contrast
• Natural wood accents and textures
• Subway tile or shiplap backsplashes
• Farmhouse sinks with vintage-style faucets

**What specifically appeals to you?** Is it the color palette, the mixed materials, or the cozy-meets-clean aesthetic?

Understanding your preferences helps me guide you toward the perfect vision for your space!"""
        
        suggestions = [
            "I love the white and black contrast",
            "The mixed materials appeal to me", 
            "I want that cozy but clean feeling",
            "Help me find similar examples"
        ]
    
    elif any(word in message_lower for word in ["current", "existing", "space", "now"]):
        response = f"""I'd love to help you understand your current {room_type}! To give you the best guidance, tell me:

**About Your Current Space:**
• What do you like about how it functions now?
• What frustrates you or feels outdated?
• How do you use this space daily?
• What would you change if you could?

**Your Lifestyle Needs:**
• Who uses this space regularly?
• What activities happen here?
• Any special storage or functional requirements?

Understanding your current situation helps me suggest improvements that truly enhance your daily life!"""
        
        suggestions = [
            "Describe what I like about it",
            "Explain what frustrates me",
            "Tell you how I use the space",
            "Share my biggest wish list"
        ]
    
    elif any(word in message_lower for word in ["inspiration", "ideas", "style", "look"]):
        response = f"""Perfect! Let's explore your design inspiration for this {room_type}. I specialize in helping you organize your ideas and understand your style:

**Style Discovery Questions:**
• What feeling do you want your space to have? (cozy, modern, elegant, energizing)
• Are you drawn to light or dark color schemes?
• Do you prefer clean lines or more decorative elements?
• What materials make you feel at home? (wood, stone, metal, etc.)

**Organizing Your Inspiration:**
• Current space photos (what you have now)
• Ideal inspiration images (what you love)
• Specific elements that catch your eye

I'll help you identify patterns in your preferences and create a clear vision!"""
        
        suggestions = [
            "Describe my ideal feeling/mood",
            "Talk about colors I'm drawn to",
            "Share materials I love",
            "Help me organize my inspiration"
        ]
    
    else:
        # General welcome message
        conversation_count = len(messages)
        if conversation_count == 0:
            response = f"""Hi! I'm Iris, your design inspiration assistant! I'm here to help you discover and organize your vision for this {room_type} project.

**I specialize in:**
✨ Understanding your current space and what you want to change
🎨 Helping you discover and organize your style preferences  
💡 Extracting specific elements from inspiration you love
📋 Creating clear project requirements for contractors
💰 Keeping your vision realistic and budget-conscious

**Let's start!** What brings you here today? Are you looking to understand your current space better, or do you want to explore your ideal vision?"""
        else:
            response = f"""I'm here to help you refine your {room_type} vision! Based on our conversation so far, I can help you:

• **Organize Your Ideas**: Sort your inspiration into current vs ideal
• **Identify Your Style**: Understand what elements you're consistently drawn to
• **Create Action Items**: Turn inspiration into specific contractor requirements
• **Stay On Budget**: Prioritize improvements for maximum impact

What would you like to focus on next?"""
        
        suggestions = [
            "Tell you about my current space",
            "Explore my ideal vision",
            "Help organize my inspiration",
            "Create contractor requirements"
        ]
    
    return {
        "response": response,
        "suggestions": suggestions
    }

async def save_message_to_unified_system(conversation_id: str, user_message: str, assistant_response: str, user_id: str):
    """Save conversation messages to unified system"""
    try:
        # Save user message via HTTP
        user_msg_request = {
            "conversation_id": conversation_id,
            "sender_type": "user",
            "sender_id": user_id,
            "content": user_message,
            "content_type": "text"
        }
        
        response = requests.post(
            f"{get_backend_url()}/conversations/message",
            json=user_msg_request,
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to save user message: {response.status_code}")
        
        # Save assistant message via HTTP
        assistant_msg_request = {
            "conversation_id": conversation_id,
            "sender_type": "agent",
            "agent_type": "IRIS",
            "content": assistant_response,
            "content_type": "text"
        }
        
        response = requests.post(
            f"{get_backend_url()}/conversations/message",
            json=assistant_msg_request,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("Successfully saved messages to unified system")
        else:
            logger.error(f"Failed to save assistant message: {response.status_code}")
        
    except Exception as e:
        logger.error(f"Error saving messages to unified system: {e}")

# Image Analysis Endpoint (Unified System Compatible)
class ImageAnalysisRequest(BaseModel):
    image_urls: list[str]
    category: str  # 'current' or 'ideal'
    filenames: list[str]
    conversation_id: str
    user_id: str

class ImageAnalysisResponse(BaseModel):
    analysis: str
    tags: list[str]
    category: str

@router.post("/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image_unified(request: ImageAnalysisRequest):
    """Analyze uploaded images using unified conversation system"""
    try:
        # Store image analysis as memory in unified system
        await store_image_analysis_memory(
            request.conversation_id,
            request.image_urls,
            request.category,
            request.user_id
        )
        
        if client:
            # Use GPT-4V for image analysis  
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text", 
                                    "text": f"Analyze this {request.category} space image for a home renovation project. Focus on style, materials, colors, and design elements. If current space, identify improvement opportunities. If inspiration, highlight appealing elements."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": request.image_urls[0]}
                                }
                            ]
                        }
                    ],
                    max_completion_tokens=500  # Fixed: GPT-4o uses max_completion_tokens
                )
                
                analysis = response.choices[0].message.content
                
            except Exception as vision_error:
                logger.warning(f"GPT-4V failed: {vision_error}")
                analysis = get_fallback_image_analysis(request.category)
        else:
            analysis = get_fallback_image_analysis(request.category)
        
        # Generate appropriate tags
        if request.category == "current":
            tags = ["current-space", "needs-assessment", "baseline"]
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
            analysis=f"I can see your {request.category} image! Tell me what specific aspects appeal to you or concern you about this space.",
            tags=[request.category, "pending-analysis"],
            category=request.category
        )

async def store_design_preferences_memory(conversation_id: str, user_message: str, ai_response: str, context: dict):
    """Store design preferences in unified memory system for cross-agent access"""
    try:
        # Extract design preferences from conversation
        preferences = extract_design_preferences(user_message, ai_response, context)
        
        if preferences:
            # Store memory via HTTP request
            memory_request = {
                "conversation_id": conversation_id,
                "memory_type": "design_preferences",
                "key": "iris_style_preferences",
                "value": {
                    "preferences": preferences,
                    "last_updated": datetime.now().isoformat(),
                    "conversation_context": context.get("conversation", {}).get("title", "Design Project")
                },
                "confidence": 0.9
            }
            
            response = requests.post(
                f"{get_backend_url()}/conversations/memory",
                json=memory_request,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Stored design preferences: {list(preferences.keys())}")
            else:
                logger.error(f"Failed to store memory: {response.status_code}")
        
    except Exception as e:
        logger.error(f"Error storing design preferences memory: {e}")

async def store_image_analysis_memory(conversation_id: str, image_urls: list[str], category: str, user_id: str):
    """Store image analysis as memory in unified system"""
    try:
        # Store image metadata via HTTP request
        memory_request = {
            "conversation_id": conversation_id,
            "memory_type": "image_analysis",
            "key": f"uploaded_image_{category}",
            "value": {
                "image_urls": image_urls,
                "category": category,
                "uploaded_by": user_id,
                "uploaded_at": datetime.now().isoformat()
            },
            "confidence": 1.0
        }
        
        response = requests.post(
            f"{get_backend_url()}/conversations/memory",
            json=memory_request,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Stored image analysis memory for {category} images")
        else:
            logger.error(f"Failed to store image memory: {response.status_code}")
        
    except Exception as e:
        logger.error(f"Error storing image analysis memory: {e}")

def extract_design_preferences(user_message: str, ai_response: str, context: dict) -> dict:
    """Extract design preferences from Iris conversation for cross-agent memory"""
    preferences = {}
    
    # Combine message content for analysis
    combined_text = f"{user_message} {ai_response}".lower()
    
    # Extract style preferences
    style_keywords = {
        "modern": ["modern", "contemporary", "minimalist", "clean lines"],
        "farmhouse": ["farmhouse", "rustic", "shiplap", "barn door"],
        "traditional": ["traditional", "classic", "formal"],
        "industrial": ["industrial", "exposed brick", "metal", "concrete"],
        "scandinavian": ["scandinavian", "hygge", "light wood"],
        "mediterranean": ["mediterranean", "terracotta", "stucco"]
    }
    
    detected_styles = []
    for style, keywords in style_keywords.items():
        if any(keyword in combined_text for keyword in keywords):
            detected_styles.append(style)
    
    if detected_styles:
        preferences["preferred_styles"] = detected_styles
    
    # Extract color preferences
    color_keywords = {
        "neutral": ["white", "beige", "cream", "gray", "neutral"],
        "warm": ["warm", "cozy", "earth tones", "brown", "orange"],
        "cool": ["cool", "blue", "green", "calming"],
        "dark": ["dark", "black", "deep colors", "dramatic"],
        "bright": ["bright", "colorful", "vibrant", "bold"]
    }
    
    detected_colors = []
    for color_type, keywords in color_keywords.items():
        if any(keyword in combined_text for keyword in keywords):
            detected_colors.append(color_type)
    
    if detected_colors:
        preferences["color_preferences"] = detected_colors
    
    # Extract material preferences
    materials = ["wood", "stone", "metal", "glass", "ceramic", "marble", "granite", "quartz"]
    detected_materials = [material for material in materials if material in combined_text]
    
    if detected_materials:
        preferences["material_preferences"] = detected_materials
    
    # Extract room-specific information
    room_type = context.get("conversation", {}).get("metadata", {}).get("room_type")
    if room_type:
        preferences["focus_room"] = room_type
    
    # Extract budget mentions
    budget_keywords = ["budget", "cost", "price", "affordable", "expensive", "cheap"]
    if any(keyword in combined_text for keyword in budget_keywords):
        preferences["budget_conscious"] = True
    
    return preferences

def get_fallback_image_analysis(category: str) -> str:
    """Fallback image analysis when AI vision is unavailable"""
    if category == "current":
        return """I can see your current space! To give you the best guidance, tell me:

• What aspects of this space do you want to keep?
• What feels outdated or needs improvement?
• How does the current layout work for your daily routine?
• Are there any functional challenges you face?

Understanding what you like and dislike about your current space helps me suggest targeted improvements that will make the biggest impact!"""
    else:
        return """I can see your inspiration image! This is a great way to explore your style preferences. Tell me:

• What specific elements catch your eye in this image?
• Is it the color scheme, materials, layout, or overall feeling?
• How do you imagine incorporating these elements into your space?
• What aspects feel most important to achieve?

Understanding what draws you to certain inspirations helps me guide you toward a cohesive vision for your project!"""

# Create singleton instance for compatibility
iris_unified_agent = router