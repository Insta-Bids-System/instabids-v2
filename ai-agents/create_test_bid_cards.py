"""
Create test bid cards for Mike's Plumbing with various ZIP codes and project types
Tests radius search and category matching
"""

import requests
import json
from datetime import datetime, timedelta

# Mike's Plumbing profile:
# - Location: Boca Raton, FL 33442
# - Specialties: Plumbing, Drain Services, Water Heater Installation

# ZIP codes at various distances from 33442 (Boca Raton/Deerfield Beach)
ZIP_CODES = {
    "33442": {"city": "Deerfield Beach", "state": "FL", "distance": 0},     # Same ZIP
    "33441": {"city": "Deerfield Beach", "state": "FL", "distance": 2},     # 2 miles
    "33064": {"city": "Pompano Beach", "state": "FL", "distance": 5},      # 5 miles
    "33060": {"city": "Pompano Beach", "state": "FL", "distance": 8},      # 8 miles
    "33428": {"city": "Boca Raton", "state": "FL", "distance": 10},        # 10 miles
    "33062": {"city": "Pompano Beach", "state": "FL", "distance": 12},     # 12 miles
    "33308": {"city": "Fort Lauderdale", "state": "FL", "distance": 15},   # 15 miles
    "33301": {"city": "Fort Lauderdale", "state": "FL", "distance": 20},   # 20 miles
    "33020": {"city": "Hollywood", "state": "FL", "distance": 25},         # 25 miles
    "33160": {"city": "Sunny Isles Beach", "state": "FL", "distance": 30}, # 30 miles
    "33139": {"city": "Miami Beach", "state": "FL", "distance": 40},       # 40 miles
    "33101": {"city": "Miami", "state": "FL", "distance": 45},            # 45 miles
}

# Test bid cards with different project types
TEST_BID_CARDS = [
    # EXACT MATCH - Plumbing projects (should match Mike's specialties)
    {
        "project_type": "Plumbing",
        "description": "Fix leaky kitchen faucet and replace garbage disposal",
        "budget_range_min": 500,
        "budget_range_max": 1500,
        "timeline": "1-2 days",
        "zip_code": "33442"  # Same ZIP - 0 miles
    },
    {
        "project_type": "Water Heater Installation",
        "description": "Replace 50 gallon water heater with tankless system",
        "budget_range_min": 3000,
        "budget_range_max": 5000,
        "timeline": "2-3 days",
        "zip_code": "33441"  # 2 miles away
    },
    {
        "project_type": "Drain Services",
        "description": "Clear main sewer line blockage and camera inspection",
        "budget_range_min": 800,
        "budget_range_max": 1500,
        "timeline": "Emergency - ASAP",
        "zip_code": "33064"  # 5 miles away
    },
    {
        "project_type": "Plumbing Repair",
        "description": "Multiple bathroom fixtures need repair - toilets running, shower dripping",
        "budget_range_min": 600,
        "budget_range_max": 1200,
        "timeline": "This week",
        "zip_code": "33060"  # 8 miles away
    },
    {
        "project_type": "Plumbing",
        "description": "Install new bathroom fixtures and fix pipe leak under sink",
        "budget_range_min": 1500,
        "budget_range_max": 2500,
        "timeline": "Flexible",
        "zip_code": "33428"  # 10 miles away
    },
    {
        "project_type": "Water Heater Repair",
        "description": "Water heater not producing hot water, needs diagnosis and repair",
        "budget_range_min": 400,
        "budget_range_max": 800,
        "timeline": "ASAP",
        "zip_code": "33062"  # 12 miles away
    },
    {
        "project_type": "Drain Cleaning",
        "description": "Kitchen sink and dishwasher backing up, need drain cleaned",
        "budget_range_min": 300,
        "budget_range_max": 600,
        "timeline": "2-3 days",
        "zip_code": "33308"  # 15 miles away
    },
    {
        "project_type": "Plumbing Installation",
        "description": "Add new outdoor faucet and install water line to garage",
        "budget_range_min": 1200,
        "budget_range_max": 2000,
        "timeline": "Next week",
        "zip_code": "33301"  # 20 miles away
    },
    {
        "project_type": "Sewer Line Repair",
        "description": "Tree roots in sewer line causing backups, need repair or replacement",
        "budget_range_min": 3000,
        "budget_range_max": 6000,
        "timeline": "Urgent",
        "zip_code": "33020"  # 25 miles away
    },
    {
        "project_type": "Plumbing",
        "description": "Remodel master bathroom plumbing for new layout",
        "budget_range_min": 4000,
        "budget_range_max": 7000,
        "timeline": "1 month",
        "zip_code": "33160"  # 30 miles away
    },
    
    # PARTIAL MATCH - Related but not exact
    {
        "project_type": "Bathroom Remodel",
        "description": "Full bathroom remodel including plumbing fixture replacement",
        "budget_range_min": 8000,
        "budget_range_max": 12000,
        "timeline": "6 weeks",
        "zip_code": "33441"  # 2 miles - has plumbing in description
    },
    {
        "project_type": "Kitchen Renovation",
        "description": "Kitchen update including new sink plumbing and dishwasher installation",
        "budget_range_min": 15000,
        "budget_range_max": 25000,
        "timeline": "2 months",
        "zip_code": "33064"  # 5 miles - has plumbing in description
    },
    
    # NO MATCH - Different trades (should NOT match)
    {
        "project_type": "Landscaping",
        "description": "Front yard landscaping redesign with new plants and mulch",
        "budget_range_min": 2000,
        "budget_range_max": 4000,
        "timeline": "2 weeks",
        "zip_code": "33442"  # Same ZIP but wrong trade
    },
    {
        "project_type": "Electrical",
        "description": "Upgrade electrical panel from 100 to 200 amp service",
        "budget_range_min": 3000,
        "budget_range_max": 5000,
        "timeline": "1 week",
        "zip_code": "33441"  # 2 miles - wrong trade
    },
    {
        "project_type": "Roofing",
        "description": "Replace shingle roof with metal roof",
        "budget_range_min": 12000,
        "budget_range_max": 18000,
        "timeline": "2 weeks",
        "zip_code": "33064"  # 5 miles - wrong trade
    },
    {
        "project_type": "HVAC",
        "description": "Replace central AC unit and ductwork",
        "budget_range_min": 6000,
        "budget_range_max": 10000,
        "timeline": "1 week",
        "zip_code": "33060"  # 8 miles - wrong trade
    },
    
    # EDGE CASES - Test boundary conditions
    {
        "project_type": "Emergency Plumbing",
        "description": "Pipe burst flooding basement - EMERGENCY SERVICE NEEDED",
        "budget_range_min": 2000,
        "budget_range_max": 5000,
        "timeline": "IMMEDIATE",
        "zip_code": "33139"  # 40 miles - outside typical radius
    },
    {
        "project_type": "Plumbing",
        "description": "Commercial plumbing for restaurant - grease trap and floor drains",
        "budget_range_min": 10000,
        "budget_range_max": 20000,
        "timeline": "1 month",
        "zip_code": "33101"  # 45 miles - far away
    }
]

