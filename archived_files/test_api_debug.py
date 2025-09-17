import requests
import json

# Test the conversations API
response = requests.get(
    "http://localhost:8008/api/messages/conversations/4c9dfb00-ee77-41da-8b8d-2615dbd31d95",
    params={
        "user_type": "homeowner",
        "user_id": "11111111-1111-1111-1111-111111111111"
    }
)

print(f"Status: {response.status_code}")
print(f"Response type: {type(response.json())}")
print(f"Response content: {json.dumps(response.json(), indent=2)[:1000]}")