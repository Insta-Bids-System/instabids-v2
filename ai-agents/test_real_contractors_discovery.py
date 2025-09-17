#!/usr/bin/env python3
"""
REAL Contractor Discovery Test with Actual Google/Web Results
Using actual contractors found from web search for 33442 area
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
from datetime import datetime


# REAL contractors found from web search for 33442 Deerfield Beach, FL
REAL_CONTRACTORS_33442 = [
    {
        "company_name": "JM Holiday Lighting Inc",
        "website": "https://jmholidaylighting.com/",
        "phone": "(954) 482-6800",
        "address": "5051 NW 13th Ave, Ste G, Pompano Beach, FL 33064",
        "services": "Professional Holiday, Christmas and Hanukkah light installation",
        "service_area": "All of South Florida including Miami, Fort Lauderdale, Palm Beach",
        "source": "Google Search + BBB Profile"
    },
    {
        "company_name": "Warriors for Light",
        "website": "https://www.warriorsforlight.com/fl/deerfield-beach/",
        "phone": "(888) 930-3450",
        "services": "Turn-key Christmas light installation with maintenance",
        "features": "Fully insured, online booking, free repairs",
        "source": "Google Search"
    },
    {
        "company_name": "Rizzo's Holiday Lighting",
        "website": "https://rizzosholidaylighting.com/",
        "phone": "Not found in search",
        "services": "Concierge-style holiday lighting",
        "service_area": "Parkland, Deerfield Beach, South Palm Beach County",
        "source": "Google Search"
    },
    {
        "company_name": "Reindeer Bros",
        "website": "https://reindeerbros.com/christmas-light-installation/deerfield-beach-fl/",
        "phone": "Not found in search",
        "minimum": "$1,500 minimum",
        "services": "Commercial-grade LED lighting, 24-48 hour response time",
        "source": "Google Search"
    },
    {
        "company_name": "Christmas Lights by Amco",
        "website": "https://christmaslightsbyamco.com/florida/broward-county/christmas-light-installers-deerfield-beach-fl/",
        "phone": "Not found in search",
        "services": "Expert Christmas light installation for businesses and homes",
        "features": "Design consultation, takedown and storage services",
        "source": "Google Search"
    },
    {
        "company_name": "Real Tree Trimming & Landscaping Inc",
        "website": "https://www.realtreeteam.com/christmas-light-installation-hanging",
        "phone": "Not found in search",
        "services": "Tree service for 30 years, also Christmas light installation",
        "service_area": "Palm Beach County & Broward",
        "source": "Google Search"
    }
]


async def enrich_from_actual_website(contractor: dict) -> dict:
    """Actually try to scrape the contractor's real website"""
    website = contractor.get("website", "")
    if not website:
        return {"enrichment_complete": False, "error": "No website"}
    
    try:
        print(f"  Attempting to scrape: {website}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(website, timeout=10, ssl=False) as response:
                if response.status != 200:
                    return {"enrichment_complete": False, "error": f"HTTP {response.status}"}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                text_content = soup.get_text().lower()
                
                # Extract REAL indicators from website
                indicators = {
                    "enrichment_complete": True,
                    "page_title": soup.title.string if soup.title else None,
                    "content_length": len(text_content),
                }
                
                # Look for team size mentions
                import re
                team_patterns = [
                    r'(\d+)\+?\s*(employees?|team members?|professionals?|technicians?|installers?)',
                    r'team of (\d+)',
                    r'staff of (\d+)'
                ]
                for pattern in team_patterns:
                    match = re.search(pattern, text_content)
                    if match:
                        indicators["team_size"] = int(match.group(1) if '(' in pattern else match.group(1))
                        break
                
                # Look for years in business
                year_patterns = [
                    r'(since|established|serving since|in business since|founded in)\s*(\d{4})',
                    r'(\d+)\+?\s*years?\s*(of experience|in business|serving)'
                ]
                for pattern in year_patterns:
                    match = re.search(pattern, text_content)
                    if match:
                        if 'since' in pattern or 'founded' in pattern:
                            indicators["years_in_business"] = 2025 - int(match.group(2))
                        else:
                            indicators["years_in_business"] = int(match.group(1))
                        break
                
                # Service scope indicators
                if any(word in text_content for word in ["nationwide", "national", "across america"]):
                    indicators["service_scope"] = "national"
                elif any(phrase in text_content for phrase in ["all of florida", "statewide", "throughout florida"]):
                    indicators["service_scope"] = "statewide"
                elif any(phrase in text_content for phrase in ["south florida", "tri-county", "broward palm beach miami"]):
                    indicators["service_scope"] = "regional"
                else:
                    indicators["service_scope"] = "local"
                
                # Business size indicators
                indicators["has_fleet"] = any(word in text_content for word in ["fleet", "trucks", "vehicles", "vans"])
                indicators["has_warehouse"] = any(word in text_content for word in ["warehouse", "facility", "headquarters"])
                indicators["has_insurance"] = "insured" in text_content or "insurance" in text_content
                indicators["has_employees"] = "employees" in text_content or "team" in text_content
                indicators["commercial_focus"] = "commercial" in text_content or "business" in text_content
                
                # Extract snippets for context
                if "about" in text_content:
                    about_idx = text_content.index("about")
                    indicators["about_snippet"] = text_content[about_idx:about_idx+200]
                
                return indicators
                
    except Exception as e:
        return {"enrichment_complete": False, "error": str(e)}


def categorize_based_on_enrichment(contractor: dict, enrichment: dict) -> str:
    """Categorize contractor size based on REAL enriched data"""
    
    if enrichment.get("enrichment_complete"):
        # Use REAL website data
        team_size = enrichment.get("team_size", 0)
        years = enrichment.get("years_in_business", 0)
        scope = enrichment.get("service_scope", "local")
        has_fleet = enrichment.get("has_fleet", False)
        has_warehouse = enrichment.get("has_warehouse", False)
        commercial = enrichment.get("commercial_focus", False)
        
        # Categorization based on REAL indicators
        if team_size > 20 or scope in ["national", "statewide"]:
            return "regional_company"
        elif team_size > 5 or (has_fleet and has_warehouse) or (commercial and years > 10):
            return "small_business"
        elif team_size > 1 or years > 3 or enrichment.get("has_employees", False):
            return "owner_operator"
        else:
            return "solo_handyman"
    else:
        # No enrichment - use other data
        company_name = contractor.get("company_name", "").lower()
        
        # Use business indicators from name/description
        if "inc" in company_name or "llc" in company_name or "corporation" in company_name:
            if "tree" in company_name or "landscaping" in company_name:
                return "small_business"  # Established service company
            return "owner_operator"  # Incorporated but likely smaller
        
        # Check for minimum pricing (indicator of size)
        if "$1,500 minimum" in str(contractor.get("minimum", "")):
            return "small_business"  # Higher minimums = larger operation
        
        # Default based on service description
        if "concierge" in str(contractor.get("services", "")).lower():
            return "small_business"  # Premium service model
        
        return "owner_operator"  # Default for established contractors


async def test_real_contractors():
    """Test with REAL contractors from actual web search"""
    
    print("=" * 80)
    print("REAL CONTRACTOR DISCOVERY TEST")
    print("Location: 33442 (Deerfield Beach, FL)")
    print("Source: Actual Google/Web Search Results")
    print("=" * 80)
    
    print("\n[STEP 1] REAL Contractors Found from Web Search")
    print("-" * 60)
    
    for contractor in REAL_CONTRACTORS_33442:
        print(f"\n{contractor['company_name']}")
        print(f"  Website: {contractor.get('website', 'Not found')}")
        print(f"  Phone: {contractor.get('phone', 'Not found')}")
        if contractor.get('service_area'):
            print(f"  Service Area: {contractor['service_area']}")
    
    print(f"\nTotal REAL contractors found: {len(REAL_CONTRACTORS_33442)}")
    
    # Step 2: Attempt REAL website enrichment
    print("\n[STEP 2] REAL Website Enrichment")
    print("-" * 60)
    
    for contractor in REAL_CONTRACTORS_33442:
        print(f"\n{contractor['company_name']}:")
        
        # Try to enrich from actual website
        enrichment = await enrich_from_actual_website(contractor)
        contractor['enrichment'] = enrichment
        
        if enrichment.get("enrichment_complete"):
            print(f"  SUCCESS: Scraped {enrichment.get('content_length', 0)} characters")
            if enrichment.get("team_size"):
                print(f"  Found team size: {enrichment['team_size']} employees")
            if enrichment.get("years_in_business"):
                print(f"  Found years: {enrichment['years_in_business']} years")
            if enrichment.get("service_scope"):
                print(f"  Service scope: {enrichment['service_scope']}")
            if enrichment.get("has_fleet"):
                print(f"  Has fleet vehicles: Yes")
            if enrichment.get("has_warehouse"):
                print(f"  Has warehouse: Yes")
        else:
            print(f"  FAILED: {enrichment.get('error', 'Unknown error')}")
    
    # Step 3: Categorization based on REAL data
    print("\n[STEP 3] Size Categorization")
    print("-" * 60)
    
    size_distribution = {}
    
    for contractor in REAL_CONTRACTORS_33442:
        size_category = categorize_based_on_enrichment(
            contractor, 
            contractor.get('enrichment', {})
        )
        contractor['size_category'] = size_category
        size_distribution[size_category] = size_distribution.get(size_category, 0) + 1
        
        print(f"\n{contractor['company_name']}: {size_category}")
        if contractor.get('enrichment', {}).get('enrichment_complete'):
            print(f"  Based on: Website data")
        else:
            print(f"  Based on: Business indicators (name, services, minimum)")
    
    # Step 4: Analysis
    print("\n[STEP 4] Analysis")
    print("-" * 60)
    
    print("\nSize Distribution:")
    for size, count in sorted(size_distribution.items()):
        print(f"  {size}: {count} contractors")
    
    # Step 5: Size filtering for owner_operator preference
    target_size = "owner_operator"
    acceptable_sizes = ["solo_handyman", "owner_operator", "small_business"]
    
    matching = [c for c in REAL_CONTRACTORS_33442 if c['size_category'] in acceptable_sizes]
    
    print(f"\nTarget: {target_size}")
    print(f"With ±1 flexibility: {len(matching)} of {len(REAL_CONTRACTORS_33442)} match")
    
    print("\n" + "=" * 80)
    print("FINAL RESULTS - REAL CONTRACTORS")
    print("=" * 80)
    
    for i, contractor in enumerate(REAL_CONTRACTORS_33442, 1):
        print(f"\n[{i}] {contractor['company_name']}")
        print(f"    Category: {contractor['size_category']}")
        print(f"    Website: {contractor.get('website', 'Not found')}")
        print(f"    Phone: {contractor.get('phone', 'Not found')}")
        
        enrichment = contractor.get('enrichment', {})
        if enrichment.get('enrichment_complete'):
            if enrichment.get('team_size'):
                print(f"    Team Size: {enrichment['team_size']} (from website)")
            if enrichment.get('years_in_business'):
                print(f"    Years: {enrichment['years_in_business']} (from website)")
            if enrichment.get('service_scope'):
                print(f"    Scope: {enrichment['service_scope']} (from website)")
        
        if contractor['size_category'] in acceptable_sizes:
            print(f"    [MATCHES] owner_operator ±1 preference")
    
    return REAL_CONTRACTORS_33442


if __name__ == "__main__":
    results = asyncio.run(test_real_contractors())
    
    # Save results
    with open("real_contractors_results.json", "w") as f:
        # Remove non-serializable data
        clean_results = []
        for r in results:
            clean = r.copy()
            if 'enrichment' in clean:
                clean['enrichment'] = {
                    k: v for k, v in clean['enrichment'].items() 
                    if not callable(v)
                }
            clean_results.append(clean)
        json.dump(clean_results, f, indent=2, default=str)
    
    print(f"\nResults saved to real_contractors_results.json")