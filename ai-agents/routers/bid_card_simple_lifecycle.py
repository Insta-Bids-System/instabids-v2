#!/usr/bin/env python3
"""
Simplified Bid Card Lifecycle API Routes
Phase 1 implementation focusing on core functionality
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database_simple import get_client


router = APIRouter(prefix="/api/bid-cards-simple", tags=["bid-card-simple"])


class SimpleBidCardResponse(BaseModel):
    """Simplified bid card data"""
    bid_card: dict[str, Any]
    status: str
    metrics: dict[str, Any]


@router.get("/{bid_card_id}")
async def get_simple_bid_card(bid_card_id: str):
    """Get basic bid card information"""
    try:
        db = get_client()

        # Get core bid card data
        result = db.table("bid_cards").select("*").eq("id", bid_card_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Bid card not found")

        bid_card = result.data[0]

        # Calculate basic metrics
        created_at = datetime.fromisoformat(bid_card["created_at"].replace("Z", "+00:00"))
        age_hours = (datetime.now() - created_at).total_seconds() / 3600

        # Extract bid count from bid_document if it exists
        bid_document = bid_card.get("bid_document", {})
        submitted_bids = bid_document.get("submitted_bids", [])
        bids_received = len(submitted_bids)

        metrics = {
            "age_hours": round(age_hours, 2),
            "age_days": round(age_hours / 24, 2),
            "bids_received": bids_received,
            "bids_needed": bid_card.get("contractor_count_needed", 0),
            "completion_percentage": (bids_received / bid_card.get("contractor_count_needed", 1)) * 100 if bid_card.get("contractor_count_needed", 0) > 0 else 0,
            "is_recent": age_hours <= 24,
            "status": bid_card.get("status", "unknown")
        }

        return {
            "success": True,
            "bid_card": bid_card,
            "metrics": metrics,
            "message": f"Retrieved bid card {bid_card.get('bid_card_number', 'N/A')}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving bid card: {e!s}")


@router.get("/{bid_card_id}/timeline")
async def get_simple_timeline(bid_card_id: str):
    """Get basic timeline for bid card"""
    try:
        db = get_client()

        timeline_events = []

        # Get bid card creation event
        bid_card_result = db.table("bid_cards").select("*").eq("id", bid_card_id).execute()
        if bid_card_result.data:
            bid_card = bid_card_result.data[0]
            timeline_events.append({
                "timestamp": bid_card["created_at"],
                "event_type": "bid_card_created",
                "description": f"Bid card {bid_card.get('bid_card_number', 'N/A')} created",
                "details": {
                    "project_type": bid_card.get("project_type", "unknown"),
                    "urgency": bid_card.get("urgency_level", "unknown"),
                    "contractors_needed": bid_card.get("contractor_count_needed", 0)
                }
            })

            # Add bid submission events from bid_document
            bid_document = bid_card.get("bid_document", {})
            submitted_bids = bid_document.get("submitted_bids", [])

            for bid in submitted_bids:
                if "submitted_at" in bid:
                    timeline_events.append({
                        "timestamp": bid["submitted_at"],
                        "event_type": "bid_submitted",
                        "description": f"Bid submitted by {bid.get('contractor_name', 'Unknown')}",
                        "details": {
                            "bid_amount": bid.get("bid_amount", 0),
                            "contractor_name": bid.get("contractor_name", "Unknown"),
                            "timeline_days": bid.get("timeline_days", 0)
                        }
                    })

        # Sort timeline by timestamp
        timeline_events.sort(key=lambda x: x["timestamp"])

        return {
            "success": True,
            "timeline": timeline_events,
            "total_events": len(timeline_events)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving timeline: {e!s}")


@router.get("/{bid_card_id}/bids")
async def get_simple_bids(bid_card_id: str):
    """Get submitted bids for bid card"""
    try:
        db = get_client()

        # Get bid card
        result = db.table("bid_cards").select("*").eq("id", bid_card_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Bid card not found")

        bid_card = result.data[0]
        bid_document = bid_card.get("bid_document", {})
        submitted_bids = bid_document.get("submitted_bids", [])

        # Add basic calculated fields
        for i, bid in enumerate(submitted_bids):
            bid["bid_rank"] = i + 1
            bid["is_lowest"] = i == 0 if submitted_bids else False
            bid["is_highest"] = i == len(submitted_bids) - 1 if submitted_bids else False

        # Sort by bid amount
        submitted_bids.sort(key=lambda x: x.get("bid_amount", 0))

        return {
            "success": True,
            "bids": submitted_bids,
            "total_bids": len(submitted_bids),
            "target_bids": bid_card.get("contractor_count_needed", 0),
            "completion_percentage": (len(submitted_bids) / bid_card.get("contractor_count_needed", 1)) * 100 if bid_card.get("contractor_count_needed", 0) > 0 else 0
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving bids: {e!s}")


@router.post("/{bid_card_id}/submit-bid")
async def submit_simple_bid(bid_card_id: str, bid_data: dict):
    """Submit a bid for a bid card (simplified)"""
    try:
        db = get_client()

        # Get current bid card
        result = db.table("bid_cards").select("*").eq("id", bid_card_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Bid card not found")

        bid_card = result.data[0]
        bid_document = bid_card.get("bid_document", {})
        submitted_bids = bid_document.get("submitted_bids", [])

        # Create new bid
        new_bid = {
            "bid_id": f"bid_{len(submitted_bids) + 1}_{int(datetime.now().timestamp())}",
            "contractor_id": bid_data.get("contractor_id", "unknown"),
            "contractor_name": bid_data.get("contractor_name", "Unknown Contractor"),
            "contractor_email": bid_data.get("contractor_email", ""),
            "contractor_phone": bid_data.get("contractor_phone", ""),
            "bid_amount": bid_data.get("bid_amount", 0),
            "timeline_days": bid_data.get("timeline_days", 0),
            "start_date": bid_data.get("start_date", ""),
            "completion_date": bid_data.get("completion_date", ""),
            "bid_content": bid_data.get("bid_content", ""),
            "materials_included": bid_data.get("materials_included", ""),
            "labor_breakdown": bid_data.get("labor_breakdown", ""),
            "warranty_offered": bid_data.get("warranty_offered", ""),
            "submitted_at": datetime.now().isoformat(),
            "status": "submitted"
        }

        # Add to submitted bids
        submitted_bids.append(new_bid)

        # Update bid document
        bid_document["submitted_bids"] = submitted_bids
        bid_document["bids_received_count"] = len(submitted_bids)
        bid_document["last_bid_at"] = datetime.now().isoformat()

        # Check if target met
        contractor_count_needed = bid_card.get("contractor_count_needed", 0)
        bids_target_met = len(submitted_bids) >= contractor_count_needed

        # Update bid card
        update_data = {
            "bid_document": bid_document,
            "bids_received_count": len(submitted_bids),
            "bids_target_met": bids_target_met,
            "updated_at": datetime.now().isoformat()
        }

        # Update status if target met
        if bids_target_met and bid_card.get("status") != "bids_complete":
            update_data["status"] = "bids_complete"

        # Save to database
        update_result = db.table("bid_cards").update(update_data).eq("id", bid_card_id).execute()

        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to update bid card")

        return {
            "success": True,
            "bid_id": new_bid["bid_id"],
            "message": f"Bid submitted successfully by {new_bid['contractor_name']}",
            "bids_received": len(submitted_bids),
            "target_bids": contractor_count_needed,
            "target_met": bids_target_met,
            "status": update_result.data[0].get("status", "unknown")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting bid: {e!s}")


@router.get("/")
async def list_simple_bid_cards(
    limit: int = 10,
    offset: int = 0,
    status: Optional[str] = None,
    project_type: Optional[str] = None
):
    """List bid cards with basic filtering"""
    try:
        db = get_client()

        # Build query
        query = db.table("bid_cards").select("*")

        if status:
            query = query.eq("status", status)
        if project_type:
            query = query.eq("project_type", project_type)

        # Add pagination
        query = query.range(offset, offset + limit - 1).order("created_at", desc=True)

        result = query.execute()
        bid_cards = result.data or []

        # Add basic metrics to each bid card
        for bid_card in bid_cards:
            bid_document = bid_card.get("bid_document", {})
            submitted_bids = bid_document.get("submitted_bids", [])
            bids_received = len(submitted_bids)

            bid_card["bids_received"] = bids_received
            bid_card["completion_percentage"] = (bids_received / bid_card.get("contractor_count_needed", 1)) * 100 if bid_card.get("contractor_count_needed", 0) > 0 else 0

        return {
            "success": True,
            "bid_cards": bid_cards,
            "total": len(bid_cards),
            "limit": limit,
            "offset": offset,
            "has_more": len(bid_cards) == limit
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing bid cards: {e!s}")
