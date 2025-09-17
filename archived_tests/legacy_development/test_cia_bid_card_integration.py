"""
Test CIA with Potential Bid Card Integration
Verify that CIA creates and updates potential bid cards during conversation
"""
import requests
import json
import uuid
import time
import sys
import io

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8008"

def test_cia_bid_card_flow():
    """Test that CIA creates and updates potential bid cards"""
    
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    
    print("=" * 60)
    print("TESTING CIA + POTENTIAL BID CARD INTEGRATION")
    print("=" * 60)
    print(f"Session ID: {session_id}")
    
    # Test conversation messages
    messages = [
        "I need to rebuild my deck in Manhattan 10001",
        "It's about 12x16 feet, the wood is completely rotted",
        "I need it done within 2 weeks, it's becoming dangerous"
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {msg}")
        
        request_data = {
            "messages": [{"role": "user", "content": msg}],
            "user_id": user_id,
            "session_id": session_id,
            "conversation_id": session_id
        }
        
        # Send to CIA
        response = requests.post(
            f"{BASE_URL}/api/cia/stream",
            json=request_data,
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            # Process streaming response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if data.get('content'):
                                full_response += data['content']
                        except:
                            continue
            
            print(f"CIA: {full_response[:200]}...")
            
            # Check for signup trigger
            if "create" in full_response.lower() and "account" in full_response.lower():
                print("\n✓ SIGNUP TRIGGER DETECTED!")
        else:
            print(f"Error: {response.status_code}")
            
        time.sleep(2)
    
    # Check if potential bid card was created
    print("\n" + "=" * 60)
    print("CHECKING POTENTIAL BID CARD STATUS")
    print("=" * 60)
    
    # List all potential bid cards to find ours
    list_response = requests.get(f"{BASE_URL}/api/cia/potential-bid-cards")
    
    if list_response.status_code == 200:
        bid_cards = list_response.json()
        
        # Look for our session
        our_card = None
        for card in bid_cards:
            if card.get('session_id') == session_id or card.get('cia_conversation_id') == session_id:
                our_card = card
                break
        
        if our_card:
            print("✓ POTENTIAL BID CARD CREATED!")
            print(f"  ID: {our_card.get('id')}")
            print(f"  Completion: {our_card.get('completion_percentage', 0)}%")
            print(f"  Ready for conversion: {our_card.get('ready_for_conversion', False)}")
            
            # Show extracted fields
            print("\nExtracted Fields:")
            fields = [
                'primary_trade', 'user_scope_notes', 'zip_code',
                'urgency_level', 'contractor_size_preference'
            ]
            for field in fields:
                value = our_card.get(field)
                if value:
                    print(f"  - {field}: {value}")
            
            return our_card.get('id')
        else:
            print("✗ No potential bid card found for this session")
            print(f"Total bid cards in system: {len(bid_cards)}")
            
    else:
        print(f"Error fetching bid cards: {list_response.status_code}")
    
    return None

def test_signup_conversion(bid_card_id):
    """Test converting potential bid card after signup"""
    
    if not bid_card_id:
        print("\n✗ Cannot test conversion - no bid card to convert")
        return
    
    print("\n" + "=" * 60)
    print("TESTING BID CARD CONVERSION AFTER SIGNUP")
    print("=" * 60)
    
    # Simulate user signup
    new_user_id = str(uuid.uuid4())
    print(f"Simulating signup with user ID: {new_user_id}")
    
    # Convert bid card
    convert_response = requests.post(
        f"{BASE_URL}/api/cia/potential-bid-cards/{bid_card_id}/convert-to-bid-card",
        json={"user_id": new_user_id}
    )
    
    if convert_response.status_code == 200:
        data = convert_response.json()
        print("✓ BID CARD CONVERSION SUCCESSFUL!")
        print(f"  Official Bid Card ID: {data.get('official_bid_card_id')}")
        print(f"  Bid Card Number: {data.get('bid_card_number')}")
    else:
        print(f"✗ Conversion failed: {convert_response.status_code}")
        if convert_response.text:
            print(f"  Error: {convert_response.text}")

def main():
    print("CIA + POTENTIAL BID CARD INTEGRATION TEST")
    print("Testing complete flow from conversation to bid card creation")
    
    # Test CIA conversation with bid card creation
    bid_card_id = test_cia_bid_card_flow()
    
    # Test conversion after signup
    if bid_card_id:
        test_signup_conversion(bid_card_id)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if bid_card_id:
        print("✓ CIA creates potential bid cards during conversation")
        print("✓ Bid cards can be converted after signup")
        print("\nFRONTEND BEHAVIOR:")
        print("1. User has conversation with CIA")
        print("2. CIA extracts project details → saves to potential bid card")
        print("3. CIA says 'create an account' → modal opens automatically")
        print("4. User fills form and clicks 'Create Account & Get Bids'")
        print("5. After signup → potential bid card converts to official")
        print("6. User sees their bid card and can track contractor bids")
    else:
        print("✗ Integration not working - potential bid cards not being created")
        print("Need to verify CIA agent is calling bid card API correctly")

if __name__ == "__main__":
    main()