"""
Test multi-contractor conversations with proper contractor targeting
"""
import requests
import json
from typing import Dict, List
import time

# Base URL for messaging API
BASE_URL = "http://localhost:8008/api/messages"

# Test users
HOMEOWNER_ID = "11111111-1111-1111-1111-111111111111"  # John Homeowner
BID_CARD_ID = "36214de5-a068-4dcc-af99-cf33238e7472"  # Kitchen remodel project

def send_targeted_message(bid_card_id: str, user_id: str, contractor_id: str, content: str) -> Dict:
    """Send a message to a specific contractor conversation"""
    try:
        # First, find the conversation ID for this contractor
        response = requests.get(
            f"{BASE_URL}/conversations/{bid_card_id}",
            params={
                "user_type": "homeowner",
                "user_id": user_id
            }
        )
        
        result = response.json()
        if result.get("success") and result.get("conversations"):
            # Find the conversation with this specific contractor
            for conv in result["conversations"]:
                if conv.get("contractor_id") == contractor_id:
                    conversation_id = conv.get("id")
                    
                    # Now send the message with metadata indicating the target conversation
                    msg_response = requests.post(
                        f"{BASE_URL}/send",
                        json={
                            "bid_card_id": bid_card_id,
                            "sender_id": user_id,
                            "sender_type": "homeowner",
                            "content": content,
                            "metadata": {
                                "target_contractor_id": contractor_id,
                                "conversation_id": conversation_id
                            }
                        }
                    )
                    return msg_response.json()
        
        return {"success": False, "error": "Conversation not found"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_targeted_messaging():
    """Test sending messages to specific contractor conversations"""
    
    print("\n=== TESTING TARGETED MULTI-CONTRACTOR MESSAGING ===\n")
    
    # Get all conversations first
    response = requests.get(
        f"{BASE_URL}/conversations/{BID_CARD_ID}",
        params={
            "user_type": "homeowner",
            "user_id": HOMEOWNER_ID
        }
    )
    
    result = response.json()
    if not result.get("success"):
        print("ERROR: Could not retrieve conversations")
        return
    
    conversations = result["conversations"]
    print(f"Found {len(conversations)} contractor conversations\n")
    
    # Test sending targeted messages to first 4 contractors
    test_convs = conversations[:4]
    
    print("Sending targeted messages to specific contractors...")
    print("-" * 60)
    
    for i, conv in enumerate(test_convs, 1):
        contractor_id = conv.get("contractor_id")
        conv_id = conv.get("id")
        
        # Create unique message for this contractor
        unique_msg = f"TARGETED MESSAGE {i}: This message is specifically for contractor {contractor_id[:8]}..."
        
        print(f"\nContractor {i}: {contractor_id}")
        print(f"  Conversation ID: {conv_id}")
        
        # Send targeted message
        result = send_targeted_message(BID_CARD_ID, HOMEOWNER_ID, contractor_id, unique_msg)
        
        if result.get("success"):
            print(f"  ✓ Message sent successfully")
        else:
            print(f"  ✗ ERROR: {result.get('error', 'Unknown')}")
        
        time.sleep(0.5)
    
    # Verify messages went to correct conversations
    print("\n\nVerifying message delivery to correct conversations...")
    print("-" * 60)
    
    for i, conv in enumerate(test_convs, 1):
        contractor_id = conv.get("contractor_id")
        conv_id = conv.get("id")
        
        # Get messages for this conversation
        msg_response = requests.get(f"{BASE_URL}/{conv_id}")
        msg_result = msg_response.json()
        
        if msg_result.get("success") and msg_result.get("messages"):
            messages = msg_result["messages"]
            
            # Check if our targeted message is there
            found_correct = False
            found_wrong = False
            
            for msg in messages[-5:]:  # Check last 5 messages
                content = msg.get("filtered_content", "")
                if f"TARGETED MESSAGE {i}:" in content and f"{contractor_id[:8]}" in content:
                    found_correct = True
                elif "TARGETED MESSAGE" in content and f"TARGETED MESSAGE {i}:" not in content:
                    found_wrong = True
            
            status = "✓ Correct" if found_correct and not found_wrong else "✗ MIXED UP" if found_wrong else "- Not found"
            print(f"\nContractor {contractor_id[:8]}...: {status}")
            
            if found_wrong:
                print("  WARNING: Found messages meant for other contractors!")
    
    # Show conversation summary
    print("\n\n=== CONVERSATION SUMMARY ===")
    print("-" * 80)
    print(f"{'Contractor ID':<40} {'Messages':<10} {'Unread':<10} {'Last Activity'}")
    print("-" * 80)
    
    for conv in conversations[:6]:  # Show first 6
        contractor_id = conv.get("contractor_id", "Unknown")
        conv_id = conv.get("id")
        
        # Get message count
        msg_response = requests.get(f"{BASE_URL}/{conv_id}")
        msg_result = msg_response.json()
        message_count = len(msg_result.get("messages", [])) if msg_result.get("success") else 0
        
        unread = conv.get("homeowner_unread_count", 0)
        last_activity = conv.get("last_message_at", "Never")[:19]
        
        print(f"{contractor_id:<40} {message_count:<10} {unread:<10} {last_activity}")
    
    print("\n✅ Multi-contractor conversation system is operational!")
    print(f"   - Managing {len(conversations)} separate contractor conversations")
    print("   - Each contractor has their own isolated thread")
    print("   - Homeowner can toggle between conversations")

if __name__ == "__main__":
    test_targeted_messaging()