#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append('C:/Users/Not John Or Justin/Documents/instabids/ai-agents')

from datetime import datetime
from supabase import create_client, Client

print("TESTING SUPABASE DATABASE INSERTION DIRECTLY")
print("=" * 50)

# Load environment variables
from dotenv import load_dotenv
load_dotenv('C:/Users/Not John Or Justin/Documents/instabids/.env', override=True)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")

print(f"Supabase URL: {supabase_url}")
print(f"Supabase key loaded: {bool(supabase_key)}")

if not supabase_url or not supabase_key:
    print("ERROR: Missing Supabase credentials")
    exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

print(f"\nStep 1: Test basic Supabase connection")
print("-" * 30)

try:
    # Try to read existing data first
    result = supabase.table("inspiration_images").select("*").eq("board_id", "26cf972b-83e4-484c-98b6-a5d1a4affee3").limit(5).execute()
    print(f"SUCCESS: Can read from inspiration_images table")
    print(f"Found {len(result.data)} existing images")
    
    for img in result.data:
        print(f"  - ID: {img.get('id')}, Category: {img.get('category')}")
        
except Exception as e:
    print(f"ERROR reading from database: {e}")

print(f"\nStep 2: Test inserting a new vision image")
print("-" * 30)

# Create a test vision image record
test_timestamp = datetime.now().isoformat()
vision_image_record = {
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "image_url": "https://example.com/test_image.jpg",
    "thumbnail_url": "https://example.com/test_image.jpg",
    "source": "ai_generated",
    "tags": ["vision", "ai_generated", "test"],
    "ai_analysis": {
        "description": f"Test image generated at {test_timestamp}",
        "style": "Test Style",
        "generated_from": {
            "test": True,
            "timestamp": test_timestamp
        }
    },
    "user_notes": f"Test vision image created at {test_timestamp}",
    "category": "vision",
    "position": 0
}

try:
    print("Attempting to insert test vision image...")
    vision_result = supabase.table("inspiration_images").insert(vision_image_record).execute()
    
    if vision_result.data:
        print(f"SUCCESS: Test image inserted!")
        print(f"New image ID: {vision_result.data[0]['id']}")
        print(f"Created at: {vision_result.data[0].get('created_at')}")
    else:
        print("WARNING: Insert returned no data")
        print(f"Result: {vision_result}")
        
except Exception as e:
    print(f"ERROR: Failed to insert vision image: {e}")
    print(f"Error type: {type(e)}")
    
    # Check if it's a permission issue
    if "permission" in str(e).lower() or "policy" in str(e).lower():
        print("This appears to be a Row Level Security (RLS) policy issue")
    elif "foreign key" in str(e).lower():
        print("This appears to be a foreign key constraint issue")
    elif "unique" in str(e).lower():
        print("This appears to be a unique constraint issue")

print(f"\nStep 3: Check if test image was saved")
print("-" * 30)

try:
    result = supabase.table("inspiration_images").select("*").eq("board_id", "26cf972b-83e4-484c-98b6-a5d1a4affee3").execute()
    vision_images = [img for img in result.data if img.get('category') == 'vision']
    
    print(f"Total vision images now: {len(vision_images)}")
    
    # Look for our test image
    test_images = [img for img in vision_images if 'test' in str(img.get('ai_analysis', {})).lower()]
    
    if test_images:
        print(f"SUCCESS: Found {len(test_images)} test image(s)")
        for img in test_images:
            print(f"  - ID: {img.get('id')}")
            print(f"    Created: {img.get('created_at')}")
    else:
        print("No test images found - insertion may have failed")

except Exception as e:
    print(f"ERROR checking for test image: {e}")

print(f"\n" + "=" * 50)
print("SUPABASE DIRECT TEST COMPLETE")
print("=" * 50)