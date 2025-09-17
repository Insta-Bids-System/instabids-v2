#!/usr/bin/env python3
"""
Create the missing auth account for the contractor profile
"""

import os
import sys
sys.path.append('ai-agents')
from dotenv import load_dotenv
from supabase import create_client

# Load from ai-agents directory where service key works
load_dotenv('ai-agents/.env', override=True)

def create_auth_account():
    """Create the missing auth account"""
    
    # Get credentials from ai-agents .env (which has working service key)
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    print(f"URL: {supabase_url}")
    print(f"Service Key: {supabase_service_key[:20] if supabase_service_key else 'None'}...")
    
    if not supabase_url or not supabase_service_key:
        print("[ERROR] Missing service role key")
        return None
        
    # Use service role key for admin operations
    supabase = create_client(supabase_url, supabase_service_key)
    
    # Contractor info
    email = "info@jmholidaylighting.com"
    password = "TestPassword123!"  # Fixed password for testing
    company_name = "JM Holiday Lighting, Inc."
    
    try:
        print(f"[AUTH] Creating account for: {email}")
        
        # Create auth user
        auth_result = supabase.auth.admin.create_user({
            'email': email,
            'password': password,
            'email_confirm': True
        })
        
        if auth_result.user:
            user_id = auth_result.user.id
            print(f"[AUTH] ✓ Created auth user: {user_id}")
            
            # Create profile
            profile_data = {
                'id': user_id,
                'email': email,
                'full_name': company_name,
                'role': 'contractor'
            }
            
            supabase.table('profiles').insert(profile_data).execute()
            print(f"[AUTH] ✓ Created profile")
            
            # Create contractor record with AI data
            contractor_record = {
                'id': user_id,
                'business_name': company_name,
                'email': email,
                'phone': "(561) 573-7090",
                'website': "http://jmholidaylighting.com/"
            }
            
            supabase.table('contractors').insert(contractor_record).execute()
            print(f"[AUTH] ✓ Created contractor record")
            
            print(f"\\n" + "="*60)
            print("[SUCCESS] CONTRACTOR LOGIN READY!")
            print("="*60)
            print(f"LOGIN CREDENTIALS:")
            print(f"  URL: http://localhost:5173/login")
            print(f"  Email: {email}")  
            print(f"  Password: {password}")
            print(f"  Dashboard: http://localhost:5173/contractor-dashboard")
            print(f"")
            print(f"TEST THIS LOGIN NOW!")
            print("="*60)
            
            return {
                'email': email,
                'password': password,
                'user_id': user_id
            }
        else:
            print(f"[ERROR] Failed to create auth user")
            return None
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

if __name__ == "__main__":
    create_auth_account()