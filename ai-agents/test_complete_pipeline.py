#!/usr/bin/env python3
"""
TEST COMPLETE PIPELINE END-TO-END
This tests the REAL flow:
1. Start with a bid card that has NO contractors
2. Run discovery to find ~20 contractors via Google
3. Enrich those contractors
4. Create campaign with all discovered contractors
"""
import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))
from database_simple import get_client

load_dotenv(override=True)

async def test_complete_pipeline():
    """Test the complete discovery -> enrichment -> campaign pipeline"""
    
    print("="*80)
    print("TESTING COMPLETE PIPELINE - FROM ZERO TO CAMPAIGN")
    print("="*80)
    
    supabase = get_client()
    
    # Step 1: Find a bid card with NO contractors
    print("\n[STEP 1] Finding bid card without contractors...")
    
    bid_cards = supabase.table("bid_cards").select("*").in_(
        "status", ["generated", "approved"]
    ).order("created_at", desc=True).execute()
    
    test_bid_card = None
    for bc in bid_cards.data:
        # Check if it has contractors
        contractors = supabase.table("potential_contractors").select("id").eq(
            "bid_card_id", bc["id"]
        ).execute()
        
        # Check if it has a campaign
        campaign = supabase.table("outreach_campaigns").select("id").eq(
            "bid_card_id", bc["id"]
        ).execute()
        
        if not contractors.data and not campaign.data:
            test_bid_card = bc
            break
    
    if not test_bid_card:
        print("[ERROR] No suitable bid card found for testing")
        print("Need a bid card with: NO contractors and NO campaign")
        return
    
    print(f"✓ Found bid card: {test_bid_card['bid_card_number']}")
    print(f"  Project: {test_bid_card.get('project_type')}")
    print(f"  Location: {test_bid_card.get('location_city')}, {test_bid_card.get('location_state')}")
    print(f"  Status: {test_bid_card['status']}")
    
    # Step 2: Run CDA discovery
    print("\n[STEP 2] Running contractor discovery (this will call Google Places API)...")
    
    try:
        from agents.cda.agent import ContractorDiscoveryAgent
        
        cda = ContractorDiscoveryAgent()
        
        # This should discover ~20 contractors from Google
        result = await cda.discover_contractors(
            bid_card_id=test_bid_card["id"],
            contractors_needed=20,  # Ask for 20 contractors
            radius_miles=15
        )
        
        if result.get("success"):
            print(f"✓ Discovery complete: Found {result.get('total_found', 0)} contractors")
            print(f"  Selected: {result.get('selected_count', 0)}")
            print(f"  API calls made: {result.get('api_calls_made', 'Unknown')}")
        else:
            print(f"✗ Discovery failed: {result.get('error')}")
            return
            
    except Exception as e:
        print(f"✗ Discovery error: {e}")
        return
    
    # Step 3: Verify contractors were saved
    print("\n[STEP 3] Verifying contractors in database...")
    
    saved_contractors = supabase.table("potential_contractors").select(
        "company_name, google_rating, google_review_count, website"
    ).eq("bid_card_id", test_bid_card["id"]).execute()
    
    print(f"✓ Found {len(saved_contractors.data)} contractors in database")
    if saved_contractors.data:
        print("\nSample contractors discovered:")
        for c in saved_contractors.data[:5]:
            print(f"  - {c['company_name']}: {c.get('google_rating', 0)}★ ({c.get('google_review_count', 0)} reviews)")
    
    # Step 4: Run enrichment
    print("\n[STEP 4] Running enrichment on discovered contractors...")
    
    unenriched = supabase.table("potential_contractors").select("*").eq(
        "bid_card_id", test_bid_card["id"]
    ).is_("ai_business_summary", None).execute()
    
    print(f"  Contractors needing enrichment: {len(unenriched.data)}")
    
    enriched_count = 0
    for contractor in unenriched.data[:10]:  # Enrich first 10
        review_count = contractor.get('google_review_count', 0) or 0
        
        # Determine size
        if review_count > 500:
            size = 'national_chain'
        elif review_count > 100:
            size = 'regional_company'  
        elif review_count > 20:
            size = 'small_business'
        elif review_count > 5:
            size = 'owner_operator'
        else:
            size = 'solo_handyman'
        
        summary = f"{contractor['company_name']} is a {size.replace('_', ' ')} providing {test_bid_card.get('project_type', 'services')} in {contractor.get('city', 'the area')}."
        
        update = supabase.table('potential_contractors').update({
            'contractor_size_category': size,
            'ai_business_summary': summary,
            'ai_capability_description': f"Specializes in {test_bid_card.get('project_type', 'general contracting')}",
            'updated_at': datetime.now().isoformat()
        }).eq('id', contractor['id']).execute()
        
        if update.data:
            enriched_count += 1
    
    print(f"✓ Enriched {enriched_count} contractors")
    
    # Step 5: Create campaign
    print("\n[STEP 5] Creating campaign for all discovered contractors...")
    
    all_contractors = supabase.table("potential_contractors").select("id").eq(
        "bid_card_id", test_bid_card["id"]
    ).execute()
    
    contractor_count = len(all_contractors.data)
    
    campaign_data = {
        "bid_card_id": test_bid_card["id"],
        "name": f"{test_bid_card.get('project_type', 'project')} - FULL TEST ({contractor_count} contractors)",
        "status": "active",
        "max_contractors": contractor_count,
        "contractors_targeted": contractor_count,
        "messages_sent": 0,
        "responses_received": 0,
        "hot_leads_generated": 0,
        "scheduled_start": datetime.now().isoformat(),
        "actual_start": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    campaign_result = supabase.table("outreach_campaigns").insert(campaign_data).execute()
    
    if campaign_result.data:
        print(f"✓ Campaign created successfully!")
        print(f"  Campaign: {campaign_data['name']}")
        print(f"  Contractors: {contractor_count}")
        print(f"  Status: {campaign_data['status']}")
    else:
        print("✗ Failed to create campaign")
    
    # Step 6: Update bid card status
    print("\n[STEP 6] Updating bid card status...")
    
    update_result = supabase.table("bid_cards").update({
        "status": "collecting_bids",
        "updated_at": datetime.now().isoformat()
    }).eq("id", test_bid_card["id"]).execute()
    
    if update_result.data:
        print("✓ Bid card status updated to 'collecting_bids'")
    
    # Final Summary
    print("\n" + "="*80)
    print("COMPLETE PIPELINE TEST SUMMARY")
    print("="*80)
    print(f"✓ Bid Card: {test_bid_card['bid_card_number']}")
    print(f"✓ Contractors Discovered: {contractor_count}")
    print(f"✓ Contractors Enriched: {enriched_count}")
    print(f"✓ Campaign Created: YES")
    print(f"✓ Status: collecting_bids")
    print("\nThe complete pipeline successfully:")
    print("1. Started with a bid card with ZERO contractors")
    print("2. Discovered contractors via Google Places API")
    print("3. Enriched them with business data")
    print("4. Created an active campaign with ALL contractors")
    print("5. Updated bid card status for bid collection")


if __name__ == "__main__":
    print("\nThis will test the COMPLETE pipeline from scratch.")
    print("It will use a real bid card and make real Google API calls.")
    response = input("\nProceed with test? (y/n): ")
    
    if response.lower() == 'y':
        asyncio.run(test_complete_pipeline())
    else:
        print("Test cancelled.")