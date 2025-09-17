"""
IMPROVED Tier 1 Matcher - Enrich FIRST, Then Categorize
Fixes the backwards logic of guessing size from reviews before enrichment
"""
import os
import sys
from typing import Any, Dict, List, Optional
import asyncio
import aiohttp
from bs4 import BeautifulSoup

from supabase import Client

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.radius_search_fixed import calculate_distance_miles, get_zip_codes_in_radius


class ImprovedTier1Matcher:
    """
    CORRECT FLOW:
    1. Discovery - Get ALL contractors (no size filtering)
    2. Enrichment - Scrape websites for REAL data
    3. Size Analysis - Determine size from ACTUAL data
    4. Filtering - Apply size preference with ±1 flexibility
    """
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    async def find_and_enrich_contractors(
        self, 
        bid_data: dict[str, Any], 
        radius_miles: int = 15,
        contractors_needed: int = 20
    ) -> dict[str, Any]:
        """
        Complete discovery flow with enrichment FIRST
        """
        print("\n[IMPROVED FLOW] Starting CORRECT contractor discovery")
        
        # Step 1: Extract requirements
        project_type = bid_data.get("project_type", "").lower()
        location = self._extract_location(bid_data)
        zip_code = location.get("zip_code", "")
        size_preference = self._extract_size_preference(bid_data)
        
        print(f"[STEP 1] Project: {project_type} in {zip_code}")
        print(f"[STEP 1] Size preference: {size_preference}")
        
        # Step 2: Discovery WITHOUT size filtering
        all_contractors = await self._discover_all_contractors(
            project_type,
            location, 
            radius_miles,
            contractors_needed * 2  # Get extra for filtering later
        )
        print(f"\n[STEP 2] Discovered {len(all_contractors)} contractors (no size filter yet)")
        
        # Step 3: ENRICHMENT - Get real data from websites
        enriched_contractors = await self._enrich_contractors(all_contractors)
        print(f"\n[STEP 3] Enriched {len(enriched_contractors)} contractors with website data")
        
        # Step 4: Size Analysis using REAL data
        analyzed_contractors = self._analyze_contractor_sizes(enriched_contractors)
        print(f"\n[STEP 4] Analyzed sizes based on REAL data:")
        size_breakdown = {}
        for c in analyzed_contractors:
            size = c.get('actual_size', 'unknown')
            size_breakdown[size] = size_breakdown.get(size, 0) + 1
        for size, count in size_breakdown.items():
            print(f"  - {size}: {count} contractors")
        
        # Step 5: Apply size filtering with ±1 flexibility
        filtered_contractors = self._filter_by_size_preference(
            analyzed_contractors,
            size_preference
        )
        print(f"\n[STEP 5] Filtered to {len(filtered_contractors)} contractors matching size preference")
        
        # Step 6: Select final contractors
        selected_contractors = filtered_contractors[:contractors_needed]
        
        return {
            "success": True,
            "total_discovered": len(all_contractors),
            "total_enriched": len(enriched_contractors),
            "total_analyzed": len(analyzed_contractors),
            "total_filtered": len(filtered_contractors),
            "selected_contractors": selected_contractors,
            "size_breakdown": size_breakdown,
            "discovery_method": "enrichment_first"
        }
    
    async def _discover_all_contractors(
        self,
        project_type: str,
        location: dict,
        radius_miles: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Discovery WITHOUT size filtering - get ALL contractors
        """
        zip_code = location.get("zip_code", "")
        if not zip_code:
            return []
        
        # Get zip codes in radius
        target_zip_codes = get_zip_codes_in_radius(zip_code, radius_miles)
        
        # Query contractor_leads WITHOUT size filtering
        query = self.supabase.table("contractor_leads").select("*")
        
        # Basic filters only
        query = query.in_("lead_status", ["qualified", "contacted", "new"])
        
        # Location filter
        if location.get("state"):
            query = query.eq("state", location["state"])
        
        # Order by quality
        query = query.order("rating", desc=True)
        query = query.order("review_count", desc=True)
        query = query.limit(limit)
        
        result = query.execute()
        contractors = result.data if result.data else []
        
        # Filter by radius
        filtered = []
        for contractor in contractors:
            c_zip = contractor.get("zip_code", "")
            if c_zip and c_zip in target_zip_codes:
                distance = calculate_distance_miles(zip_code, c_zip)
                contractor["distance_miles"] = distance
                filtered.append(contractor)
        
        return filtered
    
    async def _enrich_contractors(self, contractors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich contractors with REAL website data
        """
        enriched = []
        
        async with aiohttp.ClientSession() as session:
            for contractor in contractors[:20]:  # Limit for performance
                website = contractor.get("website", "")
                
                if website:
                    print(f"[ENRICHING] {contractor.get('company_name')} - {website}")
                    website_data = await self._scrape_website(session, website)
                    
                    # Add REAL data to contractor
                    contractor.update({
                        "team_size": website_data.get("team_size"),
                        "years_in_business": website_data.get("years_in_business"),
                        "about_text": website_data.get("about_text"),
                        "office_locations": website_data.get("office_locations"),
                        "certifications": website_data.get("certifications"),
                        "service_areas": website_data.get("service_areas"),
                        "fleet_mentions": website_data.get("fleet_mentions"),
                        "warehouse_mentions": website_data.get("warehouse_mentions"),
                        "enrichment_complete": True
                    })
                else:
                    contractor["enrichment_complete"] = False
                
                enriched.append(contractor)
        
        return enriched
    
    async def _scrape_website(self, session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
        """
        Extract REAL size indicators from website
        """
        try:
            async with session.get(url, timeout=5) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract real indicators
                text_content = soup.get_text().lower()
                
                # Look for team size mentions
                team_size = None
                if "team of" in text_content:
                    # Extract number after "team of"
                    import re
                    match = re.search(r'team of (\d+)', text_content)
                    if match:
                        team_size = int(match.group(1))
                
                # Look for years in business
                years = None
                if "serving since" in text_content or "established" in text_content:
                    match = re.search(r'(since|established) (\d{4})', text_content)
                    if match:
                        years = 2025 - int(match.group(2))
                
                # Look for multiple locations
                locations = []
                if "locations" in text_content or "offices" in text_content:
                    locations = ["main", "branch"]  # Simplified
                
                # Look for fleet/warehouse mentions
                fleet = "fleet" in text_content or "trucks" in text_content
                warehouse = "warehouse" in text_content or "facility" in text_content
                
                return {
                    "team_size": team_size,
                    "years_in_business": years,
                    "about_text": text_content[:500],  # First 500 chars
                    "office_locations": locations,
                    "certifications": [],  # Would need more parsing
                    "service_areas": [],  # Would need more parsing
                    "fleet_mentions": fleet,
                    "warehouse_mentions": warehouse
                }
        except:
            return {}
    
    def _analyze_contractor_sizes(self, contractors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Determine ACTUAL size from enriched website data
        """
        for contractor in contractors:
            if contractor.get("enrichment_complete"):
                # Use REAL data to determine size
                team_size = contractor.get("team_size", 0) or 0
                years = contractor.get("years_in_business", 0) or 0
                locations = len(contractor.get("office_locations", []))
                fleet = contractor.get("fleet_mentions", False)
                warehouse = contractor.get("warehouse_mentions", False)
                
                # ACCURATE size determination from REAL data
                if team_size > 50 or locations > 3:
                    contractor["actual_size"] = "enterprise"
                elif team_size > 20 or locations > 1 or (fleet and warehouse):
                    contractor["actual_size"] = "regional_company"
                elif team_size > 5 or years > 10:
                    contractor["actual_size"] = "small_business"
                elif team_size > 1 or years > 3:
                    contractor["actual_size"] = "owner_operator"
                else:
                    contractor["actual_size"] = "solo_handyman"
                
                print(f"  {contractor.get('company_name')}: {contractor['actual_size']} (team: {team_size}, years: {years})")
            else:
                # No website data - use review count as LAST RESORT
                review_count = contractor.get("review_count", 0)
                if review_count > 100:
                    contractor["actual_size"] = "small_business"
                elif review_count > 20:
                    contractor["actual_size"] = "owner_operator"
                else:
                    contractor["actual_size"] = "solo_handyman"
                
                contractor["size_confidence"] = "low"  # Mark as guess
        
        return contractors
    
    def _filter_by_size_preference(
        self, 
        contractors: List[Dict[str, Any]], 
        preference: str
    ) -> List[Dict[str, Any]]:
        """
        Apply ±1 size flexibility AFTER accurate sizing
        """
        size_flexibility = {
            "solo_handyman": ["solo_handyman", "owner_operator"],
            "owner_operator": ["solo_handyman", "owner_operator", "small_business"],
            "small_business": ["owner_operator", "small_business", "regional_company"],
            "regional_company": ["small_business", "regional_company", "enterprise"],
            "enterprise": ["regional_company", "enterprise"]
        }
        
        acceptable_sizes = size_flexibility.get(preference, [preference])
        
        return [
            c for c in contractors 
            if c.get("actual_size") in acceptable_sizes
        ]
    
    def _extract_location(self, bid_data: dict) -> dict:
        """Extract location from various possible locations in bid data"""
        return (
            bid_data.get("location") or 
            bid_data.get("bid_document", {}).get("location") or 
            {}
        )
    
    def _extract_size_preference(self, bid_data: dict) -> str:
        """Extract size preference from bid data"""
        return (
            bid_data.get("contractor_requirements", {}).get("contractor_size_preference") or
            bid_data.get("bid_document", {}).get("contractor_requirements", {}).get("contractor_size_preference") or
            "owner_operator"  # Default to owner_operator (size 2)
        )


# Test the improved flow
if __name__ == "__main__":
    import asyncio
    from database_simple import get_client
    
    async def test_improved_flow():
        supabase = get_client()
        
        # Test bid data
        bid_data = {
            "project_type": "christmas light installation",
            "location": {
                "zip_code": "33442",
                "city": "Deerfield Beach",
                "state": "FL"
            },
            "contractor_requirements": {
                "contractor_size_preference": "owner_operator"
            }
        }
        
        matcher = ImprovedTier1Matcher(supabase)
        result = await matcher.find_and_enrich_contractors(
            bid_data,
            radius_miles=15,
            contractors_needed=10
        )
        
        print("\n[RESULTS]")
        print(f"Total discovered: {result['total_discovered']}")
        print(f"Total enriched: {result['total_enriched']}")
        print(f"Total analyzed: {result['total_analyzed']}")
        print(f"Total filtered: {result['total_filtered']}")
        print(f"Selected: {len(result['selected_contractors'])}")
        
        print("\n[SIZE BREAKDOWN]")
        for size, count in result['size_breakdown'].items():
            print(f"  {size}: {count}")
        
        print("\n[SELECTED CONTRACTORS]")
        for c in result['selected_contractors']:
            print(f"  - {c.get('company_name')} ({c.get('actual_size')})")
    
    # Run the test
    asyncio.run(test_improved_flow())