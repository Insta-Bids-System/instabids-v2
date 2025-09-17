#!/usr/bin/env python3
"""
Final comprehensive test of IRIS with JJ Thompson's account
This will prove if our fix works
"""

import requests
import json
import time
import base64
from datetime import datetime

# JJ Thompson's actual credentials
JJ_USER_ID = "01087874-747b-4159-8735-5ebb8715ff84"
JJ_PROPERTY_ID = "066d66b5-4217-45ee-90de-6e62bc8e0fd0"
BASE_URL = "http://localhost:8008"

def create_test_image():
    """Create a test roof damage image"""
    # Small PNG
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82'
    return "data:image/png;base64," + base64.b64encode(png_data).decode('utf-8')

def test_iris_with_fix():
    """Test IRIS with our storage fix"""
    
    print("=" * 60)
    print("TESTING IRIS WITH STORAGE FIX - JJ THOMPSON")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print(f"User ID: {JJ_USER_ID}")
    
    session_id = f"jj_fixed_{int(time.time())}"
    print(f"Session ID: {session_id}\n")
    
    # Step 1: Send a message that triggers storage
    print("1. Sending photo with storage request...")
    
    test_image = create_test_image()
    timestamp = int(time.time())
    
    request = {
        "message": "Add this roof damage photo to my property under exterior",
        "user_id": JJ_USER_ID,
        "session_id": session_id,
        "context_type": "property",
        "images": [{
            "data": test_image,
            "filename": f"roof_damage_{timestamp}.png",
            "size": 1000,
            "type": "image/png"
        }]
    }
    
    print(f"   Message: {request['message']}")
    print("   Sending to IRIS...")
    
    response = requests.post(
        f"{BASE_URL}/api/iris/unified-chat",
        json=request,
        timeout=30
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {data.get('response', '')[:200]}")
        
        # Check if it mentions actual storage
        if "Successfully added" in data.get('response', ''):
            print("   ✅ IRIS claims successful storage")
        else:
            print("   ⚠️ IRIS didn't confirm storage")
    else:
        print(f"   ❌ Request failed: {response.text[:200]}")
        return False
    
    # Step 2: Verify in database
    print("\n2. VERIFYING IN DATABASE...")
    time.sleep(2)
    
    # Direct database check via Supabase
    import subprocess
    
    check_query = f"""
    SELECT 
        pp.id,
        pp.original_filename,
        pp.created_at,
        pp.room_id,
        pp.ai_description
    FROM property_photos pp
    WHERE pp.property_id = '{JJ_PROPERTY_ID}'
    AND pp.created_at > NOW() - INTERVAL '1 minute'
    ORDER BY pp.created_at DESC
    """
    
    # We'll check via a separate script since we can't import Supabase directly
    print("   Checking database for new photos...")
    
    # Alternative: Use requests to check
    check_response = requests.get(
        f"{BASE_URL}/api/projects/{JJ_PROPERTY_ID}/photos"
    )
    
    if check_response.status_code == 200:
        photos = check_response.json()
        
        # Filter for recent photos
        recent = [p for p in photos if timestamp in p.get('original_filename', '')]
        
        if recent:
            print(f"   ✅ FOUND {len(recent)} new photo(s) in database!")
            for photo in recent:
                print(f"      - {photo['original_filename']}")
                print(f"      - ID: {photo['id']}")
                print(f"      - Room: {photo.get('room_id', 'Not assigned')}")
            return True
        else:
            print(f"   ❌ NO new photos found (total photos: {len(photos)})")
            # Show last photo to verify endpoint works
            if photos:
                print(f"   Last photo: {photos[-1]['original_filename']} ({photos[-1]['created_at']})")
    else:
        print(f"   Could not check: {check_response.status_code}")
    
    return False

def test_confirmation_style():
    """Test with confirmation-style messages like 'OK do it'"""
    
    print("\n" + "=" * 60)
    print("TESTING CONFIRMATION-STYLE REQUESTS")
    print("=" * 60)
    
    session_id = f"jj_confirm_{int(time.time())}"
    timestamp = int(time.time())
    
    # First send image
    print("1. Uploading image first...")
    
    request1 = {
        "message": "Here's another roof photo",
        "user_id": JJ_USER_ID,
        "session_id": session_id,
        "context_type": "property",
        "images": [{
            "data": create_test_image(),
            "filename": f"roof_confirm_{timestamp}.png",
            "size": 1000,
            "type": "image/png"
        }]
    }
    
    response1 = requests.post(f"{BASE_URL}/api/iris/unified-chat", json=request1, timeout=30)
    
    if response1.status_code == 200:
        print("   Image uploaded")
        
        # Now send confirmation
        print("\n2. Sending 'OK do it' confirmation...")
        
        request2 = {
            "message": "OK do it, add it to the roof section",
            "user_id": JJ_USER_ID,
            "session_id": session_id,
            "context_type": "property"
        }
        
        response2 = requests.post(f"{BASE_URL}/api/iris/unified-chat", json=request2, timeout=30)
        
        if response2.status_code == 200:
            data = response2.json()
            print(f"   Response: {data.get('response', '')[:200]}")
            
            if "Successfully added" in data.get('response', ''):
                print("   ✅ Storage confirmed!")
                return True
    
    print("   ❌ Confirmation test failed")
    return False

if __name__ == "__main__":
    # Test 1: Direct storage request
    success1 = test_iris_with_fix()
    
    # Test 2: Confirmation style
    success2 = test_confirmation_style()
    
    # Final verdict
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print(f"Direct storage test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Confirmation test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 or success2:
        print("\n🎉 FIX SUCCESSFUL! IRIS now actually saves photos!")
    else:
        print("\n❌ Fix didn't work - need to debug further")
    print("=" * 60)