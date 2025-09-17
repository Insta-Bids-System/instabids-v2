import requests
import json

# Create a real homeowner conversation
def test_real_homeowner_creation():
    url = "http://localhost:8008/api/cia/chat"
    
    # First message - bathroom emergency
    payload = {
        "message": "Hi, I need help with my bathroom. The toilet is leaking and it's causing water damage!",
        "user_id": "test-user-123",
        "session_id": "test-session-123"
    }
    
    print("Sending bathroom emergency request...")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Follow up with more details
    if response.status_code == 200:
        print("\n\nSending follow-up with details...")
        payload["message"] = "It's been leaking for about 2 days now. I'm in Chicago, zip code 60614. I need someone ASAP!"
        response2 = requests.post(url, json=payload)
        print(f"Status: {response2.status_code}")
        print(f"Response: {json.dumps(response2.json(), indent=2)}")

if __name__ == "__main__":
    test_real_homeowner_creation()