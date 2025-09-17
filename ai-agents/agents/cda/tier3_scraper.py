"""
Tier 3: External Contractor Sourcing
Web scraping and external source identification
"""
import re
from typing import Any

from supabase import Client


class Tier3Scraper:
    """Tier 3 external contractor sourcing via web scraping"""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    def identify_external_sources(self, bid_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Identify external sources for contractor discovery

        For MVP, we'll identify sources and return search parameters.
        Full scraping implementation would require Scrapy spiders.
        """
        try:
            project_type = bid_data.get("project_type", "").lower()
            location = bid_data.get("location", {})
            zip_code = self._extract_zip_code(location)
            city_state = self._extract_city_state(location)

            print(f"[Tier3] Identifying external sources for: {project_type} in {city_state} ({zip_code})")

            # Define search sources and parameters
            sources = []

            # Google Business Search
            google_search = self._create_google_search_params(project_type, city_state, zip_code)
            sources.append(google_search)

            # Yelp Search
            yelp_search = self._create_yelp_search_params(project_type, city_state, zip_code)
            sources.append(yelp_search)

            # Angie's List Search
            angies_search = self._create_angies_search_params(project_type, city_state, zip_code)
            sources.append(angies_search)

            # Better Business Bureau
            bbb_search = self._create_bbb_search_params(project_type, city_state, zip_code)
            sources.append(bbb_search)

            # State License Database
            license_search = self._create_license_search_params(project_type, location)
            if license_search:
                sources.append(license_search)

            print(f"[Tier3] Identified {len(sources)} external sources")

            return sources

        except Exception as e:
            print(f"[Tier3 ERROR] Failed to identify external sources: {e}")
            return []

    def _extract_zip_code(self, location: dict[str, Any]) -> str:
        """Extract zip code from location data"""
        if not location:
            return ""

        full_location = location.get("full_location", "")
        zip_match = re.search(r"\b(\d{5})\b", full_location)
        return zip_match.group(1) if zip_match else ""

    def _extract_city_state(self, location: dict[str, Any]) -> str:
        """Extract city and state from location data"""
        if not location:
            return ""

        full_location = location.get("full_location", "")

        # Try to extract city, state from full location
        # Format: "Melbourne, Florida 32904" -> "Melbourne, FL"
        parts = full_location.split(",")
        if len(parts) >= 2:
            city = parts[0].strip()
            state_part = parts[1].strip()

            # Extract state name/abbreviation before zip code
            state_match = re.search(r"^([A-Za-z\s]+)", state_part)
            if state_match:
                state = state_match.group(1).strip()

                # Convert full state names to abbreviations
                state_abbrevs = {
                    "florida": "FL", "california": "CA", "texas": "TX",
                    "new york": "NY", "illinois": "IL", "pennsylvania": "PA"
                }
                state_lower = state.lower()
                if state_lower in state_abbrevs:
                    state = state_abbrevs[state_lower]

                return f"{city}, {state}"

        return full_location

    def _create_google_search_params(self, project_type: str, city_state: str, zip_code: str) -> dict[str, Any]:
        """Create Google Business search parameters"""
        # Map project types to search terms
        search_terms = {
            "kitchen": "kitchen remodeling contractors",
            "bathroom": "bathroom renovation contractors",
            "roofing": "roofing contractors",
            "lawn care": "lawn care landscaping services",
            "plumbing": "plumbing contractors",
            "electrical": "electrical contractors",
            "flooring": "flooring installation contractors"
        }

        search_term = search_terms.get(project_type, f"{project_type} contractors")

        return {
            "source": "Google Business",
            "search_type": "local_business",
            "query": f"{search_term} near {city_state}",
            "location": city_state,
            "zip_code": zip_code,
            "category": project_type,
            "url": f'https://www.google.com/search?q={search_term.replace(" ", "+")}+near+{city_state.replace(" ", "+").replace(",", "%2C")}',
            "expected_results": "10-20 contractors",
            "scraping_difficulty": "high"  # Google has anti-bot measures
        }

    def _create_yelp_search_params(self, project_type: str, city_state: str, zip_code: str) -> dict[str, Any]:
        """Create Yelp search parameters"""
        # Yelp category mappings
        yelp_categories = {
            "kitchen": "kitchenbath",
            "bathroom": "kitchenbath",
            "roofing": "roofing",
            "lawn care": "landscaping",
            "plumbing": "plumbing",
            "electrical": "electricians",
            "flooring": "flooring"
        }

        category = yelp_categories.get(project_type, "contractors")

        return {
            "source": "Yelp",
            "search_type": "business_directory",
            "query": f"{project_type} contractors",
            "location": city_state,
            "zip_code": zip_code,
            "category": category,
            "url": f"https://www.yelp.com/search?find_desc={category}&find_loc={city_state}",
            "expected_results": "5-15 contractors",
            "scraping_difficulty": "medium"
        }

    def _create_angies_search_params(self, project_type: str, city_state: str, zip_code: str) -> dict[str, Any]:
        """Create Angie's List search parameters"""
        return {
            "source": "Angie's List",
            "search_type": "contractor_directory",
            "query": f"{project_type} contractors",
            "location": city_state,
            "zip_code": zip_code,
            "category": project_type,
            "url": f'https://www.angieslist.com/search/contractors/{project_type.replace(" ", "-")}',
            "expected_results": "3-10 contractors",
            "scraping_difficulty": "medium"
        }

    def _create_bbb_search_params(self, project_type: str, city_state: str, zip_code: str) -> dict[str, Any]:
        """Create Better Business Bureau search parameters"""
        return {
            "source": "Better Business Bureau",
            "search_type": "business_directory",
            "query": f"{project_type} contractors",
            "location": city_state,
            "zip_code": zip_code,
            "category": project_type,
            "url": f'https://www.bbb.org/search?find_country=USA&find_text={project_type.replace(" ", "%20")}+contractors&find_type=Business&find_loc={city_state.replace(" ", "%20")}',
            "expected_results": "2-8 contractors",
            "scraping_difficulty": "low"
        }

    def _create_license_search_params(self, project_type: str, location: dict[str, Any]) -> dict[str, Any]:
        """Create state license database search parameters"""
        # Determine state from location
        full_location = location.get("full_location", "").lower()

        # Florida license database (example)
        if "florida" in full_location or "fl" in full_location:
            license_types = {
                "kitchen": "Certified General Contractor",
                "bathroom": "Certified General Contractor",
                "roofing": "Certified Roofing Contractor",
                "plumbing": "Certified Plumbing Contractor",
                "electrical": "Certified Electrical Contractor"
            }

            license_type = license_types.get(project_type)
            if license_type:
                return {
                    "source": "Florida DBPR License Search",
                    "search_type": "license_database",
                    "query": license_type,
                    "location": location.get("full_location", ""),
                    "state": "Florida",
                    "url": "https://www.myfloridalicense.com/wl11.asp",
                    "expected_results": "5-20 contractors",
                    "scraping_difficulty": "low"
                }

        return None

    def execute_scraping(self, source_params: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Execute actual web scraping for a source

        This would be implemented with Scrapy spiders in production.
        For now, returns mock data structure.
        """
        # TODO: Implement actual Scrapy spiders
        # For now, return mock external contractor data

        mock_contractors = [
            {
                "discovery_tier": 3,
                "source": source_params["source"],
                "company_name": f"External {source_params['category'].title()} Pro",
                "contact_name": "Unknown",
                "email": "contact@external-contractor.com",
                "phone": "555-EXTERNAL",
                "specialties": [source_params["category"]],
                "location": source_params["location"],
                "rating": 0.0,  # Would be scraped
                "total_projects": 0,  # Unknown for external
                "match_score": 60.0,  # Lower score for external
                "match_reasons": ["Found via external search", f'Listed on {source_params["source"]}'],
                "onboarded": False,
                "external_data": {
                    "source_url": source_params["url"],
                    "scraping_date": "2025-01-29",
                    "verification_needed": True
                }
            }
        ]

        print(f"[Tier3] Mock scraping {source_params['source']} would return {len(mock_contractors)} contractors")
        return mock_contractors
