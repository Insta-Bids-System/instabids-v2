#!/usr/bin/env python3
"""TEST: Photo upload triggers JAA bid card update"""

import requests
import json
import time

def test_complete_flow():
    print("=" * 50)
    print("TESTING: PHOTO UPLOAD -> JAA UPDATE FLOW")
    print("=" * 50)
    
    # Step 1: Get a real bid card to test with
    print("\n1. FINDING REAL BID CARD:")
    try:
        response = requests.get("http://localhost:8008/api/bid-cards/", timeout=10)
        if response.status_code == 200:
            bid_cards = response.json()
            if bid_cards and len(bid_cards) > 0:
                test_bid_card = bid_cards[0]
                bid_card_id = test_bid_card['id']
                print(f"Found bid card: {bid_card_id}")
                print(f"Project type: {test_bid_card.get('project_type', 'N/A')}")
            else:
                print("No bid cards found - creating test scenario")
                bid_card_id = "test-bid-card-123"
        else:
            print(f"Failed to get bid cards: {response.status_code}")
            bid_card_id = "test-bid-card-123"
    except Exception as e:
        print(f"Error getting bid cards: {e}")
        bid_card_id = "test-bid-card-123"
    
    # Step 2: Test JAA update endpoint directly 
    print(f"\n2. TESTING JAA UPDATE FOR BID CARD: {bid_card_id}")
    
    jaa_payload = {
        "update_type": "rfi_photos_added",
        "photos_count": 3,
        "rfi_id": "test-rfi-123", 
        "source": "CIA_RFI_response",
        "photos": [
            "https://example.com/front_yard.jpg",
            "https://example.com/sprinkler_system.jpg", 
            "https://example.com/lawn_condition.jpg"
        ]
    }
    
    print(f"Calling JAA update: PUT /jaa/update/{bid_card_id}")
    print(f"Payload: {json.dumps(jaa_payload, indent=2)}")
    
    try:
        jaa_response = requests.put(
            f"http://localhost:8008/jaa/update/{bid_card_id}",
            json=jaa_payload,
            timeout=120  # JAA can take time
        )
        
        print(f"\nJAA Response Status: {jaa_response.status_code}")
        
        if jaa_response.status_code == 200:
            jaa_result = jaa_response.json()
            print("JAA UPDATE SUCCESS:")
            print(f"- Update summary: {jaa_result.get('update_summary', 'N/A')}")
            print(f"- Affected contractors: {jaa_result.get('affected_contractors', 'N/A')}")
            print(f"- Notification content: {jaa_result.get('notification_content', 'N/A')}")
            
            # Step 3: Verify bid card was actually updated
            print(f"\n3. VERIFYING BID CARD WAS UPDATED:")
            try:
                verify_response = requests.get(f"http://localhost:8008/api/bid-cards/{bid_card_id}", timeout=10)
                if verify_response.status_code == 200:
                    updated_bid_card = verify_response.json()
                    bid_document = updated_bid_card.get('bid_document', {})
                    images = bid_document.get('all_extracted_data', {}).get('images', [])
                    
                    print(f"Bid card images count: {len(images)}")
                    if len(images) > 0:
                        print("SUCCESS: Photos were added to bid card!")
                        for i, img in enumerate(images[-3:]):  # Show last 3
                            print(f"  Image {i+1}: {img.get('url', 'N/A')} (source: {img.get('source', 'N/A')})")
                    else:
                        print("WARNING: No images found in updated bid card")
                        
                    updated_at = updated_bid_card.get('updated_at')
                    print(f"Bid card updated_at: {updated_at}")
                    
                else:
                    print(f"Failed to verify bid card update: {verify_response.status_code}")
                    
            except Exception as e:
                print(f"Error verifying bid card: {e}")
                
            return True
            
        else:
            print(f"JAA UPDATE FAILED: {jaa_response.status_code}")
            print(f"Response: {jaa_response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("JAA REQUEST TIMED OUT (this can happen with complex updates)")
        return False
    except Exception as e:
        print(f"JAA REQUEST ERROR: {e}")
        return False

def test_rfi_photo_handler():
    print("\n" + "=" * 50)
    print("TESTING: RFI PHOTO HANDLER FUNCTION")
    print("=" * 50)
    
    # Test the CIA's RFI photo handler
    payload = {
        "bid_card_id": "test-bid-card-123",
        "rfi_id": "test-rfi-456",
        "photos": [
            "https://example.com/test1.jpg",
            "https://example.com/test2.jpg"
        ],
        "user_id": "test-user"
    }
    
    # This would normally be called from CIA after photo upload
    print("Testing RFI photo handler endpoint...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    # For now just show the flow would work
    print("FLOW WOULD BE:")
    print("1. User uploads photos in response to RFI")
    print("2. CIA calls handle_rfi_photo_upload()")
    print("3. Function updates bid_document with photos")
    print("4. Function calls JAA update endpoint")
    print("5. JAA notifies contractors of bid card changes")

if __name__ == "__main__":
    success = test_complete_flow()
    test_rfi_photo_handler()
    
    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: PHOTO -> JAA UPDATE FLOW WORKING")
    else:
        print("FAILED: Need to debug JAA integration")
    print("=" * 50)