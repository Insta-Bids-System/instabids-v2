"""
JAA Routes - Job Assessment Agent API Endpoints
Owner: Agent 2 (Backend Core)
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

# Import JAA agent
from agents.jaa.agent import JobAssessmentAgent
# Import contractor notification service
from services.bid_card_change_notification_service import notify_contractors_of_bid_card_change


# Create router
router = APIRouter()

# Global JAA agent instance (initialized in main.py)
jaa_agent: Optional[JobAssessmentAgent] = None

def set_jaa_agent(agent: JobAssessmentAgent):
    """Set the JAA agent instance"""
    global jaa_agent
    jaa_agent = agent

@router.post("/process/{thread_id}")
async def process_with_jaa(thread_id: str):
    """Process CIA conversation with JAA to generate bid card"""
    if not jaa_agent:
        raise HTTPException(500, "JAA agent not initialized")

    try:
        result = await jaa_agent.process_conversation(thread_id)

        if result["success"]:
            return {
                "success": True,
                "bid_card_number": result["bid_card_number"],
                "bid_card_data": result["bid_card_data"],
                "cia_thread_id": result["cia_thread_id"],
                "database_id": result["database_id"]
            }
        else:
            raise HTTPException(500, result.get("error", "Unknown error processing conversation"))

    except Exception as e:
        print(f"[JAA API ERROR] {e}")
        raise HTTPException(500, f"JAA processing failed: {e!s}")

@router.put("/update/{bid_card_id}")
async def update_bid_card_with_jaa(bid_card_id: str, update_request: dict):
    """Update existing bid card with intelligent analysis and contractor notification"""
    if not jaa_agent:
        raise HTTPException(500, "JAA agent not initialized")

    try:
        # Update bid card via JAA
        result = await jaa_agent.update_existing_bid_card(bid_card_id, update_request)

        if not result["success"]:
            raise HTTPException(500, result.get("error", "Unknown error updating bid card"))

        # NEW: Notify engaged contractors about the change
        notification_result = await notify_contractors_of_bid_card_change(
            bid_card_id=bid_card_id,
            change_type=determine_change_type(update_request),
            description=result.get("update_summary", "Project has been updated"),
            previous_value=result.get("previous_value"),
            new_value=result.get("new_value")
        )

        return {
            "success": True,
            "bid_card_id": result["bid_card_id"],
            "update_summary": result["update_summary"],
            "affected_contractors": result["affected_contractors"],
            "notification_content": result["notification_content"],
            "next_actions": result["next_actions"],
            "updated_at": result["updated_at"],
            "updated_by": result["updated_by"],
            # NEW: Contractor notification results
            "contractor_notifications": {
                "success": notification_result["success"],
                "contractors_notified": notification_result.get("contractors_notified", 0),
                "engagement_breakdown": notification_result.get("engagement_breakdown", {}),
                "error": notification_result.get("error")
            }
        }

    except Exception as e:
        print(f"[JAA UPDATE API ERROR] {e}")
        raise HTTPException(500, f"JAA bid card update failed: {e!s}")


def determine_change_type(update_request: dict) -> str:
    """Determine the type of change based on update request"""
    if "budget" in update_request or "budget_min" in update_request or "budget_max" in update_request:
        return "budget_change"
    elif "scope" in update_request or "description" in update_request or "project_description" in update_request:
        return "scope_change" 
    elif "urgency" in update_request or "timeline" in update_request or "deadline" in update_request:
        return "deadline_change"
    elif "location" in update_request or "address" in update_request:
        return "location_change"
    elif "requirements" in update_request or "specifications" in update_request:
        return "requirements_change"
    else:
        return "general_update"
