#!/usr/bin/env python3
"""
Smart Contractor Selection Algorithm
Searches for more contractors and selects the best based on ratings and review count
"""
import logging
from dataclasses import dataclass
from typing import Any, Optional


logger = logging.getLogger(__name__)


@dataclass
class ContractorScore:
    """Score calculation for contractor ranking"""
    contractor_id: str
    company_name: str
    rating_score: float  # 0-50 points
    review_score: float  # 0-30 points
    proximity_score: float  # 0-20 points
    total_score: float  # 0-100 points
    google_rating: float
    google_review_count: int
    distance_miles: float


class SmartContractorSelector:
    """
    Intelligent contractor selection that:
    1. Searches for more contractors (10-15)
    2. Scores them based on rating, reviews, and proximity
    3. Selects the best fitting contractors
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.min_rating = 3.5  # Minimum acceptable rating
        self.min_reviews = 5   # Minimum review count for credibility

    def select_best_contractors(
        self,
        all_contractors: list[dict[str, Any]],
        contractors_needed: int = 3,
        project_type: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Select the best contractors from a larger pool

        Args:
            all_contractors: List of all discovered contractors (10-15)
            contractors_needed: How many contractors to select (default 3)
            project_type: Type of project for relevance scoring

        Returns:
            Dictionary with selected contractors and scoring details
        """
        try:
            logger.info(f"Selecting best {contractors_needed} contractors from pool of {len(all_contractors)}")

            # Step 1: Filter out low-quality contractors
            viable_contractors = self._filter_viable_contractors(all_contractors)
            logger.info(f"Filtered to {len(viable_contractors)} viable contractors")

            if len(viable_contractors) < contractors_needed:
                logger.warning(f"Only {len(viable_contractors)} viable contractors found, needed {contractors_needed}")

            # Step 2: Calculate scores for each contractor
            scored_contractors = []
            for contractor in viable_contractors:
                score = self._calculate_contractor_score(contractor, project_type)
                scored_contractors.append(score)

            # Step 3: Sort by total score (highest first)
            scored_contractors.sort(key=lambda x: x.total_score, reverse=True)

            # Step 4: Select top contractors
            selected_scores = scored_contractors[:contractors_needed]
            selected_contractors = []

            for score in selected_scores:
                # Get full contractor data
                contractor = next(c for c in all_contractors if c.get("id") == score.contractor_id)
                contractor["selection_score"] = score.total_score
                contractor["selection_reason"] = self._get_selection_reason(score)
                selected_contractors.append(contractor)

            # Step 5: Log selection details
            selection_summary = {
                "success": True,
                "total_discovered": len(all_contractors),
                "viable_contractors": len(viable_contractors),
                "selected_count": len(selected_contractors),
                "contractors": selected_contractors,
                "scoring_details": [
                    {
                        "company": score.company_name,
                        "total_score": round(score.total_score, 2),
                        "rating": f"{score.google_rating}/5.0",
                        "reviews": score.google_review_count,
                        "distance": f"{score.distance_miles:.1f} miles",
                        "breakdown": {
                            "rating_score": round(score.rating_score, 2),
                            "review_score": round(score.review_score, 2),
                            "proximity_score": round(score.proximity_score, 2)
                        }
                    } for score in selected_scores
                ],
                "rejected_count": len(all_contractors) - len(selected_contractors),
                "rejected_reasons": self._get_rejection_summary(all_contractors, selected_contractors)
            }

            logger.info(f"Selected {len(selected_contractors)} contractors with average score: {sum(s.total_score for s in selected_scores)/len(selected_scores):.1f}")

            return selection_summary

        except Exception as e:
            logger.error(f"Error in smart contractor selection: {e!s}")
            return {
                "success": False,
                "error": str(e),
                "contractors": all_contractors[:contractors_needed]  # Fallback to first N
            }

    def _filter_viable_contractors(self, contractors: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter out contractors that don't meet minimum criteria"""
        viable = []

        for contractor in contractors:
            # Skip if missing critical data
            if not contractor.get("company_name"):
                continue

            # Get rating and review data (handle None values)
            rating = contractor.get("google_rating")
            reviews = contractor.get("google_review_count")

            # Convert to numeric values, handling None and non-numeric values
            try:
                rating = float(rating) if rating is not None else 0
                reviews = int(reviews) if reviews is not None else 0
            except (ValueError, TypeError):
                rating = 0
                reviews = 0

            # Update the contractor dict with clean numeric values
            contractor["google_rating"] = rating
            contractor["google_review_count"] = reviews

            if (rating >= self.min_rating and reviews >= self.min_reviews) or (rating >= 4.5 and reviews >= 3) or reviews >= 50:
                viable.append(contractor)

        return viable

    def _calculate_contractor_score(self, contractor: dict[str, Any], project_type: Optional[str] = None) -> ContractorScore:
        """Calculate comprehensive score for a contractor"""

        # Extract data - values should already be clean from _filter_viable_contractors
        rating = contractor.get("google_rating", 0)
        reviews = contractor.get("google_review_count", 0)
        distance = contractor.get("distance_miles")

        # Ensure numeric types and handle None distance
        try:
            rating = float(rating) if rating is not None else 0
            reviews = int(reviews) if reviews is not None else 0
            distance = float(distance) if distance is not None else 10
        except (ValueError, TypeError):
            rating = 0
            reviews = 0
            distance = 10

        # Calculate rating score (0-50 points)
        # 5.0 = 50 points, 4.0 = 30 points, 3.0 = 10 points
        if rating >= 5.0:
            rating_score = 50
        elif rating >= 4.5:
            rating_score = 40 + (rating - 4.5) * 20
        elif rating >= 4.0:
            rating_score = 30 + (rating - 4.0) * 20
        elif rating >= 3.5:
            rating_score = 20 + (rating - 3.5) * 20
        else:
            rating_score = max(0, rating * 4)

        # Calculate review count score (0-30 points)
        # Prioritize established businesses with more reviews
        if reviews >= 100:
            review_score = 30
        elif reviews >= 80:
            review_score = 28 + (reviews - 80) / 10  # 80-100 reviews: 28-30 points
        elif reviews >= 60:
            review_score = 26 + (reviews - 60) / 10  # 60-80 reviews: 26-28 points
        elif reviews >= 40:
            review_score = 23 + (reviews - 40) / 6.7  # 40-60 reviews: 23-26 points
        elif reviews >= 25:
            review_score = 20 + (reviews - 25) / 5    # 25-40 reviews: 20-23 points
        elif reviews >= 15:
            review_score = 17 + (reviews - 15) / 3.3  # 15-25 reviews: 17-20 points
        elif reviews >= 10:
            review_score = 15 + (reviews - 10) / 2.5  # 10-15 reviews: 15-17 points
        elif reviews >= 5:
            review_score = 10 + (reviews - 5) * 1     # 5-10 reviews: 10-15 points
        else:
            review_score = reviews * 2                 # <5 reviews: 0-10 points

        # Calculate proximity score (0-20 points)
        # Closer is better: 0-5 miles = 20 points, 5-10 = 15, 10-20 = 10, 20+ = 5
        if distance <= 5:
            proximity_score = 20
        elif distance <= 10:
            proximity_score = 15 + (10 - distance)
        elif distance <= 20:
            proximity_score = 10 + (20 - distance) / 2
        else:
            proximity_score = max(0, 30 - distance) / 2

        # Calculate total score
        total_score = rating_score + review_score + proximity_score

        return ContractorScore(
            contractor_id=contractor.get("id", ""),
            company_name=contractor.get("company_name", "Unknown"),
            rating_score=rating_score,
            review_score=review_score,
            proximity_score=proximity_score,
            total_score=total_score,
            google_rating=rating,
            google_review_count=reviews,
            distance_miles=distance
        )

    def _get_selection_reason(self, score: ContractorScore) -> str:
        """Generate human-readable selection reason"""
        reasons = []

        if score.google_rating >= 4.8:
            reasons.append("exceptional rating")
        elif score.google_rating >= 4.5:
            reasons.append("excellent rating")
        elif score.google_rating >= 4.0:
            reasons.append("strong rating")

        if score.google_review_count >= 100:
            reasons.append("very established business")
        elif score.google_review_count >= 50:
            reasons.append("well-established business")
        elif score.google_review_count >= 25:
            reasons.append("proven track record")

        if score.distance_miles <= 5:
            reasons.append("very close proximity")
        elif score.distance_miles <= 10:
            reasons.append("nearby location")

        return f"Selected for {' and '.join(reasons)}" if reasons else "Selected based on overall score"

    def _get_rejection_summary(self, all_contractors: list[dict[str, Any]], selected: list[dict[str, Any]]) -> dict[str, int]:
        """Summarize why contractors were rejected"""
        selected_ids = {c["id"] for c in selected}
        rejected = [c for c in all_contractors if c.get("id") not in selected_ids]

        reasons = {
            "low_rating": 0,
            "few_reviews": 0,
            "too_far": 0,
            "lower_score": 0
        }

        for contractor in rejected:
            rating = contractor.get("google_rating", 0)
            reviews = contractor.get("google_review_count", 0)
            distance = contractor.get("distance_miles", 10)

            if rating < self.min_rating:
                reasons["low_rating"] += 1
            elif reviews < self.min_reviews:
                reasons["few_reviews"] += 1
            elif distance > 25:
                reasons["too_far"] += 1
            else:
                reasons["lower_score"] += 1

        return reasons

    def optimize_search_parameters(self, project_type: str, location: dict[str, Any]) -> dict[str, Any]:
        """
        Optimize search parameters to find more high-quality contractors

        Returns optimized parameters for contractor search
        """
        # Holiday lighting specific optimizations
        if "holiday" in project_type.lower() or "christmas" in project_type.lower():
            return {
                "search_terms": [
                    "holiday lighting installation",
                    "christmas light installation",
                    "holiday decorating services",
                    "christmas decorating company",
                    "professional holiday lighting"
                ],
                "initial_search_count": 15,  # Search for more initially
                "search_radius_miles": 25,    # Wider search area
                "include_business_types": [
                    "electrician",
                    "lighting_contractor",
                    "event_management_company",
                    "landscaping_company"  # Many landscapers do holiday lighting
                ]
            }

        # Default parameters for other project types
        return {
            "search_terms": [project_type],
            "initial_search_count": 12,
            "search_radius_miles": 20,
            "include_business_types": []
        }
