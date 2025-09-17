"""
Tier 1: Internal Contractor Matching
Optimized PostgreSQL queries for onboarded contractors
"""
from typing import Any

from supabase import Client


class Tier1Matcher:
    """Tier 1 contractor matching using internal database"""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    def find_matching_contractors(self, bid_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Find matching contractors from internal database

        Uses optimized query from PRD:
        SELECT * FROM contractors
        WHERE onboarded = true
          AND zip_codes CONTAINS project_zip
          AND specialties CONTAINS project_type
          AND project_size BETWEEN min_size AND max_size
          AND availability = 'available'
        """
        try:
            # Extract search criteria from bid data
            project_type = bid_data.get("project_type", "").lower()
            location = bid_data.get("location", {})
            zip_code = self._extract_zip_code(location)
            budget_max = bid_data.get("budget_max", 0)

            print(f"[Tier1] Searching for: {project_type} in {zip_code}, budget up to ${budget_max}")

            # Build the query using Supabase PostgREST
            query = self.supabase.table("contractors").select("*")

            # Apply filters step by step
            query = query.eq("onboarded", True)
            query = query.eq("availability", "available")

            # Filter by project size (budget compatibility)
            if budget_max > 0:
                query = query.lte("min_project_size", budget_max)
                query = query.gte("max_project_size", budget_max)

            # Order by rating (best contractors first)
            query = query.order("rating", desc=True)
            query = query.order("total_projects", desc=True)

            # Execute query
            result = query.execute()
            contractors = result.data if result.data else []

            print(f"[Tier1] Initial query returned {len(contractors)} contractors")

            # Filter by zip code and specialties (client-side for now)
            # TODO: Implement proper GIN index queries when Supabase supports it
            filtered_contractors = []

            for contractor in contractors:
                # Check zip code match
                contractor_zips = contractor.get("zip_codes", [])
                if zip_code and not any(zip_code in str(czip) for czip in contractor_zips):
                    continue

                # Check specialty match
                contractor_specialties = contractor.get("specialties", [])
                if project_type and not any(project_type in str(spec).lower() for spec in contractor_specialties):
                    continue

                # Add Tier 1 metadata
                contractor["discovery_tier"] = 1
                contractor["match_score"] = self._calculate_tier1_score(contractor, bid_data)
                contractor["match_reasons"] = self._get_match_reasons(contractor, bid_data)

                filtered_contractors.append(contractor)

            # Sort by match score
            filtered_contractors.sort(key=lambda x: x["match_score"], reverse=True)

            print(f"[Tier1] After filtering: {len(filtered_contractors)} matching contractors")

            # Return top 5 from Tier 1
            return filtered_contractors[:5]

        except Exception as e:
            print(f"[Tier1 ERROR] Failed to find matching contractors: {e}")
            return []

    def _extract_zip_code(self, location: dict[str, Any]) -> str:
        """Extract zip code from location data"""
        if not location:
            return ""

        full_location = location.get("full_location", "")

        # Look for zip code patterns in location
        import re
        zip_match = re.search(r"\b(\d{5})\b", full_location)
        if zip_match:
            return zip_match.group(1)

        return ""

    def _calculate_tier1_score(self, contractor: dict[str, Any], bid_data: dict[str, Any]) -> float:
        """Calculate match score for Tier 1 contractor"""
        score = 0.0

        # Base score from rating (0-5 scale)
        rating = float(contractor.get("rating", 0))
        score += rating * 20  # Max 100 points from rating

        # Experience bonus (total projects)
        total_projects = contractor.get("total_projects", 0)
        if total_projects > 100:
            score += 20
        elif total_projects > 50:
            score += 15
        elif total_projects > 20:
            score += 10
        elif total_projects > 5:
            score += 5

        # Insurance verification bonus
        if contractor.get("insurance_verified"):
            score += 10

        # License verification bonus
        if contractor.get("license_number"):
            score += 5

        # Project size compatibility
        budget_max = bid_data.get("budget_max", 0)
        min_size = contractor.get("min_project_size", 0)
        max_size = contractor.get("max_project_size", 999999)

        if min_size <= budget_max <= max_size:
            score += 15  # Perfect fit
        elif budget_max < min_size:
            score -= 10  # Project too small
        elif budget_max > max_size * 1.5:
            score -= 5   # Project much larger than usual

        return min(100.0, max(0.0, score))

    def _get_match_reasons(self, contractor: dict[str, Any], bid_data: dict[str, Any]) -> list[str]:
        """Get human-readable match reasons"""
        reasons = []

        # Rating
        rating = float(contractor.get("rating", 0))
        if rating >= 4.8:
            reasons.append("Excellent rating (4.8+)")
        elif rating >= 4.5:
            reasons.append("Great rating (4.5+)")
        elif rating >= 4.0:
            reasons.append("Good rating (4.0+)")

        # Experience
        total_projects = contractor.get("total_projects", 0)
        if total_projects > 100:
            reasons.append("Highly experienced (100+ projects)")
        elif total_projects > 50:
            reasons.append("Very experienced (50+ projects)")
        elif total_projects > 20:
            reasons.append("Experienced (20+ projects)")

        # Verifications
        if contractor.get("insurance_verified"):
            reasons.append("Insurance verified")
        if contractor.get("license_number"):
            reasons.append("Licensed contractor")

        # Specialty match
        project_type = bid_data.get("project_type", "").lower()
        contractor_specialties = contractor.get("specialties", [])
        for spec in contractor_specialties:
            if project_type in str(spec).lower():
                reasons.append(f"Specializes in {spec}")
                break

        return reasons
