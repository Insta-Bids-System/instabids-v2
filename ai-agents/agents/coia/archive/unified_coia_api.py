"""
Unified COIA API Router
Provides REST API endpoints for the consolidated COIA agent with multiple interfaces
"""
from config.service_urls import get_backend_url

import logging
from datetime import datetime
from typing import Any, Optional

import aiohttp
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# OLD LANGGRAPH IMPORTS REMOVED - Using DeepAgents only
# All LangGraph components archived - system now uses DeepAgents framework


logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(tags=["Unified COIA"])

# DeepAgents system - no global app instance needed
# Each endpoint uses DeepAgents directly


# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chat interface"""
    message: str = Field(..., description="User message to process")
    session_id: str = Field(..., description="Conversation session ID")
    contractor_lead_id: Optional[str] = Field(None, description="Contractor lead ID if available")
    project_id: Optional[str] = Field(None, description="Original project ID if applicable")
    user_id: Optional[str] = Field(None, description="User ID for anonymous-to-authenticated flow")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for session tracking")
    context: Optional[dict[str, Any]] = Field(None, description="Additional context")


class ResearchRequest(BaseModel):
    """Request model for research portal interface"""
    company_data: dict[str, Any] = Field(..., description="Company information to research")
    session_id: str = Field(..., description="Research session ID")
    context: Optional[dict[str, Any]] = Field(None, description="Additional context")


class IntelligenceRequest(BaseModel):
    """Request model for intelligence dashboard interface"""
    contractor_data: dict[str, Any] = Field(..., description="Contractor data to enhance")
    session_id: str = Field(..., description="Intelligence session ID")
    context: Optional[dict[str, Any]] = Field(None, description="Additional context")


class BidCardLinkRequest(BaseModel):
    """Request model for bid card link interface"""
    bid_card_id: str = Field(..., description="ID of the bid card")
    contractor_lead_id: str = Field(..., description="ID of the contractor lead")
    verification_token: str = Field(..., description="Verification token for secure access")
    session_id: Optional[str] = Field(None, description="Session ID (auto-generated if not provided)")


class BusinessResearchRequest(BaseModel):
    """Request model for business research"""
    company_name: str = Field(..., description="Company name to research")
    location: str = Field(..., description="Business location")
    contractor_id: Optional[str] = Field(None, description="Contractor ID if available")


class BusinessResearchResponse(BaseModel):
    """Response model for business research"""
    success: bool = Field(..., description="Whether research succeeded")
    website: Optional[str] = Field(None, description="Company website")
    phone: Optional[str] = Field(None, description="Business phone number")
    address: Optional[str] = Field(None, description="Business address")
    rating: Optional[float] = Field(None, description="Google rating")
    reviews_count: Optional[int] = Field(None, description="Number of reviews")
    business_hours: Optional[dict] = Field(None, description="Business hours")
    google_business_url: Optional[str] = Field(None, description="Google Business listing URL")
    social_media: Optional[dict] = Field(None, description="Social media profiles")
    services: Optional[list[str]] = Field(None, description="Services offered")
    description: Optional[str] = Field(None, description="Business description")


class CoIAResponse(BaseModel):
    """Unified response model for all COIA interfaces"""
    success: bool = Field(..., description="Whether the request succeeded")
    response: Optional[str] = Field(None, description="AI response message")
    current_mode: Optional[str] = Field(None, description="Current operational mode")
    interface: Optional[str] = Field(None, description="Interface used")
    session_id: str = Field(..., description="Session identifier")
    contractor_lead_id: Optional[str] = Field(None, description="Permanent contractor identifier for state persistence")

    # State information
    contractor_profile: Optional[dict[str, Any]] = Field(None, description="Current contractor profile")
    profile_completeness: Optional[float] = Field(None, description="Profile completion percentage")
    completion_ready: Optional[bool] = Field(None, description="Whether onboarding is complete")
    contractor_created: Optional[bool] = Field(None, description="Whether contractor account was created")
    contractor_id: Optional[str] = Field(None, description="Created contractor ID")

    # Mode-specific data
    research_completed: Optional[bool] = Field(None, description="Whether research was completed")
    research_findings: Optional[dict[str, Any]] = Field(None, description="Research results")
    business_info: Optional[dict[str, Any]] = Field(None, description="Business information from research")
    company_name: Optional[str] = Field(None, description="Extracted company name")
    intelligence_data: Optional[dict[str, Any]] = Field(None, description="Intelligence enhancement data")

    # Metadata
    last_updated: Optional[str] = Field(None, description="Last update timestamp")
    transition_reason: Optional[str] = Field(None, description="Reason for mode transition")
    error_details: Optional[str] = Field(None, description="Error details if any")

    # Bid card attachments
    bidCards: Optional[list[dict[str, Any]]] = Field(None, description="Attached bid cards for display")
    aiRecommendation: Optional[str] = Field(None, description="AI recommendation for bid cards")


