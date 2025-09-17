#!/usr/bin/env python3
"""
Campaign Management API
Real-time campaign oversight with outreach tracking and contractor management
"""

from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from uuid import uuid4
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from database_simple import db
from services.agent_orchestrator import orchestrator


router = APIRouter(prefix="/api/campaign-management", tags=["campaign-management"])


class CampaignSummary(BaseModel):
    """Campaign summary for dashboard display"""
    id: str
    name: str
    bid_card_id: str
    bid_card_number: Optional[str] = None
    project_type: Optional[str] = None
    status: str
    max_contractors: int
    contractors_targeted: int
    contractors_responded: int
    bids_received: int
    created_at: str
    updated_at: str
    target_completion_date: Optional[str] = None
    progress_percentage: float
    response_rate: float
    # Urgency and timeline fields
    urgency_level: Optional[str] = None
    user_timeline_days: Optional[int] = None
    internal_timeline_hours: Optional[int] = None
    deadline_adjusted_timeline_hours: Optional[int] = None


class CampaignDetail(BaseModel):
    """Detailed campaign information"""
    # Basic campaign info
    id: str
    name: str
    bid_card_id: str
    bid_card_number: Optional[str] = None
    project_type: Optional[str] = None
    project_description: Optional[str] = None
    status: str
    
    # Campaign settings
    max_contractors: int
    contractors_targeted: int
    contractors_responded: int
    bids_received: int
    
    # Timeline
    created_at: str
    updated_at: str
    target_completion_date: Optional[str] = None
    
    # Date flow fields for deadline-based timing
    bid_collection_deadline: Optional[str] = None
    project_completion_deadline: Optional[str] = None
    deadline_adjusted_timeline_hours: Optional[int] = None
    deadline_hard: Optional[bool] = None
    
    # Performance metrics
    progress_percentage: float
    response_rate: float
    avg_response_time_hours: Optional[float] = None
    
    # Campaign contractors
    assigned_contractors: List[Dict[str, Any]]
    
    # Outreach attempts
    outreach_history: List[Dict[str, Any]]
    
    # Check-ins and progress
    check_ins: List[Dict[str, Any]]
    
    # Campaign decision audit trail
    strategy_data: Optional[Dict[str, Any]] = None
    decision_inputs: Optional[Dict[str, Any]] = None


class CampaignStats(BaseModel):
    """Campaign statistics for dashboard"""
    total_campaigns: int
    active_campaigns: int
    completed_campaigns: int
    paused_campaigns: int
    cancelled_campaigns: int
    total_contractors_targeted: int
    total_responses_received: int
    total_bids_received: int
    average_response_rate: float
    average_campaign_duration_hours: float


