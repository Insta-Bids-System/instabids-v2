#!/usr/bin/env python3
"""
Fix the demo board to show actual generated vision image
"""
import requests
import json
from datetime import datetime

print("FIXING DEMO VISION IMAGE")
print("=" * 50)

# Step 1: Generate a new vision image through the API
print("\n1. Generating new vision image...")
generation_payload = {
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
    "ideal_image_id": "demo-inspiration-1",
    "current_image_id": "demo-current-1",
    "user_preferences": "Modern industrial kitchen with exposed brick wall and pendant lighting from my inspiration"
}

try:
    response = requests.post(
        "http://localhost:8008/api/image-generation/generate-dream-space",
        json=generation_payload,
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        generated_url = result.get("generated_image_url", "")
        print(f"SUCCESS: Generated new image")
        print(f"URL: {generated_url[:80]}...")
        
        # Step 2: Update the demo_boards.py to return this specific image
        print("\n2. Updating demo_boards.py to use this generated image...")
        
        # Read the current file
        with open("Documents/instabids/ai-agents/api/demo_boards.py", "r") as f:
            content = f.read()
        
        # Replace the hardcoded Unsplash URL with the generated one
        old_url = 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80'
        
        if generated_url and generated_url != old_url:
            content = content.replace(old_url, generated_url)
            
            # Write back
            with open("Documents/instabids/ai-agents/api/demo_boards.py", "w") as f:
                f.write(content)
            
            print("SUCCESS: Updated demo_boards.py with new generated image URL")
            print("\n3. The demo board will now show the newly generated image!")
            print("\nNOTE: You may need to restart the backend server for changes to take effect")
        else:
            print("NOTICE: Generated URL is same as existing or empty")
            
    else:
        print(f"FAIL: Generation failed: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "="*50)
print("To see the change:")
print("1. Restart backend if needed")
print("2. Go to http://localhost:5174")
print("3. Login as Demo User")
print("4. Navigate to Inspiration")
print("5. The 'My Vision' column should show the new generated image")