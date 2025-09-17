"""
Campaign Management API Router
Provides endpoints for viewing and managing campaigns in the admin dashboard
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Use the centralized database connection
from database_simple import get_client


router = APIRouter(prefix="/api/admin", tags=["admin"])

# Get Supabase client from centralized database module
supabase = get_client()


class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    user: dict[str, Any] | None = None
    session: dict[str, Any] | None = None

class CampaignResponse(BaseModel):
    campaigns: list[dict[str, Any]]
    total: int
    active_count: int


@router.post("/login")
async def admin_login(request: LoginRequest):
    """Admin login endpoint"""
    try:
        # Simple admin authentication
        if request.email == "admin@instabids.com" and request.password == "admin123":
            # Create session
            session_id = str(uuid.uuid4())
            session_data = {
                "session_id": session_id,
                "user_email": request.email,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
            }

            return {
                "success": True,
                "message": "Login successful",
                "admin_user": {
                    "id": "admin-user",
                    "email": request.email,
                    "full_name": "Admin User",
                    "role": "admin",
                    "permissions": ["all"],
                    "created_at": datetime.now().isoformat(),
                    "is_active": True
                },
                "session": session_data
            }
        else:
            return {
                "success": False,
                "message": "Invalid credentials",
                "admin_user": None,
                "session": None
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session")
async def get_session():
    """Check session status"""
    return {
        "success": True,
        "authenticated": True,
        "admin_user": {
            "id": "admin-user",
            "email": "admin@instabids.com",
            "full_name": "Admin User",
            "role": "admin",
            "permissions": ["all"],
            "created_at": datetime.now().isoformat(),
            "is_active": True
        },
        "session": {
            "session_id": str(uuid.uuid4()),
            "admin_user_id": "admin-user",
            "email": "admin@instabids.com",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "last_activity": datetime.now().isoformat(),
            "is_active": True
        }
    }


@router.get("/campaigns")
async def get_campaigns(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Number of campaigns to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """Get all campaigns with their current status"""
    try:
        # Build query
        query = supabase.table("outreach_campaigns").select(
            "*, bid_cards!inner(bid_card_number, project_type, urgency_level)"
        )

        if status:
            query = query.eq("status", status)

        # Get campaigns with bid card info
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

        campaigns = []
        for campaign in result.data:
            # Get check-ins for this campaign
            check_ins_result = supabase.table("campaign_check_ins")\
                .select("*")\
                .eq("campaign_id", campaign["id"])\
                .order("check_in_percentage").execute()

            # Format campaign data
            formatted_campaign = {
                "campaign_id": campaign["id"],
                "bid_card_id": campaign["bid_card_id"],
                "bid_card_number": campaign["bid_cards"]["bid_card_number"],
                "project_type": campaign["bid_cards"]["project_type"],
                "urgency_level": campaign["bid_cards"].get("urgency_level"),
                "max_contractors": campaign.get("max_contractors", 0),
                "contractors_targeted": campaign.get("contractors_targeted", 0),
                "responses_received": campaign.get("responses_received", 0),
                "campaign_status": campaign.get("status", "active"),
                "created_at": campaign["created_at"],
                "check_ins": []
            }

            # Add check-in data
            for check_in in check_ins_result.data:
                formatted_campaign["check_ins"].append({
                    "id": check_in["id"],
                    "check_in_percentage": check_in.get("check_in_percentage", 0),
                    "scheduled_time": check_in.get("scheduled_time"),
                    "bids_expected": check_in.get("bids_expected", 0),
                    "bids_received": check_in.get("bids_received", 0),
                    "on_track": check_in.get("on_track", False),
                    "escalation_needed": check_in.get("escalation_needed", False),
                    "additional_contractors_needed": check_in.get("additional_contractors_needed", 0),
                    "status": check_in.get("status", "pending")
                })

            campaigns.append(formatted_campaign)

        # Count active campaigns
        active_count = len([c for c in campaigns if c["campaign_status"] == "active"])

        return CampaignResponse(
            campaigns=campaigns,
            total=len(campaigns),
            active_count=active_count
        )

    except Exception as e:
        print(f"Error fetching campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns/{campaign_id}/details")
async def get_campaign_details(campaign_id: str):
    """Get detailed information about a specific campaign including all contractors"""
    try:
        # Get campaign info
        campaign_result = supabase.table("outreach_campaigns")\
            .select("*, bid_cards!inner(bid_card_number, project_type, urgency_level)")\
            .eq("id", campaign_id).single().execute()

        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")

        campaign = campaign_result.data

        # Get check-ins
        check_ins_result = supabase.table("campaign_check_ins")\
            .select("*")\
            .eq("campaign_id", campaign_id)\
            .order("check_in_percentage").execute()

        # Get contractors in campaign
        contractors_result = supabase.table("campaign_contractors")\
            .select("*, contractor_leads!inner(company_name, contractor_size, specialties, google_rating)")\
            .eq("campaign_id", campaign_id).execute()

        # Determine tier for each contractor
        contractors = []
        for cc in contractors_result.data:
            contractor_data = {
                "id": cc["id"],
                "contractor_id": cc["contractor_id"],
                "company_name": cc["contractor_leads"]["company_name"],
                "contractor_size": cc["contractor_leads"].get("contractor_size"),
                "specialties": cc["contractor_leads"].get("specialties", []),
                "tier": 1,  # Default to tier 1, will determine based on history
                "status": cc.get("status", "pending"),
                "contacted_at": cc.get("sent_at"),
                "responded_at": cc.get("responded_at")
            }

            # Try to determine tier based on contractor history
            # Tier 1: Internal (in contractors table)
            # Tier 2: Previously contacted (has outreach history)
            # Tier 3: New (no previous contact)

            # Check if internal contractor
            internal_check = supabase.table("contractors")\
                .select("id")\
                .eq("id", cc["contractor_id"])\
                .limit(1).execute()

            if internal_check.data:
                contractor_data["tier"] = 1
            else:
                # Check for previous outreach
                outreach_check = supabase.table("contractor_outreach_attempts")\
                    .select("id")\
                    .eq("contractor_lead_id", cc["contractor_id"])\
                    .neq("campaign_id", campaign_id)\
                    .limit(1).execute()

                if outreach_check.data:
                    contractor_data["tier"] = 2
                else:
                    contractor_data["tier"] = 3

            # Check for bid submission
            bid_check = supabase.table("bids")\
                .select("id")\
                .eq("bid_card_id", campaign["bid_card_id"])\
                .eq("contractor_id", cc["contractor_id"])\
                .limit(1).execute()

            if bid_check.data:
                contractor_data["status"] = "bid_submitted"
            elif contractor_data["responded_at"]:
                contractor_data["status"] = "responded"
            elif contractor_data["contacted_at"]:
                contractor_data["status"] = "contacted"

            contractors.append(contractor_data)

        # Format response
        response = {
            "campaign_id": campaign["id"],
            "bid_card_id": campaign["bid_card_id"],
            "bid_card_number": campaign["bid_cards"]["bid_card_number"],
            "project_type": campaign["bid_cards"]["project_type"],
            "urgency_level": campaign["bid_cards"].get("urgency_level"),
            "max_contractors": campaign.get("max_contractors", 0),
            "contractors_targeted": campaign.get("contractors_targeted", 0),
            "responses_received": campaign.get("responses_received", 0),
            "campaign_status": campaign.get("status", "active"),
            "created_at": campaign["created_at"],
            "check_ins": [],
            "contractors": contractors
        }

        # Add check-in data
        for check_in in check_ins_result.data:
            response["check_ins"].append({
                "id": check_in["id"],
                "check_in_percentage": check_in.get("check_in_percentage", 0),
                "scheduled_time": check_in.get("scheduled_time"),
                "bids_expected": check_in.get("bids_expected", 0),
                "bids_received": check_in.get("bids_received", 0),
                "on_track": check_in.get("on_track", False),
                "escalation_needed": check_in.get("escalation_needed", False),
                "additional_contractors_needed": check_in.get("additional_contractors_needed", 0),
                "status": check_in.get("status", "pending")
            })

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching campaign details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaigns/{campaign_id}/escalate")
async def trigger_escalation(campaign_id: str):
    """Manually trigger escalation to add more contractors to a campaign"""
    try:
        # Get campaign info
        campaign_result = supabase.table("outreach_campaigns")\
            .select("*, bid_cards!inner(*)")\
            .eq("id", campaign_id).single().execute()

        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")

        campaign = campaign_result.data
        bid_card = campaign["bid_cards"]

        # Calculate how many more contractors to add
        # This would normally call the timing engine to calculate properly
        additional_contractors = 5  # Default to adding 5 more

        # Update campaign
        update_result = supabase.table("outreach_campaigns")\
            .update({
                "max_contractors": campaign["max_contractors"] + additional_contractors,
                "notes": f"Manual escalation triggered at {datetime.now().isoformat()}"
            })\
            .eq("id", campaign_id).execute()

        # Log the escalation
        check_in_result = supabase.table("campaign_check_ins").insert({
            "campaign_id": campaign_id,
            "check_in_time": datetime.now().isoformat(),
            "progress_percentage": 0,  # Manual trigger
            "escalation_triggered": True,
            "contractors_added": additional_contractors,
            "notes": "Manual escalation triggered from admin dashboard"
        }).execute()

        return {
            "success": True,
            "message": f"Added {additional_contractors} contractors to campaign",
            "new_max": campaign["max_contractors"] + additional_contractors
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error triggering escalation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns/check-ins/upcoming")
async def get_upcoming_check_ins():
    """Get all upcoming check-ins across all active campaigns"""
    try:
        # Get check-ins scheduled for the next 24 hours
        future_time = (datetime.now() + timedelta(hours=24)).isoformat()

        result = supabase.table("campaign_check_ins")\
            .select("*, outreach_campaigns!inner(id, bid_card_id, status)")\
            .eq("status", "pending")\
            .eq("outreach_campaigns.status", "active")\
            .lte("scheduled_time", future_time)\
            .order("scheduled_time").execute()

        upcoming = []
        for check_in in result.data:
            upcoming.append({
                "campaign_id": check_in["campaign_id"],
                "check_in_percentage": check_in["check_in_percentage"],
                "scheduled_time": check_in["scheduled_time"],
                "time_until": calculate_time_until(check_in["scheduled_time"]),
                "escalation_needed": check_in.get("escalation_needed", False)
            })

        return {
            "upcoming_check_ins": upcoming,
            "total": len(upcoming)
        }

    except Exception as e:
        print(f"Error fetching upcoming check-ins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def calculate_time_until(scheduled_time: str) -> str:
    """Calculate human-readable time until a scheduled event"""
    try:
        scheduled = datetime.fromisoformat(scheduled_time.replace("Z", "+00:00"))
        now = datetime.now()
        diff = scheduled - now

        if diff.total_seconds() <= 0:
            return "Now"

        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    except:
        return "Unknown"
