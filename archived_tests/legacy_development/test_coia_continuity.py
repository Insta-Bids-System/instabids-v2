#!/usr/bin/env python3
"""Test COIA conversation continuity with same contractor_lead_id"""

import requests
import json
import time

def test_conversation_continuity():
    """Test that same contractor_lead_id maintains conversation context"""
    
    contractor_lead_id = "test-continuity-dec12"
    base_url = "http://localhost:8008/api/coia/chat"
    
    print(f"Testing COIA conversation continuity with contractor_lead_id: {contractor_lead_id}")
    print("=" * 70)
    
    # First message
    print("\n1. Sending first message...")
    response1 = requests.post(base_url, json={
        "contractor_lead_id": contractor_lead_id,
        "message": "Hi, I'm looking for information about JM Holiday Lighting"
    })
    
    if response1.status_code != 200:
        print(f"❌ First request failed: {response1.status_code}")
        print(f"Response: {response1.text}")
        return
    
    data1 = response1.json()
    conv_id_1 = data1.get('conversation_id')
    print(f"✅ First request successful")
    print(f"   Conversation ID: {conv_id_1}")
    print(f"   Response preview: {data1.get('response', '')[:150]}...")
    
    # Wait a moment
    time.sleep(2)
    
    # Second message - should continue same conversation
    print("\n2. Sending second message with same contractor_lead_id...")
    response2 = requests.post(base_url, json={
        "contractor_lead_id": contractor_lead_id,
        "message": "What services do they offer?"
    })
    
    if response2.status_code != 200:
        print(f"❌ Second request failed: {response2.status_code}")
        print(f"Response: {response2.text}")
        return
    
    data2 = response2.json()
    conv_id_2 = data2.get('conversation_id')
    print(f"✅ Second request successful")
    print(f"   Conversation ID: {conv_id_2}")
    print(f"   Response preview: {data2.get('response', '')[:150]}...")
    
    # Verify continuity
    print("\n3. Verifying conversation continuity...")
    if conv_id_1 and conv_id_2:
        if conv_id_1 == conv_id_2:
            print(f"✅ SUCCESS: Same conversation maintained!")
            print(f"   Both requests used conversation ID: {conv_id_1}")
        else:
            print(f"❌ FAILURE: Different conversations created!")
            print(f"   First ID:  {conv_id_1}")
            print(f"   Second ID: {conv_id_2}")
    else:
        print(f"❌ ERROR: Missing conversation IDs")
        print(f"   First ID:  {conv_id_1}")
        print(f"   Second ID: {conv_id_2}")
    
    # Third message to further verify
    print("\n4. Sending third message to verify persistence...")
    response3 = requests.post(base_url, json={
        "contractor_lead_id": contractor_lead_id,
        "message": "What about their pricing?"
    })
    
    if response3.status_code == 200:
        data3 = response3.json()
        conv_id_3 = data3.get('conversation_id')
        print(f"✅ Third request successful")
        print(f"   Conversation ID: {conv_id_3}")
        
        if conv_id_3 == conv_id_1:
            print(f"✅ CONFIRMED: All three messages in same conversation!")
        else:
            print(f"❌ Third message created new conversation: {conv_id_3}")

if __name__ == "__main__":
    test_conversation_continuity()