"""
Agent Context API Router
Provides privacy-filtered conversation context endpoints for all agents
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Import context adapters
from adapters.homeowner_context import HomeownerContextAdapter
from adapters.iris_context import IrisContextAdapter
from adapters.contractor_context import ContractorContextAdapter
from adapters.messaging_context import MessagingContextAdapter

# Import policy engine
from services.context_policy import context_policy, AgentType, PrivacySide

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize context adapters
homeowner_adapter = HomeownerContextAdapter()
iris_adapter = IrisContextAdapter()
contractor_adapter = ContractorContextAdapter()
messaging_adapter = MessagingContextAdapter()

# Pydantic models for API requests
class ContextRequest(BaseModel):
    agent_type: str
    user_id: str
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None
    include_cross_agent: bool = True

class CrossAgentContextRequest(BaseModel):
    requesting_agent: str
    user_id: str
    target_agents: Optional[List[str]] = None

class MessagingContextRequest(BaseModel):
    thread_id: str
    participants: List[Dict[str, Any]]
    message_type: str = "project_communication"

class MessageFilterRequest(BaseModel):
    message: Dict[str, Any]
    sender_side: str  # "homeowner" or "contractor"
    recipient_side: str  # "homeowner" or "contractor"

@router.get("/context/{agent_type}")
async def get_agent_context(
    agent_type: str,
    user_id: str = Query(...),
    project_id: Optional[str] = Query(None),
    conversation_id: Optional[str] = Query(None)
):
    """
    Get context for specific agent type with privacy filtering
    
    Available agent types:
    - CIA: Customer Interface Agent (homeowner-side)
    - IRIS: Design inspiration agent (homeowner-side)
    - HMA: Homeowner Management Agent (homeowner-side)
    - COIA: Contractor Interface Agent (contractor-side)
    - MESSAGING: Messaging system agent (neutral)
    """
    try:
        # Validate agent type
        try:
            agent_enum = AgentType(agent_type.upper())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid agent type: {agent_type}. Valid types: {[a.value for a in AgentType]}"
            )
        
        logger.info(f"Getting context for {agent_type} - user: {user_id}")
        
        # Route to appropriate adapter based on agent type
        if agent_enum in [AgentType.CIA, AgentType.HMA]:
            context = homeowner_adapter.get_agent_context(
                user_id=user_id,
                project_id=project_id,
                conversation_id=conversation_id,
                agent_type=agent_enum
            )
        elif agent_enum == AgentType.IRIS:
            context = iris_adapter.get_inspiration_context(
                user_id=user_id,
                project_id=project_id
            )
        elif agent_enum == AgentType.COIA:
            context = contractor_adapter.get_contractor_context(
                contractor_id=user_id,  # For contractor agents, user_id is contractor_id
                session_id=conversation_id
            )
        elif agent_enum == AgentType.BSA:
            # BSA uses same contractor context system as COIA
            context = contractor_adapter.get_contractor_context(
                contractor_id=user_id,  # For BSA agents, user_id is contractor_id
                session_id=conversation_id
            )
        elif agent_enum == AgentType.MESSAGING:
            # Messaging context requires different parameters - use separate endpoint
            raise HTTPException(
                status_code=400,
                detail="Use /messaging-context endpoint for messaging agent context"
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported agent type: {agent_type}")
        
        # Add metadata
        context["request_metadata"] = {
            "agent_type": agent_type,
            "user_id": user_id,
            "project_id": project_id,
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "privacy_filtered": True
        }
        
        return {
            "success": True,
            "context": context
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cross-agent-context")
async def get_cross_agent_context(request: CrossAgentContextRequest):
    """
    Get cross-agent context with privacy filtering
    
    Allows agents to access context from other agents while respecting privacy boundaries:
    - Same-side agents can share full context
    - Cross-side agents get privacy-filtered context
    - NEUTRAL agents get full access
    """
    try:
        # Validate requesting agent
        try:
            requesting_agent = AgentType(request.requesting_agent.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid requesting agent: {request.requesting_agent}"
            )
        
        logger.info(f"Getting cross-agent context for {requesting_agent.value}")
        
        # Get cross-agent context through policy engine
        context = context_policy.get_cross_agent_context(
            requesting_agent=requesting_agent,
            user_id=request.user_id,
            include_agent_types=[AgentType(a.upper()) for a in request.target_agents] if request.target_agents else None
        )
        
        return {
            "success": True,
            "requesting_agent": request.requesting_agent,
            "context": context,
            "privacy_note": "Context filtered based on agent privacy boundaries"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cross-agent context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messaging-context")
async def get_messaging_context(request: MessagingContextRequest):
    """
    Get messaging context for cross-side communication
    Only available to MESSAGING (neutral) agents
    """
    try:
        logger.info(f"Getting messaging context for thread: {request.thread_id}")
        
        context = messaging_adapter.get_messaging_context(
            thread_id=request.thread_id,
            participants=request.participants,
            message_type=request.message_type
        )
        
        return {
            "success": True,
            "thread_id": request.thread_id,
            "context": context
        }
        
    except Exception as e:
        logger.error(f"Error getting messaging context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/filter-message")
async def filter_message(request: MessageFilterRequest):
    """
    Apply privacy filtering to cross-side messages
    """
    try:
        logger.info(f"Filtering message from {request.sender_side} to {request.recipient_side}")
        
        filtered_message = messaging_adapter.apply_message_filtering(
            message=request.message,
            sender_side=request.sender_side,
            recipient_side=request.recipient_side
        )
        
        return {
            "success": True,
            "original_message": request.message,
            "filtered_message": filtered_message,
            "filtering_applied": True
        }
        
    except Exception as e:
        logger.error(f"Error filtering message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/{conversation_id}/access-check")
async def check_conversation_access(
    conversation_id: str,
    requesting_agent: str = Query(...),
    user_id: str = Query(...)
):
    """
    Check if an agent can access a specific conversation
    """
    try:
        # Validate requesting agent
        try:
            agent_enum = AgentType(requesting_agent.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent type: {requesting_agent}"
            )
        
        # TODO: Get conversation metadata from unified conversation system
        conversation_metadata = {
            "conversation_id": conversation_id,
            "participants": [{"type": "user", "id": user_id}],
            "agent_type": "CIA",  # Placeholder - would get from actual conversation
            "conversation_type": "project_setup"
        }
        
        # Check access through policy engine
        can_access = context_policy.can_access_conversation(
            requesting_agent=agent_enum,
            conversation_metadata=conversation_metadata
        )
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "requesting_agent": requesting_agent,
            "can_access": can_access,
            "privacy_boundary_enforced": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking conversation access: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/project/{project_id}/conversations")
async def get_project_conversations(
    project_id: str,
    requesting_agent: str = Query(...),
    user_id: str = Query(...)
):
    """
    Get all conversations for a specific project with privacy filtering
    """
    try:
        # Validate requesting agent
        try:
            agent_enum = AgentType(requesting_agent.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent type: {requesting_agent}"
            )
        
        logger.info(f"Getting project conversations for {requesting_agent} - project: {project_id}")
        
        # Route to appropriate adapter
        if agent_enum in [AgentType.CIA, AgentType.HMA]:
            conversations = homeowner_adapter.get_project_conversations(
                user_id=user_id,
                project_id=project_id,
                agent_type=agent_enum
            )
        else:
            # TODO: Implement for other agent types
            conversations = []
        
        return {
            "success": True,
            "project_id": project_id,
            "requesting_agent": requesting_agent,
            "conversations": conversations,
            "privacy_filtered": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/cross-project-insights")
async def get_cross_project_insights(
    user_id: str,
    requesting_agent: str = Query(...)
):
    """
    Get cross-project insights for intelligent agent questioning
    """
    try:
        # Validate requesting agent
        try:
            agent_enum = AgentType(requesting_agent.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent type: {requesting_agent}"
            )
        
        logger.info(f"Getting cross-project insights for {requesting_agent} - user: {user_id}")
        
        # Only homeowner-side agents should get cross-project insights
        if agent_enum in [AgentType.CIA, AgentType.HMA]:
            insights = homeowner_adapter.get_cross_project_insights(
                user_id=user_id,
                agent_type=agent_enum
            )
        else:
            insights = {"insights": [], "note": "Cross-project insights not available for this agent type"}
        
        return {
            "success": True,
            "user_id": user_id,
            "requesting_agent": requesting_agent,
            "insights": insights
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cross-project insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/privacy/policy-info")
async def get_privacy_policy_info():
    """
    Get information about the privacy policy and agent boundaries
    """
    try:
        return {
            "success": True,
            "privacy_policy": {
                "agent_sides": {
                    "homeowner_side": ["CIA", "IRIS", "HMA"],
                    "contractor_side": ["COIA"],
                    "neutral": ["MESSAGING", "ADMIN"]
                },
                "privacy_rules": [
                    "Homeowner agents cannot see contractor real names/contact info",
                    "Contractor agents cannot see homeowner real names/contact info", 
                    "Same-side agents can share full context",
                    "Cross-side sharing uses aliases only",
                    "Neutral agents can access all contexts for coordination"
                ],
                "alias_system": {
                    "contractors_see": "Project Owner",
                    "homeowners_see": "Contractor [ID]",
                    "purpose": "Protect personal identity until selection/hiring"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting privacy policy info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check for agent context API"""
    return {
        "status": "healthy",
        "service": "agent_context_api",
        "adapters": {
            "homeowner_adapter": "active",
            "iris_adapter": "active", 
            "contractor_adapter": "active",
            "messaging_adapter": "active"
        },
        "privacy_policy": "enforced",
        "version": "1.0"
    }