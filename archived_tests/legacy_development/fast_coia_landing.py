"""
Fast COIA Landing API - Immediate Response Architecture
Provides sub-2 second responses while processing DeepAgents in background
"""
import logging
from datetime import datetime
from typing import Any, Optional
import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import json

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(tags=["Fast COIA"])

class ChatRequest(BaseModel):
    """Request model for landing page conversations"""
    message: str = Field(..., description="User message to process")
    session_id: str = Field(..., description="Conversation session ID")
    contractor_lead_id: Optional[str] = Field(None, description="Contractor lead ID if available")
    user_id: Optional[str] = Field(None, description="User ID for session tracking")

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

def extract_company_name_quick(message: str) -> tuple[Optional[str], Optional[str]]:
    """Fast extraction of company name and location from message"""
    import re
    
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
    
    for pattern in company_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            company_name = match.group(1).strip()
            break
            
    for pattern in location_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            break
            
    return company_name, location

@router.post("/fast-landing", response_model=CoIAResponse)
async def fast_landing_conversation(request: ChatRequest) -> CoIAResponse:
    """
    FAST COIA landing endpoint - responds in under 2 seconds
    Processes DeepAgents and research in background after immediate response
    """
    try:
        logger.info(f"⚡ Fast landing request - Session: {request.session_id}")
        
        # Generate contractor_lead_id if needed
        import uuid
        contractor_lead_id = request.contractor_lead_id
        if not contractor_lead_id:
            contractor_lead_id = f"fast-{uuid.uuid4().hex[:12]}"
        
        # Fast company name extraction (immediate)
        company_name, location_hint = extract_company_name_quick(request.message)
        company_name = company_name or "your business"
        
        # Generate immediate intelligent response
        if company_name and company_name != "your business":
            response_message = f"""Welcome to InstaBids, {company_name}! I'm excited to help you connect with homeowners who need your services.

I'm already working behind the scenes to:
🔍 Research your business details and verify your information  
📊 Build your contractor profile with your specialties
🎯 Find matching projects in your area
💼 Prepare your account setup

While I'm gathering this information, could you tell me:
• What's your primary specialty?
• What area do you typically serve?
• How long have you been in business?

This helps me find the perfect projects for you!"""
        else:
            response_message = """Welcome to InstaBids! I'm here to help connect contractors like you with homeowners who need your services.

To get started, I'd love to learn about your business:
• What's your company name?
• What's your primary specialty? 
• What area do you typically serve?

Once I have these details, I can start finding great projects for you!"""

        # Start background processing AFTER response (non-blocking)
        if company_name and company_name != "your business":
            logger.info(f"🔧 Starting background processing for {company_name}")
            
            async def background_processing():
                """Background DeepAgents and research processing"""
                try:
                    logger.info(f"🔍 Background: Starting research for {company_name}")
                    
                    # Import DeepAgents and tools
                    from agents.coia.landing_deepagent import get_agent as get_landing_agent
                    from agents.coia.memory_integration import save_coia_state, restore_coia_state
                    
                    # Restore previous state
                    restored_state = await restore_coia_state(contractor_lead_id, request.session_id)
                    
                    # Prepare DeepAgents input
                    all_messages = restored_state.get('messages', [])
                    all_messages.append({"role": "user", "content": request.message})
                    
                    da_input = {
                        "messages": all_messages,
                        "context": restored_state
                    }
                    
                    # Process with DeepAgents (in background)
                    agent = get_landing_agent()
                    da_result = await agent.ainvoke(da_input)
                    
                    # Save state with DeepAgents results
                    updated_state = {
                        **restored_state,
                        "messages": da_result.get("messages", all_messages) if hasattr(da_result, '__getitem__') else all_messages,
                        "company_name": company_name,
                        "contractor_lead_id": contractor_lead_id,
                        "session_id": request.session_id,
                        "background_processed": True,
                        "fast_response_given": True,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Extract any staging_id or profile data
                    if hasattr(da_result, '__getitem__'):
                        for key in ["staging_id", "contractor_profile", "services_preferences"]:
                            if key in da_result:
                                updated_state[key] = da_result[key]
                    
                    await save_coia_state(contractor_lead_id, updated_state, request.session_id)
                    logger.info(f"✅ Background processing complete for {company_name}")
                    
                    # TODO: Send WebSocket notification that processing is complete
                    
                except Exception as e:
                    logger.error(f"❌ Background processing failed: {e}")
            
            # Start background task (non-blocking)
            asyncio.create_task(background_processing())
        
        # Return immediate response
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
        logger.error(f"❌ Fast landing error: {e}")
        return CoIAResponse(
            success=False,
            response="I apologize, but I'm having trouble right now. Please try again.",
            interface="landing_page", 
            session_id=request.session_id,
            contractor_lead_id=request.contractor_lead_id
        )

# Export router
__all__ = ["router"]