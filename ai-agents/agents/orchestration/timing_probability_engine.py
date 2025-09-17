#!/usr/bin/env python3
"""
Timing & Probability Engine for Contractor Outreach
Calculates how many contractors to contact based on bid requirements and timeline
"""

import math
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from dotenv import load_dotenv


load_dotenv()


class UrgencyLevel(Enum):
    """Project urgency levels - AGGRESSIVE BUSINESS TIMELINES"""
    EMERGENCY = "emergency"      # < 1 hour (NOTE: Future enhancement - needs pre-loaded contractors for lockouts/emergency plumbing)
    URGENT = "urgent"           # 1-12 hours (same day response)
    STANDARD = "standard"       # 12-72 hours (3 day max)
    GROUP_BIDDING = "group_bidding"  # 72-120 hours (5 day max, multiple projects)
    FLEXIBLE = "flexible"       # 120+ hours (5+ days, absolute maximum)


@dataclass
class TierStrategy:
    """Outreach strategy for a contractor tier"""
    tier: int
    tier_name: str
    response_rate: float
    available_count: int
    to_contact: int
    expected_responses: float


@dataclass
class OutreachStrategy:
    """Complete outreach strategy for a project"""
    bids_needed: int
    timeline_hours: int
    urgency_level: UrgencyLevel

    # Tier strategies
    tier1_strategy: TierStrategy
    tier2_strategy: TierStrategy
    tier3_strategy: TierStrategy

    # Totals
    total_to_contact: int
    expected_total_responses: float

    # Check-in schedule (AGGRESSIVE TIMING)
    check_in_times: list[datetime]
    escalation_thresholds: dict[datetime, int]  # Expected bids at each check-in

    # Recommendations
    confidence_score: float  # 0-100, likelihood of success
    risk_factors: list[str]
    recommendations: list[str]

    # Group bidding support (with defaults)
    is_group_bidding: bool = False
    group_bidding_projects: Optional[list[str]] = None  # Other project IDs in group


