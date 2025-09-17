#!/usr/bin/env python3
"""Complete messaging API test"""

import requests
import json
import time

API_BASE = "http://localhost:8008/api/messages"

def test_health():
    """Test health endpoint"""
    print("=== TESTING HEALTH ENDPOINT ===")
    response = requests.get(f"{API_BASE}/health", timeout=10)
    print(f"Health Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_send_message():
    """Test sending a message with content filtering"""
    print("\n=== TESTING MESSAGE SENDING ===")
    
    message_data = {
        "content": "Hi, I'm interested in your project. Call me at 555-123-4567 or email john@test.com",
        "sender_type": "contractor",
        "sender_id": "test-contractor-123",
        "bid_card_id": "test-bid-card-456",
        "message_type": "text"
    }
    
    print(f"Sending message: {message_data['content']}")
    
    try:
        response = requests.post(
            f"{API_BASE}/send",
            json=message_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Message ID: {result['id']}")
            print(f"Filtered Content: {result['filtered_content']}")
            print(f"Content Filtered: {result['content_filtered']}")
            print(f"Filter Reasons: {len(result['filter_reasons'])} filters applied")
            
            # Verify filtering worked
            success = (
                "[CONTACT REMOVED]" in result["filtered_content"] and
                result["content_filtered"] and
                len(result["filter_reasons"]) >= 2
            )
            print(f"Filtering Test: {'PASSED' if success else 'FAILED'}")
            return success
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Request failed: {e}")
        return False

def test_broadcast_message():
    """Test broadcast message sending"""
    print("\n=== TESTING BROADCAST MESSAGE ===")
    
    broadcast_data = {
        "content": "Project update: Timeline changed. Contact me at 555-987-6543 for details.",
        "sender_type": "homeowner",
        "sender_id": "test-homeowner-789",
        "bid_card_id": "test-bid-card-456",
        "recipient_type": "all_contractors"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/broadcast",
            json=broadcast_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"Broadcast Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Broadcast ID: {result['broadcast_id']}")
            print(f"Filtered Content: {result['filtered_content']}")
            print(f"Content Filtered: {result['content_filtered']}")
            
            success = "[CONTACT REMOVED]" in result["filtered_content"]
            print(f"Broadcast Filtering: {'PASSED' if success else 'FAILED'}")
            return success
        else:
            print(f"Broadcast Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Broadcast Request failed: {e}")
        return False

def run_all_tests():
    """Run complete API test suite"""
    print("=== MESSAGING API COMPLETE TEST SUITE ===")
    
    results = []
    
    # Test health
    results.append(test_health())
    
    # Test message sending
    results.append(test_send_message())
    
    # Test broadcast
    results.append(test_broadcast_message())
    
    # Overall results
    passed = sum(results)
    total = len(results)
    
    print(f"\n=== TEST RESULTS ===")
    print(f"Passed: {passed}/{total}")
    print(f"Overall: {'PASSED' if passed == total else 'FAILED'}")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        print(f"\n=== FINAL RESULT: {'ALL TESTS PASSED' if success else 'SOME TESTS FAILED'} ===")
    except Exception as e:
        print(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()