#!/usr/bin/env python3
"""
Test to show exactly what the CIA field extraction does now
"""
import requests
import json
import uuid
import time

BASE_URL = "http://localhost:8008"

def test_turn(session_id, user_id, message, turn_num):
    """Test one conversation turn and show what gets extracted"""
    print(f"\n{'='*60}")
    print(f"🔄 TURN {turn_num}")
    print(f"💬 USER: {message}")
    
    # Send message
    request_data = {
        "messages": [{"role": "user", "content": message}],
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": session_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/cia/stream", json=request_data, timeout=30, stream=True)
        
        if response.status_code == 200:
            # Consume stream
            for line in response.iter_lines():
                if line and "[DONE]" in line.decode():
                    break
            print("✅ Conversation completed")
        else:
            print(f"❌ Failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    
    # Wait for processing
    time.sleep(3)
    
    # Get bid card to see what was extracted
    try:
        response = requests.get(f"{BASE_URL}/api/cia/conversation/{session_id}/potential-bid-card")
        if response.status_code == 200:
            data = response.json()
            fields = data.get('fields_collected', {})
            filled = {k: v for k, v in fields.items() if v not in [None, "", [], {}]}
            
            print(f"📋 BID CARD AFTER TURN {turn_num}:")
            print(f"   Completion: {data.get('completion_percentage', 0)}%")
            print(f"   Total Fields: {len(filled)}")
            
            print(f"📊 EXTRACTED FIELDS:")
            for field, value in filled.items():
                print(f"   ✅ {field}: {value}")
            
            return {
                'completion': data.get('completion_percentage', 0),
                'fields': filled,
                'field_count': len(filled)
            }
        else:
            print("❌ No bid card found")
            return None
            
    except Exception as e:
        print(f"❌ Error getting bid card: {e}")
        return None

def main():
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    
    print("🧪 TESTING: What Actually Gets Extracted")
    print(f"Session: {session_id}")
    
    # Test 3 strategic turns
    turns = [
        "I need bathroom renovation in Manhattan 10001, budget $30,000",
        "Timeline is 6 weeks, want marble countertops and subway tile",
        "Need licensed contractors with insurance"
    ]
    
    previous_result = None
    
    for i, message in enumerate(turns, 1):
        result = test_turn(session_id, user_id, message, i)
        
        if result and previous_result:
            # Show what changed
            new_fields = set(result['fields'].keys()) - set(previous_result['fields'].keys())
            updated_fields = []
            for field in result['fields']:
                if field in previous_result['fields'] and result['fields'][field] != previous_result['fields'][field]:
                    updated_fields.append(field)
            
            print(f"\n🔄 CHANGES FROM TURN {i-1} TO {i}:")
            print(f"   Completion: {previous_result['completion']}% → {result['completion']}%")
            print(f"   New Fields: {list(new_fields)}")
            print(f"   Updated Fields: {updated_fields}")
        
        previous_result = result
    
    print(f"\n{'='*60}")
    print("🎯 FINAL SUMMARY")
    if previous_result:
        print(f"✅ Final Completion: {previous_result['completion']}%")
        print(f"✅ Total Fields Extracted: {previous_result['field_count']}")
        print(f"✅ Progressive Updates: {'Working' if previous_result['completion'] > 30 else 'Not Working'}")
    else:
        print("❌ No final result")

if __name__ == "__main__":
    main()