#!/usr/bin/env python3
"""
Add test contractors to the database for testing the complete flow
"""

import sys
import os
import uuid
from datetime import datetime

# Add the agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from database_simple import db

def add_test_contractors():
    """Add various test contractors to the database"""
    
    print("Adding test contractors to database...")
    
    test_contractors = [
        # Mold remediation specialists
        {
            'id': str(uuid.uuid4()),
            'company_name': 'ABC Mold Removal Experts',
            'contact_name': 'John Smith',
            'email': 'contact@abcmold.com',
            'phone': '(206) 555-0101',
            'website': 'https://abcmold.com',
            'source': 'manual',
            'specialties': ['mold remediation', 'water damage', 'air quality testing'],
            'city': 'Seattle',
            'state': 'WA',
            'years_in_business': 15,
            'license_verified': True,
            'lead_score': 92,
            'lead_status': 'qualified',  # Added this field
            'contractor_size': 'small_business',  # Added this field
            'rating': 4.8,  # Added this field
            'review_count': 127,  # Added this field
            'created_at': datetime.now().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'company_name': 'Seattle Clean Air Services',
            'contact_name': 'Mary Johnson',
            'email': 'info@seattlecleanair.com',
            'phone': '(206) 555-0102',
            'website': 'https://seattlecleanair.com',
            'source': 'google_maps',
            'specialties': ['mold remediation', 'hvac cleaning', 'EPA certified'],
            'city': 'Seattle',
            'state': 'WA',
            'years_in_business': 8,
            'license_verified': True,
            'lead_score': 88,
            'lead_status': 'qualified',
            'contractor_size': 'small_business',
            'rating': 4.7,
            'review_count': 89,
            'created_at': datetime.now().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'company_name': 'Emergency Mold Response Team',
            'contact_name': 'Bob Wilson',
            'email': 'emergency@moldresponse.com',
            'phone': '(425) 555-0103',
            'website': 'https://emergencymoldresponse.com',
            'source': 'yelp',
            'specialties': ['emergency mold removal', '24/7 service', 'child-safe protocols'],
            'city': 'Seattle',
            'state': 'WA',
            'years_in_business': 10,
            'license_verified': True,
            'lead_score': 95,
            'lead_status': 'qualified',
            'contractor_size': 'small_business',
            'rating': 4.9,
            'review_count': 215,
            'created_at': datetime.now().isoformat()
        },
        # HVAC contractors
        {
            'id': str(uuid.uuid4()),
            'company_name': 'Comfort Zone HVAC',
            'contact_name': 'Tom Davis',
            'email': 'service@comfortzonehvac.com',
            'phone': '(206) 555-0201',
            'website': 'https://comfortzonehvac.com',
            'source': 'angi',
            'specialties': ['hvac', 'heating', 'cooling', 'air quality'],
            'city': 'Seattle',
            'state': 'WA',
            'years_in_business': 20,
            'license_verified': True,
            'lead_score': 90,
            'lead_status': 'contacted',
            'contractor_size': 'regional_company',
            'rating': 4.6,
            'review_count': 342,
            'created_at': datetime.now().isoformat()
        },
        # General contractors
        {
            'id': str(uuid.uuid4()),
            'company_name': 'All-Pro Home Services',
            'contact_name': 'Mike Brown',
            'email': 'info@allprohome.com',
            'phone': '(425) 555-0301',
            'website': 'https://allprohome.com',
            'source': 'bbb',
            'specialties': ['general contracting', 'mold remediation', 'water damage', 'remodeling'],
            'city': 'Bellevue',
            'state': 'WA',
            'years_in_business': 12,
            'license_verified': True,
            'lead_score': 87,
            'lead_status': 'qualified',
            'contractor_size': 'small_business',
            'rating': 4.5,
            'review_count': 156,
            'created_at': datetime.now().isoformat()
        }
    ]
    
    # Insert contractors
    success_count = 0
    for contractor in test_contractors:
        try:
            result = db.client.table('contractor_leads').insert(contractor).execute()
            if result.data:
                success_count += 1
                print(f"  Added: {contractor['company_name']} ({contractor.get('source', 'manual')})")
        except Exception as e:
            print(f"  Error adding {contractor['company_name']}: {e}")
    
    print(f"\nSuccessfully added {success_count} contractors to database")
    
    # Verify by querying
    print("\nVerifying contractors in database:")
    result = db.client.table('contractor_leads').select('company_name, source, specialties').execute()
    if result.data:
        print(f"Total contractors: {len(result.data)}")
        for contractor in result.data[:5]:
            print(f"  - {contractor['company_name']} | {contractor.get('source', 'Unknown')}")

if __name__ == "__main__":
    add_test_contractors()