#!/usr/bin/env python3
"""
Debug Image Generation - Check what's happening
"""
import requests
import json

def test_generation_debug():
    """Test with detailed logging"""
    
    payload = {
        "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
        "ideal_image_id": "demo-inspiration-1", 
        "current_image_id": "demo-current-1",
        "user_preferences": "Modern industrial kitchen with exposed brick and pendant lighting"
    }
    
    print("Making generation request...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        "http://localhost:8008/api/image-generation/generate-dream-space",
        json=payload,
        timeout=60
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Check if there are server logs we can see
    return response.status_code == 200

if __name__ == "__main__":
    test_generation_debug()