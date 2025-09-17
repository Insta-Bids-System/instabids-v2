"""
Debug Signup Link Generation
Test specifically why signup links aren't being generated
"""

import requests
import json
import time
import sys

# Fix Unicode issues on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
BACKEND_URL = "http://localhost:8008"
TEST_CONTRACTOR_ID = f"signup-debug-{int(time.time())}"

def test_signup_debug():
    """Debug signup link generation step by step"""
    print("🔍 DEBUG: SIGNUP LINK GENERATION")
    
    # Step 1: Build complete profile
    print("\n📋 Step 1: Building complete profile")
    profile_response = requests.post(
        f"{BACKEND_URL}/api/coia/landing",
        json={
            "contractor_lead_id": TEST_CONTRACTOR_ID,
            "session_id": TEST_CONTRACTOR_ID,
            "message": "Hi, I'm Professional Painters Plus. Email mike@test.com, phone 555-123-4567, we've been painting for 15 years."
        }
    )
    
    profile_result = profile_response.json()
    profile = profile_result.get('contractor_profile', {})
    
    print(f"✅ Profile built:")
    print(f"   Company: {profile.get('company_name')}")
    print(f"   Email: {profile.get('email')}")
    print(f"   Primary Trade: {profile.get('primary_trade')}")
    print(f"   Years: {profile.get('years_in_business')}")
    
    # Check minimum data requirements
    has_email = bool(profile.get("email"))
    has_company = bool(profile.get("company_name"))
    has_trade = bool(profile.get("primary_trade"))
    has_specializations = bool(profile.get("specializations"))
    
    has_minimum_data = (
        has_email and 
        (has_company or has_trade or has_specializations)
    )
    
    print(f"\n🔍 Minimum Data Check:")
    print(f"   Has Email: {has_email}")
    print(f"   Has Company: {has_company}")
    print(f"   Has Trade: {has_trade}")
    print(f"   Has Specializations: {has_specializations}")
    print(f"   Meets Requirements: {has_minimum_data}")
    
    time.sleep(1)
    
    # Step 2: Try different account creation keywords
    print(f"\n📝 Step 2: Testing account creation keywords")
    
    test_messages = [
        "I'd like to create my account",
        "create account",
        "sign up",
        "get started",
        "start receiving bid opportunities",
        "I want to join InstaBids"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n   Test {i}: '{message}'")
        
        response = requests.post(
            f"{BACKEND_URL}/api/coia/landing",
            json={
                "contractor_lead_id": TEST_CONTRACTOR_ID,
                "session_id": TEST_CONTRACTOR_ID,
                "message": message
            }
        )
        
        result = response.json()
        signup_generated = result.get('signup_link_generated', False)
        signup_data = result.get('signup_data')
        response_text = result.get('response', '')
        
        # Check for URL in response
        has_url = 'http://localhost:' in response_text and '/contractor/signup' in response_text
        
        print(f"      Signup Generated: {signup_generated}")
        print(f"      Has Signup Data: {bool(signup_data)}")
        print(f"      URL in Response: {has_url}")
        
        if signup_generated or has_url:
            print(f"      🎉 SUCCESS with message: '{message}'")
            if signup_data:
                print(f"      Company: {signup_data.get('company_name')}")
                print(f"      Email: {signup_data.get('email')}")
            return True
        
        time.sleep(0.5)
    
    print(f"\n❌ No signup link generated with any keyword")
    
    # Step 3: Check raw response for debugging
    print(f"\n🔧 Step 3: Raw response analysis")
    debug_response = requests.post(
        f"{BACKEND_URL}/api/coia/landing",
        json={
            "contractor_lead_id": TEST_CONTRACTOR_ID,
            "session_id": TEST_CONTRACTOR_ID,
            "message": "create account for my company"
        }
    )
    
    debug_result = debug_response.json()
    print(f"Full response keys: {list(debug_result.keys())}")
    print(f"Response text: {debug_result.get('response', '')[:200]}...")
    
    return False

if __name__ == "__main__":
    success = test_signup_debug()
    print(f"\n🎯 RESULT: {'SUCCESS' if success else 'FAILED'}")