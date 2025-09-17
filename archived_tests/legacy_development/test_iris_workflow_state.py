#!/usr/bin/env python3
"""
Test IRIS workflow state saving and retrieval
"""

import requests
import json
import time
import base64

def create_test_image():
    """Create a simple base64 test image"""
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82'
    return "data:image/png;base64," + base64.b64encode(png_data).decode('utf-8')

def test_workflow_state():
    """Test just the workflow state saving"""
    base_url = "http://localhost:8008"
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    
    print("Testing IRIS Workflow State System")
    print("=" * 50)
    
    # Step 1: Upload image and get first workflow question
    print("\n1. Uploading image to get first workflow question...")
    
    test_image = create_test_image()
    
    upload_request = {
        "message": "I'm uploading a test photo",
        "user_id": user_id,
        "session_id": f"workflow_test_{int(time.time())}",
        "context_type": "property",
        "images": [{
            "data": test_image,
            "filename": "test.png",
            "size": 1000,
            "type": "image/png"
        }],
        "trigger_image_workflow": True
    }
    
    response = requests.post(f"{base_url}/api/iris/unified-chat", 
                           json=upload_request, timeout=30)
    
    if response.status_code != 200:
        print(f"Upload failed: {response.status_code}")
        print(response.text)
        return
    
    upload_data = response.json()
    session_id = upload_data.get("session_id")
    workflow_questions = upload_data.get("workflow_questions", [])
    
    print(f"Upload successful, session_id: {session_id}")
    print(f"Workflow questions: {len(workflow_questions)}")
    
    if workflow_questions:
        print(f"First question: {workflow_questions[0].get('question')}")
        print(f"Options: {workflow_questions[0].get('options')}")
    
    # Step 2: Answer first question to trigger workflow state saving
    print("\n2. Answering first question to trigger workflow state saving...")
    
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
    
    # Wait a moment and watch the logs
    print("   Sending request... Check backend logs for workflow state saving")
    
    response = requests.post(f"{base_url}/api/iris/unified-chat", 
                           json=first_answer_request, timeout=30)
    
    if response.status_code != 200:
        print(f"First answer failed: {response.status_code}")
        print(response.text)
        return
    
    first_answer_data = response.json()
    print(f"First answer processed successfully")
    print(f"Second workflow questions: {len(first_answer_data.get('workflow_questions', []))}")
    
    # Step 3: Check if workflow state was actually saved
    print("\n3. Checking if workflow state was saved to database...")
    
    # Give database a moment to save
    time.sleep(1)
    
    # Use MCP to check the database
    print(f"   Looking for workflow state with session_id: {session_id}")
    print("   Check the unified_conversation_memory table for workflow_state entries")

if __name__ == "__main__":
    test_workflow_state()