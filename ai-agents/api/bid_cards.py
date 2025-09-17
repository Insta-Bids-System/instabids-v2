"""
Bid Card Public API Endpoints
Handles public viewing and tracking of bid cards
"""

import os
import secrets
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field
from supabase import Client, create_client


router = APIRouter(prefix="/api/bid-cards", tags=["bid-cards"])

# Initialize Supabase client
supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_ANON_KEY"]
)

class BidCardView(BaseModel):
    """Track bid card view"""
    contractor_lead_id: Optional[str] = None
    session_id: Optional[str] = None
    referrer: Optional[str] = None

class EngagementEvent(BaseModel):
    """Track engagement events"""
    view_id: str
    event_type: str = Field(..., pattern="^(photo_view|contact_click|share|save|cta_click)$")
    event_data: Optional[dict[str, Any]] = {}

class PublicBidCard(BaseModel):
    """Public bid card data (no PII)"""
    id: str
    project_type: str
    timeline: str
    budget_display: str
    location: dict[str, str]  # Only city and state
    project_details: dict[str, Any]
    photo_urls: list[str]
    hero_image_url: Optional[str]
    created_at: datetime
    view_count: int
    days_until_deadline: Optional[int]

def generate_session_id() -> str:
    """Generate a secure session ID for tracking"""
    return secrets.token_urlsafe(32)

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    # Check for proxy headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"

