#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

print("=== TESTING DEMO API DIRECTLY ===")
print("=" * 60)

board_id = "26cf972b-83e4-484c-98b6-a5d1a4affee3"

# Test the demo API endpoint
print("1. Calling demo API...")
response = requests.get(f'http://localhost:8008/api/demo/inspiration/images?board_id={board_id}')

if response.ok:
    images = response.json()
    print(f"   API returned {len(images)} images")
    
    for i, img in enumerate(images):
        print(f"\n   Image {i+1}:")
        print(f"     ID: {img.get('id')}")
        print(f"     Tags: {img.get('tags')}")
        print(f"     URL: {img.get('image_url', '')[:100]}...")
        print(f"     Source: {img.get('source')}")
        print(f"     Category: {img.get('category')}")
        
        # Check if this is our Iris image
        if img.get('id') == "3b92f67e-2790-480a-875f-8586759bab86":
            print("     [THIS IS THE IRIS-GENERATED IMAGE!]")
            
    # Count vision images
    vision_images = [img for img in images if 'vision' in str(img.get('tags', [])).lower()]
    print(f"\n   Total vision images: {len(vision_images)}")
    
    if vision_images:
        print("\n=== VISION IMAGES FOUND ===")
        for v_img in vision_images:
            print(f"   - ID: {v_img.get('id')}")
            print(f"     Created: {v_img.get('created_at')}")
            print(f"     URL works: {requests.head(v_img.get('image_url', '')).ok if v_img.get('image_url') else False}")
    
else:
    print(f"   API Error: {response.status_code}")
    print(f"   Response: {response.text}")

print("\n2. Testing individual image URLs...")
# Test if the OpenAI URLs are still working
test_urls = [
    "https://oaidalleapiprodscus.blob.core.windows.net/private/org-tLB6HTyaZgCnGqK1sjqL4T4f/user-PmjgxJ0vJIobq9YBl3sEr3Uc/img-Q7wGq8p9ZnFXaVDvVp8e0kCG.png",
    "https://oaidalleapiprodscus.blob.core.windows.net/private/org-tLB6HTyaZgCnGqK1sjqL4T4f/user-PmjgxJ0vJIobq9YBl3sEr3Uc/img-abc123.png"
]

for url in test_urls:
    try:
        head_response = requests.head(url, timeout=5)
        print(f"   {url[:50]}... -> {head_response.status_code}")
    except:
        print(f"   {url[:50]}... -> TIMEOUT/ERROR")

print("\n" + "=" * 60)
print("DEMO API TEST COMPLETE")