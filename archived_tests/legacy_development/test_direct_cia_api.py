#!/usr/bin/env python3
"""
Direct CIA API test - simplified version
"""

import requests
import json
import time
import uuid

def test_cia_api():
    print("=== CIA API DIRECT TEST ===")
    
    user_id = f"test-user-{uuid.uuid4().hex[:6]}"
    conversation_id = f"test-conv-{uuid.uuid4().hex[:6]}"
    
    print(f"User ID: {user_id}")
    print(f"Conversation ID: {conversation_id}")
    
    # Test 1: Simple greeting
    print("\n--- Test 1: Simple Greeting ---")
    response = requests.post(
        "http://localhost:8008/api/cia/stream",
        json={
            "messages": [{"role": "user", "content": "Hello, I need help with a bathroom renovation."}],
            "conversation_id": conversation_id,
            "user_id": user_id
        },
        timeout=10,
        stream=True
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("Response chunks:")
        count = 0
        for line in response.iter_lines():
            if line and count < 10:  # Just show first 10 chunks
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if 'choices' in data:
                            content = data['choices'][0].get('delta', {}).get('content', '')
                            if content:
                                print(f"  Chunk {count}: {content}")
                                count += 1
                    except:
                        pass
            elif count >= 10:
                break
    
    # Test 2: Check potential bid card
    print("\n--- Test 2: Check Potential Bid Card ---")
    time.sleep(2)
    
    try:
        bid_check = requests.get(
            f"http://localhost:8008/api/cia/conversation/{conversation_id}/potential-bid-card",
            timeout=5
        )
        
        print(f"Bid card check status: {bid_check.status_code}")
        if bid_check.status_code == 200:
            data = bid_check.json()
            print("Bid card data found:")
            print(json.dumps(data, indent=2)[:500] + "...")
        else:
            print("No bid card found yet")
            
    except Exception as e:
        print(f"Bid card check error: {e}")
    
    # Test 3: Follow-up message with details
    print("\n--- Test 3: Follow-up with Project Details ---")
    response2 = requests.post(
        "http://localhost:8008/api/cia/stream",
        json={
            "messages": [
                {"role": "user", "content": "Hello, I need help with a bathroom renovation."},
                {"role": "user", "content": "I want to update my master bathroom. Budget is $25,000. I'm at 456 Oak St, Denver CO 80203. My name is John Smith."}
            ],
            "conversation_id": conversation_id,
            "user_id": user_id
        },
        timeout=10,
        stream=True
    )
    
    print(f"Follow-up status: {response2.status_code}")
    
    # Test 4: Final bid card check
    print("\n--- Test 4: Final Bid Card Check ---")
    time.sleep(2)
    
    try:
        final_bid_check = requests.get(
            f"http://localhost:8008/api/cia/conversation/{conversation_id}/potential-bid-card",
            timeout=5
        )
        
        print(f"Final bid card status: {final_bid_check.status_code}")
        if final_bid_check.status_code == 200:
            data = final_bid_check.json()
            print("Final bid card data:")
            if 'fields' in data:
                print(f"  Fields extracted: {len(data['fields'])}")
                for key, value in data['fields'].items():
                    print(f"    {key}: {value}")
            print(f"  Completion: {data.get('completion_percentage', 0)}%")
        else:
            print("No bid card found")
            
    except Exception as e:
        print(f"Final bid card check error: {e}")

if __name__ == "__main__":
    test_cia_api()