# Landing Page Interface Endpoints (Unauthenticated)
@router.post("/landing", response_model=CoIAResponse)
async def landing_page_conversation(request: ChatRequest) -> CoIAResponse:
    """
    Handle landing page onboarding conversations (unauthenticated)
    Optimized for contractor onboarding with signup link generation
    WITH PERMANENT STATE PERSISTENCE using contractor_lead_id
    """
    import os
    print(f"🔴 LANDING_PAGE_CONVERSATION CALLED! ENV={os.getenv('USE_DEEPAGENTS_LANDING', 'NOT SET')}", flush=True)
    logger.error(f"🔴 LANDING_PAGE_CONVERSATION CALLED! ENV={os.getenv('USE_DEEPAGENTS_LANDING', 'NOT SET')}")
    try:
        logger.info(f"Landing page request - Session: {request.session_id}, Message length: {len(request.message)}")
        
        # Get unified COIA app
        app = await get_unified_coia_app()
        
        # Get state manager for persistence
        state_manager = await get_state_manager()
        
        # Generate or use existing contractor_lead_id for permanent tracking
        import uuid
        contractor_lead_id = request.contractor_lead_id
        saved_state = None  # Initialize saved_state for DeepAgents branch
        if not contractor_lead_id:
            contractor_lead_id = f"landing-{uuid.uuid4().hex[:12]}"
            logger.info(f"🆕 Generated new contractor_lead_id: {contractor_lead_id}")
        else:
            logger.info(f"📂 Using existing contractor_lead_id: {contractor_lead_id}")
            
            # RESTORE SAVED STATE FOR RETURNING VISITOR
            saved_state = await state_manager.restore_state(contractor_lead_id)
            if saved_state:
                logger.info(f"✅ Restored {len(saved_state)} state fields for returning contractor")
                logger.info(f"   Company: {saved_state.get('company_name')}")
        
        # Invoke landing page interface with permanent ID
        # DeepAgents branch (flag-controlled) with graceful fallback
        import os as _os
        env_value = _os.getenv("USE_DEEPAGENTS_LANDING", "")
        use_da = env_value.lower() == "true"
        logger.info(f"🔍 DeepAgents Debug: USE_DEEPAGENTS_LANDING={env_value}, use_da={use_da}")
        if use_da:
            logger.info("🚀 DeepAgents branch ENTERED - attempting to import and execute")
            try:
                logger.info("📥 Attempting to import landing_deepagent...")
                from agents.coia.landing_deepagent import get_agent as _get_landing_agent
                logger.info("📥 Import successful, getting agent instance...")
                agent = _get_landing_agent()
                logger.info("🤖 Agent instance created successfully")
                
                # Compose DeepAgents input
                da_messages = [{"role": "user", "content": request.message}]
                da_context = saved_state or {}
                da_input = {"messages": da_messages, "context": da_context}
                logger.info(f"📤 Invoking DeepAgents with input: {da_input}")
                
                da_result = agent.invoke(da_input)
                logger.info(f"📥 DeepAgents result type: {type(da_result)}")
                
                # DeepAgents returns {messages, todos, files} - use as-is
                result = da_result if isinstance(da_result, dict) else {"messages": []}
                logger.info("✅ DeepAgents landing path executed SUCCESSFULLY")
            except Exception as da_err:
                logger.error(f"❌ DeepAgents landing failed, falling back to LangGraph: {da_err}")
                result = await invoke_coia_landing_page(
                    app=app,
                    user_message=request.message,
                    session_id=request.session_id,
                    contractor_lead_id=contractor_lead_id
                )
        else:
            logger.info("🏛️ Using LangGraph path (DeepAgents disabled or flag false)")
            result = await invoke_coia_landing_page(
                app=app,
                user_message=request.message,
                session_id=request.session_id,
                contractor_lead_id=contractor_lead_id
            )
        
        # SAVE STATE AFTER PROCESSING (non-blocking)
        import asyncio
        asyncio.create_task(
            state_manager.save_state(
                contractor_lead_id=contractor_lead_id,
                state=result,
                conversation_id=request.conversation_id
            )
        )
        logger.info(f"💾 Initiated state save for {contractor_lead_id}")
        
        # Extract response message - FIXED for DeepAgents compatibility
        response_message = ""
        
        # Handle DeepAgents response format
        if use_da and isinstance(da_result, dict) and "messages" in da_result:
            logger.info(f"🔍 DeepAgents result has messages: {len(da_result['messages'])}")
            # DeepAgents messages format
            for msg in reversed(da_result["messages"]):
                if isinstance(msg, dict):
                    # Handle dict-style messages
                    if msg.get("role") == "assistant" and msg.get("content"):
                        response_message = msg["content"]
                        logger.info(f"✅ Found DeepAgents assistant response: {response_message[:100]}...")
                        break
                elif hasattr(msg, "type") and msg.type == "ai":
                    # Handle LangChain-style messages
                    response_message = msg.content
                    logger.info(f"✅ Found LangChain AI response: {response_message[:100]}...")
                    break
                elif hasattr(msg, "__class__") and "AI" in msg.__class__.__name__:
                    response_message = msg.content
                    logger.info(f"✅ Found AI class response: {response_message[:100]}...")
                    break
        
        # Fallback: if DeepAgents returned empty or no valid response, check LangGraph result
        if not response_message and result.get("messages"):
            logger.info("🔄 Checking LangGraph result for messages")
            for msg in reversed(result["messages"]):
                if (hasattr(msg, "type") and msg.type == "ai") or (hasattr(msg, "__class__") and "AI" in msg.__class__.__name__):
                    response_message = msg.content
                    logger.info(f"✅ Found LangGraph response: {response_message[:100]}...")
                    break
        
        # Emergency fallback: if still no response, return error
        if not response_message:
            logger.error(f"❌ NO RESPONSE EXTRACTED! da_result type: {type(da_result)}, result type: {type(result)}")
            if use_da and isinstance(da_result, dict):
                logger.error(f"   da_result keys: {list(da_result.keys())}")
            if isinstance(result, dict):
                logger.error(f"   result keys: {list(result.keys())}")
            response_message = "I apologize, but I'm having trouble generating a response right now. Please try rephrasing your message."
        
        # Get conversation_id from request if provided
        conversation_id = request.conversation_id
        
        # STEP 3: Save assistant response to conversation
        if conversation_id and response_message:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{get_backend_url()}/api/conversations/message", json={
                    "conversation_id": conversation_id,
                    "sender_type": "assistant",
                    "sender_id": "coia",
                    "content": response_message
                }) as msg_response:
                    if msg_response.status == 200:
                        logger.info(f"Saved assistant message to conversation {conversation_id}")
                
                # STEP 4: Store memory/context if available
                if result.get("contractor_profile"):
                    async with session.post(f"{get_backend_url()}/api/conversations/memory", json={
                        "conversation_id": conversation_id,
                        "memory_type": "contractor_profile",
                        "content": result.get("contractor_profile")
                    }) as mem_response:
                        if mem_response.status == 200:
                            logger.info(f"Saved contractor profile to memory for conversation {conversation_id}")
                
                if result.get("research_findings"):
                    async with session.post(f"{get_backend_url()}/api/conversations/memory", json={
                        "conversation_id": conversation_id,
                        "memory_type": "research_findings",
                        "content": result.get("research_findings")
                    }) as mem_response:
                        if mem_response.status == 200:
                            logger.info(f"Saved research findings to memory for conversation {conversation_id}")
        
        # Build response with signup data if generated
        response_dict = {
            "success": True,
            "response": response_message,
            "current_mode": result.get("current_mode", "conversation"),  # Use actual mode from result
            "interface": "landing_page",
            "session_id": request.session_id,
            "contractor_lead_id": contractor_lead_id,  # Always return the permanent ID
            "profile_completeness": result.get("profile_completeness"),
            "profile_ready_for_signup": result.get("profile_ready_for_signup", False),
            "signup_link_generated": result.get("signup_link_generated", False),
            "research_completed": result.get("research_completed"),  # Add research status
            "business_info": result.get("business_info"),  # Add business info from research
            "company_name": result.get("company_name"),  # Add company name
            "contractor_created": result.get("contractor_created"),  # Add account creation status
            "bidCards": result.get("bid_cards_attached"),  # Add bid cards if found - FIXED: Changed to camelCase
            "last_updated": result.get("last_updated", datetime.now().isoformat()),
        }
        
        # Add signup data if link was generated
        if result.get("signup_data"):
            response_dict["signup_data"] = result.get("signup_data")
        
        return CoIAResponse(**response_dict)
        
    except Exception as e:
        logger.error(f"Error in landing page conversation: {e}")
        return CoIAResponse(
            success=False,
            response="I apologize, but I'm having trouble processing your request right now. Please try again.",
            current_mode="conversation",
            interface="landing_page",
            session_id=request.session_id,
            error_details=str(e)
        )


