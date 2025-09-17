"""
Test Complete CIA Flow with Proper UUIDs
Verify conversation → potential bid card → signup trigger → memory persistence
"""
import requests
import json
import time
import uuid
import sys
import io

# Set UTF-8 encoding for output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8008"

def test_cia_conversation_with_uuid():
    """Test CIA conversation with proper UUID format"""
    
    # Generate proper UUIDs
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"  # Anonymous user
    
    print("=" * 60)
    print("TESTING CIA CONVERSATION WITH PROPER UUID")
    print("=" * 60)
    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id} (anonymous)")
    
    # Multiple conversation turns
    conversation_turns = [
        "My deck is falling apart and needs to be rebuilt. It's about 12x16 feet in Manhattan, NY 10001",
        "I need it done within the next month, it's getting unsafe. The wood is rotting.",
        "I'd prefer a mid-range quality, nothing too fancy but professional work",
        "Yes, I can take some photos of the current deck damage. How do I share them?"
    ]
    
    for i, user_message in enumerate(conversation_turns, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {user_message}")
        
        request_data = {
            "messages": [{"role": "user", "content": user_message}],
            "user_id": user_id,
            "session_id": session_id,
            "conversation_id": session_id,
            "project_context": {}
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/cia/stream",
                json=request_data,
                timeout=30,
                stream=True
            )
            
            if response.status_code == 200:
                full_response = ""
                chunk_count = 0
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                if data.get('content'):
                                    full_response += data['content']
                                    chunk_count += 1
                            except:
                                continue
                
                print(f"CIA Response ({chunk_count} chunks):")
                print(full_response[:300] + "..." if len(full_response) > 300 else full_response)
                
                # Check for signup triggers
                signup_triggers = [
                    "create an account",
                    "sign up",
                    "register",
                    "create your InstaBids account"
                ]
                
                for trigger in signup_triggers:
                    if trigger.lower() in full_response.lower():
                        print(f"\n>>> SIGNUP TRIGGER DETECTED: '{trigger}'")
                        break
                        
            else:
                print(f"Request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error in turn {i}: {e}")
            return None
            
        time.sleep(2)  # Pause between turns
    
    return session_id

def check_potential_bid_card(session_id):
    """Check if potential bid card was created"""
    
    print("\n" + "=" * 60)
    print("CHECKING POTENTIAL BID CARD")
    print("=" * 60)
    
    try:
        # First check via conversation endpoint
        response = requests.get(f"{BASE_URL}/api/cia/conversation/{session_id}/potential-bid-card")
        
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Potential bid card found!")
            print(f"  Bid Card ID: {data.get('id')}")
            print(f"  Completion: {data.get('completion_percentage', 0)}%")
            print(f"  Ready for conversion: {data.get('ready_for_conversion', False)}")
            
            fields = data.get('fields_collected', {})
            print(f"\nExtracted fields ({len(fields)} total):")
            for key, value in fields.items():
                if value:
                    print(f"  - {key}: {value}")
                    
            return data.get('id')
            
        elif response.status_code == 404:
            print("No potential bid card found")
            
            # Try alternate method - check potential_bid_cards table directly
            print("\nChecking via potential bid cards list...")
            list_response = requests.get(f"{BASE_URL}/api/cia/potential-bid-cards")
            
            if list_response.status_code == 200:
                bid_cards = list_response.json()
                print(f"Found {len(bid_cards)} total potential bid cards")
                
                # Look for our session
                for card in bid_cards:
                    if card.get('conversation_id') == session_id:
                        print(f"FOUND: Bid card for our session!")
                        return card.get('id')
                        
            return None
        else:
            print(f"Error checking bid card: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_signup_trigger_ui():
    """Explain what happens in UI when signup is triggered"""
    
    print("\n" + "=" * 60)
    print("SIGNUP FLOW IN UI")
    print("=" * 60)
    
    print("""
    When the CIA agent mentions "create an account" or similar phrases:
    
    1. AUTOMATIC MODAL: AccountSignupModal opens automatically
       - No button needed - triggered by AI response content
       - Modal appears over the chat interface
    
    2. SIGNUP FORM FIELDS:
       - Full Name (required)
       - Email (required)
       - Password (required)
       - ZIP code (pre-filled from conversation)
       - Phone (optional)
    
    3. AFTER SIGNUP:
       - User authentication via Supabase
       - Profile creation in database
       - Potential bid card converts to official bid card
       - Session memory links to new user account
       - Welcome message confirms account creation
    
    4. BUTTON TEXT: "Create Account & Get Bids"
       - Located at bottom of modal
       - Blue background with loading spinner when clicked
    
    5. SUCCESS FLOW:
       - Modal closes
       - Welcome message appears in chat
       - User can continue conversation as authenticated user
       - All previous context maintained
    """)

def main():
    """Run complete flow test"""
    
    print("COMPLETE CIA FLOW TEST")
    print("Testing: Conversation → Bid Card → Signup Trigger → Memory")
    
    # Test 1: Full conversation with proper UUIDs
    session_id = test_cia_conversation_with_uuid()
    
    if session_id:
        # Test 2: Check if potential bid card was created
        time.sleep(3)  # Allow processing time
        bid_card_id = check_potential_bid_card(session_id)
        
        # Test 3: Explain signup UI flow
        test_signup_trigger_ui()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Conversation: SUCCESS (Session: {session_id})")
        print(f"Potential Bid Card: {'SUCCESS' if bid_card_id else 'NOT FOUND'}")
        if bid_card_id:
            print(f"  Bid Card ID: {bid_card_id}")
        print("Signup Trigger: Check conversation for 'create account' phrases")
        print("\nNEXT STEPS:")
        print("1. Check UI at http://localhost:5173 to see signup modal")
        print("2. Fill form to test account creation")
        print("3. Verify bid card conversion after signup")
        print("4. Test returning user memory persistence")
    else:
        print("Conversation test failed - cannot continue")

if __name__ == "__main__":
    main()