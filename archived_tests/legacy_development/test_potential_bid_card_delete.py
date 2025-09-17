"""
Test the potential bid card delete functionality
"""

import requests
import json

BASE_URL = 'http://localhost:8008'
USER_ID = '550e8400-e29b-41d4-a716-446655440001'

def test_delete_functionality():
    print("Testing Potential Bid Card Delete Functionality")
    print("=" * 50)
    
    # Step 1: Get current potential bid cards
    print("\n1. Getting current potential bid cards...")
    response = requests.get(f'{BASE_URL}/api/cia/user/{USER_ID}/potential-bid-cards')
    
    if response.status_code == 200:
        data = response.json()
        bid_cards = data.get('bid_cards', [])
        print(f"   Found {len(bid_cards)} potential bid cards")
        
        if len(bid_cards) == 0:
            print("   No potential bid cards to delete")
            return
        
        # Get the first one to delete
        test_card = bid_cards[0]
        print(f"   Test card ID: {test_card['id']}")
        print(f"   Test card title: {test_card.get('title', 'Untitled')}")
        
    else:
        print(f"   Failed to get bid cards: {response.status_code}")
        return
    
    # Step 2: Delete the test card
    print(f"\n2. Deleting potential bid card {test_card['id']}...")
    delete_response = requests.delete(f'{BASE_URL}/api/cia/potential-bid-cards/{test_card["id"]}')
    
    print(f"   Delete response: {delete_response.status_code}")
    
    if delete_response.status_code == 200:
        result = delete_response.json()
        print(f"   [SUCCESS] {result.get('message', 'Deleted successfully')}")
    else:
        print(f"   [ERROR] Failed to delete: {delete_response.text}")
        return
    
    # Step 3: Verify the card is gone
    print("\n3. Verifying deletion...")
    verify_response = requests.get(f'{BASE_URL}/api/cia/user/{USER_ID}/potential-bid-cards')
    
    if verify_response.status_code == 200:
        verify_data = verify_response.json()
        remaining_cards = verify_data.get('bid_cards', [])
        print(f"   Remaining potential bid cards: {len(remaining_cards)}")
        
        # Check if the deleted card is gone
        deleted_card_exists = any(card['id'] == test_card['id'] for card in remaining_cards)
        
        if not deleted_card_exists:
            print("   [SUCCESS] Card successfully deleted from database")
            print(f"   Count decreased from {len(bid_cards)} to {len(remaining_cards)}")
        else:
            print("   [ERROR] Card still exists in database")
    else:
        print(f"   [ERROR] Failed to verify deletion: {verify_response.status_code}")
    
    print("\n" + "=" * 50)
    print("DELETE FUNCTIONALITY TEST SUMMARY")
    print("=" * 50)
    
    if delete_response.status_code == 200 and not deleted_card_exists:
        print("[SUCCESS] Delete functionality working correctly!")
        print("- API endpoint responds ✓")
        print("- Database deletion confirmed ✓")
        print("- Frontend can use this feature ✓")
    else:
        print("[ERROR] Delete functionality has issues")

if __name__ == "__main__":
    test_delete_functionality()