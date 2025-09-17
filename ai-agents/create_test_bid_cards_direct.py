"""
Create test bid cards directly in Supabase database for BSA radius testing
Tests Mike's Plumbing search functionality at various distances
"""

import os
import sys
from datetime import datetime, timedelta
import uuid
from database import SupabaseDB

# Mike's Plumbing profile:
# - Location: Boca Raton, FL 33442
# - Specialties: Plumbing, Drain Services, Water Heater Installation

# ZIP codes at various distances from 33442
ZIP_CODES = {
    "33442": {"city": "Deerfield Beach", "state": "FL", "distance": 0},
    "33441": {"city": "Deerfield Beach", "state": "FL", "distance": 2},
    "33064": {"city": "Pompano Beach", "state": "FL", "distance": 5},
    "33060": {"city": "Pompano Beach", "state": "FL", "distance": 8},
    "33428": {"city": "Boca Raton", "state": "FL", "distance": 10},
    "33062": {"city": "Pompano Beach", "state": "FL", "distance": 12},
    "33308": {"city": "Fort Lauderdale", "state": "FL", "distance": 15},
    "33301": {"city": "Fort Lauderdale", "state": "FL", "distance": 20},
    "33020": {"city": "Hollywood", "state": "FL", "distance": 25},
    "33160": {"city": "Sunny Isles Beach", "state": "FL", "distance": 30},
    "33139": {"city": "Miami Beach", "state": "FL", "distance": 40},
    "33101": {"city": "Miami", "state": "FL", "distance": 45},
    "32801": {"city": "Orlando", "state": "FL", "distance": 180},  # Far test
}

