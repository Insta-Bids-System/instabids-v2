"""
Bid Card Distribution Tracker
Tracks which contractors received which bid cards and when
Prevents duplicate sends and enables follow-up campaigns
"""
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from dotenv import load_dotenv
from supabase import create_client


class BidDistributionTracker:
    """Tracks bid card distribution to contractors"""

    def __init__(self):
        """Initialize tracker with Supabase connection"""
        load_dotenv(override=True)
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)

        print("[BidTracker] Initialized Bid Distribution Tracker")

    def record_distribution(self,
                          bid_card_id: str,
                          contractor_id: str,
                          distribution_method: str,
                          match_score: Optional[float] = None,
                          campaign_id: Optional[str] = None) -> dict[str, Any]:
        """
        Record that a bid card was sent to a contractor

        Args:
            bid_card_id: ID of the bid card
            contractor_id: ID of the contractor
            distribution_method: How it was sent (email, sms, form, manual)
            match_score: Opus 4 match score if available
            campaign_id: ID of the outreach campaign

        Returns:
            Dict with success status and distribution record
        """
        try:
            # Check if already distributed
            existing = self._check_existing_distribution(bid_card_id, contractor_id)

            if existing:
                return {
                    "success": False,
                    "error": "Already distributed",
                    "existing_record": existing,
                    "message": f'Bid card already sent to this contractor on {existing["distributed_at"]}'
                }

            # Create distribution record
            distribution_record = {
                "id": str(uuid.uuid4()),
                "bid_card_id": bid_card_id,
                "contractor_id": contractor_id,
                "distribution_method": distribution_method,
                "match_score": match_score,
                "campaign_id": campaign_id,
                "distributed_at": datetime.now().isoformat(),
                "status": "sent",
                "opened_at": None,
                "responded_at": None,
                "response_type": None,
                "follow_up_count": 0,
                "last_follow_up_at": None
            }

            # Store in database
            result = self.supabase.table("bid_card_distributions").insert(distribution_record).execute()

            if result.data:
                print(f"[BidTracker] Recorded distribution: Bid {bid_card_id} → Contractor {contractor_id} via {distribution_method}")
                return {
                    "success": True,
                    "distribution_id": result.data[0]["id"],
                    "record": result.data[0]
                }
            else:
                return {"success": False, "error": "Failed to store distribution record"}

        except Exception as e:
            print(f"[BidTracker ERROR] Failed to record distribution: {e}")
            return {"success": False, "error": str(e)}

    def _check_existing_distribution(self, bid_card_id: str, contractor_id: str) -> Optional[dict[str, Any]]:
        """Check if bid card was already sent to contractor"""
        try:
            result = self.supabase.table("bid_card_distributions").select("*").eq(
                "bid_card_id", bid_card_id
            ).eq(
                "contractor_id", contractor_id
            ).limit(1).execute()

            return result.data[0] if result.data else None

        except Exception:
            return None

    def get_contractors_for_bid(self, bid_card_id: str) -> dict[str, Any]:
        """Get all contractors who received a specific bid card"""
        try:
            result = self.supabase.table("bid_card_distributions").select(
                "*, potential_contractors!contractor_id(*)"
            ).eq("bid_card_id", bid_card_id).execute()

            contractors = []
            for dist in result.data:
                contractor_info = dist.get("potential_contractors", {})
                contractors.append({
                    "contractor_id": dist["contractor_id"],
                    "company_name": contractor_info.get("company_name", "Unknown"),
                    "distributed_at": dist["distributed_at"],
                    "method": dist["distribution_method"],
                    "status": dist["status"],
                    "responded": bool(dist.get("responded_at")),
                    "match_score": dist.get("match_score")
                })

            return {
                "success": True,
                "bid_card_id": bid_card_id,
                "total_distributed": len(contractors),
                "contractors": contractors,
                "response_rate": sum(1 for c in contractors if c["responded"]) / len(contractors) * 100 if contractors else 0
            }

        except Exception as e:
            print(f"[BidTracker ERROR] Failed to get contractors: {e}")
            return {"success": False, "error": str(e)}

    def get_bids_for_contractor(self, contractor_id: str) -> dict[str, Any]:
        """Get all bid cards sent to a specific contractor"""
        try:
            result = self.supabase.table("bid_card_distributions").select(
                "*, bid_cards!bid_card_id(*)"
            ).eq("contractor_id", contractor_id).execute()

            bid_cards = []
            for dist in result.data:
                bid_info = dist.get("bid_cards", {})
                bid_cards.append({
                    "bid_card_id": dist["bid_card_id"],
                    "project_type": bid_info.get("project_type", "Unknown"),
                    "distributed_at": dist["distributed_at"],
                    "method": dist["distribution_method"],
                    "status": dist["status"],
                    "opened": bool(dist.get("opened_at")),
                    "responded": bool(dist.get("responded_at"))
                })

            return {
                "success": True,
                "contractor_id": contractor_id,
                "total_received": len(bid_cards),
                "bid_cards": bid_cards
            }

        except Exception as e:
            print(f"[BidTracker ERROR] Failed to get bid cards: {e}")
            return {"success": False, "error": str(e)}

    def update_status(self,
                     bid_card_id: str,
                     contractor_id: str,
                     status_update: dict[str, Any]) -> dict[str, Any]:
        """
        Update distribution status (opened, responded, etc.)

        status_update can include:
        - opened_at: When contractor opened the message
        - responded_at: When contractor responded
        - response_type: 'interested', 'not_interested', 'need_info', 'busy'
        - response_notes: Any additional notes
        """
        try:
            # Find the distribution record
            existing = self._check_existing_distribution(bid_card_id, contractor_id)

            if not existing:
                return {"success": False, "error": "Distribution record not found"}

            # Update the record
            result = self.supabase.table("bid_card_distributions").update(
                status_update
            ).eq("id", existing["id"]).execute()

            if result.data:
                print(f"[BidTracker] Updated status for Bid {bid_card_id} → Contractor {contractor_id}")
                return {"success": True, "updated": result.data[0]}
            else:
                return {"success": False, "error": "Failed to update status"}

        except Exception as e:
            print(f"[BidTracker ERROR] Failed to update status: {e}")
            return {"success": False, "error": str(e)}

    def get_follow_up_candidates(self,
                               days_since_sent: int = 3,
                               max_follow_ups: int = 2) -> dict[str, Any]:
        """Get contractors who need follow-up"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_since_sent)).isoformat()

            # Query for distributions that need follow-up
            result = self.supabase.table("bid_card_distributions").select(
                "*, potential_contractors!contractor_id(*), bid_cards!bid_card_id(*)"
            ).is_("responded_at", "null").lt("distributed_at", cutoff_date).lt("follow_up_count", max_follow_ups).execute()

            candidates = []
            for dist in result.data:
                contractor = dist.get("potential_contractors", {})
                bid_card = dist.get("bid_cards", {})

                candidates.append({
                    "distribution_id": dist["id"],
                    "bid_card_id": dist["bid_card_id"],
                    "contractor_id": dist["contractor_id"],
                    "company_name": contractor.get("company_name", "Unknown"),
                    "project_type": bid_card.get("project_type", "Unknown"),
                    "distributed_at": dist["distributed_at"],
                    "days_since_sent": (datetime.now() - datetime.fromisoformat(dist["distributed_at"])).days,
                    "follow_up_count": dist["follow_up_count"],
                    "last_method": dist["distribution_method"],
                    "match_score": dist.get("match_score", 0)
                })

            # Sort by match score (prioritize high matches)
            candidates.sort(key=lambda x: x["match_score"], reverse=True)

            return {
                "success": True,
                "total_candidates": len(candidates),
                "candidates": candidates
            }

        except Exception as e:
            print(f"[BidTracker ERROR] Failed to get follow-up candidates: {e}")
            return {"success": False, "error": str(e)}

    def record_follow_up(self, distribution_id: str, method: str) -> dict[str, Any]:
        """Record that a follow-up was sent"""
        try:
            result = self.supabase.table("bid_card_distributions").update({
                "follow_up_count": self.supabase.rpc("increment", {"x": 1}),
                "last_follow_up_at": datetime.now().isoformat(),
                "last_follow_up_method": method
            }).eq("id", distribution_id).execute()

            return {"success": bool(result.data)}

        except Exception as e:
            print(f"[BidTracker ERROR] Failed to record follow-up: {e}")
            return {"success": False, "error": str(e)}

    def get_distribution_analytics(self, bid_card_id: Optional[str] = None) -> dict[str, Any]:
        """Get analytics on bid distribution performance"""
        try:
            # Base query
            query = self.supabase.table("bid_card_distributions").select("*")

            if bid_card_id:
                query = query.eq("bid_card_id", bid_card_id)

            result = query.execute()

            if not result.data:
                return {"success": True, "message": "No distribution data found"}

            # Calculate analytics
            total = len(result.data)
            opened = sum(1 for d in result.data if d.get("opened_at"))
            responded = sum(1 for d in result.data if d.get("responded_at"))
            interested = sum(1 for d in result.data if d.get("response_type") == "interested")

            # Method breakdown
            method_stats = {}
            for dist in result.data:
                method = dist["distribution_method"]
                if method not in method_stats:
                    method_stats[method] = {"sent": 0, "opened": 0, "responded": 0}
                method_stats[method]["sent"] += 1
                if dist.get("opened_at"):
                    method_stats[method]["opened"] += 1
                if dist.get("responded_at"):
                    method_stats[method]["responded"] += 1

            # Match score performance
            score_ranges = {"90-100": 0, "70-89": 0, "50-69": 0, "0-49": 0}
            score_responses = {"90-100": 0, "70-89": 0, "50-69": 0, "0-49": 0}

            for dist in result.data:
                score = dist.get("match_score", 0)
                if score >= 90:
                    range_key = "90-100"
                elif score >= 70:
                    range_key = "70-89"
                elif score >= 50:
                    range_key = "50-69"
                else:
                    range_key = "0-49"

                score_ranges[range_key] += 1
                if dist.get("responded_at"):
                    score_responses[range_key] += 1

            analytics = {
                "success": True,
                "total_distributed": total,
                "open_rate": (opened / total * 100) if total > 0 else 0,
                "response_rate": (responded / total * 100) if total > 0 else 0,
                "interest_rate": (interested / total * 100) if total > 0 else 0,
                "method_performance": method_stats,
                "match_score_performance": {
                    range_key: {
                        "sent": count,
                        "response_rate": (score_responses[range_key] / count * 100) if count > 0 else 0
                    }
                    for range_key, count in score_ranges.items()
                }
            }

            if bid_card_id:
                analytics["bid_card_id"] = bid_card_id

            return analytics

        except Exception as e:
            print(f"[BidTracker ERROR] Failed to get analytics: {e}")
            return {"success": False, "error": str(e)}


# Create the table if it doesn't exist
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS bid_card_distributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_card_id UUID REFERENCES bid_cards(id),
    contractor_id UUID REFERENCES potential_contractors(id),
    distribution_method TEXT NOT NULL,
    match_score FLOAT,
    campaign_id TEXT,
    distributed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    opened_at TIMESTAMP WITH TIME ZONE,
    responded_at TIMESTAMP WITH TIME ZONE,
    response_type TEXT,
    response_notes TEXT,
    status TEXT DEFAULT 'sent',
    follow_up_count INTEGER DEFAULT 0,
    last_follow_up_at TIMESTAMP WITH TIME ZONE,
    last_follow_up_method TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bid_card_id, contractor_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_bid_distributions_bid_card ON bid_card_distributions(bid_card_id);
CREATE INDEX IF NOT EXISTS idx_bid_distributions_contractor ON bid_card_distributions(contractor_id);
CREATE INDEX IF NOT EXISTS idx_bid_distributions_status ON bid_card_distributions(status);
CREATE INDEX IF NOT EXISTS idx_bid_distributions_response ON bid_card_distributions(responded_at);
"""


# Test the tracker
if __name__ == "__main__":
    tracker = BidDistributionTracker()

    print("\nTesting Bid Distribution Tracker...")

    # Test recording a distribution
    test_result = tracker.record_distribution(
        bid_card_id="test-bid-123",
        contractor_id="test-contractor-456",
        distribution_method="email",
        match_score=85.5,
        campaign_id="campaign-001"
    )

    print(f"\nRecord Distribution Result: {json.dumps(test_result, indent=2)}")

    # Test getting analytics
    analytics = tracker.get_distribution_analytics()
    print(f"\nDistribution Analytics: {json.dumps(analytics, indent=2)}")

    print("\nNote: Run the CREATE TABLE SQL in Supabase to set up the bid_card_distributions table")
