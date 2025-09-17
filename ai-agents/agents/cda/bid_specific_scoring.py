"""
Bid-Card-Specific Match Scoring System
Calculates contractor match scores based on specific project requirements
"""
import json
from dataclasses import dataclass
from typing import Any


@dataclass
class BidCardPreferences:
    """Extracted preferences from bid card"""
    project_type: str
    budget_range: tuple  # (min, max)
    urgency_level: str  # emergency, week, month, flexible
    complexity: str  # simple, moderate, complex
    preferred_contractor_size: str  # mom_and_pop, medium, large, any
    quality_vs_price: str  # quality_first, balanced, budget_conscious
    special_requirements: list[str]  # licensed, insured, specific_experience
    location_preference: str  # local_only, within_25_miles, any_distance


class BidSpecificScoringEngine:
    """Calculate contractor match scores based on specific bid card requirements"""

    def __init__(self):
        # Define contractor size indicators
        self.size_indicators = {
            "mom_and_pop": {
                "max_reviews": 50,
                "keywords": ["family", "local", "owner-operated", "small business"],
                "max_locations": 1
            },
            "medium": {
                "review_range": (50, 200),
                "keywords": ["professional", "established", "team"],
                "location_range": (1, 3)
            },
            "large": {
                "min_reviews": 200,
                "keywords": ["corporation", "franchise", "national", "chain"],
                "min_locations": 3
            }
        }

    def calculate_bid_specific_score(self,
                                   contractor: dict[str, Any],
                                   bid_preferences: BidCardPreferences,
                                   bid_location: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate match score for a contractor based on specific bid card requirements

        Returns:
            Dict with score breakdown and final match_score
        """
        score_breakdown = {
            "base_score": 50.0,
            "size_match": 0.0,
            "budget_match": 0.0,
            "urgency_match": 0.0,
            "quality_match": 0.0,
            "location_match": 0.0,
            "specialization_match": 0.0,
            "requirements_match": 0.0,
            "penalties": 0.0
        }

        # 1. Contractor Size Match (Critical for mom & pop preference)
        size_score = self._calculate_size_match(contractor, bid_preferences.preferred_contractor_size)
        score_breakdown["size_match"] = size_score

        # 2. Budget Alignment
        budget_score = self._calculate_budget_match(contractor, bid_preferences.budget_range)
        score_breakdown["budget_match"] = budget_score

        # 3. Urgency Response Capability
        urgency_score = self._calculate_urgency_match(contractor, bid_preferences.urgency_level)
        score_breakdown["urgency_match"] = urgency_score

        # 4. Quality vs Price Preference
        quality_score = self._calculate_quality_match(contractor, bid_preferences.quality_vs_price)
        score_breakdown["quality_match"] = quality_score

        # 5. Location Proximity
        location_score = self._calculate_location_match(contractor, bid_location, bid_preferences.location_preference)
        score_breakdown["location_match"] = location_score

        # 6. Project Type Specialization
        specialization_score = self._calculate_specialization_match(contractor, bid_preferences.project_type)
        score_breakdown["specialization_match"] = specialization_score

        # 7. Special Requirements (licensed, insured, etc.)
        requirements_score = self._check_special_requirements(contractor, bid_preferences.special_requirements)
        score_breakdown["requirements_match"] = requirements_score

        # 8. Apply Penalties
        penalties = self._calculate_penalties(contractor, bid_preferences)
        score_breakdown["penalties"] = penalties

        # Calculate final score
        total_score = sum(score_breakdown.values())
        final_score = max(0, min(100, total_score))

        return {
            "match_score": final_score,
            "score_breakdown": score_breakdown,
            "contractor_size_detected": self._detect_contractor_size(contractor),
            "matches_preferences": final_score >= 70,
            "recommendation": self._get_recommendation(final_score, score_breakdown)
        }

    def _calculate_size_match(self, contractor: dict[str, Any], preferred_size: str) -> float:
        """Calculate how well contractor size matches preference"""
        if preferred_size == "any":
            return 0.0  # No bonus or penalty

        detected_size = self._detect_contractor_size(contractor)

        # Perfect match = 20 points
        if detected_size == preferred_size:
            return 20.0

        # Partial matches
        if preferred_size == "mom_and_pop":
            if detected_size == "medium":
                return -10.0  # Penalty for being too big
            elif detected_size == "large":
                return -20.0  # Big penalty for corporate when wanting mom & pop

        elif preferred_size == "large":
            if detected_size == "mom_and_pop":
                return -15.0  # Penalty for being too small
            elif detected_size == "medium":
                return -5.0   # Small penalty

        return 0.0

    def _detect_contractor_size(self, contractor: dict[str, Any]) -> str:
        """Detect contractor size based on various indicators"""
        review_count = contractor.get("google_review_count", 0)
        company_name = contractor.get("company_name", "").lower()
        website = contractor.get("website", "").lower()

        # Check for mom & pop indicators
        if review_count <= self.size_indicators["mom_and_pop"]["max_reviews"]:
            mom_pop_keywords = self.size_indicators["mom_and_pop"]["keywords"]
            if any(keyword in company_name or keyword in website for keyword in mom_pop_keywords):
                return "mom_and_pop"
            if review_count < 20:  # Very few reviews usually means small business
                return "mom_and_pop"

        # Check for large company indicators
        if review_count >= self.size_indicators["large"]["min_reviews"]:
            return "large"

        large_keywords = self.size_indicators["large"]["keywords"]
        if any(keyword in company_name for keyword in large_keywords):
            return "large"

        # Default to medium
        return "medium"

    def _calculate_budget_match(self, contractor: dict[str, Any], budget_range: tuple) -> float:
        """Calculate budget alignment based on contractor indicators"""
        # Use review count and rating as proxy for pricing
        # More reviews + high rating often = higher prices
        rating = contractor.get("google_rating", 0)
        review_count = contractor.get("google_review_count", 0)

        # Estimate price tier
        if rating >= 4.8 and review_count > 100:
            price_tier = "premium"
        elif rating >= 4.5 and review_count > 50:
            price_tier = "mid_high"
        elif rating >= 4.0:
            price_tier = "mid"
        else:
            price_tier = "budget"

        budget_min, budget_max = budget_range
        budget_midpoint = (budget_min + budget_max) / 2

        # Score based on budget fit
        if budget_midpoint < 5000:  # Small budget
            if price_tier == "budget":
                return 10.0
            elif price_tier == "mid":
                return 5.0
            else:
                return -5.0
        elif budget_midpoint < 20000:  # Medium budget
            if price_tier in ["mid", "mid_high"]:
                return 10.0
            else:
                return 5.0
        else:  # Large budget
            if price_tier in ["premium", "mid_high"]:
                return 10.0
            else:
                return 0.0

    def _calculate_urgency_match(self, contractor: dict[str, Any], urgency: str) -> float:
        """Calculate contractor's ability to handle urgency"""
        # Contractors with websites and good ratings can usually respond faster
        has_website = bool(contractor.get("website"))
        has_phone = bool(contractor.get("phone"))
        rating = contractor.get("google_rating", 0)

        if urgency == "emergency":
            # Need responsive contractors
            score = 0.0
            if has_phone:
                score += 5.0
            if has_website:
                score += 3.0
            if rating >= 4.5:  # Good contractors are usually more responsive
                score += 2.0
            return score

        elif urgency == "week":
            # Standard urgency
            if has_phone or has_website:
                return 5.0
            return 0.0

        else:  # month or flexible
            return 0.0  # No urgency bonus needed

    def _calculate_quality_match(self, contractor: dict[str, Any], quality_preference: str) -> float:
        """Match contractor quality indicators with preference"""
        rating = contractor.get("google_rating", 0)
        review_count = contractor.get("google_review_count", 0)

        if quality_preference == "quality_first":
            # Prioritize high ratings
            if rating >= 4.8 and review_count >= 20:
                return 15.0
            elif rating >= 4.5:
                return 10.0
            elif rating >= 4.0:
                return 5.0
            else:
                return -10.0  # Penalty for lower quality

        elif quality_preference == "budget_conscious":
            # Middle ratings often mean better prices
            if 3.5 <= rating <= 4.5:
                return 10.0
            elif rating > 4.5:
                return 5.0  # Might be expensive
            else:
                return 0.0

        else:  # balanced
            if rating >= 4.0:
                return 8.0
            elif rating >= 3.5:
                return 4.0
            else:
                return 0.0

    def _calculate_location_match(self, contractor: dict[str, Any], bid_location: dict[str, Any], preference: str) -> float:
        """Calculate location proximity score"""
        contractor_zip = contractor.get("zip_code", "")
        bid_zip = bid_location.get("zip_code", "")

        # Simple zip code matching for now
        if contractor_zip and bid_zip:
            if contractor_zip == bid_zip:
                return 10.0  # Same zip code
            elif contractor_zip[:3] == bid_zip[:3]:
                return 7.0   # Same area code
            else:
                return 3.0   # Different area

        return 0.0

    def _calculate_specialization_match(self, contractor: dict[str, Any], project_type: str) -> float:
        """Check if contractor specializes in the project type"""
        company_name = contractor.get("company_name", "").lower()
        specialties = contractor.get("specialties", [])
        google_types = contractor.get("google_types", [])

        # Map project types to keywords
        project_keywords = {
            "kitchen": ["kitchen", "cabinet", "remodel"],
            "bathroom": ["bathroom", "bath", "plumbing"],
            "roofing": ["roof", "roofing", "shingle"],
            "lawn care": ["lawn", "landscape", "turf", "grass"],
            "artificial turf": ["artificial", "synthetic", "turf"],
            "plumbing": ["plumb", "pipe", "drain"],
            "electrical": ["electric", "wire", "volt"]
        }

        keywords = project_keywords.get(project_type.lower(), [project_type.lower()])

        # Check for specialization
        score = 0.0
        for keyword in keywords:
            if keyword in company_name:
                score = max(score, 10.0)
            if any(keyword in str(spec).lower() for spec in specialties):
                score = max(score, 8.0)
            if any(keyword in str(gtype).lower() for gtype in google_types):
                score = max(score, 6.0)

        return score

    def _check_special_requirements(self, contractor: dict[str, Any], requirements: list[str]) -> float:
        """Check if contractor meets special requirements"""
        score = 0.0

        for requirement in requirements:
            if (requirement == "licensed" and contractor.get("license_number")) or (requirement == "insured" and contractor.get("insurance_verified")) or (requirement == "bonded" and contractor.get("bonded")):
                score += 5.0

        return score

    def _calculate_penalties(self, contractor: dict[str, Any], preferences: BidCardPreferences) -> float:
        """Apply penalties for mismatches"""
        penalties = 0.0

        # No contact info penalty
        if not contractor.get("phone") and not contractor.get("email"):
            penalties -= 10.0

        # Poor rating penalty
        if contractor.get("google_rating", 0) < 3.0:
            penalties -= 15.0

        # No reviews penalty (might be fake)
        if contractor.get("google_review_count", 0) == 0:
            penalties -= 5.0

        return penalties

    def _get_recommendation(self, score: float, breakdown: dict[str, float]) -> str:
        """Generate recommendation based on score analysis"""
        if score >= 85:
            return "Excellent match - prioritize for outreach"
        elif score >= 70:
            return "Good match - include in outreach"
        elif score >= 55:
            return "Fair match - consider as backup"
        else:
            # Explain why it's a poor match
            if breakdown["size_match"] < -10:
                return "Poor match - wrong contractor size for project"
            elif breakdown["quality_match"] < 0:
                return "Poor match - quality doesn't meet requirements"
            else:
                return "Poor match - doesn't meet project criteria"


# Example usage
if __name__ == "__main__":
    # Example bid card preferences
    preferences = BidCardPreferences(
        project_type="kitchen remodel",
        budget_range=(5000, 15000),
        urgency_level="week",
        complexity="moderate",
        preferred_contractor_size="mom_and_pop",  # Customer wants small local business
        quality_vs_price="balanced",
        special_requirements=["licensed", "insured"],
        location_preference="local_only"
    )

    # Example contractor (mom & pop)
    contractor = {
        "company_name": "Family Kitchen Remodeling",
        "google_rating": 4.6,
        "google_review_count": 23,  # Low review count = likely small business
        "phone": "(555) 123-4567",
        "website": "familykitchenremodel.com",
        "zip_code": "33442",
        "license_number": "FL123456",
        "insurance_verified": True
    }

    # Example bid location
    bid_location = {
        "zip_code": "33442",
        "city": "Coconut Creek",
        "state": "FL"
    }

    # Calculate score
    engine = BidSpecificScoringEngine()
    result = engine.calculate_bid_specific_score(contractor, preferences, bid_location)

    print("Bid-Specific Match Score:", json.dumps(result, indent=2))
