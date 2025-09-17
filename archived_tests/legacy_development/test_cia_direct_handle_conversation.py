#!/usr/bin/env python3
"""
Test CIA handle_conversation method directly to debug bid card creation
"""
import asyncio
import requests
import json
import uuid
import sys
import io

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8008"

async def test_cia_handle_conversation():
    """Test the CIA agent's handle_conversation method directly"""
    
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    
    print("=" * 60)
    print("CIA HANDLE_CONVERSATION DIRECT TEST")
    print("=" * 60)
    print(f"Session ID: {session_id}")
    
    # Use the non-streaming endpoint that should call handle_conversation
    print("\n1. Calling CIA handle_conversation via non-streaming API...")
    
    request_data = {
        "messages": [{"role": "user", "content": "I need deck repair in Manhattan 10001, budget around $5000"}],
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": session_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/cia/chat",
            json=request_data,
            timeout=60  # Give it more time
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✓ CIA responded successfully")
            print(f"  Response: {data.get('response', '')[:100]}...")
            
            # Check potential bid card immediately after
            print("\n2. Checking for potential bid card...")
            bid_card_response = requests.get(
                f"{BASE_URL}/api/cia/conversation/{session_id}/potential-bid-card"
            )
            
            if bid_card_response.status_code == 200:
                bid_card_data = bid_card_response.json()
                print("✓ POTENTIAL BID CARD CREATED!")
                print(f"  ID: {bid_card_data.get('id')}")
                print(f"  Completion: {bid_card_data.get('completion_percentage')}%")
                print(f"  Fields: {list(bid_card_data.get('fields_collected', {}).keys())}")
                return True
            elif bid_card_response.status_code == 404:
                print("✗ No potential bid card found")
                print("  This means CIA handle_conversation was NOT called or failed")
                return False
            else:
                print(f"✗ Error checking bid card: {bid_card_response.status_code}")
                print(f"  Error: {bid_card_response.text}")
                return False
        else:
            print(f"✗ CIA request failed: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("Testing CIA handle_conversation method directly")
    print("This bypasses streaming to test the core logic")
    
    success = asyncio.run(test_cia_handle_conversation())
    
    print("\n" + "=" * 60)
    if success:
        print("✓ CIA HANDLE_CONVERSATION CREATES POTENTIAL BID CARDS")
        print("Integration is working correctly!")
    else:
        print("✗ CIA HANDLE_CONVERSATION NOT CREATING BID CARDS")
        print("Issue is in the core handle_conversation logic")

if __name__ == "__main__":
    main()