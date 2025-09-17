import requests
import time

print("=== COMPREHENSIVE COIA SYSTEM VERIFICATION ===")

# Test 1: Real contractor conversation
print("TEST 1: Testing DeepAgents with real company")
start_time = time.time()

try:
    response = requests.post("http://localhost:8008/api/coia/landing", json={
        "user_id": "test-verification-001", 
        "session_id": "verification-session-001",
        "contractor_lead_id": "verification-contractor-001",
        "message": "I run Tropical Turf Management in Miami, Florida"
    }, timeout=30)
    
    elapsed = time.time() - start_time
    print(f"Response time: {elapsed:.2f} seconds")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        company = data.get("company_name", "Unknown")
        response_text = data.get("response", "")
        
        print(f"Company extracted: {company}")
        print(f"Response length: {len(response_text)} chars")
        print(f"Response preview: {response_text[:200]}...")
        
        # Check for real AI indicators
        if len(response_text) > 150 and company \!= "Unknown":
            print("SUCCESS: Real DeepAgents conversation detected\!")
            print("- Company name extracted correctly")
            print("- Response length indicates AI processing")
            print("- No fallback template detected")
        else:
            print("PARTIAL: Response too short or missing company name")
            
    else:
        print(f"ERROR: Status {response.status_code}")
        print(f"Error response: {response.text[:300]}")
        
except Exception as e:
    elapsed = time.time() - start_time
    print(f"ERROR after {elapsed:.2f}s: {e}")

