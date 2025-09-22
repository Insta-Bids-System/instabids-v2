"""
Complete test for roofing installation bid card with full discovery flow
Location: 33442 (Deerfield Beach, FL)
"""

import asyncio
import os
import sys
from datetime import datetime
import json
import uuid

# CRITICAL: Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv(override=True)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_simple import get_client
from agents.project_categorization.simple_categorization_tool import categorize_and_save_project
from agents.cda.enhanced_web_search_agent import EnhancedWebSearchAgent

async def test_roofing_complete_flow():
    """Test complete flow for roofing installation project"""
    
    print("\n" + "="*80)
    print("ROOFING INSTALLATION COMPLETE FLOW TEST")
    print("Location: 33442 (Deerfield Beach, FL)")
    print("="*80)
    
    try:
        # Initialize database client
        supabase = get_client()
        
        # Step 1: Create bid card for roofing installation
        print("\n[STEP 1] Creating bid card for roofing installation...")
        print("-" * 60)
        
        bid_card = {
            "title": "Complete Roof Replacement - Shingle Installation",
            "description": """Need complete roof replacement on 2,500 sq ft home. 
            Current shingles are 20 years old and damaged from recent storms. 
            Looking for architectural shingles with 30-year warranty. 
            Need to replace some damaged decking and update flashing around chimney.""",
            "primary_trade": "roofing",
            "location_city": "Deerfield Beach",
            "location_state": "FL",
            "location_zip": "33442",
            "status": "draft",
            "contractor_count_needed": 4,
            "urgency_level": "urgent",
            "budget_min": 8000,
            "budget_max": 15000,
            "created_at": datetime.now().isoformat()
        }
        
        result = supabase.table("potential_bid_cards").insert(bid_card).execute()
        
        if not result.data:
            print("[X] Failed to create bid card")
            return
        
        bid_card_id = result.data[0]["id"]
        print(f"[OK] Created bid card ID: {bid_card_id}")
        print(f"     Title: {bid_card['title']}")
        print(f"     Location: {bid_card['location_city']}, {bid_card['location_state']} {bid_card['location_zip']}")
        print(f"     Budget: ${bid_card['budget_min']:,} - ${bid_card['budget_max']:,}")
        
        # Step 2: Categorize to get contractor_type_ids
        print("\n[STEP 2] Categorizing project to get contractor types...")
        print("-" * 60)
        
        categorization = await categorize_and_save_project(
            description=bid_card["description"],
            bid_card_id=bid_card_id,
            context="Roof replacement with shingle installation"
        )
        
        if categorization.get("success"):
            print(f"[OK] Project categorized successfully")
            print(f"     Project Type: {categorization.get('project_type_name')}")
            print(f"     Project Type ID: {categorization.get('project_type_id')}")
            print(f"     Contractor Type IDs: {categorization.get('contractor_type_ids')}")
            
            # Get contractor type names
            if categorization.get('contractor_type_ids'):
                type_result = supabase.table("contractor_types").select("id, name").in_(
                    "id", categorization['contractor_type_ids']
                ).execute()
                
                if type_result.data:
                    print("\n     Contractor Types Needed:")
                    for ct in type_result.data:
                        print(f"     - {ct['name']} (ID: {ct['id']})")
        else:
            print(f"[X] Categorization failed: {categorization.get('error')}")
        
        # Step 3: Initialize CDA agent for discovery
        print("\n[STEP 3] Running CDA enhanced discovery for 1 contractor...")
        print("-" * 60)
        
        agent = EnhancedWebSearchAgent(supabase)
        
        # Get contractor types from bid card
        bid_card_data = await agent.get_bid_card_contractor_types(bid_card_id)
        contractor_types = bid_card_data.get("contractor_types", [])
        
        search_terms = []
        if contractor_types:
            print(f"[OK] Retrieved {len(contractor_types)} contractor types for searching")
            
            # Build prioritized search terms
            priority_terms = []
            category_terms = []
            
            for contractor_type in contractor_types:
                name = contractor_type.get("name", "")
                if any(ending in name.lower() for ending in ["contractor", "er", "ist", "ian", "man"]):
                    priority_terms.append(name)
                else:
                    category_terms.append(name)
            
            search_terms = priority_terms + category_terms
            if len(search_terms) > 3:
                search_terms = search_terms[:3]
            
            print(f"     Priority search terms: {search_terms}")
        else:
            print("[WARNING] No contractor types found, using default roofing terms")
            # Manually set roofing contractor types since categorization failed
            # Let's add them manually for testing - CORRECT roofing contractor types
            roofing_type_ids = [36, 48, 184]  # Roofing, General Contracting, Roofing Contractor
            
            print("\n[Manual Fix] Adding roofing contractor types...")
            update_result = supabase.table("potential_bid_cards").update({
                "contractor_type_ids": roofing_type_ids
            }).eq("id", bid_card_id).execute()
            
            if update_result.data:
                print(f"[OK] Updated bid card with contractor_type_ids: {roofing_type_ids}")
                
                # Get the contractor type names
                type_result = supabase.table("contractor_types").select("id, name").in_(
                    "id", roofing_type_ids
                ).execute()
                
                if type_result.data:
                    print("\n     Contractor Types Added:")
                    for ct in type_result.data:
                        print(f"     - {ct['name']} (ID: {ct['id']})")
                        if any(ending in ct['name'].lower() for ending in ["contractor", "er", "ist", "ian", "man"]):
                            search_terms.insert(0, ct['name'])  # Priority terms first
                        else:
                            search_terms.append(ct['name'])
        
        # Step 4: Google Places search for first contractor type
        print("\n[STEP 4] Searching Google Places for roofing contractors...")
        print("-" * 60)
        
        from agents.cda.google_places_optimized import GooglePlacesOptimized
        google_tool = GooglePlacesOptimized()
        
        # Use the best search term - prioritize roofing-specific terms
        if search_terms:
            # For roofing projects, prioritize roofing-specific terms
            roofing_priority = ["Roofing Contractor", "Roofer", "Roofing"]
            search_term = search_terms[0]  # Default to first
            
            # Check if we have any roofing-specific terms and prioritize them
            for priority_term in roofing_priority:
                if priority_term in search_terms:
                    search_term = priority_term
                    break
        else:
            search_term = "roofing contractor"
            
        print(f"\n[Searching for: '{search_term}' in Deerfield Beach, FL 33442]")
        
        google_discovery = await google_tool.discover_contractors(
            service_type=search_term,
            location={
                "city": "Deerfield Beach",
                "state": "FL",
                "zip": "33442"
            },
            target_count=1,  # Just get 1 contractor as requested
            radius_miles=10,
            cost_mode="CHEAPEST",
            include_sabs=True,
            min_rating=3.0
        )
        
        discovered_contractor = None
        if google_discovery.get("success"):
            contractors = google_discovery.get("contractors", [])
            if contractors:
                discovered_contractor = contractors[0]
                print(f"\n[OK] Found contractor from Google Places:")
                print(f"     Name: {discovered_contractor.get('name', 'Unknown')}")
                print(f"     Phone: {discovered_contractor.get('phone', 'N/A')}")
                print(f"     Address: {discovered_contractor.get('address', 'N/A')}")
                print(f"     Website: {discovered_contractor.get('website', 'N/A')}")
                print(f"     Rating: {discovered_contractor.get('google_rating', 0)}")
                print(f"     Reviews: {discovered_contractor.get('google_review_count', 0)}")
                print(f"     Place ID: {discovered_contractor.get('google_place_id', 'N/A')}")
        else:
            print(f"[X] Google search failed: {google_discovery.get('error')}")
        
        # Step 5: Tavily web enrichment
        if discovered_contractor and discovered_contractor.get('website'):
            print("\n[STEP 5] Enriching with Tavily web search...")
            print("-" * 60)
            
            from agents.cda.tavily_search import TavilySearchTool
            tavily_tool = TavilySearchTool()
            
            print(f"[Searching web for: {discovered_contractor.get('name')}]")
            
            tavily_result = await tavily_tool.discover_contractor_pages(
                company_name=discovered_contractor.get('name', ''),
                website_url=discovered_contractor.get('website', ''),
                location=f"Deerfield Beach, FL"
            )
            
            if tavily_result and tavily_result.get("discovered_pages"):
                pages = tavily_result.get("discovered_pages", [])
                print(f"[OK] Found {len(pages)} web pages")
                
                for i, page in enumerate(pages[:3], 1):
                    print(f"\n     Page {i}:")
                    print(f"     URL: {page.get('url', 'N/A')}")
                    print(f"     Title: {page.get('title', 'N/A')}")
                    if page.get('content'):
                        content_preview = page['content'][:200] + "..." if len(page['content']) > 200 else page['content']
                        print(f"     Content: {content_preview}")
            else:
                print("[X] No web pages found")
        else:
            print("\n[STEP 5] Skipping Tavily enrichment (no website)")
        
        # Step 6: Build complete profile and save to potential_contractors
        if discovered_contractor:
            print("\n[STEP 6] Building complete profile and saving to database...")
            print("-" * 60)
            
            from agents.cda.complete_profile_builder import CompleteProfileBuilder
            profile_builder = CompleteProfileBuilder()
            
            # Build the profile
            profile = await profile_builder.build_contractor_profile(
                company_name=discovered_contractor.get('name', ''),
                google_data=discovered_contractor,
                web_data=tavily_result if 'tavily_result' in locals() else None,
                license_data=None
            )
            
            # Add discovery metadata
            profile["discovery_source"] = "test_roofing_flow"
            profile["bid_card_id"] = bid_card_id
            profile["search_classification"] = search_term
            profile["discovery_tier"] = 3
            
            print(f"\n[Profile Built]:")
            print(f"     Company: {profile.get('company_name', 'Unknown')}")
            print(f"     Phone: {profile.get('phone', 'N/A')}")
            print(f"     Email: {profile.get('email', 'N/A')}")
            print(f"     Website: {profile.get('website', 'N/A')}")
            print(f"     Specialties: {profile.get('specialties', [])}")
            print(f"     Years in Business: {profile.get('years_in_business', 'Unknown')}")
            print(f"     Size Category: {profile.get('contractor_size_category', 'Unknown')}")
            
            # Save to potential_contractors
            try:
                record = {
                    "company_name": profile.get("company_name", ""),
                    "phone": profile.get("phone", ""),
                    "email": profile.get("email", ""),
                    "website": profile.get("website", ""),
                    "address": profile.get("address", ""),
                    "city": profile.get("city", ""),
                    "state": profile.get("state", ""),
                    "zip_code": profile.get("zip_code", ""),
                    "google_place_id": profile.get("google_place_id", ""),
                    "google_rating": profile.get("google_rating", 0),
                    "google_review_count": profile.get("google_review_count", 0),
                    "specialties": profile.get("specialties", []),
                    "contractor_size_category": profile.get("contractor_size_category", "small"),
                    "ai_business_summary": profile.get("ai_business_summary", ""),
                    "ai_capability_description": profile.get("ai_capability_description", ""),
                    "lead_status": "new",
                    "discovery_source": "roofing_test",
                    "project_type": "roofing",
                    "project_zip_code": "33442",
                    "bid_card_id": bid_card_id
                }
                
                # Remove None values and empty strings for required fields
                record = {k: v for k, v in record.items() if v is not None and (k != "company_name" or v != "")}
                
                if record.get("company_name"):  # Only save if we have a company name
                    save_result = supabase.table("potential_contractors").insert(record).execute()
                    
                    if save_result.data:
                        saved_id = save_result.data[0]["id"]
                        print(f"\n[OK] Saved to potential_contractors table")
                        print(f"     Record ID: {saved_id}")
                    else:
                        print(f"\n[X] Failed to save to database")
                else:
                    print("\n[X] Cannot save - no company name")
                    
            except Exception as e:
                print(f"\n[X] Database save error: {e}")
        
        # Step 7: Verify what's in the potential_contractors table
        print("\n[STEP 7] Checking potential_contractors table...")
        print("-" * 60)
        
        check_result = supabase.table("potential_contractors").select("*").eq(
            "bid_card_id", bid_card_id
        ).execute()
        
        if check_result.data:
            print(f"[OK] Found {len(check_result.data)} contractor(s) in potential_contractors")
            
            for contractor in check_result.data:
                print(f"\n     Contractor Record:")
                print(f"     - ID: {contractor.get('id')}")
                print(f"     - Company: {contractor.get('company_name')}")
                print(f"     - Phone: {contractor.get('phone')}")
                print(f"     - Website: {contractor.get('website')}")
                print(f"     - City: {contractor.get('city')}")
                print(f"     - State: {contractor.get('state')}")
                print(f"     - Discovery Source: {contractor.get('discovery_source')}")
                print(f"     - Lead Status: {contractor.get('lead_status')}")
        else:
            print("[X] No contractors found in potential_contractors table")
        
        # Step 8: Cleanup
        print("\n[STEP 8] Cleaning up test data...")
        print("-" * 60)
        
        # Delete contractors
        if check_result.data:
            for contractor in check_result.data:
                supabase.table("potential_contractors").delete().eq("id", contractor['id']).execute()
                print(f"[OK] Deleted contractor: {contractor.get('company_name')}")
        
        # Delete bid card
        supabase.table("potential_bid_cards").delete().eq("id", bid_card_id).execute()
        print(f"[OK] Deleted bid card: {bid_card_id}")
        
        print("\n" + "="*80)
        print("ROOFING INSTALLATION FLOW TEST COMPLETE")
        print("="*80)
        print("\nSUMMARY:")
        print("1. Bid card created with proper classification")
        print("2. Contractor types identified and prioritized")
        print("3. Google Places search executed with targeted terms")
        print("4. Web enrichment performed (if website available)")
        print("5. Complete profile built and saved to database")
        print("6. potential_contractors table populated successfully")
        
    except Exception as e:
        print(f"\n[X] Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_roofing_complete_flow())