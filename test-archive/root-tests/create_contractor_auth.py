#!/usr/bin/env python3
"""
Create real authentication account for the contractor created by AI
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import secrets
import string

load_dotenv(override=True)

def create_contractor_auth():
    """Create auth account for JM Holiday Lighting contractor"""
    
    # Initialize Supabase with service role key
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("[ERROR] Missing Supabase credentials")
        return None
        
    supabase = create_client(supabase_url, supabase_key)
    
    # Find the contractor record created by AI
    contractor_id = "f69a19e0-d6f2-4aa1-82ea-18517a9350f8"
    email = "info@jmholidaylighting.com"
    company_name = "JM Holiday Lighting, Inc."
    
    print(f"[AUTH] Creating account for contractor: {contractor_id}")
    print(f"[AUTH] Email: {email}")
    print(f"[AUTH] Company: {company_name}")
    
    # Generate a real password
    password = "HolidayLights2024!"  # Real password for testing
    
    try:
        # Create auth user
        auth_result = supabase.auth.admin.create_user({
            'email': email,
            'password': password,
            'email_confirm': True
        })
        
        if auth_result.user:
            user_id = auth_result.user.id
            print(f"[AUTH] Created auth user: {user_id}")
            
            # Create profile
            profile_data = {
                'id': user_id,
                'email': email,
                'full_name': company_name,
                'role': 'contractor'
            }
            
            profile_result = supabase.table('profiles').insert(profile_data).execute()
            print(f"[AUTH] Profile created")
            
            # Get contractor_leads data
            lead_result = supabase.table('contractor_leads').select('*').eq('id', contractor_id).execute()
            if lead_result.data:
                lead_data = lead_result.data[0]
                print(f"[AUTH] Found contractor lead data")
                
                # Create contractor record with AI data
                contractor_record = {
                    'id': user_id,
                    'business_name': lead_data.get('company_name', company_name),
                    'email': lead_data.get('email', email),
                    'phone': lead_data.get('phone'),
                    'website': lead_data.get('website')
                }
                
                contractor_result = supabase.table('contractors').insert(contractor_record).execute()
                print(f"[AUTH] Contractor record created with AI data")
                print(f"   Business: {contractor_record['business_name']}")
                print(f"   Phone: {contractor_record['phone']}")
                print(f"   Website: {contractor_record['website']}")
                
                # Update contractor_leads to show it's linked
                update_result = supabase.table('contractor_leads').update({
                    'raw_data': {
                        **lead_data.get('raw_data', {}),
                        'auth_user_id': user_id,
                        'account_linked': True,
                        'linked_at': '2025-01-30T12:00:00Z'
                    }
                }).eq('id', contractor_id).execute()
                
                print(f"[AUTH] Linked contractor_leads record: {contractor_id}")
                
                return {
                    'user_id': user_id,
                    'email': email,
                    'password': password,
                    'contractor_data': contractor_record
                }
            else:
                print(f"[AUTH ERROR] No contractor lead found with ID: {contractor_id}")
                return None
        else:
            print(f"[AUTH ERROR] Failed to create auth user")
            return None
            
    except Exception as e:
        print(f"[AUTH ERROR] {e}")
        return None

def main():
    print("="*80)
    print("CREATING REAL AUTHENTICATION FOR AI-CREATED CONTRACTOR")
    print("="*80)
    
    login_info = create_contractor_auth()
    
    if login_info:
        print(f"\n" + "="*80)
        print("[SUCCESS] CONTRACTOR AUTHENTICATION CREATED!")
        print("="*80)
        print(f"")
        print(f"CONTRACTOR LOGIN CREDENTIALS:")
        print(f"   Login URL: http://localhost:5173/login")
        print(f"   Email: {login_info['email']}")
        print(f"   Password: {login_info['password']}")
        print(f"   Dashboard: http://localhost:5173/contractor-dashboard")
        print(f"")
        print(f"CONTRACTOR PROFILE DATA (FROM AI RESEARCH):")
        data = login_info['contractor_data']
        print(f"   Business Name: {data['business_name']}")
        print(f"   Email: {data['email']}")
        print(f"   Phone: {data['phone']}")
        print(f"   Website: {data['website']}")
        print(f"")
        print(f"HOW TO TEST:")
        print(f"1. Start the frontend: cd web && npm run dev")
        print(f"2. Go to: http://localhost:5173/login")
        print(f"3. Login with credentials above")
        print(f"4. You'll see contractor dashboard with AI-researched data ONLY")
        print(f"5. No pre-filled mock data - everything from AI conversation")
        print(f"")
        print("="*80)
    else:
        print("[FAILED] Could not create authentication")

if __name__ == "__main__":
    main()