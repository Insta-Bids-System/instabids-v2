"""
Copy both actual images and confirm they're saved
"""

import shutil
from pathlib import Path

print("=" * 60)
print("SAVING YOUR ACTUAL IMAGES")
print("=" * 60)

# Source paths (your actual images)
backyard_source = r"C:\Users\Not John Or Justin\Downloads\Lawn-repair.jpg"
turf_source = r"C:\Users\Not John Or Justin\Pictures\download (4).jpeg"

# Destination paths
backyard_dest = r"C:\Users\Not John Or Justin\Documents\instabids\test-images\YOUR_ACTUAL_BACKYARD.jpg"
turf_dest = r"C:\Users\Not John Or Justin\Documents\instabids\test-images\YOUR_IDEAL_TURF.jpg"

# Copy backyard image
try:
    if Path(backyard_source).exists():
        shutil.copy2(backyard_source, backyard_dest)
        print(f"[SUCCESS] Backyard image copied!")
        print(f"  From: {backyard_source}")
        print(f"  To: {backyard_dest}")
        print(f"  Size: {Path(backyard_dest).stat().st_size} bytes")
    else:
        print(f"[ERROR] Backyard source not found: {backyard_source}")
except Exception as e:
    print(f"[ERROR] Backyard copy failed: {e}")

print()

# Copy turf image
try:
    if Path(turf_source).exists():
        shutil.copy2(turf_source, turf_dest)
        print(f"[SUCCESS] Turf image copied!")
        print(f"  From: {turf_source}")
        print(f"  To: {turf_dest}")
        print(f"  Size: {Path(turf_dest).stat().st_size} bytes")
    else:
        print(f"[ERROR] Turf source not found: {turf_source}")
except Exception as e:
    print(f"[ERROR] Turf copy failed: {e}")

print()
print("=" * 60)
print("VERIFICATION")
print("=" * 60)

# Verify both images exist
backyard_exists = Path(backyard_dest).exists()
turf_exists = Path(turf_dest).exists()

print(f"Backyard image: {'✓ EXISTS' if backyard_exists else '✗ MISSING'}")
print(f"Turf image: {'✓ EXISTS' if turf_exists else '✗ MISSING'}")

if backyard_exists and turf_exists:
    print("\n[CONFIRMED] Both images are now saved and ready for testing!")
else:
    print("\n[ERROR] Missing images - cannot proceed with testing")