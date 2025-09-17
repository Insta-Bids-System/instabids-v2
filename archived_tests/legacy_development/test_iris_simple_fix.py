#!/usr/bin/env python3
"""
Simple test for IRIS room_id fix
"""

import requests
import base64

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

def test_iris():
    base_url = "http://localhost:8008"
    
    print("Testing IRIS photo upload with room_id fix...")
    
    test_image_b64 = create_test_image()
    
    response = requests.post(f"{base_url}/api/iris/unified-chat", json={
        "user_id": "01087874-747b-4159-8735-5ebb8715ff84",  # JJ Thompson
        "session_id": "simple_fix_test", 
        "message": "Add this photo to my backyard",
        "images": [{"data": test_image_b64, "type": "png"}],
        "context_type": "property"
    }, timeout=60)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        resp_json = response.json()
        response_text = resp_json.get('response', '')
        print("Response:", response_text.replace("\u2705", "SUCCESS").replace("\u274c", "FAILED")[:100])
    else:
        print("Error:", response.status_code)

if __name__ == "__main__":
    test_iris()