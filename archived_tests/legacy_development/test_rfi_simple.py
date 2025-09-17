#!/usr/bin/env python3
"""Simple test of RFI flow with CIA agent"""

import requests
import json
import time

def test_rfi_chat():
    """Test the regular chat endpoint with RFI context"""
    
    url = "http://localhost:8008/api/cia/chat"
    
    # Create request with RFI context
    payload = {
        "message": "I need to provide photos that were requested",
        "session_id": f"rfi_test_{int(time.time())}",
        "user_id": "550e8400-e29b-41d4-a716-446655440001",  # Demo homeowner
        "rfi_context": {
            "rfi_id": "test-rfi-123",
            "bid_card_id": "test-bid-card",
            "contractor_name": "ABC Landscaping",
            "request_type": "pictures",
            "specific_items": ["front yard", "sprinkler system", "lawn condition"],
            "priority": "high",
            "custom_message": "Please make sure the photos show the current condition clearly"
        }
    }
    
    print("Testing RFI flow with regular chat endpoint...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nSending request...")
    
    try:
        # Make request with shorter timeout
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("\nSuccess! Response received:")
            print("-" * 50)
            print(f"Response: {data.get('response', 'No response text')}")
            print(f"Session ID: {data.get('session_id')}")
            print(f"Current Phase: {data.get('current_phase')}")
            print("-" * 50)
            
            # Check if response acknowledges RFI context
            response_text = data.get('response', '').lower()
            rfi_keywords = ["photo", "picture", "contractor", "landscaping", "yard", "sprinkler", "abc"]
            acknowledged = any(keyword in response_text for keyword in rfi_keywords)
            
            if acknowledged:
                print("\nRFI context acknowledged in response!")
            else:
                print("\nWarning: RFI context may not have been acknowledged")
                
        else:
            print(f"\nRequest failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\nRequest timed out after 10 seconds")
        print("This likely means the CIA agent is having issues initializing.")
        print("Check that OpenAI API key is valid and accessible.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_rfi_chat()