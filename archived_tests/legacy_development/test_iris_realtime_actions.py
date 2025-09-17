"""
Test IRIS Real-time Action Capabilities
Tests that IRIS can actually modify bid cards and see updates in UI
"""

import requests
import json
import time

BASE_URL = "http://localhost:8008"

def test_iris_actions():
    """Test IRIS performing real-time actions"""
    
    print("Testing IRIS Real-time Actions...")
    print("=" * 50)
    
    # Test user
    test_user_id = "test_user_123"
    test_bid_card_id = "78c3f7cb-64d8-496e-b396-32b24d790252"  # Example bid card
    
    # Test 1: Ask IRIS to add a repair item
    print("\n1. Testing: Add repair item via conversation")
    response = requests.post(
        f"{BASE_URL}/api/iris/unified-chat",
        json={
            "user_id": test_user_id,
            "message": "Please add a backyard fence repair to my project. It needs to be 50 feet of wooden fence replacement.",
            "session_id": f"test_session_{int(time.time())}",
            "context": {
                "bid_card_id": test_bid_card_id,
                "property_id": "test_property_123"
            }
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        response_text = result.get('response', '').encode('ascii', 'ignore').decode('ascii')
        print(f"[SUCCESS] IRIS Response: {response_text[:200]}...")
        if "added" in result.get('response', '').lower():
            print("   -> IRIS successfully added the repair item!")
    else:
        print(f"[ERROR] Error: {response.status_code} - {response.text}")
    
    # Test 2: Ask IRIS to update urgency
    print("\n2. Testing: Update urgency level")
    response = requests.post(
        f"{BASE_URL}/api/iris/unified-chat",
        json={
            "user_id": test_user_id,
            "message": "This project is urgent now! We need it done ASAP because of an upcoming event.",
            "session_id": f"test_session_{int(time.time())}",
            "context": {
                "bid_card_id": test_bid_card_id
            }
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        response_text = result.get('response', '').encode('ascii', 'ignore').decode('ascii')
        print(f"[SUCCESS] IRIS Response: {response_text[:200]}...")
        if "urgent" in result.get('response', '').lower() or "updated" in result.get('response', '').lower():
            print("   -> IRIS successfully updated urgency!")
    else:
        print(f"[ERROR] Error: {response.status_code}")
    
    # Test 3: Direct action endpoint test
    print("\n3. Testing: Direct action endpoint")
    response = requests.post(
        f"{BASE_URL}/api/iris/actions/add-repair-item",
        json={
            "request_id": f"test_{int(time.time())}",
            "agent_name": "IRIS",
            "user_id": test_user_id,
            "bid_card_id": test_bid_card_id,
            "item": {
                "description": "Replace kitchen sink faucet",
                "severity": "medium",
                "category": "Plumbing",
                "estimated_cost": 350
            }
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"[SUCCESS] Action Result: {result.get('message', '')}")
        print(f"   -> Item added: {result.get('item', {}).get('description', '')}")
    else:
        print(f"[ERROR] Error: {response.status_code} - {response.text}")
    
    # Test 4: Create potential bid card
    print("\n4. Testing: Create potential bid card")
    response = requests.post(
        f"{BASE_URL}/api/iris/potential-bid-cards",
        params={"user_id": test_user_id},
        json={
            "title": "Backyard Landscaping Project",
            "room_location": "Backyard",
            "primary_trade": "Landscaping",
            "project_complexity": "medium",
            "user_scope_notes": "Need new fence, garden beds, and patio area"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"[SUCCESS] Created potential bid card: {result.get('potential_bid_card', {}).get('title', '')}")
        card_id = result.get('potential_bid_card', {}).get('id')
        
        # Test updating it
        if card_id:
            print(f"\n5. Testing: Update potential bid card {card_id}")
            update_response = requests.put(
                f"{BASE_URL}/api/iris/potential-bid-cards/{card_id}",
                json={
                    "user_scope_notes": "Added lighting requirements and irrigation system",
                    "priority": 2
                }
            )
            
            if update_response.status_code == 200:
                print(f"[SUCCESS] Updated potential bid card successfully")
            else:
                print(f"[ERROR] Update failed: {update_response.status_code}")
    else:
        print(f"[ERROR] Error creating bid card: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("IRIS Real-time Actions Test Complete!")
    print("\nTo see the visual effects:")
    print("1. Open the bid card in the UI")
    print("2. Have IRIS modify it via chat")
    print("3. Watch for glowing effects and real-time updates!")

if __name__ == "__main__":
    test_iris_actions()