class ContractorOutreachCalculator:
    """
    Calculate optimal contractor outreach strategy
    Core business rule: Need 4 bids minimum per project
    """

    def __init__(self):
        """Initialize with response rate assumptions"""
        # Response rates by tier (can be updated from historical data)
        self.base_response_rates = {
            1: 0.90,  # 90% for internal contractors
            2: 0.50,  # 50% for prospects
            3: 0.33   # 33% for new/cold
        }

        # Maximum contractors per tier (business rules)
        self.max_per_tier = {
            1: 5,   # Max 5 internal contractors
            2: 10,  # Max 10 prospects
            3: 15   # Max 15 new/cold
        }

        # Urgency multipliers for AGGRESSIVE TIMELINES
        self.urgency_multipliers = {
            UrgencyLevel.EMERGENCY: 0.6,      # 40% lower response rate (< 1 hour)
            UrgencyLevel.URGENT: 0.75,        # 25% lower response rate (same day)
            UrgencyLevel.STANDARD: 1.0,       # Normal response rate (3 days)
            UrgencyLevel.GROUP_BIDDING: 1.15, # 15% higher (contractors like multiple projects)
            UrgencyLevel.FLEXIBLE: 1.1        # 10% higher response rate (5+ days)
        }

    def calculate_outreach_strategy(self,
                                  bids_needed: int = 4,
                                  timeline_hours: int = 24,
                                  tier1_available: int = 10,
                                  tier2_available: int = 30,
                                  tier3_available: int = 100,
                                  project_type: Optional[str] = None,
                                  location: Optional[dict[str, Any]] = None,
                                  group_bidding_projects: Optional[list[str]] = None) -> OutreachStrategy:
        """
        Calculate optimal outreach strategy with AGGRESSIVE BUSINESS TIMELINES

        Args:
            bids_needed: Target number of bids (default 4)
            timeline_hours: Hours available to get bids (AGGRESSIVE TIMELINES)
            tier1_available: Number of Tier 1 contractors available
            tier2_available: Number of Tier 2 contractors available
            tier3_available: Number of Tier 3 contractors available
            project_type: Type of project (affects response rates)
            location: Project location (affects availability)
            group_bidding_projects: List of project IDs for group bidding (increases response rates)

        Returns:
            Complete outreach strategy with aggressive check-in schedule and group bidding support
        """
        # Determine urgency level
        urgency = self._determine_urgency(timeline_hours)

        # Check if this is group bidding scenario
        is_group_bidding = bool(group_bidding_projects) or urgency == UrgencyLevel.GROUP_BIDDING

        # Adjust response rates based on urgency and group bidding
        adjusted_rates = self._adjust_response_rates(urgency, project_type, is_group_bidding)

        # Calculate contractors needed per tier
        tier_strategies = self._calculate_tier_strategies(
            bids_needed,
            tier1_available,
            tier2_available,
            tier3_available,
            adjusted_rates
        )

        # Calculate check-in schedule
        check_in_times = self._calculate_check_in_schedule(timeline_hours)

        # Calculate escalation thresholds
        escalation_thresholds = self._calculate_escalation_thresholds(
            bids_needed,
            timeline_hours,
            check_in_times
        )

        # Calculate totals
        total_to_contact = sum(s.to_contact for s in tier_strategies)
        expected_responses = sum(s.expected_responses for s in tier_strategies)

        # Assess confidence and risks
        confidence_score = self._calculate_confidence_score(
            expected_responses,
            bids_needed,
            total_to_contact
        )

        risk_factors = self._identify_risk_factors(
            tier_strategies,
            urgency,
            confidence_score
        )

        recommendations = self._generate_recommendations(
            tier_strategies,
            confidence_score,
            risk_factors,
            urgency
        )

        return OutreachStrategy(
            bids_needed=bids_needed,
            timeline_hours=timeline_hours,
            urgency_level=urgency,
            tier1_strategy=tier_strategies[0],
            tier2_strategy=tier_strategies[1],
            tier3_strategy=tier_strategies[2],
            total_to_contact=total_to_contact,
            expected_total_responses=expected_responses,
            check_in_times=check_in_times,
            escalation_thresholds=escalation_thresholds,
            is_group_bidding=is_group_bidding,
            group_bidding_projects=group_bidding_projects or [],
            confidence_score=confidence_score,
            risk_factors=risk_factors,
            recommendations=recommendations
        )

    def _determine_urgency(self, timeline_hours: int) -> UrgencyLevel:
        """Determine urgency level based on AGGRESSIVE BUSINESS TIMELINES"""
        if timeline_hours < 1:
            return UrgencyLevel.EMERGENCY      # < 1 hour: Emergency
        elif timeline_hours <= 12:
            return UrgencyLevel.URGENT         # 1-12 hours: Same day
        elif timeline_hours <= 72:            # 12-72 hours: 3 days max
            return UrgencyLevel.STANDARD
        elif timeline_hours <= 120:           # 72-120 hours: 5 days max (group bidding)
            return UrgencyLevel.GROUP_BIDDING
        else:
            return UrgencyLevel.FLEXIBLE       # 120+ hours: 5+ days absolute maximum

    def _adjust_response_rates(self,
                             urgency: UrgencyLevel,
                             project_type: Optional[str] = None,
                             is_group_bidding: bool = False) -> dict[int, float]:
        """Adjust response rates based on urgency, project type, and group bidding"""
        multiplier = self.urgency_multipliers[urgency]

        # GROUP BIDDING BOOST: Contractors love multiple project opportunities
        if is_group_bidding:
            multiplier *= 1.2  # 20% higher response rate for group bidding

        # Additional adjustments for project type
        if project_type:
            if project_type.lower() in ["emergency", "urgent", "leak", "damage"]:
                multiplier *= 0.8  # Lower response rate for emergencies
            elif project_type.lower() in ["remodel", "renovation", "addition"]:
                multiplier *= 1.1  # Higher response rate for planned work

        return {
            tier: min(0.95, rate * multiplier)  # Cap at 95% max
            for tier, rate in self.base_response_rates.items()
        }

    def _calculate_tier_strategies(self,
                                 bids_needed: int,
                                 tier1_available: int,
                                 tier2_available: int,
                                 tier3_available: int,
                                 response_rates: dict[int, float]) -> list[TierStrategy]:
        """Calculate how many contractors to contact per tier"""
        strategies = []
        remaining_bids = bids_needed

        # Start with Tier 1 (highest response rate)
        tier1_to_contact = min(
            tier1_available,
            self.max_per_tier[1],
            math.ceil(remaining_bids / response_rates[1])
        )
        tier1_expected = tier1_to_contact * response_rates[1]
        remaining_bids = max(0, bids_needed - tier1_expected)

        strategies.append(TierStrategy(
            tier=1,
            tier_name="Internal",
            response_rate=response_rates[1],
            available_count=tier1_available,
            to_contact=tier1_to_contact,
            expected_responses=tier1_expected
        ))

        # Then Tier 2
        tier2_to_contact = min(
            tier2_available,
            self.max_per_tier[2],
            math.ceil(remaining_bids / response_rates[2]) if remaining_bids > 0 else 0
        )
        tier2_expected = tier2_to_contact * response_rates[2]
        remaining_bids = max(0, remaining_bids - tier2_expected)

        strategies.append(TierStrategy(
            tier=2,
            tier_name="Prospects",
            response_rate=response_rates[2],
            available_count=tier2_available,
            to_contact=tier2_to_contact,
            expected_responses=tier2_expected
        ))

        # Finally Tier 3
        tier3_to_contact = min(
            tier3_available,
            self.max_per_tier[3],
            math.ceil(remaining_bids / response_rates[3]) if remaining_bids > 0 else 0
        )
        tier3_expected = tier3_to_contact * response_rates[3]

        strategies.append(TierStrategy(
            tier=3,
            tier_name="New/Cold",
            response_rate=response_rates[3],
            available_count=tier3_available,
            to_contact=tier3_to_contact,
            expected_responses=tier3_expected
        ))

        return strategies

    def _calculate_check_in_schedule(self, timeline_hours: int) -> list[datetime]:
        """Calculate AGGRESSIVE check-in times based on business timeline requirements"""
        now = datetime.now()

        # AGGRESSIVE CHECK-IN SCHEDULES based on timeline
        if timeline_hours < 1:  # EMERGENCY: < 1 hour
            # Check every 15 minutes for first hour
            check_points = [0.25, 0.5, 0.75]  # 15min, 30min, 45min
        elif timeline_hours <= 12:  # URGENT: 1-12 hours (same day)
            # Check every 2-4 hours
            check_points = [0.17, 0.5, 0.83]  # 2hrs, 6hrs, 10hrs for 12hr timeline
        elif timeline_hours <= 72:  # STANDARD: 3 days max
            # Check every 12 hours
            check_points = [0.17, 0.5, 0.83]  # 12hrs, 36hrs, 60hrs for 72hr timeline
        elif timeline_hours <= 120:  # GROUP_BIDDING: 5 days max
            # Check daily
            check_points = [0.2, 0.5, 0.8]    # 24hrs, 60hrs, 96hrs for 120hr timeline
        else:  # FLEXIBLE: 5+ days
            # Standard check-ins
            check_points = [0.25, 0.50, 0.75]

        return [
            now + timedelta(hours=timeline_hours * point)
            for point in check_points
        ]

    def _calculate_escalation_thresholds(self,
                                       bids_needed: int,
                                       timeline_hours: int,
                                       check_in_times: list[datetime]) -> dict[datetime, int]:
        """Calculate expected bids at each check-in point"""
        # Linear progression expected
        check_points = [0.25, 0.50, 0.75]

        return {
            check_in_times[i]: math.ceil(bids_needed * check_points[i])
            for i in range(len(check_in_times))
        }

    def _calculate_confidence_score(self,
                                  expected_responses: float,
                                  bids_needed: int,
                                  total_to_contact: int) -> float:
        """Calculate confidence score (0-100)"""
        # Base confidence on expected vs needed ratio
        base_confidence = min(100, (expected_responses / bids_needed) * 100)

        # Penalize if we're contacting too many (desperation)
        if total_to_contact > 20:
            base_confidence *= 0.9

        # Boost if we have good margin
        if expected_responses >= bids_needed * 1.5:
            base_confidence = min(100, base_confidence * 1.1)

        return round(base_confidence, 1)

    def _identify_risk_factors(self,
                             tier_strategies: list[TierStrategy],
                             urgency: UrgencyLevel,
                             confidence_score: float) -> list[str]:
        """Identify potential risk factors"""
        risks = []

        # Low confidence
        if confidence_score < 70:
            risks.append("Low confidence in meeting bid target")

        # Too few Tier 1 contractors
        if tier_strategies[0].to_contact < 2:
            risks.append("Limited internal contractors available")

        # Heavy reliance on Tier 3
        tier3_percent = (tier_strategies[2].to_contact /
                        sum(s.to_contact for s in tier_strategies) * 100
                        if sum(s.to_contact for s in tier_strategies) > 0 else 0)
        if tier3_percent > 60:
            risks.append(f"Heavy reliance on cold outreach ({tier3_percent:.0f}%)")

        # Urgent timeline
        if urgency in [UrgencyLevel.EMERGENCY, UrgencyLevel.URGENT]:
            risks.append("Urgent timeline may reduce response rates")

        # Maxed out tiers
        for strategy in tier_strategies:
            if strategy.to_contact == self.max_per_tier[strategy.tier]:
                risks.append(f"Tier {strategy.tier} at maximum capacity")

        return risks

    def _generate_recommendations(self,
                                tier_strategies: list[TierStrategy],
                                confidence_score: float,
                                risk_factors: list[str],
                                urgency: UrgencyLevel) -> list[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Low confidence
        if confidence_score < 70:
            recommendations.append("Consider expanding search radius or criteria")
            recommendations.append("Prepare for manual outreach if needed")

        # Urgent projects
        if urgency in [UrgencyLevel.EMERGENCY, UrgencyLevel.URGENT]:
            recommendations.append("Prioritize phone calls over email for Tier 1")
            recommendations.append("Consider incentive for quick response")

        # Tier-specific recommendations
        if tier_strategies[0].available_count < tier_strategies[0].to_contact:
            recommendations.append("Recruit more internal contractors for future projects")

        if tier_strategies[2].to_contact > 8:
            recommendations.append("Enrich and qualify more Tier 3 contractors proactively")

        # Check-in recommendations
        if urgency == UrgencyLevel.EMERGENCY:
            recommendations.append("Set up hourly monitoring for first 3 hours")

        return recommendations


class ResponseCheckInManager:
    """Monitor campaign responses and trigger escalations"""

    def __init__(self, calculator: ContractorOutreachCalculator):
        self.calculator = calculator
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")

    def check_response_status(self,
                            campaign_id: str,
                            strategy: OutreachStrategy,
                            current_time: datetime) -> dict[str, Any]:
        """
        Check if responses are on track

        Returns:
            - bids_received: Current bid count
            - bids_expected: Expected bids by now
            - on_track: Boolean
            - escalation_needed: Boolean
            - additional_contractors_needed: Dict by tier
        """
        # This would query the database for actual responses
        # Placeholder for now
        bids_received = 0  # Would query from database

        # Find which check-in period we're in
        elapsed_hours = (current_time - datetime.now()).total_seconds() / 3600
        progress_ratio = elapsed_hours / strategy.timeline_hours

        # Expected bids based on linear progression
        bids_expected = math.ceil(strategy.bids_needed * progress_ratio)

        # Determine if escalation needed
        on_track = bids_received >= bids_expected
        escalation_needed = not on_track and bids_received < (bids_expected * 0.75)

        # Calculate additional contractors needed
        additional_needed = {}
        if escalation_needed:
            shortfall = strategy.bids_needed - bids_received
            # Would use calculator to determine which tiers to add
            additional_needed = {
                "tier_2": min(4, shortfall),
                "tier_3": max(0, shortfall - 4)
            }

        return {
            "bids_received": bids_received,
            "bids_expected": bids_expected,
            "on_track": on_track,
            "escalation_needed": escalation_needed,
            "additional_contractors_needed": additional_needed,
            "progress_percentage": round(progress_ratio * 100, 1)
        }


# Example usage and testing
if __name__ == "__main__":
    print("CONTRACTOR OUTREACH TIMING & PROBABILITY ENGINE")
    print("=" * 70)

    calculator = ContractorOutreachCalculator()

    # Test scenarios
    scenarios = [
        {
            "name": "Emergency Plumbing (6 hours)",
            "bids_needed": 4,
            "timeline_hours": 6,
            "tier1_available": 2,
            "tier2_available": 15,
            "tier3_available": 50,
            "project_type": "emergency plumbing"
        },
        {
            "name": "Kitchen Remodel (24 hours)",
            "bids_needed": 4,
            "timeline_hours": 24,
            "tier1_available": 5,
            "tier2_available": 20,
            "tier3_available": 100,
            "project_type": "kitchen remodel"
        },
        {
            "name": "Lawn Care (3 days)",
            "bids_needed": 4,
            "timeline_hours": 72,
            "tier1_available": 3,
            "tier2_available": 10,
            "tier3_available": 80,
            "project_type": "lawn maintenance"
        }
    ]

    for scenario in scenarios:
        print(f"\n{scenario['name']}")
        print("-" * 50)

        # Remove 'name' from scenario dict for the call
        scenario_params = {k: v for k, v in scenario.items() if k != "name"}
        strategy = calculator.calculate_outreach_strategy(**scenario_params)

        print(f"Urgency Level: {strategy.urgency_level.value}")
        print("\nContractor Outreach Plan:")
        print(f"  Tier 1 (Internal): {strategy.tier1_strategy.to_contact} of {strategy.tier1_strategy.available_count} "
              f"(expect {strategy.tier1_strategy.expected_responses:.1f} responses)")
        print(f"  Tier 2 (Prospects): {strategy.tier2_strategy.to_contact} of {strategy.tier2_strategy.available_count} "
              f"(expect {strategy.tier2_strategy.expected_responses:.1f} responses)")
        print(f"  Tier 3 (New/Cold): {strategy.tier3_strategy.to_contact} of {strategy.tier3_strategy.available_count} "
              f"(expect {strategy.tier3_strategy.expected_responses:.1f} responses)")

        print(f"\nTotal: {strategy.total_to_contact} contractors")
        print(f"Expected Responses: {strategy.expected_total_responses:.1f}")
        print(f"Confidence Score: {strategy.confidence_score}%")

        print("\nCheck-in Schedule:")
        for _i, check_time in enumerate(strategy.check_in_times):
            threshold = strategy.escalation_thresholds[check_time]
            hours_from_now = (check_time - datetime.now()).total_seconds() / 3600
            print(f"  {hours_from_now:.1f} hours: Expect {threshold} bids")

        if strategy.risk_factors:
            print("\nRisk Factors:")
            for risk in strategy.risk_factors:
                print(f"  ! {risk}")

        if strategy.recommendations:
            print("\nRecommendations:")
            for rec in strategy.recommendations:
                print(f"  -> {rec}")
