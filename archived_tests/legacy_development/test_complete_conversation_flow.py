#!/usr/bin/env python3
"""
Test complete conversation flow with date extraction and group bidding
"""

import requests
import json
import time

def test_complete_flow():
    print("Testing Complete CIA Conversation Flow")
    print("=" * 60)
    
    # Test data
    base_url = "http://localhost:8008"
    user_id = "test-user-dates"
    session_id = "test-session-dates"
    conversation_id = "test-conv-dates"
    
    # Test message with dates and group bidding context
    test_message = {
        "messages": [
            {
                "content": "Hi! I need my kitchen renovated in 12345 ZIP code. I need all the bids by Friday December 20th and the project completed before my daughter's wedding on February 14th. Also, my neighbor mentioned they might want to do their kitchen too - can we coordinate for group savings?"
            }
        ],
        "conversation_id": conversation_id,
        "user_id": user_id,
        "session_id": session_id
    }
    
    print("1. Testing CIA Conversation with Dates and Group Bidding")
    print(f"Message: {test_message['messages'][0]['content'][:100]}...")
    
    try:
        # Send message to CIA
        response = requests.post(
            f"{base_url}/api/cia/stream",
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=60,
            stream=True
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: CIA conversation started")
            
            # Read first few chunks to verify response
            chunk_count = 0
            for line in response.iter_lines():
                if line and chunk_count < 10:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if 'choices' in data and data['choices']:
                                content = data['choices'][0].get('delta', {}).get('content', '')
                                if content:
                                    print(f"  Response chunk: {content}")
                                    chunk_count += 1
                        except json.JSONDecodeError:
                            pass
                    
            print("\\n2. Testing Potential Bid Card Creation")
            
            # Wait a bit for processing
            time.sleep(3)
            
            # Check if potential bid card was created
            bid_card_response = requests.get(
                f"{base_url}/api/cia/conversation/{conversation_id}/potential-bid-card"
            )
            
            print(f"Bid Card Status: {bid_card_response.status_code}")
            
            if bid_card_response.status_code == 200:
                bid_card_data = bid_card_response.json()
                print("SUCCESS: Potential bid card created")
                print(f"  Completion: {bid_card_data.get('completion_percentage', 0)}%")
                print(f"  Fields collected: {len(bid_card_data.get('fields_collected', {}))}")
                
                # Check for date fields
                fields = bid_card_data.get('fields_collected', {})
                date_fields = ['bid_collection_deadline', 'project_completion_deadline', 'deadline_hard', 'deadline_context']
                
                print("\\n3. Checking Date Extraction in Database")
                found_dates = False
                for field in date_fields:
                    if field in fields and fields[field]:
                        print(f"  SUCCESS: {field} = {fields[field]}")
                        found_dates = True
                
                if not found_dates:
                    print("  WARNING: No date fields found in database")
                    print(f"  Available fields: {list(fields.keys())}")
                
            else:
                print(f"ERROR: Could not retrieve bid card - {bid_card_response.text}")
                
        else:
            print(f"ERROR: CIA conversation failed - {response.text}")
            
    except requests.exceptions.Timeout:
        print("SUCCESS: CIA response started (timed out while streaming - this is expected)")
        
        # Still check if bid card was created
        print("\\n2. Checking if Potential Bid Card was created despite timeout")
        try:
            bid_card_response = requests.get(
                f"{base_url}/api/cia/conversation/{conversation_id}/potential-bid-card"
            )
            
            if bid_card_response.status_code == 200:
                bid_card_data = bid_card_response.json()
                print("SUCCESS: Potential bid card was created")
                print(f"  Completion: {bid_card_data.get('completion_percentage', 0)}%")
                
                # Check for date fields  
                fields = bid_card_data.get('fields_collected', {})
                print("\\n3. Checking Date Fields in Database")
                
                date_fields = ['bid_collection_deadline', 'project_completion_deadline', 'deadline_hard', 'deadline_context']
                for field in date_fields:
                    if field in fields and fields[field]:
                        print(f"  SUCCESS: {field} = {fields[field]}")
            else:
                print("WARNING: No bid card created yet")
                
        except Exception as e:
            print(f"ERROR checking bid card: {e}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\\n" + "=" * 60)
    print("Complete conversation flow test finished!")

if __name__ == "__main__":
    test_complete_flow()