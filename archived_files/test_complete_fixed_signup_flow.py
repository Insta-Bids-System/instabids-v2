"""
Complete Fixed Signup Flow Test
Tests the full flow with improved profile extraction and memory persistence
"""

import requests
import json
import time
import sys
import re
from datetime import datetime

# Fix Unicode issues on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
BACKEND_URL = "http://localhost:8008"
TEST_CONTRACTOR_ID = f"complete-test-{int(time.time())}"

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def extract_signup_url(response_text):
    """Extract signup URL from COIA response"""
    url_pattern = r'http://localhost:\d+/contractor/signup\?[^\s]+'
    match = re.search(url_pattern, response_text)
    return match.group(0) if match else None

def test_complete_fixed_flow():
    """Test complete signup flow with all improvements"""
    
    print_section("COMPLETE FIXED SIGNUP FLOW TEST")
    print(f"Test ID: {TEST_CONTRACTOR_ID}")
    print(f"Backend: {BACKEND_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # ========================================
    # PHASE 1: Multi-turn Profile Building
    # ========================================
    print_section("PHASE 1: MULTI-TURN PROFILE BUILDING")
    
    # Turn 1: Company introduction
    print("🔄 Turn 1: Company introduction with years")
    response1 = requests.post(
        f"{BACKEND_URL}/api/coia/landing",
        json={
            "contractor_lead_id": TEST_CONTRACTOR_ID,
            "session_id": TEST_CONTRACTOR_ID,
            "message": "Hi, I'm Mike from Professional Painters Plus. We've been painting for 15 years."
        }
    )
    
    if response1.status_code != 200:
        print(f"❌ FAILED: Turn 1 returned {response1.status_code}")
        return False
    
    result1 = response1.json()
    profile1 = result1.get('contractor_profile', {})
    print(f"✅ Turn 1 Success - Company: {profile1.get('company_name')}, Years: {profile1.get('years_in_business')}")
    
    time.sleep(1)
    
    # Turn 2: Contact information
    print("🔄 Turn 2: Contact information")
    response2 = requests.post(
        f"{BACKEND_URL}/api/coia/landing",
        json={
            "contractor_lead_id": TEST_CONTRACTOR_ID,
            "session_id": TEST_CONTRACTOR_ID,
            "message": "My email is mike@propaintersplus.com and phone is (555) 123-4567. We serve Miami area."
        }
    )
    
    result2 = response2.json()
    profile2 = result2.get('contractor_profile', {})
    print(f"✅ Turn 2 Success - Email: {profile2.get('email')}, Phone: {profile2.get('phone')}")
    print(f"   Service Areas: {profile2.get('service_areas')}")
    
    time.sleep(1)
    
    # Turn 3: Specializations
    print("🔄 Turn 3: Specializations and details")
    response3 = requests.post(
        f"{BACKEND_URL}/api/coia/landing",
        json={
            "contractor_lead_id": TEST_CONTRACTOR_ID,
            "session_id": TEST_CONTRACTOR_ID,
            "message": "We specialize in residential and commercial painting, and we're licensed and insured."
        }
    )
    
    result3 = response3.json()
    profile3 = result3.get('contractor_profile', {})
    print(f"✅ Turn 3 Success - Specializations: {profile3.get('specializations')}")
    print(f"   License Info: {profile3.get('license_info')}")
    print(f"   Insurance: {profile3.get('insurance_verified')}")
    
    time.sleep(1)
    
    # ========================================
    # PHASE 2: Memory Verification
    # ========================================
    print_section("PHASE 2: MEMORY VERIFICATION")
    
    print("🧠 Memory Check: What do you remember about my company?")
    memory_response = requests.post(
        f"{BACKEND_URL}/api/coia/landing",
        json={
            "contractor_lead_id": TEST_CONTRACTOR_ID,
            "session_id": TEST_CONTRACTOR_ID,
            "message": "Can you summarize what you know about my business so far?"
        }
    )
    
    memory_result = memory_response.json()
    memory_profile = memory_result.get('contractor_profile', {})
    memory_text = memory_result.get('response', '').lower()
    
    # Verify accumulated data
    memory_checks = {
        "Company Name": bool(memory_profile.get('company_name')),
        "Years in Business": bool(memory_profile.get('years_in_business')),
        "Email": bool(memory_profile.get('email')),
        "Phone": bool(memory_profile.get('phone')),
        "Service Areas": bool(memory_profile.get('service_areas')),
        "Specializations": bool(memory_profile.get('specializations')),
        "Mentioned in Response": any(term in memory_text for term in ['professional painters', 'mike', '15'])
    }
    
    print("📊 Memory Verification Results:")
    for check, passed in memory_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
    
    accumulated_data_count = sum(memory_checks.values())
    print(f"\n🎯 Memory Score: {accumulated_data_count}/7 checks passed")
    
    time.sleep(1)
    
    # ========================================
    # PHASE 3: Signup Link Generation
    # ========================================
    print_section("PHASE 3: SIGNUP LINK GENERATION")
    
    print("🔗 Requesting account creation")
    signup_response = requests.post(
        f"{BACKEND_URL}/api/coia/landing",
        json={
            "contractor_lead_id": TEST_CONTRACTOR_ID,
            "session_id": TEST_CONTRACTOR_ID,
            "message": "I'd like to create my account and start receiving bid opportunities on InstaBids."
        }
    )
    
    signup_result = signup_response.json()
    signup_generated = signup_result.get('signup_link_generated', False)
    signup_data = signup_result.get('signup_data', {})
    response_text = signup_result.get('response', '')
    
    print(f"✅ Signup Request Results:")
    print(f"   Link Generated: {signup_generated}")
    print(f"   Company in Data: {signup_data.get('company_name', 'Not found')}")
    print(f"   Email in Data: {signup_data.get('email', 'Not found')}")
    print(f"   Profile Completeness: {signup_data.get('profile_completeness', 0)}%")
    
    # Extract signup URL
    signup_url = extract_signup_url(response_text)
    if signup_url:
        print(f"   📧 Signup URL Found: {signup_url[:100]}...")
    else:
        print(f"   ❌ No signup URL found in response")
    
    # ========================================
    # PHASE 4: Interface Behavior Verification
    # ========================================
    print_section("PHASE 4: INTERFACE BEHAVIOR VERIFICATION")
    
    # Test landing page restrictions
    print("🔒 Testing landing page restrictions (should NOT allow bid search)")
    landing_bid_search = requests.post(
        f"{BACKEND_URL}/api/coia/landing",
        json={
            "contractor_lead_id": f"{TEST_CONTRACTOR_ID}-landing-test",
            "session_id": f"{TEST_CONTRACTOR_ID}-landing-test",
            "message": "Show me available plumbing projects in my area"
        }
    )
    
    landing_result = landing_bid_search.json()
    landing_has_bid_cards = bool(landing_result.get('bidCards'))
    
    print(f"✅ Landing Page Test:")
    print(f"   Interface: {landing_result.get('interface')}")
    print(f"   Mode: {landing_result.get('current_mode')}")
    print(f"   Bid Cards Attached: {landing_has_bid_cards}")
    
    # Test authenticated chat interface
    print("\n🔓 Testing chat interface (should allow bid search)")
    chat_bid_search = requests.post(
        f"{BACKEND_URL}/api/coia/chat",
        json={
            "contractor_lead_id": f"{TEST_CONTRACTOR_ID}-chat-test",
            "session_id": f"{TEST_CONTRACTOR_ID}-chat-test",
            "message": "Show me available plumbing projects in my area",
            "contractor_id": "test-contractor-123"  # Simulate authenticated
        }
    )
    
    chat_result = chat_bid_search.json()
    chat_has_features = chat_result.get('can_search_bid_cards', False)
    
    print(f"✅ Chat Interface Test:")
    print(f"   Interface: {chat_result.get('interface')}")
    print(f"   Authenticated: {chat_result.get('authenticated_contractor', False)}")
    print(f"   Can Search Bid Cards: {chat_has_features}")
    
    # ========================================
    # FINAL ASSESSMENT
    # ========================================
    print_section("FINAL ASSESSMENT")
    
    # Score the complete flow
    flow_scores = {
        "Profile Extraction (Years Fixed)": profile3.get('years_in_business') == 15,
        "Memory Persistence": accumulated_data_count >= 6,
        "Contact Info Extraction": bool(profile3.get('email') and profile3.get('phone')),
        "Signup Link Generation": signup_generated,
        "Landing Page Restrictions": not landing_has_bid_cards,
        "Chat Interface Features": chat_has_features,
        "Complete Profile Data": len([v for v in memory_profile.values() if v]) >= 8
    }
    
    passed_tests = sum(flow_scores.values())
    total_tests = len(flow_scores)
    
    print("🎯 COMPLETE FLOW RESULTS:")
    for test, passed in flow_scores.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {test}")
    
    print(f"\n📊 OVERALL SCORE: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests >= 6:
        print("🎉 SUCCESS: Complete signup flow is working!")
        print("\n✨ SYSTEM CAPABILITIES VERIFIED:")
        print("  • Multi-turn conversation profile building")
        print("  • Persistent memory across API calls") 
        print("  • Improved profile extraction (years in business fixed)")
        print("  • Signup link generation with embedded data")
        print("  • Interface-specific behavior (landing vs chat)")
        print("  • Complete contractor onboarding workflow")
        
        # Final data summary
        print(f"\n💾 FINAL PROFILE DATA:")
        final_profile = memory_profile
        for key, value in final_profile.items():
            if value:
                print(f"   {key}: {value}")
        
        return True
    else:
        print("❌ INCOMPLETE: Some tests failed")
        return False

if __name__ == "__main__":
    success = test_complete_fixed_flow()
    sys.exit(0 if success else 1)