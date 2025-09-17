import requests
import json
import uuid

# Create a real homeowner conversation with proper UUID
def test_real_homeowner_creation():
    url = "http://localhost:8008/api/cia/chat"
    
    # Generate a proper UUID
    user_id = str(uuid.uuid4())
    session_id = f"session-{int(time.time())}"
    
    # First message - bathroom emergency
    payload = {
        "message": "Hi, I need help with my bathroom. The toilet is leaking and it's causing water damage!",
        "user_id": user_id,
        "session_id": session_id
    }
    
    print(f"Creating homeowner with UUID: {user_id}")
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
        
        # One more message to complete the details
        if response2.status_code == 200:
            print("\n\nProviding more specifics...")
            payload["message"] = "The leak is from the base of the toilet. There's water damage on the bathroom floor and it's starting to warp. I had to shut off the water. My name is Sarah Johnson and my phone is 312-555-0123."
            response3 = requests.post(url, json=payload)
            print(f"Status: {response3.status_code}")
            print(f"Response: {json.dumps(response3.json(), indent=2)}")
    
    return user_id

if __name__ == "__main__":
    import time
    user_id = test_real_homeowner_creation()
    print(f"\n\nHomeowner created with ID: {user_id}")