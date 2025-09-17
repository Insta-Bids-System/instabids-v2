"""
Test inspiration board retrieval from unified memory
"""

import requests
import json
import sys
import time

# Fix Unicode output on Windows
sys.stdout.reconfigure(encoding='utf-8')

# Test configuration
BASE_URL = "http://localhost:8008"
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440001"  # User from previous tests

def test_board_retrieval():
    """Test if inspiration boards are being returned correctly"""
    print("\n" + "="*60)
    print("INSPIRATION BOARD RETRIEVAL TEST")
    print("="*60)
    
    # Step 1: Check context API for boards
    print("\n1. CHECKING CONTEXT API FOR INSPIRATION BOARDS...")
    context_response = requests.get(f"{BASE_URL}/api/iris/context/{TEST_USER_ID}")
    
    if context_response.status_code == 200:
        context = context_response.json()
        
        # Check inspiration boards specifically
        boards = context.get('inspiration_boards', [])
        print(f"Found {len(boards)} inspiration boards in context")
        
        if boards:
            for i, board in enumerate(boards):
                print(f"  Board {i+1}:")
                print(f"    - ID: {board.get('id', 'None')}")
                print(f"    - Title: {board.get('title', 'None')}")
                print(f"    - Room Type: {board.get('room_type', 'None')}")
                print(f"    - Images: {len(board.get('images', []))}")
                print(f"    - Created: {board.get('created_at', 'None')}")
        else:
            print("  ❌ No inspiration boards found in context")
            
        # Check photos_from_unified_system for comparison
        photos = context.get('photos_from_unified_system', {})
        inspiration_photos = photos.get('inspiration_photos', [])
        print(f"\nFound {len(inspiration_photos)} inspiration photos in unified system")
        
        if inspiration_photos:
            for i, photo in enumerate(inspiration_photos[:3]):
                print(f"  Photo {i+1}: {photo.get('file_path', 'No path')}")
                metadata = photo.get('metadata', {})
                print(f"    - Room: {metadata.get('room_type', 'None')}")
                print(f"    - Features: {metadata.get('features', [])}")
    else:
        print(f"❌ Context API failed: {context_response.status_code}")
        print(f"Error: {context_response.text}")
        return
    
    # Step 2: Test with fresh image upload to verify storage
    print("\n2. UPLOADING FRESH IMAGE TO TEST STORAGE...")
    
    session_id = f"board_test_{int(time.time() * 1000)}"
    
    # Simple test image
    test_image_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    upload_response = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
        "user_id": TEST_USER_ID,
        "session_id": session_id,
        "message": "Here's a modern kitchen design I love for inspiration",
        "images": [{
            "data": test_image_data,
            "filename": "modern_kitchen_test.png"
        }]
    })
    
    if upload_response.status_code == 200:
        upload_result = upload_response.json()
        print(f"✅ Image uploaded successfully")
        print(f"Response: {upload_result.get('response', '')[:200]}...")
        
        # Wait for processing
        time.sleep(3)
        
        # Check context again
        print("\n3. CHECKING CONTEXT AFTER NEW UPLOAD...")
        context_response2 = requests.get(f"{BASE_URL}/api/iris/context/{TEST_USER_ID}")
        
        if context_response2.status_code == 200:
            context2 = context_response2.json()
            boards_after = context2.get('inspiration_boards', [])
            photos_after = context2.get('photos_from_unified_system', {}).get('inspiration_photos', [])
            
            print(f"Boards after upload: {len(boards_after)}")
            print(f"Photos after upload: {len(photos_after)}")
            
            if len(boards_after) > len(boards):
                print("✅ New board created after upload")
            elif len(photos_after) > len(inspiration_photos):
                print("⚠️ Photo stored but not appearing in boards")
            else:
                print("❌ No change detected after upload")
    else:
        print(f"❌ Upload failed: {upload_response.status_code}")
        print(f"Error: {upload_response.text}")

if __name__ == "__main__":
    test_board_retrieval()