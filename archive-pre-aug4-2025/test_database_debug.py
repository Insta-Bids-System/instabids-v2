#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append('C:/Users/Not John Or Justin/Documents/instabids/ai-agents')

from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import requests

print("DEBUGGING DATABASE SAVE ISSUE")
print("=" * 50)

# Load environment variables
load_dotenv('C:/Users/Not John Or Justin/Documents/instabids/.env', override=True)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

print("Step 1: Test the EXACT same record structure that worked before")
print("-" * 50)

# Use the exact same structure that worked in our earlier test
vision_image_record = {
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "image_url": "https://example.com/debug_test.jpg",
    "thumbnail_url": "https://example.com/debug_test.jpg",
    "source": "url",  # Known to work
    "tags": ["vision", "ai_generated", "debug"],
    "ai_analysis": {
        "description": "Debug test image",
        "style": "Test",
        "generated_from": {"debug": True}
    },
    "user_notes": "Debug test image",
    "category": "ideal",  # Known to work
    "position": 0
}

print("Attempting to insert debug test record...")
try:
    result = supabase.table("inspiration_images").insert(vision_image_record).execute()
    
    if result.data:
        print(f"SUCCESS: Debug record inserted!")
        print(f"ID: {result.data[0]['id']}")
        new_id = result.data[0]['id']
        
        # Clean up immediately
        supabase.table("inspiration_images").delete().eq("id", new_id).execute()
        print("Cleaned up debug record")
    else:
        print("FAILED: No data returned")
        
except Exception as e:
    print(f"ERROR: {e}")
    print(f"Error type: {type(e)}")

print("\nStep 2: Test with OpenAI URL from recent API call")
print("-" * 50)

# Test with an actual OpenAI URL format
openai_url_record = {
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "image_url": "https://oaidalleapiprodscus.blob.core.windows.net/private/test.png",
    "thumbnail_url": "https://oaidalleapiprodscus.blob.core.windows.net/private/test.png",
    "source": "url",
    "tags": ["vision", "ai_generated", "debug", "openai"],
    "ai_analysis": {
        "description": "Debug test with OpenAI URL format",
        "style": "Test",
        "generated_from": {"debug": True, "url_type": "openai"}
    },
    "user_notes": "Debug test with OpenAI URL",
    "category": "ideal",
    "position": 0
}

print("Attempting to insert OpenAI URL format record...")
try:
    result = supabase.table("inspiration_images").insert(openai_url_record).execute()
    
    if result.data:
        print(f"SUCCESS: OpenAI URL record inserted!")
        print(f"ID: {result.data[0]['id']}")
        new_id = result.data[0]['id']
        
        # Clean up immediately
        supabase.table("inspiration_images").delete().eq("id", new_id).execute()
        print("Cleaned up OpenAI URL record")
    else:
        print("FAILED: No data returned")
        
except Exception as e:
    print(f"ERROR: {e}")
    print(f"Error type: {type(e)}")

print("\nStep 3: Check current database state")
print("-" * 50)

try:
    result = supabase.table("inspiration_images").select("*").eq("board_id", "26cf972b-83e4-484c-98b6-a5d1a4affee3").execute()
    print(f"Current images in database: {len(result.data)}")
    
    for img in result.data:
        print(f"  - {img.get('id')}: {img.get('category')} / {img.get('source')} / created: {img.get('created_at')[:19]}")
        
except Exception as e:
    print(f"Error checking database: {e}")

print("\nStep 4: Make API call and check for new image immediately")
print("-" * 50)

# Get current count
try:
    before_result = supabase.table("inspiration_images").select("*").eq("board_id", "26cf972b-83e4-484c-98b6-a5d1a4affee3").execute()
    before_count = len(before_result.data)
    print(f"Images before API call: {before_count}")
except:
    before_count = 0

# Make API call
payload = {
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
    "ideal_image_id": "115f9265-e462-458f-a159-568790fc6941",
    "current_image_id": "5d46e708-3f0c-4985-9617-68afd8e2892b",
    "user_preferences": "Debug test call"
}

try:
    print("Making API call to image generation...")
    api_response = requests.post('http://localhost:8008/api/image-generation/generate-dream-space', 
                                json=payload, timeout=30)
    
    if api_response.ok:
        api_data = api_response.json()
        print(f"API Response: Success={api_data.get('success')}, Saved={api_data.get('saved_as_vision')}")
    else:
        print(f"API Error: {api_response.status_code}")
        
except Exception as e:
    print(f"API Call Error: {e}")

# Check count after
import time
time.sleep(2)  # Wait for database update

try:
    after_result = supabase.table("inspiration_images").select("*").eq("board_id", "26cf972b-83e4-484c-98b6-a5d1a4affee3").execute()
    after_count = len(after_result.data)
    print(f"Images after API call: {after_count}")
    
    if after_count > before_count:
        print(f"SUCCESS: {after_count - before_count} new image(s) added!")
        # Show newest image
        newest = sorted(after_result.data, key=lambda x: x.get('created_at', ''))[-1]
        print(f"Newest image: {newest.get('id')}")
        print(f"  Created: {newest.get('created_at')}")
        print(f"  Category: {newest.get('category')}")
        print(f"  Source: {newest.get('source')}")
        print(f"  Tags: {newest.get('tags')}")
    else:
        print("ISSUE: No new images added despite API success")
        
except Exception as e:
    print(f"Error checking after API call: {e}")

print("\n" + "=" * 50)
print("DATABASE DEBUG COMPLETE")
print("=" * 50)