#!/usr/bin/env python3
"""
Test what's ACTUALLY working right now.
"""

import requests
import json

def test_cia_chat():
    """Test the actual CIA chat endpoint."""
    
    # Test simple chat
    response = requests.post(
        "http://localhost:8008/api/cia/stream",
        json={
            "messages": [
                {"role": "user", "content": "I need a new deck installed. My budget is $15,000 to $20,000. I'm at 123 Main St, Austin TX 78701."}
            ],
            "conversation_id": "test-conv-789",
            "user_id": "test-user-456"
        }
    )
    
    print(f"Status: {response.status_code}")
    print("\nResponse (first 1000 chars):")
    print(response.text[:1000])
    
    # Parse SSE response for extraction data
    lines = response.text.split('\n')
    ai_response = ""
    extracted_data = {}
    
    for line in lines:
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                if 'choices' in data:
                    content = data['choices'][0].get('delta', {}).get('content', '')
                    ai_response += content
            except:
                pass
    
    print("\n" + "="*60)
    print("Full AI Response:")
    print(ai_response[:500] + "..." if len(ai_response) > 500 else ai_response)
    
    # Now test with a follow-up message to see if it maintains context
    print("\n" + "="*60)
    print("Testing follow-up message...")
    
    response2 = requests.post(
        "http://localhost:8008/api/cia/stream",
        json={
            "messages": [
                {"role": "user", "content": "I need a new deck installed. My budget is $15,000 to $20,000. I'm at 123 Main St, Austin TX 78701."},
                {"role": "assistant", "content": ai_response},
                {"role": "user", "content": "My name is John Smith and my email is john@example.com"}
            ],
            "conversation_id": "test-conv-789",
            "user_id": "test-user-456"
        }
    )
    
    print(f"Follow-up Status: {response2.status_code}")
    
    # Check potential bid card endpoint
    print("\n" + "="*60)
    print("Checking potential bid card...")
    
    bid_response = requests.get(
        f"http://localhost:8008/api/cia/conversation/test-conv-789/potential-bid-card"
    )
    
    if bid_response.status_code == 200:
        print("Potential bid card data:")
        print(json.dumps(bid_response.json(), indent=2))
    else:
        print(f"No bid card data: {bid_response.status_code}")

if __name__ == "__main__":
    print("Testing ACTUAL CIA Chat System...")
    print("="*60)
    test_cia_chat()