# Landing Streaming Endpoint (SSE)
@router.post("/landing/stream")
async def landing_page_stream(request: ChatRequest):
    """
    Stream landing page responses in real-time (SSE) using DeepAgents.
    Requires USE_DEEPAGENTS_LANDING=true.
    """
    try:
        import os as _os
        import json
        use_da = _os.getenv("USE_DEEPAGENTS_LANDING", "").lower() == "true"
        if not use_da:
            # Keep behavior explicit: streaming is only implemented for DeepAgents path.
            raise HTTPException(status_code=400, detail="DeepAgents landing streaming requires USE_DEEPAGENTS_LANDING=true")

        # State restore for returning visitors
        state_manager = await get_state_manager()
        contractor_lead_id = request.contractor_lead_id
        saved_state = {}
        if contractor_lead_id:
            saved_state = await state_manager.restore_state(contractor_lead_id) or {}

        from agents.coia.landing_deepagent import get_agent as _get_landing_agent
        agent = _get_landing_agent()

        async def event_gen():
            try:
                da_messages = [{"role": "user", "content": request.message}]
                da_context = saved_state or {}
                da_input = {"messages": da_messages, "context": da_context}

                # Stream DeepAgents events
                async for chunk in agent.astream(da_input):
                    try:
                        # Emit raw chunk as JSON to stay schema-agnostic
                        payload = json.dumps(chunk, default=str)
                        yield f"data: {payload}\n\n"
                    except Exception as enc_err:
                        # Fallback: stringify chunk
                        yield f"data: {str(chunk)}\n\n"

                # Signal completion
                yield "data: [DONE]\n\n"

                # Persist final state non-blocking (best-effort)
                try:
                    import asyncio
                    if contractor_lead_id:
                        # We don't have final result here; persist saved_state + last message as a minimal update
                        minimal_state = {"last_streamed_at": datetime.now().isoformat()}
                        asyncio.create_task(state_manager.save_state(contractor_lead_id, minimal_state, request.conversation_id))
                except Exception:
                    pass

            except Exception as stream_err:
                err_payload = {"error": str(stream_err)}
                yield f"data: {json.dumps(err_payload)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(event_gen(), media_type="text/event-stream")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in landing streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat Interface Endpoints (Authenticated)
