"""
Comprehensive CIA Conversation Test - 8-10 Turn Detailed Conversation
Tests the complete potential bid card creation and field extraction process
"""

import json
import requests
import time

# Test configuration
BASE_URL = "http://localhost:8008"
conversation_id = f"comprehensive_test_{int(time.time())}"
session_id = f"session_{int(time.time())}"
user_id = "00000000-0000-0000-0000-000000000000"  # Anonymous user

def create_potential_bid_card():
    """Create initial potential bid card"""
    print("STEP 1: Creating potential bid card...")
    
    response = requests.post(f"{BASE_URL}/api/cia/potential-bid-cards", json={
        "conversation_id": conversation_id,
        "session_id": session_id,
        "user_id": user_id,
        "title": "Comprehensive Test Project"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"SUCCESS: Created potential bid card: {data['id']}")
        print(f"   Status: {data['status']}")
        print(f"   Completion: {data['completion_percentage']}%")
        print(f"   Missing fields: {data['missing_fields']}")
        return data['id']
    else:
        print(f"ERROR: Failed to create bid card: {response.text}")
        return None

def get_bid_card_by_conversation():
    """Get bid card by conversation ID"""
    response = requests.get(f"{BASE_URL}/api/cia/conversation/{conversation_id}/potential-bid-card")
    if response.status_code == 200:
        return response.json()
    return None

def chat_with_cia(message, turn_number):
    """Send message to CIA and get streaming response"""
    print(f"\nTURN {turn_number}: USER")
    print(f"Message: {message}")
    
    start_time = time.time()
    
    try:
        response = requests.post(f"{BASE_URL}/api/cia/stream", 
            json={
                "messages": [{"role": "user", "content": message}],
                "conversation_id": conversation_id,
                "user_id": user_id,
                "max_tokens": 300
            },
            stream=True,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"ERROR: HTTP {response.status_code} - {response.text}")
            return None
            
        # Collect streaming response
        full_response = ""
        chunk_count = 0
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    data_content = line_text[6:]
                    
                    if data_content == '[DONE]':
                        break
                        
                    try:
                        chunk = json.loads(data_content)
                        if chunk.get('choices') and chunk['choices'][0].get('delta') and chunk['choices'][0]['delta'].get('content'):
                            content = chunk['choices'][0]['delta']['content']
                            full_response += content
                            chunk_count += 1
                    except json.JSONDecodeError:
                        continue
        
        response_time = time.time() - start_time
        
        print(f"CIA RESPONSE (Turn {turn_number}):")
        print(f"Response: {full_response}")
        print(f"Response time: {response_time:.2f}s, Chunks: {chunk_count}")
        
        return full_response
        
    except Exception as e:
        print(f"ERROR in turn {turn_number}: {e}")
        return None

def check_bid_card_after_turn(turn_number):
    """Check bid card status after each conversation turn"""
    print(f"\nBID CARD STATUS AFTER TURN {turn_number}:")
    
    # Get bid card status
    bid_card = get_bid_card_by_conversation()
    if bid_card:
        print(f"   Completion: {bid_card['completion_percentage']}%")
        print(f"   Status: {bid_card['status']}")
        print(f"   Ready for conversion: {bid_card['ready_for_conversion']}")
        print(f"   Missing fields: {bid_card['missing_fields']}")
        print(f"   Fields collected: {list(bid_card['fields_collected'].keys())}")
        
        # Show bid card preview
        if bid_card.get('bid_card_preview'):
            preview = bid_card['bid_card_preview']
            print(f"   PREVIEW:")
            print(f"      Title: {preview.get('title', 'N/A')}")
            print(f"      Project Type: {preview.get('project_type', 'N/A')}")
            print(f"      Description: {preview.get('description', 'N/A')}")
            print(f"      Location: {preview.get('location', 'N/A')}")
            print(f"      Timeline: {preview.get('timeline', 'N/A')}")
        
        return bid_card
    else:
        print("   ERROR: No bid card found")
        return None

def main():
    """Run comprehensive CIA conversation test"""
    print("COMPREHENSIVE CIA CONVERSATION TEST")
    print("=" * 60)
    
    # Step 1: Create potential bid card
    bid_card_id = create_potential_bid_card()
    if not bid_card_id:
        return
    
    print(f"\nStarting conversation with ID: {conversation_id}")
    print(f"Bid card ID: {bid_card_id}")
    
    # Multi-turn conversation
    conversation_turns = [
        "Hi, I need help with a home improvement project",
        "I want to remodel my bathroom. It's a full renovation - new tile, vanity, shower, everything.",
        "I live in Seattle, WA 98102. The bathroom is about 40 square feet.",
        "I'm hoping to get this done within the next 2-3 months. No huge rush but I'd like to start soon.",
        "My budget is flexible but I'm thinking around $15,000 to $25,000 for the whole project.",
        "I definitely want high-quality materials - maybe marble or quartz countertops and good fixtures.",
        "For contractors, I prefer working with established companies that have good reviews and insurance.",
        "My email is john.homeowner@email.com and my phone is 206-555-0123 for contact.",
        "Do you think that budget is realistic for what I'm describing?",
        "Great! I'm ready to see some contractor options. How do we proceed from here?"
    ]
    
    # Execute conversation turns
    for i, message in enumerate(conversation_turns, 1):
        # Send message to CIA
        response = chat_with_cia(message, i)
        
        if response is None:
            print(f"ERROR: Conversation failed at turn {i}")
            break
            
        # Check bid card status after each turn
        bid_card = check_bid_card_after_turn(i)
        
        # Add small delay between turns
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("FINAL BID CARD STATUS")
    print("=" * 60)
    
    final_bid_card = get_bid_card_by_conversation()
    if final_bid_card:
        print(f"Final completion: {final_bid_card['completion_percentage']}%")
        print(f"Ready for conversion: {final_bid_card['ready_for_conversion']}")
        print(f"Status: {final_bid_card['status']}")
        
        if final_bid_card['ready_for_conversion']:
            print("\nBID CARD IS READY FOR CONVERSION TO OFFICIAL!")
        else:
            print(f"\nStill missing: {final_bid_card['missing_fields']}")
    
    print("\nCOMPREHENSIVE TEST COMPLETED")

if __name__ == "__main__":
    main()