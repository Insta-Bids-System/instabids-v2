import requests
import time

print("=== TESTING FAST COIA ENDPOINT ===")
start_time = time.time()

try:
    response = requests.post('http://localhost:8008/api/coia/fast-landing', json={
        'user_id': 'test-fast-001', 
        'session_id': 'session-fast-001',
        'contractor_lead_id': 'fast-contractor-001',
        'message': 'I run Elite Roofing Solutions in Miami, Florida'
    }, timeout=5)
    
    elapsed = time.time() - start_time
    print(f"Response time: {elapsed:.2f} seconds")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Company: {data.get('company_name')}")
        print(f"Response preview: {data.get('response', '')[:200]}...")
        
        if elapsed < 2.0:
            print("SUCCESS: Fast response under 2 seconds!")
        else:
            print("SLOW: Still over 2 seconds")
    else:
        print(f"Error: {response.text[:300]}")
        
except Exception as e:
    elapsed = time.time() - start_time
    print(f"Error after {elapsed:.2f}s: {e}")