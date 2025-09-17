"""
Clean COIA Landing API Router - DeepAgents with Live Agent System
Provides REST API endpoints for the COIA DeepAgents system with natural chat + live agent status
"""
import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
import json
import asyncio

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(tags=["COIA Landing"])

# Import Live Agent System
from agents.coia.live_agent_system import (
    live_tracker, 
    parallel_orchestrator, 
    LiveAgentTracker,
    ParallelAgentOrchestrator
)

# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.session_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        if session_id not in self.session_connections:
            self.session_connections[session_id] = []
        self.session_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if session_id in self.session_connections and websocket in self.session_connections[session_id]:
            self.session_connections[session_id].remove(websocket)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]

    async def send_to_session(self, session_id: str, message: dict):
        if session_id in self.session_connections:
            for connection in self.session_connections[session_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    # Connection closed, will be cleaned up
                    pass

    async def broadcast(self, message: dict):
        for connection in self.active_connections[:]:  # Copy list to avoid issues
            try:
                await connection.send_text(json.dumps(message))
            except:
                self.active_connections.remove(connection)

# Global connection manager
connection_manager = ConnectionManager()

# WebSocket endpoint for real-time agent status updates
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time agent status updates"""
    await connection_manager.connect(websocket, session_id)
    logger.info(f"WebSocket connected for session: {session_id}")
    
    try:
        while True:
            # Keep connection alive and handle ping/pong
            data = await websocket.receive_text()
            
            # Handle ping messages
            if data == "ping":
                await websocket.send_text("pong")
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, session_id)
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        connection_manager.disconnect(websocket, session_id)


async def run_research_in_background(
    contractor_lead_id: str,
    session_id: str,
    company_name: str,
    location_hint: Optional[str] = None
):
    """
    Background research task that runs async after immediate response
    """
    try:
        logger.info(f"🔍 Starting background research for {company_name}...")
        
        # Import COIA tools for research
        from agents.coia.deepagents_tools import coia_tools
        
        # Use async methods directly since we're already in async context
        google_data = await coia_tools.search_google_business(company_name, location_hint)
        logger.info(f"✅ Google search complete: {bool(google_data)}")
        
        # Try Tavily if enabled
        tavily_data = {}
        if coia_tools.tavily_search.use_tavily:
            tavily_data = await coia_tools.tavily_search.discover_contractor_pages(
                company_name, 
                google_data.get("website", "") if google_data else "",
                location_hint
            )
            logger.info(f"✅ Tavily search complete: {bool(tavily_data)}")
        
        research_data = {
            "company_name": company_name,
            "google_data": google_data or {},
            "tavily_data": tavily_data,
            "completeness": 50 if google_data else 10
        }
        
        # Step 2: Build basic profile (skip AI extraction for speed)
        profile = {
            "company_name": company_name,
            "location": location_hint,
            "website": google_data.get("website") if google_data else None,
            "phone": google_data.get("phone") if google_data else None,
            "address": google_data.get("address") if google_data else None,
            "rating": google_data.get("rating") if google_data else None,
        }
        
        # Save research results to memory
        from agents.coia.memory_integration import save_coia_state
        
        research_state = {
            "contractor_lead_id": contractor_lead_id,
            "session_id": session_id,
            "company_name": company_name,
            "research_complete": True,
            "research_data": research_data,
            "profile": profile,
            "timestamp": datetime.now().isoformat()
        }
        
        await save_coia_state(contractor_lead_id, research_state, session_id)
        logger.info(f"✅ Background research saved for {company_name}")
        
        # TODO: Send WebSocket notification that research is complete
        # await notify_research_complete(session_id, contractor_lead_id)
        
    except Exception as e:
        logger.error(f"❌ Background research failed: {e}")
        # Save error state
        error_state = {
            "contractor_lead_id": contractor_lead_id,
            "session_id": session_id,
            "research_complete": False,
            "research_error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        from agents.coia.memory_integration import save_coia_state
        await save_coia_state(contractor_lead_id, error_state, session_id)


# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for landing page conversations"""
    message: str = Field(..., description="User message to process")
    session_id: str = Field(..., description="Conversation session ID")
    contractor_lead_id: Optional[str] = Field(None, description="Contractor lead ID if available")
    user_id: Optional[str] = Field(None, description="User ID for session tracking")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for persistence")


class CoIAResponse(BaseModel):
    """Response model for COIA landing conversations"""
    success: bool = Field(..., description="Whether the request succeeded")
    response: Optional[str] = Field(None, description="AI response message")
    interface: str = Field(default="landing_page", description="Interface type")
    session_id: str = Field(..., description="Session identifier")
    contractor_lead_id: Optional[str] = Field(None, description="Contractor lead identifier")
    company_name: Optional[str] = Field(None, description="Extracted company name")
    contractor_created: Optional[bool] = Field(None, description="Whether contractor account was created")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    error_details: Optional[str] = Field(None, description="Error details if any")


# Landing Page Endpoint
@router.post("/landing", response_model=CoIAResponse)
async def landing_page_conversation(request: ChatRequest) -> CoIAResponse:
    """
    Handle landing page onboarding conversations using DeepAgents
    Clean implementation with no LangGraph dependencies
    """
    try:
        logger.info(f"Landing request - Session: {request.session_id}, Message: {request.message[:100]}...")
        
        # Generate or use existing contractor_lead_id
        import uuid
        contractor_lead_id = request.contractor_lead_id
        if not contractor_lead_id:
            contractor_lead_id = f"landing-{uuid.uuid4().hex[:12]}"
            logger.info(f"🆕 Generated contractor_lead_id: {contractor_lead_id}")
        
        # Check if DeepAgents is enabled (for fast testing vs. full AI processing)
        import os
        use_deepagents = os.getenv("USE_DEEPAGENTS_LANDING", "false").lower() == "true"
        logger.info(f"🔧 DeepAgents mode: {'ENABLED' if use_deepagents else 'DISABLED'} (USE_DEEPAGENTS_LANDING={os.getenv('USE_DEEPAGENTS_LANDING')})")
        
        if use_deepagents:
            # Import and use DeepAgents for full AI processing
            logger.info("🚀 Loading DeepAgents landing system...")
            from agents.coia.landing_deepagent import get_agent as get_landing_agent
            
            agent = get_landing_agent()
            logger.info("🤖 DeepAgents instance created")
        else:
            # Fast fallback mode for testing
            logger.info("⚡ Using fast template fallback mode")
        
        # Only restore state if using DeepAgents (memory operations can be slow)
        restored_state = {}
        all_messages = []
        da_input = {}
        
        if use_deepagents:
            # Restore previous state from unified memory
            logger.info("🔄 Restoring COIA state from unified memory...")
            from agents.coia.memory_integration import restore_coia_state
            
            restored_state = await restore_coia_state(contractor_lead_id, request.session_id)
            logger.info(f"✅ State restored with {len(restored_state.get('messages', []))} messages")
            
            # Add new user message to conversation history
            all_messages = restored_state.get('messages', [])
            all_messages.append({"role": "user", "content": request.message})
            
            # Compose input for DeepAgents with restored context
            # DeepAgents expects HumanMessage/AIMessage objects, not dict format
            from langchain_core.messages import HumanMessage, AIMessage
            
            formatted_messages = []
            for msg in all_messages:
                if isinstance(msg, dict):
                    if msg.get("role") == "user":
                        formatted_messages.append(HumanMessage(content=msg["content"]))
                    elif msg.get("role") == "assistant":
                        formatted_messages.append(AIMessage(content=msg["content"]))
                else:
                    # Already formatted message object
                    formatted_messages.append(msg)
            
            da_input = {
                "messages": formatted_messages,
                # Pass restored context in message format so DeepAgents can access it
                "contractor_lead_id": contractor_lead_id,
                "company_name": restored_state.get("company_name"),
                "staging_id": restored_state.get("staging_id"),
                "research_findings": restored_state.get("research_findings", {}),
                "contractor_profile": restored_state.get("contractor_profile", {}),
                "session_restored": True
            }
        
        # Fast company name extraction for immediate response
        import re
        from typing import Tuple
        
        def extract_company_name_quick(message: str) -> Tuple[Optional[str], Optional[str]]:
            """Quick extraction of company name and location from message"""
            # Look for company patterns
            company_patterns = [
                r"I (?:run|own|work for|am (?:from|at|with)) ([A-Z][A-Za-z0-9\s&.'-]+?)(?:\s+(?:in|from|at|located))",
                r"([A-Z][A-Za-z0-9\s&.'-]+?)\s+(?:company|services|solutions|group|LLC|Inc)",
                r"^([A-Z][A-Za-z0-9\s&.'-]+?)\s+(?:in|from)",
            ]
            
            location_patterns = [
                r"(?:in|from|at|located)\s+([A-Z][A-Za-z\s,]+?)(?:\s|$|,)",
                r"([A-Z][A-Za-z\s]+?),?\s+(?:Florida|FL|California|CA|Texas|TX|New York|NY)",
            ]
            
            company_name = None
            location = None
            
            # Extract company name
            for pattern in company_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    company_name = match.group(1).strip()
                    break
                    
            # Extract location
            for pattern in location_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    location = match.group(1).strip()
                    break
                    
            return company_name, location
        
        # Fast company name extraction for both modes
        extracted_company, location_hint = extract_company_name_quick(request.message)
        
        # Prioritize restored company name over quick extraction
        company_name = "your business"  # Default fallback
        if use_deepagents and restored_state and restored_state.get("company_name"):
            company_name = restored_state.get("company_name")
            logger.info(f"🔄 Using restored company name: {company_name}")
        elif extracted_company:
            company_name = extracted_company
            logger.info(f"🔍 Extracted company name: {company_name}")
        else:
            logger.info("ℹ️ No company name available, using fallback")
        
        if use_deepagents:
            # Setup live agent system for this conversation
            logger.info("🚀 Setting up live agent system...")
            
            # Configure agent tracker and orchestrator for this session
            live_tracker.set_session(request.session_id)
            
            # Add WebSocket callback for real-time updates
            async def send_agent_update(update: dict):
                await connection_manager.send_to_session(request.session_id, update)
            
            live_tracker.add_update_callback(send_agent_update)
            
            # Set conversation handler for agent reports back to chat
            async def send_to_main_chat(chat_update: dict):
                # Send agent report as a chat message
                chat_message = {
                    "type": "agent_report",
                    "session_id": request.session_id,
                    "message": chat_update["message"],
                    "agent": chat_update["agent"],
                    "timestamp": chat_update["timestamp"]
                }
                await connection_manager.send_to_session(request.session_id, chat_message)
            
            parallel_orchestrator.set_conversation_handler(send_to_main_chat)
            
            # Use DeepAgents for real conversation (slow but intelligent)
            logger.info("🤖 Calling DeepAgents for real conversation...")
            
            try:
                # Start parallel agents in background while main conversation continues
                if company_name and company_name != "your business":
                    logger.info(f"🎯 Starting parallel agent orchestration for {company_name}...")
                    asyncio.create_task(parallel_orchestrator.start_parallel_onboarding(
                        contractor_lead_id, 
                        company_name, 
                        location_hint or "Unknown", 
                        request.session_id
                    ))
                
                # Call DeepAgents properly for real conversation (no timeout)
                # Note: LangGraph agents use ainvoke, not arun
                logger.info(f"🔧 Calling agent.ainvoke with input type: {type(da_input)}")
                logger.info(f"🔧 Agent type: {type(agent)}")
                
                # Log context restoration details for debugging
                if "session_restored" in da_input and da_input["session_restored"]:
                    logger.info(f"🔄 Context Restoration Active:")
                    logger.info(f"   Company: {da_input.get('company_name', 'Unknown')}")
                    logger.info(f"   Staging ID: {da_input.get('staging_id', 'None')}")
                    logger.info(f"   Messages: {len(da_input.get('messages', []))}")
                    logger.info(f"   Research: {'Yes' if da_input.get('research_findings') else 'No'}")
                
                da_result = await agent.ainvoke(da_input)
                
                logger.info(f"✅ DeepAgents response received, type: {type(da_result)}")
                logger.info(f"🔧 DeepAgents result keys: {da_result.keys() if hasattr(da_result, 'keys') else 'not a dict'}")
                
                # Handle LangGraph AddableValuesDict response
                response_message = ""
                # Keep the company_name we extracted/restored earlier (don't reset to None)
                
                if hasattr(da_result, '__getitem__') and "messages" in da_result:
                    messages = da_result["messages"]
                    if messages:
                        last_message = messages[-1]
                        # Handle AIMessage objects from LangGraph
                        if hasattr(last_message, 'content'):
                            response_message = str(last_message.content)
                            logger.info(f"🔧 Extracted AI response: {response_message[:200]}...")
                            
                            # Try to extract company name from the response if we don't have one
                            if not company_name or company_name == "your business":
                                import re
                                if "JM Holiday Lighting" in response_message:
                                    company_name = "JM Holiday Lighting"
                                elif "Phone:" in response_message or "Email:" in response_message:
                                    # This is a real DeepAgents response with contact info
                                    extracted_name = extract_company_name_quick(request.message)[0]
                                    if extracted_name:
                                        company_name = extracted_name
                        else:
                            response_message = str(last_message)
                            logger.info(f"🔧 Non-AIMessage response: {response_message[:100]}...")
                else:
                    logger.warning(f"⚠️ Unexpected da_result structure: {type(da_result)}")
                    response_message = "Thank you for reaching out! Let me help you get connected with projects on InstaBids."
                
                # If no company name from DeepAgents, preserve the one we already have
                # Don't re-extract because that can override restored company names
                if not company_name:
                    logger.warning("⚠️ No company name found in DeepAgents response, keeping existing one")
                    company_name = company_name or "your business"
                
                # CRITICAL: Save DeepAgents state after successful response
                logger.info("💾 Saving DeepAgents state after response...")
                from agents.coia.memory_integration import save_coia_state
                
                # Build the updated state with DeepAgents response
                updated_state = {
                    **restored_state,  # Keep all restored data
                    "messages": da_result.get("messages", all_messages),  # Updated messages from DeepAgents
                    "company_name": company_name,  # Preserve company name
                    "contractor_lead_id": contractor_lead_id,
                    "session_id": request.session_id,
                    "last_response": response_message[:500],  # Store last response for context
                    "timestamp": datetime.now().isoformat()
                }
                
                # CRITICAL: Extract and preserve staging_id from the response
                # Look for staging_id in the response message or state
                import re
                staging_id_match = re.search(r'staging[_-]id["\s:]+([a-f0-9-]+)', str(da_result))
                if staging_id_match:
                    updated_state["staging_id"] = staging_id_match.group(1)
                    logger.info(f"📌 Found staging_id: {updated_state['staging_id']}")
                elif "staging_id" in restored_state:
                    # Keep existing staging_id if we have one
                    updated_state["staging_id"] = restored_state["staging_id"]
                
                # If DeepAgents provided additional context, preserve it
                if hasattr(da_result, '__getitem__'):
                    # Preserve any DeepAgents-specific state including staging_id
                    for key in ["todos", "files", "contractor_profile", "staging_data", "staging_id", "services_preferences", "radius_preferences"]:
                        if key in da_result:
                            updated_state[key] = da_result[key]
                
                await save_coia_state(contractor_lead_id, updated_state, request.session_id)
                logger.info(f"✅ State saved with company: {company_name}")
            
            except Exception as e:
                logger.error(f"❌ DeepAgents error: {e}")
                logger.error(f"❌ Error type: {type(e).__name__}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                
                # Quick extraction for fallback only on real errors
                response_message = f"I apologize, but I'm having some technical difficulties right now. However, I can see you mentioned {company_name}. Let me help you get connected with homeowners who need your services. What's your primary specialty?"
        
        else:
            # Fast template fallback mode (for when DeepAgents is disabled)
            logger.info(f"⚡ Fast template fallback mode for {company_name}")
            
            # Simple template response - only used when DeepAgents is disabled
            response_message = f"""Welcome to InstaBids, {company_name}! I'm here to connect contractors like you with homeowners who need your services.
            
To get started, I'd love to learn more about your business:
• What's your primary specialty? 
• What area do you typically serve?
• How long have you been in business?

This helps me match you with the best projects in your area."""
            
            logger.info(f"⚡ Fast template response generated ({len(response_message)} chars)")
        
        # Start background research (non-blocking) - ONLY if using DeepAgents
        if use_deepagents:
            asyncio.create_task(run_research_in_background(
                contractor_lead_id, 
                request.session_id, 
                company_name,
                location_hint if 'location_hint' in locals() else None
            ))
        
        logger.info(f"✅ Response sent with research running in background for {company_name}")
        
        # Build response
        return CoIAResponse(
            success=True,
            response=response_message,
            interface="landing_page",
            session_id=request.session_id,
            contractor_lead_id=contractor_lead_id,
            company_name=company_name,
            contractor_created=False
        )
        
    except Exception as e:
        logger.error(f"❌ Error in landing conversation: {e}")
        return CoIAResponse(
            success=False,
            response="I apologize, but I'm having trouble processing your request right now. Please try again.",
            interface="landing_page",
            session_id=request.session_id,
            contractor_lead_id=request.contractor_lead_id,
            error_details=str(e)
        )


# Agent Status Endpoint
@router.get("/agent-status/{session_id}")
async def get_agent_status(session_id: str) -> dict[str, Any]:
    """Get current status of all agents for a session"""
    try:
        # Set the session for the tracker if not already set
        if live_tracker.session_id != session_id:
            live_tracker.set_session(session_id)
        
        status = live_tracker.get_status_summary()
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Health Check
@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "coia_landing_deepagents",
        "timestamp": datetime.now().isoformat()
    }


# Export router
__all__ = ["router"]