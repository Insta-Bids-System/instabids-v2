"""
BSA Fast Streaming Endpoint - DeepAgents Powered
Optimized for <5 second response times with 4 specialized sub-agents
Upgraded to use DeepAgents framework while maintaining exact API compatibility
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import asyncio
import os
import logging
from openai import AsyncOpenAI

from database import SupabaseDB
# OLD BSA imports removed - now using DeepAgents implementation
from agents.bsa.memory_integration import save_bsa_state, restore_bsa_state, BSAMemoryIntegrator
from adapters.contractor_context import ContractorContextAdapter
from memory.contractor_ai_memory import ContractorAIMemory
from services.my_bids_tracker import my_bids_tracker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/bsa", tags=["BSA-Stream"])

# Initialize database and adapters
db = SupabaseDB()
contractor_adapter = ContractorContextAdapter()
memory_integrator = BSAMemoryIntegrator()
ai_memory = ContractorAIMemory()  # Initialize AI extraction memory system

# ============================================================================
# REQUEST MODEL
# ============================================================================

class BSAStreamRequest(BaseModel):
    contractor_id: str
    message: str
    session_id: Optional[str] = None
    # Include all optional fields to prevent validation failures
    images: Optional[List[str]] = None
    bid_card_id: Optional[str] = None

# ============================================================================
# FAST STREAMING ENDPOINT
# ============================================================================

@router.post("/fast-stream")
async def bsa_fast_stream_endpoint(request: BSAStreamRequest):
    """Frontend compatibility endpoint - delegates to unified-stream"""
    return await bsa_unified_stream(request)

@router.post("/unified-stream") 
async def bsa_unified_stream(request: BSAStreamRequest):
    """
    Fast BSA streaming endpoint - DeepAgents Powered
    
    UPGRADED: Now uses DeepAgents framework with 4 specialized sub-agents:
    - Bid Card Search Specialist
    - Bid Submission Specialist  
    - Market Research Specialist
    - Group Bidding Specialist
    
    Key optimizations maintained:
    1. Stream starts immediately (no waiting for context)
    2. Context loading happens async while streaming
    3. Database saves are non-blocking
    4. True SSE streaming with immediate chunk forwarding
    5. Unified memory system integration
    """
    
    async def generate_stream():
        try:
            # Start streaming immediately - same as before
            yield f"data: {json.dumps({'status': 'starting', 'message': 'BSA DeepAgents initializing...'})}\n\n"
            
            # Fast fail if no OpenAI API key - same as before
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                yield f"data: {json.dumps({'error': 'No OpenAI API key configured'})}\n\n"
                return
            
            # Load unified memory state using complete BSAMemoryIntegrator
            yield f"data: {json.dumps({'status': 'loading_memory', 'message': 'Restoring BSA DeepAgents state...'})}\n\n"
            
            # Use BSAMemoryIntegrator for complete state restoration
            contractor_memory_task = asyncio.create_task(
                memory_integrator.restore_deepagents_state(request.contractor_id, None)
            )
            # Session-specific memory restoration
            session_memory_task = asyncio.create_task(
                memory_integrator.restore_deepagents_state(request.contractor_id, request.session_id)
            ) if request.session_id else None
            
            # Load My Bids context in parallel
            my_bids_task = asyncio.create_task(
                my_bids_tracker.load_full_my_bids_context(request.contractor_id)
            )
            
            # Start context loading async (non-blocking) - same as before
            context_task = asyncio.create_task(load_contractor_context_async(request.contractor_id))
            
            # Get My Bids context if ready quickly
            my_bids_context = None
            try:
                my_bids_context = await asyncio.wait_for(my_bids_task, timeout=2.0)
                if my_bids_context and my_bids_context.get('total_my_bids', 0) > 0:
                    yield f"data: {json.dumps({'status': 'my_bids_loaded', 'message': f'Found {my_bids_context["total_my_bids"]} bid cards in your My Bids section', 'my_bids_count': my_bids_context['total_my_bids']})}\n\n"
                    logger.info(f"BSA: Loaded {my_bids_context['total_my_bids']} My Bids for contractor {request.contractor_id}")
            except asyncio.TimeoutError:
                logger.warning("My Bids loading timed out, continuing without")
            
            # Get memory state if ready quickly
            restored_state = {}
            try:
                # Try to get contractor-level memory first (increased timeout for production)
                contractor_state = await asyncio.wait_for(contractor_memory_task, timeout=3.0)
                if contractor_state and "messages" in contractor_state:
                    restored_state = contractor_state
                    
                # If we have session-specific memory, merge/override with it
                if session_memory_task:
                    try:
                        session_state = await asyncio.wait_for(session_memory_task, timeout=2.0)
                        if session_state and "messages" in session_state:
                            # Use session-specific if it has more messages (more recent)
                            if len(session_state.get("messages", [])) > len(restored_state.get("messages", [])):
                                restored_state = session_state
                    except asyncio.TimeoutError:
                        pass
                
                if restored_state and "messages" in restored_state:
                    message_count = len(restored_state.get("messages", []))
                    yield f"data: {json.dumps({'status': 'memory_restored', 'message': f'Welcome back! Restored {message_count} previous messages.'})}\n\n"
                else:
                    yield f"data: {json.dumps({'status': 'memory_empty', 'message': 'Starting fresh conversation...'})}\n\n"
                    
            except asyncio.TimeoutError:
                # Continue without memory if it takes too long
                yield f"data: {json.dumps({'status': 'memory_timeout', 'message': 'Starting fresh session...'})}\n\n"
            
            # Route to DeepAgents streaming processor with same API pattern
            session_id = request.session_id or f"bsa_{datetime.now().timestamp()}"
            full_response = ""
            
            try:
                # Extract conversation history from restored state with token trimming
                conversation_history = []
                if restored_state and "messages" in restored_state:
                    # Convert LangChain messages to dict format for OpenAI
                    from langchain_core.messages import HumanMessage, AIMessage
                    logger.info(f"BSA: Restoring {len(restored_state['messages'])} messages from state")
                    
                    # Apply token trimming to prevent overflow
                    def estimate_tokens(text: str) -> int:
                        return len(text) // 4
                    
                    def trim_messages_for_api(messages, max_tokens: int = 150000):
                        """Trim messages to fit API token limits"""
                        if not messages:
                            return messages
                        
                        # Estimate tokens for all messages
                        total_tokens = sum(estimate_tokens(str(getattr(msg, 'content', str(msg)))) for msg in messages)
                        
                        if total_tokens <= max_tokens:
                            logger.info(f"BSA: All {len(messages)} messages fit in {total_tokens} estimated tokens")
                            return messages
                        
                        # Trim from the beginning, keep most recent messages
                        trimmed = []
                        current_tokens = 0
                        
                        for msg in reversed(messages):  # Start from most recent
                            content = str(getattr(msg, 'content', str(msg)))
                            msg_tokens = estimate_tokens(content)
                            
                            if current_tokens + msg_tokens <= max_tokens:
                                trimmed.insert(0, msg)  # Insert at beginning to maintain order
                                current_tokens += msg_tokens
                            else:
                                break
                        
                        logger.warning(f"BSA: Trimmed {len(messages)} messages to {len(trimmed)} messages "
                                     f"(estimated {total_tokens} → {current_tokens} tokens)")
                        
                        # Ensure minimum context
                        if len(trimmed) < 6 and len(messages) >= 6:
                            trimmed = messages[-6:]  # Keep last 3 exchanges minimum
                            logger.info(f"BSA: Ensured minimum context with last 6 messages")
                        
                        return trimmed
                    
                    # Apply trimming before conversion
                    trimmed_messages = trim_messages_for_api(restored_state["messages"])
                    
                    for msg in trimmed_messages:
                        if isinstance(msg, HumanMessage):
                            conversation_history.append({"role": "user", "content": msg.content})
                        elif isinstance(msg, AIMessage):
                            conversation_history.append({"role": "assistant", "content": msg.content})
                        elif hasattr(msg, 'type') and hasattr(msg, 'content'):
                            # Legacy format fallback
                            role = "assistant" if msg.type == "ai" else "user"
                            conversation_history.append({"role": role, "content": msg.content})
                        elif isinstance(msg, dict):
                            conversation_history.append(msg)
                    logger.info(f"BSA: Converted to {len(conversation_history)} conversation history items (token-limited)")
                else:
                    logger.info("BSA: No messages found in restored state")
                
                # Inject My Bids context into conversation if available
                if my_bids_context and my_bids_context.get('total_my_bids', 0) > 0:
                    # Create a system message with My Bids context
                    my_bids_summary = f"""You are assisting a contractor who has {my_bids_context['total_my_bids']} bid cards in their My Bids section.
                    They have sent {my_bids_context.get('total_messages', 0)} messages and submitted {my_bids_context.get('total_proposals', 0)} proposals.
                    Engagement level: {my_bids_context.get('engagement_level', 'low')}.
                    """
                    
                    if my_bids_context.get('active_conversations'):
                        my_bids_summary += f"\nActive conversations: {len(my_bids_context['active_conversations'])} bid cards with recent activity."
                    
                    # Add context about specific bid cards if relevant
                    if my_bids_context.get('my_bids') and len(my_bids_context['my_bids']) > 0:
                        recent_bids = my_bids_context['my_bids'][:3]  # Get top 3 most recent
                        my_bids_summary += "\nRecent bid cards they've interacted with:"
                        for bid in recent_bids:
                            my_bids_summary += f"\n- {bid.get('bid_card_title', 'Unknown')} ({bid.get('status', 'viewed')})"
                    
                    # Prepend as system context
                    conversation_history.insert(0, {"role": "system", "content": my_bids_summary})
                    logger.info(f"BSA: Injected My Bids context into conversation")
                
                # Inject AI-extracted contractor memory if available
                try:
                    ai_memory_prompt = await ai_memory.get_memory_for_system_prompt(request.contractor_id)
                    if ai_memory_prompt:
                        # Add AI memory as a separate system message for clarity
                        conversation_history.insert(0, {"role": "system", "content": ai_memory_prompt})
                        logger.info(f"BSA: Injected AI memory context for contractor {request.contractor_id}")
                except Exception as e:
                    logger.warning(f"Failed to load AI memory context: {e}")
                
                # USE DEEPAGENTS BSA - PROPER ORCHESTRATION WITH SUBAGENTS
                from agents.bsa.bsa_deepagents import bsa_deepagent_stream
                
                # Call the DeepAgents orchestrator with full context
                async for chunk in bsa_deepagent_stream(
                    contractor_id=request.contractor_id,
                    message=request.message,
                    conversation_history=conversation_history,
                    session_id=session_id,
                    bid_card_id=request.bid_card_id
                ):
                    # Forward chunk EXACTLY as received - this is what was working!
                    # Don't try to interpret or modify the events
                    yield f"data: {json.dumps(chunk)}\n\n"
                    
                    # Track full response for saving to memory
                    if 'choices' in chunk and chunk['choices']:
                        if chunk['choices'][0].get('delta', {}).get('content'):
                            full_response += chunk['choices'][0]['delta']['content']
                
                # After streaming, save to unified memory system (non-blocking)
                # Build updated conversation history
                from langchain_core.messages import HumanMessage, AIMessage
                
                # Get existing messages or start fresh
                if restored_state and "messages" in restored_state:
                    current_messages = restored_state.get("messages", [])
                else:
                    current_messages = []
                
                # Add this conversation turn
                current_messages.append(HumanMessage(content=request.message))
                if full_response:
                    current_messages.append(AIMessage(content=full_response))
                
                # Create updated state
                updated_state = {
                    "messages": current_messages,
                    "last_interaction": datetime.now().isoformat(),
                    "session_id": session_id,
                    "contractor_id": request.contractor_id,
                    "bid_card_id": request.bid_card_id
                }
                
                # If we had restored state, preserve other fields
                if restored_state:
                    for key, value in restored_state.items():
                        if key not in updated_state:
                            updated_state[key] = value
                
                # Save state using complete BSAMemoryIntegrator (DeepAgents state persistence)
                # Convert LangChain messages to DeepAgents state format
                from deepagents.state import DeepAgentState
                
                deepagents_state = DeepAgentState(
                    messages=current_messages,
                    todos=[],
                    files=[],
                    metadata={
                        "contractor_id": request.contractor_id,
                        "session_id": session_id,
                        "bid_card_id": request.bid_card_id,
                        "last_interaction": datetime.now().isoformat()
                    }
                )
                
                # Save to BOTH contractor-level (cross-session) AND session-level memory
                asyncio.create_task(memory_integrator.save_deepagents_state(
                    contractor_id=request.contractor_id, 
                    state=deepagents_state, 
                    session_id=None  # Contractor-level persistence
                ))
                asyncio.create_task(memory_integrator.save_deepagents_state(
                    contractor_id=request.contractor_id, 
                    state=deepagents_state, 
                    session_id=session_id  # Session-specific persistence
                ))
                
                # Also save to legacy unified conversation system for compatibility
                asyncio.create_task(save_conversation_async(
                    contractor_id=request.contractor_id,
                    session_id=session_id,
                    message=request.message,
                    response=full_response
                ))
                
                # ADDED: AI EXTRACTION MEMORY SYSTEM - Extract insights after each turn
                # This analyzes the conversation and extracts contractor insights using GPT-4o
                if full_response:  # Only extract if we have a meaningful response
                    conversation_data = {
                        'input': request.message,
                        'response': full_response,
                        'context': f"BSA conversation for contractor {request.contractor_id}",
                        'project_type': 'contractor_bidding',  # BSA is always about bidding
                        'bid_amount': None,  # Could extract from response if present
                        'timeline': None  # Could extract from response if present
                    }
                    
                    # Extract and save AI insights asynchronously (non-blocking)
                    asyncio.create_task(ai_memory.update_contractor_memory(
                        contractor_id=request.contractor_id,
                        conversation_data=conversation_data
                    ))
                    
                    logger.info(f"AI extraction initiated for contractor {request.contractor_id}")
                    
                    # Track bid card interaction if mentioned in conversation
                    if request.bid_card_id:
                        # Track that contractor engaged with this bid card
                        asyncio.create_task(my_bids_tracker.track_bid_interaction(
                            contractor_id=request.contractor_id,
                            bid_card_id=request.bid_card_id,
                            interaction_type='message_sent',
                            details={'message': request.message[:200], 'session_id': session_id}
                        ))
                        logger.info(f"Tracked bid interaction for contractor {request.contractor_id} on bid {request.bid_card_id}")
                
                # Get context result if ready (but don't wait) - same as before
                context_info = None
                if context_task.done():
                    try:
                        context_info = await context_task
                    except:
                        pass
                
                # Send completion with context info - same format as before
                yield f"data: {json.dumps({
                    'status': 'complete',
                    'context_info': context_info,
                    'deepagents_powered': True,
                    'memory_integrated': True
                })}\n\n"
                
            except Exception as e:
                logger.error(f"DeepAgents streaming error: {e}")
                yield f"data: {json.dumps({'error': str(e), 'deepagents_error': True})}\n\n"
                
        except Exception as e:
            logger.error(f"BSA stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

# ============================================================================
# ASYNC HELPER FUNCTIONS (Non-blocking)
# ============================================================================

async def load_contractor_context_async(contractor_id: str) -> Dict[str, Any]:
    """Load contractor context asynchronously without blocking the stream - DeepAgents Enhanced"""
    try:
        # Load from both contractors and contractor_leads tables for full context
        contractor = await db.get_contractor_by_id(contractor_id)
        contractor_lead = await db.get_contractor_lead_by_id(contractor_id)
        
        # Merge data for rich context
        context = {
            "has_profile": contractor is not None or contractor_lead is not None,
            "contractor_name": "Unknown Contractor",
            "specialties": [],
            "primary_specialty": None,
            "years_experience": None,
            "certifications": [],
            "license_verified": False,
            "insurance_verified": False,
            "tier": 3  # Default to Tier 3
        }
        
        # Populate from contractor table (Tier 1 authenticated)
        if contractor:
            context.update({
                "contractor_name": contractor.get("company_name", "Contractor"),
                "tier": 1,
                "total_jobs": contractor.get("total_jobs", 0),
                "rating": contractor.get("rating", 0),
                "verified": contractor.get("verified", False)
            })
        
        # Populate from contractor_leads table (Tier 2/3 discovery)
        if contractor_lead:
            context.update({
                "contractor_name": contractor_lead.get("company_name", contractor_lead.get("contact_name", "Contractor")),
                "specialties": contractor_lead.get("specialties", []),
                "years_experience": contractor_lead.get("years_in_business"),
                "certifications": contractor_lead.get("certifications", []),
                "license_verified": contractor_lead.get("license_verified", False),
                "insurance_verified": contractor_lead.get("insurance_verified", False),
                "phone": contractor_lead.get("phone"),
                "email": contractor_lead.get("email"),
                "website": contractor_lead.get("website"),
                "tier": 2 if contractor_lead.get("lead_score", 0) > 80 else 3
            })
        
        # Determine primary specialty for trade-specific routing
        if context["specialties"]:
            # Map specialties to sub-agent categories
            specialty_mapping = {
                "kitchen": ["kitchen", "cabinet", "remodel", "renovation"],
                "landscaping": ["landscaping", "lawn", "garden", "outdoor", "yard"],
                "electrical": ["electrical", "wiring", "lighting", "power"],
                "general": ["construction", "renovation", "repair", "maintenance"]
            }
            
            for category, keywords in specialty_mapping.items():
                if any(keyword in spec.lower() for spec in context["specialties"] for keyword in keywords):
                    context["primary_specialty"] = category
                    break
            
            context["primary_specialty"] = context["primary_specialty"] or "general"
        
        context["total_context_items"] = len([v for v in context.values() if v])
        return context
        
    except Exception as e:
        logger.error(f"Enhanced context load error: {e}")
        return {
            "has_profile": False,
            "total_context_items": 0,
            "contractor_name": "Contractor",
            "specialties": [],
            "primary_specialty": "general",
            "tier": 3
        }

async def save_conversation_async(contractor_id: str, session_id: str, message: str, response: str):
    """Save conversation to database asynchronously without blocking"""
    try:
        await db.save_unified_conversation({
            "user_id": contractor_id,
            "session_id": session_id,
            "agent_type": "BSA",
            "input_data": message,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to save conversation: {e}")

# ============================================================================
# CONTRACTOR CONTEXT ENDPOINT - Frontend Compatibility
# ============================================================================

@router.get("/contractor/{contractor_id}/context")
async def get_bsa_contractor_context(
    contractor_id: str,
    contractor_lead_id: Optional[str] = None
):
    """
    Get complete contractor context for BSA - Frontend Compatibility Endpoint
    
    This endpoint provides the exact context format expected by BSAChat.tsx
    Uses the full ContractorContextAdapter to load comprehensive contractor data
    """
    try:
        logger.info(f"Loading BSA context for contractor {contractor_id}")
        
        # Use the complete ContractorContextAdapter system
        context = contractor_adapter.get_contractor_context(
            contractor_id=contractor_id,
            session_id=None  # Context loading doesn't need session_id
        )
        
        # Transform to format expected by frontend (BSAChat.tsx lines 67-87)
        conversation_history = context.get("conversation_history", [])
        # Separate COIA and BSA conversations based on agent type in metadata
        coia_conversations = []
        bsa_conversations = []
        
        for conv in conversation_history:
            # Check if conversation metadata indicates BSA agent
            if isinstance(conv, dict) and ("BSA" in str(conv.get("agent_type", "")) or "BSA" in str(conv.get("summary", ""))):
                bsa_conversations.append(conv)
            else:
                coia_conversations.append(conv)
        
        frontend_context = {
            "total_context_items": len([v for v in context.values() if v and v != []]),
            "has_profile": context.get("contractor_profile", {}).get("profile_available", False),
            "coia_conversations": len(coia_conversations),
            "bsa_conversations": len(bsa_conversations),
            "bid_history": len(context.get("bid_history", [])),
            "enhanced_profile": context.get("contractor_profile", {}).get("verified", False),
            
            # Additional context data for rich profiles
            "contractor_profile": context.get("contractor_profile", {}),
            "available_projects": context.get("available_projects", []),
            "submitted_bids": context.get("submitted_bids", []),
            "campaign_data": context.get("campaign_data", []),
            "engagement_summary": context.get("engagement_summary", {}),
            
            # Success rate calculation
            "success_rate": calculate_success_rate(context.get("bid_history", [])),
            "average_bid": calculate_average_bid(context.get("bid_history", [])),
            
            # Metadata
            "contractor_id": contractor_id,
            "loaded_at": datetime.utcnow().isoformat(),
            "privacy_filtered": True
        }
        
        logger.info(f"✅ BSA context loaded: {frontend_context['total_context_items']} items")
        return frontend_context
        
    except Exception as e:
        logger.error(f"Error loading BSA contractor context: {e}")
        
        # Return minimal context on error (prevents frontend crashes)
        return {
            "total_context_items": 0,
            "has_profile": False,
            "coia_conversations": 0,
            "bsa_conversations": 0,
            "bid_history": 0,
            "enhanced_profile": False,
            "contractor_id": contractor_id,
            "error": str(e)
        }

def calculate_success_rate(bid_history: List[Dict[str, Any]]) -> float:
    """Calculate contractor's bid success rate"""
    if not bid_history:
        return 0.0
    
    successful_bids = [bid for bid in bid_history if bid.get("selected", False)]
    return (len(successful_bids) / len(bid_history)) * 100

def calculate_average_bid(bid_history: List[Dict[str, Any]]) -> float:
    """Calculate contractor's average bid amount"""
    if not bid_history:
        return 0.0
    
    valid_bids = [bid.get("bid_amount", 0) for bid in bid_history if bid.get("bid_amount")]
    if not valid_bids:
        return 0.0
    
    return sum(valid_bids) / len(valid_bids)