#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time

print("TESTING DATABASE SAVE FUNCTIONALITY")
print("=" * 50)

base_url = 'http://localhost:8008'
board_id = '26cf972b-83e4-484c-98b6-a5d1a4affee3'

print("Step 1: Check current images in database")
print("-" * 30)

# Get current count
response = requests.get(f'{base_url}/api/demo/inspiration/images', 
                      params={'board_id': board_id})

if response.ok:
    images = response.json()
    vision_images = [img for img in images if img.get('category') == 'vision']
    initial_count = len(vision_images)
    print(f"Current vision images in database: {initial_count}")
    
    for i, img in enumerate(vision_images, 1):
        print(f"  {i}. ID: {img.get('id')}")
        print(f"     Created: {img.get('created_at')}")

else:
    print(f"Error getting images: {response.status_code}")
    initial_count = 0

print(f"\nStep 2: Generate new image with detailed logging")
print("-" * 30)

# Generate a new image with unique identifier
unique_test = f"TEST_{int(time.time())}"
response = requests.post(f'{base_url}/api/image-generation/generate-dream-space', 
    json={
        'board_id': board_id,
        'ideal_image_id': 'inspiration_1',
        'current_image_id': 'current_1',
        'user_preferences': f'{unique_test}: modern kitchen with unique subway tile pattern'
    })

if response.status_code == 200:
    result = response.json()
    print(f"Generation successful: {result.get('success')}")
    print(f"Generation ID: {result.get('generation_id')}")
    print(f"Saved as vision: {result.get('saved_as_vision')}")
    print(f"Message: {result.get('message')}")
    generation_id = result.get('generation_id')
else:
    print(f"Generation failed: {response.status_code}")
    print(response.text)
    generation_id = None

print(f"\nStep 3: Check if image was actually saved")
print("-" * 30)

# Wait for database update
time.sleep(5)

response = requests.get(f'{base_url}/api/demo/inspiration/images', 
                      params={'board_id': board_id})

if response.ok:
    images = response.json()
    vision_images = [img for img in images if img.get('category') == 'vision']
    new_count = len(vision_images)
    
    print(f"Vision images after generation: {new_count}")
    print(f"Expected increase: 1, Actual increase: {new_count - initial_count}")
    
    if new_count > initial_count:
        print("SUCCESS: New image was saved to database!")
        
        # Find the newest image
        newest_image = max(vision_images, key=lambda x: x.get('created_at', ''))
        print(f"Newest image:")
        print(f"  ID: {newest_image.get('id')}")
        print(f"  Created: {newest_image.get('created_at')}")
        print(f"  URL: {newest_image.get('image_url', '')[:100]}...")
        
        # Check if it contains our unique test identifier
        ai_analysis = newest_image.get('ai_analysis', {})
        if unique_test in str(ai_analysis):
            print(f"CONFIRMED: Found our test identifier '{unique_test}' in the image data!")
        else:
            print(f"WARNING: Could not find test identifier '{unique_test}' in image data")
            
    else:
        print("PROBLEM: No new image was saved to database")
        print("This indicates the database save operation is failing")
        
        print("\nAll current vision images:")
        for i, img in enumerate(vision_images, 1):
            print(f"  {i}. ID: {img.get('id')}")
            print(f"     Created: {img.get('created_at')}")
            print(f"     User Notes: {img.get('user_notes', 'None')}")

else:
    print(f"Error checking database: {response.status_code}")

print(f"\nStep 4: Test with direct database query")
print("-" * 30)

# Try to get more detailed info about what's in the database
try:
    response = requests.get(f'{base_url}/api/demo/inspiration/images', 
                          params={'board_id': board_id})
    
    if response.ok:
        all_images = response.json()
        print(f"Total images on board: {len(all_images)}")
        
        categories = {}
        for img in all_images:
            cat = img.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
            
        print("Images by category:")
        for cat, count in categories.items():
            print(f"  {cat}: {count}")
            
except Exception as e:
    print(f"Database query error: {e}")

print(f"\n" + "=" * 50)
print("DATABASE SAVE TEST COMPLETE")
print("=" * 50)