#!/usr/bin/env python3
"""
Test CIA field updates through strategic conversation turns
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

def send_cia_message(session_id, user_id, message, conversation_history):
    """Send message to CIA and consume full response"""
    conversation_history.append({"role": "user", "content": message})
    
    request_data = {
        "messages": conversation_history,
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": session_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/cia/stream",
            json=request_data,
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            content_chunks = []
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode()
                    if line_str.startswith("data: "):
                        data_part = line_str[6:]
                        if data_part == "[DONE]":
                            break
                        elif data_part.strip():
                            try:
                                chunk_data = json.loads(data_part)
                                if "choices" in chunk_data:
                                    content = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if content:
                                        content_chunks.append(content)
                            except:
                                pass
            
            response_text = "".join(content_chunks)
            conversation_history.append({"role": "assistant", "content": response_text})
            return response_text
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Exception: {e}"

def get_bid_card_status(session_id):
    """Get current bid card status"""
    try:
        response = requests.get(f"{BASE_URL}/api/cia/conversation/{session_id}/potential-bid-card")
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

def print_field_comparison(before, after, turn_number):
    """Print comparison of bid card fields before/after turn"""
    print(f"\n📊 TURN {turn_number} FIELD UPDATES:")
    
    before_fields = before.get('fields_collected', {}) if before else {}
    after_fields = after.get('fields_collected', {}) if after else {}
    
    before_completion = before.get('completion_percentage', 0) if before else 0
    after_completion = after.get('completion_percentage', 0) if after else 0
    
    print(f"   Completion: {before_completion}% → {after_completion}%")
    
    # Show field changes
    all_fields = set(before_fields.keys()) | set(after_fields.keys())
    
    for field in sorted(all_fields):
        before_val = before_fields.get(field)
        after_val = after_fields.get(field)
        
        if before_val != after_val:
            if before_val in [None, "", [], {}] and after_val not in [None, "", [], {}]:
                print(f"   ✅ NEW: {field} = {after_val}")
            elif before_val not in [None, "", [], {}] and after_val not in [None, "", [], {}]:
                print(f"   🔄 UPDATED: {field} = {before_val} → {after_val}")

def test_strategic_conversation_turns():
    """Test strategic conversation turns that should update different fields"""
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    conversation_history = []
    
    print("=" * 60)
    print("🧪 CIA STRATEGIC FIELD UPDATE TEST")
    print("=" * 60)
    print(f"Session ID: {session_id}")
    
    # Strategic messages targeting specific field types
    test_turns = [
        {
            "message": "I need kitchen renovation in Brooklyn 11201",
            "targets": ["project_type", "zip_code", "location"]
        },
        {
            "message": "Budget is $45,000, timeline is urgent - need it done in 4 weeks",
            "targets": ["budget_range", "timeline", "urgency"]
        },
        {
            "message": "I want quartz countertops, white cabinets, and subway tile backsplash",
            "targets": ["materials", "project_description"]
        },
        {
            "message": "Need licensed contractors with insurance, and work must be done weekdays only",
            "targets": ["contractor_preferences", "special_requirements"]
        }
    ]
    
    previous_bid_card = None
    
    for i, turn in enumerate(test_turns, 1):
        print(f"\n{'='*20} TURN {i} {'='*20}")
        print(f"🎯 Target Fields: {', '.join(turn['targets'])}")
        print(f"💬 Message: {turn['message']}")
        
        # Send message
        response = send_cia_message(session_id, user_id, turn['message'], conversation_history)
        print(f"🤖 Response: {response[:150]}{'...' if len(response) > 150 else ''}")
        
        # Wait for state management
        time.sleep(4)
        
        # Get updated bid card
        current_bid_card = get_bid_card_status(session_id)
        
        # Show field updates
        print_field_comparison(previous_bid_card, current_bid_card, i)
        
        previous_bid_card = current_bid_card
    
    # Final analysis
    print(f"\n{'='*60}")
    print("🎯 FINAL ANALYSIS")
    print(f"{'='*60}")
    
    if current_bid_card:
        fields = current_bid_card.get('fields_collected', {})
        filled_fields = {k: v for k, v in fields.items() if v not in [None, "", [], {}]}
        completion = current_bid_card.get('completion_percentage', 0)
        
        print(f"✅ Bid Card ID: {current_bid_card.get('id')}")
        print(f"📈 Final Completion: {completion}%")
        print(f"📝 Fields Filled: {len(filled_fields)} / {len(fields)}")
        print(f"🔄 Ready for Conversion: {current_bid_card.get('ready_for_conversion', False)}")
        
        print(f"\n📋 ALL COLLECTED FIELDS:")
        for field, value in filled_fields.items():
            print(f"   ✅ {field}: {value}")
        
        missing = current_bid_card.get('missing_fields', [])
        if missing:
            print(f"\n❌ Still Missing: {', '.join(missing)}")
        
        # Success assessment
        expected_updates = 8  # Approximate number of fields we expect to fill
        if len(filled_fields) >= 6 and completion >= 50:
            print(f"\n🎉 SUCCESS: CIA effectively builds contextual bid cards!")
            print(f"   ✅ Multi-turn conversation tracking works")
            print(f"   ✅ Field extraction and updates functional")
            print(f"   ✅ Context maintained across conversation")
            return True
        else:
            print(f"\n⚠️  PARTIAL SUCCESS: Some field updates working")
            print(f"   ℹ️  May need more conversation turns for full completion")
            return False
    else:
        print("❌ FAILED: No bid card created")
        return False

def main():
    print("🚀 Testing CIA field updates through strategic conversation")
    success = test_strategic_conversation_turns()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 FIELD UPDATE TEST PASSED!")
        print("✅ CIA successfully builds and updates bid cards through conversation")
    else:
        print("❌ FIELD UPDATE TEST NEEDS IMPROVEMENT")
        print("⚠️  Check field extraction and update logic")

if __name__ == "__main__":
    main()