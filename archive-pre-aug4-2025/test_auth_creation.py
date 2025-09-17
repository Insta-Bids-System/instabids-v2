#!/usr/bin/env python3
"""
Test the auth account creation directly
"""

import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(override=True)

async def test_auth_creation():
    """Test creating a Supabase auth account"""
    
    # Initialize Supabase with service role key for admin operations
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("[ERROR] Missing Supabase credentials")
        return
        
    supabase = create_client(supabase_url, supabase_key)
    print(f"[OK] Supabase connected: {supabase_url[:30]}...")
    
    # Test data
    test_email = "test.contractor@example.com"
    test_password = "TempPass123"
    test_company = "Test Contracting LLC"
    
    try:
        # Check if we have admin access
        print(f"\n[AUTH] Testing auth account creation...")
        
        # Try to create auth user
        auth_result = supabase.auth.admin.create_user({
            'email': test_email,
            'password': test_password,
            'email_confirm': True
        })
        
        if auth_result.user:
            user_id = auth_result.user.id
            print(f"[OK] Created auth user: {user_id}")
            print(f"   Email: {auth_result.user.email}")
            
            # Create profile
            profile_data = {
                'id': user_id,
                'email': test_email,
                'full_name': test_company,
                'role': 'contractor'
            }
            
            profile_result = supabase.table('profiles').insert(profile_data).execute()
            if profile_result.data:
                print(f"[OK] Created profile record")
            else:
                print(f"[ERROR] Failed to create profile: {profile_result}")
            
            # Create contractor record
            contractor_record = {
                'id': user_id,
                'business_name': test_company,
                'email': test_email
            }
            
            contractor_result = supabase.table('contractors').insert(contractor_record).execute()
            if contractor_result.data:
                print(f"[OK] Created contractor record")
            else:
                print(f"[ERROR] Failed to create contractor: {contractor_result}")
            
            print(f"\n[SUCCESS] Test contractor account created:")
            print(f"   Login Email: {test_email}")
            print(f"   Password: {test_password}")
            print(f"   User ID: {user_id}")
            
            # Clean up - delete the test user
            try:
                supabase.auth.admin.delete_user(user_id)
                print(f"[CLEANUP] Cleaned up test user")
            except:
                print(f"[WARNING] Could not clean up test user - manual deletion may be needed")
            
        else:
            print(f"[ERROR] Failed to create auth user: {auth_result}")
            
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        
        # Check if it's a permissions issue
        if "Admin API" in str(e) or "service_role" in str(e):
            print(f"")
            print(f"[ISSUE] Need service_role key for auth.admin methods")
            print(f"   Current key appears to be anon key")
            print(f"   Need SUPABASE_SERVICE_ROLE_KEY in .env")
        
if __name__ == "__main__":
    asyncio.run(test_auth_creation())