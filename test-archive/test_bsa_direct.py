"""
Direct test of BSA endpoint
"""
import requests
import json

# Test data
data = {
    "contractor_id": "22222222-2222-2222-2222-222222222222",
    "message": "Show me turf projects near 33442",
    "session_id": "direct-test"
}

print("Testing BSA endpoint directly...")
print(f"Request: {json.dumps(data, indent=2)}")
print("-" * 50)

try:
    # Make request
    response = requests.post(
        "http://localhost:8008/api/bsa/unified-stream",
        json=data,
        stream=True,
        timeout=20
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("Response streaming:")
        event_count = 0
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                print(f"  {line_str[:100]}")
                event_count += 1
                if event_count > 10:
                    print("  ... (truncated)")
                    break
        
        if event_count == 0:
            print("  NO DATA RETURNED")
    else:
        print(f"Error: {response.text[:500]}")
        
except Exception as e:
    print(f"Exception: {e}")