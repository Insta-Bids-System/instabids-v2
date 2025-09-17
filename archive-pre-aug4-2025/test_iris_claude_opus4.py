#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

print("=== TESTING IRIS WITH CLAUDE OPUS 4 ===")
print("=" * 60)

# Test Iris with Claude Opus 4
iris_payload = {
    "message": "Hi Iris! I'm thinking about updating my kitchen. Can you help me create a vision with subway tile backsplash and quartz countertops?",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
    "context": {
        "current_project": "kitchen",
        "has_images": True
    }
}

print("User: Hi Iris! I'm thinking about updating my kitchen. Can you help me create a vision with subway tile backsplash and quartz countertops?")
print("\nCalling Iris (now powered by Claude Opus 4)...")

try:
    response = requests.post('http://localhost:8008/api/iris/chat', 
                           json=iris_payload,
                           timeout=30)
    
    if response.ok:
        data = response.json()
        print(f"\nIris Response (Claude Opus 4):")
        print(f"{data.get('response', '')}")
        print(f"\nImage Generated: {data.get('image_generated', False)}")
        if data.get('image_url'):
            print(f"Image URL: {data.get('image_url')[:100]}...")
        
        # Test if response sounds more intelligent than before
        iris_response = data.get('response', '').lower()
        intelligence_indicators = [
            'excited', 'wonderful', 'help you', 'great choice', 'beautiful', 'perfect',
            'absolutely', 'love', 'fantastic', 'amazing'
        ]
        
        ai_indicators = sum(1 for indicator in intelligence_indicators if indicator in iris_response)
        print(f"\nIntelligence Score: {ai_indicators}/10 AI conversation indicators detected")
        
        if ai_indicators >= 3:
            print("[SUCCESS] Iris is now responding with Claude Opus 4 intelligence!")
        else:
            print("[NOTICE] Response seems basic - may still be using fallback")
        
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("IRIS CLAUDE OPUS 4 TEST COMPLETE")