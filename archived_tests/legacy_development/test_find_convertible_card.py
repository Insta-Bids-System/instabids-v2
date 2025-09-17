"""
Find a potential bid card that's ready for conversion to test data transfer
"""

import requests
import json

BASE_URL = 'http://localhost:8008'
USER_ID = '550e8400-e29b-41d4-a716-446655440001'

def find_convertible_card():
    print("Finding Convertible Potential Bid Cards")
    print("=" * 50)
    
    # Get all potential bid cards
    response = requests.get(f'{BASE_URL}/api/cia/user/{USER_ID}/potential-bid-cards')
    
    if response.status_code == 200:
        data = response.json()
        bid_cards = data.get('bid_cards', [])
        print(f"Found {len(bid_cards)} potential bid cards")
        
        # Check each card for conversion readiness
        for i, card in enumerate(bid_cards):
            print(f"\n--- Card {i+1}: {card['id']} ---")
            print(f"Title: {card.get('title', 'Untitled')}")
            print(f"Completion: {card.get('completion_percentage', 0)}%")
            
            # Check required fields
            required_fields = ['primary_trade', 'user_scope_notes', 'zip_code', 'email_address', 'urgency_level']
            missing = []
            present = []
            
            for field in required_fields:
                value = card.get(field)
                if value is None or value == '' or value == []:
                    missing.append(field)
                else:
                    present.append(field)
                    print(f"  [OK] {field}: {value}")
            
            if missing:
                print(f"  [MISSING] Required fields: {', '.join(missing)}")
            else:
                print(f"  [READY] READY FOR CONVERSION!")
                return card
        
        # If no ready cards found, let's create one by updating an existing card
        if bid_cards:
            print(f"\n--- Updating first card to make it conversion-ready ---")
            test_card = bid_cards[0]
            card_id = test_card['id']
            
            # Update required fields
            updates = [
                {'field_name': 'zip_code', 'field_value': '12345'},
                {'field_name': 'email_address', 'field_value': 'test@example.com'}
            ]
            
            for update in updates:
                print(f"Setting {update['field_name']} = {update['field_value']}")
                update_response = requests.put(
                    f'{BASE_URL}/api/cia/potential-bid-cards/{card_id}/field',
                    json=update
                )
                
                if update_response.status_code == 200:
                    print(f"  [OK] Updated {update['field_name']}")
                else:
                    print(f"  [ERROR] Failed to update {update['field_name']}: {update_response.text}")
            
            # Return the updated card info
            updated_response = requests.get(f'{BASE_URL}/api/cia/potential-bid-cards/{card_id}')
            if updated_response.status_code == 200:
                return updated_response.json()
            else:
                return test_card
                
    else:
        print(f"Failed to get potential bid cards: {response.status_code}")
        return None

if __name__ == "__main__":
    convertible_card = find_convertible_card()
    if convertible_card:
        print(f"\n[SUCCESS] Found/created convertible card: {convertible_card['id']}")
        print(f"Ready for conversion: {convertible_card.get('ready_for_conversion', False)}")
    else:
        print("\n[ERROR] No convertible cards found")