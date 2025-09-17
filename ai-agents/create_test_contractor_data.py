"""
Create test contractor data for COIA bid card flow testing
"""

import requests
import json
from datetime import datetime

def create_test_contractor_data():
    """Create test contractor data via API"""
    
    # Test contractor data based on the bid card emails
    test_contractors = [
        {
            "company_name": "Coral Gables Renovations",
            "email": "maria@cgrenov.com",
            "phone": "(305) 555-0123",
            "website": "https://coralgablesreno.com",
            "specialties": ["home improvement", "renovation", "general contractor"],
            "service_zip_codes": ["33134", "33146", "33156"],
            "years_in_business": 8,
            "google_rating": 4.7,
            "google_review_count": 127,
            "contractor_size": "LOCAL_BUSINESS_TEAMS",
            "lead_score": 85,
            "data_completeness": 0.9,
            "tier": 2,
            "certifications": ["Florida General Contractor License", "EPA RRP Certification"],
            "license_info": "CGC1234567",
            "source": "manual",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "company_name": "Premium Home Solutions",
            "email": "info@premiumhomesolutions.com", 
            "phone": "(954) 555-0198",
            "website": "https://premiumhomesolutions.com",
            "specialties": ["kitchen remodeling", "bathroom renovation", "flooring"],
            "service_zip_codes": ["33301", "33304", "33308"],
            "years_in_business": 12,
            "google_rating": 4.9,
            "google_review_count": 203,
            "contractor_size": "LOCAL_BUSINESS_TEAMS", 
            "lead_score": 92,
            "data_completeness": 0.95,
            "tier": 1,
            "certifications": ["Florida Building Contractor License", "NKBA Certified"],
            "license_info": "CBC7891011",
            "source": "manual",
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Use the database client to insert data
    try:
        from database_simple import get_client
        
        db = get_client()
        
        for contractor in test_contractors:
            # Insert into contractor_leads table
            result = db.table("contractor_leads").insert(contractor).execute()
            
            if result.data:
                print(f"✓ Created contractor: {contractor['company_name']}")
            else:
                print(f"✗ Failed to create contractor: {contractor['company_name']}")
                
        print(f"\n✓ Successfully created {len(test_contractors)} test contractors")
        return True
        
    except Exception as e:
        print(f"✗ Error creating test data: {e}")
        return False

if __name__ == "__main__":
    print("Creating test contractor data for COIA bid card flow...")
    success = create_test_contractor_data()
    
    if success:
        print("\n✅ Test data creation complete!")
        print("Now you can run: python test_coia_bid_card_flow.py")
    else:
        print("\n❌ Test data creation failed")