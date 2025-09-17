#!/usr/bin/env python3
"""
Test direct creation of potential bid card via API
"""
import requests
import json
from uuid import uuid4

# Generate valid UUIDs
conversation_id = str(uuid4())
user_id = str(uuid4())
session_id = conversation_id  # Use same ID for both

print(f"Test IDs:")
print(f"  Conversation/Session ID: {conversation_id}")
print(f"  User ID: {user_id}")
print()

# Test 1: Create potential bid card directly
print("Test 1: Creating potential bid card directly...")
create_payload = {
    "conversation_id": conversation_id,
    "session_id": session_id,
    # Don't provide user_id since it requires existing homeowner
    "title": "Backyard Landscaping Project"
}

response = requests.post(
    "http://localhost:8008/api/cia/potential-bid-cards",
    json=create_payload
)

if response.status_code == 200:
    bid_card = response.json()
    bid_card_id = bid_card["id"]
    print(f"[OK] Created potential bid card: {bid_card_id}")
    print(f"   Status: {bid_card['status']}")
    print(f"   Completion: {bid_card['completion_percentage']}%")
    print()
    
    # Test 2: Update fields
    print("Test 2: Updating fields...")
    fields_to_update = [
        ("project_type", "landscaping"),
        ("project_description", "Install new sod and irrigation system in backyard"),
        ("zip_code", "78702"),
        ("email_address", "john@example.com"),
        ("timeline", "urgent")
    ]
    
    for field_name, field_value in fields_to_update:
        update_payload = {
            "field_name": field_name,
            "field_value": field_value,
            "source": "conversation"
        }
        
        update_response = requests.put(
            f"http://localhost:8008/api/cia/potential-bid-cards/{bid_card_id}/field",
            json=update_payload
        )
        
        if update_response.status_code == 200:
            result = update_response.json()
            print(f"   [OK] Updated {field_name}: {result['completion_percentage']}% complete")
        else:
            print(f"   [FAIL] Failed to update {field_name}: {update_response.status_code}")
    
    print()
    
    # Test 3: Get final state
    print("Test 3: Getting final bid card state...")
    get_response = requests.get(
        f"http://localhost:8008/api/cia/potential-bid-cards/{bid_card_id}"
    )
    
    if get_response.status_code == 200:
        final_state = get_response.json()
        print(f"[OK] Final bid card state:")
        print(f"   Completion: {final_state['completion_percentage']}%")
        print(f"   Ready for conversion: {final_state['ready_for_conversion']}")
        print(f"   Missing fields: {final_state['missing_fields']}")
        print(f"   Fields collected: {json.dumps(final_state['fields_collected'], indent=6)}")
    else:
        print(f"[FAIL] Failed to get bid card: {get_response.status_code}")
    
else:
    print(f"[FAIL] Failed to create bid card: {response.status_code}")
    print(f"   Error: {response.text}")