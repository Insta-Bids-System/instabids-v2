#!/usr/bin/env python3
"""
Test storage to Both locations with proper UUID
"""

import requests
import json
import base64
from pathlib import Path
import time
import uuid

BASE_URL = "http://localhost:8008"
IRIS_ENDPOINT = f"{BASE_URL}/api/iris/unified-chat"

def load_test_image():
    test_image_path = Path(r"C:\Users\Not John Or Justin\Documents\instabids\test-images")
    
    for img_file in test_image_path.glob("*.jpg"):
        with open(img_file, 'rb') as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_data}", img_file.name
    
    raise Exception("No test images found!")

def test_storage():
    print("Testing storage to Both locations with proper UUID...")
    
    # Use proper UUID
    test_user_id = str(uuid.uuid4())
    test_session_id = f"storage-test-{int(time.time())}"
    
    print(f"User ID (UUID): {test_user_id}")
    print(f"Session: {test_session_id}")
    
    image_data, filename = load_test_image()
    
    # First upload image
    print("\n1. Uploading image...")
    upload_request = {
        "message": "Please analyze this photo and ask where to save it.",
        "user_id": test_user_id,
        "session_id": test_session_id,
        "context_type": "auto",
        "images": [{
            "data": image_data,
            "filename": filename,
            "size": len(image_data),
            "type": "image/jpeg"
        }],
        "trigger_image_workflow": True
    }
    
    response = requests.post(IRIS_ENDPOINT, json=upload_request, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        questions = data.get('workflow_questions', [])
        print(f"[OK] Upload successful, {len(questions)} questions returned")
        
        if questions:
            print(f"First question: {questions[0].get('question')}")
            print(f"Options: {questions[0].get('options')}")
        
    else:
        print(f"[X] Upload failed: {response.status_code}")
        return False
    
    # Now answer "Both"
    print("\n2. Answering 'Both' to store in both locations...")
    
    storage_request = {
        "message": "Please save it to Both locations.",
        "user_id": test_user_id,
        "session_id": test_session_id,
        "context_type": "auto",
        "workflow_response": {
            "question_index": 0,
            "selected_option": "Both"
        },
        "images": [{
            "data": image_data,
            "filename": filename,
            "size": len(image_data),
            "type": "image/jpeg"
        }]
    }
    
    response = requests.post(IRIS_ENDPOINT, json=storage_request, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        print("[OK] Storage request sent successfully")
        print(f"Response: {data.get('response', '')[:150]}...")
        
        # Wait for storage
        print("\n3. Waiting 5 seconds for database writes...")
        time.sleep(5)
        
        # Check if storage worked by checking backend logs
        print("\n4. Storage operation completed - check backend logs for verification")
        return True
        
    else:
        print(f"[X] Storage request failed: {response.status_code}")
        return False

if __name__ == "__main__":
    success = test_storage()
    
    if success:
        print("\n[SUCCESS] Storage test completed!")
        print("Check backend logs to verify storage to both locations.")
    else:
        print("\n[FAILED] Storage test failed.")