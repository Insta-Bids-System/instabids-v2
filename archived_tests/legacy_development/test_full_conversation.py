#!/usr/bin/env python3
"""
Full 8-10 turn conversation test with CIA agent
"""

import requests
import json
import time

def send_cia_message(base_url, conversation_id, user_id, session_id, message):
    """Send a message to CIA and get the response"""
    
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
            timeout=30,
            stream=True
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            full_response = ""
            chunk_count = 0
            
            for line in response.iter_lines():
                if line and chunk_count < 50:  # Limit chunks to avoid too much output
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if 'choices' in data and data['choices']:
                                content = data['choices'][0].get('delta', {}).get('content', '')
                                if content:
                                    full_response += content
                                    chunk_count += 1
                        except json.JSONDecodeError:
                            pass
            
            return full_response[:500] + "..." if len(full_response) > 500 else full_response
        else:
            return f"ERROR: {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        return "Response started (timed out while streaming - normal behavior)"
    except Exception as e:
        return f"ERROR: {e}"

def check_bid_card_progress(base_url, conversation_id):
    """Check the current bid card progress"""
    try:
        response = requests.get(
            f"{base_url}/api/cia/conversation/{conversation_id}/potential-bid-card",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
    except Exception as e:
        print(f"Error checking bid card: {e}")
        return None

def run_full_conversation():
    print("Starting Full 8-10 Turn CIA Conversation Test")
    print("=" * 70)
    
    base_url = "http://localhost:8008"
    conversation_id = "full-test-conv"
    user_id = "full-test-user"
    session_id = "full-test-session"
    
    # Conversation turns
    turns = [
        "Hi! I'm interested in getting my backyard renovated.",
        
        "It's about 2000 square feet. I want to add a deck, some landscaping, and maybe a fire pit area. My ZIP code is 90210.",
        
        "I'd like to get all the bids by next Friday and have the work completed before my daughter's wedding on March 15th. This is pretty urgent for me.",
        
        "My budget is probably around $25,000 to $35,000 based on what I've researched online. I want good quality work but nothing too fancy.",
        
        "Yes, I have some photos! I can upload them. Also, my neighbor mentioned they might want to do their backyard too - can we coordinate for group savings?",
        
        "I prefer working with established contractors who have insurance. I don't want just handymen for this - it's a big project for my daughter's special day.",
        
        "The deck should be about 400 square feet, composite materials preferred. For landscaping, I want drought-resistant plants since we're in California.",
        
        "I need permits for the deck I assume? And the fire pit needs to be safe - maybe gas instead of wood burning? What do you think?",
        
        "Perfect! My email is sarah.wedding@email.com for contractor responses. When can we start getting bids?",
        
        "Sounds great! Let's get this started so I can make my daughter's wedding perfect!"
    ]
    
    print(f"Planning {len(turns)} conversation turns...\n")
    
    for i, message in enumerate(turns, 1):
        print(f"TURN {i}: User Message")
        print(f"'{message}'\n")
        
        print("CIA Response:")
        response = send_cia_message(base_url, conversation_id, user_id, session_id, message)
        print(f"{response}\n")
        
        # Check bid card progress after each turn
        print("Bid Card Progress:")
        bid_card = check_bid_card_progress(base_url, conversation_id)
        
        if bid_card:
            completion = bid_card.get('completion_percentage', 0)
            fields = bid_card.get('fields_collected', {})
            print(f"  Completion: {completion}%")
            print(f"  Fields: {len(fields)} collected")
            
            # Show key fields
            key_fields = ['project_type', 'budget_min', 'budget_max', 'timeline', 'zip_code', 'email',
                         'bid_collection_deadline', 'project_completion_deadline', 'contractor_preference']
            
            for field in key_fields:
                if field in fields and fields[field]:
                    print(f"    {field}: {fields[field]}")
        else:
            print("  No bid card created yet")
        
        print("-" * 70)
        
        # Small delay between turns
        time.sleep(2)
    
    # Final bid card summary
    print("\nFINAL BID CARD SUMMARY")
    print("=" * 70)
    
    final_bid_card = check_bid_card_progress(base_url, conversation_id)
    
    if final_bid_card:
        print(f"Completion: {final_bid_card.get('completion_percentage', 0)}%")
        print(f"Ready for conversion: {final_bid_card.get('ready_for_conversion', False)}")
        
        print("\nAll Collected Fields:")
        fields = final_bid_card.get('fields_collected', {})
        for field, value in fields.items():
            if value:
                print(f"  {field}: {value}")
        
        print(f"\nTotal fields collected: {len([f for f in fields.values() if f])}")
        
        # Check for critical date fields
        date_fields = ['bid_collection_deadline', 'project_completion_deadline', 'deadline_hard', 'deadline_context']
        print("\nDate Fields Extracted:")
        for field in date_fields:
            if field in fields:
                print(f"  {field}: {fields[field]}")
        
        # Check for group bidding mention
        description = fields.get('project_description', '')
        if 'group' in description.lower() or 'neighbor' in description.lower():
            print(f"\nGroup Bidding Detected: YES")
            print(f"Context: {description}")
        else:
            print(f"\nGroup Bidding Detected: NO")
            
    else:
        print("ERROR: No final bid card found!")
    
    print("\n" + "=" * 70)
    print("Full conversation test completed!")

if __name__ == "__main__":
    run_full_conversation()