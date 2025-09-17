"""
Tier 1: Internal Contractor Matching - UPDATED FOR REAL DATABASE
Now uses contractor_leads table instead of contractors table
ENHANCED: Added radius-based geographical search using uszipcode + haversine
"""
import os
import sys
from typing import Any

from supabase import Client


# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.radius_search_fixed import calculate_distance_miles, get_zip_codes_in_radius


class Tier1Matcher:
    """Tier 1 contractor matching using contractor_leads database"""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    def find_matching_contractors(self, bid_data: dict[str, Any], radius_miles: int = 15) -> list[dict[str, Any]]:
        """
        Find matching contractors from contractor_leads table within radius

        For MVP, we're searching contractor_leads that are:
        - Status = 'qualified' or 'contacted'
        - Have required specialties
        - Service the project location (within radius_miles)
        - Match the contractor size preference
        
        Args:
            bid_data: Bid card data with location and requirements
            radius_miles: Search radius in miles (default 15)
        """
        try:
            # Extract search criteria from bid data
            project_type = bid_data.get("project_type", "").lower()
            # Try multiple locations for location data
            location = (
                bid_data.get("location") or 
                bid_data.get("bid_document", {}).get("location") or 
                {}
            )
            zip_code = location.get("zip_code", "")
            budget_min = bid_data.get("budget_min", 0)
            budget_max = bid_data.get("budget_max", 0)

            # Get contractor size preference from bid data (check multiple locations)
            contractor_size_pref = (
                bid_data.get("contractor_requirements", {}).get("contractor_size_preference") or
                bid_data.get("bid_document", {}).get("contractor_requirements", {}).get("contractor_size_preference") or
                "small_business"
            )

            print(f"[Tier1] Searching for: {project_type} contractors within {radius_miles} miles of {zip_code}")
            print(f"[Tier1] Budget: ${budget_min}-${budget_max}")
            print(f"[Tier1] Contractor size preference: {contractor_size_pref}")

            if not zip_code:
                print("[Tier1 ERROR] No zip code provided in bid data")
                return {
                    "success": False,
                    "contractors": [],
                    "error": "No zip code provided"
                }

            # Get all zip codes within radius of project location
            target_zip_codes = get_zip_codes_in_radius(zip_code, radius_miles)
            print(f"[Tier1] Found {len(target_zip_codes)} zip codes within {radius_miles} miles")

            # Build the query
            query = self.supabase.table("contractor_leads").select("*")

            # Filter by status - only qualified or contacted leads
            query = query.in_("lead_status", ["qualified", "contacted"])

            # Filter by contractor size if specified
            if contractor_size_pref and contractor_size_pref != "any":
                # Allow some flexibility in size
                size_options = self._get_flexible_sizes(contractor_size_pref)
                query = query.in_("contractor_size", size_options)

            # Filter by location (state level for broad filtering)
            if location.get("state"):
                query = query.eq("state", location["state"])

            # Order by quality indicators
            query = query.order("rating", desc=True)
            query = query.order("review_count", desc=True)
            query = query.order("lead_score", desc=True)

            # Get more results since we'll filter by radius
            query = query.limit(100)

            # Execute query
            result = query.execute()
            contractors = result.data if result.data else []

            print(f"[Tier1] Initial query returned {len(contractors)} contractor leads")

            # Client-side filtering for specialties and radius-based location match
            filtered_contractors = []

            for contractor in contractors:
                # Check specialty match
                contractor_specialties = contractor.get("specialties", [])
                if not contractor_specialties:
                    # If no specialties listed, include them anyway (might be general contractor)
                    pass
                elif not self._check_specialty_match(project_type, contractor_specialties):
                    continue

                # Check location proximity using radius search
                if not self._check_radius_location_match(contractor, zip_code, radius_miles):
                    continue

                # Add Tier 1 metadata
                contractor["discovery_tier"] = 1
                contractor["match_score"] = self._calculate_tier1_score(contractor, bid_data)
                contractor["match_reasons"] = self._get_match_reasons(contractor, bid_data)

                filtered_contractors.append(contractor)

            # Sort by distance first, then by match score
            filtered_contractors.sort(key=lambda x: (x.get("distance_miles", 999), -x["match_score"]))

            print(f"[Tier1] After radius filtering: {len(filtered_contractors)} matching contractors")

            # Return top contractors from Tier 1
            return {
                "success": True,
                "contractors": filtered_contractors[:10],
                "search_radius_miles": radius_miles,
                "zip_codes_searched": len(target_zip_codes)
            }

        except Exception as e:
            print(f"[Tier1 ERROR] Failed to find matching contractors: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "contractors": [],
                "error": str(e)
            }

    def _get_flexible_sizes(self, size_preference: str) -> list[str]:
        """Get flexible size options based on preference"""
        size_flexibility = {
            "solo_handyman": ["solo_handyman", "owner_operator"],
            "owner_operator": ["solo_handyman", "owner_operator", "small_business"],
            "small_business": ["owner_operator", "small_business", "regional_company"],
            "regional_company": ["small_business", "regional_company", "national_chain"],
            "national_chain": ["regional_company", "national_chain"]
        }
        return size_flexibility.get(size_preference, [size_preference])

    def _check_specialty_match(self, project_type: str, specialties: list[str]) -> bool:
        """Check if contractor specialties match project type"""
        if not project_type or not specialties:
            return True  # If we don't know, include them

        # Project type keywords
        project_keywords = project_type.lower().split()

        # Check each specialty
        for specialty in specialties:
            specialty_lower = specialty.lower()
            # Check for any keyword match
            for keyword in project_keywords:
                if keyword in specialty_lower:
                    return True

        # Common mappings
        mappings = {
            "kitchen": ["kitchen", "remodel", "cabinet", "countertop"],
            "bathroom": ["bathroom", "bath", "plumbing", "tile"],
            "deck": ["deck", "patio", "outdoor", "carpentry"],
            "roofing": ["roof", "roofing", "shingle", "gutter"],
            "painting": ["paint", "painting", "drywall", "interior"],
            "flooring": ["floor", "flooring", "tile", "hardwood", "carpet"],
            "plumbing": ["plumb", "plumbing", "pipe", "drain"],
            "electrical": ["electric", "electrical", "wiring", "panel"]
        }

        # Check mappings
        for key, values in mappings.items():
            if key in project_type:
                for specialty in specialties:
                    if any(v in specialty.lower() for v in values):
                        return True

        return False

    def _check_radius_location_match(self, contractor: dict[str, Any], project_zip: str, radius_miles: int) -> bool:
        """Check if contractor is within radius of project location using distance calculation"""
        try:
            # Get contractor's zip code
            contractor_zip = None

            # Try different zip code fields the contractor might have
            if contractor.get("zip_code"):
                contractor_zip = str(contractor["zip_code"]).strip()
            elif contractor.get("zip"):
                contractor_zip = str(contractor["zip"]).strip()
            elif contractor.get("postal_code"):
                contractor_zip = str(contractor["postal_code"]).strip()
            elif contractor.get("location_zip"):
                contractor_zip = str(contractor["location_zip"]).strip()

            if not contractor_zip:
                print(f"[Tier1] No zip code found for contractor {contractor.get('id', 'unknown')}")
                return False

            # Calculate distance between project and contractor
            distance = calculate_distance_miles(project_zip, contractor_zip)

            if distance is None:
                print(f"[Tier1] Could not calculate distance between {project_zip} and {contractor_zip}")
                return False

            # Add distance to contractor data for sorting
            contractor["distance_miles"] = distance

            # Check if within radius
            within_radius = distance <= radius_miles

            if within_radius:
                print(f"[Tier1] Contractor {contractor.get('company_name', 'Unknown')} is {distance} miles away (within {radius_miles} mile radius)")

            return within_radius

        except Exception as e:
            print(f"[Tier1] Error checking radius location match: {e}")
            return False

    def _check_location_match(self, contractor: dict[str, Any], location: dict[str, Any]) -> bool:
        """Legacy location matching method - kept for backward compatibility"""
        # For now, match by state and city
        if not location:
            return True

        # State match
        if location.get("state") and contractor.get("state"):
            if location["state"] != contractor["state"]:
                return False

        # City match (more flexible)
        if location.get("city") and contractor.get("city"):
            # Allow nearby cities
            project_city = location["city"].lower()
            contractor_city = contractor["city"].lower()

            # Exact match or common metro areas
            if project_city == contractor_city:
                return True

            # Check service radius
            radius = contractor.get("service_radius_miles")
            if radius and radius >= 25:  # Willing to travel
                return True

        # Zip code check
        if location.get("zip_code"):
            project_zip = location["zip_code"]
            service_zips = contractor.get("service_zip_codes", [])
            if service_zips and project_zip in service_zips:
                return True

        # Default to true if we can't determine
        return True

    def _calculate_tier1_score(self, contractor: dict[str, Any], bid_data: dict[str, Any]) -> float:
        """Calculate match score for contractor lead"""
        score = 0.0

        # Base score from lead score if available
        lead_score = contractor.get("lead_score", 50)
        score += lead_score  # Already 0-100 scale

        # Rating bonus (0-5 scale)
        rating = float(contractor.get("rating", 0))
        if rating > 0:
            score += rating * 4  # Max 20 points from rating

        # Review count bonus
        review_count = contractor.get("review_count", 0)
        if review_count >= 100:
            score += 15
        elif review_count >= 50:
            score += 10
        elif review_count >= 20:
            score += 5
        elif review_count >= 5:
            score += 2

        # Verification bonuses
        if contractor.get("license_verified"):
            score += 10
        if contractor.get("insurance_verified"):
            score += 10
        if contractor.get("bonded"):
            score += 5

        # Size match bonus
        size_pref = bid_data.get("contractor_requirements", {}).get("contractor_size_preference")
        if size_pref and contractor.get("contractor_size") == size_pref:
            score += 10  # Exact size match

        # Years in business
        years = contractor.get("years_in_business") or 0
        if years >= 10:
            score += 10
        elif years >= 5:
            score += 5
        elif years >= 2:
            score += 2

        return min(100.0, max(0.0, score))

    def _get_match_reasons(self, contractor: dict[str, Any], bid_data: dict[str, Any]) -> list[str]:
        """Get human-readable match reasons"""
        reasons = []

        # Company size
        size = contractor.get("contractor_size", "unknown")
        size_labels = {
            "solo_handyman": "Solo handyman",
            "owner_operator": "Owner-operator",
            "small_business": "Small business",
            "regional_company": "Regional company",
            "national_chain": "National chain"
        }
        if size in size_labels:
            reasons.append(size_labels[size])

        # Rating
        rating = float(contractor.get("rating", 0))
        review_count = contractor.get("review_count", 0)
        if (rating >= 4.5 and review_count >= 10) or (rating >= 4.0 and review_count >= 5):
            reasons.append(f"{rating} star rating ({review_count} reviews)")
        elif rating > 0:
            reasons.append(f"{rating} star rating")

        # Experience
        years = contractor.get("years_in_business") or 0
        if years >= 10:
            reasons.append(f"{years}+ years in business")
        elif years >= 5:
            reasons.append(f"{years} years experience")

        # Verifications
        verifications = []
        if contractor.get("license_verified"):
            verifications.append("Licensed")
        if contractor.get("insurance_verified"):
            verifications.append("Insured")
        if contractor.get("bonded"):
            verifications.append("Bonded")

        if verifications:
            reasons.append(", ".join(verifications))

        # Specialty match
        project_type = bid_data.get("project_type", "").lower()
        contractor_specialties = contractor.get("specialties", [])
        for spec in contractor_specialties:
            if project_type in str(spec).lower() or any(word in str(spec).lower() for word in project_type.split()):
                reasons.append(f"Specializes in {spec}")
                break

        # Location with distance
        distance = contractor.get("distance_miles")
        city = contractor.get("city", "")
        state = contractor.get("state", "")

        if distance is not None:
            if city and state:
                reasons.append(f"Based in {city}, {state} ({distance} miles away)")
            else:
                reasons.append(f"{distance} miles away")
        elif city and state:
            reasons.append(f"Based in {city}, {state}")

        return reasons
