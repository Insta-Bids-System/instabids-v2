#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append('C:/Users/Not John Or Justin/Documents/instabids/ai-agents')

from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

print("TESTING DIRECT DATABASE SAVE WITH API STRUCTURE")
print("=" * 60)

# Load the exact same environment as the API
load_dotenv('C:/Users/Not John Or Justin/Documents/instabids/ai-agents/../.env', override=True)

# Initialize Supabase client exactly like the API
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")

print(f"Supabase URL: {supabase_url}")
print(f"Supabase key loaded: {bool(supabase_key)}")

if not supabase_url or not supabase_key:
    print("ERROR: Missing Supabase credentials")
    exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

# Use the EXACT same structure as the API with a real generated URL
generated_image_url = "https://oaidalleapiprodscus.blob.core.windows.net/private/test_proof.png"

# Create the exact record the API creates
vision_image_record = {
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",  # Demo user (now exists)
    "image_url": generated_image_url,
    "thumbnail_url": generated_image_url,
    "source": "url",
    "tags": ["vision", "ai_generated", "dream_space", "kitchen"],
    "ai_analysis": {
        "description": "AI-generated dream space combining current layout with inspiration elements",
        "style": "AI Transformation",
        "generated_from": {
            "current_image_id": "5d46e708-3f0c-4985-9617-68afd8e2892b",
            "ideal_image_id": "115f9265-e462-458f-a159-568790fc6941",
            "prompt": "Test proof prompt"
        }
    },
    "user_notes": "AI-generated vision of my transformed space",
    "category": "ideal",  # Changed from "vision" to "ideal" to match database constraint
    "position": 0
}

print("\nTesting EXACT API record structure...")
print(f"Board ID: {vision_image_record['board_id']}")
print(f"Homeowner ID: {vision_image_record['user_id']}")
print(f"Category: {vision_image_record['category']}")
print(f"Source: {vision_image_record['source']}")

try:
    print("\nAttempting database insert...")
    vision_result = supabase.table("inspiration_images").insert(vision_image_record).execute()
    
    if vision_result.data:
        print("SUCCESS: Vision image saved to database!")
        print(f"New image ID: {vision_result.data[0]['id']}")
        print(f"Created at: {vision_result.data[0]['created_at']}")
        print(f"Category: {vision_result.data[0]['category']}")
        print(f"Homeowner ID: {vision_result.data[0]['user_id']}")
        
        # Verify it appears in the API
        print(f"\nVerifying image appears in demo API...")
        import requests
        demo_response = requests.get('http://localhost:8008/api/demo/inspiration/images', 
                                   params={'board_id': '26cf972b-83e4-484c-98b6-a5d1a4affee3'})
        
        if demo_response.ok:
            demo_images = demo_response.json()
            print(f"Demo API now returns {len(demo_images)} images")
            
            # Find our test image
            test_images = [img for img in demo_images if img.get('id') == vision_result.data[0]['id']]
            if test_images:
                print("SUCCESS: Test image visible in demo API!")
            else:
                print("WARNING: Test image not visible in demo API")
        
        # Clean up
        print(f"\nCleaning up test image...")
        supabase.table("inspiration_images").delete().eq("id", vision_result.data[0]['id']).execute()
        print("Test image cleaned up")
        
        print(f"\nCONCLUSION: The API record structure works perfectly!")
        print(f"The issue must be in the API's exception handling or execution flow.")
        
    else:
        print("ERROR: Insert returned no data")
        
except Exception as e:
    print(f"ERROR: Database insert failed: {e}")
    print(f"Error type: {type(e)}")
    
    # Detailed error analysis
    error_str = str(e).lower()
    if 'policy' in error_str:
        print("ISSUE: Row Level Security policy blocking insert")
    elif 'constraint' in error_str:
        print("ISSUE: Database constraint violation")
    elif 'foreign key' in error_str:
        print("ISSUE: Foreign key constraint (missing referenced record)")
    elif 'unique' in error_str:
        print("ISSUE: Unique constraint violation")

print(f"\n" + "=" * 60)
print("DIRECT API SAVE TEST COMPLETE")
print("=" * 60)