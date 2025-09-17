import requests
import time

# Test COIA endpoint
response = requests.post(
    "http://localhost:8008/api/coia/landing",
    json={
        "session_id": f"coia-perf-test-{int(time.time())}",
        "message": "I run Test Solar Company",
        "company_name": "Test Solar Company",
        "location": "San Francisco, CA"
    }
)

print(f"Status: {response.status_code}")
print(f"Response time: {response.elapsed.total_seconds():.2f}s")
if response.status_code == 200:
    print(f"Response preview: {response.text[:200]}...")
else:
    print(f"Error: {response.text}")