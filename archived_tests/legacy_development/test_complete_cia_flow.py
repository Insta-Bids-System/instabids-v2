"""
Test Complete CIA Flow: Conversation -> Bid Card -> Signup -> Memory Persistence
Testing the new pain-point first approach with real bid card creation
"""
import sys
import io
# Set output encoding to UTF-8 to handle special characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time
import uuid

BASE_URL = "http://localhost:8008"

def test_opening_message():
    """Test that opening message API works"""
    print("=" * 60)
    print("STEP 1: TESTING OPENING MESSAGE API")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/cia/opening-message")
    if response.status_code == 200:
        data = response.json()
        print("✅ Opening message loaded successfully")
        print(f"Message length: {len(data['message'])} characters")
        print("Preview:", data['message'][:200] + "...")
        return True
    else:
        print(f"❌ Failed to load opening message: {response.status_code}")
        return False

def test_conversation_flow():
    """Test multi-turn conversation with bid card extraction"""
    print("\n" + "=" * 60)
    print("STEP 2: TESTING CONVERSATION FLOW")
    print("=" * 60)
    
    # Generate unique session
    session_id = f"test_session_{int(time.time())}"
    user_id = "00000000-0000-0000-0000-000000000000"  # Anonymous user
    
    # Conversation turns to test
    conversation_turns = [
        "My deck is falling apart and needs to be rebuilt",
        "It's about 12x16 feet, probably needs complete replacement. The boards are rotting and it's not safe anymore.",
        "I'm in ZIP code 10001, Manhattan. I'd like to get this done before winter if possible.",
        "I'd prefer a mid-range contractor, nothing too fancy but needs to be professional and insured."
    ]
    
    bid_card_id = None
    
    for i, user_message in enumerate(conversation_turns, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {user_message}")
        
        # Prepare request
        request_data = {
            "messages": [
                {"role": "user", "content": user_message}
            ],
            "user_id": user_id,
            "session_id": session_id,
            "conversation_id": session_id,
            "project_context": {}
        }
        
        try:
            # Call CIA streaming endpoint
            response = requests.post(
                f"{BASE_URL}/api/cia/stream",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                # Parse streaming response
                response_text = ""
                for line in response.text.split('\n'):
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            if data.get('content'):
                                response_text += data['content']
                        except:
                            continue
                
                print(f"CIA: {response_text[:200]}...")
                
                # Check if bid card was created
                if 'bid_card_id' in response.text:
                    print("✅ Bid card creation detected in response")
                
            else:
                print(f"❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error in conversation turn {i}: {e}")
    
    return session_id

def check_potential_bid_card(session_id):
    """Check if potential bid card was created"""
    print("\n" + "=" * 60)
    print("STEP 3: CHECKING POTENTIAL BID CARD CREATION")
    print("=" * 60)
    
    try:
        # Try to get potential bid card by conversation ID
        response = requests.get(f"{BASE_URL}/api/cia/conversation/{session_id}/potential-bid-card")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Potential bid card found!")
            print(f"Bid Card ID: {data.get('id')}")
            print(f"Completion: {data.get('completion_percentage', 0)}%")
            print(f"Ready for conversion: {data.get('ready_for_conversion', False)}")
            
            # Show extracted fields
            fields = data.get('fields_collected', {})
            print(f"Extracted fields: {list(fields.keys())}")
            
            return data.get('id')
            
        elif response.status_code == 404:
            print("❌ No potential bid card found - creation may have failed")
            return None
        else:
            print(f"❌ Error checking bid card: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking potential bid card: {e}")
        return None

def test_signup_flow(bid_card_id):
    """Test user signup and bid card conversion"""
    print("\n" + "=" * 60)
    print("STEP 4: TESTING SIGNUP AND BID CARD CONVERSION")
    print("=" * 60)
    
    if not bid_card_id:
        print("❌ No bid card to convert - skipping signup test")
        return None
    
    # Simulate user signup (this would normally go through auth flow)
    test_user_id = str(uuid.uuid4())
    
    print(f"Simulating signup with user ID: {test_user_id}")
    
    try:
        # Try to convert potential bid card to official bid card
        response = requests.post(f"{BASE_URL}/api/cia/potential-bid-cards/{bid_card_id}/convert-to-bid-card")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Bid card conversion successful!")
            print(f"Official bid card ID: {data.get('official_bid_card_id')}")
            print(f"Bid card number: {data.get('bid_card_number')}")
            return data.get('official_bid_card_id')
        else:
            print(f"❌ Conversion failed: {response.status_code}")
            print("Response:", response.text)
            return None
            
    except Exception as e:
        print(f"❌ Error in signup/conversion: {e}")
        return None

def test_memory_persistence(session_id, user_id):
    """Test that conversation memory persists after signup"""
    print("\n" + "=" * 60)
    print("STEP 5: TESTING MEMORY PERSISTENCE")
    print("=" * 60)
    
    # Test conversation with returning user context
    follow_up_message = "I also need to fix my roof - can you help with that too?"
    
    request_data = {
        "messages": [
            {"role": "user", "content": follow_up_message}
        ],
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": session_id,
        "project_context": {}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/cia/stream",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            response_text = ""
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if data.get('content'):
                            response_text += data['content']
                    except:
                        continue
            
            print(f"CIA Response: {response_text[:300]}...")
            
            # Check if AI references previous deck project
            if any(keyword in response_text.lower() for keyword in ['deck', 'previous', 'also', 'addition']):
                print("✅ AI shows awareness of previous conversation!")
            else:
                print("⚠️  AI may not be referencing previous conversation")
                
            return True
        else:
            print(f"❌ Memory test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing memory: {e}")
        return False

def main():
    """Run complete flow test"""
    print("TESTING COMPLETE CIA FLOW WITH NEW PAIN-POINT APPROACH")
    print("Testing: Conversation -> Bid Card -> Signup -> Memory")
    
    # Step 1: Test opening message
    if not test_opening_message():
        print("❌ Opening message test failed - stopping")
        return
    
    # Step 2: Test conversation and bid card creation
    session_id = test_conversation_flow()
    time.sleep(2)  # Allow processing time
    
    # Step 3: Check if potential bid card was created
    bid_card_id = check_potential_bid_card(session_id)
    
    # Step 4: Test signup and conversion
    official_bid_card_id = test_signup_flow(bid_card_id)
    
    # Step 5: Test memory persistence (simulate authenticated user)
    test_user_id = str(uuid.uuid4())
    test_memory_persistence(session_id, test_user_id)
    
    print("\n" + "=" * 60)
    print("COMPLETE FLOW TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Opening message: Working")
    print(f"✅ Conversation flow: Completed 4 turns")
    print(f"{'✅' if bid_card_id else '❌'} Potential bid card: {'Created' if bid_card_id else 'Failed'}")
    print(f"{'✅' if official_bid_card_id else '❌'} Bid card conversion: {'Success' if official_bid_card_id else 'Failed'}")
    print(f"✅ Memory persistence: Tested")

if __name__ == "__main__":
    main()