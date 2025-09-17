"""
Contractor Scoring Algorithm
Unified scoring system for all tiers of contractors
"""
from typing import Any


class ContractorScorer:
    """Unified contractor scoring and ranking system"""

    def score_contractors(self, contractors: list[dict[str, Any]], bid_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Score and rank contractors from all tiers

        Args:
            contractors: List of contractors from all tiers
            bid_data: Bid card data for scoring context

        Returns:
            Sorted list of contractors by score (highest first)
        """
        try:
            print(f"[Scorer] Scoring {len(contractors)} contractors")

            scored_contractors = []

            for contractor in contractors:
                # Calculate comprehensive score
                total_score = self._calculate_total_score(contractor, bid_data)

                # Add final score to contractor data
                contractor["final_score"] = total_score
                contractor["score_breakdown"] = self._get_score_breakdown(contractor, bid_data)

                scored_contractors.append(contractor)

            # Sort by final score (highest first)
            scored_contractors.sort(key=lambda x: x["final_score"], reverse=True)

            print(f"[Scorer] Top contractor: {scored_contractors[0]['company_name']} (score: {scored_contractors[0]['final_score']:.1f})")

            return scored_contractors

        except Exception as e:
            print(f"[Scorer ERROR] Failed to score contractors: {e}")
            return contractors

    def _calculate_total_score(self, contractor: dict[str, Any], bid_data: dict[str, Any]) -> float:
        """Calculate comprehensive contractor score"""
        total_score = 0.0

        # Base score from tier and existing match score
        tier = contractor.get("discovery_tier", 3)
        match_score = contractor.get("match_score", 0)

        # Tier preference (Tier 1 is preferred)
        if tier == 1:
            total_score += 100  # Internal contractors get highest base
            total_score += match_score * 0.5  # Tier 1 match score (0-100)
        elif tier == 2:
            total_score += 80   # Re-engagement gets good base
            total_score += match_score * 0.4  # Tier 2 match score (0-100)
        elif tier == 3:
            total_score += 50   # External gets lowest base
            total_score += match_score * 0.3  # Tier 3 match score (0-100)

        # Quality indicators
        total_score += self._score_quality_indicators(contractor)

        # Project fit
        total_score += self._score_project_fit(contractor, bid_data)

        # Availability and responsiveness
        total_score += self._score_availability(contractor)

        # Verification and trust
        total_score += self._score_verification(contractor)

        return min(300.0, max(0.0, total_score))  # Cap at 300 points

    def _score_quality_indicators(self, contractor: dict[str, Any]) -> float:
        """Score based on quality indicators"""
        score = 0.0

        # Rating score (0-50 points)
        rating = float(contractor.get("rating", 0))
        if rating >= 4.8:
            score += 50
        elif rating >= 4.5:
            score += 40
        elif rating >= 4.0:
            score += 30
        elif rating >= 3.5:
            score += 20
        elif rating >= 3.0:
            score += 10

        # Experience score (0-30 points)
        total_projects = contractor.get("total_projects", 0)
        if total_projects >= 200:
            score += 30
        elif total_projects >= 100:
            score += 25
        elif total_projects >= 50:
            score += 20
        elif total_projects >= 20:
            score += 15
        elif total_projects >= 10:
            score += 10
        elif total_projects >= 5:
            score += 5

        return score

    def _score_project_fit(self, contractor: dict[str, Any], bid_data: dict[str, Any]) -> float:
        """Score based on project fit"""
        score = 0.0

        # Specialty match (0-25 points)
        project_type = bid_data.get("project_type", "").lower()
        contractor_specialties = contractor.get("specialties", [])

        specialty_match = False
        for specialty in contractor_specialties:
            if project_type in str(specialty).lower():
                score += 25
                specialty_match = True
                break

        if not specialty_match and "general" in str(contractor_specialties).lower():
            score += 10  # General contractors get partial credit

        # Budget compatibility (0-20 points)
        budget_max = bid_data.get("budget_max", 0)
        min_size = contractor.get("min_project_size", 0)
        max_size = contractor.get("max_project_size", 999999)

        if budget_max > 0:
            if min_size <= budget_max <= max_size:
                score += 20  # Perfect fit
            elif budget_max < min_size:
                # Project too small - penalize
                ratio = budget_max / min_size if min_size > 0 else 0
                score += max(0, 10 * ratio)
            elif budget_max > max_size:
                # Project larger than usual - slight penalty
                score += 15

        # Location proximity (0-15 points)
        # For now, assume all contractors are local if they match zip code
        project_zip = self._extract_zip_from_bid(bid_data)
        contractor_zips = contractor.get("zip_codes", [])

        if project_zip and any(project_zip in str(czip) for czip in contractor_zips):
            score += 15

        return score

    def _score_availability(self, contractor: dict[str, Any]) -> float:
        """Score based on availability"""
        score = 0.0

        availability = contractor.get("availability", "").lower()

        if availability == "available":
            score += 20
        elif availability == "busy":
            score += 5  # Might be available soon
        # 'unavailable' gets 0 points

        # Onboarded contractors are more responsive
        if contractor.get("onboarded"):
            score += 10

        return score

    def _score_verification(self, contractor: dict[str, Any]) -> float:
        """Score based on verification and trust indicators"""
        score = 0.0

        # License verification
        if contractor.get("license_number"):
            score += 15

        # Insurance verification
        if contractor.get("insurance_verified"):
            score += 15

        # Tier-specific trust indicators
        tier = contractor.get("discovery_tier", 3)

        if tier == 1:
            score += 10  # Internal contractors are pre-verified
        elif tier == 2:
            # Previous interaction history
            reengagement_data = contractor.get("reengagement_data", {})
            if reengagement_data.get("last_response") == "interested":
                score += 8
            elif reengagement_data.get("last_response") == "pending":
                score += 4
        # Tier 3 (external) gets no bonus until verified

        return score

    def _get_score_breakdown(self, contractor: dict[str, Any], bid_data: dict[str, Any]) -> dict[str, float]:
        """Get detailed score breakdown for transparency"""
        breakdown = {
            "tier_base": 0.0,
            "match_score": 0.0,
            "quality": self._score_quality_indicators(contractor),
            "project_fit": self._score_project_fit(contractor, bid_data),
            "availability": self._score_availability(contractor),
            "verification": self._score_verification(contractor)
        }

        # Calculate tier base and match score
        tier = contractor.get("discovery_tier", 3)
        match_score = contractor.get("match_score", 0)

        if tier == 1:
            breakdown["tier_base"] = 100
            breakdown["match_score"] = match_score * 0.5
        elif tier == 2:
            breakdown["tier_base"] = 80
            breakdown["match_score"] = match_score * 0.4
        elif tier == 3:
            breakdown["tier_base"] = 50
            breakdown["match_score"] = match_score * 0.3

        return breakdown

    def _extract_zip_from_bid(self, bid_data: dict[str, Any]) -> str:
        """Extract zip code from bid data"""
        location = bid_data.get("location", {})
        full_location = location.get("full_location", "")

        import re
        zip_match = re.search(r"\b(\d{5})\b", full_location)
        return zip_match.group(1) if zip_match else ""
