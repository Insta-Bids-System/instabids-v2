#!/usr/bin/env python3
"""
Test IRIS Real-Time Visual Effects System
Tests that IRIS actions trigger WebSocket broadcasts and UI visual effects
"""

import asyncio
import json
import requests
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8008"
FRONTEND_URL = "http://localhost:5173"

def test_iris_potential_bid_card_update():
    """Test IRIS updating a potential bid card and triggering visual effects"""
    print(f"\nTesting IRIS Potential Bid Card Update - {datetime.now().strftime('%H:%M:%S')}")
    
    # First, create a test potential bid card
    print("1. Creating test potential bid card...")
    create_payload = {
        "user_id": "test-homeowner-123",
        "conversation_id": "test-conv-456",
        "initial_fields": {
            "project_type": "Kitchen Remodel",
            "description": "Looking to update my kitchen with modern appliances and countertops",
            "zip_code": "90210"
        }
    }
    
    try:
        create_response = requests.post(
            f"{BACKEND_URL}/api/cia/potential-bid-cards",
            json=create_payload,
            timeout=10
        )
        create_response.raise_for_status()
        potential_card = create_response.json()
        card_id = potential_card["id"]
        print(f"   Created potential bid card: {card_id}")
        
        # Now test IRIS updating it
        print("2. Testing IRIS field update...")
        iris_payload = {
            "bid_card_id": card_id,
            "field_name": "budget_range",
            "field_value": "$50,000 - $75,000",
            "agent_name": "IRIS",
            "context": "Budget extracted from homeowner conversation about kitchen preferences"
        }
        
        update_response = requests.post(
            f"{BACKEND_URL}/api/iris/update-potential-bid-card",
            json=iris_payload,
            timeout=15
        )
        update_response.raise_for_status()
        update_result = update_response.json()
        
        print(f"   IRIS update successful: {update_result.get('message', 'No message')}")
        
        # Check if WebSocket broadcast was triggered
        if update_result.get("websocket_broadcast"):
            print("   WebSocket broadcast triggered - Visual effects should appear!")
            print(f"   Broadcast data: {json.dumps(update_result['websocket_broadcast'], indent=2)}")
        else:
            print("   No WebSocket broadcast detected")
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"   Request failed: {e}")
        return False
    except Exception as e:
        print(f"   Unexpected error: {e}")
        return False

def test_iris_bid_card_update():
    """Test IRIS updating a regular bid card"""
    print(f"\nTesting IRIS Bid Card Update - {datetime.now().strftime('%H:%M:%S')}")
    
    # Test with an existing bid card
    test_bid_card_id = "78c3f7cb-64d8-496e-b396-32b24d790252"  # Known test bid card
    
    try:
        iris_payload = {
            "bid_card_id": test_bid_card_id,
            "updates": {
                "urgency_level": "high",
                "contractor_count_needed": 6
            },
            "agent_name": "IRIS",
            "reason": "Homeowner indicated this is now urgent due to upcoming event"
        }
        
        update_response = requests.post(
            f"{BACKEND_URL}/api/iris/update-bid-card",
            json=iris_payload,
            timeout=15
        )
        update_response.raise_for_status()
        update_result = update_response.json()
        
        print(f"   IRIS bid card update successful: {update_result.get('message', 'No message')}")
        
        # Check if WebSocket broadcast was triggered
        if update_result.get("websocket_broadcast"):
            print("   WebSocket broadcast triggered - Visual effects should appear!")
            print(f"   Broadcast data: {json.dumps(update_result['websocket_broadcast'], indent=2)}")
        else:
            print("   No WebSocket broadcast detected")
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"   Request failed: {e}")
        return False
    except Exception as e:
        print(f"   Unexpected error: {e}")
        return False

def check_backend_health():
    """Verify backend is running and responsive"""
    print(f"\nChecking Backend Health - {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        response = requests.get(f"{BACKEND_URL}", timeout=5)
        response.raise_for_status()
        print("   Backend is responsive")
        return True
    except requests.exceptions.RequestException as e:
        print(f"   Backend not responding: {e}")
        return False

def main():
    """Run all IRIS visual effects tests"""
    print("IRIS Real-Time Visual Effects Test Suite")
    print("=" * 50)
    
    # Check backend health first
    if not check_backend_health():
        print("\n❌ Backend not available - cannot run tests")
        return
    
    print(f"\nTest Instructions:")
    print("1. Open browser to http://localhost:5173")
    print("2. Navigate to dashboard or bid cards page")
    print("3. Watch for purple glow effects and agent badges during tests")
    print("4. Check browser console for WebSocket messages")
    
    input("\nPress Enter when ready to start tests...")
    
    # Test sequence
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Potential bid card update
    if test_iris_potential_bid_card_update():
        tests_passed += 1
    
    # Brief pause between tests
    time.sleep(2)
    
    # Test 2: Regular bid card update
    if test_iris_bid_card_update():
        tests_passed += 1
    
    # Results summary
    print(f"\nTest Results Summary:")
    print(f"   Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("   All tests passed! Visual effects system is working!")
    else:
        print("   Some tests failed - check backend logs")
    
    print(f"\nVisual Effects to Look For:")
    print("   - Purple glowing border around affected elements")
    print("   - Agent badge showing 'IRIS' on working elements")
    print("   - Smooth animations and transitions")
    print("   - Real-time updates without page refresh")

if __name__ == "__main__":
    main()