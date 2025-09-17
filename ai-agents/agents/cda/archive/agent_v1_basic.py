"""
CDA (Contractor Discovery Agent) - 3-Tier Contractor Sourcing
Implements PRD requirements for finding qualified contractors
"""
import os
import sys
from datetime import datetime
from typing import Any, Optional

from dotenv import load_dotenv
from supabase import create_client


# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from agents.cda.scoring import ContractorScorer
from agents.cda.tier1_matcher_v2 import Tier1Matcher
from agents.cda.tier2_reengagement_v2 import Tier2Reengagement
from agents.cda.tier3_scraper import Tier3Scraper
from agents.cda.web_search_agent import WebSearchContractorAgent


class ContractorDiscoveryAgent:
    """CDA - 3-tier contractor sourcing system"""

    def __init__(self):
        """Initialize CDA with Supabase connection and tier components"""
        load_dotenv(override=True)
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)

        # Initialize tier components
        self.tier1_matcher = Tier1Matcher(self.supabase)
        self.tier2_reengagement = Tier2Reengagement(self.supabase)
        self.tier3_scraper = Tier3Scraper(self.supabase)
        self.web_search_agent = WebSearchContractorAgent(self.supabase)
        self.scorer = ContractorScorer()

        print("[CDA] Initialized Contractor Discovery Agent with 3-tier sourcing")

    def discover_contractors(self, bid_card_id: str) -> dict[str, Any]:
        """
        Main CDA function: Execute 3-tier contractor discovery

        Args:
            bid_card_id: ID of the bid card to find contractors for

        Returns:
            Dict with success status and contractor results
        """
        print(f"\n[CDA] Starting contractor discovery for bid card: {bid_card_id}")
        start_time = datetime.now()

        try:
            # Step 1: Load bid card data
            print("[CDA] Loading bid card data...")

            # Check if this is a test ID and use mock data
            if bid_card_id.startswith("12345678-1234-1234-1234"):
                print("[CDA] Using mock data for test")
                bid_card = {
                    "id": bid_card_id,
                    "bid_card_number": "BC-TEST-MOCK",
                    "urgency_level": "emergency",
                    "contractor_count_needed": 4
                }
                bid_data = {
                    "project_type": "kitchen remodel",
                    "budget_min": 25000,
                    "budget_max": 35000,
                    "urgency_level": "emergency",
                    "location": {
                        "full_location": "Orlando, FL 32801",
                        "zip_code": "32801"
                    },
                    "contractor_requirements": {
                        "contractor_count": 4,
                        "specialties_required": ["kitchen remodeling"]
                    }
                }
            elif bid_card_id == "test-solar-project":
                print("[CDA] Using mock solar project data for test")
                bid_card = {
                    "id": bid_card_id,
                    "bid_card_number": "BC-TEST-SOLAR",
                    "urgency_level": "week",
                    "contractor_count_needed": 8
                }
                bid_data = {
                    "project_type": "solar panel installation",
                    "budget_min": 15000,
                    "budget_max": 25000,
                    "urgency_level": "week",
                    "location": {
                        "full_location": "Miami, FL 33101",
                        "city": "Miami",
                        "state": "FL",
                        "zip_code": "33101"
                    },
                    "contractor_requirements": {
                        "contractor_count": 8,
                        "specialties_required": ["solar panel installation"]
                    }
                }
            else:
                result = self.supabase.table("bid_cards").select("*").eq("id", bid_card_id).single().execute()

                if not result.data:
                    return {
                        "success": False,
                        "error": f"No bid card found for ID: {bid_card_id}"
                    }

                bid_card = result.data
                bid_data = bid_card.get("bid_document", {}).get("all_extracted_data", {})

            print(f"[CDA] Loaded bid card: {bid_card['bid_card_number']}")
            print(f"[CDA] Project: {bid_data.get('project_type', 'unknown')}")
            print(f"[CDA] Location: {bid_data.get('location', {}).get('full_location', 'unknown')}")
            print(f"[CDA] Budget: ${bid_data.get('budget_min', 0)}-${bid_data.get('budget_max', 0)}")

            # Step 2: Execute 3-tier discovery
            all_contractors = []
            tier_results = {
                "tier_1_matches": [],
                "tier_2_matches": [],
                "tier_3_sources": []
            }

            # Tier 1: Internal contractor matching
            print("\n[CDA] Executing Tier 1: Internal contractor matching...")
            tier1_contractors = self.tier1_matcher.find_matching_contractors(bid_data)
            all_contractors.extend(tier1_contractors)
            tier_results["tier_1_matches"] = tier1_contractors
            print(f"[CDA] Tier 1 found: {len(tier1_contractors)} contractors")

            # Tier 2: Re-engagement (only if we need more contractors)
            contractors_needed = bid_card.get("contractor_count_needed", 3)
            if len(all_contractors) < contractors_needed:
                print(f"\n[CDA] Executing Tier 2: Re-engagement (need {contractors_needed - len(all_contractors)} more)...")
                tier2_contractors = self.tier2_reengagement.find_reengagement_candidates(bid_data)
                all_contractors.extend(tier2_contractors)
                tier_results["tier_2_matches"] = tier2_contractors
                print(f"[CDA] Tier 2 found: {len(tier2_contractors)} contractors")

            # Tier 3: External sourcing (only if we still need more)
            if len(all_contractors) < contractors_needed:
                print(f"\n[CDA] Executing Tier 3: External sourcing (need {contractors_needed - len(all_contractors)} more)...")

                # Use web search agent to find actual contractors
                web_search_result = self.web_search_agent.discover_contractors_for_bid(
                    bid_card_id, contractors_needed - len(all_contractors)
                )

                if web_search_result["success"]:
                    # Convert potential contractors to standard format
                    tier3_contractors = []
                    for contractor in web_search_result["contractors"]:
                        tier3_contractor = {
                            "id": contractor["id"],
                            "discovery_tier": 3,
                            "company_name": contractor["company_name"],
                            "contact_name": contractor.get("contact_name"),
                            "email": contractor.get("email"),
                            "phone": contractor.get("phone"),
                            "website": contractor.get("website"),
                            "address": contractor.get("address"),
                            "city": contractor.get("city"),
                            "state": contractor.get("state"),
                            "zip_code": contractor.get("zip_code"),
                            "specialties": contractor.get("specialties", []),
                            "rating": contractor.get("google_rating", 0.0),
                            "review_count": contractor.get("google_review_count", 0),
                            "years_in_business": contractor.get("years_in_business"),
                            "match_score": contractor.get("match_score", 50.0),
                            "match_reasons": [
                                f"Found via {contractor['discovery_source']}",
                                f"Search rank #{contractor.get('search_rank', 'Unknown')}",
                                f"{contractor.get('google_rating', 'No')} star rating" if contractor.get("google_rating") else "Web directory listing"
                            ],
                            "onboarded": False,
                            "external_data": {
                                "source": contractor["discovery_source"],
                                "source_query": contractor["source_query"],
                                "google_place_id": contractor.get("google_place_id"),
                                "distance_miles": contractor.get("distance_miles")
                            }
                        }
                        tier3_contractors.append(tier3_contractor)

                    all_contractors.extend(tier3_contractors)
                    tier_results["tier_3_matches"] = tier3_contractors
                    print(f"[CDA] Tier 3 web search found: {len(tier3_contractors)} contractors")
                else:
                    # Fallback to old tier3 scraper for source identification
                    tier3_sources = self.tier3_scraper.identify_external_sources(bid_data)
                    tier_results["tier_3_sources"] = tier3_sources
                    print(f"[CDA] Tier 3 fallback identified: {len(tier3_sources)} external sources")

            # Step 3: Score and rank all contractors
            print(f"\n[CDA] Scoring and ranking {len(all_contractors)} contractors...")
            scored_contractors = self.scorer.score_contractors(all_contractors, bid_data)

            # Step 4: Select top contractors
            final_contractors = scored_contractors[:contractors_needed]

            # Step 5: Cache discovery results
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            cache_record = {
                "bid_card_id": bid_card_id,
                "tier_1_matches": tier_results["tier_1_matches"],
                "tier_2_matches": tier_results["tier_2_matches"],
                "tier_3_sources": tier_results["tier_3_sources"],
                "discovery_status": "completed",
                "total_contractors_found": len(all_contractors),
                "processing_time_ms": processing_time
            }

            print("[CDA] Caching discovery results...")
            cache_result = self.supabase.table("contractor_discovery_cache").insert(cache_record).execute()

            # Step 6: Return results
            print(f"\n[CDA] SUCCESS: Discovery completed in {processing_time}ms")
            print(f"[CDA] Found {len(all_contractors)} total contractors")
            print(f"[CDA] Returning top {len(final_contractors)} contractors")
            print(f"[CDA] Tier breakdown: T1={len(tier_results['tier_1_matches'])}, T2={len(tier_results['tier_2_matches'])}, T3={len(tier_results['tier_3_sources'])}")

            return {
                "success": True,
                "bid_card_id": bid_card_id,
                "contractors_found": final_contractors,
                "tier_breakdown": {
                    "tier_1_count": len(tier_results["tier_1_matches"]),
                    "tier_2_count": len(tier_results["tier_2_matches"]),
                    "tier_3_count": len(tier_results["tier_3_sources"]),
                    "total_found": len(all_contractors)
                },
                "processing_time_ms": processing_time,
                "cache_id": cache_result.data[0]["id"] if cache_result.data else None
            }

        except Exception as e:
            print(f"[CDA ERROR] Failed to discover contractors: {e}")
            import traceback
            traceback.print_exc()

            # Log failure to cache
            try:
                processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
                cache_record = {
                    "bid_card_id": bid_card_id,
                    "discovery_status": "failed",
                    "total_contractors_found": 0,
                    "processing_time_ms": processing_time
                }
                self.supabase.table("contractor_discovery_cache").insert(cache_record).execute()
            except:
                pass

            return {
                "success": False,
                "error": str(e)
            }

    def get_discovery_cache(self, bid_card_id: str) -> Optional[dict[str, Any]]:
        """Get cached discovery results for a bid card"""
        try:
            result = self.supabase.table("contractor_discovery_cache").select("*").eq("bid_card_id", bid_card_id).order("created_at", desc=True).limit(1).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            print(f"[CDA ERROR] Failed to get discovery cache: {e}")
            return None


# Test the CDA agent
if __name__ == "__main__":
    cda = ContractorDiscoveryAgent()

    # Test with a bid card ID (will need to be replaced with real ID)
    # For now, we'll test the initialization
    print("\n✅ CDA Agent initialized successfully")
    print("Ready for contractor discovery operations")