def create_bid_cards():
    """Create all test bid cards in the database"""
    
    print("=" * 60)
    print("CREATING TEST BID CARDS FOR MIKE'S PLUMBING")
    print("=" * 60)
    
    created_count = 0
    failed_count = 0
    
    for i, card_data in enumerate(TEST_BID_CARDS, 1):
        # Get city/state from ZIP
        zip_info = ZIP_CODES.get(card_data["zip_code"], {"city": "Unknown", "state": "FL", "distance": 99})
        
        # Build the bid card
        bid_card = {
            "project_type": card_data["project_type"],
            "description": card_data["description"],
            "budget_range_min": card_data["budget_range_min"],
            "budget_range_max": card_data["budget_range_max"],
            "timeline": card_data["timeline"],
            "zip_code": card_data["zip_code"],
            "city": zip_info["city"],
            "state": zip_info["state"],
            "status": "active",  # Make all active for testing
            "urgency_level": "urgent" if "emergency" in card_data["description"].lower() or "asap" in card_data["timeline"].lower() else "flexible",
            "allows_questions": True,
            "group_bid_eligible": card_data["budget_range_max"] > 5000,  # Group bid for larger projects
            "visibility": "public"
        }
        
        # Try multiple endpoints
        endpoints = [
            "/api/iris/actions/create-bid-card",
            "/api/bid-cards",
            "/api/bid-cards/simple-create"
        ]
        
        created = False
        for endpoint in endpoints:
            try:
                # For IRIS endpoint, wrap in proper format
                if "iris" in endpoint:
                    payload = {
                        "request_id": f"test_create_{i}_{datetime.now().timestamp()}",
                        "agent_name": "TEST",
                        "property_id": "test-property-123",
                        "bid_card_data": bid_card
                    }
                else:
                    payload = bid_card
                
                response = requests.post(
                    f"http://localhost:8008{endpoint}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    created_count += 1
                    distance = zip_info["distance"]
                    match_type = "EXACT" if "plumb" in card_data["project_type"].lower() or "drain" in card_data["project_type"].lower() or "water heater" in card_data["project_type"].lower() else "NO MATCH"
                    
                    print(f"{i:2}. ✓ Created: {card_data['project_type'][:30]:<30} | ZIP: {card_data['zip_code']} ({distance:2} mi) | {match_type}")
                    created = True
                    break
                    
            except Exception as e:
                continue
        
        if not created:
            failed_count += 1
            print(f"{i:2}. ✗ Failed: {card_data['project_type'][:30]:<30} | ZIP: {card_data['zip_code']}")
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: Created {created_count}/{len(TEST_BID_CARDS)} bid cards")
    print(f"Failed: {failed_count}")
    print("=" * 60)
    
    # Now test the search with different radius values
    print("\nTESTING RADIUS SEARCH:")
    print("-" * 40)
    
    test_radii = [5, 10, 25, 50]
    
    for radius in test_radii:
        # Search for plumbing projects within radius
        response = requests.get(
            f"http://localhost:8008/api/bid-cards/search",
            params={
                "zip_code": "33442",
                "radius_miles": radius,
                "status": "active"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            print(f"Radius {radius:2} miles: Found {total} bid cards")
            
            # Count by project type
            if data.get("bid_cards"):
                plumbing_count = sum(1 for card in data["bid_cards"] if "plumb" in card.get("project_type", "").lower())
                drain_count = sum(1 for card in data["bid_cards"] if "drain" in card.get("project_type", "").lower())
                water_heater_count = sum(1 for card in data["bid_cards"] if "water heater" in card.get("project_type", "").lower())
                other_count = total - plumbing_count - drain_count - water_heater_count
                
                print(f"  - Plumbing: {plumbing_count}")
                print(f"  - Drain: {drain_count}")
                print(f"  - Water Heater: {water_heater_count}")
                print(f"  - Other: {other_count}")
        else:
            print(f"Radius {radius:2} miles: Search failed")

if __name__ == "__main__":
    create_bid_cards()