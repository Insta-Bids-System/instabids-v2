#!/usr/bin/env python3

import requests
import json

# Send third message from homeowner
url = "http://localhost:8008/api/messages/send"
payload = {
    "bid_card_id": "2cb6e43a-2c92-4e30-93f2-e44629f8975f",
    "content": "That sounds great! I have a few questions: What's your experience with kitchen remodels? Do you provide free estimates? Also, what's your typical timeline for a project like this?",
    "sender_type": "homeowner", 
    "sender_id": "11111111-1111-1111-1111-111111111111",
    "conversation_id": "5034dc04-4f70-4375-a442-b80817346906"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if result.get('success'):
        print(f"\n✅ Message 3 sent successfully!")
        print(f"Filtered content: {result.get('filtered_content')}")
        print(f"Content filtered: {result.get('content_filtered')}")
    else:
        print(f"\n❌ Message 3 failed: {result.get('error')}")
        
except Exception as e:
    print(f"Error: {e}")