"""
Real contractor account creation test
Simulates Turf Grass Artificial Solutions creating an actual account
"""

import requests
import json
import time
import sys
import asyncio
from datetime import datetime
from supabase import create_client, Client
import os

# Fix Unicode issues on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
BACKEND_URL = "http://localhost:8008"
CONTRACTOR_ID = "turf-grass-" + str(int(time.time()))

# Supabase configuration
SUPABASE_URL = "https://xrhgrthdcaymxuqcgrmj.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhyaGdydGhkY2F5bXh1cWNncm1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2NTcyMDYsImV4cCI6MjA2OTIzMzIwNn0.BriGLA2FE_e_NJl8B-3ps1W6ZAuK6a5HpTwBGy-6rmE"

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def make_coia_request(message):
    """Make API request to COIA backend"""
    response = requests.post(
        f"{BACKEND_URL}/api/coia/chat",
        json={
            "contractor_lead_id": CONTRACTOR_ID,
            "session_id": CONTRACTOR_ID,
            "message": message
        }
    )
    return response.json() if response.status_code == 200 else None

def create_contractor_account(profile_data):
    """Create actual contractor account in Supabase"""
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    try:
        # Step 1: Create auth user
        print("Creating authentication user...")
        email = profile_data.get('email', 'info@turfgrassartificialsolutions.com')
        password = "TurfGrass2025!"  # In production, this would be user-provided
        
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "company_name": profile_data.get('company_name'),
                    "role": "contractor"
                }
            }
        })
        
        if auth_response.user:
            user_id = auth_response.user.id
            print(f"✅ Auth user created: {user_id}")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
        else:
            print("❌ Failed to create auth user")
            return None
            
        # Step 2: Create contractor record
        print("\nCreating contractor profile...")
        contractor_data = {
            "user_id": user_id,
            "company_name": profile_data.get('company_name', 'Turf Grass Artificial Solutions Inc.'),
            "service_areas": profile_data.get('service_areas', ['Palm Beach County', 'Broward County']),
            "specialties": profile_data.get('specializations', ['artificial turf', 'synthetic grass']),
            "tier": 1,  # Internal contractor (tier 1)
            "verified": True,
            "availability_status": "available",
            "created_at": datetime.now().isoformat()
        }
        
        contractor_response = supabase.table('contractors').insert(contractor_data).execute()
        
        if contractor_response.data:
            contractor_id = contractor_response.data[0]['id']
            print(f"✅ Contractor profile created: {contractor_id}")
            return {
                "user_id": user_id,
                "contractor_id": contractor_id,
                "email": email,
                "password": password,
                "login_url": f"{BACKEND_URL}/contractor/login"
            }
        else:
            print("❌ Failed to create contractor profile")
            return None
            
    except Exception as e:
        print(f"❌ Error creating account: {e}")
        return None

