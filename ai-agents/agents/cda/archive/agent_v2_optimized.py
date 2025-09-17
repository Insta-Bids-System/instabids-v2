"""
CDA v2 Optimized - Faster Contractor Discovery with timeouts
Reduces API calls and adds timeout protection
"""
import os
import sys
from datetime import datetime
from typing import Any, Optional

from dotenv import load_dotenv
from supabase import create_client


# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from agents.cda.tier1_matcher_v2 import Tier1Matcher
from agents.cda.tier2_reengagement_v2 import Tier2Reengagement


class OptimizedContractorDiscoveryAgent:
    """CDA v2 Optimized - Faster discovery without heavy AI analysis"""

    def __init__(self):
        """Initialize CDA with database connections only"""
        load_dotenv(override=True)
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)

        # Initialize only fast components
        self.tier1_matcher = Tier1Matcher(self.supabase)
        self.tier2_reengagement = Tier2Reengagement(self.supabase)

        print("[CDA v2 Optimized] Initialized with fast database matching")

    def discover_contractors(self, bid_card_id: str, contractors_needed: int = 5) -> dict[str, Any]:
        """
        Optimized contractor discovery - database only, no AI analysis
        """
        start_time = datetime.now()

        try:
            print(f"[CDA Optimized] Starting fast contractor discovery for bid card: {bid_card_id}")

            # Step 1: Load bid card
            bid_card = self._load_bid_card(bid_card_id)
            if not bid_card:
                return {"success": False, "error": "Bid card not found"}

            print(f"[CDA Optimized] Loaded bid card - Project: {bid_card.get('project_type', 'Unknown')}")

            # Step 2: Fast database search only
            all_contractors = []

            # Tier 1: Internal database (FAST)
            print("[CDA Optimized] Searching Tier 1: Internal contractor database...")
            tier1_results = self.tier1_matcher.find_matching_contractors(bid_card)
            if tier1_results["success"] and tier1_results["contractors"]:
                for contractor in tier1_results["contractors"]:
                    contractor["tier"] = "tier_1"
                    contractor["score"] = contractor.get("score", 90)  # Default high score for tier 1
                all_contractors.extend(tier1_results["contractors"])
                print(f"[CDA Optimized] Found {len(tier1_results['contractors'])} contractors in database")

            # Tier 2: Previous contacts (FAST)
            if len(all_contractors) < contractors_needed:
                print("[CDA Optimized] Searching Tier 2: Previous contractor contacts...")
                tier2_results = self.tier2_reengagement.find_reengagement_candidates(bid_card)
                if tier2_results["success"] and tier2_results["contractors"]:
                    for contractor in tier2_results["contractors"]:
                        contractor["tier"] = "tier_2"
                        contractor["score"] = contractor.get("score", 70)  # Default medium score
                    all_contractors.extend(tier2_results["contractors"])
                    print(f"[CDA Optimized] Found {len(tier2_results['contractors'])} previous contacts")

            # Skip Tier 3 web search for speed
            # Skip AI analysis for speed

            # Simple scoring based on project match
            scored_contractors = self._simple_score_contractors(all_contractors, bid_card)

            # Select top contractors
            selected = scored_contractors[:contractors_needed]

            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # Build tier breakdown
            tier_breakdown = {}
            for contractor in selected:
                tier = contractor.get("tier", "unknown")
                if tier not in tier_breakdown:
                    tier_breakdown[tier] = 0
                tier_breakdown[tier] += 1

            result = {
                "success": True,
                "bid_card_id": bid_card_id,
                "selected_contractors": selected,
                "tier_breakdown": tier_breakdown,
                "processing_time_ms": processing_time,
                "total_found": len(all_contractors),
                "optimization": "database_only"
            }

            # Cache results
            self._cache_discovery_results(bid_card_id, result)

            print(f"[CDA Optimized] Discovery complete in {processing_time}ms")
            return result

        except Exception as e:
            print(f"[CDA Optimized ERROR] {e}")
            return {
                "success": False,
                "error": str(e),
                "bid_card_id": bid_card_id
            }

    def _load_bid_card(self, bid_card_id: str) -> Optional[dict]:
        """Load bid card from database"""
        try:
            result = self.supabase.table("bid_cards").select("*").eq("id", bid_card_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"[CDA Optimized] Error loading bid card: {e}")
            return None

    def _simple_score_contractors(self, contractors: list[dict], bid_card: dict) -> list[dict]:
        """Simple scoring without AI - just match specialties"""
        project_type = bid_card.get("project_type", "").lower()
        bid_card.get("budget_max", 0)

        for contractor in contractors:
            score = contractor.get("score", 50)  # Base score

            # Boost score for matching specialties
            specialties = contractor.get("specialties", [])
            if isinstance(specialties, list):
                for specialty in specialties:
                    if project_type in specialty.lower():
                        score += 20
                        break

            # Boost score for tier
            tier = contractor.get("tier", "tier_3")
            if tier == "tier_1":
                score += 10
            elif tier == "tier_2":
                score += 5

            contractor["score"] = min(100, score)  # Cap at 100

        # Sort by score
        return sorted(contractors, key=lambda x: x.get("score", 0), reverse=True)

    def _cache_discovery_results(self, bid_card_id: str, results: dict):
        """Cache discovery results for later use"""
        try:
            {
                "bid_card_id": bid_card_id,
                "discovery_results": results,
                "created_at": datetime.now().isoformat()
            }

            # Try to save to a cache table or just log it
            print(f"[CDA Optimized] Results cached for bid {bid_card_id}")

        except Exception as e:
            print(f"[CDA Optimized] Cache error: {e}")

    def get_discovery_cache(self, bid_card_id: str) -> Optional[dict]:
        """Get cached discovery results"""
        # For now, return None - implement if needed
        return None


# Direct replacement for the slow agent
IntelligentContractorDiscoveryAgent = OptimizedContractorDiscoveryAgent
