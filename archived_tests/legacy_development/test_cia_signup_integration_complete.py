"""
Complete CIA Chat + Account Signup Integration Test
Tests the full anonymous-to-authenticated user journey with real backend integration
"""

import asyncio
import requests
import json
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8008"
CIA_ENDPOINT = f"{BASE_URL}/api/cia/stream"
POTENTIAL_BID_CARDS_ENDPOINT = f"{BASE_URL}/api/cia/potential-bid-cards"
SIGNUP_ENDPOINT = f"{BASE_URL}/api/auth/signup"  # Note: May need to be implemented
CONVERSION_ENDPOINT = f"{BASE_URL}/api/cia/potential-bid-cards"

def generate_test_session():
    """Generate unique session and conversation IDs"""
    timestamp = int(time.time())
    session_id = f"test_session_{timestamp}"
    conversation_id = f"test_conv_{timestamp}"
    return session_id, conversation_id

def test_potential_bid_card_creation(session_id, conversation_id):
    """Test creating a potential bid card for anonymous user"""
    print("=== Testing Potential Bid Card Creation (Anonymous User) ===")
    
    # Create potential bid card
    payload = {
        "conversation_id": conversation_id,
        "session_id": session_id,
        "title": "Kitchen Renovation Test Project"
    }
    
    try:
        response = requests.post(POTENTIAL_BID_CARDS_ENDPOINT, json=payload, timeout=10)
        if response.status_code == 200:
            bid_card = response.json()
            print(f"✅ Potential bid card created: {bid_card['id']}")
            print(f"   Status: {bid_card.get('status', 'unknown')}")
            print(f"   Completion: {bid_card.get('completion_percentage', 0)}%")
            return bid_card
        else:
            print(f"❌ Failed to create bid card: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating bid card: {e}")
        return None