@router.get("/campaigns", response_model=Dict[str, Any])
async def get_all_campaigns(
    status: Optional[str] = None,
    project_type: Optional[str] = None,
    bid_card_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get all campaigns with filtering and real-time status
    """
    try:
        campaigns = []
        
        # Get all outreach campaigns
        query = db.client.table("outreach_campaigns").select("""
            *,
            bid_cards!inner(
                bid_card_number,
                project_type,
                contractor_count_needed
            )
        """)
        
        # Apply filters
        if status:
            query = query.eq("status", status)
        if project_type:
            query = query.eq("bid_cards.project_type", project_type)  
        if bid_card_id:
            query = query.eq("bid_card_id", bid_card_id)
            
        campaigns_result = query.order("created_at", desc=True).execute()
        
        print(f"DEBUG: Found {len(campaigns_result.data) if campaigns_result.data else 0} campaigns")
        
        for campaign in campaigns_result.data:
            # Get campaign contractors count
            contractors_result = db.client.table("campaign_contractors")\
                .select("contractor_id", count="exact")\
                .eq("campaign_id", campaign["id"])\
                .execute()
            
            contractors_targeted = contractors_result.count if contractors_result.count else 0
            
            # Get response count (try different approaches)
            contractors_responded = 0
            bids_received = 0
            
            try:
                # Try to get responses from contractor_responses table
                responses_result = db.client.table("contractor_responses")\
                    .select("id", count="exact")\
                    .eq("campaign_id", campaign["id"])\
                    .execute()
                contractors_responded = responses_result.count if responses_result.count else 0
            except Exception as e:
                print(f"DEBUG: Could not query contractor_responses table: {e}")
                # Try alternative approach - look for responses in outreach attempts
                try:
                    responses_result = db.client.table("contractor_outreach_attempts")\
                        .select("id", count="exact")\
                        .eq("campaign_id", campaign["id"])\
                        .eq("status", "responded")\
                        .execute()
                    contractors_responded = responses_result.count if responses_result.count else 0
                except Exception as e2:
                    print(f"DEBUG: Could not query contractor_outreach_attempts table: {e2}")
            
            try:
                # Try to get bids from contractor_bids table
                bids_result = db.client.table("contractor_bids")\
                    .select("id", count="exact")\
                    .eq("campaign_id", campaign["id"])\
                    .execute()
                bids_received = bids_result.count if bids_result.count else 0
            except Exception as e:
                print(f"DEBUG: Could not query contractor_bids table: {e}")
                # Use default value of 0
                bids_received = 0
            
            # Calculate response rate
            response_rate = (contractors_responded / contractors_targeted * 100) if contractors_targeted > 0 else 0
            
            # Calculate progress percentage
            max_contractors = campaign.get("max_contractors", 0) or contractors_targeted
            if max_contractors > 0:
                progress_percentage = (contractors_targeted / max_contractors * 100)
                # Boost progress based on responses and bids
                if contractors_responded > 0:
                    progress_percentage = min(100, progress_percentage + (contractors_responded / max_contractors * 20))
                if bids_received > 0:
                    progress_percentage = min(100, progress_percentage + (bids_received / max_contractors * 30))
            else:
                progress_percentage = 0
            
            bid_card = campaign.get("bid_cards", {})
            
            # Calculate internal timeline based on urgency level
            urgency_level = bid_card.get("urgency_level", "standard")
            internal_timeline_hours = None
            user_timeline_days = None
            
            # Map urgency levels to internal timelines
            urgency_timelines = {
                "emergency": 24,  # 1 day internal target
                "urgent": 48,     # 2 days internal target
                "week": 48,       # User says week, we try for 2 days
                "standard": 72,   # 3 days internal target
                "flexible": 120,  # 5 days internal target
                "group": 168      # 7 days internal target
            }
            
            # Get internal timeline based on urgency
            internal_timeline_hours = urgency_timelines.get(urgency_level, 72)
            
            # Calculate user's timeline expectation
            if urgency_level == "emergency":
                user_timeline_days = 1
            elif urgency_level == "urgent":
                user_timeline_days = 3
            elif urgency_level == "week":
                user_timeline_days = 7
            elif urgency_level == "standard":
                user_timeline_days = 7
            elif urgency_level == "flexible":
                user_timeline_days = 14
            elif urgency_level == "group":
                user_timeline_days = 30
            
            # Check for deadline-adjusted timeline from strategy data
            strategy_data = campaign.get("strategy_data", {})
            if strategy_data and isinstance(strategy_data, dict):
                deadline_adjusted = strategy_data.get("timeline_hours")
                if deadline_adjusted:
                    internal_timeline_hours = deadline_adjusted
            
            campaign_summary = CampaignSummary(
                id=campaign["id"],
                name=campaign.get("name") or f"Campaign for {bid_card.get('bid_card_number', 'Unknown')}",
                bid_card_id=campaign["bid_card_id"],
                bid_card_number=bid_card.get("bid_card_number"),
                project_type=bid_card.get("project_type"),
                status=campaign.get("status", "unknown"),
                max_contractors=max_contractors,
                contractors_targeted=contractors_targeted,
                contractors_responded=contractors_responded,
                bids_received=bids_received,
                created_at=campaign["created_at"],
                updated_at=campaign["updated_at"],
                target_completion_date=campaign.get("target_completion_date"),
                progress_percentage=round(progress_percentage, 1),
                response_rate=round(response_rate, 1),
                urgency_level=urgency_level,
                user_timeline_days=user_timeline_days,
                internal_timeline_hours=internal_timeline_hours,
                deadline_adjusted_timeline_hours=internal_timeline_hours
            )
            
            campaigns.append(campaign_summary)
            print(f"DEBUG: Added campaign: {campaign_summary.name} (Progress: {campaign_summary.progress_percentage}%)")

        print(f"DEBUG: Total campaigns processed: {len(campaigns)}")
        
        # Apply pagination
        total_count = len(campaigns)
        campaigns = campaigns[offset:offset + limit]
        
        return {
            "campaigns": [c.dict() for c in campaigns],
            "total_count": total_count,
            "filters_applied": {
                "status": status,
                "project_type": project_type,
                "bid_card_id": bid_card_id
            }
        }

    except Exception as e:
        print(f"ERROR: Failed to retrieve campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving campaigns: {str(e)}")


@router.get("/campaigns/{campaign_id}", response_model=CampaignDetail)
async def get_campaign_detail(campaign_id: str):
    """Get detailed information about a specific campaign"""
    try:
        # Get campaign with bid card info
        campaign_result = db.client.table("outreach_campaigns")\
            .select("""
                *,
                bid_cards!inner(
                    bid_card_number,
                    project_type,
                    contractor_count_needed,
                    bid_collection_deadline,
                    project_completion_deadline,
                    deadline_hard,
                    deadline_context,
                    urgency_level,
                    budget_min,
                    budget_max,
                    description
                )
            """)\
            .eq("id", campaign_id)\
            .single()\
            .execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign = campaign_result.data
        bid_card = campaign.get("bid_cards", {})
        
        # Get assigned contractors with details (try both possible relationships)
        assigned_contractors = []
        
        try:
            # Try with contractors table first
            contractors_result = db.client.table("campaign_contractors")\
                .select("""
                    *,
                    contractors!inner(
                        id, company_name, contact_name, email, phone,
                        tier, rating, specialties, city, state
                    )
                """)\
                .eq("campaign_id", campaign_id)\
                .execute()
        except Exception as e:
            print(f"DEBUG: Could not join campaign_contractors with contractors: {e}")
            try:
                # Try with contractor_leads table instead
                contractors_result = db.client.table("campaign_contractors")\
                    .select("""
                        *,
                        contractor_leads!inner(
                            id, company_name, contact_name, email, phone,
                            tier, rating, specialties, city, state
                        )
                    """)\
                    .eq("campaign_id", campaign_id)\
                    .execute()
            except Exception as e2:
                print(f"DEBUG: Could not join campaign_contractors with contractor_leads: {e2}")
                # Get just the campaign_contractors without joins
                contractors_result = db.client.table("campaign_contractors")\
                    .select("*")\
                    .eq("campaign_id", campaign_id)\
                    .execute()
        
        assigned_contractors = []
        for assignment in contractors_result.data or []:
            # Handle different possible join results
            contractor_data = None
            if "contractors" in assignment:
                contractor_data = assignment["contractors"]
            elif "contractor_leads" in assignment:
                contractor_data = assignment["contractor_leads"]
            else:
                # No join data available, use basic assignment info
                contractor_data = {
                    "id": assignment.get("contractor_id", "unknown"),
                    "company_name": f"Contractor {assignment.get('contractor_id', 'Unknown')}",
                    "contact_name": None,
                    "email": None,
                    "phone": None,
                    "tier": None,
                    "rating": None,
                    "specialties": [],
                    "city": None,
                    "state": None
                }
            
            assigned_contractors.append({
                "assignment_id": assignment["id"],
                "contractor_id": contractor_data["id"],
                "company_name": contractor_data.get("company_name", "Unknown"),
                "contact_name": contractor_data.get("contact_name"),
                "email": contractor_data.get("email"),
                "phone": contractor_data.get("phone"),
                "tier": contractor_data.get("tier"),
                "rating": contractor_data.get("rating"),
                "specialties": contractor_data.get("specialties", []),
                "city": contractor_data.get("city"),
                "state": contractor_data.get("state"),
                "assigned_at": assignment.get("assigned_at") or assignment.get("created_at", "unknown"),
                "status": assignment.get("status", "assigned")
            })
        
        # Get outreach history with defensive querying
        outreach_history = []
        try:
            outreach_result = db.client.table("contractor_outreach_attempts")\
                .select("*")\
                .eq("campaign_id", campaign_id)\
                .order("sent_at", desc=True)\
                .execute()
            
            for attempt in outreach_result.data or []:
                outreach_history.append({
                    "attempt_id": attempt["id"],
                    "contractor_company": attempt.get("contractor_lead_id", "Unknown Contractor"),
                    "channel": attempt.get("channel", "unknown"),
                    "status": attempt.get("status", "unknown"),
                    "sent_at": attempt.get("sent_at", "unknown"),
                    "message_content": attempt.get("message_content", "")[:100] + "..." if attempt.get("message_content", "") else ""
                })
        except Exception as e:
            print(f"DEBUG: Could not query contractor_outreach_attempts: {e}")
            outreach_history = []
        
        # Get check-ins with defensive querying
        check_ins = []
        try:
            checkins_result = db.client.table("campaign_check_ins")\
                .select("*")\
                .eq("campaign_id", campaign_id)\
                .order("check_in_time", desc=True)\
                .execute()
            
            for checkin in checkins_result.data or []:
                check_ins.append({
                    "check_in_id": checkin["id"],
                    "check_in_type": checkin.get("check_in_type", "unknown"),
                    "check_in_time": checkin.get("check_in_time", "unknown"),
                    "contractors_needed": checkin.get("contractors_needed"),
                    "escalation_triggered": checkin.get("escalation_triggered", False),
                    "notes": checkin.get("notes", "")
                })
        except Exception as e:
            print(f"DEBUG: Could not query campaign_check_ins: {e}")
            check_ins = []
        
        # Calculate metrics
        contractors_targeted = len(assigned_contractors)
        
        # Use defensive querying for responses and bids
        contractors_responded = 0
        bids_received = 0
        
        try:
            responses_result = db.client.table("contractor_responses")\
                .select("id", count="exact")\
                .eq("campaign_id", campaign_id)\
                .execute()
            contractors_responded = responses_result.count if responses_result.count else 0
        except Exception as e:
            print(f"DEBUG: Could not query contractor_responses for detail: {e}")
            contractors_responded = 0
        
        try:
            bids_result = db.client.table("contractor_bids")\
                .select("id", count="exact")\
                .eq("campaign_id", campaign_id)\
                .execute()
            bids_received = bids_result.count if bids_result.count else 0
        except Exception as e:
            print(f"DEBUG: Could not query contractor_bids for detail: {e}")
            bids_received = 0
        
        response_rate = (contractors_responded / contractors_targeted * 100) if contractors_targeted > 0 else 0
        
        # Calculate progress percentage
        max_contractors = campaign.get("max_contractors", 0) or contractors_targeted
        if max_contractors > 0:
            progress_percentage = (contractors_targeted / max_contractors * 100)
            if contractors_responded > 0:
                progress_percentage = min(100, progress_percentage + (contractors_responded / max_contractors * 20))
            if bids_received > 0:
                progress_percentage = min(100, progress_percentage + (bids_received / max_contractors * 30))
        else:
            progress_percentage = 0
        
        # Build decision inputs from bid card data
        decision_inputs = {
            "project_details": {
                "project_type": bid_card.get("project_type"),
                "urgency_level": bid_card.get("urgency_level"),
                "budget_range": {
                    "min": bid_card.get("budget_min"),
                    "max": bid_card.get("budget_max")
                },
                "contractor_count_needed": bid_card.get("contractor_count_needed"),
                "project_description": bid_card.get("description")
            },
            "timing_requirements": {
                "bid_collection_deadline": bid_card.get("bid_collection_deadline"),
                "project_completion_deadline": bid_card.get("project_completion_deadline"),
                "deadline_hard": bid_card.get("deadline_hard", False),
                "deadline_context": bid_card.get("deadline_context")
            },
            "campaign_settings": {
                "max_contractors": max_contractors,
                "target_criteria": campaign.get("target_criteria"),
                "created_at": campaign["created_at"]
            }
        }

        return CampaignDetail(
            id=campaign["id"],
            name=campaign.get("name") or f"Campaign for {bid_card.get('bid_card_number', 'Unknown')}",
            bid_card_id=campaign["bid_card_id"],
            bid_card_number=bid_card.get("bid_card_number"),
            project_type=bid_card.get("project_type"),
            project_description=bid_card.get("description"),
            status=campaign.get("status", "unknown"),
            max_contractors=max_contractors,
            contractors_targeted=contractors_targeted,
            contractors_responded=contractors_responded,
            bids_received=bids_received,
            created_at=campaign["created_at"],
            updated_at=campaign["updated_at"],
            target_completion_date=campaign.get("target_completion_date"),
            # Date flow fields from bid card
            bid_collection_deadline=bid_card.get("bid_collection_deadline"),
            project_completion_deadline=bid_card.get("project_completion_deadline"),
            deadline_adjusted_timeline_hours=campaign.get("deadline_adjusted_timeline_hours"),
            deadline_hard=bid_card.get("deadline_hard", False),
            progress_percentage=round(progress_percentage, 1),
            response_rate=round(response_rate, 1),
            avg_response_time_hours=None,  # Would calculate from response times
            assigned_contractors=assigned_contractors,
            outreach_history=outreach_history[:20],  # Last 20 attempts
            check_ins=check_ins,
            # Campaign decision audit trail
            strategy_data=campaign.get("strategy_data"),
            decision_inputs=decision_inputs
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Failed to retrieve campaign details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving campaign details: {str(e)}")


@router.get("/dashboard-stats", response_model=CampaignStats)
async def get_campaign_dashboard_stats():
    """Get real-time stats for campaign dashboard"""
    try:
        # Get all campaigns
        campaigns_result = db.client.table("outreach_campaigns")\
            .select("*")\
            .execute()
        
        campaigns = campaigns_result.data if campaigns_result.data else []
        
        # Count by status
        total_campaigns = len(campaigns)
        active_campaigns = len([c for c in campaigns if c.get("status") == "active"])
        completed_campaigns = len([c for c in campaigns if c.get("status") == "completed"])
        paused_campaigns = len([c for c in campaigns if c.get("status") == "paused"])
        cancelled_campaigns = len([c for c in campaigns if c.get("status") == "cancelled"])
        
        # Get aggregate stats with defensive querying
        total_contractors_targeted = 0
        total_responses_received = 0
        total_bids_received = 0
        
        try:
            contractors_result = db.client.table("campaign_contractors")\
                .select("id", count="exact")\
                .execute()
            total_contractors_targeted = contractors_result.count if contractors_result.count else 0
        except Exception as e:
            print(f"DEBUG: Could not query campaign_contractors for stats: {e}")
        
        try:
            responses_result = db.client.table("contractor_responses")\
                .select("id", count="exact")\
                .execute()
            total_responses_received = responses_result.count if responses_result.count else 0
        except Exception as e:
            print(f"DEBUG: Could not query contractor_responses for stats: {e}")
        
        try:
            bids_result = db.client.table("contractor_bids")\
                .select("id", count="exact")\
                .execute()
            total_bids_received = bids_result.count if bids_result.count else 0
        except Exception as e:
            print(f"DEBUG: Could not query contractor_bids for stats: {e}")
        
        # Calculate averages
        average_response_rate = (total_responses_received / total_contractors_targeted * 100) if total_contractors_targeted > 0 else 0
        
        # Calculate average campaign duration
        completed_durations = []
        for campaign in campaigns:
            if campaign.get("status") == "completed" and campaign.get("created_at") and campaign.get("updated_at"):
                created = datetime.fromisoformat(campaign["created_at"].replace('Z', '+00:00'))
                updated = datetime.fromisoformat(campaign["updated_at"].replace('Z', '+00:00'))
                duration_hours = (updated - created).total_seconds() / 3600
                completed_durations.append(duration_hours)
        
        average_campaign_duration_hours = sum(completed_durations) / len(completed_durations) if completed_durations else 0
        
        return CampaignStats(
            total_campaigns=total_campaigns,
            active_campaigns=active_campaigns,
            completed_campaigns=completed_campaigns,
            paused_campaigns=paused_campaigns,
            cancelled_campaigns=cancelled_campaigns,
            total_contractors_targeted=total_contractors_targeted,
            total_responses_received=total_responses_received,
            total_bids_received=total_bids_received,
            average_response_rate=round(average_response_rate, 1),
            average_campaign_duration_hours=round(average_campaign_duration_hours, 1)
        )

    except Exception as e:
        print(f"ERROR: Failed to retrieve campaign stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving campaign stats: {str(e)}")


@router.post("/campaigns/{campaign_id}/assign-contractors")
async def assign_contractors_to_campaign(
    campaign_id: str,
    contractor_data: dict
):
    """
    Manually assign contractors to a campaign
    """
    try:
        contractor_ids = contractor_data.get("contractor_ids", [])
        
        if not contractor_ids:
            raise HTTPException(status_code=400, detail="No contractor IDs provided")
        
        # Verify campaign exists
        campaign_result = db.client.table("outreach_campaigns")\
            .select("id, bid_card_id")\
            .eq("id", campaign_id)\
            .single()\
            .execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign = campaign_result.data
        assigned_count = 0
        
        for contractor_id in contractor_ids:
            # Check if contractor is already assigned
            existing = db.client.table("campaign_contractors")\
                .select("id")\
                .eq("campaign_id", campaign_id)\
                .eq("contractor_id", contractor_id)\
                .execute()
            
            if existing.data:
                continue  # Skip already assigned contractors
            
            # Add contractor to campaign (use only fields that exist in schema)
            assignment = {
                "id": str(uuid4()),
                "campaign_id": campaign_id,
                "contractor_id": contractor_id
            }
            
            db.client.table("campaign_contractors").insert(assignment).execute()
            
            # Create outreach attempt record (use minimal required fields)
            outreach_attempt = {
                "id": str(uuid4()),
                "bid_card_id": campaign["bid_card_id"],
                "campaign_id": campaign_id,
                "contractor_lead_id": contractor_id,
                "channel": "email",  # Use valid enum value
                "status": "sent",
                "message_content": "Manually assigned to campaign by admin via dashboard"
            }
            
            db.client.table("contractor_outreach_attempts").insert(outreach_attempt).execute()
            assigned_count += 1
            
            # NEW: Trigger actual agent outreach
            try:
                print(f"DEBUG: Triggering agent outreach for contractor {contractor_id}")
                # Run async task in background to not block the response
                asyncio.create_task(
                    orchestrator.trigger_contractor_outreach(
                        contractor_id=contractor_id,
                        campaign_id=campaign_id,
                        channel="auto"  # Will try both email and form
                    )
                )
                print(f"DEBUG: Agent outreach triggered successfully")
            except Exception as e:
                print(f"WARNING: Failed to trigger agent outreach: {e}")
                # Don't fail the assignment if agent trigger fails
        
        return {
            "success": True,
            "message": f"Successfully assigned {assigned_count} contractors to campaign. Agent outreach initiated.",
            "campaign_id": campaign_id,
            "contractors_assigned": assigned_count,
            "agent_outreach": "initiated"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Failed to assign contractors to campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error assigning contractors to campaign: {str(e)}")

@router.put("/campaigns/{campaign_id}/status", response_model=dict)
async def update_campaign_status(campaign_id: str, request: dict):
    """Update campaign status (pause/resume/complete)"""
    try:
        new_status = request.get("status")
        if new_status not in ["active", "paused", "completed", "cancelled"]:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid status. Must be: active, paused, completed, or cancelled"}
            )
        
        # Update campaign status
        result = db.client.table("outreach_campaigns")\
            .update({
                "status": new_status,
                "updated_at": datetime.now().isoformat()
            })\
            .eq("id", campaign_id)\
            .execute()
        
        if not result.data:
            return JSONResponse(
                status_code=404,
                content={"detail": "Campaign not found"}
            )
        
        # If pausing, create a check-in record with all required fields
        if new_status == "paused":
            # Based on error, these fields are required with default values
            check_in = {
                "id": str(uuid4()),
                "campaign_id": campaign_id,
                "check_in_time": datetime.now().isoformat(),
                "progress_percentage": 0.0,  # Required field
                "contractors_targeted": 0,
                "contractors_responded": 0,
                "bids_received": 0,
                "response_rate": 0.0,
                "escalation_triggered": False,
                "escalation_reason": None,
                "contractors_added": 0,
                "contractor_tier_added": 0,
                "follow_up_messages_sent": 0,
                "notification_sent": False,
                "alert_admin": False,
                "status": "pending",
                "notes": "Campaign manually paused by admin"
            }
            
            try:
                db.client.table("campaign_check_ins").insert(check_in).execute()
            except Exception as e:
                print(f"WARNING: Could not create check-in record: {e}")
                # Continue without creating check-in - status update is more important
        
        return {
            "success": True,
            "message": f"Campaign status updated to {new_status}",
            "campaign_id": campaign_id,
            "new_status": new_status
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error updating campaign status: {str(e)}"}
        )

@router.post("/campaigns/{campaign_id}/escalate", response_model=dict)
async def escalate_campaign(campaign_id: str, request: dict):
    """Escalate campaign by adding more contractors"""
    try:
        # Get campaign details
        campaign_result = db.client.table("outreach_campaigns")\
            .select("*, bid_cards!inner(contractor_count_needed)")\
            .eq("id", campaign_id)\
            .single()\
            .execute()
        
        if not campaign_result.data:
            return JSONResponse(
                status_code=404,
                content={"detail": "Campaign not found"}
            )
        
        campaign = campaign_result.data
        additional_contractors = request.get("additional_contractors", 5)
        
        # Create escalation check-in with all required fields
        check_in = {
            "id": str(uuid4()),
            "campaign_id": campaign_id,
            "check_in_time": datetime.now().isoformat(),
            "progress_percentage": 0.0,  # Will be calculated properly later
            "contractors_targeted": 0,
            "contractors_responded": 0,
            "bids_received": 0,
            "response_rate": 0.0,
            "escalation_triggered": True,
            "escalation_reason": "Manual escalation by admin",
            "contractors_added": additional_contractors,
            "contractor_tier_added": 0,  # Could determine tier later
            "follow_up_messages_sent": 0,
            "notification_sent": False,
            "alert_admin": False,
            "status": "escalated",
            "notes": f"Manual escalation: Adding {additional_contractors} more contractors"
        }
        
        try:
            db.client.table("campaign_check_ins").insert(check_in).execute()
        except Exception as e:
            print(f"WARNING: Could not create check-in record: {e}")
            # Continue without creating check-in - escalation is more important
        
        # Update campaign metrics
        new_max = campaign.get("max_contractors", 0) + additional_contractors
        db.client.table("outreach_campaigns")\
            .update({
                "max_contractors": new_max,
                "updated_at": datetime.now().isoformat()
            })\
            .eq("id", campaign_id)\
            .execute()
        
        return {
            "success": True,
            "message": f"Campaign escalated with {additional_contractors} additional contractors",
            "campaign_id": campaign_id,
            "new_max_contractors": new_max
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error escalating campaign: {str(e)}"}
        )