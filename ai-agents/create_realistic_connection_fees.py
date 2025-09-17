#!/usr/bin/env python3
"""
Create realistic connection fee test data with complete contractor details
This script creates comprehensive test scenarios for the admin panel
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import uuid
import random
from datetime import datetime, timedelta
from database_simple import db

# Realistic contractor data
REALISTIC_CONTRACTORS = [
    {
        "company_name": "Elite Kitchen & Bath Solutions",
        "contact_name": "Michael Rodriguez",
        "phone": "(555) 234-5678",
        "email": "mike@elitekitchenbath.com",
        "specialties": ["Kitchen Renovation", "Bathroom Remodel", "Custom Cabinetry"],
        "years_experience": 15,
        "license_number": "KB-2024-8901",
        "rating": 4.8,
        "total_projects": 127
    },
    {
        "company_name": "SunCoast Roofing & Exteriors",
        "contact_name": "Jennifer Martinez",
        "phone": "(555) 345-6789", 
        "email": "j.martinez@suncoastroofing.com",
        "specialties": ["Emergency Roof Repair", "Roof Replacement", "Gutter Installation"],
        "years_experience": 12,
        "license_number": "RF-2024-5567",
        "rating": 4.9,
        "total_projects": 203
    },
    {
        "company_name": "GreenScape Landscape Design",
        "contact_name": "David Chen", 
        "phone": "(555) 456-7890",
        "email": "david@greenscapeld.com",
        "specialties": ["Landscape Design", "Irrigation Systems", "Outdoor Lighting"],
        "years_experience": 8,
        "license_number": "LS-2024-3344",
        "rating": 4.7,
        "total_projects": 89
    },
    {
        "company_name": "Premier HVAC Solutions",
        "contact_name": "Sarah Johnson",
        "phone": "(555) 567-8901",
        "email": "sarah.johnson@premierhvac.com", 
        "specialties": ["HVAC Installation", "AC Repair", "Duct Cleaning"],
        "years_experience": 18,
        "license_number": "HV-2024-7788",
        "rating": 4.6,
        "total_projects": 156
    },
    {
        "company_name": "Artisan Flooring Masters",
        "contact_name": "Robert Thompson",
        "phone": "(555) 678-9012",
        "email": "rob@artisanflooringmasters.com",
        "specialties": ["Hardwood Flooring", "Tile Installation", "Carpet Installation"],
        "years_experience": 22,
        "license_number": "FL-2024-9900",
        "rating": 4.9,
        "total_projects": 298
    }
]

# Realistic project scenarios
PROJECT_SCENARIOS = [
    {
        "title": "Modern Kitchen Renovation - Downtown Condo",
        "project_type": "Kitchen Renovation",
        "homeowner_name": "Emily & James Wilson",
        "homeowner_email": "emily.wilson@email.com",
        "winning_bid_amount": 35000,
        "project_category": "year_round",
        "category_adjustment": -10500,  # 30% discount
        "urgency": "standard"
    },
    {
        "title": "Emergency Roof Leak Repair - Coral Gables",
        "project_type": "Emergency Roof Repair", 
        "homeowner_name": "Marcus Rodriguez",
        "homeowner_email": "m.rodriguez@email.com",
        "winning_bid_amount": 8500,
        "project_category": "emergency",
        "category_adjustment": 2125,  # 25% increase
        "urgency": "emergency"
    },
    {
        "title": "Backyard Landscape Transformation",
        "project_type": "Landscape Design",
        "homeowner_name": "Patricia & Tom Anderson",
        "homeowner_email": "patricia.anderson@email.com", 
        "winning_bid_amount": 22000,
        "project_category": "year_round",
        "category_adjustment": -6600,  # 30% discount
        "urgency": "standard"
    },
    {
        "title": "HVAC System Replacement - 3BR Home",
        "project_type": "HVAC Installation",
        "homeowner_name": "Lisa Chen",
        "homeowner_email": "lisa.chen@email.com",
        "winning_bid_amount": 12000,
        "project_category": "standard",
        "category_adjustment": 0,
        "urgency": "standard"
    },
    {
        "title": "Master Bedroom Hardwood Installation",
        "project_type": "Hardwood Flooring",
        "homeowner_name": "Michael & Sandra Davis",
        "homeowner_email": "michael.davis@email.com",
        "winning_bid_amount": 15500,
        "project_category": "year_round", 
        "category_adjustment": -4650,  # 30% discount
        "urgency": "standard",
        "referral_code": "FRIEND2024",
        "referrer_email": "jennifer.taylor@email.com"
    }
]

def calculate_connection_fee(bid_amount, project_category, has_referral=False):
    """Calculate connection fee based on bid amount and category"""
    # Progressive fee structure
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
    
    # Category adjustments
    category_multiplier = 1.0
    if project_category == "emergency":
        category_multiplier = 1.25  # 25% increase
    elif project_category == "year_round":
        category_multiplier = 0.7   # 30% decrease
    
    adjusted_fee = base_fee * category_multiplier
    
    # Referral split (50/50)
    final_fee = adjusted_fee
    referrer_payout = 0
    if has_referral:
        referrer_payout = adjusted_fee * 0.5
        # Final fee stays the same, but referrer gets 50%
    
    return {
        "base_fee": base_fee,
        "adjusted_fee": adjusted_fee,
        "final_fee": final_fee,
        "referrer_payout": referrer_payout
    }

def create_realistic_connection_fees():
    """Create comprehensive test data for connection fees"""
    print("🎯 Creating realistic connection fee test data...")
    
    created_fees = []
    
    for i, (contractor, project) in enumerate(zip(REALISTIC_CONTRACTORS, PROJECT_SCENARIOS)):
        print(f"\n📋 Creating scenario {i+1}: {project['title']}")
        
        try:
            # 1. Create/Update contractor with complete details
            contractor_id = str(uuid.uuid4())
            
            # Check if contractor already exists
            existing = db.client.table("contractors").select("id").eq("company_name", contractor["company_name"]).execute()
            
            if existing.data:
                contractor_id = existing.data[0]["id"]
                print(f"   ✅ Using existing contractor: {contractor['company_name']}")
            else:
                contractor_data = {
                    "id": contractor_id,
                    "company_name": contractor["company_name"],
                    "contact_name": contractor["contact_name"],
                    "phone": contractor["phone"],
                    "email": contractor["email"],
                    "license_number": contractor["license_number"],
                    "rating": contractor["rating"],
                    "total_jobs": contractor["total_projects"],
                    "years_in_business": contractor["years_experience"],
                    "specialties": contractor["specialties"],
                    "verified": True,
                    "tier": 1,
                    "created_at": datetime.now().isoformat()
                }
                
                result = db.client.table("contractors").insert(contractor_data).execute()
                print(f"   ✅ Created contractor: {contractor['company_name']}")
            
            # 2. Create realistic bid card
            bid_card_id = str(uuid.uuid4())
            bid_card_number = f"BC-{random.randint(100000, 999999)}"
            
            bid_card_data = {
                "id": bid_card_id,
                "bid_card_number": bid_card_number,
                "title": project["title"],
                "project_type": project["project_type"],
                "homeowner_name": project["homeowner_name"],
                "homeowner_email": project["homeowner_email"],
                "winner_contractor_id": contractor_id,
                "status": "bids_complete",
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 14))).isoformat()
            }
            
            bid_result = db.client.table("bid_cards").insert(bid_card_data).execute()
            print(f"   ✅ Created bid card: {bid_card_number}")
            
            # 3. Calculate connection fee
            has_referral = "referral_code" in project
            fee_calc = calculate_connection_fee(
                project["winning_bid_amount"], 
                project["project_category"],
                has_referral
            )
            
            # 4. Create connection fee record
            fee_id = str(uuid.uuid4())
            
            # Determine fee status (mix of paid/unpaid/overdue)
            fee_statuses = ["calculated", "calculated", "paid", "calculated"]  # More unpaid than paid
            fee_status = random.choice(fee_statuses)
            
            days_ago = random.randint(0, 21)  # 0-21 days ago
            created_date = datetime.now() - timedelta(days=days_ago)
            
            # If older than 7 days and unpaid, mark as overdue
            if days_ago > 7 and fee_status == "calculated":
                fee_status = "calculated"  # Keep as calculated but overdue by days
            
            connection_fee_data = {
                "id": fee_id,
                "bid_card_id": bid_card_id,
                "contractor_id": contractor_id,
                "user_id": str(uuid.uuid4()),  # Mock homeowner ID
                "winning_bid_amount": project["winning_bid_amount"],
                "base_fee_amount": fee_calc["base_fee"],
                "final_fee_amount": fee_calc["final_fee"],
                "project_category": project["project_category"],
                "calculation_method": "progressive_bid_amount_v1.0",
                "fee_status": fee_status,
                "calculated_at": created_date.isoformat(),
                "created_at": created_date.isoformat(),
                "payment_processed_at": datetime.now().isoformat() if fee_status == "paid" else None
            }
            
            fee_result = db.client.table("connection_fees").insert(connection_fee_data).execute()
            print(f"   ✅ Created connection fee: ${fee_calc['final_fee']} ({fee_status})")
            
            # 5. Create referral tracking if applicable
            if has_referral:
                referral_data = {
                    "id": str(uuid.uuid4()),
                    "connection_fee_id": fee_id,
                    "referrer_user_id": str(uuid.uuid4()),
                    "referred_user_id": str(uuid.uuid4()),
                    "referral_code": project["referral_code"],
                    "referrer_payout_amount": fee_calc["referrer_payout"],
                    "payout_status": "processed" if fee_status == "paid" else "pending",
                    "payout_processed_at": datetime.now().isoformat() if fee_status == "paid" else None,
                    "created_at": created_date.isoformat()
                }
                
                referral_result = db.client.table("referral_tracking").insert(referral_data).execute()
                print(f"   ✅ Created referral tracking: {project['referral_code']} (${fee_calc['referrer_payout']} to referrer)")
            
            created_fees.append({
                "contractor": contractor["company_name"],
                "project": project["title"], 
                "bid_amount": project["winning_bid_amount"],
                "fee_amount": fee_calc["final_fee"],
                "status": fee_status,
                "days_ago": days_ago
            })
            
        except Exception as e:
            print(f"   ❌ Error creating scenario {i+1}: {str(e)}")
            continue
    
    print(f"\n🎉 Successfully created {len(created_fees)} realistic connection fee scenarios!")
    print("\n📊 Summary:")
    for fee in created_fees:
        overdue_text = f" ({fee['days_ago']} days ago)" if fee['days_ago'] > 7 and fee['status'] == 'calculated' else ""
        print(f"   • {fee['contractor']}: ${fee['bid_amount']} → ${fee['fee_amount']} ({fee['status']}){overdue_text}")
    
    return created_fees

if __name__ == "__main__":
    created_fees = create_realistic_connection_fees()
    print(f"\n✅ Test data creation complete! Created {len(created_fees)} connection fees.")
    print("🔗 Now check the admin panel: http://localhost:5173/admin/connection-fees")