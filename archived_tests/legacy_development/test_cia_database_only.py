#!/usr/bin/env python3
"""
Test CIA database operations only - check if extraction and memory work
"""

import requests
import json
import uuid
import time

def test_database_operations():
    print("=== CIA DATABASE OPERATIONS TEST ===")
    
    user_id = f"test-user-{uuid.uuid4().hex[:6]}"
    conversation_id = f"test-conv-{uuid.uuid4().hex[:6]}"
    
    print(f"User ID: {user_id}")
    print(f"Conversation ID: {conversation_id}")
    
    # Start a non-streaming request to avoid timeout
    print("\n--- Starting CIA conversation (non-streaming) ---")
    try:
        # First, try to trigger extraction with a rich message
        response = requests.post(
            "http://localhost:8008/api/cia/extract-info",
            json={
                "message": "I need help with a kitchen renovation. I'm John Smith at 123 Main St, Austin TX. My budget is $30,000 and I want new cabinets and countertops. Email: john@example.com, phone 512-555-1234",
                "conversation_id": conversation_id,
                "user_id": user_id
            },
            timeout=5
        )
        print(f"Extraction endpoint status: {response.status_code}")
        if response.status_code == 200:
            print("Extraction response:", response.json())
    except Exception as e:
        print(f"Extraction endpoint not available: {e}")
    
    # Check potential bid card endpoints
    print("\n--- Checking potential bid card endpoints ---")
    
    endpoints_to_check = [
        f"http://localhost:8008/api/cia/conversation/{conversation_id}/potential-bid-card",
        f"http://localhost:8008/api/cia/potential-bid-cards/{conversation_id}",
        f"http://localhost:8008/api/cia/user/{user_id}/conversations",
        f"http://localhost:8008/api/cia/user/{user_id}/memory"
    ]
    
    for endpoint in endpoints_to_check:
        try:
            response = requests.get(endpoint, timeout=3)
            print(f"{endpoint} -> {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Data: {str(data)[:200]}...")
        except Exception as e:
            print(f"{endpoint} -> ERROR: {e}")
    
    # Try to create a potential bid card directly
    print("\n--- Attempting direct bid card creation ---")
    try:
        bid_card_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "fields": {
                "project_type": "kitchen renovation",
                "contact_name": "John Smith", 
                "location": "123 Main St, Austin TX",
                "budget_min": 25000,
                "budget_max": 35000,
                "contact_email": "john@example.com",
                "contact_phone": "512-555-1234"
            }
        }
        
        response = requests.post(
            "http://localhost:8008/api/cia/potential-bid-cards",
            json=bid_card_data,
            timeout=5
        )
        
        print(f"Direct bid card creation status: {response.status_code}")
        if response.status_code == 200:
            created_data = response.json()
            print("Created bid card:", json.dumps(created_data, indent=2))
            
            # Try to retrieve it
            bid_card_id = created_data.get('id')
            if bid_card_id:
                retrieve_response = requests.get(
                    f"http://localhost:8008/api/cia/potential-bid-cards/{bid_card_id}",
                    timeout=3
                )
                print(f"Retrieval status: {retrieve_response.status_code}")
                if retrieve_response.status_code == 200:
                    print("Retrieved bid card:", json.dumps(retrieve_response.json(), indent=2))
        else:
            print(f"Creation failed: {response.text}")
            
    except Exception as e:
        print(f"Direct bid card creation error: {e}")
    
    # Check conversation memory storage
    print("\n--- Testing conversation memory ---")
    try:
        memory_data = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "memory_type": "project_context",
            "data": {
                "project_type": "kitchen renovation",
                "budget_discussed": True,
                "contact_collected": True
            }
        }
        
        response = requests.post(
            "http://localhost:8008/api/conversations/memory",
            json=memory_data,
            timeout=5
        )
        
        print(f"Memory storage status: {response.status_code}")
        if response.status_code == 200:
            print("Memory stored successfully")
            
            # Try to retrieve
            retrieve_response = requests.get(
                f"http://localhost:8008/api/conversations/memory/{user_id}",
                timeout=3
            )
            print(f"Memory retrieval status: {retrieve_response.status_code}")
            
    except Exception as e:
        print(f"Memory storage error: {e}")
    
    print("\n--- Test Summary ---")
    print(f"User ID: {user_id}")
    print(f"Conversation ID: {conversation_id}")
    print("Tested database operations without streaming timeouts")

if __name__ == "__main__":
    test_database_operations()