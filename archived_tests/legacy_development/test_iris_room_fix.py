#!/usr/bin/env python3
"""
Test IRIS photo upload with room_id fix
"""

import requests
import json
import base64
import sys

def create_test_image():
    """Create a simple test image as base64"""
    import io
    from PIL import Image
    
    # Create a simple red image
    img = Image.new('RGB', (100, 100), color='red')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return base64.b64encode(img_buffer.read()).decode('utf-8')

def test_iris_room_fix():
    """Test IRIS photo storage with room_id fix"""
    base_url = "http://localhost:8008"
    
    print("=== IRIS PHOTO ROOM FIX TEST ===")
    
    # Create test image
    print("Creating test image...")
    test_image_b64 = create_test_image()
    print(f"Test image created: {len(test_image_b64)} characters")
    
    # Test with message that should detect backyard and get room_id
    try:
        print("Sending photo upload request...")
        response = requests.post(f"{base_url}/api/iris/unified-chat", json={
            "user_id": "01087874-747b-4159-8735-5ebb8715ff84",  # JJ Thompson
            "session_id": "room_fix_test", 
            "message": "Add this photo to my backyard",
            "images": [{"data": test_image_b64, "type": "png"}],
            "context_type": "property"
        }, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            resp_json = response.json()
            response_text = resp_json.get('response', '')
            
            # Check for success
            print("Response:", response_text[:200])
            
            if "Successfully saved" in response_text:
                print("✅ SUCCESS: Photo upload worked!")
                
                # Now check if the photo was saved with correct room_id
                print("\nChecking database for room_id...")
                import os
                import sys
                sys.path.append('/Users/Not John Or Justin/Documents/instabids/ai-agents')
                
                try:
                    from database_simple import db
                    
                    # Check recent photos for this user's property
                    photos_result = db.client.table("property_photos").select("id, property_id, room_id, ai_description, created_at").eq("property_id", "066d66b5-4217-45ee-90de-6e62bc8e0fd0").order("created_at", desc=True).limit(3).execute()
                    
                    if photos_result.data:
                        print(f"Found {len(photos_result.data)} recent photos:")
                        for i, photo in enumerate(photos_result.data):
                            print(f"  Photo {i+1}:")
                            print(f"    ID: {photo['id']}")
                            print(f"    Room ID: {photo['room_id']}")
                            print(f"    Description: {photo['ai_description']}")
                            print(f"    Created: {photo['created_at']}")
                            
                            if photo['room_id']:
                                print(f"    ✅ Has room_id: {photo['room_id']}")
                            else:
                                print(f"    ❌ No room_id (still NULL)")
                            print()
                    else:
                        print("❌ No photos found in database")
                        
                except Exception as e:
                    print(f"❌ Database check failed: {e}")
                
            else:
                print("❌ Upload may have failed")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text[:200])
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_iris_room_fix()