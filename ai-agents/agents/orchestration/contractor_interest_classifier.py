#!/usr/bin/env python3
"""
Contractor Interest Classifier
Identifies interested contractors based on engagement patterns

This agent implements the missing interest classification logic that moves contractors
from 'contacted' status to 'interested' based on positive engagement patterns.
"""

import os
import sys
from datetime import datetime


# Add the root directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv

from database_simple import SupabaseDB


# Load environment variables
load_dotenv(override=True)

class ContractorInterestClassifier:
    """Agent that identifies interested contractors based on engagement data"""

    def __init__(self):
        """Initialize the interest classifier"""
        self.db = SupabaseDB()
        self.interest_criteria = {
            "minimum_positive_responses": 1,
            "high_interest_threshold": 80,  # engagement_score
            "response_rate_threshold": 0.5,  # 50% response rate
            "recent_activity_days": 30,
            "tier_1_promotion_threshold": 2  # positive responses needed for Tier 1
        }

    def classify_interested_contractors(self) -> dict[str, int]:
        """
        Find and classify interested contractors based on engagement patterns

        Interest indicators:
        1. Positive responses to outreach attempts
        2. High engagement scores
        3. Quick response times
        4. Multiple interactions

        Returns dict with classification results
        """
        try:
            print("🔍 Finding contractors with positive engagement...")

            # Get contractors with positive engagement
            result = self.db.client.table("contractor_engagement_summary")\
                .select("*, potential_contractors(id, company_name, lead_status, tier)")\
                .gte("positive_responses", self.interest_criteria["minimum_positive_responses"])\
                .execute()

            engagements = result.data if result.data else []
            print(f"📊 Found {len(engagements)} contractors with positive engagement")

            if not engagements:
                return {
                    "newly_interested": 0,
                    "promoted_to_tier1": 0,
                    "total_evaluated": 0,
                    "message": "No contractors with positive engagement found"
                }

            newly_interested = 0
            promoted_to_tier1 = 0
            already_interested = 0

            for engagement in engagements:
                contractor_id = engagement["contractor_lead_id"]
                contractor_info = engagement.get("potential_contractors")

                if not contractor_info:
                    print(f"⚠️ No contractor info found for engagement {contractor_id}")
                    continue

                company_name = contractor_info.get("company_name", "Unknown")
                current_status = contractor_info.get("lead_status", "unknown")
                current_tier = contractor_info.get("tier", 3)

                # Evaluate interest level
                interest_assessment = self._evaluate_interest(engagement)

                print(f"📋 Evaluating {company_name}")
                print(f"   Current: {current_status}, Tier {current_tier}")
                print(f"   Interest Level: {interest_assessment['level']}")
                print(f"   Score: {interest_assessment['score']}")

                # Skip if already interested
                if current_status == "interested":
                    already_interested += 1
                    print("   📌 Already marked as interested")
                    continue

                # Determine if contractor should be marked as interested
                should_be_interested = interest_assessment["level"] in ["high", "very_high"]
                should_promote_tier = interest_assessment["score"] >= self.interest_criteria["tier_1_promotion_threshold"]

                if should_be_interested:
                    # Update to interested status
                    new_tier = 1 if should_promote_tier else max(1, current_tier - 1)  # Promote tier

                    update_data = {
                        "lead_status": "interested",
                        "tier": new_tier,
                        "last_interest_shown_at": datetime.now().isoformat(),
                        "interest_score": interest_assessment["score"],
                        "interest_reason": interest_assessment["reason"]
                    }

                    # Execute update
                    self.db.client.table("potential_contractors")\
                        .update(update_data)\
                        .eq("id", contractor_id)\
                        .execute()

                    newly_interested += 1
                    if new_tier == 1:
                        promoted_to_tier1 += 1

                    print(f"   ✅ INTERESTED - Promoted from Tier {current_tier} to Tier {new_tier}")
                else:
                    print(f"   📋 Not quite interested yet - {interest_assessment['reason']}")

            results = {
                "newly_interested": newly_interested,
                "promoted_to_tier1": promoted_to_tier1,
                "already_interested": already_interested,
                "total_evaluated": len(engagements)
            }

            print("\n🎯 Interest Classification Results:")
            print(f"   ✅ Newly Interested: {newly_interested}")
            print(f"   ⬆️ Promoted to Tier 1: {promoted_to_tier1}")
            print(f"   📌 Already Interested: {already_interested}")
            print(f"   📊 Total Evaluated: {len(engagements)}")

            return results

        except Exception as e:
            error_msg = f"Error classifying interested contractors: {e}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}

    def _evaluate_interest(self, engagement: dict) -> dict:
        """
        Evaluate interest level based on engagement patterns

        Scoring factors:
        - Positive responses (weight: 3x)
        - Response rate (weight: 2x)
        - Engagement score (weight: 1x)
        - Recency of responses (weight: 1x)

        Interest levels:
        - very_high: 8+ points
        - high: 5-7 points
        - medium: 3-4 points
        - low: 1-2 points
        """
        score = 0
        factors = []

        # Positive responses (most important factor)
        positive_responses = engagement.get("positive_responses", 0)
        total_responses = engagement.get("total_responses", 0)

        if positive_responses >= 3:
            score += 4
            factors.append(f"{positive_responses} positive responses")
        elif positive_responses >= 2:
            score += 3
            factors.append(f"{positive_responses} positive responses")
        elif positive_responses >= 1:
            score += 2
            factors.append(f"{positive_responses} positive response")

        # Response rate
        if total_responses > 0:
            response_rate = positive_responses / total_responses
            if response_rate >= 0.8:
                score += 2
                factors.append(f"{response_rate:.0%} response rate")
            elif response_rate >= 0.5:
                score += 1
                factors.append(f"{response_rate:.0%} response rate")

        # Engagement score (from summary)
        engagement_score = engagement.get("engagement_score", 0)
        if engagement_score >= 90:
            score += 2
            factors.append("very high engagement")
        elif engagement_score >= 70:
            score += 1
            factors.append("high engagement")

        # Recency factor
        last_responded = engagement.get("last_responded_at")
        if last_responded:
            try:
                last_response = datetime.fromisoformat(last_responded.replace("Z", "+00:00"))
                days_since = (datetime.now() - last_response.replace(tzinfo=None)).days

                if days_since <= 7:
                    score += 1
                    factors.append("recent activity")
                elif days_since <= 14:
                    factors.append("activity within 2 weeks")
                else:
                    factors.append(f"last activity {days_since} days ago")
            except:
                pass

        # Quality indicators
        total_outreach = engagement.get("total_outreach_attempts", 0)
        if total_outreach > 0 and total_responses > 0:
            overall_response_rate = total_responses / total_outreach
            if overall_response_rate >= 0.3:  # 30% overall response rate is excellent
                score += 1
                factors.append("excellent overall response rate")

        # Determine interest level
        if score >= 8:
            level = "very_high"
        elif score >= 5:
            level = "high"
        elif score >= 3:
            level = "medium"
        else:
            level = "low"

        return {
            "level": level,
            "score": score,
            "reason": f"{level} interest: {', '.join(factors[:3])}"
        }

    def get_interest_stats(self) -> dict[str, any]:
        """Get current interest classification statistics"""
        try:
            stats = {}

            # Count by status
            for status in ["contacted", "interested", "qualified"]:
                result = self.db.client.table("potential_contractors")\
                    .select("id", count="exact")\
                    .eq("lead_status", status)\
                    .execute()

                stats[f"{status}_count"] = result.count if result.count else 0

            # Count by tier
            for tier in [1, 2, 3]:
                result = self.db.client.table("potential_contractors")\
                    .select("id", count="exact")\
                    .eq("tier", tier)\
                    .execute()

                stats[f"tier_{tier}_count"] = result.count if result.count else 0

            # Get engagement summary stats
            result = self.db.client.table("contractor_engagement_summary")\
                .select("positive_responses", count="exact")\
                .gte("positive_responses", 1)\
                .execute()

            stats["contractors_with_positive_responses"] = result.count if result.count else 0

            # Calculate rates
            total_contacted = stats.get("contacted_count", 0) + stats.get("interested_count", 0)
            if total_contacted > 0:
                stats["interest_rate"] = round((stats.get("interested_count", 0) / total_contacted * 100), 1)
            else:
                stats["interest_rate"] = 0

            return stats

        except Exception as e:
            return {"error": str(e)}

    def classify_single_contractor(self, contractor_id: str) -> dict[str, any]:
        """
        Classify interest for a single contractor

        Returns classification result for the specific contractor
        """
        try:
            # Get engagement data for this contractor
            result = self.db.client.table("contractor_engagement_summary")\
                .select("*, potential_contractors(id, company_name, lead_status, tier)")\
                .eq("contractor_lead_id", contractor_id)\
                .execute()

            if not result.data:
                return {"success": False, "error": f"No engagement data found for contractor {contractor_id}"}

            engagement = result.data[0]
            contractor_info = engagement.get("potential_contractors")

            if not contractor_info:
                return {"success": False, "error": f"Contractor {contractor_id} not found"}

            # Evaluate interest
            interest_assessment = self._evaluate_interest(engagement)

            current_status = contractor_info.get("lead_status")
            should_be_interested = interest_assessment["level"] in ["high", "very_high"]

            result_data = {
                "success": True,
                "contractor_id": contractor_id,
                "company_name": contractor_info.get("company_name"),
                "current_status": current_status,
                "interest_level": interest_assessment["level"],
                "interest_score": interest_assessment["score"],
                "should_be_interested": should_be_interested,
                "reason": interest_assessment["reason"]
            }

            # Update if needed
            if should_be_interested and current_status != "interested":
                new_tier = min(1, contractor_info.get("tier", 3))

                update_data = {
                    "lead_status": "interested",
                    "tier": new_tier,
                    "last_interest_shown_at": datetime.now().isoformat(),
                    "interest_score": interest_assessment["score"],
                    "interest_reason": interest_assessment["reason"]
                }

                self.db.supabase.table("potential_contractors")\
                    .update(update_data)\
                    .eq("id", contractor_id)\
                    .execute()

                result_data["updated"] = True
                result_data["new_status"] = "interested"
                result_data["new_tier"] = new_tier
            else:
                result_data["updated"] = False

            return result_data

        except Exception as e:
            return {"success": False, "error": str(e)}


# Test function
async def test_interest_classifier():
    """Test the contractor interest classifier"""
    print("🧪 TESTING CONTRACTOR INTEREST CLASSIFIER")
    print("=" * 60)

    classifier = ContractorInterestClassifier()

    # Get current stats
    print("📊 Current Interest Statistics:")
    stats = classifier.get_interest_stats()
    for key, value in stats.items():
        if "error" not in key:
            print(f"   {key}: {value}")

    # Run interest classification
    print("\n🔍 Running interest classification...")
    results = classifier.classify_interested_contractors()

    print("\n✅ Interest classification completed!")
    return results


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_interest_classifier())
