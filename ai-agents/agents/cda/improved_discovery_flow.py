"""
IMPROVED CDA Discovery Flow
Fix: Enrich websites FIRST, then categorize size based on real data
"""

from typing import Dict, Any, List
import asyncio
from agents.cda.web_search_agent import WebSearchContractorAgent

class ImprovedContractorDiscovery:
    """
    CORRECT FLOW:
    1. Discovery - Get ALL contractors from Google (no size filtering yet)
    2. Enrichment - Scrape websites FIRST to get real company data
    3. Analysis - Use website data to determine actual size
    4. Filtering - Apply size preferences based on accurate data
    5. Selection - Choose contractors using the 5/10/15 rule
    """
    
    def discover_and_categorize(self, bid_card_id: str, bids_needed: int = 4):
        """
        The CORRECT flow for contractor discovery
        """
        
        # Step 1: Calculate how many contractors to find using the REAL 5/10/15 rule
        contractors_to_find = self._calculate_contractors_needed(bids_needed)
        
        print(f"\n[CORRECT CALCULATION]")
        print(f"Bids needed: {bids_needed}")
        print(f"Using 5/10/15 rule:")
        print(f"  - Tier 1 (90% response): Up to 5 contractors")
        print(f"  - Tier 2 (50% response): Up to 10 contractors")  
        print(f"  - Tier 3 (33% response): Up to 15 contractors")
        print(f"Total to contact: {contractors_to_find}")
        
        # Step 2: Discovery - Get ALL contractors, no size filtering yet
        all_contractors = self._discover_all_contractors(bid_card_id, contractors_to_find * 2)
        print(f"\n[DISCOVERY] Found {len(all_contractors)} contractors total")
        
        # Step 3: ENRICHMENT FIRST - Get real data from websites
        enriched_contractors = []
        for contractor in all_contractors:
            if contractor.get('website'):
                print(f"\n[ENRICHING] {contractor['company_name']}")
                enriched_data = self._scrape_website_for_size_data(contractor['website'])
                
                # Update contractor with REAL data from website
                contractor.update({
                    'team_size': enriched_data.get('team_size'),
                    'years_in_business': enriched_data.get('years_in_business'),
                    'about_text': enriched_data.get('about_text'),
                    'service_areas': enriched_data.get('service_areas'),
                    'certifications': enriched_data.get('certifications'),
                    'actual_size_category': self._determine_size_from_website_data(enriched_data)
                })
            else:
                # No website - mark for later estimation
                contractor['actual_size_category'] = 'unknown_needs_analysis'
            
            enriched_contractors.append(contractor)
        
        # Step 4: INTELLIGENT SIZE ANALYSIS using real data
        for contractor in enriched_contractors:
            if contractor['actual_size_category'] == 'unknown_needs_analysis':
                # NOW use GPT-4 with all available data
                contractor['actual_size_category'] = self._analyze_size_with_gpt4(contractor)
        
        # Step 5: Apply size filtering AFTER we have real data
        filtered_contractors = self._filter_by_size_preference(
            enriched_contractors, 
            bid_card_size_preference='owner_operator'
        )
        
        # Step 6: Select contractors using proper tier distribution
        selected_contractors = self._select_using_tier_strategy(
            filtered_contractors,
            contractors_to_find
        )
        
        return selected_contractors
    
    def _calculate_contractors_needed(self, bids_needed: int) -> int:
        """
        The REAL 5/10/15 rule implementation
        Based on response rates:
        - Tier 1: 90% response rate -> Need 5 to get 4.5 responses
        - Tier 2: 50% response rate -> Need 8 to get 4 responses  
        - Tier 3: 33% response rate -> Need 12 to get 4 responses
        """
        # This is simplified - actual implementation uses timing_probability_engine.py
        if bids_needed == 4:
            return 20  # 5 + 8 + 7 = 20 contractors total
        elif bids_needed == 10:
            return 50  # Scale up proportionally
        else:
            return bids_needed * 5  # General 5-to-1 ratio
    
    def _scrape_website_for_size_data(self, website_url: str) -> Dict[str, Any]:
        """
        Extract REAL size indicators from website
        """
        # This would actually scrape the website and look for:
        indicators = {
            'team_size': None,  # "Our team of 15 professionals"
            'years_in_business': None,  # "Serving since 1995"
            'about_text': None,  # Full about us section
            'office_locations': [],  # Multiple locations = larger
            'certifications': [],  # More certs = more established
            'service_areas': [],  # Wider coverage = larger
            'employee_photos': 0,  # Count team photos
            'fleet_mentions': False,  # "Our fleet of trucks"
            'warehouse_mentions': False,  # "Our 10,000 sq ft facility"
        }
        
        # Actual scraping would happen here
        return indicators
    
    def _determine_size_from_website_data(self, website_data: Dict[str, Any]) -> str:
        """
        Use REAL website data to categorize size accurately
        """
        team_size = website_data.get('team_size', 0)
        years = website_data.get('years_in_business', 0)
        locations = len(website_data.get('office_locations', []))
        
        # ACCURATE size determination from REAL data
        if team_size > 50 or locations > 3:
            return 'enterprise'
        elif team_size > 20 or locations > 1:
            return 'regional_company'
        elif team_size > 5 or years > 10:
            return 'small_business'
        elif team_size > 1 or years > 3:
            return 'owner_operator'
        else:
            return 'solo_handyman'
    
    def _filter_by_size_preference(self, contractors: List, preference: str) -> List:
        """
        Apply +/-1 size flexibility AFTER we have accurate size data
        """
        size_flexibility = {
            'solo_handyman': ['solo_handyman', 'owner_operator'],
            'owner_operator': ['solo_handyman', 'owner_operator', 'small_business'],
            'small_business': ['owner_operator', 'small_business', 'regional_company'],
            'regional_company': ['small_business', 'regional_company', 'enterprise'],
            'enterprise': ['regional_company', 'enterprise']
        }
        
        acceptable_sizes = size_flexibility.get(preference, [preference])
        
        return [c for c in contractors if c['actual_size_category'] in acceptable_sizes]
    
    def _select_using_tier_strategy(self, contractors: List, target_count: int) -> List:
        """
        Select contractors using proper tier distribution
        Max 5 from Tier 1, Max 10 from Tier 2, Max 15 from Tier 3
        """
        tier1 = []
        tier2 = []
        tier3 = []
        
        for contractor in contractors:
            if contractor.get('discovery_tier') == 1:
                if len(tier1) < 5:
                    tier1.append(contractor)
            elif contractor.get('discovery_tier') == 2:
                if len(tier2) < 10:
                    tier2.append(contractor)
            else:
                if len(tier3) < 15:
                    tier3.append(contractor)
        
        # Combine in priority order
        selected = tier1 + tier2 + tier3
        
        return selected[:target_count]


# CORRECT PROMPT FOR SIZE ANALYSIS (using real data)
SIZE_ANALYSIS_PROMPT = """
Analyze this contractor's size based on ACTUAL DATA from their website and Google:

WEBSITE DATA COLLECTED:
- Team size mentioned: {team_size}
- Years in business: {years_in_business}
- Office locations: {office_locations}
- About text: {about_text}
- Service areas: {service_areas}
- Fleet/warehouse mentions: {fleet_warehouse}

GOOGLE DATA:
- Review count: {review_count}
- Rating: {rating}
- Business types: {business_types}

Based on this REAL DATA (not guessing from review count), categorize as:
- solo_handyman: 1 person operation
- owner_operator: 2-3 person team  
- small_business: 4-20 employees
- regional_company: 20-100 employees, multiple locations
- enterprise: 100+ employees, statewide/national

Return JSON with:
- size_category: The accurate size based on real data
- confidence: How confident you are (0-100)
- reasoning: Explain what data points led to this conclusion
"""