@router.post("/chat", response_model=CoIAResponse)
async def chat_conversation(request: ChatRequest) -> CoIAResponse:
    """
    Handle chat interface conversations
    Primary interface for contractor onboarding conversations
    """
    try:
        logger.info(f"Chat request - Session: {request.session_id}, Message length: {len(request.message)}")
        
        # Import HTTP client for unified conversation API calls
        import aiohttp
        import uuid
        
        # Helper to ensure valid UUID - MUST BE DETERMINISTIC!
        def ensure_uuid(value: Optional[str]) -> str:
            """Convert string to valid UUID, return deterministic UUID for same string"""
            if not value:
                return "00000000-0000-0000-0000-000000000000"
            
            try:
                # If it's already a valid UUID, return it
                uuid.UUID(value)
                return value
            except ValueError:
                # If not a valid UUID, create a deterministic UUID from the string
                # This ensures the same string always generates the same UUID
                import hashlib
                namespace_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
                return str(uuid.uuid5(namespace_uuid, value))
        
        # STEP 1: Get or create unified conversation
        conversation_id = None
        async with aiohttp.ClientSession() as session:
            # Check if conversation exists for this user
            user_id = request.contractor_lead_id or request.user_id or "anonymous"
            # Use the deterministic UUID for lookups
            user_uuid = ensure_uuid(user_id)
            async with session.get(f"{get_backend_url()}/api/conversations/user/{user_uuid}") as response:
                if response.status == 200:
                    response_data = await response.json()
                    # The API returns {"success": true, "conversations": [...]}
                    if response_data.get("success") and response_data.get("conversations"):
                        conversations = response_data["conversations"]
                        if conversations and len(conversations) > 0:
                            # Get the conversation_id from the nested structure
                            # Each item has unified_conversations with the actual conversation data
                            first_conv = conversations[0]
                            if "unified_conversations" in first_conv:
                                conv_data = first_conv["unified_conversations"]
                                if isinstance(conv_data, dict):
                                    conversation_id = conv_data.get("id")
                                elif isinstance(conv_data, list) and len(conv_data) > 0:
                                    conversation_id = conv_data[0].get("id")
                            else:
                                # Fallback to direct conversation_id if structure is different
                                conversation_id = first_conv.get("conversation_id")
                            
                            if conversation_id:
                                logger.info(f"Found existing conversation: {conversation_id}")
            
            # Create new conversation if needed
            if not conversation_id:
                async with session.post(f"{get_backend_url()}/api/conversations/create", json={
                    "user_id": user_uuid,  # Use the already computed deterministic UUID
                    "agent_type": "coia",
                    "context": {
                        "session_id": request.session_id,
                        "interface": "chat",
                        "project_id": request.project_id
                    }
                }) as response:
                    if response.status == 200:
                        result = await response.json()
                        conversation_id = result.get("conversation_id")
                        logger.info(f"Created new conversation: {conversation_id}")
            
            # STEP 2: Save user message to conversation
            if conversation_id:
                async with session.post(f"{get_backend_url()}/api/conversations/message", json={
                    "conversation_id": conversation_id,
                    "sender_type": "user",
                    "sender_id": user_uuid,  # Use the deterministic UUID
                    "content": request.message
                }) as msg_response:
                    if msg_response.status == 200:
                        logger.info(f"Saved user message to conversation {conversation_id}")

        # Get unified COIA app
        app = await get_unified_coia_app()

        # FIXED: Use ContractorContextAdapter for memory retrieval
        thread_id = request.contractor_lead_id if request.contractor_lead_id else request.session_id
        config = {
            "configurable": {
                "thread_id": thread_id,
            },
            "recursion_limit": 20,  # Lower limit for faster response
            "max_concurrency": 5
        }

        # Create user message
        from langchain_core.messages import HumanMessage, AIMessage
        
        # Load conversation context via ContractorContextAdapter
        conversation_history = []
        existing_profile = {}
        
        if request.contractor_lead_id:
            try:
                # Import the unified adapter
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                from adapters.contractor_context import ContractorContextAdapter
                
                adapter = ContractorContextAdapter()
                context = adapter.get_contractor_context(request.contractor_lead_id, request.session_id)
                
                existing_profile = context.get("contractor_profile", {})
                conversation_history_data = context.get("conversation_history", [])
                
                logger.info(f"✅ Loaded context via adapter for {request.contractor_lead_id}")
                logger.info(f"  - Company: {existing_profile.get('company_name', 'Unknown')}")
                logger.info(f"  - Conversations: {len(conversation_history_data)}")
                
                # Create conversation summary from history
                if conversation_history_data:
                    summary_parts = []
                    for conv in conversation_history_data[-3:]:  # Last 3 conversations
                        summary = conv.get("summary", "")
                        if summary:
                            summary_parts.append(summary)
                    
                    if summary_parts:
                        conversation_summary = "Previous conversations: " + "; ".join(summary_parts)
                        conversation_history.append(AIMessage(content=conversation_summary))
                        logger.info(f"📝 Added conversation summary: {len(summary_parts)} previous sessions")
                
            except Exception as adapter_error:
                logger.error(f"Error loading context via adapter: {adapter_error}")
        
        # Create initial state with loaded context
        from agents.coia.unified_graph import create_initial_state
        initial_state = create_initial_state(
            session_id=request.session_id,
            interface="chat",
            contractor_lead_id=request.contractor_lead_id,
            original_project_id=request.project_id
        ).to_langgraph_state()
        
        # Apply existing profile data
        if existing_profile.get("profile_available"):
            initial_state["company_name"] = existing_profile.get("company_name")
            initial_state["contractor_profile"] = existing_profile
            logger.info(f"🏢 Applied existing profile: {existing_profile.get('company_name')}")
        
        # Add conversation history + new message
        initial_state["messages"] = conversation_history + [HumanMessage(content=request.message)]
        input_data = initial_state

        # Stream through workflow - take first meaningful AI response
        response_message = ""
        async for chunk in app.astream(input_data, config):
            # Check if chunk contains messages with AI response
            if isinstance(chunk, dict):
                for node_name, node_data in chunk.items():
                    if isinstance(node_data, dict) and "messages" in node_data:
                        messages = node_data["messages"]
                        # Get the last AI message from this chunk
                        for msg in reversed(messages):
                            if (hasattr(msg, "type") and msg.type == "ai") or \
                               (hasattr(msg, "__class__") and "AI" in msg.__class__.__name__):
                                if msg.content and msg.content.strip():
                                    response_message = msg.content
                                    logger.info(f"Got AI response from {node_name}: {response_message[:100]}...")
                                    break
                    
                    # If we got a response, break out of streaming
                    if response_message:
                        break
            
            # Stop streaming after we get the first meaningful response
            if response_message:
                break

        # Get final state for additional data
        final_state = await app.aget_state(config)
        result = final_state.values if final_state else {}
        
        # STEP 3: Save assistant response to conversation
        if conversation_id and response_message:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{get_backend_url()}/api/conversations/message", json={
                    "conversation_id": conversation_id,
                    "sender_type": "assistant",
                    "sender_id": "coia",
                    "content": response_message
                }) as msg_response:
                    if msg_response.status == 200:
                        logger.info(f"Saved assistant message to conversation {conversation_id}")
                
                # STEP 4: Store memory/context if available
                if result.get("contractor_profile"):
                    async with session.post(f"{get_backend_url()}/api/conversations/memory", json={
                        "conversation_id": conversation_id,
                        "memory_type": "contractor_profile",
                        "content": result.get("contractor_profile")
                    }) as mem_response:
                        if mem_response.status == 200:
                            logger.info(f"Saved contractor profile to memory for conversation {conversation_id}")
                
                if result.get("research_findings"):
                    async with session.post(f"{get_backend_url()}/api/conversations/memory", json={
                        "conversation_id": conversation_id,
                        "memory_type": "research_findings",
                        "content": result.get("research_findings")
                    }) as mem_response:
                        if mem_response.status == 200:
                            logger.info(f"Saved research findings to memory for conversation {conversation_id}")

        # Build response with bid card attachments
        response_dict = {
            "success": True,
            "response": response_message,
            "current_mode": result.get("current_mode", "conversation"),
            "interface": "chat",
            "session_id": request.session_id,
            "contractor_profile": result.get("contractor_profile"),
            "profile_completeness": result.get("profile_completeness"),
            "completion_ready": result.get("completion_ready", False),
            "contractor_created": result.get("contractor_created", False),
            "contractor_id": result.get("contractor_id"),
            "research_completed": result.get("research_completed", False),
            "research_findings": result.get("research_findings"),
            "intelligence_data": result.get("intelligence_data"),
            "last_updated": result.get("last_updated", datetime.now().isoformat()),
            "transition_reason": result.get("transition_reason"),
            "error_details": result.get("error_state"),
        }

        # Add bid cards if available
        if result.get("bid_cards_attached"):
            response_dict["bidCards"] = result.get("bid_cards_attached")
        # Safely access nested dictionary for AI recommendation
        tool_results = result.get("tool_results")
        if tool_results and isinstance(tool_results, dict):
            bid_card_search = tool_results.get("bid_card_search")
            if bid_card_search and isinstance(bid_card_search, dict):
                ai_rec = bid_card_search.get("ai_recommendation")
                if ai_rec:
                    response_dict["aiRecommendation"] = ai_rec

        return CoIAResponse(**response_dict)

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error in chat conversation: {e}")
        logger.error(f"Full traceback: {error_trace}")
        return CoIAResponse(
            success=False,
            response="I apologize, but I'm having trouble processing your request right now. Please try again.",
            current_mode="conversation",
            interface="chat",
            session_id=request.session_id,
            error_details=f"Error: {str(e)}\nType: {type(e).__name__}"
        )


