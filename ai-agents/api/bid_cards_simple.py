"""
Simplified Bid Cards API - Works with existing database structure
"""
import os
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import create_client


# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(supabase_url, supabase_key)

router = APIRouter(prefix="/api/bid-cards", tags=["bid-cards"])

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

class ExpressInterestRequest(BaseModel):
    """Request to express interest in a bid card"""
    company_name: str
    contact_name: str
    email: str
    phone: str
    message: Optional[str] = ""

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"

def load_html_template() -> str:
    """Load HTML template for bid card previews"""
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "bid_card_preview.html")
    try:
        with open(template_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback minimal template
        return """<!DOCTYPE html>
<html><head>
<title>{{project_type}} Project - Instabids</title>
<meta property="og:title" content="{{project_type}} - {{budget_display}}">
<meta property="og:description" content="{{project_type}} in {{location_city}}{{location_state}}. {{timeline}}">
<meta property="og:image" content="{{og_image_url}}">
</head><body>
<h1>{{project_type}}</h1>
<p>Budget: {{budget_display}}</p>
<p>Location: {{location_city}}{{location_state}}</p>
<p>Timeline: {{timeline}}</p>
</body></html>"""

def get_project_icon(project_type: str) -> str:
    """Get emoji icon for project type"""
    project_icons = {
        "kitchen_remodel": "🏠",
        "bathroom_remodel": "🚿",
        "roofing": "🏘️",
        "flooring": "🪵",
        "painting": "🎨",
        "landscaping": "🌿",
        "electrical": "⚡",
        "plumbing": "🔧",
        "hvac": "🌡️",
        "windows": "🪟",
        "siding": "🏗️",
        "deck": "🪜",
        "fence": "🚧",
        "driveway": "🛣️"
    }
    return project_icons.get(project_type.lower(), "🔨")

def generate_simple_og_image(bid_card_data: dict[str, Any]) -> str:
    """Generate a simple Open Graph image URL"""
    # For now, return a placeholder image service URL
    # In production, this would use the OG image generator
    project_type = bid_card_data.get("project_type", "project").replace("_", "%20")
    budget = bid_card_data.get("budget_display", "Budget%20TBD").replace("$", "%24").replace(" ", "%20")
    location = f"{bid_card_data.get('location', {}).get('city', 'Location')}".replace(" ", "%20")

    # Use a placeholder image service (in production, use our OG generator)
    return f"https://via.placeholder.com/1200x630/667eea/ffffff?text={project_type}+{budget}+{location}"

@router.get("/{bid_card_id}/preview", response_class=HTMLResponse)
async def get_bid_card_preview(
    bid_card_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Get rich HTML preview of bid card with Open Graph meta tags
    Perfect for sharing in social media, emails, SMS, etc.
    """
    try:
        # Get bid card data (reuse logic from JSON endpoint)
        bid_card_data = await _get_bid_card_data(bid_card_id, request, background_tasks)

        # Load HTML template
        template = load_html_template()

        # Prepare template variables
        location_city = bid_card_data["location"].get("city", "Location")
        location_state = bid_card_data["location"].get("state", "")
        location_state_formatted = f", {location_state}" if location_state else ""

        project_type_display = bid_card_data["project_type"].replace("_", " ").title()
        current_url = str(request.url)
        api_url = current_url.replace("/preview", "")
        og_image_url = generate_simple_og_image(bid_card_data)

        # Template replacements
        template_vars = {
            "project_type": project_type_display,
            "project_icon": get_project_icon(bid_card_data["project_type"]),
            "budget_display": bid_card_data["budget_display"],
            "timeline": bid_card_data["timeline"],
            "location_city": location_city,
            "location_state": location_state_formatted,
            "bid_card_id": bid_card_id,
            "bid_card_id_short": bid_card_id[:8],
            "current_url": current_url,
            "api_url": api_url,
            "og_image_url": og_image_url
        }

        # Replace template variables
        html_content = template
        for key, value in template_vars.items():
            html_content = html_content.replace(f"{{{{{key}}}}}", str(value))

        return HTMLResponse(content=html_content, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _get_bid_card_data(bid_card_id: str, request: Request, background_tasks: BackgroundTasks) -> dict[str, Any]:
    """
    Shared helper function to get bid card data
    """
    # Fetch bid card with actual columns from database
    result = supabase.table("bid_cards").select(
        "id, project_type, urgency_level, budget_min, budget_max, "
        "bid_document, requirements_extracted, created_at, status"
    ).eq("id", bid_card_id).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Bid card not found")

    bid_card = result.data

    # Extract location from bid_document or requirements_extracted
    location = {"city": "Not specified", "state": ""}
    if bid_card.get("bid_document"):
        bid_doc = bid_card["bid_document"]
        if isinstance(bid_doc, dict) and "location" in bid_doc:
            location = bid_doc["location"]

    if bid_card.get("requirements_extracted"):
        req_ext = bid_card["requirements_extracted"]
        if isinstance(req_ext, dict) and "location" in req_ext:
            location = req_ext["location"]

    # Create timeline description from urgency_level
    urgency_level = bid_card.get("urgency_level", "flexible").lower()
    timeline_descriptions = {
        "emergency": "Emergency - ASAP",
        "week": "Within 1 week",
        "month": "Within 1 month",
        "flexible": "Flexible timeline"
    }
    timeline = timeline_descriptions.get(urgency_level, "Flexible timeline")

    # Create budget display
    budget_min = bid_card.get("budget_min", 0)
    budget_max = bid_card.get("budget_max", 0)
    if budget_min and budget_max:
        budget_display = f"${budget_min:,} - ${budget_max:,}"
    elif budget_min:
        budget_display = f"${budget_min:,}+"
    else:
        budget_display = "Budget not specified"

    # Calculate days until deadline based on urgency
    urgency_days = {
        "emergency": 7,
        "week": 7,
        "month": 30,
        "flexible": None
    }
    days_until_deadline = urgency_days.get(urgency_level)

    # Simple view tracking (skip for now since view_count column may not exist)
    # background_tasks.add_task(increment_view_count, bid_card_id)

    # Return standardized data
    return {
        "id": bid_card["id"],
        "project_type": bid_card["project_type"],
        "timeline": timeline,
        "budget_display": budget_display,
        "location": location,
        "project_details": bid_card.get("bid_document", {}),
        "photo_urls": [],  # No photo URLs in current schema
        "hero_image_url": None,  # No hero image in current schema
        "created_at": bid_card["created_at"],
        "view_count": 0,  # Default to 0 since column doesn't exist
        "days_until_deadline": days_until_deadline
    }

@router.get("/{bid_card_id}", response_model=PublicBidCard)
async def get_public_bid_card(
    bid_card_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Get public bid card details (no auth required)
    """
    try:
        bid_card_data = await _get_bid_card_data(bid_card_id, request, background_tasks)
        return PublicBidCard(**bid_card_data)

    except Exception as e:
        if hasattr(e, "status_code") and e.status_code == 404:
            raise e
        print(f"Error fetching bid card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/homeowner/{user_id}")
async def get_homeowner_bid_cards(user_id: str):
    """Get all bid cards for a specific homeowner"""
    try:
        # First get all conversations for this user
        conversations_result = supabase.table("agent_conversations").select("thread_id").eq("user_id", user_id).execute()

        if not conversations_result.data:
            return []

        # Get thread IDs
        thread_ids = [conv["thread_id"] for conv in conversations_result.data]

        # Get bid cards linked to these conversations
        result = supabase.table("bid_cards").select("*").in_("cia_thread_id", thread_ids).order("created_at", desc=True).execute()

        if not result.data:
            return []

        return result.data

    except Exception as e:
        print(f"[API ERROR] Failed to get homeowner bid cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{bid_card_id}/express-interest")
async def express_interest(
    bid_card_id: str,
    request: ExpressInterestRequest
):
    """
    Contractor expresses interest in bid card
    """
    try:
        # Verify bid card exists
        bid_result = supabase.table("bid_cards").select("id").eq("id", bid_card_id).single().execute()

        if not bid_result.data:
            raise HTTPException(status_code=404, detail="Bid card not found")

        # Create contractor lead record
        contractor_data = {
            "company_name": request.company_name,
            "contact_name": request.contact_name,
            "email": request.email,
            "phone": request.phone,
            "website": "",
            "service_area": [],
            "specialties": [],
            "company_size": "unknown",
            "status": "lead",
            "source": "bid_card_interest"
        }

        # Insert contractor if not exists
        contractor_result = supabase.table("contractor_leads").upsert(
            contractor_data,
            on_conflict="email"
        ).execute()

        # Create outreach attempt record
        if contractor_result.data:
            contractor_id = contractor_result.data[0]["id"]

            outreach_data = {
                "contractor_lead_id": contractor_id,
                "bid_card_id": bid_card_id,
                "channel": "web_form",
                "status": "interested",
                "message_content": f"Contractor {request.company_name} expressed interest via bid card form. Message: {request.message}",
                "response_received": True,
                "response_content": f"Interest expressed by {request.contact_name}"
            }

            supabase.table("contractor_outreach_attempts").insert(outreach_data).execute()

        return {"success": True, "message": "Interest recorded successfully"}

    except Exception as e:
        print(f"Error recording interest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def increment_view_count(bid_card_id: str):
    """Simple view count increment"""
    try:
        # Get current count
        result = supabase.table("bid_cards").select("view_count").eq("id", bid_card_id).single().execute()

        if result.data:
            current_count = result.data.get("view_count", 0) or 0
            new_count = current_count + 1

            # Update count
            supabase.table("bid_cards").update({
                "view_count": new_count
            }).eq("id", bid_card_id).execute()

    except Exception as e:
        print(f"Error incrementing view count: {e}")
        # Don't fail if view tracking fails
