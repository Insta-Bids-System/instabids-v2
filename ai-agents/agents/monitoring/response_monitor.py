"""
Response Monitoring System
Tracks contractor responses across all channels
Monitors email opens, link clicks, form submissions, and direct responses
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from dotenv import load_dotenv
from supabase import create_client


class ResponseType(Enum):
    """Types of contractor responses"""
    EMAIL_OPEN = "email_open"
    LINK_CLICK = "link_click"
    EMAIL_REPLY = "email_reply"
    FORM_SUBMISSION = "form_submission"
    PHONE_CALL = "phone_call"
    SMS_REPLY = "sms_reply"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    NEED_INFO = "need_info"
    BUSY = "busy"


class ResponseMonitor:
    """Monitors and tracks contractor responses to outreach"""

    def __init__(self):
        """Initialize response monitoring system"""
        load_dotenv(override=True)
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)

        print("[Monitor] Initialized Response Monitoring System")

    def track_email_open(self,
                        distribution_id: str,
                        opened_at: Optional[datetime] = None) -> dict[str, Any]:
        """
        Track when a contractor opens an email

        Args:
            distribution_id: ID from bid_card_distributions table
            opened_at: When the email was opened (defaults to now)
        """
        try:
            opened_at = opened_at or datetime.now()

            # Update distribution record
            result = self.supabase.table("bid_card_distributions").update({
                "opened_at": opened_at.isoformat(),
                "status": "opened"
            }).eq("id", distribution_id).execute()

            if result.data:
                # Log the response event
                self._log_response_event(
                    distribution_id=distribution_id,
                    event_type=ResponseType.EMAIL_OPEN.value,
                    event_data={"opened_at": opened_at.isoformat()}
                )

                print(f"[Monitor] Tracked email open for distribution {distribution_id}")
                return {"success": True, "distribution_id": distribution_id}
            else:
                return {"success": False, "error": "Distribution not found"}

        except Exception as e:
            print(f"[Monitor ERROR] Failed to track email open: {e}")
            return {"success": False, "error": str(e)}

    def track_link_click(self,
                        distribution_id: str,
                        link_type: str = "bid_details",
                        clicked_at: Optional[datetime] = None) -> dict[str, Any]:
        """
        Track when a contractor clicks a link in outreach

        Args:
            distribution_id: ID from bid_card_distributions table
            link_type: Type of link clicked (bid_details, unsubscribe, etc.)
            clicked_at: When the link was clicked
        """
        try:
            clicked_at = clicked_at or datetime.now()

            # If first click, also mark as opened
            dist_result = self.supabase.table("bid_card_distributions").select("opened_at").eq(
                "id", distribution_id
            ).limit(1).execute()

            if dist_result.data and not dist_result.data[0].get("opened_at"):
                self.track_email_open(distribution_id, clicked_at)

            # Log the click event
            self._log_response_event(
                distribution_id=distribution_id,
                event_type=ResponseType.LINK_CLICK.value,
                event_data={
                    "link_type": link_type,
                    "clicked_at": clicked_at.isoformat()
                }
            )

            # Update engagement score
            self._update_engagement_score(distribution_id, "link_click")

            print(f"[Monitor] Tracked {link_type} link click for distribution {distribution_id}")
            return {"success": True, "distribution_id": distribution_id}

        except Exception as e:
            print(f"[Monitor ERROR] Failed to track link click: {e}")
            return {"success": False, "error": str(e)}

    def track_contractor_response(self,
                                distribution_id: str,
                                response_type: str,
                                response_channel: str,
                                response_content: Optional[str] = None,
                                metadata: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Track actual contractor response (email reply, form submission, call, etc.)

        Args:
            distribution_id: ID from bid_card_distributions table
            response_type: Type from ResponseType enum
            response_channel: Channel of response (email, sms, form, phone)
            response_content: Content of the response if available
            metadata: Additional data about the response
        """
        try:
            now = datetime.now()

            # Determine interest level from response type
            interest_mapping = {
                "interested": "high",
                "not_interested": "none",
                "need_info": "medium",
                "busy": "low",
                "form_submission": "high",
                "email_reply": "medium",
                "phone_call": "high"
            }

            interest_level = interest_mapping.get(response_type, "unknown")

            # Update distribution record
            update_data = {
                "responded_at": now.isoformat(),
                "response_type": response_type,
                "response_channel": response_channel,
                "status": "responded",
                "interest_level": interest_level
            }

            result = self.supabase.table("bid_card_distributions").update(
                update_data
            ).eq("id", distribution_id).execute()

            if result.data:
                # Get contractor and bid card info for notifications
                dist_data = result.data[0]

                # Log detailed response
                response_record = {
                    "id": str(uuid.uuid4()),
                    "distribution_id": distribution_id,
                    "contractor_id": dist_data["contractor_id"],
                    "bid_card_id": dist_data["bid_card_id"],
                    "response_type": response_type,
                    "response_channel": response_channel,
                    "response_content": response_content,
                    "interest_level": interest_level,
                    "metadata": metadata,
                    "responded_at": now.isoformat()
                }

                self.supabase.table("contractor_responses").insert(response_record).execute()

                # Update engagement score
                self._update_engagement_score(distribution_id, "response")

                # Create notification for high interest
                if interest_level == "high":
                    self._create_high_interest_notification(dist_data)

                print(f"[Monitor] Tracked {response_type} response via {response_channel}")
                return {
                    "success": True,
                    "distribution_id": distribution_id,
                    "interest_level": interest_level,
                    "response_id": response_record["id"]
                }
            else:
                return {"success": False, "error": "Distribution not found"}

        except Exception as e:
            print(f"[Monitor ERROR] Failed to track response: {e}")
            return {"success": False, "error": str(e)}

    def get_response_analytics(self,
                             bid_card_id: Optional[str] = None,
                             campaign_id: Optional[str] = None,
                             date_range: Optional[tuple[datetime, datetime]] = None) -> dict[str, Any]:
        """
        Get comprehensive response analytics

        Args:
            bid_card_id: Filter by specific bid card
            campaign_id: Filter by specific campaign
            date_range: Tuple of (start_date, end_date)
        """
        try:
            # Build query
            query = self.supabase.table("bid_card_distributions").select("*")

            if bid_card_id:
                query = query.eq("bid_card_id", bid_card_id)
            if campaign_id:
                query = query.eq("campaign_id", campaign_id)
            if date_range:
                query = query.gte("distributed_at", date_range[0].isoformat())
                query = query.lte("distributed_at", date_range[1].isoformat())

            result = query.execute()
            distributions = result.data if result.data else []

            # Calculate metrics
            total = len(distributions)
            sent = total
            opened = sum(1 for d in distributions if d.get("opened_at"))
            responded = sum(1 for d in distributions if d.get("responded_at"))

            # Interest breakdown
            interest_levels = {"high": 0, "medium": 0, "low": 0, "none": 0, "unknown": 0}
            for dist in distributions:
                level = dist.get("interest_level", "unknown")
                interest_levels[level] = interest_levels.get(level, 0) + 1

            # Response time analysis
            response_times = []
            for dist in distributions:
                if dist.get("responded_at") and dist.get("distributed_at"):
                    sent_time = datetime.fromisoformat(dist["distributed_at"].replace("Z", "+00:00"))
                    response_time = datetime.fromisoformat(dist["responded_at"].replace("Z", "+00:00"))
                    hours_to_respond = (response_time - sent_time).total_seconds() / 3600
                    response_times.append(hours_to_respond)

            avg_response_time = sum(response_times) / len(response_times) if response_times else 0

            # Channel performance
            channel_stats = {}
            for dist in distributions:
                channel = dist.get("distribution_method", "unknown")
                if channel not in channel_stats:
                    channel_stats[channel] = {
                        "sent": 0, "opened": 0, "responded": 0, "interested": 0
                    }
                channel_stats[channel]["sent"] += 1
                if dist.get("opened_at"):
                    channel_stats[channel]["opened"] += 1
                if dist.get("responded_at"):
                    channel_stats[channel]["responded"] += 1
                if dist.get("interest_level") == "high":
                    channel_stats[channel]["interested"] += 1

            analytics = {
                "success": True,
                "summary": {
                    "total_sent": sent,
                    "total_opened": opened,
                    "total_responded": responded,
                    "open_rate": (opened / sent * 100) if sent > 0 else 0,
                    "response_rate": (responded / sent * 100) if sent > 0 else 0,
                    "avg_response_time_hours": round(avg_response_time, 1)
                },
                "interest_breakdown": interest_levels,
                "channel_performance": channel_stats,
                "best_performing_channel": self._get_best_channel(channel_stats),
                "filters_applied": {
                    "bid_card_id": bid_card_id,
                    "campaign_id": campaign_id,
                    "date_range": [d.isoformat() for d in date_range] if date_range else None
                }
            }

            return analytics

        except Exception as e:
            print(f"[Monitor ERROR] Failed to get analytics: {e}")
            return {"success": False, "error": str(e)}

    def get_hot_leads(self, limit: int = 10) -> dict[str, Any]:
        """
        Get contractors showing high interest across all campaigns

        Returns contractors with high engagement scores or explicit interest
        """
        try:
            # Get high interest responses
            result = self.supabase.table("bid_card_distributions").select(
                "*, potential_contractors!contractor_id(*), bid_cards!bid_card_id(*)"
            ).eq("interest_level", "high").order(
                "responded_at", desc=True
            ).limit(limit).execute()

            hot_leads = []
            for dist in result.data:
                contractor = dist.get("potential_contractors", {})
                bid_card = dist.get("bid_cards", {})

                hot_leads.append({
                    "contractor_id": dist["contractor_id"],
                    "company_name": contractor.get("company_name", "Unknown"),
                    "contact_info": {
                        "email": contractor.get("primary_email"),
                        "phone": contractor.get("phone")
                    },
                    "bid_card": {
                        "id": dist["bid_card_id"],
                        "project_type": bid_card.get("project_type", "Unknown"),
                        "location": bid_card.get("location", {})
                    },
                    "responded_at": dist["responded_at"],
                    "response_channel": dist.get("response_channel"),
                    "match_score": dist.get("match_score", 0),
                    "engagement_score": dist.get("engagement_score", 0)
                })

            return {
                "success": True,
                "total_hot_leads": len(hot_leads),
                "hot_leads": hot_leads
            }

        except Exception as e:
            print(f"[Monitor ERROR] Failed to get hot leads: {e}")
            return {"success": False, "error": str(e)}

    def get_contractor_engagement_history(self, contractor_id: str) -> dict[str, Any]:
        """Get complete engagement history for a contractor"""
        try:
            # Get all distributions for this contractor
            dist_result = self.supabase.table("bid_card_distributions").select(
                "*, bid_cards!bid_card_id(*)"
            ).eq("contractor_id", contractor_id).order("distributed_at", desc=True).execute()

            # Get all responses
            self.supabase.table("contractor_responses").select("*").eq(
                "contractor_id", contractor_id
            ).order("responded_at", desc=True).execute()

            distributions = dist_result.data if dist_result.data else []

            # Build engagement timeline
            timeline = []

            for dist in distributions:
                bid_card = dist.get("bid_cards", {})

                # Distribution event
                timeline.append({
                    "event_type": "outreach_sent",
                    "timestamp": dist["distributed_at"],
                    "channel": dist["distribution_method"],
                    "bid_card": bid_card.get("project_type", "Unknown"),
                    "bid_card_id": dist["bid_card_id"]
                })

                # Open event
                if dist.get("opened_at"):
                    timeline.append({
                        "event_type": "email_opened",
                        "timestamp": dist["opened_at"],
                        "bid_card_id": dist["bid_card_id"]
                    })

                # Response event
                if dist.get("responded_at"):
                    timeline.append({
                        "event_type": "responded",
                        "timestamp": dist["responded_at"],
                        "response_type": dist.get("response_type"),
                        "interest_level": dist.get("interest_level"),
                        "bid_card_id": dist["bid_card_id"]
                    })

            # Sort timeline by timestamp
            timeline.sort(key=lambda x: x["timestamp"], reverse=True)

            # Calculate engagement metrics
            total_outreach = len(distributions)
            total_opens = sum(1 for d in distributions if d.get("opened_at"))
            total_responses = sum(1 for d in distributions if d.get("responded_at"))
            high_interest_count = sum(1 for d in distributions if d.get("interest_level") == "high")

            return {
                "success": True,
                "contractor_id": contractor_id,
                "metrics": {
                    "total_outreach_received": total_outreach,
                    "total_opened": total_opens,
                    "total_responded": total_responses,
                    "high_interest_projects": high_interest_count,
                    "open_rate": (total_opens / total_outreach * 100) if total_outreach > 0 else 0,
                    "response_rate": (total_responses / total_outreach * 100) if total_outreach > 0 else 0
                },
                "engagement_timeline": timeline[:20],  # Last 20 events
                "current_status": self._determine_contractor_status(distributions)
            }

        except Exception as e:
            print(f"[Monitor ERROR] Failed to get engagement history: {e}")
            return {"success": False, "error": str(e)}

    def _log_response_event(self,
                          distribution_id: str,
                          event_type: str,
                          event_data: dict[str, Any]):
        """Log a response event for tracking"""
        try:
            event_record = {
                "distribution_id": distribution_id,
                "event_type": event_type,
                "event_data": event_data,
                "created_at": datetime.now().isoformat()
            }

            self.supabase.table("response_events").insert(event_record).execute()

        except Exception as e:
            print(f"[Monitor ERROR] Failed to log event: {e}")

    def _update_engagement_score(self, distribution_id: str, action: str):
        """Update contractor engagement score based on actions"""
        try:
            # Score weights
            scores = {
                "email_open": 10,
                "link_click": 25,
                "response": 50,
                "high_interest": 100
            }

            score_increment = scores.get(action, 0)

            # Get current score
            result = self.supabase.table("bid_card_distributions").select(
                "engagement_score"
            ).eq("id", distribution_id).limit(1).execute()

            if result.data:
                current_score = result.data[0].get("engagement_score", 0) or 0
                new_score = current_score + score_increment

                # Update score
                self.supabase.table("bid_card_distributions").update({
                    "engagement_score": new_score
                }).eq("id", distribution_id).execute()

        except Exception as e:
            print(f"[Monitor ERROR] Failed to update engagement score: {e}")

    def _create_high_interest_notification(self, distribution_data: dict[str, Any]):
        """Create notification for high interest responses"""
        try:
            notification = {
                "type": "high_interest_lead",
                "title": "Hot Lead Alert",
                "message": f'Contractor showed high interest in bid {distribution_data["bid_card_id"]}',
                "data": {
                    "contractor_id": distribution_data["contractor_id"],
                    "bid_card_id": distribution_data["bid_card_id"],
                    "distribution_id": distribution_data["id"]
                },
                "priority": "high",
                "created_at": datetime.now().isoformat()
            }

            self.supabase.table("notifications").insert(notification).execute()

        except Exception as e:
            print(f"[Monitor ERROR] Failed to create notification: {e}")

    def _get_best_channel(self, channel_stats: dict[str, dict[str, int]]) -> str:
        """Determine best performing channel"""
        best_channel = None
        best_response_rate = 0

        for channel, stats in channel_stats.items():
            if stats["sent"] > 0:
                response_rate = stats["responded"] / stats["sent"]
                if response_rate > best_response_rate:
                    best_response_rate = response_rate
                    best_channel = channel

        return best_channel or "none"

    def _determine_contractor_status(self, distributions: list[dict[str, Any]]) -> str:
        """Determine contractor's current engagement status"""
        if not distributions:
            return "new"

        # Check recent activity (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_distributions = [
            d for d in distributions
            if datetime.fromisoformat(d["distributed_at"].replace("Z", "+00:00")) > thirty_days_ago
        ]

        if not recent_distributions:
            return "inactive"

        # Check for high interest
        high_interest = any(d.get("interest_level") == "high" for d in recent_distributions)
        if high_interest:
            return "hot_lead"

        # Check for any responses
        any_responses = any(d.get("responded_at") for d in recent_distributions)
        if any_responses:
            return "engaged"

        # Check for opens
        any_opens = any(d.get("opened_at") for d in recent_distributions)
        if any_opens:
            return "aware"

        return "contacted"