# Test bid cards with proper schema fields
TEST_BID_CARDS = [
    # EXACT MATCHES - Should be found by Mike's search (Plumbing projects)
    {
        "project_type": "Plumbing",
        "title": "Fix Kitchen Faucet and Garbage Disposal",
        "description": "Fix leaky kitchen faucet and replace garbage disposal",
        "budget_min": 500, "budget_max": 1500,
        "location_zip": "33442", "distance": 0,
        "urgency_level": "flexible",
        "categories": ["Plumbing", "Kitchen Repair"]
    },
    {
        "project_type": "Water Heater Installation",
        "title": "Replace Water Heater with Tankless System",
        "description": "Replace 50 gallon water heater with tankless system",
        "budget_min": 3000, "budget_max": 5000,
        "location_zip": "33441", "distance": 2,
        "urgency_level": "urgent",
        "categories": ["Water Heater", "Plumbing Installation"]
    },
    {
        "project_type": "Drain Services",
        "title": "Clear Main Sewer Line Blockage",
        "description": "Clear main sewer line blockage and camera inspection",
        "budget_min": 800, "budget_max": 1500,
        "location_zip": "33064", "distance": 5,
        "urgency_level": "emergency",
        "categories": ["Drain Services", "Sewer Repair"]
    },
    {
        "project_type": "Plumbing Repair",
        "title": "Multiple Bathroom Fixture Repairs",
        "description": "Multiple bathroom fixtures need repair - toilets running, shower dripping",
        "budget_min": 600, "budget_max": 1200,
        "location_zip": "33060", "distance": 8,
        "urgency_level": "week",
        "categories": ["Plumbing", "Bathroom Repair"]
    },
    {
        "project_type": "Plumbing",
        "title": "Install New Bathroom Fixtures",
        "description": "Install new bathroom fixtures and fix pipe leak under sink",
        "budget_min": 1500, "budget_max": 2500,
        "location_zip": "33428", "distance": 10,
        "urgency_level": "flexible",
        "categories": ["Plumbing Installation", "Bathroom"]
    },
    {
        "project_type": "Water Heater Repair",
        "title": "Water Heater Not Producing Hot Water",
        "description": "Water heater not producing hot water, needs diagnosis and repair",
        "budget_min": 400, "budget_max": 800,
        "location_zip": "33062", "distance": 12,
        "urgency_level": "urgent",
        "categories": ["Water Heater", "Repair"]
    },
    {
        "project_type": "Drain Cleaning",
        "title": "Kitchen Sink and Dishwasher Backup",
        "description": "Kitchen sink and dishwasher backing up, need drain cleaned",
        "budget_min": 300, "budget_max": 600,
        "location_zip": "33308", "distance": 15,
        "urgency_level": "week",
        "categories": ["Drain Services", "Kitchen"]
    },
    {
        "project_type": "Plumbing Installation",
        "title": "Add Outdoor Faucet and Water Line",
        "description": "Add new outdoor faucet and install water line to garage",
        "budget_min": 1200, "budget_max": 2000,
        "location_zip": "33301", "distance": 20,
        "urgency_level": "flexible",
        "categories": ["Plumbing", "Installation"]
    },
    {
        "project_type": "Sewer Line Repair",
        "title": "Tree Roots in Sewer Line",
        "description": "Tree roots in sewer line causing backups, need repair or replacement",
        "budget_min": 3000, "budget_max": 6000,
        "location_zip": "33020", "distance": 25,
        "urgency_level": "urgent",
        "categories": ["Sewer", "Plumbing Repair"]
    },
    {
        "project_type": "Plumbing",
        "title": "Master Bathroom Plumbing Remodel",
        "description": "Remodel master bathroom plumbing for new layout",
        "budget_min": 4000, "budget_max": 7000,
        "location_zip": "33160", "distance": 30,
        "urgency_level": "month",
        "categories": ["Plumbing", "Bathroom Remodel"]
    },
    
    # EDGE CASES - Test boundary conditions
    {
        "project_type": "Emergency Plumbing",
        "title": "Pipe Burst - EMERGENCY",
        "description": "Pipe burst flooding basement - EMERGENCY SERVICE NEEDED",
        "budget_min": 2000, "budget_max": 5000,
        "location_zip": "33139", "distance": 40,
        "urgency_level": "emergency",
        "categories": ["Emergency", "Plumbing"]
    },
    {
        "project_type": "Commercial Plumbing",
        "title": "Restaurant Plumbing Installation",
        "description": "Commercial plumbing for restaurant - grease trap and floor drains",
        "budget_min": 10000, "budget_max": 20000,
        "location_zip": "33101", "distance": 45,
        "urgency_level": "month",
        "categories": ["Commercial", "Plumbing"]
    },
    
    # NON-MATCHES - Different trades (should NOT match)
    {
        "project_type": "Landscaping",
        "title": "Front Yard Landscaping Redesign",
        "description": "Front yard landscaping redesign with new plants and mulch",
        "budget_min": 2000, "budget_max": 4000,
        "location_zip": "33442", "distance": 0,
        "urgency_level": "flexible",
        "categories": ["Landscaping", "Yard Work"]
    },
    {
        "project_type": "Electrical",
        "title": "Upgrade Electrical Panel",
        "description": "Upgrade electrical panel from 100 to 200 amp service",
        "budget_min": 3000, "budget_max": 5000,
        "location_zip": "33441", "distance": 2,
        "urgency_level": "week",
        "categories": ["Electrical", "Panel Upgrade"]
    },
    {
        "project_type": "Roofing",
        "title": "Replace Shingle Roof",
        "description": "Replace shingle roof with metal roof",
        "budget_min": 12000, "budget_max": 18000,
        "location_zip": "33064", "distance": 5,
        "urgency_level": "month",
        "categories": ["Roofing", "Home Improvement"]
    },
    {
        "project_type": "HVAC",
        "title": "Replace Central AC Unit",
        "description": "Replace central AC unit and ductwork",
        "budget_min": 6000, "budget_max": 10000,
        "location_zip": "33060", "distance": 8,
        "urgency_level": "week",
        "categories": ["HVAC", "Cooling"]
    },
    
    # FAR AWAY TEST - Orlando (180 miles)
    {
        "project_type": "Plumbing",
        "title": "Orlando Plumbing Project",
        "description": "Plumbing project in Orlando - should be outside all reasonable radii",
        "budget_min": 2000, "budget_max": 3000,
        "location_zip": "32801", "distance": 180,
        "urgency_level": "flexible",
        "categories": ["Plumbing", "Far Distance Test"]
    }
]

def generate_bid_card_number():
    """Generate a unique bid card number"""
    timestamp = int(datetime.now().timestamp())
    return f"BC-TEST-{timestamp}-{uuid.uuid4().hex[:6].upper()}"

