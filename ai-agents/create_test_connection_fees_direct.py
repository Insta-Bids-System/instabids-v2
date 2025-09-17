#!/usr/bin/env python3
"""
Create realistic connection fee test data directly using Supabase
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import uuid
import random
from datetime import datetime, timedelta
from database_simple import db

def create_test_data():
    print("Creating realistic connection fee test data...")
    
    # Test scenarios
    scenarios = [
        {
            "contractor": {
                "company_name": "Elite Kitchen & Bath Solutions",
                "contact_name": "Michael Rodriguez", 
                "phone": "(555) 234-5678",
                "email": "mike@elitekitchenbath.com",
                "license_number": "KB-2024-8901",
                "rating": 4.8,
                "total_jobs": 127,
                "years_in_business": 15,
                "specialties": ["Kitchen Renovation", "Bathroom Remodel", "Custom Cabinetry"]
            },
            "project": {
                "title": "Modern Kitchen Renovation - Downtown Condo",
                "homeowner_name": "Emily & James Wilson",
                "bid_amount": 35000,
                "project_category": "year_round"
            }
        },
        {
            "contractor": {
                "company_name": "SunCoast Roofing & Exteriors", 
                "contact_name": "Jennifer Martinez",
                "phone": "(555) 345-6789",
                "email": "j.martinez@suncoastroofing.com", 
                "license_number": "RF-2024-5567",
                "rating": 4.9,
                "total_jobs": 203,
                "years_in_business": 12,
                "specialties": ["Emergency Roof Repair", "Roof Replacement", "Gutter Installation"]
            },
            "project": {
                "title": "Emergency Roof Leak Repair - Coral Gables",
                "homeowner_name": "Marcus Rodriguez",
                "bid_amount": 8500,
                "project_category": "emergency"
            }
        }
    ]
    
    for i, scenario in enumerate(scenarios):
        print(f"\nCreating scenario {i+1}: {scenario['project']['title']}")
        
        try:
            # Create contractor
            contractor_id = str(uuid.uuid4())
            contractor_data = {
                "id": contractor_id,
                **scenario["contractor"],
                "verified": True,
                "tier": 1,
                "created_at": datetime.now().isoformat()
            }
            
            # Check if contractor exists
            existing = db.client.table("contractors").select("id").eq("company_name", scenario["contractor"]["company_name"]).execute()
            if existing.data:
                contractor_id = existing.data[0]["id"]
                print(f"   Using existing contractor: {scenario['contractor']['company_name']}")
            else:
                result = db.client.table("contractors").insert(contractor_data).execute()
                print(f"   Created contractor: {scenario['contractor']['company_name']}")
            
            # Create bid card
            bid_card_id = str(uuid.uuid4())
            bid_card_number = f"BC-{random.randint(100000, 999999)}"
            bid_card_data = {
                "id": bid_card_id,
                "bid_card_number": bid_card_number,
                "title": scenario["project"]["title"],
                "homeowner_name": scenario["project"]["homeowner_name"],
                "winner_contractor_id": contractor_id,
                "status": "bids_complete",
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 14))).isoformat()
            }
            
            bid_result = db.client.table("bid_cards").insert(bid_card_data).execute()
            print(f"   Created bid card: {bid_card_number}")
            
            # Calculate fee
            bid_amount = scenario["project"]["bid_amount"]
            if bid_amount <= 5000:
                base_fee = 20
            elif bid_amount <= 10000:
                base_fee = 75
            elif bid_amount <= 15000:
                base_fee = 125
            elif bid_amount <= 25000:
                base_fee = 175
            elif bid_amount <= 40000:
                base_fee = 200
            else:
                base_fee = 250
            
            category_multiplier = 1.0
            if scenario["project"]["project_category"] == "emergency":
                category_multiplier = 1.25
            elif scenario["project"]["project_category"] == "year_round":
                category_multiplier = 0.7
            
            final_fee = base_fee * category_multiplier
            
            # Create connection fee
            fee_id = str(uuid.uuid4())
            fee_status = random.choice(["calculated", "paid", "calculated"])
            days_ago = random.randint(0, 21)
            created_date = datetime.now() - timedelta(days=days_ago)
            
            connection_fee_data = {
                "id": fee_id,
                "bid_card_id": bid_card_id,
                "contractor_id": contractor_id,
                "winning_bid_amount": bid_amount,
                "base_fee_amount": base_fee,
                "final_fee_amount": final_fee,
                "project_category": scenario["project"]["project_category"],
                "fee_status": fee_status,
                "created_at": created_date.isoformat()
            }
            
            fee_result = db.client.table("connection_fees").insert(connection_fee_data).execute()
            print(f"   Created connection fee: ${final_fee} ({fee_status})")
            
        except Exception as e:
            print(f"   Error creating scenario {i+1}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\nTest data creation complete!")

if __name__ == "__main__":
    create_test_data()