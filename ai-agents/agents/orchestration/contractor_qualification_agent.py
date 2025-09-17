#!/usr/bin/env python3
"""
Contractor Qualification Agent
Automatically qualifies or disqualifies contractors based on enriched data

This agent implements the missing qualification logic that moves contractors
from 'enriched' status to 'qualified' or 'disqualified' based on specific criteria.
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

class ContractorQualificationAgent:
    """Agent that automatically qualifies contractors based on enrichment data"""

    def __init__(self):
        """Initialize the qualification agent"""
        self.db = SupabaseDB()
        self.qualification_criteria = {
            "minimum_lead_score": 40,
            "qualified_threshold": 70,
            "license_required": False,  # Not all contractors need licenses
            "insurance_preferred": True,
            "minimum_rating": 3.0,
            "minimum_reviews": 1
        }

    def qualify_all_enriched_contractors(self) -> dict[str, int]:
        """
        Qualify all contractors with 'enriched' status

        Returns dict with counts of qualified, disqualified, and total processed
        """
        try:
            print("🔍 Finding enriched contractors to qualify...")

            # Get all enriched contractors
            result = self.db.client.table("potential_contractors")\
                .select("*")\
                .eq("lead_status", "enriched")\
                .execute()

            contractors = result.data if result.data else []
            print(f"📊 Found {len(contractors)} enriched contractors to evaluate")

            if not contractors:
                return {
                    "qualified": 0,
                    "disqualified": 0,
                    "total_processed": 0,
                    "message": "No enriched contractors found"
                }

            qualified_count = 0
            disqualified_count = 0
            unchanged_count = 0

            for contractor in contractors:
                qualification = self._evaluate_contractor(contractor)

                print(f"📋 Evaluating {contractor.get('company_name', 'Unknown')}")
                print(f"   Score: {qualification['score']}, Status: {qualification['status']}")

                # Only update if status should change
                if qualification["status"] != "enriched":
                    update_data = {
                        "lead_status": qualification["status"],
                        "qualification_score": qualification["score"],
                        "qualified_at": datetime.now().isoformat() if qualification["status"] == "qualified" else None,
                        "disqualification_reason": qualification.get("reason") if qualification["status"] == "disqualified" else None
                    }

                    # Update contractor status
                    self.db.client.table("potential_contractors").update(update_data)\
                        .eq("id", contractor["id"]).execute()

                    if qualification["status"] == "qualified":
                        qualified_count += 1
                        print(f"   ✅ QUALIFIED - {contractor.get('company_name')}")
                    elif qualification["status"] == "disqualified":
                        disqualified_count += 1
                        print(f"   ❌ DISQUALIFIED - {qualification.get('reason')}")
                else:
                    unchanged_count += 1
                    print(f"   📋 ENRICHED - Needs improvement: {qualification.get('reason', 'Score too low')}")

            results = {
                "qualified": qualified_count,
                "disqualified": disqualified_count,
                "unchanged": unchanged_count,
                "total_processed": len(contractors)
            }

            print("\n🎯 Qualification Results:")
            print(f"   ✅ Qualified: {qualified_count}")
            print(f"   ❌ Disqualified: {disqualified_count}")
            print(f"   📋 Still Enriched: {unchanged_count}")
            print(f"   📊 Total Processed: {len(contractors)}")

            return results

        except Exception as e:
            error_msg = f"Error qualifying contractors: {e}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}

    def _evaluate_contractor(self, contractor: dict) -> dict:
        """
        Evaluate a single contractor for qualification

        Scoring system (out of 100):
        - Lead score: 40 points max (existing quality score)
        - License verification: 25 points
        - Insurance verification: 15 points
        - Rating and reviews: 20 points

        Thresholds:
        - 70+ points: QUALIFIED
        - 40-69 points: ENRICHED (stay enriched, needs improvement)
        - <40 points: DISQUALIFIED
        """
        score = 0
        reasons = []

        # 1. Lead score (40 points max)
        lead_score = contractor.get("lead_score", 0)
        if lead_score:
            score += min(lead_score * 0.4, 40)
        else:
            reasons.append("No lead score available")

        # 2. License verification (25 points)
        license_verified = contractor.get("license_verified")
        if license_verified:
            score += 25
        elif license_verified is False:
            reasons.append("License not verified")
        else:
            # Unknown license status - neutral (no points, no penalty)
            pass

        # 3. Insurance verification (15 points)
        insurance_verified = contractor.get("insurance_verified")
        if insurance_verified:
            score += 15
        elif insurance_verified is False:
            reasons.append("Insurance not verified")
        else:
            # Unknown insurance status - neutral
            pass

        # 4. Rating and reviews (20 points max)
        rating = contractor.get("rating", 0)
        review_count = contractor.get("review_count", 0)

        if rating and review_count:
            if rating >= 4.5 and review_count >= 10:
                score += 20
            elif rating >= 4.0 and review_count >= 5:
                score += 15
            elif rating >= 3.5 and review_count >= 1:
                score += 10
            elif rating >= 3.0:
                score += 5
            else:
                reasons.append(f"Low rating ({rating}) or insufficient reviews ({review_count})")
        else:
            reasons.append("No rating or review data")

        # Additional business quality factors
        contractor_size = contractor.get("contractor_size", "")
        if contractor_size in ["LOCAL_BUSINESS_TEAMS", "NATIONAL_COMPANY"]:
            score += 5  # Bonus for established businesses

        specialties = contractor.get("specialties", [])
        if specialties and len(specialties) > 1:
            score += 3  # Bonus for multiple service types

        # Determine qualification status
        if score >= self.qualification_criteria["qualified_threshold"]:
            return {
                "status": "qualified",
                "score": round(score, 1),
                "reason": None
            }
        elif score >= self.qualification_criteria["minimum_lead_score"]:
            return {
                "status": "enriched",  # Stay enriched, needs improvement
                "score": round(score, 1),
                "reason": f"Score {round(score, 1)} needs improvement: {', '.join(reasons[:3])}"
            }
        else:
            return {
                "status": "disqualified",
                "score": round(score, 1),
                "reason": f"Score {round(score, 1)} too low: {', '.join(reasons[:3])}"
            }

    def qualify_single_contractor(self, contractor_id: str) -> dict[str, any]:
        """
        Qualify a single contractor by ID

        Returns qualification result for the specific contractor
        """
        try:
            # Get the contractor data
            result = self.db.client.table("potential_contractors")\
                .select("*")\
                .eq("id", contractor_id)\
                .execute()

            if not result.data:
                return {"success": False, "error": f"Contractor {contractor_id} not found"}

            contractor = result.data[0]

            # Evaluate the contractor
            qualification = self._evaluate_contractor(contractor)

            # Update if status should change
            if qualification["status"] != contractor.get("lead_status"):
                update_data = {
                    "lead_status": qualification["status"],
                    "qualification_score": qualification["score"],
                    "qualified_at": datetime.now().isoformat() if qualification["status"] == "qualified" else None,
                    "disqualification_reason": qualification.get("reason") if qualification["status"] == "disqualified" else None
                }

                self.db.client.table("potential_contractors").update(update_data)\
                    .eq("id", contractor_id).execute()

            return {
                "success": True,
                "contractor_id": contractor_id,
                "company_name": contractor.get("company_name"),
                "old_status": contractor.get("lead_status"),
                "new_status": qualification["status"],
                "score": qualification["score"],
                "reason": qualification.get("reason")
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_qualification_stats(self) -> dict[str, int]:
        """Get current qualification statistics"""
        try:
            # Count contractors by status
            stats = {}

            for status in ["new", "enriched", "qualified", "disqualified", "contacted", "interested"]:
                result = self.db.client.table("potential_contractors")\
                    .select("id", count="exact")\
                    .eq("lead_status", status)\
                    .execute()

                stats[status] = result.count if result.count else 0

            # Calculate totals
            stats["total"] = sum(stats.values())
            stats["qualified_rate"] = round((stats["qualified"] / stats["total"] * 100), 1) if stats["total"] > 0 else 0

            return stats

        except Exception as e:
            return {"error": str(e)}


# Test function
async def test_qualification_agent():
    """Test the contractor qualification agent"""
    print("🧪 TESTING CONTRACTOR QUALIFICATION AGENT")
    print("=" * 60)

    agent = ContractorQualificationAgent()

    # Get current stats
    print("📊 Current Qualification Statistics:")
    stats = agent.get_qualification_stats()
    for status, count in stats.items():
        if status != "error":
            print(f"   {status}: {count}")

    # Run qualification on all enriched contractors
    print("\n🔍 Running qualification process...")
    results = agent.qualify_all_enriched_contractors()

    print("\n✅ Qualification completed!")
    return results


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_qualification_agent())
