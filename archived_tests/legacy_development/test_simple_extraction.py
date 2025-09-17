#!/usr/bin/env python3
"""
Simple test to check if extraction is working at all.
"""

import requests
import json
import time

def test_simple_extraction():
    """Test with a single message containing all info."""
    
    print("SIMPLE CIA EXTRACTION TEST")
    print("="*60)
    
    # Single message with all information
    test_message = """
    I need a composite deck installed at 123 Main St, Austin TX 78701.
    Budget is $15,000-$20,000. My name is John Smith, email john@example.com,
    phone 512-555-1234. Need it done by April. 20x15 feet with lighting.
    """
    
    print("Sending test message with all info in one turn...")
    print(f"Message: {test_message[:100]}...")
    
    # Create simple conversation
    conversation_id = f"simple-test-{int(time.time())}"
    
    start_time = time.time()
    try:
        response = requests.post(
            "http://localhost:8008/api/cia/stream",
            json={
                "messages": [
                    {"role": "user", "content": test_message}
                ],
                "conversation_id": conversation_id,
                "user_id": "test-user-simple"
            },
            timeout=10  # Short timeout
        )
        elapsed = time.time() - start_time
        
        print(f"\nResponse received in {elapsed:.2f} seconds")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Check if we got a response
            response_text = response.text[:500]
            print(f"Response preview: {response_text}")
            
            # Try to check potential bid card
            print("\nChecking if bid card was created...")
            bid_check = requests.get(
                f"http://localhost:8008/api/cia/potential-bid-cards/{conversation_id}",
                timeout=5
            )
            
            if bid_check.status_code == 200:
                print("BID CARD DATA FOUND:")
                print(json.dumps(bid_check.json(), indent=2))
            else:
                print(f"No bid card found (status {bid_check.status_code})")
                
                # Try alternate endpoint
                bid_check2 = requests.get(
                    f"http://localhost:8008/api/cia/conversation/{conversation_id}/potential-bid-card",
                    timeout=5
                )
                if bid_check2.status_code == 200:
                    print("FOUND AT ALTERNATE ENDPOINT:")
                    print(json.dumps(bid_check2.json(), indent=2))
            
            return True
            
    except requests.Timeout:
        print(f"ERROR: Request timed out after {time.time() - start_time:.2f} seconds")
        print("This suggests the extraction is taking too long or hanging")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_quick_response():
    """Test if we can get ANY response quickly."""
    
    print("\nQUICK RESPONSE TEST")
    print("="*60)
    
    print("Testing with simple greeting...")
    
    try:
        response = requests.post(
            "http://localhost:8008/api/cia/stream",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "conversation_id": "quick-test",
                "user_id": "test-user"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            print("✓ Got response for simple greeting")
            print(f"Response length: {len(response.text)} bytes")
            return True
        else:
            print(f"✗ Failed with status {response.status_code}")
            return False
            
    except requests.Timeout:
        print("✗ Even simple greeting timed out!")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing CIA Extraction System")
    print("="*60)
    
    # First test if we can get any response
    quick_ok = test_quick_response()
    
    if quick_ok:
        print("\n" + "="*60)
        # Now test extraction
        extraction_ok = test_simple_extraction()
        
        if extraction_ok:
            print("\n✅ EXTRACTION IS WORKING")
        else:
            print("\n❌ EXTRACTION IS NOT WORKING")
    else:
        print("\n❌ BASIC CHAT IS NOT WORKING")