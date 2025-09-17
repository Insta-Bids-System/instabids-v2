"""
Final BSA test - check if bid cards are returned
"""
import requests
import json

data = {
    "contractor_id": "22222222-2222-2222-2222-222222222222",
    "message": "Show me turf projects near 33442",
    "session_id": "final-test"
}

print("Testing BSA...")

try:
    response = requests.post(
        "http://localhost:8008/api/bsa/unified-stream",
        json=data,
        stream=True,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        bid_cards_found = False
        sub_agent_messages = []
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        event = json.loads(line_str[6:])
                        
                        # Check for bid cards
                        if event.get('type') == 'bid_cards_found':
                            bid_cards_found = True
                            cards = event.get('bid_cards', [])
                            print(f"BID CARDS FOUND: {len(cards)} cards")
                            for i, card in enumerate(cards[:3]):
                                print(f"  {i+1}. {card.get('title', 'Unknown')}")
                        
                        # Track sub-agent messages
                        elif event.get('type') == 'sub_agent_status':
                            msg = event.get('message', '')
                            sub_agent_messages.append(msg)
                            print(f"STATUS: {msg}")
                        
                    except:
                        pass
        
        print("\n--- RESULTS ---")
        print(f"Bid cards found: {bid_cards_found}")
        print(f"Sub-agent messages: {len(sub_agent_messages)}")
        
        if bid_cards_found:
            print("\nSUCCESS: BSA is working!")
        else:
            print("\nFAILED: No bid cards returned")
            
except Exception as e:
    print(f"Error: {e}")