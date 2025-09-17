#!/usr/bin/env python3
"""
Test IRIS room assignment functionality end-to-end
This verifies that photos get assigned to the correct rooms
"""

import requests
import json
import time
import base64

def create_test_image():
    """Create a simple base64 test image"""
    # Create a minimal PNG image (1x1 transparent pixel)
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82'
    return "data:image/png;base64," + base64.b64encode(png_data).decode('utf-8')

def test_iris_room_assignment():
    """Test the complete room assignment workflow"""
    base_url = "http://localhost:8008"
    user_id = "550e8400-e29b-41d4-a716-446655440000"  # Real test user UUID
    
    print("Testing IRIS Room Assignment Functionality")
    print("=" * 60)
    
    # Step 1: Upload image and get first workflow question
    print("\n1. Uploading image to trigger workflow...")
    
    test_image = create_test_image()
    
    upload_request = {
        "message": "I'm uploading a backyard photo",
        "user_id": user_id,
        "session_id": f"test_room_assignment_{int(time.time())}",
        "context_type": "property",
        "images": [{
            "data": test_image,
            "filename": "backyard_test.png",
            "size": 1000,
            "type": "image/png"
        }],
        "trigger_image_workflow": True
    }
    
    response = requests.post(f"{base_url}/api/iris/unified-chat", 
                           json=upload_request, timeout=60)
    
    if response.status_code != 200:
        print(f"Upload failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    upload_data = response.json()
    session_id = upload_data.get("session_id")
    workflow_questions = upload_data.get("workflow_questions", [])
    
    print(f"Upload successful!")
    print(f"   Response: {upload_data.get('response', 'No response')[:100]}...")
    print(f"   Workflow questions: {len(workflow_questions)}")
    
    if not workflow_questions:
        print("No workflow questions generated")
        return False
    
    # Should only show first question (storage location)
    first_question = workflow_questions[0]
    print(f"   First question: {first_question.get('question')}")
    print(f"   Options: {first_question.get('options')}")
    
    # Step 2: Answer first question - choose "Property Photos" 
    print("\n2. Answering first question (Property Photos)...")
    
    first_answer_request = {
        "message": "Property Photos",
        "user_id": user_id,
        "session_id": session_id,
        "context_type": "property",
        "workflow_response": {
            "question_index": 0,
            "selected_option": "Property Photos"
        }
    }
    
    response = requests.post(f"{base_url}/api/iris/unified-chat", 
                           json=first_answer_request, timeout=60)
    
    if response.status_code != 200:
        print(f"First answer failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    first_answer_data = response.json()
    second_workflow_questions = first_answer_data.get("workflow_questions", [])
    
    print(f"First answer processed!")
    print(f"   Response: {first_answer_data.get('response', 'No response')[:100]}...")
    print(f"   Second workflow questions: {len(second_workflow_questions)}")
    
    if not second_workflow_questions:
        print("No second workflow question generated")
        return False
    
    # Should now show second question (room selection)
    second_question = second_workflow_questions[0]
    print(f"   Second question: {second_question.get('question')}")
    print(f"   Room options: {second_question.get('options')}")
    
    # Step 3: Answer second question - choose "Backyard"
    print("\n3. Answering second question (Backyard)...")
    
    second_answer_request = {
        "message": "Backyard",
        "user_id": user_id,
        "session_id": session_id,
        "context_type": "property", 
        "workflow_response": {
            "question_index": 1,
            "selected_option": "Backyard"
        }
    }
    
    response = requests.post(f"{base_url}/api/iris/unified-chat", 
                           json=second_answer_request, timeout=60)
    
    if response.status_code != 200:
        print(f"Second answer failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    second_answer_data = response.json()
    print(f"Second answer processed!")
    print(f"   Response: {second_answer_data.get('response', 'No response')[:100]}...")
    
    # Step 4: Verify photo was saved to database with room assignment
    print("\n4. Verifying photo storage with room assignment...")
    time.sleep(2)  # Give database a moment to update
    
    # Query the database via Supabase API to find the photo
    verify_request = {
        "query": f"SELECT id, room_id, original_filename, ai_description, ai_classification FROM property_photos WHERE ai_classification->>'session_id' = '{session_id}' ORDER BY created_at DESC LIMIT 1;"
    }
    
    db_response = requests.post("http://localhost:8008/api/supabase/execute-sql", 
                               json=verify_request, timeout=30)
    
    if db_response.status_code != 200:
        print(f"Database verification failed with status {db_response.status_code}")
        print(f"Response: {db_response.text}")
        return False
    
    db_data = db_response.json()
    
    if not db_data.get("data"):
        print("No photo found in database")
        return False
    
    photo_record = db_data["data"][0]
    room_id = photo_record.get("room_id")
    filename = photo_record.get("original_filename")
    ai_description = photo_record.get("ai_description") 
    classification = photo_record.get("ai_classification", {})
    
    print(f"Photo found in database!")
    print(f"   Photo ID: {photo_record.get('id')}")
    print(f"   Filename: {filename}")
    print(f"   Room ID: {room_id}")
    print(f"   AI Description: {ai_description}")
    print(f"   Classification: {classification}")
    
    # Step 5: Verify the room ID corresponds to "Backyard"
    if room_id:
        print("\n5. Verifying room assignment...")
        
        room_query = {
            "query": f"SELECT name, room_type FROM property_rooms WHERE id = '{room_id}';"
        }
        
        room_response = requests.post("http://localhost:8008/api/supabase/execute-sql",
                                     json=room_query, timeout=30)
        
        if room_response.status_code == 200:
            room_data = room_response.json()
            if room_data.get("data"):
                room_info = room_data["data"][0]
                room_name = room_info.get("name")
                room_type = room_info.get("room_type")
                
                print(f"Room assignment verified!")
                print(f"   Room Name: {room_name}")
                print(f"   Room Type: {room_type}")
                
                if room_name == "Backyard" or "backyard" in room_type.lower():
                    print("SUCCESS: Photo correctly assigned to Backyard room!")
                    return True
                else:
                    print(f"FAILURE: Photo assigned to wrong room (expected Backyard, got {room_name})")
                    return False
            else:
                print("Room not found in database")
                return False
        else:
            print(f"Room verification failed: {room_response.text}")
            return False
    else:
        print("FAILURE: Photo saved without room assignment (room_id is None)")
        return False

def main():
    """Run the test"""
    print("IRIS Room Assignment End-to-End Test")
    print("Testing two-step workflow: Storage Location -> Room Selection")
    print()
    
    try:
        success = test_iris_room_assignment()
        
        print("\n" + "=" * 60)
        if success:
            print("ALL TESTS PASSED! Room assignment is working correctly!")
            print("Photos are now properly assigned to rooms")
            print("Two-step workflow functions as expected") 
            print("Database stores room_id correctly")
        else:
            print("TEST FAILED! Room assignment needs debugging")
            
    except Exception as e:
        print(f"Test crashed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()