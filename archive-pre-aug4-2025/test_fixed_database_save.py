#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append('C:/Users/Not John Or Justin/Documents/instabids/ai-agents')

from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

print("TESTING FIXED DATABASE SAVE WITH CORRECT CONSTRAINTS")
print("=" * 60)

# Load environment variables
load_dotenv('C:/Users/Not John Or Justin/Documents/instabids/.env', override=True)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Test with correct constraints: category="ideal", source="url"
test_timestamp = datetime.now().isoformat()
vision_image_record = {
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "image_url": "https://example.com/test_fixed_image.jpg",
    "thumbnail_url": "https://example.com/test_fixed_image.jpg",
    "source": "url",  # Changed from "ai_generated" to "url"
    "tags": ["vision", "ai_generated", "test", "fixed"],
    "ai_analysis": {
        "description": f"Test AI-generated image with fixed constraints at {test_timestamp}",
        "style": "AI Transformation",
        "generated_from": {
            "test": True,
            "timestamp": test_timestamp,
            "fixed_constraints": True
        }
    },
    "user_notes": f"AI-generated test image with fixed constraints created at {test_timestamp}",
    "category": "ideal",  # Using allowed category
    "position": 0
}

print("Step 1: Attempt insertion with FIXED constraints")
print("-" * 40)
print("  Category: 'ideal' (allowed)")
print("  Source: 'url' (allowed)")

try:
    print("Inserting test vision image with fixed constraints...")
    vision_result = supabase.table("inspiration_images").insert(vision_image_record).execute()
    
    if vision_result.data:
        print(f"SUCCESS: Test image inserted with fixed constraints!")
        print(f"New image ID: {vision_result.data[0]['id']}")
        print(f"Created at: {vision_result.data[0].get('created_at')}")
        print(f"Category: {vision_result.data[0].get('category')}")
        print(f"Source: {vision_result.data[0].get('source')}")
        new_image_id = vision_result.data[0]['id']
    else:
        print("WARNING: Insert returned no data")
        new_image_id = None
        
except Exception as e:
    print(f"ERROR: Failed to insert with fixed constraints: {e}")
    new_image_id = None

print(f"\nStep 2: Verify image appears in API")
print("-" * 40)

import requests
import time

time.sleep(2)  # Wait for database update

try:
    response = requests.get('http://localhost:8008/api/demo/inspiration/images', 
                          params={'board_id': '26cf972b-83e4-484c-98b6-a5d1a4affee3'})
    
    if response.ok:
        images = response.json()
        vision_images = [img for img in images if 'vision' in str(img.get('tags', [])).lower()]
        
        print(f"Total images: {len(images)}")
        print(f"Vision-tagged images: {len(vision_images)}")
        
        # Look for our test image
        test_images = [img for img in images if new_image_id and img.get('id') == new_image_id]
        
        if test_images:
            test_img = test_images[0]
            print(f"SUCCESS: Found our test image in API!")
            print(f"  ID: {test_img.get('id')}")
            print(f"  Category: {test_img.get('category')}")
            print(f"  Source: {test_img.get('source')}")
            print(f"  Tags: {test_img.get('tags')}")
        else:
            print("Test image not found in API response")
            
        print(f"\nAll vision-tagged images:")
        for i, img in enumerate(vision_images, 1):
            print(f"  {i}. ID: {img.get('id')}")
            print(f"     Category: {img.get('category')}")
            print(f"     Source: {img.get('source')}")
            print(f"     Created: {img.get('created_at')}")

    else:
        print(f"Error calling demo API: {response.status_code}")
        
except Exception as e:
    print(f"Error checking demo API: {e}")

print(f"\nStep 3: Clean up test image")
print("-" * 40)

if new_image_id:
    try:
        delete_result = supabase.table("inspiration_images").delete().eq("id", new_image_id).execute()
        print(f"Test image cleaned up successfully")
    except Exception as e:
        print(f"Error cleaning up: {e}")

print(f"\n" + "=" * 60)
print("FIXED DATABASE SAVE TEST COMPLETE")
print("=" * 60)