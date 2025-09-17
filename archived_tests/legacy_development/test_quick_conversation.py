#!/usr/bin/env python3
"""
Quick 3-turn conversation test
"""

import requests
import json
import time

def test_quick_conversation():
    print("Quick 3-Turn Conversation Test")
    print("=" * 50)
    
    base_url = "http://localhost:8008"
    conversation_id = "quick-test"
    user_id = "quick-user"
    session_id = "quick-session"
    
    # Test 3 turns
    turns = [
        "Hi! I need my kitchen renovated in 90210.",
        "I want all bids by Friday and project done before March 15th. Budget is $25,000-$35,000.",
        "My neighbor wants to do their kitchen too - can we get group savings? My email is test@email.com"
    ]
    
    for i, message in enumerate(turns, 1):
        print(f"\nTURN {i}: {message}")
        
        # Quick API test - don't wait for full response
        data = {
            "messages": [{"content": message}],
            "conversation_id": conversation_id,
            "user_id": user_id,
            "session_id": session_id
        }
        
        try:
            response = requests.post(
                f"{base_url}/api/cia/stream",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            print(f"API Response: {response.status_code}")
        except:
            print("API Response: Started (expected timeout)")
        
        # Wait a bit then check bid card
        time.sleep(3)
        
        try:
            bid_response = requests.get(
                f"{base_url}/api/cia/conversation/{conversation_id}/potential-bid-card",
                timeout=5
            )
            
            if bid_response.status_code == 200:
                bid_data = bid_response.json()
                completion = bid_data.get('completion_percentage', 0)
                fields = bid_data.get('fields_collected', {})
                
                print(f"Bid Card: {completion}% complete, {len(fields)} fields")
                
                # Show new fields
                if fields:
                    print("New fields:")
                    for k, v in fields.items():
                        if v:
                            print(f"  {k}: {v}")
            else:
                print("Bid Card: Not created yet")
                
        except Exception as e:
            print(f"Bid Card: Error - {e}")
    
    # Final summary
    print(f"\nFINAL BID CARD CHECK:")
    try:
        final_response = requests.get(
            f"{base_url}/api/cia/conversation/{conversation_id}/potential-bid-card",
            timeout=5
        )
        
        if final_response.status_code == 200:
            final_data = final_response.json()
            fields = final_data.get('fields_collected', {})
            
            print(f"Completion: {final_data.get('completion_percentage', 0)}%")
            print("All collected fields:")
            for k, v in fields.items():
                if v:
                    print(f"  {k}: {v}")
                    
            # Check date fields specifically
            date_fields = ['bid_collection_deadline', 'project_completion_deadline', 'deadline_context']
            print("\nDate extraction results:")
            for field in date_fields:
                if field in fields:
                    print(f"  {field}: {fields[field]}")
        else:
            print("No bid card found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_quick_conversation()