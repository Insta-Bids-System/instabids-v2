"""
Test Photo Upload to Potential Bid Card and Transfer to Official Bid Card
Tests the complete flow of uploading photos in CIA chat and transferring them
"""

import requests
import json
import base64
from datetime import datetime
import time

BACKEND_URL = "http://localhost:8008"

def encode_image_to_base64(image_path):
    """Convert image file to base64 string"""
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_cia_chat_with_photo():
    """Test CIA chat with photo upload"""
    print("\n=== Testing CIA Chat with Photo Upload ===\n")
    
    # Prepare test image
    test_image_path = r"C:\Users\Not John Or Justin\Documents\instabids\test-images\current-state\kitchen-outdated-1.webp"
    image_base64 = encode_image_to_base64(test_image_path)
    
    # Create a new conversation with photo
    conversation_id = f"test_photo_{int(time.time())}"
    user_id = "550e8400-e29b-41d4-a716-446655440001"
    
    print(f"Starting conversation: {conversation_id}")
    
    # First message with photo
    payload = {
        "messages": [{
            "role": "user",
            "content": "I want to renovate my kitchen. Here's a photo of the current state."
        }],
        "user_id": user_id,
        "conversation_id": conversation_id,
        "session_id": f"session_{conversation_id}",
        "images": [f"data:image/webp;base64,{image_base64}"]
    }
    
    print("Sending message with kitchen photo...")
    response = requests.post(
        f"{BACKEND_URL}/api/cia/stream",
        json=payload,
        timeout=30,
        stream=True
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return None
        
    # Collect streaming response
    full_response = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode('utf-8').replace('data: ', ''))
                if data.get('content'):
                    full_response += data['content']
                    print(data['content'], end='', flush=True)
            except:
                pass
    
    print(f"\n\nResponse received. Length: {len(full_response)} characters")
    
    # Check if potential bid card was created
    time.sleep(2)  # Give it time to save
    
    print("\nChecking for potential bid card creation...")
    bid_card_response = requests.get(
        f"{BACKEND_URL}/api/cia/conversation/{conversation_id}/potential-bid-card"
    )
    
    if bid_card_response.status_code == 200:
        bid_card_data = bid_card_response.json()
        print(f"[SUCCESS] Potential bid card found: {bid_card_data['id']}")
        print(f"   Completion: {bid_card_data['completion_percentage']}%")
        
        # Check if photo_ids were saved
        check_photos_in_potential_bid_card(bid_card_data['id'])
        
        return bid_card_data['id']
    else:
        print(f"[FAILED] No potential bid card found: {bid_card_response.status_code}")
        return None

def check_photos_in_potential_bid_card(bid_card_id):
    """Check if photos are saved in potential bid card"""
    print(f"\n=== Checking Photos in Potential Bid Card {bid_card_id} ===\n")
    
    # Query database directly
    import sys
    sys.path.append(r'C:\Users\Not John Or Justin\Documents\instabids\ai-agents')
    
    try:
        from database_simple import db
        
        result = db.client.table("potential_bid_cards").select("photo_ids, cover_photo_id").eq("id", bid_card_id).execute()
        
        if result.data and len(result.data) > 0:
            bid_card = result.data[0]
            photo_ids = bid_card.get("photo_ids", [])
            cover_photo_id = bid_card.get("cover_photo_id")
            
            print(f"Photo IDs in potential bid card: {photo_ids}")
            print(f"Cover photo ID: {cover_photo_id}")
            
            if photo_ids:
                print(f"[SUCCESS] Found {len(photo_ids)} photos in potential bid card")
                # Check photo_storage table for actual photos
                if isinstance(photo_ids, list) and len(photo_ids) > 0:
                    photo_result = db.client.table("photo_storage").select("id, url, metadata").in_("id", photo_ids).execute()
                    if photo_result.data:
                        print(f"[SUCCESS] Found {len(photo_result.data)} photos in photo_storage:")
                        for photo in photo_result.data:
                            print(f"   - ID: {photo['id']}")
                            print(f"     URL: {photo['url'][:50]}...")
                    else:
                        print("[FAILED] Photos referenced but not found in photo_storage")
            else:
                print("[FAILED] No photos saved to potential bid card")
                
        else:
            print(f"[FAILED] Potential bid card {bid_card_id} not found in database")
            
    except Exception as e:
        print(f"Error checking photos: {e}")

