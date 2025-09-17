"""
Test direct potential bid card creation via API
"""
import requests
import json
import uuid
import sys
import io

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8008"

def test_direct_bid_card_creation():
    """Test creating a potential bid card directly via API"""
    
    session_id = str(uuid.uuid4())
    conversation_id = session_id  # Use same ID for both
    user_id = "00000000-0000-0000-0000-000000000000"
    
    print("=" * 60)
    print("DIRECT POTENTIAL BID CARD CREATION TEST")
    print("=" * 60)
    print(f"Session ID: {session_id}")
    
    # Step 1: Create potential bid card
    create_payload = {
        "conversation_id": conversation_id,
        "session_id": session_id,
        "user_id": user_id,
        "title": "Test Deck Rebuild Project"
    }
    
    print("\n1. Creating potential bid card...")
    response = requests.post(
        f"{BASE_URL}/api/cia/potential-bid-cards",
        json=create_payload
    )
    
    if response.status_code == 200:
        data = response.json()
        bid_card_id = data.get("id")
        print(f"✓ Created bid card: {bid_card_id}")
        print(f"  Status: {data.get('status')}")
        print(f"  Completion: {data.get('completion_percentage')}%")
        
        # Step 2: Update some fields
        print("\n2. Updating bid card fields...")
        
        # Update project type
        update_payload = {
            "field_name": "project_type",
            "field_value": "deck_construction",
            "source": "test"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/cia/potential-bid-cards/{bid_card_id}/field",
            json=update_payload
        )
        
        if update_response.status_code == 200:
            update_data = update_response.json()
            print(f"✓ Updated project_type")
            print(f"  New completion: {update_data.get('completion_percentage')}%")
        else:
            print(f"✗ Failed to update: {update_response.status_code}")
            print(f"  Error: {update_response.text}")
        
        # Update location
        update_payload = {
            "field_name": "zip_code",
            "field_value": "10001",
            "source": "test"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/cia/potential-bid-cards/{bid_card_id}/field",
            json=update_payload
        )
        
        if update_response.status_code == 200:
            update_data = update_response.json()
            print(f"✓ Updated zip_code")
            print(f"  New completion: {update_data.get('completion_percentage')}%")
        
        # Step 3: Get final status
        print("\n3. Getting final bid card status...")
        status_response = requests.get(
            f"{BASE_URL}/api/cia/potential-bid-cards/{bid_card_id}"
        )
        
        if status_response.status_code == 200:
            final_data = status_response.json()
            print(f"✓ Final status retrieved")
            print(f"  Completion: {final_data.get('completion_percentage')}%")
            print(f"  Ready for conversion: {final_data.get('ready_for_conversion')}")
            print(f"  Fields collected: {list(final_data.get('fields_collected', {}).keys())}")
        
        return bid_card_id
            
    else:
        print(f"✗ Failed to create bid card: {response.status_code}")
        print(f"  Error: {response.text}")
        return None

def main():
    print("Testing direct potential bid card API")
    bid_card_id = test_direct_bid_card_creation()
    
    print("\n" + "=" * 60)
    if bid_card_id:
        print("✓ POTENTIAL BID CARD API WORKING")
        print(f"Successfully created and updated bid card: {bid_card_id}")
    else:
        print("✗ POTENTIAL BID CARD API NOT WORKING")

if __name__ == "__main__":
    main()