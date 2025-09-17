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

print("=== TESTING IRIS AGENT IMAGE GENERATION ===")
print("=" * 60)

# Get baseline image count
before_result = supabase.table('inspiration_images').select('*').eq('board_id', '26cf972b-83e4-484c-98b6-a5d1a4affee3').execute()
before_count = len(before_result.data)
print(f"Images before Iris conversation: {before_count}")

# Simulate user conversation with Iris
print("\n--- IRIS CONVERSATION ---")
print("User: Can you create a vision for my kitchen with modern farmhouse style? I'd love to see white shiplap walls and black metal fixtures")

iris_payload = {
    "message": "Can you create a vision for my kitchen with modern farmhouse style? I'd love to see white shiplap walls and black metal fixtures",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
    "context": {
        "current_project": "kitchen",
        "has_images": True
    }
}

print("\nSending to Iris...")
try:
    response = requests.post('http://localhost:8008/api/iris/chat', 
                           json=iris_payload,
                           timeout=30)
    
    if response.ok:
        iris_response = response.json()
        print(f"\nIris Response:")
        print(f"Message: {iris_response.get('message', '')[:200]}...")
        print(f"Image Generated: {iris_response.get('image_generated', False)}")
        print(f"Image URL: {iris_response.get('image_url', 'None')[:50] if iris_response.get('image_url') else 'None'}...")
        
        # Wait for database update
        time.sleep(3)
        
        # Check if new image was added
        after_result = supabase.table('inspiration_images').select('*').eq('board_id', '26cf972b-83e4-484c-98b6-a5d1a4affee3').execute()
        after_count = len(after_result.data)
        
        print(f"\nImages after Iris conversation: {after_count}")
        print(f"New images added: {after_count - before_count}")
        
        if after_count > before_count:
            # Get the newest image
            newest = sorted(after_result.data, key=lambda x: x.get('created_at', ''))[-1]
            
            print("\n=== IRIS-GENERATED IMAGE DETAILS ===")
            print(f"ID: {newest.get('id')}")
            print(f"Created: {newest.get('created_at')}")
            print(f"Tags: {newest.get('tags')}")
            
            # Get the prompt used
            ai_analysis = newest.get('ai_analysis', {})
            gen_from = ai_analysis.get('generated_from', {})
            dalle_prompt = gen_from.get('prompt', '')
            
            print(f"\nUser's Original Request:")
            print(f"  'Can you create a vision for my kitchen with modern farmhouse style?'")
            print(f"  'I'd love to see white shiplap walls and black metal fixtures'")
            
            print(f"\nExtracted Preferences in DALL-E Prompt:")
            # Check if user preferences made it into the prompt
            if 'modern farmhouse' in dalle_prompt.lower():
                print("  ✓ 'modern farmhouse' style detected in prompt")
            if 'shiplap' in dalle_prompt.lower():
                print("  ✓ 'white shiplap walls' detected in prompt")
            if 'black metal' in dalle_prompt.lower():
                print("  ✓ 'black metal fixtures' detected in prompt")
                
            print(f"\nFull DALL-E Prompt Generated:")
            print(f"  {dalle_prompt[:300]}...")
            
            print("\n✅ SUCCESS: Iris successfully generated image from conversation!")
        else:
            print("\n❌ No new image was created by Iris")
            
    else:
        print(f"\n❌ Iris Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 60)
print("END OF IRIS CONVERSATION TEST")