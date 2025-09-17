#!/usr/bin/env python3
"""
Simple test to verify IRIS photo upload with debug logging
"""

import requests
import json
import base64

def create_test_image():
    """Create a simple test image as base64"""
    # Create a small valid PNG image (red 100x100 pixel)
    import io
    from PIL import Image
    
    # Create a simple red image
    img = Image.new('RGB', (100, 100), color='red')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return base64.b64encode(img_buffer.read()).decode('utf-8')

def test_iris_photo_storage():
    """Test IRIS photo storage with debug verification"""
    base_url = "http://localhost:8008"
    
    print("IRIS PHOTO STORAGE TEST")
    print("=" * 50)
    
    # Create test image
    print("Creating test image...")
    test_image_b64 = create_test_image()
    print(f"Test image created: {len(test_image_b64)} characters")
    
    # Test with message that should trigger storage
    response = requests.post(f"{base_url}/api/iris/unified-chat", json={
        "user_id": "01087874-747b-4159-8735-5ebb8715ff84",  # JJ Thompson
        "session_id": "photo_storage_test_v3", 
        "message": "Add this photo to my backyard",
        "images": [{"data": test_image_b64, "type": "png"}],
        "context_type": "property"
    }, timeout=30)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        resp_json = response.json()
        print(f"Response preview: {resp_json.get('response', '')[:150]}...")
        print(f"Success: {resp_json.get('success', 'not specified')}")
    else:
        print(f"Error: {response.text}")
    
    print("\nCheck backend logs for:")
    print("1. 'NEW CODE LOADED' - Confirms updated code")
    print("2. 'DIRECT STORAGE REQUEST DETECTED' - Confirms handler reached")
    print("3. 'Processing 1 images' - Confirms image processing")

if __name__ == "__main__":
    test_iris_photo_storage()