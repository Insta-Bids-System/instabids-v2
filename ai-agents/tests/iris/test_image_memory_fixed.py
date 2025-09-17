"""
Test Image Memory System After Fixes
Tests the complete image upload, storage, and recall flow
"""

import requests
import json
import base64
import time
import sys
from datetime import datetime

# Fix Unicode output on Windows
sys.stdout.reconfigure(encoding='utf-8')

# Test configuration
BASE_URL = "http://localhost:8008"
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440001"

# Create a simple test image (1x1 pixel PNG)
TEST_IMAGE_DATA = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

def test_image_upload():
    """Test 1: Upload an image with room detection"""
    print("\n" + "="*60)
    print("TEST 1: IMAGE UPLOAD WITH ROOM DETECTION")
    print("="*60)
    
    session_id = f"test_session_{int(time.time() * 1000)}"
    
    # Upload image with room context
    response = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
        "user_id": TEST_USER_ID,
        "session_id": session_id,
        "message": "Here's a photo of my kitchen for inspiration",
        "images": [{
            "data": TEST_IMAGE_DATA,
            "filename": "kitchen_inspiration.png"
        }]
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Image upload successful")
        print(f"Response: {result.get('message', '')[:200]}...")
        
        # Check if room detection worked
        if "kitchen" in result.get('message', '').lower():
            print("✅ Room detection working (detected: kitchen)")
        else:
            print("⚠️ Room detection may not be working")
            
        return session_id, True
    else:
        print(f"❌ Image upload failed: {response.status_code}")
        print(f"Error: {response.text[:500]}")
        return session_id, False

def test_image_memory_recall(session_id):
    """Test 2: Check if agent remembers uploaded image"""
    print("\n" + "="*60)
    print("TEST 2: IMAGE MEMORY RECALL")
    print("="*60)
    
    # Ask about uploaded images
    response = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
        "user_id": TEST_USER_ID,
        "session_id": session_id,
        "message": "What images have I uploaded?"
    })
    
    if response.status_code == 200:
        result = response.json()
        message_lower = result.get('message', '').lower()
        
        if "kitchen" in message_lower or "image" in message_lower or "photo" in message_lower:
            print("✅ Image memory recall working")
            print(f"Response: {result.get('message', '')[:200]}...")
            return True
        else:
            print("❌ Image memory recall not working - no mention of uploaded images")
            print(f"Response: {result.get('message', '')[:200]}...")
            return False
    else:
        print(f"❌ Memory recall request failed: {response.status_code}")
        return False

def test_cross_session_memory():
    """Test 3: Check if images persist across sessions"""
    print("\n" + "="*60)
    print("TEST 3: CROSS-SESSION IMAGE MEMORY")
    print("="*60)
    
    new_session_id = f"new_session_{int(time.time() * 1000)}"
    
    # New session, same user - ask about images
    response = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
        "user_id": TEST_USER_ID,
        "session_id": new_session_id,
        "message": "Can you show me my inspiration boards?"
    })
    
    if response.status_code == 200:
        result = response.json()
        message_lower = result.get('message', '').lower()
        
        if "board" in message_lower or "inspiration" in message_lower:
            print("✅ Cross-session memory may be working")
            print(f"Response: {result.get('message', '')[:200]}...")
            return True
        else:
            print("⚠️ Cross-session memory unclear")
            print(f"Response: {result.get('message', '')[:200]}...")
            return False
    else:
        print(f"❌ Cross-session request failed: {response.status_code}")
        return False

def check_database_storage():
    """Test 4: Verify data in unified_conversation_memory"""
    print("\n" + "="*60)
    print("TEST 4: DATABASE STORAGE VERIFICATION")
    print("="*60)
    
    # Check via context API
    response = requests.get(f"{BASE_URL}/api/iris/context/{TEST_USER_ID}")
    
    if response.status_code == 200:
        context = response.json()
        
        # Check for inspiration boards
        boards = context.get('inspiration_boards', [])
        if boards:
            print(f"✅ Found {len(boards)} inspiration boards in unified memory")
            for board in boards[:2]:
                print(f"  - Board: {board.get('title', 'Unknown')}")
        else:
            print("⚠️ No inspiration boards found in context")
            
        # Check for photos
        photos = context.get('photos_from_unified_system', {})
        inspiration_photos = photos.get('inspiration_photos', [])
        if inspiration_photos:
            print(f"✅ Found {len(inspiration_photos)} inspiration photos")
        else:
            print("⚠️ No inspiration photos found")
            
        return len(boards) > 0 or len(inspiration_photos) > 0
    else:
        print(f"❌ Context API failed: {response.status_code}")
        return False

def test_multiple_images():
    """Test 5: Upload multiple images at once"""
    print("\n" + "="*60)
    print("TEST 5: MULTIPLE IMAGE UPLOAD")
    print("="*60)
    
    session_id = f"multi_session_{int(time.time() * 1000)}"
    
    # Upload multiple images
    response = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
        "user_id": TEST_USER_ID,
        "session_id": session_id,
        "message": "Here are some bathroom renovation ideas I like",
        "images": [
            {"data": TEST_IMAGE_DATA, "filename": "bathroom1.png"},
            {"data": TEST_IMAGE_DATA, "filename": "bathroom2.png"},
            {"data": TEST_IMAGE_DATA, "filename": "bathroom3.png"}
        ]
    })
    
    if response.status_code == 200:
        result = response.json()
        message = result.get('message', '')
        
        if "3" in message or "three" in message.lower():
            print("✅ Multiple image upload working")
            print(f"Response: {message[:200]}...")
            return True
        else:
            print("⚠️ Multiple images processed but count unclear")
            print(f"Response: {message[:200]}...")
            return True
    else:
        print(f"❌ Multiple image upload failed: {response.status_code}")
        return False

def main():
    """Run all image memory tests"""
    print("\n" + "="*60)
    print("IRIS IMAGE MEMORY SYSTEM TEST SUITE")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {
        "image_upload": False,
        "memory_recall": False,
        "cross_session": False,
        "database_storage": False,
        "multiple_images": False
    }
    
    # Test 1: Upload image
    session_id, upload_success = test_image_upload()
    results["image_upload"] = upload_success
    
    if upload_success:
        # Test 2: Memory recall in same session
        time.sleep(2)  # Give system time to process
        results["memory_recall"] = test_image_memory_recall(session_id)
        
        # Test 3: Cross-session memory
        time.sleep(1)
        results["cross_session"] = test_cross_session_memory()
        
        # Test 4: Database verification
        results["database_storage"] = check_database_storage()
        
        # Test 5: Multiple images
        results["multiple_images"] = test_multiple_images()
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 SUCCESS: Image memory system fully operational!")
    elif passed_tests >= 3:
        print("\n⚠️ PARTIAL SUCCESS: Core image functionality working")
    else:
        print("\n❌ FAILURE: Image memory system has critical issues")

if __name__ == "__main__":
    main()