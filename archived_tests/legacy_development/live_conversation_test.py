#!/usr/bin/env python3
"""
Live conversation test - shows actual CIA responses
"""

import requests
import json
import time
import uuid

def send_message_and_get_response(base_url, conversation_id, user_id, session_id, message):
    """Send message and capture the actual CIA response"""
    
    print(f"\n{'='*80}")
    print(f"USER: {message}")
    print(f"{'='*80}")
    
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
            timeout=60,
            stream=True
        )
        
        if response.status_code == 200:
            print("CIA: ", end="", flush=True)
            full_response = ""
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if 'choices' in data and data['choices']:
                                content = data['choices'][0].get('delta', {}).get('content', '')
                                if content:
                                    print(content, end="", flush=True)
                                    full_response += content
                        except json.JSONDecodeError:
                            pass
            
            print("\n")  # End the CIA response
            return full_response
            
        else:
            print(f"CIA: ERROR - {response.status_code}: {response.text}")
            return f"ERROR: {response.status_code}"
            
    except requests.exceptions.Timeout:
        print("CIA: [Response timed out but conversation likely processed]")
        return "[Timeout - response may have been processed]"
    except Exception as e:
        print(f"CIA: ERROR - {e}")
        return f"ERROR: {e}"

def check_bid_card_after_turn(base_url, conversation_id, turn_number):
    """Check bid card progress after each turn"""
    try:
        response = requests.get(
            f"{base_url}/api/cia/conversation/{conversation_id}/potential-bid-card",
            timeout=10
        )
        
        print(f"\nBID CARD STATUS AFTER TURN {turn_number}:")
        
        if response.status_code == 200:
            data = response.json()
            completion = data.get('completion_percentage', 0)
            fields = data.get('fields_collected', {})
            
            print(f"   Completion: {completion}%")
            print(f"   Fields collected: {len([f for f in fields.values() if f])}")
            
            # Show key new fields
            key_fields = ['project_type', 'zip_code', 'budget_min', 'budget_max', 
                         'bid_collection_deadline', 'project_completion_deadline', 
                         'email_address', 'timeline']
            
            new_fields = []
            for field in key_fields:
                if field in fields and fields[field]:
                    new_fields.append(f"{field}: {fields[field]}")
            
            if new_fields:
                print("   Key fields:")
                for field in new_fields[:5]:  # Show first 5
                    print(f"     • {field}")
                if len(new_fields) > 5:
                    print(f"     ... and {len(new_fields)-5} more")
        else:
            print("   No bid card created yet")
            
    except Exception as e:
        print(f"   Error checking bid card: {e}")

def run_live_conversation():
    print("LIVE CIA CONVERSATION TEST")
    print("Showing actual back-and-forth with the CIA agent")
    print("=" * 80)
    
    base_url = "http://localhost:8008"
    conversation_id = f"live-test-{int(time.time())}"
    user_id = str(uuid.uuid4())
    session_id = f"session-{int(time.time())}"
    
    # Conversation turns
    messages = [
        "Hi! I need my kitchen renovated.",
        
        "It's in 90210. I want to modernize everything - cabinets, countertops, appliances, flooring. About 300 square feet.",
        
        "I need all the bids by this Friday and the project completed before my daughter's wedding on February 14th. This is very urgent!",
        
        "My budget is around $45,000 to $60,000. I want high quality work since it's for a special occasion.",
        
        "My neighbor is also planning a kitchen remodel. Can we coordinate both projects for group savings?",
        
        "I prefer working with licensed contractors who have insurance. This is too important to risk with handymen.",
        
        "I want quartz countertops, soft-close cabinets, and stainless steel appliances. Also need new lighting.",
        
        "My email is bride.mother@wedding.com for contractor responses. When will I start getting bids?"
    ]
    
    print(f"Starting conversation with ID: {conversation_id}")
    print(f"User ID: {user_id}")
    
    for turn, message in enumerate(messages, 1):
        print(f"\nTURN {turn} OF {len(messages)}")
        
        # Send message and get CIA response
        response = send_message_and_get_response(
            base_url, conversation_id, user_id, session_id, message
        )
        
        # Check bid card progress
        time.sleep(2)  # Brief pause for processing
        check_bid_card_after_turn(base_url, conversation_id, turn)
        
        # Pause between turns
        if turn < len(messages):
            print(f"\nPausing before turn {turn+1}...")
            time.sleep(3)
    
    # Final summary
    print(f"\nFINAL CONVERSATION SUMMARY")
    print("=" * 80)
    
    try:
        final_response = requests.get(
            f"{base_url}/api/cia/conversation/{conversation_id}/potential-bid-card",
            timeout=10
        )
        
        if final_response.status_code == 200:
            final_data = final_response.json()
            fields = final_data.get('fields_collected', {})
            
            print(f"Final completion: {final_data.get('completion_percentage', 0)}%")
            print(f"Ready for conversion: {final_data.get('ready_for_conversion', False)}")
            print(f"Total fields collected: {len([f for f in fields.values() if f])}")
            
            print("\nAll extracted information:")
            for field, value in fields.items():
                if value:
                    print(f"  {field}: {value}")
                    
            # Check date extraction specifically
            date_fields = ['bid_collection_deadline', 'project_completion_deadline', 'deadline_context']
            print(f"\nDATE EXTRACTION RESULTS:")
            for field in date_fields:
                if field in fields and fields[field]:
                    print(f"  SUCCESS {field}: {fields[field]}")
                else:
                    print(f"  MISSING {field}: Not extracted")
                    
            # Check group bidding
            description = fields.get('project_description', '')
            if 'group' in description.lower() or 'neighbor' in description.lower():
                print(f"\nGROUP BIDDING: SUCCESS - Detected")
                print(f"   Context: {description}")
            else:
                print(f"\nGROUP BIDDING: NOT DETECTED")
                
        else:
            print("ERROR: No final bid card found")
            
    except Exception as e:
        print(f"ERROR getting final summary: {e}")
    
    print(f"\nLive conversation test completed!")
    print(f"Conversation ID: {conversation_id}")

if __name__ == "__main__":
    run_live_conversation()