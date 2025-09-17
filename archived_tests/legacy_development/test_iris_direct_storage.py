#!/usr/bin/env python3
"""
Direct test of IRIS storage functionality
This bypasses the LLM and directly tests if storage works
"""

import sys
import os
sys.path.append('C:/Users/Not John Or Justin/Documents/instabids/ai-agents')

from agents.iris.agent import IrisAgent
import asyncio
import uuid
from datetime import datetime

# JJ Thompson's actual user ID
JJ_USER_ID = "01087874-747b-4159-8735-5ebb8715ff84"
JJ_PROPERTY_ID = "066d66b5-4217-45ee-90de-6e62bc8e0fd0"

async def test_direct_storage():
    """Test IRIS storage directly without going through the API"""
    
    print("=== TESTING IRIS DIRECT STORAGE ===")
    print(f"User ID: {JJ_USER_ID}")
    print(f"Property ID: {JJ_PROPERTY_ID}")
    
    # Create IRIS agent instance
    iris = IrisAgent()
    
    # Create a test image
    test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    # Test 1: Store to property photos directly
    print("\n1. Testing _store_to_property_photos...")
    
    try:
        # Call the storage function directly
        photo_id = iris._store_to_property_photos(
            user_id=JJ_USER_ID,
            image_data=test_image,
            filename=f"test_roof_{int(datetime.now().timestamp())}.png",
            session_id="direct_test",
            room_id=None  # We'll test without room first
        )
        
        print(f"   SUCCESS: Photo stored with ID: {photo_id}")
        
        # Verify in database
        from database_simple import db
        result = db.client.table("property_photos").select("*").eq("id", photo_id).execute()
        
        if result.data:
            print(f"   VERIFIED: Photo exists in database")
            print(f"   Property ID: {result.data[0].get('property_id')}")
            print(f"   Filename: {result.data[0].get('original_filename')}")
        else:
            print(f"   ERROR: Photo not found in database!")
            
    except Exception as e:
        print(f"   FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Check if we can query all photos for JJ
    print("\n2. Checking all photos for JJ Thompson...")
    
    try:
        from database_simple import db
        
        # Get all photos for JJ's property
        photos = db.client.table("property_photos")\
            .select("id, original_filename, created_at, room_id")\
            .eq("property_id", JJ_PROPERTY_ID)\
            .order("created_at", desc=True)\
            .execute()
        
        print(f"   Found {len(photos.data)} photos total:")
        for photo in photos.data[:5]:  # Show last 5
            print(f"   - {photo['original_filename']} (created: {photo['created_at']}, room: {photo['room_id']})")
            
    except Exception as e:
        print(f"   Query failed: {e}")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("IRIS DIRECT STORAGE TEST")
    print("=" * 60)
    
    # Run the async test
    success = asyncio.run(test_direct_storage())
    
    print("\n" + "=" * 60)
    if success:
        print("Storage function works when called directly!")
        print("Problem: IRIS doesn't call storage when user asks to add photos")
    else:
        print("Storage function itself is broken")
    print("=" * 60)