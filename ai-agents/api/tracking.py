"""
Bid Card Tracking API
Handles contractor acquisition tracking from bid card distribution
"""
import os
import sys
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel


# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_simple import SupabaseDB


router = APIRouter()
db = SupabaseDB()

class BidCardClickRequest(BaseModel):
    bid_token: str
    source_channel: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class BidCardConversionRequest(BaseModel):
    bid_token: str
    contractor_id: str

@router.post("/track/bid-card-click")
async def track_bid_card_click(request: BidCardClickRequest, http_request: Request):
    """Track when someone clicks on a bid card link"""

    try:
        # Get IP address from request if not provided
        ip_address = request.ip_address or http_request.client.host

        # Find bid card by token
        bid_card = db.execute_query("""
            SELECT id FROM bid_cards
            WHERE public_token = %s OR bid_card_number = %s
        """, (request.bid_token, request.bid_token))

        if not bid_card:
            raise HTTPException(status_code=404, detail="Bid card not found")

        bid_card_id = bid_card[0]["id"]

        # Record the click
        db.execute_query("""
            INSERT INTO bid_card_clicks (
                bid_card_id,
                bid_card_token,
                source_channel,
                ip_address,
                user_agent,
                clicked_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            bid_card_id,
            request.bid_token,
            request.source_channel,
            ip_address,
            request.user_agent,
            datetime.now()
        ))

        # Increment click count on bid card
        db.execute_query("""
            UPDATE bid_cards
            SET click_count = COALESCE(click_count, 0) + 1
            WHERE id = %s
        """, (bid_card_id,))

        return {"success": True, "message": "Click tracked successfully"}

    except Exception as e:
        print(f"[TRACKING ERROR] Failed to track click: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/track/bid-card-conversion")
async def track_bid_card_conversion(request: BidCardConversionRequest):
    """Track when a bid card click results in contractor signup"""

    try:
        # Find the most recent click for this bid token (within last hour)
        click_record = db.execute_query("""
            SELECT id, bid_card_id
            FROM bid_card_clicks
            WHERE bid_card_token = %s
            AND clicked_at > NOW() - INTERVAL '1 hour'
            AND resulted_in_signup = FALSE
            ORDER BY clicked_at DESC
            LIMIT 1
        """, (request.bid_token,))

        if not click_record:
            # Still track the conversion even if we can't find the click
            bid_card = db.execute_query("""
                SELECT id FROM bid_cards
                WHERE public_token = %s OR bid_card_number = %s
            """, (request.bid_token, request.bid_token))

            if bid_card:
                # Create a conversion record
                db.execute_query("""
                    INSERT INTO bid_card_clicks (
                        bid_card_id,
                        bid_card_token,
                        source_channel,
                        resulted_in_signup,
                        new_contractor_id,
                        signup_completed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    bid_card[0]["id"],
                    request.bid_token,
                    "unknown",
                    True,
                    request.contractor_id,
                    datetime.now()
                ))
        else:
            # Update existing click record
            db.execute_query("""
                UPDATE bid_card_clicks
                SET resulted_in_signup = TRUE,
                    new_contractor_id = %s,
                    signup_completed_at = %s
                WHERE id = %s
            """, (
                request.contractor_id,
                datetime.now(),
                click_record[0]["id"]
            ))

            # Increment contractor signup count on bid card
            db.execute_query("""
                UPDATE bid_cards
                SET contractor_signups = COALESCE(contractor_signups, 0) + 1
                WHERE id = %s
            """, (click_record[0]["bid_card_id"],))

        return {"success": True, "message": "Conversion tracked successfully"}

    except Exception as e:
        print(f"[TRACKING ERROR] Failed to track conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bid-cards/by-token/{token}")
async def get_bid_card_by_token(token: str):
    """Get bid card details by public token for landing page display"""

    try:
        # Get bid card with basic info for display
        bid_card = db.execute_query("""
            SELECT
                id,
                public_token,
                bid_card_number,
                project_type,
                urgency_level as urgency,
                budget_min,
                budget_max,
                contractor_count_needed as contractor_count,
                created_at,
                bid_document
            FROM bid_cards
            WHERE public_token = %s OR bid_card_number = %s
        """, (token, token))

        if not bid_card:
            raise HTTPException(status_code=404, detail="Bid card not found")

        card = bid_card[0]
        bid_document = card.get("bid_document", {})
        all_data = bid_document.get("all_extracted_data", {})

        # Format for frontend
        formatted_card = {
            "id": card["id"],
            "public_token": card["public_token"] or card["bid_card_number"],
            "project_type": card["project_type"],
            "urgency": card["urgency"],
            "budget_display": f"${card['budget_min']:,} - ${card['budget_max']:,}",
            "location": {
                "city": all_data.get("location", {}).get("city", "Unknown"),
                "state": all_data.get("location", {}).get("state", "Unknown")
            },
            "contractor_count": card["contractor_count"],
            "created_at": card["created_at"]
        }

        # Increment view count
        db.execute_query("""
            UPDATE bid_cards
            SET view_count = COALESCE(view_count, 0) + 1
            WHERE id = %s
        """, (card["id"],))

        return formatted_card

    except Exception as e:
        print(f"[API ERROR] Failed to get bid card by token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/bid-card/{bid_card_id}")
async def get_bid_card_analytics(bid_card_id: str):
    """Get analytics for a specific bid card"""

    try:
        # Get overall stats
        stats = db.execute_query("""
            SELECT
                view_count,
                click_count,
                contractor_signups
            FROM bid_cards
            WHERE id = %s
        """, (bid_card_id,))

        if not stats:
            raise HTTPException(status_code=404, detail="Bid card not found")

        # Get click details by channel
        channel_stats = db.execute_query("""
            SELECT
                source_channel,
                COUNT(*) as clicks,
                SUM(CASE WHEN resulted_in_signup THEN 1 ELSE 0 END) as conversions
            FROM bid_card_clicks
            WHERE bid_card_id = %s
            GROUP BY source_channel
        """, (bid_card_id,))

        # Get recent activity
        recent_clicks = db.execute_query("""
            SELECT
                source_channel,
                resulted_in_signup,
                clicked_at
            FROM bid_card_clicks
            WHERE bid_card_id = %s
            ORDER BY clicked_at DESC
            LIMIT 10
        """, (bid_card_id,))

        card_stats = stats[0]
        total_clicks = card_stats["click_count"] or 0
        total_conversions = card_stats["contractor_signups"] or 0

        return {
            "overview": {
                "total_views": card_stats["view_count"] or 0,
                "total_clicks": total_clicks,
                "total_conversions": total_conversions,
                "conversion_rate": (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
            },
            "by_channel": {
                row["source_channel"]: {
                    "clicks": row["clicks"],
                    "conversions": row["conversions"],
                    "conversion_rate": (row["conversions"] / row["clicks"] * 100) if row["clicks"] > 0 else 0
                } for row in channel_stats
            },
            "recent_activity": [
                {
                    "channel": row["source_channel"],
                    "converted": row["resulted_in_signup"],
                    "timestamp": row["clicked_at"]
                } for row in recent_clicks
            ]
        }

    except Exception as e:
        print(f"[API ERROR] Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
