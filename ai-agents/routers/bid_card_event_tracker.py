#!/usr/bin/env python3
"""
Bid Card Event Tracking System
Records all lifecycle events for bid cards in a dedicated timeline
"""

from datetime import datetime
from typing import Any, Optional, Dict, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import json

from database_simple import db


router = APIRouter(prefix="/api/bid-card-events", tags=["bid-card-events"])


class BidCardEvent(BaseModel):
    """Event model for bid card lifecycle tracking"""
    bid_card_id: str
    event_type: str
    event_description: str
    event_details: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    created_by_type: Optional[str] = None  # system, homeowner, contractor, admin


class EventTracker:
    """Central event tracking system for bid cards"""
    
    @staticmethod
    async def track_event(
        bid_card_id: str,
        event_type: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
        created_by_type: str = "system"
    ) -> bool:
        """
        Track any event in the bid card lifecycle
        Updates both the bid_document timeline and creates audit trail
        """
        try:
            # Get the current bid card
            bid_card_result = db.client.table("bid_cards").select("*").eq("id", bid_card_id).execute()
            if not bid_card_result.data:
                return False
                
            bid_card = bid_card_result.data[0]
            bid_document = bid_card.get("bid_document", {})
            
            # Initialize timeline if it doesn't exist
            if "timeline" not in bid_document:
                bid_document["timeline"] = []
            
            # Create the event entry
            event_entry = {
                "id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "description": description,
                "details": details or {},
                "created_by": created_by,
                "created_by_type": created_by_type
            }
            
            # Add to timeline
            bid_document["timeline"].append(event_entry)
            
            # Update the bid card with new timeline
            update_result = db.client.table("bid_cards").update({
                "bid_document": bid_document,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", bid_card_id).execute()
            
            return bool(update_result.data)
            
        except Exception as e:
            print(f"Error tracking event: {e}")
            return False


# API Endpoints

@router.post("/track")
async def track_bid_card_event(event: BidCardEvent):
    """Manually track an event for a bid card"""
    success = await EventTracker.track_event(
        bid_card_id=event.bid_card_id,
        event_type=event.event_type,
        description=event.event_description,
        details=event.event_details,
        created_by=event.created_by,
        created_by_type=event.created_by_type or "system"
    )
    
    if success:
        return {"success": True, "message": "Event tracked successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to track event")


@router.get("/{bid_card_id}/timeline")
async def get_bid_card_timeline(bid_card_id: str):
    """Get the complete timeline for a bid card"""
    try:
        # Get bid card with timeline
        bid_card_result = db.client.table("bid_cards").select("*").eq("id", bid_card_id).execute()
        if not bid_card_result.data:
            raise HTTPException(status_code=404, detail="Bid card not found")
        
        bid_card = bid_card_result.data[0]
        bid_document = bid_card.get("bid_document", {})
        timeline = bid_document.get("timeline", [])
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "bid_card_id": bid_card_id,
            "bid_card_number": bid_card.get("bid_card_number"),
            "total_events": len(timeline),
            "timeline": timeline
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving timeline: {str(e)}")


# Event Tracking Helper Functions

async def track_bid_card_creation(bid_card_id: str, user_id: str, project_type: str, urgency: str):
    """Track bid card creation event"""
    await EventTracker.track_event(
        bid_card_id=bid_card_id,
        event_type="bid_card_created",
        description="Bid card created",
        details={
            "user_id": user_id,
            "project_type": project_type,
            "urgency_level": urgency,
            "status": "generated"
        },
        created_by=user_id,
        created_by_type="homeowner"
    )


async def track_campaign_creation(bid_card_id: str, campaign_id: str, campaign_name: str, max_contractors: int):
    """Track campaign creation event"""
    await EventTracker.track_event(
        bid_card_id=bid_card_id,
        event_type="campaign_created",
        description=f"Outreach campaign '{campaign_name}' created",
        details={
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "max_contractors": max_contractors
        },
        created_by_type="system"
    )


async def track_contractor_discovery(bid_card_id: str, contractors_found: int, tier_1: int, tier_2: int, tier_3: int):
    """Track contractor discovery event"""
    await EventTracker.track_event(
        bid_card_id=bid_card_id,
        event_type="contractor_discovery",
        description=f"Discovered {contractors_found} contractors",
        details={
            "total_contractors": contractors_found,
            "tier_1_internal": tier_1,
            "tier_2_previous": tier_2,
            "tier_3_cold": tier_3
        },
        created_by_type="system"
    )


async def track_outreach_sent(bid_card_id: str, contractor_id: str, contractor_name: str, channel: str):
    """Track outreach sent event"""
    await EventTracker.track_event(
        bid_card_id=bid_card_id,
        event_type="outreach_sent",
        description=f"Outreach sent to {contractor_name} via {channel}",
        details={
            "contractor_id": contractor_id,
            "contractor_name": contractor_name,
            "channel": channel
        },
        created_by_type="system"
    )


async def track_bid_submission(bid_card_id: str, contractor_id: str, contractor_name: str, bid_amount: float, timeline_days: int):
    """Track bid submission event"""
    await EventTracker.track_event(
        bid_card_id=bid_card_id,
        event_type="bid_submitted",
        description=f"Bid submitted by {contractor_name}",
        details={
            "contractor_id": contractor_id,
            "contractor_name": contractor_name,
            "bid_amount": bid_amount,
            "timeline_days": timeline_days
        },
        created_by=contractor_id,
        created_by_type="contractor"
    )


async def track_status_change(bid_card_id: str, old_status: str, new_status: str, reason: Optional[str] = None):
    """Track status change event"""
    await EventTracker.track_event(
        bid_card_id=bid_card_id,
        event_type="status_changed",
        description=f"Status changed from {old_status} to {new_status}",
        details={
            "old_status": old_status,
            "new_status": new_status,
            "reason": reason
        },
        created_by_type="system"
    )


async def track_bid_accepted(bid_card_id: str, contractor_id: str, contractor_name: str, bid_amount: float):
    """Track bid acceptance event"""
    await EventTracker.track_event(
        bid_card_id=bid_card_id,
        event_type="bid_accepted",
        description=f"Bid from {contractor_name} accepted",
        details={
            "contractor_id": contractor_id,
            "contractor_name": contractor_name,
            "accepted_amount": bid_amount
        },
        created_by_type="homeowner"
    )


async def track_project_completion(bid_card_id: str, contractor_id: str, final_amount: float, satisfaction_rating: Optional[int] = None):
    """Track project completion event"""
    await EventTracker.track_event(
        bid_card_id=bid_card_id,
        event_type="project_completed",
        description="Project completed successfully",
        details={
            "contractor_id": contractor_id,
            "final_amount": final_amount,
            "satisfaction_rating": satisfaction_rating
        },
        created_by_type="system"
    )


async def track_homeowner_action(bid_card_id: str, action: str, details: Dict[str, Any], user_id: str):
    """Track any homeowner action"""
    await EventTracker.track_event(
        bid_card_id=bid_card_id,
        event_type=f"homeowner_{action}",
        description=f"Homeowner performed: {action}",
        details=details,
        created_by=user_id,
        created_by_type="homeowner"
    )


async def track_contractor_action(bid_card_id: str, action: str, details: Dict[str, Any], contractor_id: str):
    """Track any contractor action"""
    await EventTracker.track_event(
        bid_card_id=bid_card_id,
        event_type=f"contractor_{action}",
        description=f"Contractor performed: {action}",
        details=details,
        created_by=contractor_id,
        created_by_type="contractor"
    )


# Batch Event Tracking

@router.post("/track-batch")
async def track_multiple_events(events: List[BidCardEvent]):
    """Track multiple events at once"""
    results = []
    for event in events:
        success = await EventTracker.track_event(
            bid_card_id=event.bid_card_id,
            event_type=event.event_type,
            description=event.event_description,
            details=event.event_details,
            created_by=event.created_by,
            created_by_type=event.created_by_type or "system"
        )
        results.append({
            "event_type": event.event_type,
            "success": success
        })
    
    return {
        "total_events": len(events),
        "successful": sum(1 for r in results if r["success"]),
        "results": results
    }


# Timeline Analysis

@router.get("/{bid_card_id}/timeline-analysis")
async def analyze_bid_card_timeline(bid_card_id: str):
    """Analyze the timeline for insights"""
    try:
        # Get timeline
        timeline_response = await get_bid_card_timeline(bid_card_id)
        timeline = timeline_response["timeline"]
        
        if not timeline:
            return {
                "bid_card_id": bid_card_id,
                "analysis": "No events tracked yet"
            }
        
        # Analyze timeline
        event_types = {}
        for event in timeline:
            event_type = event.get("event_type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # Calculate time metrics
        first_event = timeline[-1] if timeline else None
        last_event = timeline[0] if timeline else None
        
        if first_event and last_event:
            first_time = datetime.fromisoformat(first_event["timestamp"])
            last_time = datetime.fromisoformat(last_event["timestamp"])
            duration_hours = (last_time - first_time).total_seconds() / 3600
        else:
            duration_hours = 0
        
        # Check for key milestones (matching actual event types)
        has_creation = any(e.get("event_type") == "bid_card_created" for e in timeline)
        has_discovery = any(e.get("event_type") in ["contractor_discovery", "contractors_targeted"] for e in timeline)
        has_campaign = any(e.get("event_type") == "campaign_created" for e in timeline)
        has_outreach = any(e.get("event_type") in ["contractors_targeted", "outreach_sent"] for e in timeline)
        has_bids = any(e.get("event_type") in ["bid_submitted", "bid_received"] for e in timeline)
        has_acceptance = any(e.get("event_type") == "bid_accepted" for e in timeline)
        has_completion = any(e.get("event_type") in ["project_completed", "campaign_completed", "target_reached"] for e in timeline)
        
        return {
            "bid_card_id": bid_card_id,
            "total_events": len(timeline),
            "event_breakdown": event_types,
            "duration_hours": round(duration_hours, 2),
            "milestones": {
                "creation": has_creation,
                "discovery": has_discovery,
                "campaign": has_campaign,
                "outreach": has_outreach,
                "bids_received": has_bids,
                "bid_accepted": has_acceptance,
                "project_completed": has_completion
            },
            "completeness_score": sum([
                has_creation, has_discovery, has_campaign, 
                has_outreach, has_bids, has_acceptance
            ]) / 6 * 100
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing timeline: {str(e)}")