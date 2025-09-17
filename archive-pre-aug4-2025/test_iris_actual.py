#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv('.env', override=True)
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

print("=== TESTING ACTUAL IRIS AGENT ===")
print("=" * 60)

# Count images before
before = supabase.table('inspiration_images').select('*').eq('board_id', '26cf972b-83e4-484c-98b6-a5d1a4affee3').execute()
before_count = len(before.data)
print(f"Images before: {before_count}")

# Test Iris
iris_payload = {
    "message": "I want to see my kitchen with modern industrial style. Can you create a vision with exposed brick walls and black metal pendant lights over the island?",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
    "context": {
        "current_project": "kitchen",
        "has_images": True
    }
}

print("\nCalling Iris...")
try:
    response = requests.post('http://localhost:8008/api/iris/chat', 
                           json=iris_payload,
                           timeout=60)
    
    print(f"Response status: {response.status_code}")
    
    if response.ok:
        data = response.json()
        print(f"\nIris Response: {data.get('response', '')[:200]}...")
        print(f"Image Generated: {data.get('image_generated', False)}")
        print(f"Image URL: {data.get('image_url', 'None')}")
        
        # Wait and check database
        time.sleep(3)
        
        after = supabase.table('inspiration_images').select('*').eq('board_id', '26cf972b-83e4-484c-98b6-a5d1a4affee3').execute()
        after_count = len(after.data)
        
        print(f"\nImages after: {after_count}")
        print(f"New images: {after_count - before_count}")
        
        if after_count > before_count:
            newest = sorted(after.data, key=lambda x: x.get('created_at', ''))[-1]
            print(f"\nNEW IMAGE CREATED BY IRIS!")
            print(f"ID: {newest.get('id')}")
            print(f"Tags: {newest.get('tags')}")
        else:
            print("\nNO NEW IMAGE - IRIS FAILED TO GENERATE")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")