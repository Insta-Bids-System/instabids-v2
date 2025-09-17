"""
Test Improved Profile Extraction
Test the updated regex patterns for years in business extraction
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
TEST_CONTRACTOR_ID = f"extraction-test-{int(time.time())}"

def test_improved_extraction():
    """Test improved profile extraction patterns"""
    print("🔍 TESTING IMPROVED PROFILE EXTRACTION")
    print(f"Test ID: {TEST_CONTRACTOR_ID}")
    
    # Test the exact message that was failing
    response = requests.post(
        f"{BACKEND_URL}/api/coia/landing",
        json={
            "contractor_lead_id": TEST_CONTRACTOR_ID,
            "session_id": TEST_CONTRACTOR_ID,
            "message": "Hi, I'm Mike from Professional Painters Plus. We've been painting for 15 years."
        }
    )
    
    if response.status_code != 200:
        print(f"❌ FAILED: API call returned {response.status_code}")
        return False
    
    result = response.json()
    profile = result.get('contractor_profile', {})
    
    print(f"✅ API Call Success")
    print(f"   Profile extracted:")
    print(f"   Company Name: {profile.get('company_name')}")
    print(f"   Years in Business: {profile.get('years_in_business')}")
    print(f"   Primary Trade: {profile.get('primary_trade')}")
    
    # Check if years were extracted
    years_extracted = profile.get('years_in_business') == 15
    company_extracted = 'Professional Painters Plus' in profile.get('company_name', '')
    
    print(f"\n📊 EXTRACTION RESULTS:")
    print(f"   ✅ Company Name: {'PASS' if company_extracted else 'FAIL'}")
    print(f"   ✅ Years in Business: {'PASS' if years_extracted else 'FAIL'}")
    
    if years_extracted and company_extracted:
        print(f"   ✅ OVERALL: EXTRACTION IMPROVED!")
        return True
    else:
        print(f"   ❌ OVERALL: Still needs improvement")
        return False

if __name__ == "__main__":
    test_improved_extraction()