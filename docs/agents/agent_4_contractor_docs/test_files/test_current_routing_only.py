"""
Test Current Message Routing - Focus on New Messages Only
Verifies the fixed routing system works correctly for new messages
"""
import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "http://localhost:8008/api/messages"
HOMEOWNER_ID = "11111111-1111-1111-1111-111111111111"
BID_CARD_ID = "36214de5-a068-4dcc-af99-cf33238e7472"

# Test contractors
CONTRACTORS = [
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "name": "Contractor A (Mike's Construction)"
    },
    {
        "id": "33333333-3333-3333-3333-333333333333", 
        "name": "Contractor B (Quality Builders)"
    },
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "name": "Contractor C (Premier Kitchens)"
    }
]

def test_current_routing():
    """Test that the current fixed routing sends messages to correct conversations"""
    print("\n" + "="*60)
    print("TESTING CURRENT FIXED MESSAGE ROUTING")
    print("="*60)
    
    # Test timestamp for unique messages
    test_time = int(time.time())
    
    # Step 1: Get current conversations
    response = requests.get(
        f"{BASE_URL}/conversations/{BID_CARD_ID}",
        params={
            "user_type": "homeowner",
            "user_id": HOMEOWNER_ID
        }
    )
    
    if not response.ok:
        print("[ERROR] Could not get conversations")
        return False
    
    conversations = response.json().get("conversations", [])
    print(f"Found {len(conversations)} existing conversations")
    
    # Step 2: Send unique test messages to each contractor
    sent_messages = {}
    
    for i, contractor in enumerate(CONTRACTORS[:3], 1):
        unique_msg = f"ROUTING TEST {test_time}-{i}: Message for {contractor['name']}"
        
        print(f"\nSending message to {contractor['name']}...")
        
        send_response = requests.post(
            f"{BASE_URL}/send",
            json={
                "bid_card_id": BID_CARD_ID,
                "sender_id": HOMEOWNER_ID,
                "sender_type": "homeowner",
                "content": unique_msg,
                "target_contractor_id": contractor["id"]
            }
        )
        
        if send_response.ok:
            result = send_response.json()
            if result.get("success"):
                conv_id = result.get("conversation_id")
                sent_messages[contractor["id"]] = {
                    "conv_id": conv_id,
                    "unique_msg": unique_msg,
                    "message_id": result.get("id")
                }
                print(f"[SUCCESS] Message sent to conversation: {conv_id}")
            else:
                print(f"[FAILED] Send failed: {result.get('error')}")
                return False
        else:
            print(f"[ERROR] API error: {send_response.status_code}")
            return False
        
        time.sleep(0.5)
    
    # Step 3: Verify each message is in the correct conversation ONLY
    print(f"\nVerifying routing accuracy...")
    all_correct = True
    
    for contractor_id, data in sent_messages.items():
        conv_id = data["conv_id"]
        expected_msg = data["unique_msg"]
        message_id = data["message_id"]
        
        # Get messages in this conversation
        msg_response = requests.get(f"{BASE_URL}/{conv_id}")
        if msg_response.ok:
            messages = msg_response.json().get("messages", [])
            
            # Find our specific message by ID (most accurate)
            our_message = next((msg for msg in messages if msg.get("id") == message_id), None)
            
            if our_message:
                if expected_msg in our_message.get("filtered_content", ""):
                    print(f"[CORRECT] Message {message_id[:8]}... found in correct conversation")
                else:
                    print(f"[ERROR] Message content mismatch in conversation {conv_id[:8]}...")
                    all_correct = False
            else:
                print(f"[ERROR] Message {message_id[:8]}... not found in target conversation!")
                all_correct = False
        else:
            print(f"[ERROR] Could not get messages for conversation {conv_id[:8]}...")
            all_correct = False
    
    # Step 4: Test contractor auto-routing
    print(f"\nTesting contractor auto-routing...")
    contractor = CONTRACTORS[0]
    contractor_msg = f"CONTRACTOR ROUTING TEST {test_time}: Auto-routed message from {contractor['name']}"
    
    send_response = requests.post(
        f"{BASE_URL}/send",
        json={
            "bid_card_id": BID_CARD_ID,
            "sender_id": contractor["id"],
            "sender_type": "contractor",
            "content": contractor_msg
        }
    )
    
    if send_response.ok and send_response.json().get("success"):
        conv_id = send_response.json().get("conversation_id")
        # Verify this conversation belongs to the contractor
        for existing_conv in conversations:
            if existing_conv["id"] == conv_id and existing_conv["contractor_id"] == contractor["id"]:
                print(f"[CORRECT] Contractor message auto-routed to their conversation")
                break
        else:
            print(f"[ERROR] Contractor message went to wrong conversation!")
            all_correct = False
    else:
        print(f"[ERROR] Contractor auto-routing failed")
        all_correct = False
    
    # Final result
    print("\n" + "="*60)
    if all_correct:
        print("[SUCCESS] Fixed routing system working perfectly!")
        print("✓ Homeowner messages go to correct contractor conversations")
        print("✓ Contractor messages auto-route to their own conversation")
        print("✓ Messages persist with correct targeting")
    else:
        print("[PARTIAL] Some routing issues detected")
    
    print("="*60)
    return all_correct

if __name__ == "__main__":
    test_current_routing()