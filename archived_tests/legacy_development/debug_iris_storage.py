#!/usr/bin/env python3
"""
Debug IRIS storage functions step by step
"""
import sys
sys.path.append('C:/Users/Not John Or Justin/Documents/instabids/ai-agents')

from database_simple import db
import uuid
from datetime import datetime
import json

def test_property_creation():
    """Test creating a property for the test user"""
    user_id = '01087874-747b-4159-8735-5ebb8715ff84'  # jjthompsonfau@gmail.com
    
    print("=== STEP 1: TEST PROPERTY CREATION ===")
    
    # Check if property exists
    try:
        property_result = db.client.table("properties").select("id").eq("user_id", user_id).limit(1).execute()
        
        if property_result.data and len(property_result.data) > 0:
            property_id = property_result.data[0]["id"]
            print(f"✅ Found existing property: {property_id}")
        else:
            print("❌ No property found - creating new one")
            new_property = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "name": "Debug Test Property",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            print(f"Creating property with data: {new_property}")
            property_result = db.client.table("properties").insert(new_property).execute()
            print(f"Property creation result: {property_result}")
            
            property_id = new_property["id"]
            print(f"✅ Created new property: {property_id}")
        
        return property_id
        
    except Exception as e:
        print(f"❌ Property creation failed: {e}")
        return None

def test_photo_insert(property_id):
    """Test inserting a photo directly"""
    print("\n=== STEP 2: TEST PHOTO INSERT ===")
    
    if not property_id:
        print("❌ No property_id - skipping photo insert")
        return None
    
    # Create test image data
    test_image_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    photo_entry = {
        "id": str(uuid.uuid4()),
        "property_id": property_id,
        "room_id": None,
        "photo_url": test_image_data,
        "original_filename": "debug_test_photo.png",
        "photo_type": "documentation",
        "ai_description": "DEBUG TEST: Photo uploaded via IRIS debugging",
        "ai_classification": {
            "debug_test": True,
            "upload_timestamp": datetime.now().isoformat()
        },
        "upload_date": datetime.now().isoformat(),
        "taken_date": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat()
    }
    
    print(f"Inserting photo with data: {json.dumps(photo_entry, indent=2)}")
    
    try:
        result = db.client.table("property_photos").insert(photo_entry).execute()
        print(f"✅ Photo insert successful!")
        print(f"Insert result: {result}")
        return photo_entry["id"]
        
    except Exception as e:
        print(f"❌ Photo insert failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def verify_photo_saved(photo_id):
    """Verify the photo was actually saved"""
    print("\n=== STEP 3: VERIFY PHOTO SAVED ===")
    
    if not photo_id:
        print("❌ No photo_id - skipping verification")
        return False
    
    try:
        result = db.client.table("property_photos").select("*").eq("id", photo_id).execute()
        
        if result.data and len(result.data) > 0:
            photo = result.data[0]
            print(f"✅ Photo found in database!")
            print(f"  ID: {photo['id']}")
            print(f"  Filename: {photo['original_filename']}")
            print(f"  Description: {photo['ai_description']}")
            print(f"  Created: {photo['created_at']}")
            return True
        else:
            print("❌ Photo NOT found in database")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def test_complete_iris_flow():
    """Test the complete flow"""
    print("🔧 DEBUGGING IRIS STORAGE - COMPLETE STEP-BY-STEP TEST")
    print("=" * 60)
    
    # Step 1: Create/find property
    property_id = test_property_creation()
    
    # Step 2: Insert photo
    photo_id = test_photo_insert(property_id)
    
    # Step 3: Verify photo
    success = verify_photo_saved(photo_id)
    
    print(f"\n📊 FINAL RESULT: {'✅ SUCCESS' if success else '❌ FAILURE'}")
    
    return success

if __name__ == "__main__":
    test_complete_iris_flow()