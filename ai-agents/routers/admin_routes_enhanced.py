"""Enhanced admin routes with full bid card lifecycle data"""
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException

from database_simple import db


router = APIRouter(prefix="/api/admin", tags=["admin-enhanced"])

@router.get("/bid-cards-enhanced")
async def get_enhanced_bid_cards(limit: int = 200):
    """Get bid cards with full lifecycle data using efficient batch queries"""
    try:
        # PERFORMANCE FIX: Use batch queries instead of N+1 individual queries
        # This reduces 151 queries to just 4 total queries
        
        print("[PERFORMANCE] Starting optimized bid-cards-enhanced query")
        
        # Query 1: Get base bid cards (explicitly include new service complexity fields)
        bid_cards_result = db.client.table("bid_cards").select(
            "*, service_complexity, trade_count, primary_trade, secondary_trades"
        ).order("created_at", desc=True).limit(limit).execute()

        if not bid_cards_result.data:
            print("[PERFORMANCE] No bid cards found")
            return {"bid_cards": []}

        bid_card_ids = [card["id"] for card in bid_cards_result.data]
        print(f"[PERFORMANCE] Processing {len(bid_card_ids)} bid cards")

        # Query 2: Batch get ALL campaign data for these bid cards
        campaigns_result = db.client.table("outreach_campaigns").select(
            "bid_card_id, max_contractors, contractors_targeted, responses_received, status"
        ).in_("bid_card_id", bid_card_ids).execute()

        # Create lookup dict for O(1) campaign access
        campaigns_lookup = {c["bid_card_id"]: c for c in (campaigns_result.data or [])}
        print(f"[PERFORMANCE] Found {len(campaigns_lookup)} campaigns")

        # Query 3: Batch get ALL outreach data for these bid cards
        outreach_result = db.client.table("contractor_outreach_attempts").select(
            "bid_card_id, channel, status"
        ).in_("bid_card_id", bid_card_ids).execute()

        # Create outreach metrics lookup dict
        outreach_lookup = {}
        for attempt in (outreach_result.data or []):
            bid_card_id = attempt["bid_card_id"]
            if bid_card_id not in outreach_lookup:
                outreach_lookup[bid_card_id] = {
                    "total_attempts": 0,
                    "email_sent": 0,
                    "forms_sent": 0,
                    "sms_sent": 0,
                    "successful_deliveries": 0
                }
            
            metrics = outreach_lookup[bid_card_id]
            metrics["total_attempts"] += 1
            
            channel = attempt.get("channel")
            if channel == "email":
                metrics["email_sent"] += 1
            elif channel == "form":
                metrics["forms_sent"] += 1
            elif channel == "sms":
                metrics["sms_sent"] += 1
            
            if attempt.get("status") == "sent":
                metrics["successful_deliveries"] += 1
        
        print(f"[PERFORMANCE] Processed {len(outreach_result.data or [])} outreach attempts")

        # Query 4: Batch get ALL view data for these bid cards
        views_result = db.client.table("bid_card_views").select(
            "bid_card_id, viewed_at"
        ).in_("bid_card_id", bid_card_ids).order("viewed_at", desc=True).execute()

        # Create views lookup dict
        views_lookup = {}
        for view in (views_result.data or []):
            bid_card_id = view["bid_card_id"]
            if bid_card_id not in views_lookup:
                views_lookup[bid_card_id] = {
                    "count": 0,
                    "last_viewed": view["viewed_at"]
                }
            views_lookup[bid_card_id]["count"] += 1

        print(f"[PERFORMANCE] Processed {len(views_result.data or [])} bid card views")

        # Now process each bid card using lookup data (no additional queries!)
        enhanced_cards = []
        
        for card in bid_cards_result.data:
            bid_card_id = card["id"]

            # Get campaign data from lookup (O(1))
            campaign_data = campaigns_lookup.get(bid_card_id, {})

            # Get outreach metrics from lookup (O(1))
            outreach_metrics = outreach_lookup.get(bid_card_id, {
                "total_attempts": 0,
                "email_sent": 0,
                "forms_sent": 0,
                "sms_sent": 0,
                "successful_deliveries": 0
            })

            # Get view data from lookup (O(1))
            view_data = views_lookup.get(bid_card_id, {"count": 0, "last_viewed": None})

            # Calculate next check-in based on campaign progress
            if campaign_data and campaign_data.get("responses_received") is not None:
                progress = (campaign_data.get("responses_received", 0) /
                           max(campaign_data.get("max_contractors", 1), 1))
                if progress < 0.25:
                    next_checkin = datetime.now() + timedelta(hours=6)
                elif progress < 0.5:
                    next_checkin = datetime.now() + timedelta(hours=12)
                elif progress < 0.75:
                    next_checkin = datetime.now() + timedelta(days=1)
                else:
                    next_checkin = None
            else:
                next_checkin = datetime.now() + timedelta(hours=4)

            # Build enhanced card
            enhanced_card = {
                **card,
                "campaign": campaign_data,
                "outreach": outreach_metrics,
                "views_count": view_data["count"],
                "last_viewed": view_data["last_viewed"],
                "next_checkin": next_checkin.isoformat() if next_checkin else None
            }

            enhanced_cards.append(enhanced_card)

        print(f"[PERFORMANCE] Completed processing {len(enhanced_cards)} enhanced cards")
        return {"bid_cards": enhanced_cards}

    except Exception as e:
        print(f"[ADMIN ENHANCED] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bid-card/{bid_card_id}/timeline")
async def get_bid_card_timeline(bid_card_id: str):
    """Get complete timeline of events for a bid card"""
    events = []

    # Get creation event
    card_result = db.client.table("bid_cards").select(
        "created_at, status, homeowner_name"
    ).eq("id", bid_card_id).single().execute()

    if card_result.data:
        events.append({
            "timestamp": card_result.data["created_at"],
            "type": "created",
            "description": f"Bid card created by {card_result.data['homeowner_name']}",
            "status": "completed"
        })

    # Get discovery events
    discovery_result = db.client.table("discovery_runs").select(
        "created_at, contractors_found"
    ).eq("bid_card_id", bid_card_id).execute()

    for discovery in (discovery_result.data or []):
        events.append({
            "timestamp": discovery["created_at"],
            "type": "discovery",
            "description": f"Found {discovery['contractors_found']} contractors",
            "status": "completed"
        })

    # Get outreach events
    outreach_result = db.client.table("contractor_outreach_attempts").select(
        "created_at, channel, status, contractor_lead_id"
    ).eq("bid_card_id", bid_card_id).execute()

    for outreach in (outreach_result.data or []):
        events.append({
            "timestamp": outreach["created_at"],
            "type": "outreach",
            "description": f"{outreach['channel']} sent to contractor",
            "status": outreach["status"]
        })

    # Sort events by timestamp
    events.sort(key=lambda x: x["timestamp"])

    return {"timeline": events}