@router.get("/{bid_card_id}", response_model=PublicBidCard)
async def get_public_bid_card(
    bid_card_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Get public bid card details (no auth required)
    This endpoint is publicly accessible for contractors to view projects
    """
    try:
        # Fetch bid card with only public fields
        result = supabase.table("bid_cards").select(
            "id, project_type, budget_display, location, "
            "project_details, photo_urls, hero_image_url, created_at, "
            "view_count, urgency"
        ).eq("id", bid_card_id).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Bid card not found")

        bid_card = result.data

        # Strip any PII from location (only keep city and state)
        if bid_card.get("location"):
            bid_card["location"] = {
                "city": bid_card["location"].get("city", ""),
                "state": bid_card["location"].get("state", "")
            }

        # Extract timeline from project_details if not a direct field
        timeline = bid_card.get("timeline", "")
        if not timeline and bid_card.get("project_details"):
            project_details = bid_card["project_details"]
            if isinstance(project_details, dict):
                timeline_info = project_details.get("timeline", {})
                if isinstance(timeline_info, dict):
                    timeline = timeline_info.get("description", "Flexible timeline")
                elif isinstance(timeline_info, str):
                    timeline = timeline_info
                else:
                    timeline = "Flexible timeline"
            else:
                timeline = "Flexible timeline"

        if not timeline:
            timeline = "Flexible timeline"

        # Calculate days until deadline based on urgency
        urgency_days = {
            "emergency": 7,
            "week": 7,
            "month": 30,
            "flexible": None
        }
        days_until_deadline = urgency_days.get(bid_card.get("urgency", "").lower())

        # Track view in background
        background_tasks.add_task(
            track_view_internal,
            bid_card_id=bid_card_id,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent", ""),
            referrer=request.headers.get("Referer", "")
        )

        # Prepare response data
        response_data = {
            "id": bid_card["id"],
            "project_type": bid_card["project_type"],
            "timeline": timeline,
            "budget_display": bid_card["budget_display"],
            "location": bid_card["location"],
            "project_details": bid_card.get("project_details", {}),
            "photo_urls": bid_card.get("photo_urls", []),
            "hero_image_url": bid_card.get("hero_image_url"),
            "created_at": bid_card["created_at"],
            "view_count": bid_card.get("view_count", 0),
            "days_until_deadline": days_until_deadline
        }

        return PublicBidCard(**response_data)

    except Exception as e:
        if hasattr(e, "status_code") and e.status_code == 404:
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{bid_card_id}/track-view")
async def track_bid_card_view(
    bid_card_id: str,
    view_data: BidCardView,
    request: Request
):
    """Track when a contractor views a bid card"""
    try:
        # Generate session ID if not provided
        session_id = view_data.session_id or generate_session_id()

        # Create view record
        view_record = {
            "bid_card_id": bid_card_id,
            "contractor_lead_id": view_data.contractor_lead_id,
            "ip_address": get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", ""),
            "referrer": view_data.referrer or request.headers.get("Referer", ""),
            "session_id": session_id
        }

        result = supabase.table("bid_card_views").insert(view_record).execute()

        # Update view counts
        supabase.rpc("increment_bid_card_views", {"bid_card_id": bid_card_id}).execute()

        return {
            "success": True,
            "view_id": result.data[0]["id"],
            "session_id": session_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{bid_card_id}/track-engagement")
async def track_engagement_event(
    bid_card_id: str,
    event: EngagementEvent
):
    """Track engagement events on bid card"""
    try:
        # Verify the view exists
        view_check = supabase.table("bid_card_views").select("id").eq("id", event.view_id).single().execute()

        if not view_check.data:
            raise HTTPException(status_code=404, detail="View session not found")

        # Create engagement event
        event_record = {
            "bid_card_view_id": event.view_id,
            "event_type": event.event_type,
            "event_data": event.event_data
        }

        result = supabase.table("bid_card_engagement_events").insert(event_record).execute()

        # If CTA clicked, update the view record
        if event.event_type == "cta_click":
            supabase.table("bid_card_views").update({
                "clicked_cta": True
            }).eq("id", event.view_id).execute()

        return {"success": True, "event_id": result.data[0]["id"]}

    except Exception as e:
        if hasattr(e, "status_code") and e.status_code == 404:
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{bid_card_id}/similar")
async def get_similar_bid_cards(
    bid_card_id: str,
    limit: int = 3
):
    """Get similar bid cards for cross-promotion"""
    try:
        # Get the current bid card
        current = supabase.table("bid_cards").select(
            "project_type, location, budget_range"
        ).eq("id", bid_card_id).single().execute()

        if not current.data:
            raise HTTPException(status_code=404, detail="Bid card not found")

        # Find similar bid cards
        similar = supabase.table("bid_cards").select(
            "id, project_type, timeline, budget_display, location, hero_image_url"
        ).eq("project_type", current.data["project_type"]) \
         .neq("id", bid_card_id) \
         .limit(limit) \
         .execute()

        # Strip PII from locations
        for card in similar.data:
            if card.get("location"):
                card["location"] = {
                    "city": card["location"].get("city", ""),
                    "state": card["location"].get("state", "")
                }

        return {"similar_projects": similar.data}

    except Exception as e:
        if hasattr(e, "status_code") and e.status_code == 404:
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{bid_card_id}/express-interest")
async def express_interest(
    bid_card_id: str,
    contractor_info: dict[str, Any],
    request: Request
):
    """Allow contractors to express interest in a project"""
    try:
        # Create a lead record for follow-up
        {
            "bid_card_id": bid_card_id,
            "contact_info": contractor_info,
            "source": "bid_card_cta",
            "ip_address": get_client_ip(request),
            "created_at": datetime.utcnow().isoformat()
        }

        # Store in a leads table (you'll need to create this)
        # For now, we'll track it as an engagement event
        view_record = {
            "bid_card_id": bid_card_id,
            "ip_address": get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", ""),
            "clicked_cta": True,
            "session_id": generate_session_id()
        }

        view_result = supabase.table("bid_card_views").insert(view_record).execute()

        # Track the interest event
        event_record = {
            "bid_card_view_id": view_result.data[0]["id"],
            "event_type": "cta_click",
            "event_data": {
                "contractor_info": contractor_info,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        supabase.table("bid_card_engagement_events").insert(event_record).execute()

        return {
            "success": True,
            "message": "Thank you for your interest! We'll be in touch soon.",
            "lead_id": view_result.data[0]["id"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def track_view_internal(
    bid_card_id: str,
    ip_address: str,
    user_agent: str,
    referrer: str
):
    """Internal function to track views in background"""
    try:
        view_record = {
            "bid_card_id": bid_card_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "referrer": referrer,
            "session_id": generate_session_id()
        }

        supabase.table("bid_card_views").insert(view_record).execute()

        # Update view count
        supabase.table("bid_cards").update({
            "view_count": supabase.table("bid_cards").select("view_count").eq("id", bid_card_id).single().execute().data["view_count"] + 1
        }).eq("id", bid_card_id).execute()

    except Exception:
        # Don't fail the request if tracking fails
        pass
