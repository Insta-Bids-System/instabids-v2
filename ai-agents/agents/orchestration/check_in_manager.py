#!/usr/bin/env python3
"""
Campaign Check-in & Escalation Manager
Monitors contractor responses at 1/4 intervals and triggers escalations
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from supabase import Client, create_client

from .timing_probability_engine import ContractorOutreachCalculator, OutreachStrategy, UrgencyLevel


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CheckInStatus:
    """Status of a campaign check-in"""
    campaign_id: str
    check_in_number: int  # 1, 2, 3, 4
    check_in_percentage: float  # 25%, 50%, 75%, 100%
    scheduled_time: datetime

    # Progress metrics
    bids_expected: int
    bids_received: int
    responses_expected: int
    responses_received: int

    # Performance
    on_track: bool
    performance_ratio: float  # actual/expected

    # Escalation
    escalation_needed: bool
    additional_contractors_needed: dict[str, int]  # tier -> count

    # Recommendations
    actions_taken: list[str]
    recommendations: list[str]


class EscalationLevel(Enum):
    """Escalation severity levels"""
    NONE = "none"
    MILD = "mild"          # <90% of expected
    MODERATE = "moderate"  # <75% of expected
    SEVERE = "severe"      # <50% of expected
    CRITICAL = "critical"  # <25% of expected


class CampaignCheckInManager:
    """
    Manages check-ins and escalations for outreach campaigns
    Monitors at 25%, 50%, 75% of timeline
    """

    def __init__(self):
        """Initialize with Supabase connection"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials in environment")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.calculator = ContractorOutreachCalculator()

    async def schedule_campaign_check_ins(self,
                                        campaign_id: str,
                                        bid_card_id: str,
                                        strategy: OutreachStrategy) -> list[dict[str, Any]]:
        """
        Schedule check-ins for a campaign based on the outreach strategy

        Returns list of scheduled check-in records
        """
        check_ins = []
        check_points = [0.25, 0.50, 0.75]  # 1/4 intervals

        campaign_start = datetime.now()

        for i, percentage in enumerate(check_points):
            check_in_time = campaign_start + timedelta(hours=strategy.timeline_hours * percentage)

            # Calculate expected progress
            expected_bids = int(strategy.bids_needed * percentage)
            expected_responses = int(strategy.expected_total_responses * percentage)

            # Create check-in record (mapped to actual database column names)
            check_in = {
                "campaign_id": campaign_id,
                "check_in_number": i + 1,
                "check_in_percentage": int(percentage * 100),  # INTEGER field
                "scheduled_time": check_in_time.isoformat(),
                "expected_bids": expected_bids,
                "responses_expected": expected_responses,  # mapped from expected_responses
                "escalation_needed": False,
                "check_in_time": check_in_time.isoformat(),  # Required field
                "progress_percentage": 0,  # Required field, start at 0
                "status": "pending"  # Set default status
            }

            # Insert into database
            result = self.supabase.table("campaign_check_ins").insert(check_in).execute()
            check_ins.append(result.data[0])

            logger.info(f"Scheduled check-in #{i+1} at {percentage*100}% "
                       f"({check_in_time.strftime('%Y-%m-%d %H:%M')})")

        return check_ins

    async def perform_check_in(self,
                             campaign_id: str,
                             check_in_id: Optional[str] = None) -> CheckInStatus:
        """
        Perform a check-in for a campaign
        Evaluates progress and determines if escalation is needed
        """
        # Get campaign data
        campaign = await self._get_campaign_data(campaign_id)

        # Get current check-in or find the appropriate one
        if check_in_id:
            check_in = self.supabase.table("campaign_check_ins")\
                .select("*")\
                .eq("id", check_in_id)\
                .single()\
                .execute().data
        else:
            # Find the next pending check-in
            check_ins = self.supabase.table("campaign_check_ins")\
                .select("*")\
                .eq("campaign_id", campaign_id)\
                .is_("completed_at", "null")\
                .order("scheduled_time")\
                .limit(1)\
                .execute().data

            if not check_ins:
                raise ValueError(f"No pending check-ins for campaign {campaign_id}")

            check_in = check_ins[0]

        # Get actual progress
        bids_received = await self._count_bids_received(campaign["bid_card_id"])
        responses_received = await self._count_responses_received(campaign_id)

        # Calculate performance
        performance_ratio = (bids_received / check_in["expected_bids"] * 100
                           if check_in["expected_bids"] > 0 else 0)

        on_track = performance_ratio >= 75  # 75% threshold

        # Determine escalation level
        escalation_level = self._determine_escalation_level(performance_ratio)
        escalation_needed = escalation_level != EscalationLevel.NONE

        # Calculate additional contractors needed
        additional_needed = {}
        if escalation_needed:
            additional_needed = await self._calculate_additional_contractors(
                campaign_id,
                check_in["expected_bids"] - bids_received,
                campaign["timeline_hours"] - (campaign["timeline_hours"] * check_in["check_in_percentage"] / 100)
            )

        # Generate recommendations
        recommendations = self._generate_check_in_recommendations(
            escalation_level,
            performance_ratio,
            check_in["check_in_number"]
        )

        # Update check-in record
        update_data = {
            "completed_at": datetime.now().isoformat(),
            "actual_bids": bids_received,
            "actual_responses": responses_received,
            "on_track": on_track,
            "escalation_needed": escalation_needed
        }

        self.supabase.table("campaign_check_ins")\
            .update(update_data)\
            .eq("id", check_in["id"])\
            .execute()

        # Create status object
        status = CheckInStatus(
            campaign_id=campaign_id,
            check_in_number=check_in["check_in_number"],
            check_in_percentage=check_in["check_in_percentage"],
            scheduled_time=datetime.fromisoformat(check_in["scheduled_time"]),
            bids_expected=check_in["expected_bids"],
            bids_received=bids_received,
            responses_expected=check_in["responses_expected"],
            responses_received=responses_received,
            on_track=on_track,
            performance_ratio=performance_ratio,
            escalation_needed=escalation_needed,
            additional_contractors_needed=additional_needed,
            actions_taken=[],
            recommendations=recommendations
        )

        # Trigger escalation if needed
        if escalation_needed:
            actions = await self._trigger_escalation(campaign_id, status)
            status.actions_taken = actions

        return status

    async def _get_campaign_data(self, campaign_id: str) -> dict[str, Any]:
        """Get campaign details including bid card and timeline"""
        result = self.supabase.table("outreach_campaigns")\
            .select("*, bid_cards!inner(*)")\
            .eq("id", campaign_id)\
            .single()\
            .execute()

        if not result.data:
            raise ValueError(f"Campaign {campaign_id} not found")

        campaign = result.data
        bid_card = campaign["bid_cards"]

        # Calculate timeline hours from bid card
        if bid_card["preferred_date"]:
            preferred_date = datetime.fromisoformat(bid_card["preferred_date"])
            timeline_hours = (preferred_date - datetime.now()).total_seconds() / 3600
        else:
            # Default timelines by urgency
            urgency_timelines = {
                "emergency": 6,
                "urgent": 24,
                "standard": 72,
                "flexible": 168
            }
            timeline_hours = urgency_timelines.get(bid_card.get("urgency_level", "standard"), 72)

        campaign["timeline_hours"] = max(1, timeline_hours)  # Minimum 1 hour
        campaign["bid_card_id"] = bid_card["id"]

        return campaign

    async def _count_bids_received(self, bid_card_id: str) -> int:
        """Count actual bids received for a bid card"""
        result = self.supabase.table("bids")\
            .select("id")\
            .eq("bid_card_id", bid_card_id)\
            .execute()

        return len(result.data)

    async def _count_responses_received(self, campaign_id: str) -> int:
        """Count contractor responses for a campaign"""
        result = self.supabase.table("contractor_responses")\
            .select("id")\
            .eq("campaign_id", campaign_id)\
            .not_.is_("responded_at", "null")\
            .execute()

        return len(result.data)

    def _determine_escalation_level(self, performance_ratio: float) -> EscalationLevel:
        """Determine escalation level based on performance"""
        if performance_ratio >= 90:
            return EscalationLevel.NONE
        elif performance_ratio >= 75:
            return EscalationLevel.MILD
        elif performance_ratio >= 50:
            return EscalationLevel.MODERATE
        elif performance_ratio >= 25:
            return EscalationLevel.SEVERE
        else:
            return EscalationLevel.CRITICAL

    async def _calculate_additional_contractors(self,
                                              campaign_id: str,
                                              bids_shortfall: int,
                                              remaining_hours: float) -> dict[str, int]:
        """Calculate how many additional contractors to add"""
        # Get current tier distribution
        current_distribution = await self._get_current_tier_distribution(campaign_id)

        # Use calculator to determine additional needs
        # Start with Tier 2 (prospects), then Tier 3 if needed
        additional = {
            "tier_1": 0,  # Don't add more internal - they should have responded
            "tier_2": min(4, bids_shortfall),  # Add up to 4 prospects
            "tier_3": max(0, bids_shortfall - 4)  # Rest from new/cold
        }

        # Check against maximums
        if current_distribution["tier_2"] + additional["tier_2"] > 10:
            additional["tier_2"] = max(0, 10 - current_distribution["tier_2"])
            additional["tier_3"] = bids_shortfall - additional["tier_2"]

        if current_distribution["tier_3"] + additional["tier_3"] > 15:
            additional["tier_3"] = max(0, 15 - current_distribution["tier_3"])

        return additional

    async def _get_current_tier_distribution(self, campaign_id: str) -> dict[str, int]:
        """Get current contractor distribution by tier"""
        result = self.supabase.table("campaign_contractors")\
            .select("contractor_tiers!inner(tier)")\
            .eq("campaign_id", campaign_id)\
            .execute()

        distribution = {"tier_1": 0, "tier_2": 0, "tier_3": 0}

        for contractor in result.data:
            tier = contractor["contractor_tiers"]["tier"]
            distribution[f"tier_{tier}"] += 1

        return distribution

    def _generate_check_in_recommendations(self,
                                         escalation_level: EscalationLevel,
                                         performance_ratio: float,
                                         check_in_number: int) -> list[str]:
        """Generate actionable recommendations based on check-in results"""
        recommendations = []

        if escalation_level == EscalationLevel.NONE:
            recommendations.append("Campaign on track - continue monitoring")

        elif escalation_level == EscalationLevel.MILD:
            recommendations.append("Consider sending reminder messages to non-responders")
            recommendations.append("Verify contact information is correct")

        elif escalation_level == EscalationLevel.MODERATE:
            recommendations.append("Add additional contractors from Tier 2 and 3")
            recommendations.append("Switch to phone calls for Tier 1 contractors")
            recommendations.append("Review and adjust messaging for better engagement")

        elif escalation_level == EscalationLevel.SEVERE:
            recommendations.append("Immediately add all available qualified contractors")
            recommendations.append("Escalate to manual outreach team")
            recommendations.append("Consider expanding search radius or criteria")

        elif escalation_level == EscalationLevel.CRITICAL:
            recommendations.append("URGENT: Manual intervention required")
            recommendations.append("Contact all available contractors regardless of tier")
            recommendations.append("Consider adjusting project timeline or requirements")
            recommendations.append("Alert homeowner about potential delays")

        # Check-in specific recommendations
        if check_in_number == 1 and performance_ratio < 50:
            recommendations.append("Early warning: Adjust strategy now to avoid issues")
        elif check_in_number == 2 and performance_ratio < 75:
            recommendations.append("Halfway point: Need aggressive escalation")
        elif check_in_number == 3 and performance_ratio < 100:
            recommendations.append("Final stretch: Use all available resources")

        return recommendations

    def _calculate_check_in_times(self, start_time: datetime, timeline_hours: int) -> list[datetime]:
        """Calculate check-in times at 25%, 50%, 75% intervals"""
        intervals = [0.25, 0.50, 0.75]
        return [start_time + timedelta(hours=timeline_hours * interval) for interval in intervals]

    async def _trigger_escalation(self,
                                campaign_id: str,
                                status: CheckInStatus) -> list[str]:
        """Trigger escalation actions and return list of actions taken"""
        actions_taken = []

        # Add additional contractors
        if status.additional_contractors_needed:
            for tier_key, count in status.additional_contractors_needed.items():
                if count > 0:
                    tier_num = int(tier_key.split("_")[1])
                    added = await self._add_contractors_to_campaign(
                        campaign_id,
                        tier_num,
                        count
                    )
                    actions_taken.append(f"Added {added} Tier {tier_num} contractors")

        # Send urgent reminders
        if status.escalation_needed:
            reminded = await self._send_urgent_reminders(campaign_id)
            if reminded > 0:
                actions_taken.append(f"Sent urgent reminders to {reminded} contractors")

        # Update campaign priority
        if status.performance_ratio < 50:
            self.supabase.table("outreach_campaigns")\
                .update({"priority": "high", "escalated": True})\
                .eq("id", campaign_id)\
                .execute()
            actions_taken.append("Elevated campaign to high priority")

        # Log escalation
        self.supabase.table("campaign_escalations").insert({
            "campaign_id": campaign_id,
            "check_in_id": status.check_in_number,
            "escalation_level": self._determine_escalation_level(status.performance_ratio).value,
            "performance_ratio": status.performance_ratio,
            "actions_taken": actions_taken,
            "created_at": datetime.now().isoformat()
        }).execute()

        return actions_taken

    async def _add_contractors_to_campaign(self,
                                         campaign_id: str,
                                         tier: int,
                                         count: int) -> int:
        """Add additional contractors from specified tier"""
        # Get eligible contractors not already in campaign
        existing = self.supabase.table("campaign_contractors")\
            .select("contractor_id")\
            .eq("campaign_id", campaign_id)\
            .execute()

        existing_ids = [c["contractor_id"] for c in existing.data]

        # Find new contractors from the tier
        eligible = self.supabase.table("eligible_contractors")\
            .select("*")\
            .eq("tier", tier)\
            .not_.in_("id", existing_ids)\
            .order("response_rate", desc=True)\
            .limit(count)\
            .execute()

        added = 0
        for contractor in eligible.data:
            self.supabase.table("campaign_contractors").insert({
                "campaign_id": campaign_id,
                "contractor_id": contractor["id"],
                "added_via_escalation": True,
                "created_at": datetime.now().isoformat()
            }).execute()
            added += 1

        return added

    async def _send_urgent_reminders(self, campaign_id: str) -> int:
        """Send urgent reminders to non-responsive contractors"""
        # Get contractors who haven't responded
        non_responders = self.supabase.table("campaign_contractors")\
            .select("*, contractor_responses!left(*)")\
            .eq("campaign_id", campaign_id)\
            .is_("contractor_responses.responded_at", "null")\
            .execute()

        reminded = 0
        for contractor in non_responders.data:
            # Queue urgent reminder
            self.supabase.table("outreach_queue").insert({
                "campaign_id": campaign_id,
                "contractor_id": contractor["contractor_id"],
                "message_type": "urgent_reminder",
                "priority": "high",
                "scheduled_for": datetime.now().isoformat()
            }).execute()
            reminded += 1

        return reminded

    async def monitor_active_campaigns(self):
        """
        Background task to monitor all active campaigns
        Checks for due check-ins and processes them
        """
        while True:
            try:
                # Find due check-ins
                due_check_ins = self.supabase.table("campaign_check_ins")\
                    .select("*, outreach_campaigns!inner(*)")\
                    .lte("scheduled_time", datetime.now().isoformat())\
                    .is_("completed_at", "null")\
                    .execute()

                for check_in in due_check_ins.data:
                    try:
                        logger.info(f"Processing check-in for campaign {check_in['campaign_id']}")
                        status = await self.perform_check_in(
                            check_in["campaign_id"],
                            check_in["id"]
                        )

                        # Log results
                        logger.info(f"Check-in complete: {status.performance_ratio:.1f}% of target")
                        if status.escalation_needed:
                            logger.warning(f"Escalation triggered: {status.actions_taken}")

                    except Exception as e:
                        logger.error(f"Error processing check-in {check_in['id']}: {e}")

                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in campaign monitor: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error


