#!/usr/bin/env python3
"""
REAL TEST: Holiday Lighting Contractor Discovery in 33442
This will:
1. Clear any test data
2. Use Google Places API for REAL discovery
3. Enrich with website data
4. Show categorization based on REAL data
"""
import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Import components
from agents.cda.google_places_optimized import GooglePlacesOptimized
from agents.cda.intelligent_matcher import IntelligentContractorMatcher
from database_simple import get_client
import aiohttp
from bs4 import BeautifulSoup


async def scrape_website_for_size_indicators(url: str) -> dict:
    """Actually scrape a website for size indicators"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return {"error": f"Status {response.status}"}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                text_content = soup.get_text().lower()
                
                # Extract real size indicators
                indicators = {
                    "url": url,
                    "page_title": soup.title.string if soup.title else None,
                    "has_team_mentions": "team" in text_content or "staff" in text_content,
                    "has_fleet_mentions": "fleet" in text_content or "trucks" in text_content,
                    "has_warehouse": "warehouse" in text_content or "facility" in text_content,
                    "has_multiple_locations": "locations" in text_content or "offices" in text_content,
                    "content_preview": text_content[:500] if text_content else None
                }
                
                # Look for specific size indicators
                import re
                
                # Team size
                team_match = re.search(r'(\d+)\+?\s*(employees?|team members?|professionals?|technicians?)', text_content)
                if team_match:
                    indicators["team_size"] = int(team_match.group(1))
                
                # Years in business
                year_match = re.search(r'(since|established|serving since|in business since)\s*(\d{4})', text_content)
                if year_match:
                    indicators["years_in_business"] = 2025 - int(year_match.group(2))
                
                # Service area
                if "nationwide" in text_content or "national" in text_content:
                    indicators["service_scope"] = "national"
                elif "statewide" in text_content or "florida" in text_content:
                    indicators["service_scope"] = "statewide"
                elif "county" in text_content or "tri-county" in text_content:
                    indicators["service_scope"] = "regional"
                else:
                    indicators["service_scope"] = "local"
                
                return indicators
                
    except Exception as e:
        return {"error": str(e)}


async def categorize_contractor_size(contractor: dict, website_data: dict) -> str:
    """Categorize contractor size based on REAL website data"""
    
    # Use REAL data from website
    team_size = website_data.get("team_size", 0)
    years = website_data.get("years_in_business", 0)
    has_fleet = website_data.get("has_fleet_mentions", False)
    has_warehouse = website_data.get("has_warehouse", False)
    has_multiple_locations = website_data.get("has_multiple_locations", False)
    service_scope = website_data.get("service_scope", "local")
    
    # ACCURATE categorization from REAL data
    if team_size > 50 or service_scope == "national":
        return "enterprise"
    elif team_size > 20 or has_multiple_locations or service_scope == "statewide":
        return "regional_company"
    elif team_size > 5 or (has_fleet and has_warehouse) or years > 10:
        return "small_business"
    elif team_size > 1 or years > 3:
        return "owner_operator"
    else:
        # If no website data, use review count as last resort
        review_count = contractor.get("google_review_count", 0)
        if review_count > 100:
            return "small_business"
        elif review_count > 20:
            return "owner_operator"
        else:
            return "solo_handyman"


async def test_real_discovery():
    """Run REAL discovery test for holiday lighting in 33442"""
    
    print("=" * 80)
    print("REAL HOLIDAY LIGHTING CONTRACTOR DISCOVERY TEST")
    print("Location: 33442 (Deerfield Beach, FL)")
    print("=" * 80)
    
    # Step 1: Clear test data from database
    print("\n[STEP 1] Clearing Test Data from Database")
    print("-" * 60)
    
    supabase = get_client()
    
    # Clear test holiday contractors from potential_contractors
    test_companies = [
        "Festive Lights Pro",
        "Holiday Brilliance LLC", 
        "Joe Holiday Lighting",
        "Seasonal Sparkle Services",
        "Christmas Magic Installations"
    ]
    
    for company in test_companies:
        try:
            result = supabase.table("potential_contractors").delete().eq("company_name", company).execute()
            if result.data:
                print(f"  ✓ Deleted test contractor: {company}")
        except:
            pass
    
    # Step 2: Google Places Discovery
    print("\n[STEP 2] Google Places API Discovery")
    print("-" * 60)
    
    google_searcher = GooglePlacesOptimized()
    
    # Search queries to try
    search_queries = [
        "christmas light installation Deerfield Beach FL",
        "holiday lighting contractor 33442",
        "christmas decorating service near 33442"
    ]
    
    all_contractors = []
    seen_names = set()
    
    for query in search_queries:
        print(f"\nSearching: '{query}'")
        
        try:
            # discover_contractors expects: service_type, location, target_count, radius_miles
            results = await google_searcher.discover_contractors(
                service_type="christmas light installation",
                location={
                    "city": "Deerfield Beach",
                    "state": "FL",
                    "zip": "33442"
                },
                target_count=20,
                radius_miles=15
            )
            
            contractors = results.get("contractors", [])
            print(f"  Found {len(contractors)} contractors")
            
            # Deduplicate
            for contractor in contractors:
                name = contractor.get("company_name")
                if name and name not in seen_names:
                    seen_names.add(name)
                    all_contractors.append(contractor)
                    
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\nTotal unique contractors found: {len(all_contractors)}")
    
    # Step 3: Website Enrichment and Categorization
    print("\n[STEP 3] Website Enrichment & Size Categorization")
    print("-" * 60)
    
    categorized_contractors = []
    
    for i, contractor in enumerate(all_contractors, 1):
        company_name = contractor.get("company_name")
        website = contractor.get("website", "")
        review_count = contractor.get("google_review_count", 0)
        rating = contractor.get("google_rating", 0)
        
        print(f"\n[{i}] {company_name}")
        print(f"  Reviews: {review_count}, Rating: {rating}")
        
        if website:
            print(f"  Website: {website}")
            print(f"  Enriching from website...")
            
            # Actually scrape the website
            website_data = await scrape_website_for_size_indicators(website)
            
            if "error" not in website_data:
                print(f"    ✓ Successfully scraped website")
                if website_data.get("team_size"):
                    print(f"    Team size: {website_data['team_size']} employees")
                if website_data.get("years_in_business"):
                    print(f"    Years in business: {website_data['years_in_business']}")
                if website_data.get("service_scope"):
                    print(f"    Service scope: {website_data['service_scope']}")
            else:
                print(f"    ✗ Could not scrape: {website_data['error']}")
                website_data = {}
        else:
            print(f"  No website - using review data only")
            website_data = {}
        
        # Categorize based on REAL data
        size_category = await categorize_contractor_size(contractor, website_data)
        print(f"  CATEGORY: {size_category}")
        
        contractor["size_category"] = size_category
        contractor["website_data"] = website_data
        contractor["categorization_method"] = "website_enriched" if website_data else "review_based"
        
        categorized_contractors.append(contractor)
    
    # Step 4: Size Distribution Analysis
    print("\n[STEP 4] Size Distribution Analysis")
    print("-" * 60)
    
    size_distribution = {}
    for contractor in categorized_contractors:
        size = contractor["size_category"]
        size_distribution[size] = size_distribution.get(size, 0) + 1
    
    print("\nContractor Size Distribution:")
    for size, count in sorted(size_distribution.items()):
        print(f"  {size}: {count} contractors")
    
    # Step 5: Apply ±1 Size Flexibility for owner_operator preference
    print("\n[STEP 5] Applying Size Flexibility (owner_operator ±1)")
    print("-" * 60)
    
    target_size = "owner_operator"
    acceptable_sizes = ["solo_handyman", "owner_operator", "small_business"]
    
    print(f"\nTarget size: {target_size}")
    print(f"Acceptable sizes with ±1 flexibility: {', '.join(acceptable_sizes)}")
    
    matching_contractors = [
        c for c in categorized_contractors
        if c["size_category"] in acceptable_sizes
    ]
    
    print(f"\nMatching contractors: {len(matching_contractors)} out of {len(categorized_contractors)}")
    
    # Step 6: Final Results
    print("\n[STEP 6] Final Results")
    print("-" * 60)
    
    print("\nALL CONTRACTORS FOUND AND CATEGORIZED:")
    print("=" * 80)
    
    for i, contractor in enumerate(categorized_contractors, 1):
        print(f"\n[{i}] {contractor.get('company_name')}")
        print(f"    Category: {contractor['size_category']}")
        print(f"    Method: {contractor['categorization_method']}")
        print(f"    Reviews: {contractor.get('google_review_count', 0)}")
        print(f"    Rating: {contractor.get('google_rating', 'N/A')}")
        print(f"    Website: {contractor.get('website', 'None')}")
        if contractor.get('website_data') and not contractor['website_data'].get('error'):
            wd = contractor['website_data']
            if wd.get('team_size'):
                print(f"    Team Size: {wd['team_size']} employees")
            if wd.get('years_in_business'):
                print(f"    Years: {wd['years_in_business']} years")
            if wd.get('service_scope'):
                print(f"    Scope: {wd['service_scope']}")
    
    print("\n" + "=" * 80)
    print("DISCOVERY COMPLETE")
    print(f"Total contractors found: {len(categorized_contractors)}")
    print(f"Websites enriched: {sum(1 for c in categorized_contractors if c['categorization_method'] == 'website_enriched')}")
    print(f"Review-based only: {sum(1 for c in categorized_contractors if c['categorization_method'] == 'review_based')}")
    print("=" * 80)
    
    return categorized_contractors


if __name__ == "__main__":
    # Run the real test
    results = asyncio.run(test_real_discovery())
    
    # Save results to file for analysis
    with open("holiday_lighting_discovery_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to holiday_lighting_discovery_results.json")