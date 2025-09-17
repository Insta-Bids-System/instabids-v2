#!/usr/bin/env python3
"""
8-turn CIA conversation test for contextual bid card building
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

def send_message_and_get_response(session_id, user_id, message, conversation_history):
    """Send message to CIA and get full response"""
    print(f"\n🔄 USER: {message}")
    
    # Add to conversation history
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
            timeout=45,
            stream=True
        )
        
        if response.status_code == 200:
            # Consume full stream
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
            
            assistant_response = "".join(content_chunks)
            print(f"🤖 ASSISTANT: {assistant_response[:200]}{'...' if len(assistant_response) > 200 else ''}")
            
            # Add to conversation history
            conversation_history.append({"role": "assistant", "content": assistant_response})
            
            return assistant_response
        else:
            print(f"❌ Request failed: {response.status_code}")
            return ""
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return ""

def check_bid_card_status(session_id):
    """Check bid card status and return details"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/cia/conversation/{session_id}/potential-bid-card"
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {}
    except:
        return {}

def print_bid_card_status(bid_card_data, turn_number):
    """Print formatted bid card status"""
    if not bid_card_data:
        print(f"📋 Turn {turn_number}: ❌ No bid card found")
        return
    
    completion = bid_card_data.get('completion_percentage', 0)
    fields = bid_card_data.get('fields_collected', {})
    filled_fields = {k: v for k, v in fields.items() if v not in [None, "", [], {}]}
    
    print(f"📋 Turn {turn_number}: {completion}% complete, {len(filled_fields)} fields filled")
    print(f"   Fields: {list(filled_fields.keys())}")

def run_8_turn_conversation_test():
    """Run 8-turn conversation test"""
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    conversation_history = []
    
    print("=" * 70)
    print("🧪 CIA 8-TURN CONVERSATION TEST")
    print("=" * 70)
    print(f"Session ID: {session_id}")
    
    # 8 strategic conversation turns
    turns = [
        "I need to renovate my bathroom in Manhattan",
        "It's a master bathroom, around 100 square feet. The current setup is really outdated from the 1990s.",
        "I'm in zip code 10001, Upper West Side. Budget is around $25,000 to $35,000.",
        "Timeline is flexible, maybe 6-8 weeks. I want a modern spa-like feel with high-end finishes.",
        "I'm thinking marble countertops, subway tile shower, new vanity and toilet. Quality is important.",
        "I work from home so minimal noise during business hours would be great. Also need licensed contractors.",
        "Do you think we could save money with group bidding? I'm willing to coordinate with neighbors.",
        "Perfect! Let's get some contractor quotes. I'm excited to see what's possible within my budget."
    ]
    
    for i, message in enumerate(turns, 1):
        print(f"\n{'='*20} TURN {i}/8 {'='*20}")
        
        # Send message
        response = send_message_and_get_response(session_id, user_id, message, conversation_history)
        
        # Wait for state management
        time.sleep(3)
        
        # Check bid card status
        bid_card_data = check_bid_card_status(session_id)
        print_bid_card_status(bid_card_data, i)
    
    # Final analysis
    print(f"\n{'='*70}")
    print("🎯 FINAL RESULTS")
    print(f"{'='*70}")
    
    final_bid_card = check_bid_card_status(session_id)
    if final_bid_card:
        completion = final_bid_card.get('completion_percentage', 0)
        fields = final_bid_card.get('fields_collected', {})
        filled_fields = {k: v for k, v in fields.items() if v not in [None, "", [], {}]}
        
        print(f"✅ BID CARD CREATED SUCCESSFULLY")
        print(f"   ID: {final_bid_card.get('id')}")
        print(f"   Final Completion: {completion}%")
        print(f"   Fields Filled: {len(filled_fields)}")
        print(f"   Ready for Conversion: {final_bid_card.get('ready_for_conversion', False)}")
        
        print(f"\n📋 COLLECTED INFORMATION:")
        for field, value in filled_fields.items():
            print(f"   ✅ {field}: {value}")
        
        missing = final_bid_card.get('missing_fields', [])
        if missing:
            print(f"\n❌ Missing Fields: {', '.join(missing)}")
        
        # Success criteria
        if completion >= 60 and len(filled_fields) >= 5:
            print(f"\n🎉 TEST PASSED: High-quality contextual bid card created!")
            return True
        else:
            print(f"\n⚠️  TEST PARTIAL: More information needed for complete bid card")
            return False
    else:
        print("❌ TEST FAILED: No bid card created")
        return False

def main():
    print("🚀 Starting 8-turn CIA conversation test")
    success = run_8_turn_conversation_test()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 8-TURN CONVERSATION TEST PASSED!")
        print("✅ CIA agent builds contextual bid cards through multi-turn conversations")
    else:
        print("❌ 8-TURN CONVERSATION TEST FAILED!")

if __name__ == "__main__":
    main()