@router.get("/chat/session/{session_id}")
async def get_chat_session(session_id: str) -> dict[str, Any]:
    """Get current state of a chat session"""
    try:
        # This would load state from checkpointer
        # For now, return basic session info
        return {
            "session_id": session_id,
            "interface": "chat",
            "status": "active",
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Business Research Endpoint
@router.post("/research-business", response_model=BusinessResearchResponse)
async def research_business(request: BusinessResearchRequest) -> BusinessResearchResponse:
    """
    Research business information for auto-filling contractor profiles
    Uses WebSearch and other tools to find real business data
    """
    try:
        logger.info(f"Business research - Company: {request.company_name}, Location: {request.location}")
        
        # Import WebSearch functionality
        import httpx
        import json
        
        # Search for business information
        search_query = f"{request.company_name} {request.location} contractor business"
        
        # Simulate web search (in production, use actual WebSearch MCP tool or Google Places API)
        # For now, return mock data to demonstrate the flow
        
        # Store research results in potential_contractors table
        from utils.database_simple import get_supabase_client
        supabase = await get_supabase_client()
        
        # Check if we already have data for this company
        existing = await supabase.table("potential_contractors").select("*").eq("company_name", request.company_name).single().execute()
        
        if existing.data:
            # Return cached data
            return BusinessResearchResponse(
                success=True,
                website=existing.data.get("website"),
                phone=existing.data.get("phone"),
                address=existing.data.get("address"),
                rating=existing.data.get("google_rating"),
                reviews_count=existing.data.get("google_reviews_count"),
                description=existing.data.get("ai_business_summary")
            )
        
        # For demo purposes, return structured data
        # In production, this would come from actual API calls
        return BusinessResearchResponse(
            success=True,
            website=f"{request.company_name.lower().replace(' ', '')}.com",
            phone="(555) 123-4567",
            address=f"123 Business St, {request.location}",
            rating=4.8,
            reviews_count=127,
            business_hours={
                "Monday": "8:00 AM - 6:00 PM",
                "Tuesday": "8:00 AM - 6:00 PM",
                "Wednesday": "8:00 AM - 6:00 PM",
                "Thursday": "8:00 AM - 6:00 PM",
                "Friday": "8:00 AM - 6:00 PM",
                "Saturday": "9:00 AM - 3:00 PM",
                "Sunday": "Closed"
            },
            google_business_url=f"https://g.page/{request.company_name.lower().replace(' ', '')}",
            social_media={
                "facebook": f"facebook.com/{request.company_name.lower().replace(' ', '')}",
                "instagram": f"@{request.company_name.lower().replace(' ', '_')}"
            },
            services=["Artificial Turf Installation", "Landscaping", "Lawn Care"],
            description=f"{request.company_name} is a professional contractor serving {request.location} with quality services."
        )
        
    except Exception as e:
        logger.error(f"Error researching business: {e}")
        return BusinessResearchResponse(
            success=False
        )


# Research Interface Endpoints
@router.post("/research", response_model=CoIAResponse)
async def research_company(request: ResearchRequest) -> CoIAResponse:
    """
    Handle research portal interface requests
    Specialized interface for company research and data enrichment
    """
    try:
        logger.info(f"Research request - Session: {request.session_id}, Company: {request.company_data.get('name')}")

        # Get unified COIA app
        app = await get_unified_coia_app()

        # Invoke research interface
        result = await invoke_coia_research(
            app=app,
            company_data=request.company_data,
            session_id=request.session_id
        )

        # Extract response message
        response_message = "Research completed successfully."
        if result.get("messages"):
            for msg in reversed(result["messages"]):
                if hasattr(msg, "type") and msg.type == "ai":
                    response_message = msg.content
                    break

        return CoIAResponse(
            success=True,
            response=response_message,
            current_mode=result.get("current_mode", "research"),
            interface="research_portal",
            session_id=request.session_id,
            contractor_profile=result.get("contractor_profile"),
            profile_completeness=result.get("profile_completeness"),
            completion_ready=result.get("completion_ready", False),
            contractor_created=result.get("contractor_created", False),
            contractor_id=result.get("contractor_id"),
            research_completed=result.get("research_completed", False),
            research_findings=result.get("research_findings"),
            intelligence_data=result.get("intelligence_data"),
            last_updated=result.get("last_updated", datetime.now().isoformat()),
            transition_reason=result.get("transition_reason"),
            error_details=result.get("error_state")
        )

    except Exception as e:
        logger.error(f"Error in research request: {e}")
        return CoIAResponse(
            success=False,
            response="Research request failed. Please try again.",
            current_mode="research",
            interface="research_portal",
            session_id=request.session_id,
            error_details=str(e)
        )


# Intelligence Interface Endpoints
@router.post("/intelligence", response_model=CoIAResponse)
async def enhance_intelligence(request: IntelligenceRequest) -> CoIAResponse:
    """
    Handle intelligence dashboard interface requests
    Advanced interface for data enhancement and Google Places integration
    """
    try:
        logger.info(f"Intelligence request - Session: {request.session_id}, Company: {request.contractor_data.get('company_name')}")

        # Get unified COIA app
        app = await get_unified_coia_app()

        # Invoke intelligence interface
        result = await invoke_coia_intelligence(
            app=app,
            contractor_data=request.contractor_data,
            session_id=request.session_id
        )

        # Extract response message
        response_message = "Intelligence enhancement completed successfully."
        if result.get("messages"):
            for msg in reversed(result["messages"]):
                if hasattr(msg, "type") and msg.type == "ai":
                    response_message = msg.content
                    break

        return CoIAResponse(
            success=True,
            response=response_message,
            current_mode=result.get("current_mode", "intelligence"),
            interface="intelligence_dashboard",
            session_id=request.session_id,
            contractor_profile=result.get("contractor_profile"),
            profile_completeness=result.get("profile_completeness"),
            completion_ready=result.get("completion_ready", False),
            contractor_created=result.get("contractor_created", False),
            contractor_id=result.get("contractor_id"),
            research_completed=result.get("research_completed", False),
            research_findings=result.get("research_findings"),
            intelligence_data=result.get("intelligence_data"),
            last_updated=result.get("last_updated", datetime.now().isoformat()),
            transition_reason=result.get("transition_reason"),
            error_details=result.get("error_state")
        )

    except Exception as e:
        logger.error(f"Error in intelligence request: {e}")
        return CoIAResponse(
            success=False,
            response="Intelligence enhancement failed. Please try again.",
            current_mode="intelligence",
            interface="intelligence_dashboard",
            session_id=request.session_id,
            error_details=str(e)
        )


# Profile Management Endpoints
@router.post("/profile/progressive")
async def save_progressive_profile(request: dict) -> dict:
    """
    Save profile data progressively as contractor completes steps
    Updates different tables based on which step is being completed
    """
    try:
        from utils.database_simple import get_supabase_client
        supabase = await get_supabase_client()
        
        contractor_id = request.get("contractor_id")
        step = request.get("step")
        data = request.get("data")
        
        logger.info(f"Saving progressive profile - Contractor: {contractor_id}, Step: {step}")
        
        # Update appropriate tables based on step
        if step == "business":
            # Update contractor_leads table with business info
            await supabase.table("contractor_leads").upsert({
                "id": contractor_id,
                "company_name": data.get("company_name"),
                "website": data.get("website"),
                "phone": data.get("phone"),
                "email": data.get("email"),
                "address": data.get("address"),
                "years_in_business": data.get("years_in_business"),
                "updated_at": datetime.now().isoformat()
            }).execute()
            
        elif step == "service_area":
            # Update service area information
            await supabase.table("contractor_leads").update({
                "service_radius_miles": data.get("service_radius_miles"),
                "zip_codes": data.get("zip_codes"),
                "service_areas": data.get("service_areas"),
                "updated_at": datetime.now().isoformat()
            }).eq("id", contractor_id).execute()
            
        elif step == "services":
            # Update services and specialties
            await supabase.table("contractors").upsert({
                "id": contractor_id,
                "specialties": data.get("specialties", []),
                "updated_at": datetime.now().isoformat()
            }).execute()
            
            # Also update contractor_leads with project types
            await supabase.table("contractor_leads").update({
                "project_types": data.get("specialties", []),
                "min_project_size": data.get("min_project_size"),
                "max_project_size": data.get("max_project_size"),
                "updated_at": datetime.now().isoformat()
            }).eq("id", contractor_id).execute()
        
        # Calculate profile completeness
        completeness = await calculate_profile_completeness(contractor_id, supabase)
        
        return {
            "success": True,
            "profile_completeness": completeness,
            "next_step": get_next_incomplete_step(contractor_id, completeness)
        }
        
    except Exception as e:
        logger.error(f"Error saving progressive profile: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def calculate_profile_completeness(contractor_id: str, supabase) -> float:
    """Calculate how complete a contractor's profile is"""
    try:
        # Get contractor data from both tables
        contractor = await supabase.table("contractors").select("*").eq("id", contractor_id).single().execute()
        contractor_lead = await supabase.table("contractor_leads").select("*").eq("id", contractor_id).single().execute()
        
        # Define required fields and their weights
        required_fields = {
            "company_name": 10,
            "email": 10,
            "phone": 10,
            "website": 5,
            "address": 5,
            "service_radius_miles": 10,
            "zip_codes": 5,
            "specialties": 15,
            "years_in_business": 5,
            "license_number": 10,
            "insurance_verified": 10,
            "min_project_size": 5
        }
        
        total_weight = sum(required_fields.values())
        completed_weight = 0
        
        # Check contractor table fields
        if contractor.data:
            for field, weight in required_fields.items():
                if field in ["specialties"]:
                    if contractor.data.get(field):
                        completed_weight += weight
        
        # Check contractor_leads table fields
        if contractor_lead.data:
            for field, weight in required_fields.items():
                if field not in ["specialties"]:
                    if contractor_lead.data.get(field):
                        completed_weight += weight
        
        return round((completed_weight / total_weight) * 100, 1)
        
    except:
        return 0.0


def get_next_incomplete_step(contractor_id: str, completeness: float) -> str:
    """Determine the next step the contractor should complete"""
    if completeness < 30:
        return "business"
    elif completeness < 60:
        return "service_area"
    elif completeness < 80:
        return "services"
    elif completeness < 100:
        return "credentials"
    else:
        return "complete"


# System Status and Management Endpoints
@router.get("/status")
async def get_system_status() -> dict[str, Any]:
    """Get unified COIA system status"""
    try:
        global _unified_coia_app

        # Check if system is initialized
        system_initialized = _unified_coia_app is not None

        # Check capabilities
        import os
        capabilities = {
            "conversation": True,  # Always available
            "research": bool(os.getenv("PLAYWRIGHT_AVAILABLE", False)),
            "intelligence": bool(os.getenv("GOOGLE_PLACES_API_KEY")),
            "memory": bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"))
        }

        return {
            "status": "operational" if system_initialized else "initializing",
            "system_initialized": system_initialized,
            "capabilities": capabilities,
            "interfaces": ["chat", "research_portal", "intelligence_dashboard"],
            "version": "1.0.0",
            "last_check": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }


@router.post("/restart")
async def restart_system(background_tasks: BackgroundTasks) -> dict[str, Any]:
    """Restart the unified COIA system"""
    try:
        global _unified_coia_app

        def restart_task():
            global _unified_coia_app
            _unified_coia_app = None
            logger.info("Unified COIA system marked for restart")

        background_tasks.add_task(restart_task)

        return {
            "status": "restart_initiated",
            "message": "System will reinitialize on next request",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error restarting system: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Bid Card Link Interface Endpoint
@router.post("/bid-card-link", response_model=CoIAResponse)
async def bid_card_link_conversation(request: BidCardLinkRequest) -> CoIAResponse:
    """
    Handle bid card link entry point for contractors
    Specialized interface for contractors accessing projects through email campaigns
    """
    try:
        logger.info(f"Bid card link request - Bid Card: {request.bid_card_id}, Contractor: {request.contractor_lead_id}")
        
        # Get unified COIA app
        app = await get_unified_coia_app()
        
        # Create initial message for bid card link
        user_message = f"I'm interested in learning more about this project (ID: {request.bid_card_id})"
        
        # Store bid_card_id in session for later use
        if not request.session_id:
            request.session_id = f"bidcard-{request.bid_card_id[:8]}"
        
        # Invoke bid card link interface with proper parameters
        # DeepAgents branch (flag-controlled) with graceful fallback
        import os as _os2
        use_da_bid = _os2.getenv("USE_DEEPAGENTS_BIDCARD", "").lower() == "true"
        if use_da_bid:
            try:
                from agents.coia.bidcard_deepagent import get_agent as _get_bidcard_agent
                from agents.coia.deepagents_tools import get_contractor_context as _get_ctx
                agent = _get_bidcard_agent()
                ctx = _get_ctx(request.contractor_lead_id, request.session_id)
                da_messages = [{"role": "user", "content": user_message}]
                da_input = {"messages": da_messages, "context": ctx}
                da_result = agent.invoke(da_input)
                result = da_result if isinstance(da_result, dict) else {"messages": [], "contractor_profile": None}
                logger.info("✅ DeepAgents bid-card path executed")
            except Exception as da_err2:
                logger.error(f"DeepAgents bid-card failed, falling back to LangGraph: {da_err2}")
                result = await invoke_coia_bid_card_link(
                    app=app,
                    user_message=user_message,
                    session_id=request.session_id,
                    contractor_lead_id=request.contractor_lead_id,
                    verification_token=request.verification_token,
                    source_channel="bid_card_link"
                )
        else:
            result = await invoke_coia_bid_card_link(
                app=app,
                user_message=user_message,
                session_id=request.session_id,
                contractor_lead_id=request.contractor_lead_id,
                verification_token=request.verification_token,
                source_channel="bid_card_link"
            )
        
        # Extract response message
        response_message = ""
        if result.get("messages"):
            # Get the last AI message
            for msg in reversed(result["messages"]):
                if (hasattr(msg, "type") and msg.type == "ai") or (hasattr(msg, "__class__") and "AI" in msg.__class__.__name__):
                    response_message = msg.content
                    break
        
        # Build response
        response_dict = {
            "success": True,
            "response": response_message,
            "current_mode": result.get("current_mode", "conversation"),
            "interface": "bid_card_link",
            "session_id": result.get("session_id", request.session_id),
            "contractor_profile": result.get("contractor_profile"),
            "profile_completeness": result.get("profile_completeness"),
            "completion_ready": result.get("completion_ready", False),
            "contractor_created": result.get("contractor_created", False),
            "contractor_id": result.get("contractor_id"),
            "research_completed": result.get("research_completed", False),
            "research_findings": result.get("research_findings"),
            "intelligence_data": result.get("intelligence_data"),
            "last_updated": result.get("last_updated", datetime.now().isoformat()),
            "transition_reason": result.get("transition_reason"),
            "error_details": result.get("error_state"),
        }

        # Add bid cards if available
        if result.get("bid_cards_attached"):
            response_dict["bidCards"] = result.get("bid_cards_attached")
            
        return CoIAResponse(**response_dict)
        
    except Exception as e:
        logger.error(f"Error in bid card link conversation: {e}")
        return CoIAResponse(
            success=False,
            response="I apologize, but I'm having trouble processing your bid card link request right now. Please try again.",
            current_mode="conversation",
            interface="bid_card_link",
            session_id=request.session_id or "error-session",
            error_details=str(e)
        )


# Health Check Endpoint
@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "unified_coia",
        "timestamp": datetime.now().isoformat()
    }


# Export router
__all__ = ["router"]
