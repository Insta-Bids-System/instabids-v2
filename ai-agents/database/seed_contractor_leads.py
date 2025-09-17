"""
Seed contractor_leads table with test data
This populates the database with realistic contractor data for testing
"""
import os
from datetime import datetime

from dotenv import load_dotenv
from supabase import create_client


# Load environment variables
load_dotenv(override=True)

# Connect to Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test contractor data
test_contractors = [
    # Solo Handyman
    {
        "source": "manual",
        "company_name": "Mike's Handyman Service",
        "contact_name": "Mike Rodriguez",
        "phone": "407-555-0001",
        "email": "mike@handyman-orlando.com",
        "website": "https://mikeshandyman.com",
        "address": "123 Main St",
        "city": "Orlando",
        "state": "FL",
        "zip_code": "32801",
        "contractor_size": "solo_handyman",
        "estimated_employees": "1",
        "years_in_business": 5,
        "specialties": ["general repairs", "painting", "basic plumbing"],
        "rating": 4.7,
        "review_count": 89,
        "lead_score": 75,
        "lead_status": "qualified",
        "has_contact_form": True,
        "license_verified": False,
        "insurance_verified": True
    },

    # Owner Operator
    {
        "source": "google_maps",
        "company_name": "Johnson Kitchen & Bath",
        "contact_name": "Tom Johnson",
        "phone": "407-555-0002",
        "email": "tom@johnsonkitchenbath.com",
        "website": "https://johnsonkitchenbath.com",
        "address": "456 Oak Ave",
        "city": "Orlando",
        "state": "FL",
        "zip_code": "32803",
        "contractor_size": "owner_operator",
        "estimated_employees": "2-5",
        "years_in_business": 8,
        "specialties": ["kitchen remodeling", "bathroom remodeling", "tile work"],
        "rating": 4.8,
        "review_count": 156,
        "lead_score": 85,
        "lead_status": "qualified",
        "has_contact_form": True,
        "license_verified": True,
        "insurance_verified": True,
        "license_number": "FL-GC-123456"
    },

    # Small Business
    {
        "source": "yelp",
        "company_name": "Orlando Home Pros",
        "contact_name": "Sarah Williams",
        "phone": "407-555-0003",
        "email": "info@orlandohomepros.com",
        "website": "https://orlandohomepros.com",
        "address": "789 Pine Blvd",
        "city": "Orlando",
        "state": "FL",
        "zip_code": "32801",
        "contractor_size": "small_business",
        "estimated_employees": "6-10",
        "years_in_business": 12,
        "specialties": ["kitchen remodeling", "general contractor", "home additions"],
        "rating": 4.9,
        "review_count": 234,
        "lead_score": 92,
        "lead_status": "qualified",
        "has_contact_form": True,
        "license_verified": True,
        "insurance_verified": True,
        "license_number": "FL-GC-789012",
        "bonded": True
    },

    # Another Small Business
    {
        "source": "angi",
        "company_name": "Elite Remodeling Solutions",
        "contact_name": "David Chen",
        "phone": "407-555-0004",
        "email": "david@eliteremodeling.com",
        "website": "https://eliteremodeling.com",
        "address": "321 Elm St",
        "city": "Winter Park",
        "state": "FL",
        "zip_code": "32789",
        "contractor_size": "small_business",
        "estimated_employees": "11-20",
        "years_in_business": 15,
        "specialties": ["luxury kitchen remodeling", "custom cabinets", "high-end finishes"],
        "rating": 4.8,
        "review_count": 178,
        "lead_score": 88,
        "lead_status": "qualified",
        "has_contact_form": True,
        "license_verified": True,
        "insurance_verified": True,
        "license_number": "FL-GC-345678"
    },

    # Regional Company
    {
        "source": "bbb",
        "company_name": "Central Florida Construction Group",
        "contact_name": "Robert Martinez",
        "phone": "407-555-0005",
        "email": "info@cfcgroup.com",
        "website": "https://cfcgroup.com",
        "address": "1000 Corporate Dr",
        "city": "Orlando",
        "state": "FL",
        "zip_code": "32801",
        "contractor_size": "regional_company",
        "estimated_employees": "21-50",
        "years_in_business": 20,
        "specialties": ["commercial construction", "residential remodeling", "general contractor"],
        "rating": 4.5,
        "review_count": 412,
        "lead_score": 78,
        "lead_status": "qualified",
        "has_contact_form": True,
        "license_verified": True,
        "insurance_verified": True,
        "license_number": "FL-GC-567890",
        "bonded": True
    },

    # Contacted but not qualified
    {
        "source": "google_maps",
        "company_name": "Quick Fix Handyman",
        "contact_name": "Joe Smith",
        "phone": "407-555-0006",
        "email": "joe@quickfix.com",
        "city": "Orlando",
        "state": "FL",
        "zip_code": "32804",
        "contractor_size": "solo_handyman",
        "specialties": ["general repairs"],
        "rating": 3.8,
        "review_count": 23,
        "lead_score": 45,
        "lead_status": "contacted"
    },

    # New lead
    {
        "source": "facebook",
        "company_name": "Modern Kitchen Design",
        "phone": "407-555-0007",
        "city": "Orlando",
        "state": "FL",
        "contractor_size": "small_business",
        "specialties": ["kitchen design", "kitchen remodeling"],
        "lead_status": "new",
        "lead_score": 0
    }
]

def seed_contractor_leads():
    """Insert test contractor leads into database"""
    print("Seeding contractor_leads table...")

    successful = 0
    failed = 0

    for contractor in test_contractors:
        try:
            # Add timestamps
            contractor["discovered_at"] = datetime.now().isoformat()
            contractor["created_at"] = datetime.now().isoformat()
            contractor["updated_at"] = datetime.now().isoformat()

            # Insert into database
            result = supabase.table("contractor_leads").insert(contractor).execute()

            if result.data:
                successful += 1
                print(f"[OK] Added: {contractor['company_name']}")
            else:
                failed += 1
                print(f"[FAIL] Could not add: {contractor['company_name']}")

        except Exception as e:
            failed += 1
            print(f"[ERROR] Failed to add {contractor['company_name']}: {e}")

    print(f"\nSeeding complete: {successful} successful, {failed} failed")

    # Verify data
    print("\nVerifying data in database...")
    result = supabase.table("contractor_leads").select("company_name, contractor_size, lead_status").execute()

    if result.data:
        print(f"Found {len(result.data)} contractors in database:")
        for contractor in result.data:
            print(f"  - {contractor['company_name']} ({contractor['contractor_size']}) - Status: {contractor['lead_status']}")
    else:
        print("No contractors found in database")

if __name__ == "__main__":
    seed_contractor_leads()
