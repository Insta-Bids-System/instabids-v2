#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import sys

# Test image generation with proper encoding
print("Testing image generation API with proper encoding")
print("=" * 50)

try:
    # Test the image generation endpoint directly
    response = requests.post('http://localhost:8008/api/image-generation/generate-dream-space', 
        json={
            'board_id': '26cf972b-83e4-484c-98b6-a5d1a4affee3',
            'ideal_image_id': 'inspiration_1',
            'current_image_id': 'current_1',
            'user_preferences': 'modern white cabinets and stainless steel appliances'
        })

    print(f'Response status: {response.status_code}')
    if response.status_code == 200:
        result = response.json()
        print(f'Success: {result.get("success")}')
        print(f'Message: {result.get("message")}')
        print(f'Image URL: {result.get("generated_image_url", "")[:100]}...')
        print(f'Saved as vision: {result.get("saved_as_vision")}')
        print(f'Generation ID: {result.get("generation_id")}')
    else:
        print(f'Error response: {response.text[:500]}')
        
except Exception as e:
    print(f'Exception: {e}')