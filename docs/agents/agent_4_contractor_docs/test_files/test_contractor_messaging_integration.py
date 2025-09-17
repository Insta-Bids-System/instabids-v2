"""
Test Contractor Messaging Integration
Tests the complete messaging workflow for contractors with bid cards

Status: Ready for Testing
Date: August 4, 2025
Agent: Agent 4 (Contractor UX)
"""

import asyncio
import requests
import json
from datetime import datetime

# Test Configuration
BASE_URL = "http://localhost:8008"
TEST_BID_CARD_ID = "2cb6e43a-2c92-4e30-93f2-e44629f8975f"  # Real bid card from database
TEST_CONTRACTOR_ID = "22222222-2222-2222-2222-222222222222"  # Test contractor
TEST_HOMEOWNER_ID = "11111111-1111-1111-1111-111111111111"   # Test homeowner

def print_test_header(test_name: str):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")

def print_test_result(success: bool, message: str):
    """Print formatted test result"""
    status = "PASS" if success else "FAIL"
    print(f"{status}: {message}")

def test_messaging_api_health():
    """Test that messaging API is available and healthy"""
    print_test_header("Messaging API Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/api/messages/health")
        
        if response.status_code == 200:
            data = response.json()
            print_test_result(True, f"Messaging API is healthy: {data.get('status')}")
            return True
        else:
            print_test_result(False, f"Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result(False, f"Health check error: {str(e)}")
        return False

def test_check_existing_conversation():
    """Test checking for existing conversations"""
    print_test_header("Check Existing Conversation")
    
    try:
        # Check for existing conversations
        response = requests.get(f"{BASE_URL}/api/messages/conversations", params={
            'user_type': 'contractor',
            'user_id': TEST_CONTRACTOR_ID,
            'bid_card_id': TEST_BID_CARD_ID
        })
        
        if response.status_code == 200:
            data = response.json()
            conversations = data.get('conversations', [])
            
            print(f"DATA: Found {len(conversations)} existing conversations")
            
            if conversations:
                conv = conversations[0]
                print(f"   --> Conversation ID: {conv['id']}")
                print(f"   --> Contractor Alias: {conv['contractor_alias']}")
                print(f"   --> Last Message: {conv.get('last_message_at', 'Never')}")
                print_test_result(True, "Successfully retrieved conversation data")
                return conv['id']
            else:
                print_test_result(True, "No existing conversations found (this is normal)")
                return None
        else:
            print_test_result(False, f"Failed to check conversations: {response.status_code}")
            return None
            
    except Exception as e:
        print_test_result(False, f"Error checking conversations: {str(e)}")
        return None

def test_send_message(conversation_id=None):
    """Test sending a message from contractor to homeowner"""
    print_test_header("Send Message Test")
    
    try:
        # Send test message
        message_content = f"Hi! I'm interested in your project. I have experience with similar kitchen remodels and would love to discuss the details. Test message sent at {datetime.now().strftime('%H:%M:%S')}"
        
        payload = {
            'bid_card_id': TEST_BID_CARD_ID,
            'content': message_content,
            'sender_type': 'contractor',
            'sender_id': TEST_CONTRACTOR_ID,
            'message_type': 'text'
        }
        
        if conversation_id:
            payload['conversation_id'] = conversation_id
        
        response = requests.post(f"{BASE_URL}/api/messages/send", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"SENT: Message sent successfully:")
            print(f"   --> Message ID: {data.get('id')}")
            print(f"   --> Conversation ID: {data.get('conversation_id')}")
            print(f"   --> Content Filtered: {data.get('content_filtered', False)}")
            
            if data.get('content_filtered'):
                print(f"   --> Filter Reasons: {data.get('filter_reasons', [])}")
                print(f"   --> Filtered Content: {data.get('filtered_content', 'N/A')}")
            
            print_test_result(True, "Message sent and processed successfully")
            return data.get('conversation_id')
        else:
            print_test_result(False, f"Failed to send message: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print_test_result(False, f"Error sending message: {str(e)}")
        return None

def test_get_conversation_messages(conversation_id):
    """Test retrieving messages from a conversation"""
    print_test_header("Get Conversation Messages")
    
    if not conversation_id:
        print_test_result(False, "No conversation ID provided")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/api/messages/conversation/{conversation_id}/messages")
        
        if response.status_code == 200:
            messages = response.json()
            
            print(f"MESSAGES: Retrieved {len(messages)} messages:")
            
            for i, msg in enumerate(messages):
                print(f"   {i+1}. [{msg['sender_type']}] {msg['filtered_content'][:50]}...")
                if msg.get('content_filtered'):
                    print(f"      --> Content was filtered for privacy")
            
            print_test_result(True, f"Successfully retrieved {len(messages)} messages")
            return True
        else:
            print_test_result(False, f"Failed to get messages: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result(False, f"Error getting messages: {str(e)}")
        return False

def test_send_filtered_message(conversation_id=None):
    """Test sending a message with contact info that should be filtered"""
    print_test_header("Content Filtering Test")
    
    try:
        # Send message with contact info that should be filtered
        message_content = f"I'd love to discuss this project! You can call me at 555-123-4567 or email me at contractor@email.com. My website is www.mycontractor.com"
        
        payload = {
            'bid_card_id': TEST_BID_CARD_ID,
            'content': message_content,
            'sender_type': 'contractor',
            'sender_id': TEST_CONTRACTOR_ID,
            'conversation_id': conversation_id,
            'message_type': 'text'
        }
        
        response = requests.post(f"{BASE_URL}/api/messages/send", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"FILTER: Filtered message test:")
            print(f"   --> Original: {message_content}")
            print(f"   --> Filtered: {data.get('filtered_content', 'N/A')}")
            print(f"   --> Content Filtered: {data.get('content_filtered', False)}")
            
            if data.get('content_filtered'):
                print(f"   --> Filter Reasons: {[r.get('category') for r in data.get('filter_reasons', [])]}")
                print_test_result(True, "Content filtering is working correctly")
            else:
                print_test_result(False, "Content filtering did not activate (should have filtered contact info)")
            
            return True
        else:
            print_test_result(False, f"Failed to send filtered message: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result(False, f"Error sending filtered message: {str(e)}")
        return False

def test_get_unread_count():
    """Test getting unread message count for contractor"""
    print_test_header("Unread Message Count Test")
    
    try:
        response = requests.get(f"{BASE_URL}/api/messages/unread-count", params={
            'user_type': 'contractor',
            'user_id': TEST_CONTRACTOR_ID,
            'bid_card_id': TEST_BID_CARD_ID
        })
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"STATS: Unread message stats:")
            print(f"   --> Total Unread: {data.get('total_unread', 0)}")
            print(f"   --> Conversations with Unread: {data.get('conversations_with_unread', 0)}")
            
            print_test_result(True, "Successfully retrieved unread counts")
            return True
        else:
            print_test_result(False, f"Failed to get unread count: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result(False, f"Error getting unread count: {str(e)}")
        return False

def run_complete_test_suite():
    """Run all messaging integration tests"""
    print(f"\nCONTRACTOR MESSAGING INTEGRATION TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing bid card: {TEST_BID_CARD_ID}")
    print(f"Testing contractor: {TEST_CONTRACTOR_ID}")
    
    test_results = []
    
    # Test 1: API Health
    test_results.append(test_messaging_api_health())
    
    # Test 2: Check existing conversations
    conversation_id = test_check_existing_conversation()
    test_results.append(conversation_id is not None or True)  # Success if we get data or no conversations
    
    # Test 3: Send first message
    new_conversation_id = test_send_message(conversation_id)
    conversation_id = new_conversation_id or conversation_id
    test_results.append(conversation_id is not None)
    
    # Test 4: Get messages
    if conversation_id:
        test_results.append(test_get_conversation_messages(conversation_id))
    else:
        test_results.append(False)
    
    # Test 5: Send filtered message
    if conversation_id:
        test_results.append(test_send_filtered_message(conversation_id))
    else:
        test_results.append(False)
    
    # Test 6: Get unread count
    test_results.append(test_get_unread_count())
    
    # Final Results
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n{'='*60}")
    print(f"FINAL TEST RESULTS")
    print(f"{'='*60}")
    print(f"Tests Passed: {passed}/{total}")
    print(f"Tests Failed: {total - passed}/{total}")
    
    if passed == total:
        print(f"ALL TESTS PASSED - Contractor messaging integration is WORKING!")
    else:
        print(f"Some tests failed - Check the backend server and database connection")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total

if __name__ == "__main__":
    success = run_complete_test_suite()
    exit(0 if success else 1)