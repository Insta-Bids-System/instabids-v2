"""
Enhanced Bid Card API endpoints
Supports multiple UI variants: homeowner editing, contractor bidding, marketplace browsing
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
# from supabase import Client  # Not needed, using database wrapper

# Import auth and database utilities from existing project structure
from database_simple import db
from agents.intelligent_messaging_agent import process_intelligent_message
from config.service_urls import get_backend_url


logger = logging.getLogger(__name__)



def get_supabase_client():
    return db

# For now, create a simple auth dependency that returns a test user
# This should be replaced with the actual auth system
def get_current_user():
    return {
        "id": "test-user-id",
        "user_type": "homeowner"
    }

router = APIRouter(tags=["bid-cards"])

# Pydantic models for request/response
class BudgetRange(BaseModel):
    min: float
    max: float

class Timeline(BaseModel):
    start_date: datetime
    end_date: datetime
    flexibility: str = "flexible"

class Location(BaseModel):
    address: Optional[str] = None
    city: str
    state: str
    zip_code: str
    coordinates: Optional[dict[str, float]] = None

class BidCardCreate(BaseModel):
    title: str
    description: str
    budget_range: BudgetRange
    timeline: Timeline
    location: Location
    project_type: str
    categories: list[str]
    requirements: list[str]
    preferred_schedule: Optional[list[str]] = []
    group_bid_eligible: bool = False
    allows_questions: bool = True
    requires_bid_before_message: bool = False
    visibility: str = "public"
    metadata: Optional[dict[str, Any]] = {}

class BidCardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    budget_range: Optional[BudgetRange] = None
    timeline: Optional[Timeline] = None
    location: Optional[Location] = None
    project_type: Optional[str] = None
    categories: Optional[list[str]] = None
    requirements: Optional[list[str]] = None
    preferred_schedule: Optional[list[str]] = None
    group_bid_eligible: Optional[bool] = None
    allows_questions: Optional[bool] = None
    requires_bid_before_message: Optional[bool] = None
    visibility: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

# BidSubmission model removed - using bid_card_api_simple.py for bid submissions

class MessageSend(BaseModel):
    bid_card_id: str
    bid_id: Optional[str] = None
    recipient_id: str
    content: str
    attachments: Optional[list[dict[str, Any]]] = []
    image_data: Optional[str] = None  # Base64 encoded image

# Helper functions
def serialize_bid_card(bid_card: dict[str, Any]) -> dict[str, Any]:
    """Convert database bid card to API response format"""
    return {
        "id": bid_card["id"],
        "project_id": bid_card.get("id"),  # Use bid card ID as project ID for now
        "user_id": bid_card.get("user_id"),
        "title": bid_card.get("title", ""),
        "description": bid_card.get("description", ""),
        "budget_range": {
            "min": float(bid_card.get("budget_min") or 0),
            "max": float(bid_card.get("budget_max") or 0)
        },
        "timeline": {
            "start_date": bid_card.get("timeline_start", ""),
            "end_date": bid_card.get("timeline_end", ""),
            "flexibility": bid_card.get("timeline_flexibility", "flexible")
        },
        "location": {
            "address": bid_card.get("location_address"),
            "city": bid_card.get("location_city", ""),
            "state": bid_card.get("location_state", ""),
            "zip_code": bid_card.get("location_zip", ""),
            "coordinates": {
                "lat": float(bid_card["location_lat"]) if bid_card.get("location_lat") else None,
                "lng": float(bid_card["location_lng"]) if bid_card.get("location_lng") else None
            } if bid_card.get("location_lat") else None
        },
        "project_type": bid_card.get("project_type", ""),
        "categories": bid_card.get("categories", []),
        "requirements": bid_card.get("requirements", []),
        "preferred_schedule": bid_card.get("preferred_schedule", []),
        "status": bid_card.get("status", "draft"),
        "visibility": bid_card.get("visibility", "public"),
        "group_bid_eligible": bid_card.get("group_bid_eligible", False),
        "group_bid_id": bid_card.get("group_bid_id"),
        "bid_count": bid_card.get("bid_count", 0),
        "interested_contractors": bid_card.get("interested_contractors", 0),
        "bid_deadline": bid_card.get("bid_deadline"),
        "auto_close_after_bids": bid_card.get("auto_close_after_bids"),
        "allows_questions": bid_card.get("allows_questions", True),
        "requires_bid_before_message": bid_card.get("requires_bid_before_message", False),
        "created_at": bid_card.get("created_at"),
        "updated_at": bid_card.get("updated_at"),
        "published_at": bid_card.get("published_at"),
        "metadata": bid_card.get("metadata", {}),
        
        # Date flow fields for exact deadline tracking
        "bid_collection_deadline": bid_card.get("bid_collection_deadline"),
        "project_completion_deadline": bid_card.get("project_completion_deadline"),
        "deadline_hard": bid_card.get("deadline_hard", False),
        "deadline_context": bid_card.get("deadline_context"),
        
        # Contractor-specific fields (will be properly calculated in future)
        "can_bid": True,  # For now, allow bidding on all active projects
        "has_bid": False,  # For now, assume contractor hasn't bid yet
        "my_bid": None,   # No existing bid for this contractor
        "distance_miles": 5.2,  # Mock distance - will be calculated based on contractor location
        "match_score": 0.85,    # Mock match score - will be calculated based on contractor profile
        
        # Additional contractor view fields
        "homeowner_verified": bid_card.get("homeowner_verified", True),
        "response_time_hours": bid_card.get("response_time_hours", 24),
        "success_rate": bid_card.get("success_rate", 0.95),
        "is_featured": bid_card.get("is_featured", False),
        "is_urgent": bid_card.get("is_urgent", False),
        "images": [],  # Mock empty images array
        
        # Service complexity classification fields
        "service_complexity": bid_card.get("service_complexity", "single-trade"),
        "trade_count": bid_card.get("trade_count", 1),
        "primary_trade": bid_card.get("primary_trade", ""),
        "secondary_trades": bid_card.get("secondary_trades", [])
    }

# Endpoints
@router.post("", response_model=dict[str, Any])
async def create_bid_card(
    bid_card: BidCardCreate,
    db = Depends(get_supabase_client)
):
    """Create a new bid card for a homeowner"""
    try:
        # Get the current user
        current_user = get_current_user()

        # Get the project_id for this homeowner
        project_response = db.client.table("projects").select("id").eq("user_id", current_user["id"]).single().execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="No project found for this homeowner")

        bid_card_data = {
            "project_id": project_response.data["id"],
            "user_id": current_user["id"],
            "title": bid_card.title,
            "description": bid_card.description,
            "budget_min": bid_card.budget_range.min,
            "budget_max": bid_card.budget_range.max,
            "timeline_start": bid_card.timeline.start_date.isoformat(),
            "timeline_end": bid_card.timeline.end_date.isoformat(),
            "timeline_flexibility": bid_card.timeline.flexibility,
            "location_address": bid_card.location.address,
            "location_city": bid_card.location.city,
            "location_state": bid_card.location.state,
            "location_zip": bid_card.location.zip_code,
            "location_lat": bid_card.location.coordinates.get("lat") if bid_card.location.coordinates else None,
            "location_lng": bid_card.location.coordinates.get("lng") if bid_card.location.coordinates else None,
            "project_type": bid_card.project_type,
            "categories": bid_card.categories,
            "requirements": bid_card.requirements,
            "preferred_schedule": bid_card.preferred_schedule,
            "group_bid_eligible": bid_card.group_bid_eligible,
            "allows_questions": bid_card.allows_questions,
            "requires_bid_before_message": bid_card.requires_bid_before_message,
            "visibility": bid_card.visibility,
            "metadata": json.dumps(bid_card.metadata),
            "status": "draft"
        }

        response = db.client.table("bid_cards").insert(bid_card_data).execute()
        return serialize_bid_card(response.data[0])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{bid_card_id}", response_model=dict[str, Any])
async def update_bid_card(
    bid_card_id: str,
    updates: BidCardUpdate,
    # current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_supabase_client)
):
    """Update a bid card (homeowner only)"""
    try:
        # Verify ownership
        existing = db.client.table("bid_cards").select("*").eq("id", bid_card_id).eq("user_id", current_user["id"]).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Bid card not found or you don't have permission")

        update_data = {}
        if updates.title is not None:
            update_data["title"] = updates.title
        if updates.description is not None:
            update_data["description"] = updates.description
        if updates.budget_range is not None:
            update_data["budget_min"] = updates.budget_range.min
            update_data["budget_max"] = updates.budget_range.max
        if updates.timeline is not None:
            update_data["timeline_start"] = updates.timeline.start_date.isoformat()
            update_data["timeline_end"] = updates.timeline.end_date.isoformat()
            update_data["timeline_flexibility"] = updates.timeline.flexibility
        if updates.location is not None:
            update_data["location_address"] = updates.location.address
            update_data["location_city"] = updates.location.city
            update_data["location_state"] = updates.location.state
            update_data["location_zip"] = updates.location.zip_code
            if updates.location.coordinates:
                update_data["location_lat"] = updates.location.coordinates.get("lat")
                update_data["location_lng"] = updates.location.coordinates.get("lng")
        if updates.project_type is not None:
            update_data["project_type"] = updates.project_type
        if updates.categories is not None:
            update_data["categories"] = updates.categories
        if updates.requirements is not None:
            update_data["requirements"] = updates.requirements
        if updates.preferred_schedule is not None:
            update_data["preferred_schedule"] = updates.preferred_schedule
        if updates.group_bid_eligible is not None:
            update_data["group_bid_eligible"] = updates.group_bid_eligible
        if updates.allows_questions is not None:
            update_data["allows_questions"] = updates.allows_questions
        if updates.requires_bid_before_message is not None:
            update_data["requires_bid_before_message"] = updates.requires_bid_before_message
        if updates.visibility is not None:
            update_data["visibility"] = updates.visibility
        if updates.metadata is not None:
            update_data["metadata"] = json.dumps(updates.metadata)

        # Check if we're publishing
        if "status" in update_data and update_data["status"] == "active" and existing.data["status"] == "draft":
            update_data["published_at"] = datetime.utcnow().isoformat()

        response = db.client.table("bid_cards").update(update_data).eq("id", bid_card_id).execute()
        return serialize_bid_card(response.data[0])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{bid_card_id}")
async def delete_bid_card(
    bid_card_id: str,
    # current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_supabase_client)
):
    """Delete a bid card (homeowner only)"""
    try:
        # Verify ownership and that it's still in draft
        existing = db.client.table("bid_cards").select("*").eq("id", bid_card_id).eq("user_id", current_user["id"]).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Bid card not found or you don't have permission")
        if existing.data["status"] != "draft":
            raise HTTPException(status_code=400, detail="Cannot delete published bid cards")

        db.client.table("bid_cards").delete().eq("id", bid_card_id).execute()
        return {"message": "Bid card deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/homeowner", response_model=list[dict[str, Any]])
async def get_homeowner_bid_cards(
    # current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_supabase_client)
):
    """Get all bid cards for the current homeowner with enhanced view data"""
    try:
        response = db.client.table("bid_cards").select("*").eq("user_id", current_user["id"]).execute()

        bid_cards = []
        for card in response.data:
            # Get unread message count
            unread_response = db.client.table("bid_card_messages").select("id").eq("bid_card_id", card["id"]).eq("recipient_id", current_user["id"]).eq("is_read", False).execute()

            # Get pending questions count
            questions_response = db.client.table("bid_card_messages").select("id").eq("bid_card_id", card["id"]).eq("recipient_id", current_user["id"]).eq("is_read", False).is_("reply_to_id", None).execute()

            enhanced_card = serialize_bid_card(card)
            enhanced_card.update({
                "can_edit": card["status"] in ["draft", "active"],
                "can_delete": card["status"] == "draft",
                "can_publish": card["status"] == "draft",
                "unread_messages_count": len(unread_response.data),
                "pending_questions": len(questions_response.data)
            })
            bid_cards.append(enhanced_card)

        return bid_cards

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=dict[str, Any])
async def search_bid_cards(
    status: Optional[list[str]] = Query(None),
    project_types: Optional[list[str]] = Query(None),
    categories: Optional[list[str]] = Query(None),
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    radius_miles: Optional[int] = None,
    budget_min: Optional[float] = None,
    budget_max: Optional[float] = None,
    start_after: Optional[datetime] = None,
    start_before: Optional[datetime] = None,
    group_bid_eligible: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 12,
    # current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db = Depends(get_supabase_client)
):
    """Search bid cards for contractors with filtering and sorting"""
    try:
        # Debug logging to see what parameters we're getting
        logger.info(f"Search params received: zip_code='{zip_code}' (type: {type(zip_code)}), radius_miles='{radius_miles}' (type: {type(radius_miles)})")

        # If radius search parameters are present, redirect to contractor-jobs API
        if zip_code and radius_miles:
            logger.info(f"Radius search detected: zip_code={zip_code}, radius_miles={radius_miles}")
            import httpx

            # Convert bid-cards parameters to contractor-jobs parameters
            contractor_params = {
                "zip_code": zip_code,
                "radius_miles": radius_miles,
                "page": page,
                "page_size": page_size
            }

            # Add project type filters if present
            if project_types:
                contractor_params["project_types"] = project_types

            logger.info(f"Making request to contractor-jobs API with params: {contractor_params}")

            # Make internal request to contractor-jobs API
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{get_backend_url()}/api/contractor-jobs/search",
                        params=contractor_params
                    )

                logger.info(f"Contractor-jobs API responded with status: {response.status_code}")

                # Transform response to match bid-cards format
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Got {len(data.get('job_opportunities', []))} job opportunities from contractor-jobs API")
                    # Transform job_opportunities to bid_cards format
                    bid_cards = []
                    for job in data.get("job_opportunities", []):
                        bid_card = {
                            "id": job["id"],
                            "bid_card_number": job.get("bid_card_number"),
                            "title": job["title"],
                            "description": job["description"],
                            "project_type": job["project_type"],
                            "status": job["status"],
                            "budget_min": job["budget_range"]["min"],
                            "budget_max": job["budget_range"]["max"],
                            "location_city": job["location"]["city"],
                            "location_state": job["location"]["state"],
                            "location_zip": job["location"]["zip_code"],
                            "timeline_start": job["timeline"]["start_date"],
                            "timeline_end": job["timeline"]["end_date"],
                            "contractor_count_needed": job.get("contractor_count_needed", 1),
                            "bid_count": job.get("bid_count", 0),
                            "categories": job.get("categories", []),
                            "group_bid_eligible": job.get("group_bid_eligible", False),
                            "created_at": job.get("created_at"),
                            "homeowner_verified": True,
                            "response_time_hours": 24,
                            "success_rate": 0.95,
                            "is_featured": False,
                            "is_urgent": False,
                            "distance_miles": job.get("distance_miles")
                        }
                        bid_cards.append(bid_card)

                    return {
                        "bid_cards": bid_cards,
                        "total": data["total"],
                        "page": data["page"],
                        "page_size": data["page_size"],
                        "has_more": data["has_more"]
                    }
                else:
                    # If contractor-jobs API fails, fall back to regular search
                    logger.error(f"Contractor-jobs API failed with status {response.status_code}")
            except Exception as e:
                logger.error(f"Error calling contractor-jobs API: {e}")
                # Fall back to regular search

        # Regular search if not radius search
        query = db.client.table("bid_cards").select("*")

        # Apply filters
        if status:
            query = query.in_("status", status)
        else:
            query = query.in_("status", ["active", "collecting_bids"])

        if project_types:
            query = query.in_("project_type", project_types)

        if categories:
            # This would need a more complex query for array overlap
            pass

        if city:
            query = query.eq("location_city", city)
        if state:
            query = query.eq("location_state", state)

        # For now, just do exact zip match
        # Radius search is handled by the redirect in main.py
        if zip_code:
            query = query.eq("location_zip", zip_code)

        if budget_min:
            query = query.gte("budget_max", budget_min)
        if budget_max:
            query = query.lte("budget_min", budget_max)

        if start_after:
            query = query.gte("timeline_start", start_after.isoformat())
        if start_before:
            query = query.lte("timeline_start", start_before.isoformat())

        if group_bid_eligible is not None:
            query = query.eq("group_bid_eligible", group_bid_eligible)

        # Apply sorting
        query = query.order(sort_by, desc=(sort_order == "desc"))

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        response = query.execute()

        # Get total count for pagination (without pagination limits)
        count_query = db.client.table("bid_cards").select("*", count="exact")
        
        # Apply same filters for count
        if status:
            count_query = count_query.in_("status", status)
        else:
            count_query = count_query.in_("status", ["active", "collecting_bids"])

        if project_types:
            count_query = count_query.in_("project_type", project_types)
            
        if city:
            count_query = count_query.eq("location_city", city)
        if state:
            count_query = count_query.eq("location_state", state)
        if zip_code:
            count_query = count_query.eq("location_zip", zip_code)

        if budget_min:
            count_query = count_query.gte("budget_max", budget_min)
        if budget_max:
            count_query = count_query.lte("budget_min", budget_max)

        if start_after:
            count_query = count_query.gte("timeline_start", start_after.isoformat())
        if start_before:
            count_query = count_query.lte("timeline_start", start_before.isoformat())

        if group_bid_eligible is not None:
            count_query = count_query.eq("group_bid_eligible", group_bid_eligible)

        count_response = count_query.execute()
        total_count = count_response.count if count_response.count is not None else 0

        # Enhance bid cards for marketplace view
        bid_cards = []
        for card in response.data:
            marketplace_card = serialize_bid_card(card)
            # Remove sensitive info
            marketplace_card.pop("user_id", None)

            # Add marketplace-specific fields
            is_urgent = False
            try:
                if card.get("timeline_start"):
                    start_date = datetime.fromisoformat(card["timeline_start"].replace("Z", "+00:00") if "Z" in card["timeline_start"] else card["timeline_start"])
                    days_until_start = (start_date - datetime.now()).days
                    is_urgent = days_until_start < 7
            except Exception as e:
                logger.warning(f"Error calculating urgency for bid card {card.get('id')}: {e}")
            
            marketplace_card.update({
                "homeowner_verified": True,  # Would check verification status
                "response_time_hours": 24,  # Would calculate from message history
                "success_rate": 0.95,  # Would calculate from completed projects
                "is_featured": False,  # Would check featured status
                "is_urgent": is_urgent
            })

            # Distance calculation is handled by the redirect in main.py

            bid_cards.append(marketplace_card)

        return {
            "bid_cards": bid_cards,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "has_more": (page * page_size) < total_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-token/{token}", response_model=dict[str, Any])
async def get_bid_card_by_token(
    token: str,
    db = Depends(get_supabase_client)
):
    """Get bid card details by token (for external landing page)"""
    try:
        # Query by ID (assuming token is the bid card ID)
        response = db.client.table("bid_cards").select("*").eq("id", token).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Bid card not found")
        
        bid_card = response.data
        
        # Try to find the contractor who received this bid card by looking at outreach attempts
        contractor_lead_id = None
        try:
            outreach_response = db.client.table("contractor_outreach_attempts").select("contractor_lead_id").eq("bid_card_id", token).limit(1).execute()
            if outreach_response.data and len(outreach_response.data) > 0:
                contractor_lead_id = outreach_response.data[0]["contractor_lead_id"]
                logger.info(f"Found contractor_lead_id {contractor_lead_id} for bid card {token}")
        except Exception as e:
            logger.warning(f"Could not find contractor for bid card {token}: {e}")
        
        # Format for external landing page
        return {
            "id": bid_card["id"],
            "public_token": bid_card["id"],  # Using ID as public token
            "contractor_lead_id": contractor_lead_id,  # Include contractor ID if found
            "project_type": bid_card.get("project_type", "Home Improvement"),
            "urgency": bid_card.get("urgency_level", "flexible"),
            "budget_display": f"${bid_card.get('budget_min', 5000)}-${bid_card.get('budget_max', 15000)}",
            "location": {
                "city": bid_card.get("location_city", "Your City"),
                "state": bid_card.get("location_state", "State")
            },
            "contractor_count": bid_card.get("contractor_count_needed", 4),
            "created_at": bid_card.get("created_at"),
            "photo_urls": bid_card.get("photo_urls", []),
            "project_details": {
                "scope_of_work": bid_card.get("scope_of_work", []),
                "property_details": bid_card.get("property_details", {})
            }
        }
    except Exception as e:
        logger.error(f"Error fetching bid card by token {token}: {str(e)}")
        
        # Return mock data for testing when database is unavailable
        return {
            "id": token,
            "public_token": token,
            "contractor_lead_id": "36fab309-1b11-4826-b108-dda79e12ce0d",  # Mock contractor ID
            "project_type": "Kitchen Remodel",
            "urgency": "week",
            "budget_display": "$15,000-$25,000",
            "location": {
                "city": "Orlando",
                "state": "FL"
            },
            "contractor_count": 4,
            "created_at": "2025-08-08T16:00:00Z",
            "photo_urls": [
                "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2340&q=80",
                "https://images.unsplash.com/photo-1565538810643-b5bdb714032a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2338&q=80"
            ],
            "project_details": {
                "scope_of_work": [
                    "Complete kitchen renovation",
                    "Cabinet installation and refinishing", 
                    "Countertop replacement (quartz preferred)",
                    "Appliance installation",
                    "Electrical and plumbing updates"
                ],
                "property_details": {
                    "home_type": "Single Family",
                    "home_age": "Built 1995",
                    "kitchen_size": "Medium (120 sq ft)"
                }
            }
        }

@router.get("/{bid_card_id}/contractor-view", response_model=dict[str, Any])
async def get_bid_card_contractor_view(
    bid_card_id: str,
    # current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_supabase_client)
):
    """Get bid card details for contractor view"""
    try:
        response = db.client.table("bid_cards").select("*").eq("id", bid_card_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Bid card not found")

        contractor_view = serialize_bid_card(response.data)

        # Check if contractor has already bid
        bid_response = db.client.table("contractor_bids").select("*").eq("bid_card_id", bid_card_id).eq("contractor_id", current_user["id"]).execute()

        contractor_view.update({
            "can_bid": response.data["status"] in ["active", "collecting_bids"] and not bid_response.data,
            "has_bid": bool(bid_response.data),
            "my_bid": bid_response.data[0] if bid_response.data else None,
            "distance_miles": 10.5,  # Would calculate actual distance
            "match_score": 0.85  # Would calculate based on contractor profile
        })

        return contractor_view

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Unused bid submission endpoint removed - using bid_card_api_simple.py for production bid submissions

@router.post("/messages", response_model=dict[str, Any])
async def send_bid_card_message(
    message: MessageSend,
    # current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_supabase_client)
):
    """Send a message related to a bid card with intelligent security filtering"""
    try:
        # Get current user (temporary test user for now)
        current_user = get_current_user()
        
        # Determine sender type
        sender_type = "homeowner" if current_user.get("user_type") == "homeowner" else "contractor"

        # Verify permissions
        bid_card = db.client.table("bid_cards").select("*").eq("id", message.bid_card_id).single().execute()
        if not bid_card.data:
            raise HTTPException(status_code=404, detail="Bid card not found")

        # If contractor, check if they need to bid first
        if sender_type == "contractor" and bid_card.data.get("requires_bid_before_message", False):
            bid_check = db.client.table("contractor_bids").select("id").eq("bid_card_id", message.bid_card_id).eq("contractor_id", current_user["id"]).execute()
            if not bid_check.data:
                raise HTTPException(status_code=403, detail="You must submit a bid before messaging")

        # 🚨 CRITICAL: Process message through intelligent security system
        print(f"Processing message through intelligent security system...")
        
        intelligent_result = await process_intelligent_message(
            content=message.content,
            sender_type=sender_type,
            sender_id=current_user["id"],
            bid_card_id=message.bid_card_id,
            recipient_id=message.recipient_id,
            conversation_id=f"bid_card_{message.bid_card_id}",
            attachments=message.attachments or [],
            image_data=message.image_data
        )
        
        print(f"Intelligent messaging result: {intelligent_result}")
        
        # Check if message was approved
        if not intelligent_result.get("approved", False):
            # Message was blocked - return security response
            return {
                "success": False,
                "blocked": True,
                "reason": "Message blocked for security reasons",
                "agent_decision": intelligent_result.get("agent_decision"),
                "threats_detected": intelligent_result.get("threats_detected", []),
                "agent_comments": intelligent_result.get("agent_comments", []),
                "confidence_score": intelligent_result.get("confidence_score", 0)
            }
        
        # Message approved - save the filtered version
        message_data = {
            "bid_card_id": message.bid_card_id,
            "bid_id": message.bid_id,
            "sender_id": current_user["id"],
            "sender_type": sender_type,
            "recipient_id": message.recipient_id,
            "recipient_type": "contractor" if sender_type == "homeowner" else "homeowner",
            "content": intelligent_result.get("filtered_content", message.content),
            "original_content": message.content,  # Store original for audit
            "agent_decision": intelligent_result.get("agent_decision"),
            "confidence_score": intelligent_result.get("confidence_score", 0),
            "created_at": datetime.utcnow().isoformat()
        }

        response = db.client.table("bid_card_messages").insert(message_data).execute()
        new_message = response.data[0]
        
        # Save agent comments if any
        agent_comments = intelligent_result.get("agent_comments", [])
        if agent_comments:
            for comment in agent_comments:
                comment_data = {
                    "message_id": new_message["id"],
                    "bid_card_id": message.bid_card_id,
                    "visible_to_type": comment.get("visible_to"),
                    "visible_to_id": comment.get("user_id"),
                    "content": comment.get("content"),
                    "comment_type": comment.get("type", "info"),
                    "created_at": comment.get("timestamp")
                }
                db.client.table("agent_comments").insert(comment_data).execute()

        # Handle attachments if provided and approved
        if message.attachments:
            attachment_data = [
                {
                    "message_id": new_message["id"],
                    "type": att.get("type", "unknown"),
                    "url": att["url"],
                    "name": att["name"],
                    "size": att.get("size")
                }
                for att in message.attachments
            ]
            db.client.table("message_attachments").insert(attachment_data).execute()

        # Update last_message_at on bid if applicable
        if message.bid_id:
            db.client.table("contractor_bids").update({"last_message_at": datetime.utcnow().isoformat()}).eq("id", message.bid_id).execute()
        
        # Track in My Bids if contractor is sending message
        if sender_type == "contractor":
            try:
                from services.my_bids_tracker import my_bids_tracker
                import asyncio
                # Track bid interaction asynchronously
                asyncio.create_task(my_bids_tracker.track_bid_interaction(
                    contractor_id=current_user["id"],
                    bid_card_id=message.bid_card_id,
                    interaction_type='message_sent',
                    details={
                        'message_preview': filtered_content[:200],
                        'has_attachments': bool(message.attachments),
                        'threats_detected': intelligent_result.get("threats_detected", [])
                    }
                ))
                print(f"Tracked My Bids interaction for contractor {current_user['id']} on bid {message.bid_card_id}")
            except Exception as tracking_error:
                print(f"Failed to track My Bids interaction: {tracking_error}")
                # Don't fail the message send if tracking fails

        # Return success response with intelligent messaging details
        return {
            "success": True,
            "blocked": False,
            "message": new_message,
            "agent_decision": intelligent_result.get("agent_decision"),
            "threats_detected": intelligent_result.get("threats_detected", []),
            "agent_comments": intelligent_result.get("agent_comments", []),
            "confidence_score": intelligent_result.get("confidence_score", 0),
            "filtered_content": intelligent_result.get("filtered_content"),
            "scope_changes_detected": intelligent_result.get("scope_changes_detected", []),
            "requires_bid_update": intelligent_result.get("requires_bid_update", False)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{bid_card_id}/messages", response_model=list[dict[str, Any]])
async def get_bid_card_messages(
    bid_card_id: str,
    bid_id: Optional[str] = None,
    # current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_supabase_client)
):
    """Get messages for a bid card"""
    try:
        query = db.client.table("bid_card_messages").select("*").eq("bid_card_id", bid_card_id)

        if bid_id:
            query = query.eq("bid_id", bid_id)

        # Only show messages where user is sender or recipient
        query = query.or_(f"sender_id.eq.{current_user['id']},recipient_id.eq.{current_user['id']}")

        response = query.order("created_at", desc=False).execute()

        return response.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: str,
    # current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_supabase_client)
):
    """Mark a message as read"""
    try:
        # Verify recipient
        message = db.client.table("bid_card_messages").select("*").eq("id", message_id).eq("recipient_id", current_user["id"]).single().execute()
        if not message.data:
            raise HTTPException(status_code=404, detail="Message not found or you don't have permission")

        db.client.table("bid_card_messages").update({
            "is_read": True,
            "read_at": datetime.utcnow().isoformat()
        }).eq("id", message_id).execute()

        return {"message": "Message marked as read"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{bid_card_id}/unread-count", response_model=dict[str, int])
async def get_unread_message_count(
    bid_card_id: str,
    # current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_supabase_client)
):
    """Get count of unread messages for a bid card"""
    try:
        response = db.client.table("bid_card_messages").select("id").eq("bid_card_id", bid_card_id).eq("recipient_id", current_user["id"]).eq("is_read", False).execute()

        return {"count": len(response.data)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{bid_card_id}/select-contractor")
async def select_winning_contractor(
    bid_card_id: str,
    request: dict
):
    """
    Select a winning contractor and calculate connection fee
    """
    try:
        # For testing - skip authentication
        current_user = {"id": request.get("user_id", "test-homeowner-123")}
        contractor_id = request.get("contractor_id")
        if not contractor_id:
            raise HTTPException(status_code=400, detail="contractor_id is required")
        
        # 1. Verify homeowner owns this bid card
        bid_card = db.client.table("bid_cards").select("*").eq("id", bid_card_id).execute()
        if not bid_card.data or len(bid_card.data) == 0:
            raise HTTPException(status_code=404, detail="Bid card not found")
        
        bid_card_data = bid_card.data[0]
        
        if bid_card_data.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to select contractor for this bid card")
        
        # Check if contractor already selected
        if bid_card_data.get("winner_contractor_id"):
            raise HTTPException(status_code=400, detail="A contractor has already been selected for this project")
        
        # 2. Find the winning bid from submitted_bids
        submitted_bids = bid_card_data.get("bid_document", {}).get("submitted_bids", [])
        winning_bid = None
        
        for bid in submitted_bids:
            if bid.get("contractor_id") == contractor_id:
                winning_bid = bid
                break
        
        if not winning_bid:
            raise HTTPException(status_code=404, detail="Contractor bid not found")
        
        bid_amount = winning_bid.get("bid_amount", 0)
        
        # Note: For production, ensure contractor exists in contractors table
        # For now, proceeding with contractor_id from the bid
        
        # 3. Calculate connection fee
        from api.connection_fee_calculator import ConnectionFeeCalculator
        
        calculator = ConnectionFeeCalculator()
        
        # Determine project category from bid card data
        all_data = bid_card_data.get("bid_document", {}).get("all_extracted_data", {})
        project_category = calculator.determine_project_category(
            service_type=all_data.get("service_type"),
            project_type=bid_card_data.get("project_type"),
            budget_min=all_data.get("budget_min"),
            budget_max=all_data.get("budget_max"),
            urgency_level=all_data.get("urgency_level"),
            group_bid_eligible=bid_card_data.get("group_bid_eligible", False)
        )
        
        # Get referral info if exists
        homeowner_response = db.client.table("homeowners").select("referral_code, referred_by_user_id").eq("id", bid_card_data.get("user_id")).execute()
        referral_code = None
        referrer_user_id = None
        if homeowner_response.data and len(homeowner_response.data) > 0:
            homeowner_data = homeowner_response.data[0]
            referral_code = homeowner_data.get("referral_code")
            referrer_user_id = homeowner_data.get("referred_by_user_id")
        
        # Calculate fee
        fee_result = calculator.calculate_connection_fee(
            winning_bid_amount=bid_amount,
            project_category=project_category,
            referral_code=referral_code,
            referrer_user_id=referrer_user_id
        )
        
        # 4. Save connection fee to database
        connection_fee_data = {
            "bid_card_id": bid_card_id,
            "contractor_id": contractor_id,
            "winning_bid_amount": bid_amount,
            "project_category": project_category,
            "base_fee_amount": fee_result["base_fee"],
            "category_adjustment_factor": fee_result.get("adjustment_factor", 1.0),
            "final_fee_amount": fee_result["final_fee"],
            "platform_portion": fee_result["platform_portion"],
            "referrer_portion": fee_result["referrer_portion"],
            "referral_info": {
                "referral_code": referral_code,
                "referrer_user_id": referrer_user_id
            } if referral_code else None,
            "fee_status": "calculated",
            "calculation_method": "progressive_bid_amount_v1"
        }
        
        fee_response = db.client.table("connection_fees").insert(connection_fee_data).execute()
        if not fee_response.data:
            raise HTTPException(status_code=500, detail="Failed to save connection fee")
        
        connection_fee_id = fee_response.data[0]["id"]
        
        # 5. Update bid card with winner information
        update_data = {
            "winner_contractor_id": contractor_id,
            "winner_selected_at": datetime.utcnow().isoformat(),
            "connection_fee_id": connection_fee_id,
            "winner_bid_amount": bid_amount,
            "status": "contractor_selected"
        }
        
        update_response = db.client.table("bid_cards").update(update_data).eq("id", bid_card_id).execute()
        if not update_response.data:
            raise HTTPException(status_code=500, detail="Failed to update bid card")
        
        # 6. Update bid status in submitted_bids
        for bid in submitted_bids:
            if bid.get("contractor_id") == contractor_id:
                bid["status"] = "accepted"
            else:
                bid["status"] = "rejected"
        
        bid_document = bid_card_data.get("bid_document", {})
        bid_document["submitted_bids"] = submitted_bids
        
        db.client.table("bid_cards").update({"bid_document": bid_document}).eq("id", bid_card_id).execute()
        
        # 7. Create referral tracking if applicable
        if referral_code and referrer_user_id and fee_result["referrer_portion"] > 0:
            referral_tracking = {
                "referrer_user_id": referrer_user_id,
                "referred_user_id": bid_card_data.get("user_id"),
                "referral_code": referral_code,
                "connection_fee_id": connection_fee_id,
                "referrer_payout_amount": fee_result["referrer_portion"],
                "payout_status": "pending"
            }
            db.client.table("referral_tracking").insert(referral_tracking).execute()
        
        # 8. Send notification to selected contractor
        try:
            from services.contractor_notification_service import send_contractor_selection_notification
            
            # Get project info for notification
            project_title = bid_card_data.get("project_type", "Project").replace("_", " ").title()
            
            # Send contractor notification (async - don't block main flow if it fails)
            notification_result = await send_contractor_selection_notification(
                contractor_id=contractor_id,
                bid_card_id=bid_card_id,
                connection_fee_amount=fee_result["final_fee"],
                bid_amount=bid_amount,
                project_title=project_title
            )
            
            # Log notification result but don't fail the main operation
            print(f"[ContractorSelection] Notification result: {notification_result}")
            
        except Exception as notification_error:
            # Log error but don't break the contractor selection flow
            print(f"[ContractorSelection] Failed to send notification: {notification_error}")
        
        return {
            "success": True,
            "contractor_id": contractor_id,
            "bid_amount": bid_amount,
            "connection_fee": fee_result["final_fee"],
            "platform_portion": fee_result["platform_portion"],
            "referrer_portion": fee_result["referrer_portion"],
            "contractor_receives": bid_amount - fee_result["final_fee"],
            "connection_fee_id": connection_fee_id,
            "message": f"Contractor selected successfully. Connection fee of ${fee_result['final_fee']} will be charged."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}")
async def get_user_bid_cards(user_id: str):
    """Get all bid cards for a specific user"""
    try:
        # Get all bid cards for the user
        response = db.client.table("bid_cards").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        
        if not response or not response.data:
            return []
        
        # Transform and return bid cards
        bid_cards = []
        for card in response.data:
            bid_cards.append({
                "id": card.get("id"),
                "bid_card_number": card.get("bid_card_number"),
                "title": card.get("title", "Untitled Project"),
                "status": card.get("status"),
                "urgency_level": card.get("urgency_level"),
                "budget_range": card.get("budget_range"),
                "timeline": card.get("timeline"),
                "created_at": card.get("created_at"),
                "submission_count": card.get("submission_count", 0),
                "message_count": card.get("message_count", 0)
            })
        
        return bid_cards
        
    except Exception as e:
        logger.error(f"Error fetching user bid cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))
