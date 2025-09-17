#!/usr/bin/env python3
"""
DEBUG IMAGE UPLOAD
Detailed debugging of image upload API response
"""

import requests
import base64
import uuid
import json
from PIL import Image, ImageDraw
import io
from config.service_urls import get_backend_url

def create_simple_test_image():
    """Create a simple test image"""
    img = Image.new('RGB', (200, 100), color='lightblue')
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), "Test Image", fill='black')
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def debug_image_upload():
    """Debug image upload with detailed logging"""
    
    print("DEBUG IMAGE UPLOAD")
    print("=" * 30)
    
    base_url = get_backend_url()
    
    # Test data
    image_data = create_simple_test_image()
    print(f"Created test image: {len(image_data)} bytes")
    
    # API request
    url = f"{base_url}/api/intelligent-messages/send-with-image"
    
    files = {
        'image': ('test.png', image_data, 'image/png')
    }
    
    data = {
        'content': 'Simple test message',
        'sender_type': 'contractor', 
        'sender_id': str(uuid.uuid4()),
        'bid_card_id': str(uuid.uuid4())
    }
    
    print(f"Sending to: {url}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            result = response.json()
            print(f"JSON Response: {json.dumps(result, indent=2)}")
        except:
            print(f"Raw Response: {response.text}")
            
    except Exception as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    debug_image_upload()