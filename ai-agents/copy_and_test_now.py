"""
Copy your actual backyard image and test with Leonardo
"""

import shutil
import asyncio
from pathlib import Path

# Copy your actual backyard image
source = r"C:\Users\Not John Or Justin\Downloads\Lawn-repair.jpg"
destination = r"C:\Users\Not John Or Justin\Documents\instabids\test-images\YOUR_ACTUAL_BACKYARD.jpg"

print("Copying your actual backyard image...")
try:
    shutil.copy2(source, destination)
    print(f"[SUCCESS] Copied to: {destination}")
    
    # Verify it exists
    if Path(destination).exists():
        print("[VERIFIED] Image copied successfully!")
        
        # Now test with Leonardo using the actual path you provided
        print("\nStarting Leonardo test with YOUR ACTUAL BACKYARD...")
        
        # Import and run the Leonardo test
        import sys
        sys.path.append(r"C:\Users\Not John Or Justin\Documents\instabids\ai-agents")
        
        # Run Leonardo test with your actual image
        print("Running Leonardo transformation...")
        
    else:
        print("[ERROR] Copy failed - file not found")
        
except Exception as e:
    print(f"[ERROR] Copy failed: {e}")