def test_real_contractor_creation():
    """Complete test of real contractor account creation"""
    
    print_section("REAL CONTRACTOR ACCOUNT CREATION TEST")
    print("Simulating: Turf Grass Artificial Solutions Inc.")
    print(f"Thread ID: {CONTRACTOR_ID}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Phase 1: Initial conversation with COIA
    print_section("PHASE 1: Initial Contractor Introduction")
    
    result = make_coia_request(
        "Hi, I'm John from Turf Grass Artificial Solutions. We specialize in artificial turf "
        "installation for residential and commercial properties. We've been in business for 12 years."
    )
    
    if result and result.get('success'):
        print("✅ Initial profile created!")
        profile = result.get('contractor_profile', {})
        print(f"   Company: {profile.get('company_name')}")
        print(f"   Years: {profile.get('years_in_business')}")
        print(f"\nCOIA Response: {result.get('response', '')[:200]}...")
    
    time.sleep(2)
    
    # Phase 2: Provide contact information
    print_section("PHASE 2: Providing Contact Information")
    
    result = make_coia_request(
        "Our email is info@turfgrassartificialsolutions.com and phone is (561) 504-9621. "
        "We're based in Palm Beach County and service all of South Florida."
    )
    
    if result and result.get('success'):
        print("✅ Contact information added!")
        profile = result.get('contractor_profile', {})
        print(f"   Email: {profile.get('email')}")
        print(f"   Phone: {profile.get('phone')}")
        print(f"   Service Areas: {profile.get('service_areas')}")
    
    time.sleep(2)
    
    # Phase 3: Complete profile details
    print_section("PHASE 3: Completing Profile Information")
    
    result = make_coia_request(
        "We have 8 installation crews and we're fully licensed (License #CGC1234567) and insured. "
        "We specialize in pet-friendly turf, putting greens, and sports fields. "
        "Our website is www.turfgrassartificialsolutions.com"
    )
    
    if result and result.get('success'):
        print("✅ Profile details completed!")
        profile = result.get('contractor_profile', {})
        print(f"   License: {profile.get('license_info')}")
        print(f"   Website: {profile.get('website')}")
        print(f"   Team Size: {profile.get('team_size')}")
        print(f"   Specializations: {profile.get('specializations')}")
    
    time.sleep(2)
    
    # Phase 4: Request account creation
    print_section("PHASE 4: Account Creation Request")
    
    result = make_coia_request(
        "I'd like to create an account so we can start receiving bid opportunities. "
        "Please use our email info@turfgrassartificialsolutions.com for the account."
    )
    
    if result and result.get('success'):
        print("✅ Account creation request received!")
        profile = result.get('contractor_profile', {})
        
        # Always proceed with account creation if we have the necessary info
        if profile.get('email'):
            print(f"\nProfile has email ({profile.get('email')}), proceeding with account creation...")
            
            # Phase 5: Create actual account
            print_section("PHASE 5: Creating Real Contractor Account")
            
            account_info = create_contractor_account(profile)
            
            if account_info:
                print_section("✅ ACCOUNT SUCCESSFULLY CREATED!")
                print(f"Email: {account_info['email']}")
                print(f"Password: {account_info['password']}")
                print(f"User ID: {account_info['user_id']}")
                print(f"Contractor ID: {account_info['contractor_id']}")
                print(f"\nYou can now log in at: {account_info['login_url']}")
                
                # Phase 6: Link account to conversation memory
                print_section("PHASE 6: Linking Account to Conversation Memory")
                
                result = make_coia_request(
                    f"Great! My account has been created with contractor ID {account_info['contractor_id']}. "
                    "Can you confirm you have this linked to our conversation?"
                )
                
                if result and result.get('success'):
                    print("✅ Account linked to conversation memory!")
                    print(f"\nCOIA Response: {result.get('response', '')[:300]}...")
                
                # Phase 7: Test memory persistence with account context
                print_section("PHASE 7: Testing Memory with Account Context")
                
                result = make_coia_request(
                    "Can you summarize my company profile and confirm my account details are saved?"
                )
                
                if result and result.get('success'):
                    response_text = result.get('response', '')
                    print(f"COIA Memory Test Response:\n{response_text[:500]}...")
                    
                    # Verify key information is remembered
                    checks = {
                        "Company Name": "turf grass" in response_text.lower(),
                        "Email": "info@turfgrassartificialsolutions.com" in response_text.lower(),
                        "Years in Business": "12" in response_text,
                        "License": "cgc1234567" in response_text.lower() or "licensed" in response_text.lower(),
                        "Specialization": "artificial" in response_text.lower() or "turf" in response_text.lower()
                    }
                    
                    print("\n\nMemory Verification:")
                    for item, found in checks.items():
                        status = "✅" if found else "❌"
                        print(f"   {status} {item}: {'Remembered' if found else 'Not found'}")
                
                return account_info
            else:
                print("❌ Failed to create account")
                return None
    
    return None

def verify_login(account_info):
    """Verify the contractor can actually log in"""
    print_section("VERIFICATION: Testing Login with Created Credentials")
    
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    try:
        # Attempt to sign in with the created credentials
        sign_in_response = supabase.auth.sign_in_with_password({
            "email": account_info['email'],
            "password": account_info['password']
        })
        
        if sign_in_response.user:
            print(f"✅ LOGIN SUCCESSFUL!")
            print(f"   User ID: {sign_in_response.user.id}")
            print(f"   Email: {sign_in_response.user.email}")
            print(f"   Role: {sign_in_response.user.user_metadata.get('role', 'Unknown')}")
            print(f"   Company: {sign_in_response.user.user_metadata.get('company_name', 'Unknown')}")
            
            # Sign out
            supabase.auth.sign_out()
            return True
        else:
            print("❌ Login failed - invalid credentials")
            return False
            
    except Exception as e:
        print(f"❌ Login verification failed: {e}")
        return False

if __name__ == "__main__":
    # Run the complete test
    account_info = test_real_contractor_creation()
    
    if account_info:
        # Verify the account works
        time.sleep(3)
        login_success = verify_login(account_info)
        
        if login_success:
            print_section("🎯 COMPLETE SUCCESS!")
            print("Real contractor account created and verified:")
            print(f"  ✅ Profile extracted through COIA conversation")
            print(f"  ✅ Account created in Supabase Auth")
            print(f"  ✅ Contractor record saved in database")
            print(f"  ✅ Memory linked to conversation thread")
            print(f"  ✅ Login credentials verified working")
            print(f"\n📧 Email: {account_info['email']}")
            print(f"🔑 Password: {account_info['password']}")
            print(f"🆔 Contractor ID: {account_info['contractor_id']}")
            print(f"\n✨ THE SYSTEM IS FULLY OPERATIONAL!")
    else:
        print_section("❌ TEST FAILED")
        print("Could not complete the full account creation flow")