def create_bid_cards():
    """Create test bid cards in the database"""
    db = SupabaseDB()
    
    print("=" * 60)
    print("CREATING TEST BID CARDS FOR BSA RADIUS TESTING")
    print("Mike's Plumbing - ZIP: 33442 (Boca Raton/Deerfield Beach)")
    print("=" * 60)
    
    created_count = 0
    failed_count = 0
    
    # First, clear any existing test bid cards
    try:
        # Delete existing test bid cards
        result = db.client.table('bid_cards').delete().like('bid_card_number', 'BC-TEST-%').execute()
        if result.data:
            print(f"Cleared {len(result.data)} existing test bid cards")
    except Exception as e:
        print(f"Note: Could not clear existing test cards: {e}")
    
    for i, card_data in enumerate(TEST_BID_CARDS, 1):
        zip_info = ZIP_CODES.get(card_data["location_zip"], {"city": "Unknown", "state": "FL"})
        
        # Build the bid card with all required fields
        bid_card = {
            "bid_card_number": generate_bid_card_number(),
            "project_type": card_data["project_type"],
            "title": card_data["title"],
            "description": card_data["description"],
            "budget_min": card_data["budget_min"],
            "budget_max": card_data["budget_max"],
            "location_zip": card_data["location_zip"],
            "location_city": zip_info["city"],
            "location_state": zip_info["state"],
            "urgency_level": card_data["urgency_level"],
            "status": "active",
            "contractor_count_needed": 4,
            "complexity_score": 3,
            "categories": card_data.get("categories", []),
            "timeline_flexibility": "flexible" if card_data["urgency_level"] == "flexible" else "strict",
            "landing_page_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        try:
            result = db.client.table('bid_cards').insert(bid_card).execute()
            if result.data:
                created_count += 1
                distance = card_data["distance"]
                
                # Determine if this should match Mike's specialties
                is_match = any(keyword in card_data["project_type"].lower() 
                             for keyword in ["plumb", "drain", "water heater", "sewer"])
                match_str = "✓ MATCH" if is_match else "✗ NO MATCH"
                
                print(f"{i:2}. Created: {card_data['project_type'][:30]:<30} | "
                      f"ZIP: {card_data['location_zip']} ({distance:3}mi) | {match_str}")
        except Exception as e:
            failed_count += 1
            print(f"{i:2}. Failed: {card_data['project_type'][:30]:<30} - {str(e)[:50]}")
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: Created {created_count}/{len(TEST_BID_CARDS)} bid cards")
    print(f"Failed: {failed_count}")
    print("=" * 60)
    
    return created_count

def test_radius_search():
    """Test the search_bid_cards function with different radius values"""
    print("\n" + "=" * 60)
    print("TESTING BSA RADIUS SEARCH")
    print("=" * 60)
    
    # Import the search function
    from agents.bsa.bsa_deepagents import search_bid_cards
    import asyncio
    
    async def run_tests():
        test_radii = [5, 10, 25, 50, 100]
        contractor_zip = "33442"  # Mike's Plumbing location
        
        print(f"\nSearching from ZIP: {contractor_zip} (Mike's Plumbing)")
        print("-" * 40)
        
        for radius in test_radii:
            print(f"\n--- Radius: {radius} miles ---")
            
            # Test 1: Search for ALL projects within radius
            all_result = await search_bid_cards(contractor_zip, radius, None)
            print(f"ALL projects: {all_result['total_found']} found")
            
            # Test 2: Search for PLUMBING projects
            plumb_result = await search_bid_cards(contractor_zip, radius, "Plumbing")
            print(f"PLUMBING projects: {plumb_result['total_found']} found")
            
            # Test 3: Search for DRAIN projects  
            drain_result = await search_bid_cards(contractor_zip, radius, "Drain")
            print(f"DRAIN projects: {drain_result['total_found']} found")
            
            # Test 4: Search for WATER HEATER projects
            water_result = await search_bid_cards(contractor_zip, radius, "Water Heater")
            print(f"WATER HEATER projects: {water_result['total_found']} found")
            
            # Test 5: Search for non-matching category
            hvac_result = await search_bid_cards(contractor_zip, radius, "HVAC")
            print(f"HVAC projects (should be 0): {hvac_result['total_found']} found")
            
            # Show sample results for plumbing search
            if plumb_result['total_found'] > 0 and plumb_result.get('bid_cards'):
                print(f"\n  Sample plumbing projects found:")
                for card in plumb_result['bid_cards'][:3]:  # Show first 3
                    print(f"    - {card['project_type']} in {card['location_zip']} "
                          f"({card['location_city']}): ${card['budget_min']}-${card['budget_max']}")
    
    asyncio.run(run_tests())

if __name__ == "__main__":
    # Create test bid cards
    created = create_bid_cards()
    
    if created > 0:
        # Test the search functionality
        test_radius_search()
    else:
        print("\nNo bid cards created, skipping search tests")