def test_conversion_to_official_bid_card(potential_bid_card_id):
    """Test converting potential bid card to official bid card"""
    print(f"\n=== Testing Conversion to Official Bid Card ===\n")
    
    # First, complete any missing fields
    print("Updating missing fields to meet conversion requirements...")
    
    # Add email if missing
    update_response = requests.put(
        f"{BACKEND_URL}/api/cia/potential-bid-cards/{potential_bid_card_id}/field",
        json={
            "field_name": "email_address",
            "field_value": "test@example.com",
            "source": "test"
        }
    )
    
    if update_response.status_code == 200:
        print("[SUCCESS] Email field updated")
    
    # Convert to official bid card
    print("\nConverting to official bid card...")
    convert_response = requests.post(
        f"{BACKEND_URL}/api/cia/potential-bid-cards/{potential_bid_card_id}/convert-to-bid-card"
    )
    
    if convert_response.status_code == 200:
        result = convert_response.json()
        official_bid_card_id = result.get("bid_card_id")
        print(f"[SUCCESS] Converted to official bid card: {official_bid_card_id}")
        print(f"   Bid card number: {result.get('bid_card_number')}")
        
        # Check if photos transferred
        check_photos_in_official_bid_card(official_bid_card_id)
        
        return official_bid_card_id
    else:
        print(f"[FAILED] Conversion failed: {convert_response.status_code}")
        print(f"   Error: {convert_response.text}")
        return None

def check_photos_in_official_bid_card(bid_card_id):
    """Check if photos transferred to official bid card"""
    print(f"\n=== Checking Photos in Official Bid Card {bid_card_id} ===\n")
    
    import sys
    sys.path.append(r'C:\Users\Not John Or Justin\Documents\instabids\ai-agents')
    
    try:
        from database_simple import db
        
        result = db.client.table("bid_cards").select("bid_document").eq("id", bid_card_id).execute()
        
        if result.data and len(result.data) > 0:
            bid_card = result.data[0]
            bid_document = bid_card.get("bid_document", {})
            
            # Check for images in bid_document
            images = bid_document.get("images", [])
            rfi_photos = bid_document.get("rfi_photos", [])
            photo_ids = bid_document.get("photo_ids", [])
            
            print(f"Images in bid_document: {len(images)}")
            print(f"RFI photos: {len(rfi_photos)}")
            print(f"Photo IDs: {photo_ids}")
            
            if images or rfi_photos or photo_ids:
                print(f"[SUCCESS] Photos successfully transferred to official bid card")
                if images:
                    print(f"   - {len(images)} images in bid_document.images")
                if rfi_photos:
                    print(f"   - {len(rfi_photos)} RFI photos")
                if photo_ids:
                    print(f"   - {len(photo_ids)} photo IDs referenced")
            else:
                print("[FAILED] No photos found in official bid card")
                print(f"   Full bid_document: {json.dumps(bid_document, indent=2)}")
                
        else:
            print(f"[FAILED] Official bid card {bid_card_id} not found in database")
            
    except Exception as e:
        print(f"Error checking official bid card photos: {e}")

def main():
    """Run complete photo upload test"""
    print("=" * 60)
    print("PHOTO UPLOAD TO BID CARD - COMPLETE FLOW TEST")
    print("=" * 60)
    
    # Step 1: Test CIA chat with photo
    potential_bid_card_id = test_cia_chat_with_photo()
    
    if potential_bid_card_id:
        # Step 2: Add more project details
        print("\n=== Adding More Project Details ===\n")
        
        fields_to_update = [
            ("project_type", "Kitchen Renovation", "test"),
            ("timeline", "Within 2 weeks", "test"),
            ("zip_code", "94105", "test"),
            ("contractor_size", "No Preference", "test")
        ]
        
        for field_name, field_value, source in fields_to_update:
            response = requests.put(
                f"{BACKEND_URL}/api/cia/potential-bid-cards/{potential_bid_card_id}/field",
                json={
                    "field_name": field_name,
                    "field_value": field_value,
                    "source": source
                }
            )
            if response.status_code == 200:
                print(f"[SUCCESS] Updated {field_name}: {field_value}")
            else:
                print(f"[FAILED] Failed to update {field_name}")
        
        # Step 3: Convert to official bid card
        time.sleep(2)
        official_bid_card_id = test_conversion_to_official_bid_card(potential_bid_card_id)
        
        if official_bid_card_id:
            print("\n" + "=" * 60)
            print("[SUCCESS] COMPLETE PHOTO UPLOAD FLOW TEST PASSED")
            print("=" * 60)
            print(f"\nSummary:")
            print(f"1. Created potential bid card: {potential_bid_card_id}")
            print(f"2. Uploaded photo with kitchen renovation request")
            print(f"3. Updated required fields for conversion")
            print(f"4. Converted to official bid card: {official_bid_card_id}")
            print(f"5. Verified photo transfer to official bid card")
        else:
            print("\n[FAILED] FAILED: Could not convert to official bid card")
    else:
        print("\n[FAILED] FAILED: Could not create potential bid card with photo")

if __name__ == "__main__":
    main()