"""
Download placeholder images and start Leonardo testing immediately
Since we can't access chat images directly, this uses similar backyard images
"""

import requests
import os
from pathlib import Path

# Create test-images directory if it doesn't exist
test_dir = Path(r"C:\Users\Not John Or Justin\Documents\instabids\test-images")
test_dir.mkdir(exist_ok=True)

print("=" * 70)
print("SETTING UP TEST IMAGES")
print("=" * 70)
print()

# Use realistic backyard images as placeholders
# These represent similar scenes to what user described
BACKYARD_WITH_GOAL = "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1024&h=768&fit=crop"  # Backyard with grass
ARTIFICIAL_TURF = "https://images.unsplash.com/photo-1584464491033-06628f3a6b7b?w=1024&h=768&fit=crop"  # Green artificial turf

print("[IMPORTANT] Since we can't access your chat images directly,")
print("we'll use similar backyard images for testing.")
print()
print("After you save your ACTUAL images, replace these files:")
print(f"  {test_dir}\\backyard_current.jpg")
print(f"  {test_dir}\\turf_ideal.jpg")
print()

try:
    # Download backyard image
    print("Downloading backyard image...")
    response = requests.get(BACKYARD_WITH_GOAL)
    with open(test_dir / "backyard_current.jpg", "wb") as f:
        f.write(response.content)
    print("[SUCCESS] Saved backyard_current.jpg")
    
    # Download turf image
    print("Downloading turf reference...")
    response = requests.get(ARTIFICIAL_TURF)
    with open(test_dir / "turf_ideal.jpg", "wb") as f:
        f.write(response.content)
    print("[SUCCESS] Saved turf_ideal.jpg")
    
    print()
    print("[READY] Test images downloaded!")
    print()
    print("NOW RUNNING LEONARDO TESTS...")
    print("-" * 40)
    
    # Now run the test
    import subprocess
    subprocess.run(["python", r"C:\Users\Not John Or Justin\Documents\instabids\ai-agents\test_leonardo_perfect_turf.py"])
    
except Exception as e:
    print(f"[ERROR] Failed to download images: {e}")
    print()
    print("Please manually save your images from the chat as:")
    print(f"  1. {test_dir}\\backyard_current.jpg")
    print(f"  2. {test_dir}\\turf_ideal.jpg")