"""
EAA Routes - External Acquisition Agent API Endpoints
Owner: Agent 2 (Backend Core)
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

# Import EAA agent and orchestration components
from agents.eaa.agent import ExternalAcquisitionAgent
from agents.orchestration.check_in_manager import CampaignCheckInManager
from agents.orchestration.enhanced_campaign_orchestrator import (
    CampaignRequest,
    EnhancedCampaignOrchestrator,
)
from agents.orchestration.timing_probability_engine import ContractorOutreachCalculator


# Create router
router = APIRouter()

# Global EAA agent instance (initialized in main.py)
eaa_agent: Optional[ExternalAcquisitionAgent] = None

def set_eaa_agent(agent: ExternalAcquisitionAgent):
    """Set the EAA agent instance"""
    global eaa_agent
    eaa_agent = agent

@router.post("/campaign/start")
async def start_eaa_campaign(campaign_data: dict):
    """Start EAA outreach campaign for discovered contractors"""
    if not eaa_agent:
        raise HTTPException(500, "EAA agent not initialized")

    try:
        bid_card_id = campaign_data.get("bid_card_id")
        contractors = campaign_data.get("contractors", [])
        channels = campaign_data.get("channels", ["email", "sms"])
        urgency = campaign_data.get("urgency", "week")

        if not bid_card_id or not contractors:
            raise HTTPException(400, "bid_card_id and contractors are required")

        result = eaa_agent.start_campaign(
            bid_card_id=bid_card_id,
            contractors=contractors,
            channels=channels,
            urgency=urgency
        )

        if result["success"]:
            return {
                "success": True,
                "campaign_id": result["campaign_id"],
                "messages_sent": result["messages_sent"],
                "tier_breakdown": result["tier_breakdown"],
                "tracking_url": result["tracking_url"]
            }
        else:
            raise HTTPException(500, result.get("error", "Unknown error starting campaign"))

    except Exception as e:
        print(f"[EAA API ERROR] {e}")
        raise HTTPException(500, f"EAA campaign failed: {e!s}")

@router.get("/campaign/{campaign_id}/status")
async def get_eaa_campaign_status(campaign_id: str):
    """Get EAA campaign status and metrics"""
    if not eaa_agent:
        raise HTTPException(500, "EAA agent not initialized")

    try:
        result = eaa_agent.get_campaign_status(campaign_id)

        if result["success"]:
            return {
                "success": True,
                "campaign_id": result["campaign_id"],
                "status": result["status"],
                "metrics": result["metrics"],
                "recent_responses": result["recent_responses"],
                "tier_breakdown": result["tier_breakdown"]
            }
        else:
            raise HTTPException(404, result.get("error", "Campaign not found"))

    except Exception as e:
        print(f"[EAA STATUS ERROR] {e}")
        raise HTTPException(500, f"Failed to get campaign status: {e!s}")

@router.post("/response/process")
async def process_eaa_response(response_data: dict):
    """Process incoming contractor response"""
    if not eaa_agent:
        raise HTTPException(500, "EAA agent not initialized")

    try:
        message_id = response_data.get("message_id")
        response_content = response_data.get("response_content")
        channel = response_data.get("channel")

        if not all([message_id, response_content, channel]):
            raise HTTPException(400, "message_id, response_content, and channel are required")

        result = eaa_agent.process_response(message_id, response_content, channel)

        if result["success"]:
            return {
                "success": True,
                "response_id": result["response_id"],
                "intent": result["intent"],
                "interest_level": result["interest_level"],
                "action_taken": result["action_taken"],
                "follow_up_scheduled": result["follow_up_scheduled"]
            }
        else:
            raise HTTPException(500, result.get("error", "Unknown error processing response"))

    except Exception as e:
        print(f"[EAA RESPONSE ERROR] {e}")
        raise HTTPException(500, f"Failed to process response: {e!s}")

@router.post("/onboarding/start")
async def start_eaa_onboarding(onboarding_data: dict):
    """Start contractor onboarding process"""
    if not eaa_agent:
        raise HTTPException(500, "EAA agent not initialized")

    try:
        contractor_email = onboarding_data.get("contractor_email")
        source_campaign = onboarding_data.get("source_campaign")

        if not contractor_email:
            raise HTTPException(400, "contractor_email is required")

        result = eaa_agent.start_onboarding(contractor_email, source_campaign)

        if result["success"]:
            return {
                "success": True,
                "onboarding_id": result["onboarding_id"],
                "next_step": result["next_step"],
                "estimated_completion": result["estimated_completion"]
            }
        else:
            raise HTTPException(500, result.get("error", "Unknown error starting onboarding"))

    except Exception as e:
        print(f"[EAA ONBOARDING ERROR] {e}")
        raise HTTPException(500, f"Failed to start onboarding: {e!s}")

@router.get("/analytics")
async def get_eaa_analytics(date_range: int = 30):
    """Get EAA performance analytics"""
    if not eaa_agent:
        raise HTTPException(500, "EAA agent not initialized")

    try:
        result = eaa_agent.get_analytics(date_range)

        if result["success"]:
            return {
                "success": True,
                "period_days": result["period_days"],
                "campaigns_launched": result["campaigns_launched"],
                "total_contractors_contacted": result["total_contractors_contacted"],
                "overall_metrics": result["overall_metrics"],
                "channel_performance": result["channel_performance"],
                "top_performing_templates": result["top_performing_templates"]
            }
        else:
            raise HTTPException(500, result.get("error", "Unknown error getting analytics"))

    except Exception as e:
        print(f"[EAA ANALYTICS ERROR] {e}")
        raise HTTPException(500, f"Failed to get analytics: {e!s}")

# Webhook endpoints for external services
@router.post("/webhook/email-response")
async def handle_email_webhook(webhook_data: dict):
    """Handle SendGrid email webhook"""
    if not eaa_agent:
        raise HTTPException(500, "EAA agent not initialized")

    try:
        # Process email webhook
        result = eaa_agent.email_channel.handle_webhook(webhook_data)
        return {"success": result["success"], "processed": True}

    except Exception as e:
        print(f"[EMAIL WEBHOOK ERROR] {e}")
        raise HTTPException(500, f"Failed to process email webhook: {e!s}")

@router.post("/webhook/sms-response")
async def handle_sms_webhook(webhook_data: dict):
    """Handle Twilio SMS webhook"""
    if not eaa_agent:
        raise HTTPException(500, "EAA agent not initialized")

    try:
        # Process SMS webhook
        result = eaa_agent.sms_channel.handle_incoming_sms(webhook_data)
        return {"success": result["success"], "processed": True}

    except Exception as e:
        print(f"[SMS WEBHOOK ERROR] {e}")
        raise HTTPException(500, f"Failed to process SMS webhook: {e!s}")

# Orchestration & Timing Endpoints
@router.post("/timing/calculate")
async def calculate_timing_strategy(request: dict):
    """Calculate how many contractors to contact based on timeline"""
    try:
        calculator = ContractorOutreachCalculator()
        strategy = calculator.calculate_outreach_strategy(
            bids_needed=request.get("bids_needed", 4),
            timeline_hours=request.get("timeline_hours", 24),
            tier1_available=request.get("tier1_available", 10),
            tier2_available=request.get("tier2_available", 30),
            tier3_available=request.get("tier3_available", 100),
            project_type=request.get("project_type"),
            location=request.get("location")
        )

        return {
            "success": True,
            "total_contractors": strategy.total_to_contact,
            "expected_responses": strategy.expected_total_responses,
            "confidence_level": strategy.confidence_level,
            "tier_breakdown": {
                "tier1": strategy.tier1_to_contact,
                "tier2": strategy.tier2_to_contact,
                "tier3": strategy.tier3_to_contact
            },
            "reasoning": strategy.reasoning,
            "risk_level": strategy.risk_level
        }

    except Exception as e:
        print(f"[TIMING CALCULATION ERROR] {e}")
        raise HTTPException(500, f"Failed to calculate timing strategy: {e!s}")

@router.post("/campaigns/create-intelligent")
async def create_intelligent_campaign(request: CampaignRequest):
    """Create intelligent campaign with timing calculations and orchestration"""
    try:
        orchestrator = EnhancedCampaignOrchestrator()
        result = await orchestrator.create_campaign(request)

        if result["success"]:
            return {
                "success": True,
                "campaign_id": result["campaign_id"],
                "bid_card_id": result["bid_card_id"],
                "total_contractors": result["total_contractors"],
                "tier_breakdown": result["tier_breakdown"],
                "check_in_schedule": result["check_in_schedule"],
                "confidence_level": result["confidence_level"],
                "expected_bids": result["expected_bids"]
            }
        else:
            raise HTTPException(500, result.get("error", "Failed to create intelligent campaign"))

    except Exception as e:
        print(f"[INTELLIGENT CAMPAIGN ERROR] {e}")
        raise HTTPException(500, f"Failed to create intelligent campaign: {e!s}")

@router.get("/campaigns/{campaign_id}/check-in")
async def perform_campaign_checkin(campaign_id: str):
    """Perform check-in for a campaign and escalate if needed"""
    try:
        check_in_manager = CampaignCheckInManager()
        result = await check_in_manager.perform_check_in(campaign_id)

        if result["success"]:
            return {
                "success": True,
                "campaign_id": result["campaign_id"],
                "check_in_type": result["check_in_type"],
                "current_responses": result["current_responses"],
                "target_responses": result["target_responses"],
                "on_track": result["on_track"],
                "action_taken": result.get("action_taken"),
                "additional_contractors": result.get("additional_contractors", 0),
                "next_check_in": result.get("next_check_in")
            }
        else:
            raise HTTPException(500, result.get("error", "Failed to perform check-in"))

    except Exception as e:
        print(f"[CAMPAIGN CHECK-IN ERROR] {e}")
        raise HTTPException(500, f"Failed to perform check-in: {e!s}")

@router.get("/campaigns/{campaign_id}/metrics")
async def get_campaign_metrics(campaign_id: str):
    """Get detailed metrics for a specific campaign"""
    try:
        check_in_manager = CampaignCheckInManager()
        result = await check_in_manager.get_campaign_metrics(campaign_id)

        if result["success"]:
            return {
                "success": True,
                "campaign_id": result["campaign_id"],
                "timeline_progress": result["timeline_progress"],
                "response_progress": result["response_progress"],
                "tier_performance": result["tier_performance"],
                "channel_performance": result["channel_performance"],
                "escalation_history": result["escalation_history"],
                "projected_outcome": result["projected_outcome"]
            }
        else:
            raise HTTPException(404, result.get("error", "Campaign not found"))

    except Exception as e:
        print(f"[CAMPAIGN METRICS ERROR] {e}")
        raise HTTPException(500, f"Failed to get campaign metrics: {e!s}")

@router.post("/campaigns/{campaign_id}/escalate")
async def escalate_campaign(campaign_id: str, escalation_data: dict):
    """Manually escalate a campaign by adding more contractors"""
    try:
        check_in_manager = CampaignCheckInManager()
        additional_contractors = escalation_data.get("additional_contractors", 5)
        reason = escalation_data.get("reason", "manual_escalation")

        result = await check_in_manager.escalate_campaign(
            campaign_id=campaign_id,
            additional_contractors=additional_contractors,
            reason=reason
        )

        if result["success"]:
            return {
                "success": True,
                "campaign_id": result["campaign_id"],
                "contractors_added": result["contractors_added"],
                "new_tier_breakdown": result["new_tier_breakdown"],
                "escalation_id": result["escalation_id"],
                "estimated_impact": result["estimated_impact"]
            }
        else:
            raise HTTPException(500, result.get("error", "Failed to escalate campaign"))

    except Exception as e:
        print(f"[CAMPAIGN ESCALATION ERROR] {e}")
        raise HTTPException(500, f"Failed to escalate campaign: {e!s}")
