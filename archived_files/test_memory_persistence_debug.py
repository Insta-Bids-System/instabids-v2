"""
Debug Memory Persistence Issue
Test to identify where profile data is being lost between API calls
"""

import requests
import json
import time
import sys
from datetime import datetime

# Fix Unicode issues on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
BACKEND_URL = "http://localhost:8008"
TEST_CONTRACTOR_ID = f"memory-debug-{int(time.time())}"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def debug_memory_persistence():
    """Debug memory persistence step by step"""
    print_section("MEMORY PERSISTENCE DEBUG TEST")
    print(f"Test ID: {TEST_CONTRACTOR_ID}")
    print(f"Backend: {BACKEND_URL}")
    
    # Step 1: First API call with company info
    print("\n🔍 STEP 1: First API call with company info")
    response1 = requests.post(
        f"{BACKEND_URL}/api/coia/landing",
        json={
            "contractor_lead_id": TEST_CONTRACTOR_ID,
            "session_id": TEST_CONTRACTOR_ID,
            "message": "Hi, I'm Mike from Professional Painters Plus. We've been painting for 15 years."
        }
    )
    
    if response1.status_code != 200:
        print(f"❌ FAILED: API call 1 returned {response1.status_code}")
        return
    
    result1 = response1.json()
    profile1 = result1.get('contractor_profile', {})
    
    print(f"✅ API Call 1 Success")
    print(f"   Interface: {result1.get('interface')}")
    print(f"   Profile extracted: {json.dumps(profile1, indent=2)}")
    print(f"   Company name: {profile1.get('company_name')}")
    print(f"   Years in business: {profile1.get('years_in_business')}")
    
    time.sleep(2)  # Wait for persistence
    
    # Step 2: Second API call with contact info
    print("\n🔍 STEP 2: Second API call with contact info")
    response2 = requests.post(
        f"{BACKEND_URL}/api/coia/landing",
        json={
            "contractor_lead_id": TEST_CONTRACTOR_ID,  # Same ID for memory
            "session_id": TEST_CONTRACTOR_ID,
            "message": "My email is mike@propaintersplus.com and phone is (555) 123-4567."
        }
    )
    
    if response2.status_code != 200:
        print(f"❌ FAILED: API call 2 returned {response2.status_code}")
        return
        
    result2 = response2.json()
    profile2 = result2.get('contractor_profile', {})
    
    print(f"✅ API Call 2 Success")
    print(f"   Profile extracted: {json.dumps(profile2, indent=2)}")
    print(f"   Company name: {profile2.get('company_name')}")
    print(f"   Years in business: {profile2.get('years_in_business')}")
    print(f"   Email: {profile2.get('email')}")
    print(f"   Phone: {profile2.get('phone')}")
    
    time.sleep(2)  # Wait for persistence
    
    # Step 3: Third API call asking for information
    print("\n🔍 STEP 3: Third API call asking what we know")
    response3 = requests.post(
        f"{BACKEND_URL}/api/coia/landing",
        json={
            "contractor_lead_id": TEST_CONTRACTOR_ID,  # Same ID for memory
            "session_id": TEST_CONTRACTOR_ID,
            "message": "What information do you have about my company so far?"
        }
    )
    
    if response3.status_code != 200:
        print(f"❌ FAILED: API call 3 returned {response3.status_code}")
        return
    
    result3 = response3.json()
    profile3 = result3.get('contractor_profile', {})
    response_text = result3.get('response', '').lower()
    
    print(f"✅ API Call 3 Success")
    print(f"   Profile in state: {json.dumps(profile3, indent=2)}")
    print(f"   COIA Response: {result3.get('response', '')[:300]}")
    
    # Memory analysis
    print("\n📊 MEMORY PERSISTENCE ANALYSIS")
    
    memory_checks = {
        "Company Name in Profile": bool(profile3.get('company_name')),
        "Years in Business in Profile": bool(profile3.get('years_in_business')),
        "Email in Profile": bool(profile3.get('email')),
        "Phone in Profile": bool(profile3.get('phone')),
        "Company mentioned in response": any(term in response_text for term in ['professional painters', 'painters plus', 'mike']),
        "Years mentioned in response": any(term in response_text for term in ['15', 'fifteen', 'years']),
        "Email mentioned in response": 'propaintersplus.com' in response_text or 'mike@' in response_text,
        "Phone mentioned in response": any(term in response_text for term in ['555', '123-4567', 'phone']),
    }
    
    for check, passed in memory_checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {check}")
    
    # Overall assessment
    profile_data_count = sum([
        bool(profile3.get('company_name')),
        bool(profile3.get('years_in_business')),
        bool(profile3.get('email')),
        bool(profile3.get('phone'))
    ])
    
    response_memory_count = sum([
        any(term in response_text for term in ['professional painters', 'painters plus', 'mike']),
        any(term in response_text for term in ['15', 'fifteen', 'years']),
        'propaintersplus.com' in response_text or 'mike@' in response_text,
        any(term in response_text for term in ['555', '123-4567', 'phone'])
    ])
    
    print(f"\n🎯 MEMORY PERSISTENCE RESULTS:")
    print(f"   Profile Data Fields Retained: {profile_data_count}/4")
    print(f"   Information Mentioned in Response: {response_memory_count}/4")
    
    if profile_data_count >= 3 and response_memory_count >= 2:
        print(f"   ✅ MEMORY PERSISTENCE: WORKING")
    elif profile_data_count >= 2:
        print(f"   ⚠️ MEMORY PERSISTENCE: PARTIAL")
    else:
        print(f"   ❌ MEMORY PERSISTENCE: FAILING")
    
    # Debug checkpointer state
    print(f"\n🔧 DEBUGGING INFO:")
    print(f"   Thread ID pattern: landing_{TEST_CONTRACTOR_ID}")
    print(f"   Contractor Lead ID: {TEST_CONTRACTOR_ID}")
    print(f"   Same session ID used: {TEST_CONTRACTOR_ID}")
    
    return memory_checks, profile_data_count >= 3

def run_debug_test():
    """Run the complete debug test"""
    try:
        return debug_memory_persistence()
    except Exception as e:
        print(f"\n❌ DEBUG TEST FAILED: {e}")
        import traceback
        print(traceback.format_exc())
        return None, False

if __name__ == "__main__":
    run_debug_test()