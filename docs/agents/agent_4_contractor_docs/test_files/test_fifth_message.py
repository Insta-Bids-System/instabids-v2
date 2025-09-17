#!/usr/bin/env python3

import requests
import json

# Send fifth message from homeowner
url = "http://localhost:8008/api/messages/send"
payload = {
    "bid_card_id": "2cb6e43a-2c92-4e30-93f2-e44629f8975f",
    "content": "That sounds perfect Mike! 15 years experience is exactly what I'm looking for. I'd love to schedule a consultation. When would be a good time this week? Also, do you handle all the permits and coordination with other trades like electrical and plumbing?",
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
        print(f"\nMessage 5 sent successfully!")
        print(f"Filtered content: {result.get('filtered_content')}")
        print(f"Content filtered: {result.get('content_filtered')}")
    else:
        print(f"\nMessage 5 failed: {result.get('error')}")
        
except Exception as e:
    print(f"Error: {e}")