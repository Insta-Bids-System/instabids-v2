"""
COIA Streaming Chat Router with GPT-5 Streaming Support
Implements Server-Sent Events (SSE) for real-time token streaming
"""

import asyncio
import json
import logging
import os
from typing import AsyncGenerator, Dict, Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel

from .unified_graph import UnifiedCoIAGraph
from .unified_state import UnifiedCoIAState
from .tools import coia_tools

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# GPT-5 model configuration with fallback
PREFERRED_MODEL = "gpt-5"  # Will fallback to gpt-4o if not available
FALLBACK_MODEL = "gpt-4o"

router = APIRouter()


class StreamChatRequest(BaseModel):
    message: str
    session_id: str
    contractor_id: str = None
    interface: str = "chat"


class StreamChatResponse(BaseModel):
    """SSE Response structure"""
    type: str  # "token", "tool_call", "complete", "error" 
    content: str = ""
    metadata: Dict[str, Any] = {}


async def stream_openai_chat(messages: list, model: str = PREFERRED_MODEL) -> AsyncGenerator[str, None]:
    """
    Stream OpenAI chat completion with token-by-token delivery
    """
    try:
        # Try GPT-5 first, fallback to GPT-4o
        try:
            stream = await openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                stream=True
            )
        except Exception as e:
            if model == PREFERRED_MODEL:
                logger.warning(f"GPT-5 not available, falling back to GPT-4o: {e}")
                # Fallback to GPT-4o
                stream = await openai_client.chat.completions.create(
                    model=FALLBACK_MODEL,
                    messages=messages,
                    max_tokens=1000,
                    temperature=0.7,
                    stream=True
                )
            else:
                raise e
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield content
                
    except Exception as e:
        logger.error(f"OpenAI streaming error: {e}")
        yield f"[Error: {str(e)}]"


async def generate_sse_stream(request: StreamChatRequest) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events stream for COIA chat
    """
    try:
        logger.info(f"Starting SSE stream for session {request.session_id}")
        
        # Yield initial connection confirmation
        yield f"data: {json.dumps({'type': 'connected', 'content': 'Stream connected'})}\n\n"
        
        # Process the message through COIA system
        yield f"data: {json.dumps({'type': 'processing', 'content': 'Processing your message...'})}\n\n"
        
        # Check if this is a contractor onboarding message
        if request.contractor_id or any(keyword in request.message.lower() for keyword in 
                                      ["own", "business", "company", "contractor"]):
            
            # Use research mode for contractor onboarding
            yield f"data: {json.dumps({'type': 'tool_call', 'content': 'Researching your business...'})}\n\n"
            
            # Extract business name from message
            business_name = extract_business_name(request.message)
            if business_name:
                
                # Step 1: Web search
                yield f"data: {json.dumps({'type': 'tool_call', 'content': f'Searching web for {business_name}...'})}\n\n"
                web_data = await coia_tools.web_search_company(business_name, "South Florida")
                
                # Step 2: Google Business search
                yield f"data: {json.dumps({'type': 'tool_call', 'content': 'Searching Google Business listings...'})}\n\n"
                google_data = await coia_tools.search_google_business(business_name, "South Florida")
                
                # Step 3: Build profile
                yield f"data: {json.dumps({'type': 'tool_call', 'content': 'Building contractor profile...'})}\n\n"
                profile = await coia_tools.build_contractor_profile(
                    business_name, google_data, web_data, {}
                )
                
                # Step 4: Search matching bid cards
                yield f"data: {json.dumps({'type': 'tool_call', 'content': 'Finding matching projects...'})}\n\n"
                bid_cards = await coia_tools.search_bid_cards(profile)
                
                # Generate streaming response with real data
                system_message = f"""
                You are COIA, an intelligent contractor onboarding assistant. 
                
                Based on your research, you found:
                - Business: {profile.get('company_name', business_name)}
                - Services: {', '.join(profile.get('services', []))}
                - Website: {profile.get('website', 'Not found')}
                - Completeness: {profile.get('completeness_score', 0):.0f}%
                - Matching Projects: {len(bid_cards)} projects found
                
                Respond naturally about what you discovered and ask if the information is correct.
                Be conversational and helpful, not robotic.
                """
                
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": request.message}
                ]
                
                # Stream the GPT response
                yield f"data: {json.dumps({'type': 'response_start', 'content': 'Here's what I found about your business:'})}\n\n"
                
                async for token in stream_openai_chat(messages):
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                    # Small delay to make streaming visible
                    await asyncio.sleep(0.05)
                
                # Include the research results in metadata
                yield f"data: {json.dumps({'type': 'metadata', 'content': '', 'metadata': {'profile': profile, 'bid_cards': bid_cards}})}\n\n"
                
            else:
                # No business name detected - general conversation
                messages = [
                    {"role": "system", "content": "You are COIA, a contractor onboarding assistant. Be helpful and ask for their business name."},
                    {"role": "user", "content": request.message}
                ]
                
                async for token in stream_openai_chat(messages):
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                    await asyncio.sleep(0.05)
        else:
            # General conversation mode
            messages = [
                {"role": "system", "content": "You are COIA, a helpful contractor onboarding assistant."},
                {"role": "user", "content": request.message}
            ]
            
            async for token in stream_openai_chat(messages):
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                await asyncio.sleep(0.05)
        
        # Signal completion
        yield f"data: {json.dumps({'type': 'complete', 'content': ''})}\n\n"
        
    except Exception as e:
        logger.error(f"SSE stream error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'content': f'Error: {str(e)}'})}\n\n"


def extract_business_name(message: str) -> str:
    """Extract business name from user message"""
    import re
    
    message_lower = message.lower()
    
    # Look for business name patterns
    patterns = [
        r"i own (.+?)(?:\s+in\s+|\s*[.!?]|\s*$)",
        r"my business is (.+?)(?:\s+in\s+|\s*[.!?]|\s*$)", 
        r"my company is (.+?)(?:\s+in\s+|\s*[.!?]|\s*$)",
        r"i run (.+?)(?:\s+in\s+|\s*[.!?]|\s*$)",
        r"(.+?)\s+in\s+[\w\s]+",  # "TurfGrass Artificial Solutions in South Florida"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message_lower)
        if match:
            business_name = match.group(1).strip()
            # Clean up common words
            business_name = re.sub(r"\b(a|the|my|our)\b", "", business_name).strip()
            if len(business_name) > 3:  # Valid business name
                return business_name.title()
    
    return ""


@router.post("/ai/chat/stream")
async def stream_chat(request: StreamChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events
    """
    logger.info(f"Streaming chat request from session {request.session_id}")
    
    return StreamingResponse(
        generate_sse_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )


@router.get("/ai/chat/health")
async def chat_health():
    """Health check for chat streaming"""
    return {
        "status": "healthy",
        "streaming": "available",
        "model": f"{PREFERRED_MODEL} (fallback: {FALLBACK_MODEL})"
    }