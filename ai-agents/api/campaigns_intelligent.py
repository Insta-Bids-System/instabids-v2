#!/usr/bin/env python3
"""
Intelligent Campaign API Endpoints
Integrates timing engine with campaign creation and monitoring
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from agents.orchestration.check_in_manager import CampaignCheckInManager
from agents.orchestration.enhanced_campaign_orchestrator import (
    CampaignRequest,
    EnhancedCampaignOrchestrator,
)


# Create router
router = APIRouter(prefix="/api/campaigns", tags=["intelligent-campaigns"])

# Initialize orchestrators
enhanced_orchestrator = EnhancedCampaignOrchestrator()
check_in_manager = CampaignCheckInManager()


# Request/Response Models
class CreateIntelligentCampaignRequest(BaseModel):
    """Request to create an intelligent campaign"""
    bid_card_id: str
    project_type: str
    location: dict[str, str]  # city, state, zip
    timeline_hours: int
    urgency_level: str  # emergency, urgent, standard, flexible, planning
    bids_needed: int = 4
    channels: Optional[list[str]] = None


class CheckInResponse(BaseModel):
    """Response from a campaign check-in"""
    campaign_id: str
    check_in_number: int
    bids_expected: int
    bids_received: int
    performance_ratio: float
    on_track: bool
    escalation_triggered: bool
    actions_taken: list[str]
    recommendations: list[str]


@router.post("/create-intelligent")
async def create_intelligent_campaign(
    request: CreateIntelligentCampaignRequest,
    background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """
    Create a campaign with intelligent contractor selection

    This endpoint:
    1. Analyzes contractor availability by tier
    2. Calculates optimal outreach strategy
    3. Selects specific contractors
    4. Creates campaign with check-in schedule
    5. Starts background monitoring
    """
    try:
        # Create campaign request
        campaign_request = CampaignRequest(
            bid_card_id=request.bid_card_id,
            project_type=request.project_type,
            location=request.location,
            timeline_hours=request.timeline_hours,
            urgency_level=request.urgency_level,
            bids_needed=request.bids_needed,
            channels=request.channels
        )

        # Create intelligent campaign
        result = await enhanced_orchestrator.create_intelligent_campaign(campaign_request)

        if result.get("success"):
            # Start execution in background
            background_tasks.add_task(
                enhanced_orchestrator.execute_campaign_with_monitoring,
                result["campaign_id"]
            )

            return {
                "success": True,
                "campaign_id": result["campaign_id"],
                "strategy": result["strategy"],
                "check_ins": result["check_ins"],
                "message": "Campaign created and execution started"
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}/status")
async def get_campaign_status(campaign_id: str) -> dict[str, Any]:
    """
    Get real-time campaign status including performance metrics
    """
    try:
        # Get base campaign status
        status = enhanced_orchestrator.base_orchestrator.get_campaign_status(campaign_id)

        if not status.get("success"):
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Get performance data from database
        performance_result = enhanced_orchestrator.supabase.rpc(
            "calculate_campaign_performance",
            {"p_campaign_id": campaign_id}
        ).execute()

        if performance_result.data:
            performance = performance_result.data[0]
            status["performance"] = {
                "total_contractors": performance.get("total_contractors", 0),
                "contacted": performance.get("contacted", 0),
                "responded": performance.get("responded", 0),
                "bids_submitted": performance.get("bids_submitted", 0),
                "current_response_rate": float(performance.get("current_response_rate", 0)),
                "projected_final_bids": performance.get("projected_final_bids", 0)
            }

        # Get next check-in
        check_ins = enhanced_orchestrator.supabase.table("campaign_check_ins")\
            .select("*")\
            .eq("campaign_id", campaign_id)\
            .is_("completed_at", "null")\
            .order("scheduled_at")\
            .limit(1)\
            .execute()

        if check_ins.data:
            next_check_in = check_ins.data[0]
            status["next_check_in"] = {
                "scheduled_at": next_check_in["scheduled_at"],
                "check_in_number": next_check_in["check_in_number"],
                "expected_bids": next_check_in["expected_bids"]
            }

        return status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/check-in")
async def perform_manual_check_in(campaign_id: str) -> CheckInResponse:
    """
    Manually trigger a campaign check-in
    """
    try:
        # Perform check-in
        status = await check_in_manager.perform_check_in(campaign_id)

        return CheckInResponse(
            campaign_id=campaign_id,
            check_in_number=status.check_in_number,
            bids_expected=status.bids_expected,
            bids_received=status.bids_received,
            performance_ratio=status.performance_ratio,
            on_track=status.on_track,
            escalation_triggered=status.escalation_needed,
            actions_taken=status.actions_taken,
            recommendations=status.recommendations
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}/timeline")
async def get_campaign_timeline(campaign_id: str) -> dict[str, Any]:
    """
    Get campaign timeline with all events and check-ins
    """
    try:
        # Get campaign details
        campaign_result = enhanced_orchestrator.supabase.table("outreach_campaigns")\
            .select("*, bid_cards!inner(*)")\
            .eq("id", campaign_id)\
            .single()\
            .execute()

        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")

        campaign = campaign_result.data

        # Get all check-ins
        check_ins_result = enhanced_orchestrator.supabase.table("campaign_check_ins")\
            .select("*")\
            .eq("campaign_id", campaign_id)\
            .order("scheduled_at")\
            .execute()

        # Get response tracking snapshots
        snapshots_result = enhanced_orchestrator.supabase.table("campaign_response_tracking")\
            .select("*")\
            .eq("campaign_id", campaign_id)\
            .order("snapshot_time")\
            .execute()

        # Build timeline
        timeline = {
            "campaign_id": campaign_id,
            "campaign_name": campaign["name"],
            "started_at": campaign.get("started_at"),
            "timeline_hours": campaign.get("strategy_data", {}).get("timeline_hours", 24),
            "bids_needed": campaign.get("strategy_data", {}).get("bids_needed", 4),
            "events": []
        }

        # Add campaign start
        if campaign.get("started_at"):
            timeline["events"].append({
                "time": campaign["started_at"],
                "type": "campaign_start",
                "description": f"Campaign started with {campaign.get('contractor_count', 0)} contractors"
            })

        # Add check-ins
        for check_in in check_ins_result.data:
            event = {
                "time": check_in["scheduled_at"],
                "type": "check_in",
                "check_in_number": check_in["check_in_number"],
                "description": f"Check-in #{check_in['check_in_number']} at {check_in['check_in_percentage']}%"
            }

            if check_in.get("completed_at"):
                event["completed"] = True
                event["results"] = {
                    "expected_bids": check_in["expected_bids"],
                    "actual_bids": check_in["actual_bids"],
                    "on_track": check_in["on_track"],
                    "escalation_needed": check_in["escalation_needed"]
                }

            timeline["events"].append(event)

        # Add performance snapshots
        for snapshot in snapshots_result.data:
            timeline["events"].append({
                "time": snapshot["snapshot_time"],
                "type": "performance_snapshot",
                "hours_elapsed": float(snapshot["hours_since_start"]),
                "metrics": {
                    "contacted": snapshot["contractors_contacted"],
                    "responded": snapshot["responses_received"],
                    "bids": snapshot["bids_submitted"],
                    "response_rate": float(snapshot["overall_response_rate"])
                }
            })

        # Sort events by time
        timeline["events"].sort(key=lambda x: x["time"])

        return timeline

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_campaigns() -> dict[str, Any]:
    """
    Get all active campaigns with real-time performance
    """
    try:
        # Query the real-time view
        result = enhanced_orchestrator.supabase.table("campaign_status_realtime")\
            .select("*")\
            .execute()

        campaigns = []
        for campaign in result.data:
            campaigns.append({
                "campaign_id": campaign["campaign_id"],
                "name": campaign["campaign_name"],
                "priority": campaign["priority"],
                "escalated": campaign["escalated"],
                "hours_elapsed": float(campaign["hours_elapsed"]),
                "timeline_hours": int(campaign["timeline_hours"]),
                "bids_needed": int(campaign["bids_needed"]),
                "bids_submitted": campaign["bids_submitted"],
                "performance_status": campaign["performance_status"],
                "current_response_rate": float(campaign["current_response_rate"]),
                "projected_final_bids": campaign["projected_final_bids"]
            })

        return {
            "success": True,
            "count": len(campaigns),
            "campaigns": campaigns
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/record-snapshot")
async def record_performance_snapshot(campaign_id: str) -> dict[str, Any]:
    """
    Manually record a performance snapshot for a campaign
    """
    try:
        # Call the database function
        enhanced_orchestrator.supabase.rpc(
            "record_campaign_snapshot",
            {"p_campaign_id": campaign_id}
        ).execute()

        return {
            "success": True,
            "message": "Performance snapshot recorded",
            "campaign_id": campaign_id,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Add to main.py imports:
# from api.campaigns_intelligent import router as intelligent_campaigns_router
# app.include_router(intelligent_campaigns_router)
