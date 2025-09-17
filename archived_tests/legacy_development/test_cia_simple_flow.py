"""
Test CIA with potential bid card creation - non-streaming simple test
"""
import requests
import json
import uuid
import sys
import io

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8008"

def test_cia_simple():
    """Test CIA creating bid cards without streaming complexity"""
    
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    
    print("=" * 60)
    print("CIA SIMPLE BID CARD TEST")
    print("=" * 60)
    print(f"Session ID: {session_id}")
    
    # Step 1: Send message to CIA (non-streaming)
    print("\n1. Sending message to CIA...")
    request_data = {
        "messages": [{"role": "user", "content": "I need to rebuild my deck in Manhattan 10001, it's about 12x16 feet"}],
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": session_id
    }
    
    # Try the non-streaming chat endpoint
    response = requests.post(
        f"{BASE_URL}/api/cia/chat",
        json=request_data,
        timeout=60  # Give it more time
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✓ CIA responded successfully")
        print(f"  Response: {data.get('response', '')[:100]}...")
        
        # Step 2: Check if potential bid card was created
        print("\n2. Checking for potential bid card...")
        
        # Get bid card by conversation ID
        bid_card_response = requests.get(
            f"{BASE_URL}/api/cia/conversation/{session_id}/potential-bid-card"
        )
        
        if bid_card_response.status_code == 200:
            bid_card_data = bid_card_response.json()
            print("✓ POTENTIAL BID CARD CREATED!")
            print(f"  ID: {bid_card_data.get('id')}")
            print(f"  Completion: {bid_card_data.get('completion_percentage')}%")
            print(f"  Fields collected: {list(bid_card_data.get('fields_collected', {}).keys())}")
            return True
        elif bid_card_response.status_code == 404:
            print("✗ No potential bid card found")
            
            # Try listing all bid cards to debug
            list_response = requests.get(f"{BASE_URL}/api/cia/potential-bid-cards")
            if list_response.status_code == 200:
                all_cards = list_response.json()
                print(f"  Total bid cards in system: {len(all_cards) if isinstance(all_cards, list) else 'unknown'}")
        else:
            print(f"✗ Error checking bid card: {bid_card_response.status_code}")
            
    else:
        print(f"✗ CIA request failed: {response.status_code}")
        if response.text:
            print(f"  Error: {response.text[:200]}")
    
    return False

def main():
    print("Testing CIA integration with potential bid cards")
    print("This uses the non-streaming endpoint for simplicity")
    
    success = test_cia_simple()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ CIA CREATES POTENTIAL BID CARDS")
        print("Integration is working correctly!")
    else:
        print("✗ CIA NOT CREATING BID CARDS")
        print("Integration needs debugging")

if __name__ == "__main__":
    main()