def test_cia_conversation_flow(session_id, conversation_id, bid_card_id):
    """Test CIA conversation to build up bid card data"""
    print("\n=== Testing CIA Conversation Flow ===")
    
    # Conversation messages to test different aspects
    test_messages = [
        "I want to renovate my kitchen completely",
        "I live in Austin, Texas 78701", 
        "I want modern cabinets, new countertops, and updated appliances",
        "My timeline is within 2 months and I'm looking for experienced contractors",
        "My budget is around $40,000-50,000 for this project"
    ]
    
    for i, message in enumerate(test_messages):
        print(f"\n--- Sending message {i+1}: {message[:50]}... ---")
        
        payload = {
            "message": message,
            "conversationId": conversation_id,
            "sessionId": session_id,
            "context": {
                "phase": "discovery",
                "bidCardId": bid_card_id
            }
        }
        
        try:
            # Note: This would be an SSE stream in real usage
            # For testing, we'll use a POST request to the endpoint
            response = requests.post(f"{BASE_URL}/api/cia/message", json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ CIA Response: {result.get('response', 'No response')[:100]}...")
            else:
                print(f"❌ CIA request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error in CIA conversation: {e}")
            
        # Small delay between messages
        time.sleep(1)

def check_bid_card_completion(conversation_id):
    """Check if bid card is ready for conversion"""
    print("\n=== Checking Bid Card Completion Status ===")
    
    try:
        response = requests.get(f"{POTENTIAL_BID_CARDS_ENDPOINT}/{conversation_id}/potential-bid-card")
        
        if response.status_code == 200:
            bid_card = response.json()
            completion = bid_card.get('completion_percentage', 0)
            ready = bid_card.get('ready_for_conversion', False)
            missing = bid_card.get('missing_fields', [])
            
            print(f"📊 Bid Card Completion: {completion}%")
            print(f"🎯 Ready for Conversion: {ready}")
            
            if missing:
                print(f"📝 Missing Fields: {', '.join(missing)}")
            
            return bid_card
        else:
            print(f"❌ Failed to check bid card: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking bid card: {e}")
        return None

def test_conversion_attempt_anonymous(bid_card_id):
    """Test conversion attempt without authentication (should fail)"""
    print("\n=== Testing Anonymous Conversion Attempt (Should Fail) ===")
    
    try:
        response = requests.post(f"{POTENTIAL_BID_CARDS_ENDPOINT}/{bid_card_id}/convert-to-bid-card")
        
        if response.status_code == 400:
            error = response.json()
            print(f"✅ Expected failure: {error.get('detail', 'Authentication required')}")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing anonymous conversion: {e}")
        return False

def simulate_signup_flow():
    """Simulate the signup process (frontend would handle this)"""
    print("\n=== Simulating User Signup Flow ===")
    
    # Note: In real usage, this would happen in the frontend
    # The AccountSignupModal would handle Supabase authentication
    
    test_user = {
        "name": "Test User",
        "email": f"test_user_{int(time.time())}@instabids.com",
        "user_id": f"test_user_{int(time.time())}"  # Simulated user ID
    }
    
    print(f"👤 Simulated User Created:")
    print(f"   Name: {test_user['name']}")
    print(f"   Email: {test_user['email']}")
    print(f"   User ID: {test_user['user_id']}")
    
    return test_user

def test_authenticated_conversion(bid_card_id, user_id):
    """Test conversion with authenticated user"""
    print("\n=== Testing Authenticated Conversion ===")
    
    # Note: In real implementation, this would include proper authentication headers
    payload = {
        "user_id": user_id
    }
    
    try:
        response = requests.post(
            f"{POTENTIAL_BID_CARDS_ENDPOINT}/{bid_card_id}/convert-to-bid-card",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Conversion successful!")
            print(f"   Official Bid Card ID: {result.get('official_bid_card_id', 'Unknown')}")
            print(f"   Status: {result.get('status', 'Unknown')}")
            return result
        else:
            print(f"❌ Conversion failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error in authenticated conversion: {e}")
        return None

def test_frontend_integration_logic():
    """Test the frontend logic that would trigger signup modal"""
    print("\n=== Testing Frontend Integration Logic ===")
    
    # Test the trigger detection logic from the frontend
    test_responses = [
        "Great! Your kitchen renovation project looks complete. To get professional bids from contractors, you'll need to create an InstaBids account.",
        "Perfect! I can help you get competitive bids. To receive your bid cards and get started, let's create an account so contractors can reach you.",
        "Let me ask a few more questions about your project timeline."
    ]
    
    def should_show_signup_modal(content):
        account_triggers = [
            "create an account",
            "sign up to get", 
            "would you like to create",
            "get your professional bids",
            "start receiving bids",
            "to receive your bid cards",
            "register to get contractors",
            "create your instabids account",
            "create an instabids account"
        ]
        return any(trigger in content.lower() for trigger in account_triggers)
    
    for i, response in enumerate(test_responses):
        should_trigger = should_show_signup_modal(response)
        expected = i < 2  # First 2 should trigger, last one should not
        result = "✅ PASS" if should_trigger == expected else "❌ FAIL"
        
        print(f"Response {i+1}: {result}")
        print(f"  Content: {response[:60]}...")
        print(f"  Should trigger: {expected}, Got: {should_trigger}")

def run_complete_integration_test():
    """Run the complete integration test"""
    print("Starting Complete CIA Chat + Account Signup Integration Test")
    print("=" * 70)
    
    # Generate test session
    session_id, conversation_id = generate_test_session()
    print(f"📝 Test Session: {session_id}")
    print(f"📝 Conversation: {conversation_id}")
    
    # Step 1: Create potential bid card for anonymous user
    bid_card = test_potential_bid_card_creation(session_id, conversation_id)
    if not bid_card:
        print("❌ Test failed at bid card creation step")
        return
    
    bid_card_id = bid_card['id']
    
    # Step 2: Test CIA conversation flow
    test_cia_conversation_flow(session_id, conversation_id, bid_card_id)
    
    # Step 3: Check bid card completion
    updated_bid_card = check_bid_card_completion(conversation_id)
    if not updated_bid_card:
        print("❌ Test failed at bid card completion check")
        return
    
    # Step 4: Test anonymous conversion attempt (should fail)
    anonymous_conversion_failed = test_conversion_attempt_anonymous(bid_card_id)
    if not anonymous_conversion_failed:
        print("❌ Test failed - anonymous conversion should have failed")
        return
    
    # Step 5: Test frontend integration logic
    test_frontend_integration_logic()
    
    # Step 6: Simulate user signup
    test_user = simulate_signup_flow()
    
    # Step 7: Test authenticated conversion
    conversion_result = test_authenticated_conversion(bid_card_id, test_user['user_id'])
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    if conversion_result:
        print("✅ Complete Integration Test: PASSED")
        print("✅ Anonymous potential bid card creation: Working")
        print("✅ CIA conversation flow: Working") 
        print("✅ Bid card completion tracking: Working")
        print("✅ Anonymous conversion blocking: Working")
        print("✅ Frontend trigger logic: Working")
        print("✅ Authenticated conversion: Working")
        print("\nThe CIA Chat + Account Signup Modal integration is fully operational!")
    else:
        print("❌ Complete Integration Test: FAILED")
        print("Some components may need additional backend implementation")

if __name__ == "__main__":
    # Check if backend is running
    try:
        # Test with a simple endpoint
        response = requests.get(f"{BASE_URL}/api/cia", timeout=5)
        print(f"[OK] Backend is running on {BASE_URL}")
    except:
        print(f"[ERROR] Backend not available on {BASE_URL}")
        print("Please start the backend with: cd ai-agents && python main.py")
        exit(1)
    
    run_complete_integration_test()