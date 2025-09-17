"""
Create test bid cards directly in database for Mike's Plumbing testing
"""

from database import SupabaseDB
from datetime import datetime
import uuid

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
}

# Test bid cards
TEST_BID_CARDS = [
    # EXACT MATCHES - Should be found by Mike's search
    {
        "project_type": "Plumbing",
        "description": "Fix leaky kitchen faucet and replace garbage disposal",
        "budget_min": 500, "budget_max": 1500,
        "zip_code": "33442", "distance": 0
    },
    {
        "project_type": "Water Heater Installation",
        "description": "Replace 50 gallon water heater with tankless system",
        "budget_min": 3000, "budget_max": 5000,
        "zip_code": "33441", "distance": 2
    },
    {
        "project_type": "Drain Services",
        "description": "Clear main sewer line blockage and camera inspection",
        "budget_min": 800, "budget_max": 1500,
        "zip_code": "33064", "distance": 5
    },
    {
        "project_type": "Plumbing Repair",
        "description": "Multiple bathroom fixtures need repair",
        "budget_min": 600, "budget_max": 1200,
        "zip_code": "33060", "distance": 8
    },
    {
        "project_type": "Plumbing Installation",
        "description": "Install new bathroom fixtures and fix pipe leak",
        "budget_min": 1500, "budget_max": 2500,
        "zip_code": "33428", "distance": 10
    },
    {
        "project_type": "Water Heater Repair",
        "description": "Water heater not producing hot water",
        "budget_min": 400, "budget_max": 800,
        "zip_code": "33062", "distance": 12
    },
    {
        "project_type": "Drain Cleaning",
        "description": "Kitchen sink and dishwasher backing up",
        "budget_min": 300, "budget_max": 600,
        "zip_code": "33308", "distance": 15
    },
    {
        "project_type": "Sewer Line Repair",
        "description": "Tree roots in sewer line causing backups",
        "budget_min": 3000, "budget_max": 6000,
        "zip_code": "33020", "distance": 25
    },
    {
        "project_type": "Plumbing",
        "description": "Remodel master bathroom plumbing for new layout",
        "budget_min": 4000, "budget_max": 7000,
        "zip_code": "33160", "distance": 30
    },
    
    # NON-MATCHES - Different trades
    {
        "project_type": "Landscaping",
        "description": "Front yard landscaping redesign",
        "budget_min": 2000, "budget_max": 4000,
        "zip_code": "33442", "distance": 0
    },
    {
        "project_type": "Electrical",
        "description": "Upgrade electrical panel to 200 amp",
        "budget_min": 3000, "budget_max": 5000,
        "zip_code": "33441", "distance": 2
    },
    {
        "project_type": "HVAC",
        "description": "Replace central AC unit",
        "budget_min": 6000, "budget_max": 10000,
        "zip_code": "33064", "distance": 5
    }
]

def create_bid_cards():
    db = SupabaseDB()
    
    print("=" * 60)
    print("CREATING TEST BID CARDS FOR MIKE'S PLUMBING")
    print("=" * 60)
    
    created_count = 0
    
    for i, card_data in enumerate(TEST_BID_CARDS, 1):
        zip_info = ZIP_CODES.get(card_data["zip_code"], {"city": "Unknown", "state": "FL"})
        
        # Create bid card data
        bid_card = {
            "id": str(uuid.uuid4()),
            "project_type": card_data["project_type"],
            "description": card_data["description"],
            "budget_range_min": card_data["budget_min"],
            "budget_range_max": card_data["budget_max"],
            "zip_code": card_data["zip_code"],
            "city": zip_info["city"],
            "state": zip_info["state"],
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        try:
            result = db.client.table('bid_cards').insert(bid_card).execute()
            if result.data:
                created_count += 1
                is_match = any(keyword in card_data["project_type"].lower() 
                             for keyword in ["plumb", "drain", "water heater", "sewer"])
                match_str = "MATCH" if is_match else "NO MATCH"
                print(f"{i:2}. Created: {card_data['project_type'][:25]:<25} | ZIP: {card_data['zip_code']} ({card_data['distance']:2}mi) | {match_str}")
        except Exception as e:
            print(f"{i:2}. Failed: {card_data['project_type'][:25]} - {str(e)[:30]}")
    
    print(f"\nCreated {created_count}/{len(TEST_BID_CARDS)} bid cards")
    return created_count

if __name__ == "__main__":
    created = create_bid_cards()
    
    if created > 0:
        print("\n" + "=" * 60)
        print("TESTING SEARCH WITH DIFFERENT RADIUS VALUES")
        print("=" * 60)
        
        # Now test the search function
        import asyncio
        from agents.bsa.bsa_deepagents import search_bid_cards
        
        async def test_searches():
            radii = [5, 10, 25, 50]
            
            for radius in radii:
                print(f"\n--- Radius: {radius} miles ---")
                
                # Search for ALL projects
                all_result = await search_bid_cards("33442", radius, None)
                print(f"ALL projects: {all_result['total_found']} found")
                
                # Search for PLUMBING projects
                plumb_result = await search_bid_cards("33442", radius, "Plumbing")
                print(f"PLUMBING projects: {plumb_result['total_found']} found")
                
                # Search for DRAIN projects
                drain_result = await search_bid_cards("33442", radius, "Drain")
                print(f"DRAIN projects: {drain_result['total_found']} found")
                
                # Search for WATER HEATER projects
                water_result = await search_bid_cards("33442", radius, "Water Heater")
                print(f"WATER HEATER projects: {water_result['total_found']} found")
        
        asyncio.run(test_searches())