"""
Save user's actual backyard images for Leonardo testing
These are the REAL images the user provided in the chat
"""

import requests
import os
from pathlib import Path

# Create test-images directory if it doesn't exist
test_dir = Path(r"C:\Users\Not John Or Justin\Documents\instabids\test-images")
test_dir.mkdir(exist_ok=True)

print("=" * 70)
print("SAVING YOUR ACTUAL BACKYARD IMAGES")
print("=" * 70)
print()
print("[IMPORTANT] The user provided two images in the chat:")
print("1. Their current backyard with soccer goal and patchy grass")
print("2. The ideal artificial turf they want")
print()
print("Since I cannot directly access chat images, you need to:")
print()
print("OPTION 1: Save from the chat")
print("-" * 40)
print("1. Right-click on Image #1 (current backyard) in the chat")
print("2. Save as: C:\\Users\\Not John Or Justin\\Documents\\instabids\\test-images\\backyard_current.jpg")
print()
print("3. Right-click on Image #2 (ideal turf) in the chat")
print("4. Save as: C:\\Users\\Not John Or Justin\\Documents\\instabids\\test-images\\turf_ideal.jpg")
print()
print("OPTION 2: Provide URLs")
print("-" * 40)
print("If the images are hosted somewhere, provide the URLs here:")
print()

# Placeholder for manual URL entry if user has them hosted
BACKYARD_CURRENT_URL = ""  # User needs to provide
TURF_IDEAL_URL = ""  # User needs to provide

if BACKYARD_CURRENT_URL and TURF_IDEAL_URL:
    print("Downloading from provided URLs...")
    
    # Download current backyard
    response = requests.get(BACKYARD_CURRENT_URL)
    with open(test_dir / "backyard_current.jpg", "wb") as f:
        f.write(response.content)
    print("[SUCCESS] Saved backyard_current.jpg")
    
    # Download ideal turf
    response = requests.get(TURF_IDEAL_URL)
    with open(test_dir / "turf_ideal.jpg", "wb") as f:
        f.write(response.content)
    print("[SUCCESS] Saved turf_ideal.jpg")
else:
    print("[WAITING] Please save the images manually as instructed above")
    print()
    print("Expected files:")
    print(f"  {test_dir}\\backyard_current.jpg")
    print(f"  {test_dir}\\turf_ideal.jpg")
    print()
    print("Once saved, run: python test_leonardo_real_backyard_now.py")