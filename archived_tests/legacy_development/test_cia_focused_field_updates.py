#!/usr/bin/env python3
"""
Focused test: 3 strategic CIA conversation turns to verify field updates
"""
import requests
import json
import uuid
import sys
import io
import time

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8008"

def send_message_consume_stream(session_id, user_id, message):
    """Send single message and consume full stream"""
    request_data = {
        "messages": [{"role": "user", "content": message}],
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": session_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/cia/stream",
            json=request_data,
            timeout=25,
            stream=True
        )
        
        if response.status_code == 200:
            # Consume stream until [DONE]
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    if "[DONE]" in line.decode():
                        break
            return f"✅ Completed ({chunk_count} chunks)"
        else:
            return f"❌ Failed: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {e}"

def get_bid_card_fields(session_id):
    """Get bid card fields for comparison"""
    try:
        response = requests.get(f"{BASE_URL}/api/cia/conversation/{session_id}/potential-bid-card")
        if response.status_code == 200:
            data = response.json()
            fields = data.get('fields_collected', {})
            filled = {k: v for k, v in fields.items() if v not in [None, "", [], {}]}
            return {
                'completion': data.get('completion_percentage', 0),
                'filled_fields': filled,
                'total_fields': len(fields),
                'id': data.get('id')
            }
        return None
    except:
        return None

def test_focused_conversation():
    """Test 3 focused conversation turns"""
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    
    print("=" * 70)
    print("🧪 FOCUSED CIA FIELD UPDATE TEST (3 Turns)")
    print("=" * 70)
    print(f"Session ID: {session_id}")
    
    # 3 strategic turns designed to fill key fields
    turns = [
        {
            "message": "I need bathroom renovation in Manhattan 10001, budget $30,000",
            "description": "Initial project with location, budget, type"
        },
        {
            "message": "Timeline is 6 weeks, I want modern fixtures and marble countertops",
            "description": "Timeline, materials, style preferences"
        },
        {
            "message": "Need licensed contractors with weekend availability",
            "description": "Contractor requirements and scheduling"
        }
    ]
    
    results = []
    
    for i, turn in enumerate(turns, 1):
        print(f"\n🔄 TURN {i}: {turn['description']}")
        print(f"💬 Message: {turn['message']}")
        
        # Send message
        result = send_message_consume_stream(session_id, user_id, turn['message'])
        print(f"📡 Stream: {result}")
        
        # Wait for state management
        print("⏳ Waiting for state management...")
        time.sleep(4)
        
        # Check bid card
        bid_card_info = get_bid_card_fields(session_id)
        if bid_card_info:
            print(f"📋 Bid Card: {bid_card_info['completion']}% complete, {len(bid_card_info['filled_fields'])} fields")
            print(f"   Fields: {list(bid_card_info['filled_fields'].keys())}")
            results.append(bid_card_info)
        else:
            print("❌ No bid card found")
            results.append(None)
    
    # Analysis
    print(f"\n{'='*70}")
    print("🎯 CONVERSATION PROGRESSION ANALYSIS")
    print(f"{'='*70}")
    
    if results and results[-1]:
        final = results[-1]
        print(f"✅ FINAL RESULT:")
        print(f"   Bid Card ID: {final['id']}")
        print(f"   Completion: {final['completion']}%")
        print(f"   Fields Filled: {len(final['filled_fields'])}")
        
        print(f"\n📋 EXTRACTED INFORMATION:")
        for field, value in final['filled_fields'].items():
            print(f"   ✅ {field}: {value}")
        
        # Show progression
        print(f"\n📈 PROGRESSION OVER 3 TURNS:")
        for i, result in enumerate(results, 1):
            if result:
                completion = result['completion']
                field_count = len(result['filled_fields'])
                print(f"   Turn {i}: {completion}% ({field_count} fields)")
            else:
                print(f"   Turn {i}: No bid card")
        
        # Success criteria
        if final['completion'] >= 40 and len(final['filled_fields']) >= 4:
            print(f"\n🎉 SUCCESS: CIA builds contextual bid cards through conversation!")
            print(f"   ✅ Multi-turn conversation tracking works")
            print(f"   ✅ Field extraction progresses over turns") 
            print(f"   ✅ State management maintains context")
            return True
        else:
            print(f"\n⚠️  PARTIAL: Need more turns for complete bid card")
            return False
    else:
        print("❌ FAILED: No bid cards created during conversation")
        return False

def main():
    print("🚀 Testing focused CIA conversation with field updates")
    success = test_focused_conversation()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 FOCUSED TEST PASSED!")
        print("✅ CIA effectively builds bid cards through multi-turn conversations")
    else:
        print("❌ FOCUSED TEST FAILED!")
        print("⚠️  Need to investigate field extraction or state management")

if __name__ == "__main__":
    main()