# Example usage and testing
if __name__ == "__main__":
    manager = CampaignCheckInManager()

    # Test check-in scenarios
    async def test_check_ins():
        # Mock campaign data
        test_campaign_id = "test-campaign-123"

        # Create mock outreach strategy
        strategy = OutreachStrategy(
            bids_needed=4,
            timeline_hours=24,
            urgency_level=UrgencyLevel.URGENT,
            tier1_strategy=None,  # Would be filled by calculator
            tier2_strategy=None,
            tier3_strategy=None,
            total_to_contact=12,
            expected_total_responses=4.5,
            check_in_times=[
                datetime.now() + timedelta(hours=6),
                datetime.now() + timedelta(hours=12),
                datetime.now() + timedelta(hours=18)
            ],
            escalation_thresholds={},
            confidence_score=85.0,
            risk_factors=[],
            recommendations=[]
        )

        print("CAMPAIGN CHECK-IN MANAGER TEST")
        print("=" * 50)

        # Schedule check-ins
        print("\nScheduling check-ins...")
        check_ins = await manager.schedule_campaign_check_ins(
            test_campaign_id,
            "test-bid-card-123",
            strategy
        )

        print(f"Scheduled {len(check_ins)} check-ins")

        # Simulate check-in scenarios
        scenarios = [
            {"name": "On Track", "bids": 1, "responses": 3},
            {"name": "Needs Escalation", "bids": 0, "responses": 1},
            {"name": "Critical", "bids": 0, "responses": 0}
        ]

        for scenario in scenarios:
            print(f"\n\nScenario: {scenario['name']}")
            print("-" * 30)

            # Mock the counts
            manager._count_bids_received = lambda x: scenario["bids"]
            manager._count_responses_received = lambda x: scenario["responses"]

            # Perform check-in
            # Note: This would need proper mocking in real tests
            print(f"Bids: {scenario['bids']}, Responses: {scenario['responses']}")

    # Run test
    asyncio.run(test_check_ins())
