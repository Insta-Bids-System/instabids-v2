"""
CDA v2 - Intelligent Contractor Discovery Agent
Powered by GPT-4 for nuanced matching decisions
"""
import json
import os
import sys
from datetime import datetime
from typing import Any, Optional

from dotenv import load_dotenv
from supabase import create_client


# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from agents.cda.service_specific_matcher import ServiceSpecificMatcher
from agents.cda.tier1_matcher_v2 import Tier1Matcher
from agents.cda.tier2_reengagement import Tier2Reengagement
from agents.cda.web_search_agent import WebSearchContractorAgent
from agents.cda.enhanced_web_search_agent import EnhancedWebSearchAgent
from agents.cda.adaptive_discovery import AdaptiveDiscoverySystem


class ContractorDiscoveryAgent:
    """CDA v2 - Uses GPT-4 for intelligent contractor matching"""

    def __init__(self):
        """Initialize CDA with GPT-4 brain and data sources"""
        load_dotenv(override=True)
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)

        # Initialize components
        try:
            self.service_matcher = ServiceSpecificMatcher()
            print("[CDA v2] Initialized with GPT-4 service-specific matching")
        except Exception as e:
            print(f"[CDA v2] Service matcher unavailable: {e}")
            self.service_matcher = None

        self.intelligent_matcher = None  # Legacy matcher disabled
        self.web_search = WebSearchContractorAgent(self.supabase)
        self.enhanced_web_search = EnhancedWebSearchAgent(self.supabase)  # New 66-field system
        self.tier1_matcher = Tier1Matcher(self.supabase)
        self.tier2_reengagement = Tier2Reengagement(self.supabase)
        self.adaptive_discovery = AdaptiveDiscoverySystem()  # Radius expansion system

        print("[CDA v2] Initialized with enhanced service-specific matching and adaptive discovery")

    async def discover_contractors(self, bid_card_id: str, contractors_needed: int = 5, radius_miles: int = 15) -> dict[str, Any]:
        """
        Main CDA function with intelligent matching and radius-based search

        Process:
        1. Load bid card data
        2. Calculate how many contractors to actually contact (5-to-1 ratio)
        3. Search for contractors (3-tier system with radius filtering)
        4. Score each contractor
        5. Select best matches with explanations
        
        Args:
            bid_card_id: ID of the bid card to process
            contractors_needed: Number of BIDS needed (default: 5)
            radius_miles: Search radius in miles for Tier 1 & 2 (default: 15)
        """
        try:
            print(f"[CDA v2] Starting intelligent contractor discovery for bid card: {bid_card_id} (radius: {radius_miles} miles)")

            # Step 1: Load bid card
            bid_card = self._load_bid_card(bid_card_id)
            if not bid_card:
                return {"success": False, "error": "Bid card not found"}

            print(f"[CDA v2] Loaded bid card - Project: {bid_card.get('project_type', 'Unknown')}")

            # Step 2: Calculate how many contractors to actually contact
            # Based on urgency level and the 5/10/15 rule
            bids_needed = bid_card.get("contractor_count_needed", contractors_needed)
            urgency = bid_card.get("urgency_level", "week")

            # Calculate contractors to contact based on response rates
            # Tier 1: 90% response rate (internal contractors)
            # Tier 2: 50% response rate (previous contacts)
            # Tier 3: 20% response rate (cold outreach)
            # Average blended rate ~33% for mixed tiers

            # For now, use simple 5-to-1 ratio (20% response rate assumption)
            contractors_to_find = bids_needed * 5

            print(f"[CDA v2] Need {bids_needed} bids, targeting {contractors_to_find} contractors")
            print(f"[CDA v2] Urgency level: {urgency}")

            # Step 3: Intelligent project analysis using OpenAI GPT-4
            print("[CDA v2] Analyzing project requirements with GPT-4...")

            # Format location properly for the tier matchers
            location = {
                "city": bid_card.get("location_city", ""),
                "state": bid_card.get("location_state", ""),
                "zip_code": bid_card.get("location_zip", "")
            }

            # Also update the bid_card with the formatted location for tier matchers
            bid_card["location"] = location

            # Use service-specific matcher for intelligent analysis
            if self.service_matcher:
                project_analysis = self.service_matcher.analyze_project_requirements(bid_card)
                print("[CDA v2] Intelligent Analysis Complete:")
                print(f"  - Service Category: {project_analysis.get('service_category', 'Unknown')}")
                print(f"  - Service Type: {project_analysis.get('service_type', 'Unknown')}")
                print(f"  - Specialization Required: {project_analysis.get('specialization_required', [])}")
                print(f"  - Scope Complexity: {project_analysis.get('scope_complexity', 'Unknown')}")
            else:
                # Fallback to simple analysis
                project_analysis = {
                    "service_category": bid_card.get("project_type", "Unknown"),
                    "service_type": "general",
                    "specialization_required": [],
                    "urgency_indicators": [],
                    "quality_preferences": "balanced",
                    "scope_complexity": "moderate",
                    "contractor_requirements": []
                }
                print("[CDA v2] Using fallback analysis (service matcher unavailable)")

            # Include original bid analysis structure for compatibility
            bid_analysis = {
                "contractor_size_preference": "any",
                "quality_vs_price_balance": project_analysis.get("quality_preferences", "balanced"),
                "trust_factors": ["reviews", "local"],
                "project_type": bid_card.get("project_type", "Unknown"),
                "location": location,
                "bids_needed": bids_needed,
                "contractors_to_find": contractors_to_find,
                "service_analysis": project_analysis  # Include intelligent analysis
            }

            # Step 3: Gather contractors from all sources
            all_contractors = []

            # Tier 1: Internal database with radius search
            print(f"[CDA v2] Searching Tier 1: Internal contractor database within {radius_miles} miles...")
            tier1_results = self.tier1_matcher.find_matching_contractors(bid_card, radius_miles=radius_miles)
            if tier1_results["success"] and tier1_results["contractors"]:
                all_contractors.extend(tier1_results["contractors"])
                print(f"[CDA v2] Found {len(tier1_results['contractors'])} internal contractors within radius")
            else:
                print(f"[CDA v2] No internal contractors found within {radius_miles} miles")

            # Tier 2: Previous contacts with radius search
            print(f"[CDA v2] Searching Tier 2: Previous contractor contacts within {radius_miles} miles...")
            tier2_results = self.tier2_reengagement.find_reengagement_candidates(bid_card, radius_miles=radius_miles)
            if tier2_results and len(tier2_results) > 0:
                all_contractors.extend(tier2_results)
                print(f"[CDA v2] Found {len(tier2_results)} previous contacts within radius")
            else:
                print(f"[CDA v2] No previous contacts found within {radius_miles} miles")

            # Tier 3: Enhanced web search with adaptive radius expansion
            if len(all_contractors) < contractors_to_find:  # Get the full amount we need
                print(f"[CDA v2] Searching Tier 3: Enhanced web search with adaptive radius expansion...")
                # Search for remaining contractors needed
                remaining_needed = contractors_to_find - len(all_contractors)
                
                # Use adaptive discovery with automatic radius expansion
                async def discovery_wrapper(location_dict, radius):
                    """Wrapper to make the discovery function compatible with adaptive discovery"""
                    try:
                        enhanced_results = await self.enhanced_web_search.discover_contractors_with_profiles(
                            bid_card_id=bid_card_id,
                            project_type=project_type,
                            location=location_dict,
                            contractors_needed=remaining_needed,
                            radius_miles=radius
                        )
                        if enhanced_results["success"]:
                            return enhanced_results["contractors"]
                    except:
                        # Fallback to regular web search if enhanced fails
                        web_results = self.web_search.discover_contractors_for_bid(
                            bid_card_id,
                            contractors_needed=remaining_needed,
                            radius_miles=radius
                        )
                        if web_results["success"]:
                            return web_results["contractors"]
                    return []
                
                # Use adaptive discovery with radius expansion
                discovery_result = await self.adaptive_discovery.discover_with_expansion(
                    discovery_function=discovery_wrapper,
                    location=location,
                    target_count=remaining_needed,
                    min_acceptable=max(1, remaining_needed // 2)  # Accept at least half
                )
                
                if discovery_result["contractors"]:
                    all_contractors.extend(discovery_result["contractors"])
                    print(f"[CDA v2] Found {len(discovery_result['contractors'])} contractors via adaptive discovery")
                    print(f"[CDA v2] Final radius used: {discovery_result['final_radius']} miles")
                    if discovery_result["expansion_stages"] > 1:
                        print(f"[CDA v2] Expanded search {discovery_result['expansion_stages'] - 1} times")

            # Remove duplicates
            unique_contractors = self._deduplicate_contractors(all_contractors)
            print(f"[CDA v2] Total unique contractors found: {len(unique_contractors)}")

            if not unique_contractors:
                return {
                    "success": False,
                    "error": "No contractors found",
                    "bid_analysis": bid_analysis
                }

            # Step 4: Intelligent scoring using GPT-4 service-specific matching
            print(f"[CDA v2] Scoring {len(unique_contractors)} contractors with intelligent service matching...")

            # Score each contractor using service-specific analysis
            for contractor in unique_contractors:
                if self.service_matcher:
                    try:
                        # Get intelligent scoring based on service requirements
                        scoring_result = self.service_matcher.score_contractor_match(contractor, project_analysis)

                        # Apply the intelligent scoring
                        contractor["match_score"] = scoring_result.get("match_score", 50)
                        contractor["recommendation"] = scoring_result.get("recommendation", "possible_match")
                        contractor["reasoning"] = scoring_result.get("reasoning", "Intelligent analysis")
                        contractor["key_strengths"] = scoring_result.get("key_strengths", [])
                        contractor["concerns"] = scoring_result.get("concerns", [])
                        contractor["specialization_match"] = scoring_result.get("specialization_match", "moderate")

                        print(f"[CDA v2] Intelligent score for {contractor.get('company_name', 'Unknown')}: {contractor['match_score']}")

                    except Exception as e:
                        print(f"[CDA v2] Error in intelligent scoring for {contractor.get('company_name', 'Unknown')}: {e}")
                        # Fallback to simple scoring
                        self._apply_simple_scoring(contractor)
                else:
                    # Fallback to simple scoring when service matcher unavailable
                    self._apply_simple_scoring(contractor)

            # Sort by score and select top matches
            unique_contractors.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            # Select the number we calculated we need to contact, not just the bids needed
            selected = unique_contractors[:contractors_to_find]

            selection_result = {
                "selected_contractors": selected,
                "all_scores": [
                    {
                        "name": c.get("company_name"),
                        "score": c.get("match_score"),
                        "recommendation": c.get("recommendation")
                    }
                    for c in unique_contractors
                ]
            }

            # Step 5: Simple explanation without LLM
            explanation = f"Selected {len(selected)} contractors to contact for {bids_needed} needed bids (using 5-to-1 ratio). Top matches have the best combination of customer ratings and established business presence."

            # Step 6: Store the selected contractors with match data
            stored_contractors = self._store_matched_contractors(
                selection_result["selected_contractors"],
                bid_card_id,
                bid_analysis
            )

            # Return comprehensive results with radius info
            result = {
                "success": True,
                "bid_card_id": bid_card_id,
                "search_radius_miles": radius_miles,
                "bid_analysis": bid_analysis,
                "total_found": len(unique_contractors),
                "selected_count": len(selection_result["selected_contractors"]),
                "selected_contractors": selection_result["selected_contractors"],
                "explanation": explanation,
                "all_scores": selection_result["all_scores"],
                "stored_ids": stored_contractors,
                "tier_results": {
                    "tier1_internal": len(tier1_results.get("contractors", [])) if tier1_results.get("success") else 0,
                    "tier2_previous": len(tier2_results) if tier2_results else 0,
                    "tier3_web": len(web_results.get("contractors", [])) if "web_results" in locals() and web_results.get("success") else 0
                }
            }

            print(f"[CDA v2] Discovery complete - Selected {len(selection_result['selected_contractors'])} contractors to contact")
            print(f"[CDA v2] Target: {bids_needed} bids from {contractors_to_find} contractors within {radius_miles} mile radius")
            print(f"[CDA v2] Explanation: {explanation}")

            return result

        except Exception as e:
            print(f"[CDA v2 ERROR] Discovery failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "bid_card_id": bid_card_id
            }

    def _load_bid_card(self, bid_card_id: str) -> Optional[dict[str, Any]]:
        """Load bid card from database or test data"""
        # Handle test bid cards
        if bid_card_id == "test-mom-and-pop-kitchen":
            return {
                "id": bid_card_id,
                "project_type": "kitchen remodel",
                "bid_document": {
                    "project_overview": {
                        "description": "We want to update our kitchen but keep the family feel. Looking for someone we can trust, not a big corporation. Our last contractor was terrible - took forever and overcharged us."
                    },
                    "budget_information": {
                        "budget_min": 8000,
                        "budget_max": 12000,
                        "notes": "We have some flexibility but want good value"
                    },
                    "timeline": {
                        "urgency_level": "month",
                        "notes": "Want it done right, not rushed"
                    }
                },
                "location_city": "Coconut Creek",
                "location_state": "FL",
                "location_zip": "33442",
                "contractor_count_needed": 5
            }
        elif bid_card_id == "test-emergency-roof-repair":
            return {
                "id": bid_card_id,
                "project_type": "roofing",
                "bid_document": {
                    "project_overview": {
                        "description": "I have a leak in my roof after the storm last week. Need emergency repair to fix the damaged shingles and prevent water damage. This is urgent."
                    },
                    "timeline": {
                        "urgency_level": "emergency",
                        "notes": "Need this fixed immediately before more damage occurs"
                    }
                },
                "location_city": "Coconut Creek",
                "location_state": "FL",
                "location_zip": "33442",
                "contractor_count_needed": 5
            }
        elif bid_card_id == "test-pool-maintenance":
            return {
                "id": bid_card_id,
                "project_type": "pool maintenance",
                "bid_document": {
                    "project_overview": {
                        "description": "Need regular pool cleaning and maintenance service. Chemical balancing, filter cleaning, and weekly service."
                    },
                    "budget_information": {
                        "budget_min": 150,
                        "budget_max": 300,
                        "notes": "Monthly service budget"
                    },
                    "timeline": {
                        "urgency_level": "standard",
                        "notes": "Start within a week"
                    }
                },
                "location_city": "Fort Lauderdale",
                "location_state": "FL",
                "location_zip": "33301",
                "contractor_count_needed": 4
            }
        elif bid_card_id == "test-kitchen-installation":
            return {
                "id": bid_card_id,
                "project_type": "kitchen remodel",
                "bid_document": {
                    "project_overview": {
                        "description": "Complete kitchen remodel with new cabinets, countertops, appliances, and flooring. Looking for full installation services from start to finish."
                    },
                    "timeline": {
                        "urgency_level": "month",
                        "notes": "Want professional installation team"
                    }
                },
                "location_city": "Coconut Creek",
                "location_state": "FL",
                "location_zip": "33442",
                "contractor_count_needed": 4
            }
        elif bid_card_id == "test-plumbing-maintenance":
            return {
                "id": bid_card_id,
                "project_type": "plumbing",
                "bid_document": {
                    "project_overview": {
                        "description": "Regular plumbing maintenance service needed. Check all fixtures, inspect pipes, and ongoing maintenance contract."
                    },
                    "timeline": {
                        "urgency_level": "week",
                        "notes": "Looking for ongoing service relationship"
                    }
                },
                "location_city": "Coconut Creek",
                "location_state": "FL",
                "location_zip": "33442",
                "contractor_count_needed": 3
            }

        # Load from database
        try:
            result = self.supabase.table("bid_cards").select("*").eq("id", bid_card_id).single().execute()
            return result.data if result.data else None
        except:
            return None

    def _deduplicate_contractors(self, contractors: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate contractors based on company name"""
        seen = set()
        unique = []

        for contractor in contractors:
            name = contractor.get("company_name", "").lower().strip()
            if name and name not in seen:
                seen.add(name)
                unique.append(contractor)

        return unique

    def _store_matched_contractors(self,
                                 contractors: list[dict[str, Any]],
                                 bid_card_id: str,
                                 bid_analysis: dict[str, Any]) -> list[str]:
        """Store selected contractors with intelligent match data"""
        stored_ids = []

        try:
            for contractor in contractors:
                # Prepare match record
                match_record = {
                    "bid_card_id": bid_card_id,
                    "contractor_id": contractor.get("id"),
                    "company_name": contractor.get("company_name"),
                    "match_score": contractor.get("match_score", 0),
                    "recommendation": contractor.get("recommendation", "unknown"),
                    "reasoning": contractor.get("reasoning", ""),
                    "key_strengths": json.dumps(contractor.get("key_strengths", [])),
                    "concerns": json.dumps(contractor.get("concerns", [])),
                    "bid_analysis": json.dumps(bid_analysis),
                    "created_at": datetime.now().isoformat()
                }

                # Store in contractor_bid_matches table (create if needed)
                result = self.supabase.table("contractor_bid_matches").insert(match_record).execute()

                if result.data:
                    stored_ids.append(result.data[0]["id"])
                    print(f"[CDA v2] Stored match: {contractor.get('company_name')} - Score: {contractor.get('match_score')}")

        except Exception as e:
            print(f"[CDA v2] Note: contractor_bid_matches table may not exist yet - {e}")
            # Continue anyway - main functionality still works

        return stored_ids

    def _apply_simple_scoring(self, contractor: dict[str, Any]) -> None:
        """Apply simple scoring as fallback when intelligent matching unavailable"""
        score = 70  # Base score
        if contractor.get("google_rating", 0) >= 4.5:
            score += 10
        if contractor.get("google_review_count", 0) >= 50:
            score += 10
        if contractor.get("website"):
            score += 5
        if contractor.get("email"):
            score += 5

        contractor["match_score"] = min(score, 100)
        contractor["recommendation"] = "good_match" if score >= 80 else "possible_match"
        contractor["reasoning"] = f"Basic scoring based on rating ({contractor.get('google_rating', 'N/A')}), reviews ({contractor.get('google_review_count', 0)}), and online presence"
        contractor["key_strengths"] = ["Local contractor", "Established business"]
        contractor["concerns"] = ["Limited specialization analysis"]


# Test the intelligent CDA
if __name__ == "__main__":
    print("TESTING INTELLIGENT CDA WITH OPENAI GPT-4")
    print("=" * 60)

    agent = ContractorDiscoveryAgent()

    # Test with mom & pop preference bid card with 15-mile radius
    result = agent.discover_contractors(
        bid_card_id="test-mom-and-pop-kitchen",
        contractors_needed=3,
        radius_miles=15
    )

    if result["success"]:
        print("\nSUCCESS - Intelligent Matching Results:")
        print(f"Total contractors found: {result['total_found']}")
        print(f"Selected: {result['selected_count']}")
        print(f"\nCustomer Explanation:\n{result['explanation']}")

        print("\nSelected Contractors:")
        for contractor in result["selected_contractors"]:
            print(f"\n{contractor.get('contractor_name', 'Unknown')}:")
            print(f"  Score: {contractor.get('match_score', 0)}")
            print(f"  Recommendation: {contractor.get('recommendation', 'Unknown')}")
            print(f"  Reasoning: {contractor.get('reasoning', 'No reasoning provided')}")
    else:
        print(f"\nERROR: {result.get('error', 'Unknown error')}")
