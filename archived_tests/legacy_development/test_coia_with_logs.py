import requests
import time
import subprocess

# Test COIA endpoint
print("Testing COIA endpoint...")
response = requests.post(
    "http://localhost:8008/api/coia/landing",
    json={
        "session_id": f"perf-test-{int(time.time())}",
        "message": "I run Solar Panel Installation LLC",
        "company_name": "Solar Panel Installation LLC",
        "location": "Austin, TX"
    }
)

print(f"Status: {response.status_code}")
print(f"Response time: {response.elapsed.total_seconds():.2f}s")

# Wait for background processing to start
print("\nWaiting 3 seconds for background processing...")
time.sleep(3)

# Check Docker logs for PERF entries
print("\nChecking Docker logs for PERF entries...")
result = subprocess.run(
    ['docker', 'logs', 'instabids-instabids-backend-1', '--tail=100'],
    capture_output=True,
    text=True
)

# Filter for relevant logs
for line in result.stdout.split('\n'):
    if any(keyword in line for keyword in ['Landing request', 'PERF', '🔥', 'Background', 'DeepAgents mode']):
        print(line)