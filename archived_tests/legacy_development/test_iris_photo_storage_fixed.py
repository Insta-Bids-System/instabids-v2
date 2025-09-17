#!/usr/bin/env python3
"""
Test IRIS photo storage functionality after fixing async/await issues
"""
import requests
import json
import base64
import time

def create_test_image():
    """Create a small test image in base64 format"""
    # Create a simple 10x10 pixel PNG image
    import io
    try:
        from PIL import Image
        img = Image.new('RGB', (10, 10), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        image_data = buffer.read()
        base64_data = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/png;base64,{base64_data}"
    except ImportError:
        # If PIL not available, create a minimal base64 string
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

def test_iris_photo_upload():
    """Test IRIS photo upload with workflow questions"""
    
    test_image = create_test_image()
    
    request_data = {
        "message": "I'm uploading a backyard photo for analysis",
        "user_id": "test-user-iris-storage",
        "session_id": "session-iris-storage-test",
        "context_type": "property",
        "images": [{
            "data": test_image,
            "filename": "backyard-test.png",
            "size": 1024,
            "type": "image/png"
        }],
        "trigger_image_workflow": True
    }
    
    print("🔄 Testing IRIS photo upload with fixed storage...")
    print(f"📸 Image data size: {len(test_image)} characters")
    
    try:
        response = requests.post(
            'http://localhost:8008/api/iris/unified-chat',
            json=request_data,
            timeout=120
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ IRIS API Response Success!")
            print(f"🤖 Response: {data.get('response', 'No response')[:200]}...")
            
            # Check if workflow questions are present
            if data.get('workflow_questions'):
                print(f"❓ Workflow questions: {len(data['workflow_questions'])} questions")
                for i, q in enumerate(data['workflow_questions']):
                    print(f"   Q{i+1}: {q.get('question', 'No question')}")
                    print(f"   Options: {q.get('options', [])}")
            else:
                print("⚠️ No workflow questions returned")
            
            print("🎯 Testing workflow response (Property Photos selection)...")
            
            # Test workflow response for "Property Photos"
            workflow_response_data = {
                "message": "For question 1, I choose: Property Photos",
                "user_id": "test-user-iris-storage",
                "session_id": "session-iris-storage-test",
                "context_type": "property",
                "workflow_response": {
                    "question_index": 0,
                    "selected_option": "Property Photos"
                },
                "images": [{
                    "data": test_image,
                    "filename": "backyard-test.png",
                    "size": 1024,
                    "type": "image/png"
                }]
            }
            
            workflow_response = requests.post(
                'http://localhost:8008/api/iris/unified-chat',
                json=workflow_response_data,
                timeout=120
            )
            
            print(f"📡 Workflow response status: {workflow_response.status_code}")
            
            if workflow_response.status_code == 200:
                workflow_data = workflow_response.json()
                print("✅ Workflow Response Success!")
                print(f"🤖 Storage response: {workflow_data.get('response', 'No response')[:200]}...")
                
                # Give a moment for database operations to complete
                time.sleep(2)
                
                return True
            else:
                print(f"❌ Workflow response failed: {workflow_response.text}")
                return False
                
        else:
            print(f"❌ IRIS API failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def verify_database_storage():
    """Verify that photos were actually saved to the database"""
    print("\n🔍 Checking database for stored photos...")
    
    try:
        # Import database tools
        import sys
        sys.path.append('C:/Users/Not John Or Justin/Documents/instabids/ai-agents')
        from database_simple import db
        
        # Check property_photos table
        property_photos = db.client.table("property_photos").select("*").eq("ai_description", "Backyard photo for artificial turf installation - uploaded via IRIS assistant").execute()
        
        if property_photos.data:
            print(f"✅ Found {len(property_photos.data)} photo(s) in property_photos table!")
            for photo in property_photos.data:
                print(f"   📸 Photo ID: {photo['id']}")
                print(f"   🏠 Property ID: {photo['property_id']}")
                print(f"   📝 Description: {photo.get('ai_description', 'No description')}")
                print(f"   📅 Created: {photo.get('created_at', 'No timestamp')}")
        else:
            print("❌ No photos found in property_photos table")
            
        # Check properties table for created property
        properties = db.client.table("properties").select("*").eq("user_id", "test-user-iris-storage").execute()
        
        if properties.data:
            print(f"✅ Found {len(properties.data)} property record(s) for test user!")
            for prop in properties.data:
                print(f"   🏠 Property ID: {prop['id']}")
                print(f"   📍 Name: {prop.get('name', 'No name')}")
        else:
            print("❌ No property records found for test user")
            
        return len(property_photos.data) > 0
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 IRIS Photo Storage Test - After Async/Await Fixes")
    print("=" * 60)
    
    # Test the upload and workflow
    upload_success = test_iris_photo_upload()
    
    # Verify database storage
    storage_verified = verify_database_storage()
    
    print("\n📊 Test Results:")
    print(f"   📤 Photo Upload: {'✅ PASS' if upload_success else '❌ FAIL'}")
    print(f"   💾 Database Storage: {'✅ PASS' if storage_verified else '❌ FAIL'}")
    
    if upload_success and storage_verified:
        print("\n🎉 SUCCESS: IRIS photo storage is now fully operational!")
        print("🔧 The async/await fixes have resolved the storage issues.")
    else:
        print("\n⚠️ Issues remain - check logs for details")