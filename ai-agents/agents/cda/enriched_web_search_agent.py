"""
Enhanced Web Search Agent with Automatic Enrichment
Discovers contractors and enriches them in one flow
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from supabase import Client

from agents.enrichment.smart_website_enricher import SmartWebsiteEnricher

from .web_search_agent import PotentialContractor, WebSearchContractorAgent


class EnrichedWebSearchAgent(WebSearchContractorAgent):
    """
    Extended web search agent that automatically enriches discovered contractors
    """

    def __init__(self, supabase: Client, use_playwright: bool = False):
        super().__init__(supabase)
        self.enricher = SmartWebsiteEnricher()
        self.use_playwright = use_playwright
        print("[EnrichedWebSearchAgent] Initialized with automatic enrichment")

    async def discover_and_enrich_contractors(self, bid_card_id: str, contractors_needed: int = 5) -> dict[str, Any]:
        """
        Discover contractors and automatically enrich them
        """
        try:
            print(f"[EnrichedWebSearchAgent] Starting discovery + enrichment for bid card: {bid_card_id}")

            # Step 1: Load bid card data
            bid_data = self._load_bid_card_data(bid_card_id)
            if not bid_data:
                return {"success": False, "error": "Could not load bid card data"}

            # Step 2: Extract search parameters including business size preference
            search_query = self._extract_search_query(bid_data)

            # Extract business size preference from bid data
            contractor_requirements = bid_data.get("contractor_requirements", {})
            preferred_business_size = contractor_requirements.get("preferred_business_size")

            print(f"[EnrichedWebSearchAgent] Search: {search_query.project_type} near {search_query.zip_code}")
            if preferred_business_size:
                print(f"[EnrichedWebSearchAgent] Preferred business size: {preferred_business_size}")

            # Step 3: Discover more contractors than needed (for smart selection)
            contractors_to_find = min(contractors_needed * 3, 15)  # Find 3x needed, max 15
            print(f"[EnrichedWebSearchAgent] Finding {contractors_to_find} contractors to select best {contractors_needed}")

            contractors = self._search_contractors(search_query, contractors_to_find)
            print(f"[EnrichedWebSearchAgent] Found {len(contractors)} contractors")

            # Step 4: Enrich all discovered contractors
            enriched_contractors = []
            for i, contractor in enumerate(contractors):
                print(f"\n[EnrichedWebSearchAgent] Enriching {i+1}/{len(contractors)}: {contractor.company_name}")

                # Prepare contractor data for enrichment
                contractor_dict = {
                    "website": contractor.website,
                    "company_name": contractor.company_name,
                    "google_review_count": contractor.google_review_count,
                    "project_type": contractor.project_type,
                    "phone": contractor.phone
                }

                # Enrich using website data
                if contractor.website:
                    enriched_data = self.enricher.enrich_contractor_from_website(contractor_dict)

                    # Update contractor with enriched data
                    contractor.email = enriched_data.email or contractor.email
                    contractor.business_size = enriched_data.business_size
                    contractor.service_types = enriched_data.service_types
                    contractor.service_description = enriched_data.service_description
                    contractor.service_areas = enriched_data.service_areas
                    contractor.enrichment_status = "ENRICHED"
                    contractor.enrichment_data = {
                        "about_text": enriched_data.about_text,
                        "team_size_estimate": enriched_data.team_size_estimate,
                        "years_in_business": enriched_data.years_in_business,
                        "enrichment_timestamp": datetime.now().isoformat()
                    }
                else:
                    # No website - classify based on review count
                    contractor.business_size = self._classify_by_reviews(contractor.google_review_count)
                    contractor.service_types = ["MAINTENANCE"]  # Default
                    contractor.enrichment_status = "NO_WEBSITE"

                enriched_contractors.append(contractor)

                # Show enrichment results
                print(f"   - Email: {'Found' if contractor.email else 'Not found'}")
                print(f"   - Business Size: {contractor.business_size}")
                print(f"   - Service Types: {contractor.service_types}")

            # Step 5: Smart selection based on requirements
            selected_contractors = self._smart_select_contractors(
                enriched_contractors,
                contractors_needed,
                preferred_business_size
            )

            print(f"\n[EnrichedWebSearchAgent] Selected {len(selected_contractors)} best matching contractors")

            # Step 6: Store selected contractors with enrichment data
            stored_contractors = self._store_enriched_contractors(selected_contractors, bid_card_id)

            # Step 7: Generate summary statistics
            stats = self._calculate_enrichment_stats(stored_contractors)

            result = {
                "success": True,
                "bid_card_id": bid_card_id,
                "search_query": search_query.__dict__,
                "contractors_discovered": len(contractors),
                "contractors_enriched": len(enriched_contractors),
                "contractors_selected": len(selected_contractors),
                "contractors_stored": len(stored_contractors),
                "enrichment_stats": stats,
                "contractors": stored_contractors
            }

            print(f"\n[EnrichedWebSearchAgent] Complete! Stored {len(stored_contractors)} enriched contractors")
            print(f"[EnrichedWebSearchAgent] Stats: {stats}")

            return result

        except Exception as e:
            print(f"[EnrichedWebSearchAgent ERROR] Failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "bid_card_id": bid_card_id
            }

    def _classify_by_reviews(self, review_count: Optional[int]) -> str:
        """Classify business size based on review count alone"""
        if not review_count:
            return "INDIVIDUAL_HANDYMAN"
        elif review_count > 500:
            return "NATIONAL_COMPANY"
        elif review_count > 100:
            return "LOCAL_BUSINESS_TEAMS"
        elif review_count > 10:
            return "OWNER_OPERATOR"
        else:
            return "INDIVIDUAL_HANDYMAN"

    def _smart_select_contractors(
        self,
        contractors: list[PotentialContractor],
        needed: int,
        preferred_size: Optional[str] = None
    ) -> list[PotentialContractor]:
        """
        Smart selection algorithm that considers:
        1. Business size preference match
        2. Data completeness (email, phone, website)
        3. Rating and reviews
        4. Service type match
        """
        # Score each contractor
        scored_contractors = []

        for contractor in contractors:
            score = 0

            # Business size match (30 points)
            if preferred_size and contractor.business_size == preferred_size:
                score += 30
            elif contractor.business_size in ["LOCAL_BUSINESS_TEAMS", "OWNER_OPERATOR"]:
                score += 15  # These are generally good

            # Data completeness (30 points)
            if contractor.email:
                score += 10
            if contractor.phone:
                score += 10
            if contractor.website:
                score += 10

            # Rating (20 points)
            if contractor.google_rating:
                if contractor.google_rating >= 4.5:
                    score += 20
                elif contractor.google_rating >= 4.0:
                    score += 15
                elif contractor.google_rating >= 3.5:
                    score += 10

            # Review count (20 points)
            if contractor.google_review_count:
                if contractor.google_review_count >= 100:
                    score += 20
                elif contractor.google_review_count >= 50:
                    score += 15
                elif contractor.google_review_count >= 20:
                    score += 10
                elif contractor.google_review_count >= 10:
                    score += 5

            scored_contractors.append((score, contractor))

        # Sort by score (highest first)
        scored_contractors.sort(key=lambda x: x[0], reverse=True)

        # Return top N contractors
        selected = [contractor for score, contractor in scored_contractors[:needed]]

        # Log selection reasoning
        print("\n[SmartSelection] Contractor scores:")
        for score, contractor in scored_contractors[:needed]:
            print(f"   {contractor.company_name}: {score} points")
            print(f"      Size: {contractor.business_size}, Email: {'Yes' if contractor.email else 'No'}")

        return selected

    def _store_enriched_contractors(self, contractors: list[PotentialContractor], bid_card_id: str) -> list[dict[str, Any]]:
        """Store contractors with enrichment data"""
        stored_contractors = []

        try:
            for contractor in contractors:
                # Prepare data for storage
                contractor_data = {
                    "discovery_source": contractor.discovery_source,
                    "source_query": contractor.source_query,
                    "project_zip_code": contractor.project_zip_code,
                    "project_type": contractor.project_type,
                    "company_name": contractor.company_name,
                    "contact_name": contractor.contact_name,
                    "phone": contractor.phone,
                    "email": contractor.email,
                    "website": contractor.website,
                    "address": contractor.address,
                    "city": contractor.city,
                    "state": contractor.state,
                    "zip_code": contractor.zip_code,
                    "google_place_id": contractor.google_place_id,
                    "google_rating": contractor.google_rating,
                    "google_review_count": contractor.google_review_count,
                    "google_types": contractor.google_types,
                    "google_business_status": contractor.google_business_status,
                    "search_rank": contractor.search_rank,
                    "match_score": contractor.match_score,
                    # New enrichment fields
                    "business_size": getattr(contractor, "business_size", None),
                    "service_types": getattr(contractor, "service_types", None),
                    "service_description": getattr(contractor, "service_description", None),
                    "service_areas": getattr(contractor, "service_areas", None),
                    "enrichment_status": getattr(contractor, "enrichment_status", "PENDING"),
                    "enrichment_data": getattr(contractor, "enrichment_data", None)
                }

                # Insert into database
                result = self.supabase.table("potential_contractors").insert(contractor_data).execute()

                if result.data:
                    stored_contractors.append(result.data[0])
                    print(f"[EnrichedWebSearchAgent] Stored: {contractor.company_name} ({contractor.business_size})")

            return stored_contractors

        except Exception as e:
            print(f"[EnrichedWebSearchAgent ERROR] Failed to store contractors: {e}")
            return stored_contractors

    def _calculate_enrichment_stats(self, contractors: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate enrichment statistics"""
        total = len(contractors)
        if total == 0:
            return {}

        stats = {
            "total_contractors": total,
            "with_email": sum(1 for c in contractors if c.get("email")),
            "with_phone": sum(1 for c in contractors if c.get("phone")),
            "with_website": sum(1 for c in contractors if c.get("website")),
            "enrichment_complete": sum(1 for c in contractors if c.get("enrichment_status") == "ENRICHED"),
            "business_sizes": {},
            "service_types": {}
        }

        # Count business sizes
        for contractor in contractors:
            size = contractor.get("business_size", "UNKNOWN")
            stats["business_sizes"][size] = stats["business_sizes"].get(size, 0) + 1

        # Count service types
        for contractor in contractors:
            types = contractor.get("service_types", [])
            for service_type in types:
                stats["service_types"][service_type] = stats["service_types"].get(service_type, 0) + 1

        # Calculate percentages
        stats["email_percentage"] = round(stats["with_email"] / total * 100, 1)
        stats["phone_percentage"] = round(stats["with_phone"] / total * 100, 1)
        stats["website_percentage"] = round(stats["with_website"] / total * 100, 1)
        stats["enrichment_percentage"] = round(stats["enrichment_complete"] / total * 100, 1)

        return stats

# Extend the PotentialContractor dataclass to include enrichment fields
@dataclass
class EnrichedPotentialContractor(PotentialContractor):
    """Extended contractor with enrichment fields"""
    business_size: Optional[str] = None
    service_types: Optional[list[str]] = None
    service_description: Optional[str] = None
    service_areas: Optional[list[str]] = None
    enrichment_status: Optional[str] = None
    enrichment_data: Optional[dict[str, Any]] = None
