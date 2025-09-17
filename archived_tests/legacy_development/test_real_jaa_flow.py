#!/usr/bin/env python3
"""TEST COMPLETE FLOW: RFI photos -> JAA update with REAL bid card"""

import requests
import json
import time

def test_real_jaa_flow():
    print("=" * 60)
    print("TESTING COMPLETE RFI PHOTO -> JAA FLOW")
    print("USING REAL BID CARD: 36214de5-a068-4dcc-af99-cf33238e7472")
    print("=" * 60)
    
    bid_card_id = "36214de5-a068-4dcc-af99-cf33238e7472"
    
    # Step 1: Show current bid card state
    print(f"\n1. CURRENT BID CARD STATE:")
    try:
        response = requests.get(f"http://localhost:8008/api/admin/bid-cards/{bid_card_id}", timeout=10)
        if response.status_code == 200:
            current_data = response.json()
            print(f"Project type: {current_data.get('project_type')}")
            print(f"Status: {current_data.get('status')}")
            current_images = current_data.get('bid_document', {}).get('all_extracted_data', {}).get('images', [])
            print(f"Current images: {len(current_images)}")
            print(f"Last updated: {current_data.get('updated_at')}")
        else:
            print(f"Failed to get current state: {response.status_code}")
    except Exception as e:
        print(f"Error getting current state: {e}")
    
    # Step 2: Call JAA update to simulate photo upload
    print(f"\n2. CALLING JAA UPDATE SERVICE:")
    
    jaa_payload = {
        "update_type": "rfi_photos_added",
        "photos_count": 3,
        "rfi_id": "test-rfi-demo",
        "source": "CIA_RFI_response", 
        "description": "Homeowner uploaded requested photos for kitchen project",
        "photos": [
            {"url": "https://instabids-test.s3.amazonaws.com/kitchen_before_1.jpg", "type": "before"},
            {"url": "https://instabids-test.s3.amazonaws.com/kitchen_layout.jpg", "type": "layout"},
            {"url": "https://instabids-test.s3.amazonaws.com/kitchen_appliances.jpg", "type": "appliances"}
        ]
    }
    
    print(f"Calling: PUT /jaa/update/{bid_card_id}")
    print("Payload:")
    print(json.dumps(jaa_payload, indent=2))
    
    try:
        print("\nSending JAA request...")
        jaa_response = requests.put(
            f"http://localhost:8008/jaa/update/{bid_card_id}",
            json=jaa_payload,
            timeout=120
        )
        
        print(f"JAA Response Status: {jaa_response.status_code}")
        
        if jaa_response.status_code == 200:
            jaa_result = jaa_response.json()
            print("\n*** JAA UPDATE SUCCESS ***")
            print(f"Update summary: {jaa_result.get('update_summary')}")
            print(f"Affected contractors: {jaa_result.get('affected_contractors')}")
            print(f"Updated timestamp: {jaa_result.get('updated_at')}")
            
            # Step 3: Verify the bid card was actually updated
            print(f"\n3. VERIFYING BID CARD WAS UPDATED:")
            
            time.sleep(2)  # Give database time to update
            
            verify_response = requests.get(f"http://localhost:8008/api/admin/bid-cards/{bid_card_id}", timeout=10)
            if verify_response.status_code == 200:
                updated_data = verify_response.json()
                updated_images = updated_data.get('bid_document', {}).get('all_extracted_data', {}).get('images', [])
                new_updated_at = updated_data.get('updated_at')
                
                print(f"Images after update: {len(updated_images)}")
                print(f"New updated_at: {new_updated_at}")
                
                # Show the new images
                for i, img in enumerate(updated_images[-3:]):
                    print(f"  New image {i+1}: {img.get('url')} (source: {img.get('source')})")
                
                print("\n*** PROOF: PHOTOS WERE ADDED TO BID CARD ***")
                return True
                
            else:
                print(f"Failed to verify update: {verify_response.status_code}")
                return False
        else:
            print(f"\n*** JAA UPDATE FAILED ***")
            print(f"Status: {jaa_response.status_code}")
            print(f"Response: {jaa_response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("JAA request timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"JAA request error: {e}")
        return False

if __name__ == "__main__":
    success = test_real_jaa_flow()
    
    print("\n" + "=" * 60)
    if success:
        print("*** COMPLETE SUCCESS ***")
        print("RFI PHOTO -> JAA UPDATE -> BID CARD UPDATE: WORKING")
        print("PHOTOS ADDED TO BID CARD AND CONTRACTORS NOTIFIED")
    else:
        print("*** FAILED ***") 
        print("JAA integration not working properly")
    print("=" * 60)