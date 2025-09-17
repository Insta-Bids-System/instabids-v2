"""
Quick test of CIA potential bid card creation
"""
import requests
import json
import uuid
import sys
import io

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8008"

def test_cia_quick():
    """Quick test with minimal timeout"""
    
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    
    print(f"Testing CIA with session: {session_id}")
    
    request_data = {
        "messages": [{"role": "user", "content": "I need deck repair in 10001"}],
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": session_id
    }
    
    print("Sending to CIA (10s timeout)...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/cia/stream",
            json=request_data,
            timeout=10,
            stream=True
        )
        
        if response.status_code == 200:
            print("✓ CIA responded (streaming)")
            
            # Check if bid card was created after conversation
            print("Checking for potential bid card...")
            bid_card_response = requests.get(
                f"{BASE_URL}/api/cia/conversation/{session_id}/potential-bid-card"
            )
            
            if bid_card_response.status_code == 200:
                print("✓ POTENTIAL BID CARD CREATED!")
                data = bid_card_response.json()
                print(f"  ID: {data.get('id')}")
                print(f"  Completion: {data.get('completion_percentage')}%")
                return True
            else:
                print(f"✗ No bid card found: {bid_card_response.status_code}")
                
                # Check if any bid cards exist
                list_response = requests.get(f"{BASE_URL}/api/cia/potential-bid-cards")
                if list_response.status_code == 200:
                    cards = list_response.json()
                    print(f"  Total cards in system: {len(cards) if isinstance(cards, list) else 'unknown'}")
                    
        else:
            print(f"✗ CIA failed: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("✗ Request timed out")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    return False

if __name__ == "__main__":
    success = test_cia_quick()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'} - CIA {'creates' if success else 'does not create'} potential bid cards")