#!/usr/bin/env python3

import requests
import json

# Send fourth message from contractor
url = "http://localhost:8008/api/messages/send"
payload = {
    "bid_card_id": "2cb6e43a-2c92-4e30-93f2-e44629f8975f",
    "content": "Great questions John! I have 15 years experience in kitchen remodeling and have completed over 200 projects. Yes, I provide free estimates - I can visit your home to assess the space and provide a detailed quote. For a $20,000 kitchen remodel, typical timeline is 3-4 weeks from start to finish. Would you like to schedule a consultation? My phone is 555-MIKE-123 or you can email me at mike@mikesconstruction.com",
    "sender_type": "contractor", 
    "sender_id": "22222222-2222-2222-2222-222222222222",
    "conversation_id": "5034dc04-4f70-4375-a442-b80817346906"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if result.get('success'):
        print(f"\nMessage 4 sent successfully!")
        print(f"Filtered content: {result.get('filtered_content')}")
        print(f"Content filtered: {result.get('content_filtered')}")
        if result.get('content_filtered'):
            print(f"Filter reasons: {result.get('filter_reasons')}")
    else:
        print(f"\nMessage 4 failed: {result.get('error')}")
        
except Exception as e:
    print(f"Error: {e}")