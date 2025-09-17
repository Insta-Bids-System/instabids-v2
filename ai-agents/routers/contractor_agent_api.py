"""
Simplified Contractor Agent API
Single endpoint for all contractor interactions - pre and post signup
"""

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.coia.supabase_checkpointer import create_supabase_checkpointer
from agents.coia.unified_graph import create_unified_coia_system


logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/contractor", tags=["Contractor Agent"])

# Global app instance
_contractor_agent = None


async def get_contractor_agent():
    """Get or create the contractor agent"""
    global _contractor_agent

    if _contractor_agent is None:
        logger.info("Initializing contractor agent system...")
        try:
            checkpointer = await create_supabase_checkpointer()
            _contractor_agent = await create_unified_coia_system(checkpointer)
            logger.info("Contractor agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize contractor agent: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize agent")

    return _contractor_agent


class ContractorConversation(BaseModel):
    """Single request model for all contractor conversations"""
    message: str = Field(..., description="Message from contractor")
    contractor_id: Optional[str] = Field(None, description="Contractor ID if logged in")
    session_id: Optional[str] = Field(None, description="Conversation session ID")
    context: Optional[dict[str, Any]] = Field(None, description="Additional context")


class ContractorResponse(BaseModel):
    """Response for contractor conversations"""
    success: bool
    response: str
    session_id: str

    # Context about the conversation
    is_onboarding: bool = Field(False, description="Whether this is onboarding conversation")
    is_authenticated: bool = Field(False, description="Whether contractor is logged in")

    # Onboarding specific
    onboarding_stage: Optional[str] = None
    profile_completeness: Optional[float] = None
    contractor_created: Optional[bool] = None

    # Post-signup specific
    available_projects: Optional[int] = None
    active_bids: Optional[int] = None

    # Metadata
    timestamp: str
    error: Optional[str] = None


@router.post("/conversation", response_model=ContractorResponse)
async def contractor_conversation(request: ContractorConversation) -> ContractorResponse:
    """
    Single endpoint for ALL contractor interactions
    Automatically detects context and provides appropriate responses
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid4())

        # Detect conversation context
        is_authenticated = bool(request.contractor_id)
        is_onboarding = not is_authenticated

        logger.info(f"Contractor conversation - Session: {session_id}, "
                   f"Authenticated: {is_authenticated}, Message: {request.message[:50]}...")

        # Get the unified agent
        app = await get_contractor_agent()

        # Build the input for LangGraph
        input_data = {
            "messages": [{"role": "human", "content": request.message}],
            "session_id": session_id,
            "contractor_id": request.contractor_id,
            "is_authenticated": is_authenticated,
            "is_onboarding": is_onboarding,
            "current_mode": "conversation",  # Always start in conversation mode
            "last_updated": datetime.now().isoformat()
        }

        # Add any additional context
        if request.context:
            input_data.update(request.context)

        # Process through LangGraph with automatic mode switching
        # The graph will automatically:
        # 1. Detect if research is needed (e.g., looking up company info)
        # 2. Switch to intelligence mode for enrichment (e.g., Google Places)
        # 3. Return to conversation mode with enhanced context
        result = await app.ainvoke(
            input_data,
            config={"configurable": {"thread_id": session_id}}
        )

        # Extract the response
        response_message = ""
        if result.get("messages"):
            for msg in reversed(result["messages"]):
                if hasattr(msg, "role") and msg.role == "assistant":
                    response_message = msg.content
                    break

        # Build response based on context
        response = ContractorResponse(
            success=True,
            response=response_message,
            session_id=session_id,
            is_onboarding=is_onboarding,
            is_authenticated=is_authenticated,
            timestamp=datetime.now().isoformat()
        )

        # Add onboarding-specific data if applicable
        if is_onboarding:
            response.onboarding_stage = result.get("current_stage", "welcome")
            response.profile_completeness = result.get("profile_completeness")
            response.contractor_created = result.get("contractor_created", False)

        # Add post-signup data if authenticated
        if is_authenticated:
            # TODO: Query available projects and active bids
            response.available_projects = result.get("available_projects", 0)
            response.active_bids = result.get("active_bids", 0)

        return response

    except Exception as e:
        logger.error(f"Error in contractor conversation: {e}")
        return ContractorResponse(
            success=False,
            response="I'm having trouble processing your request. Please try again.",
            session_id=request.session_id or str(uuid4()),
            is_onboarding=not bool(request.contractor_id),
            is_authenticated=bool(request.contractor_id),
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


@router.get("/session/{session_id}")
async def get_session_state(session_id: str) -> dict[str, Any]:
    """Get current state of a contractor conversation session"""
    try:
        # TODO: Load from checkpointer
        return {
            "session_id": session_id,
            "status": "active",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting session state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_agent_status() -> dict[str, Any]:
    """Get contractor agent system status"""
    try:
        import os

        return {
            "status": "operational",
            "capabilities": {
                "conversation": True,
                "research": bool(os.getenv("PLAYWRIGHT_AVAILABLE")),
                "intelligence": bool(os.getenv("GOOGLE_PLACES_API_KEY")),
                "memory": bool(os.getenv("SUPABASE_URL"))
            },
            "contexts_supported": ["onboarding", "bidding", "project_management"],
            "version": "2.0.0",  # Simplified version
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Export router
__all__ = ["router"]