# Create required tables
CREATE_TABLES_SQL = """
-- Contractor responses table
CREATE TABLE IF NOT EXISTS contractor_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distribution_id UUID REFERENCES bid_card_distributions(id),
    contractor_id UUID REFERENCES potential_contractors(id),
    bid_card_id UUID REFERENCES bid_cards(id),
    response_type TEXT NOT NULL,
    response_channel TEXT NOT NULL,
    response_content TEXT,
    interest_level TEXT,
    metadata JSONB,
    responded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Response events table (for detailed tracking)
CREATE TABLE IF NOT EXISTS response_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distribution_id UUID REFERENCES bid_card_distributions(id),
    event_type TEXT NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT,
    data JSONB,
    priority TEXT DEFAULT 'normal',
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add columns to bid_card_distributions if not exists
ALTER TABLE bid_card_distributions
ADD COLUMN IF NOT EXISTS interest_level TEXT,
ADD COLUMN IF NOT EXISTS response_channel TEXT,
ADD COLUMN IF NOT EXISTS engagement_score INTEGER DEFAULT 0;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_responses_contractor ON contractor_responses(contractor_id);
CREATE INDEX IF NOT EXISTS idx_responses_interest ON contractor_responses(interest_level);
CREATE INDEX IF NOT EXISTS idx_events_distribution ON response_events(distribution_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read_at);
"""


# Test the monitor
if __name__ == "__main__":
    monitor = ResponseMonitor()

    print("\nTesting Response Monitoring System...")

    # Test tracking email open
    test_open = monitor.track_email_open("test-dist-123")
    print(f"\nEmail Open Tracking: {json.dumps(test_open, indent=2)}")

    # Test tracking response
    test_response = monitor.track_contractor_response(
        distribution_id="test-dist-123",
        response_type="interested",
        response_channel="email",
        response_content="Yes, I would like to bid on this project. Please send more details.",
        metadata={"email_subject": "Re: Bathroom Renovation Opportunity"}
    )
    print(f"\nResponse Tracking: {json.dumps(test_response, indent=2)}")

    # Get analytics
    analytics = monitor.get_response_analytics()
    print(f"\nResponse Analytics: {json.dumps(analytics, indent=2)}")

    print("\nNote: Run the CREATE TABLES SQL in Supabase to set up required tables")
