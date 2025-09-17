#!/usr/bin/env python3
"""
Create Test Contractor Account with Login Credentials
Creates a real contractor in the database that can be used for testing
"""

import asyncio
import json
import os
import sys
from datetime import datetime
import uuid

# Add the ai-agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from database_simple import db
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ContractorAccountCreator:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        
        self.client = create_client(self.supabase_url, self.supabase_key)
        
    async def create_test_contractor_profile(self):
        """Create a complete contractor profile in the database"""
        print("Creating test contractor profile...")
        
        # Generate test contractor data
        contractor_data = {
            'id': str(uuid.uuid4()),
            'company_name': 'Elite Home Construction LLC',
            'primary_trade': 'General Contractor',
            'years_in_business': 15,
            'business_license': 'WA-GC-2024-001234',
            'insurance_liability': 2000000,
            'insurance_workers_comp': True,
            'bonded': True,
            'service_areas': ['Seattle, WA', 'Bellevue, WA', 'Redmond, WA'],
            'specializations': ['Kitchen Remodels', 'Bathroom Renovations', 'Home Additions', 'Custom Tile Work'],
            'phone': '206-555-0199',
            'email': 'testcontractor@elitehomeconstruction.com',
            'website': 'https://www.elitehomeconstruction.com',
            'business_address': '123 Construction Way, Seattle, WA 98101',
            'description': 'Premier general contractor specializing in high-end residential remodels. Licensed, bonded, and insured with 15 years of experience in the Seattle area.',
            'hourly_rate_min': 85,
            'hourly_rate_max': 125,
            'project_min_budget': 5000,
            'project_max_budget': 500000,
            'availability_status': 'available',
            'response_time_hours': 2,
            'preferred_contact_method': 'email',
            'portfolio_images': [
                'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800',
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800',
                'https://images.unsplash.com/photo-1560185007-cde436f6a4d0?w=800'
            ],
            'certifications': ['EPA Lead-Safe Certified', 'OSHA 30-Hour Construction', 'BBB A+ Rating'],
            'payment_terms': 'Net 30',
            'warranty_years': 5,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        try:
            # Insert contractor into database
            result = self.client.table('contractors').insert(contractor_data).execute()
            
            if result.data:
                contractor_id = result.data[0]['id']
                print(f"SUCCESS: Contractor profile created: {contractor_id}")
                print(f"   Company: {contractor_data['company_name']}")
                print(f"   Email: {contractor_data['email']}")
                return contractor_id, contractor_data
            else:
                print("ERROR: Failed to create contractor profile")
                return None, None
                
        except Exception as e:
            print(f"ERROR: Creating contractor: {str(e)}")
            return None, None
    
    async def create_auth_user(self, contractor_data):
        """Create authentication user for the contractor"""
        print("Creating authentication user...")
        
        try:
            # Create auth user
            email = contractor_data['email']
            password = 'TestContractor123!'  # Test password
            
            # Create user in profiles table
            profile_data = {
                'id': str(uuid.uuid4()),
                'email': email,
                'full_name': contractor_data['company_name'],
                'role': 'contractor',
                'contractor_id': contractor_data['id'],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            result = self.client.table('profiles').insert(profile_data).execute()
            
            if result.data:
                user_id = result.data[0]['id']
                print(f"SUCCESS: Auth profile created: {user_id}")
                print(f"   Login Email: {email}")
                print(f"   Password: {password}")
                return user_id, email, password
            else:
                print("ERROR: Failed to create auth profile")
                return None, None, None
                
        except Exception as e:
            print(f"ERROR: Creating auth user: {str(e)}")
            return None, None, None
    
    async def verify_contractor_login(self, email, contractor_id):
        """Verify the contractor can 'log in' by checking database"""
        print("Verifying contractor login...")
        
        try:
            # Check if we can find the contractor by email
            profile_result = self.client.table('profiles').select('*').eq('email', email).execute()
            
            if profile_result.data:
                profile = profile_result.data[0]
                print(f"SUCCESS: Profile found: {profile['full_name']}")
                
                # Get contractor details
                contractor_result = self.client.table('contractors').select('*').eq('id', contractor_id).execute()
                
                if contractor_result.data:
                    contractor = contractor_result.data[0]
                    print(f"SUCCESS: Contractor details found: {contractor['company_name']}")
                    return True, contractor
                else:
                    print("ERROR: Contractor details not found")
                    return False, None
            else:
                print("ERROR: Profile not found")
                return False, None
                
        except Exception as e:
            print(f"ERROR: Verifying login: {str(e)}")
            return False, None

async def main():
    """Create a complete test contractor account"""
    print("Creating Test Contractor Account")
    print("=" * 50)
    
    creator = ContractorAccountCreator()
    
    # Step 1: Create contractor profile
    contractor_id, contractor_data = await creator.create_test_contractor_profile()
    
    if not contractor_id:
        print("FAILED: Could not create contractor profile")
        return
    
    # Step 2: Create auth user
    user_id, email, password = await creator.create_auth_user(contractor_data)
    
    if not user_id:
        print("FAILED: Could not create auth user")
        return
    
    # Step 3: Verify login works
    login_success, contractor_details = await creator.verify_contractor_login(email, contractor_id)
    
    if not login_success:
        print("FAILED: Login verification failed")
        return
    
    # Output login credentials
    print("\n" + "=" * 50)
    print("SUCCESS: TEST CONTRACTOR ACCOUNT CREATED!")
    print("=" * 50)
    print(f"Login Email: {email}")
    print(f"Password: {password}")
    print(f"Company: {contractor_data['company_name']}")
    print(f"Contractor ID: {contractor_id}")
    print(f"User ID: {user_id}")
    print("\nYou can now test the contractor experience:")
    print(f"   1. Visit: http://localhost:5187/contractor")
    print(f"   2. Login with: {email}")
    print(f"   3. Password: {password}")
    print(f"   4. Access dashboard: http://localhost:5187/contractor/dashboard")
    
    print(f"\nContractor Profile Details:")
    print(f"   Primary Trade: {contractor_data['primary_trade']}")
    print(f"   Years in Business: {contractor_data['years_in_business']}")
    print(f"   Service Areas: {', '.join(contractor_data['service_areas'])}")
    print(f"   Specializations: {', '.join(contractor_data['specializations'])}")
    print(f"   Phone: {contractor_data['phone']}")
    print(f"   License: {contractor_data['business_license']}")
    print(f"   Insurance: ${contractor_data['insurance_liability']:,}")

if __name__ == "__main__":
    asyncio.run(main())