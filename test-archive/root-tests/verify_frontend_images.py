#!/usr/bin/env python3
"""
Verify frontend can display all 3 image categories
"""
import webbrowser

print("OPENING FRONTEND TO VERIFY IMAGES")
print("=" * 50)

# Open the frontend
url = "http://localhost:5174"
print(f"Opening browser to: {url}")
webbrowser.open(url)

print("\nMANUAL VERIFICATION STEPS:")
print("1. Click 'Login as Demo User' button") 
print("2. Click 'Inspiration' in the navigation")
print("3. You should see 3 columns:")
print("   - Current Space (left): Outdated kitchen")
print("   - Inspiration (middle): Modern industrial kitchen")
print("   - My Vision (right): AI-generated dream kitchen")
print("\nThe 'My Vision' column should show the AI-generated image")
print("with a 'Start Project from Vision' button below it.")

# Also show backend status
import requests
response = requests.get("http://localhost:8008/api/demo/inspiration/images?board_id=26cf972b-83e4-484c-98b6-a5d1a4affee3")
if response.status_code == 200:
    images = response.json()
    print(f"\nBACKEND STATUS: Serving {len(images)} images")
    vision_images = [img for img in images if "vision" in img.get("tags", [])]
    if vision_images:
        print("CONFIRMED: Vision/AI image is in backend API")
        print(f"Vision image URL: {vision_images[0]['image_url'][:60]}...")
    else:
        print("ERROR: No vision images found in backend!")