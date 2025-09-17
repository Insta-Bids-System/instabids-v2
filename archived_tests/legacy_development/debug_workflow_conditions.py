#!/usr/bin/env python3
"""
Debug IRIS workflow conditions to understand why both questions are appearing
"""

import requests
import json
import time
import base64

def create_test_image():
    """Create a simple base64 test image"""
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82'
    return "data:image/png;base64," + base64.b64encode(png_data).decode('utf-8')

def debug_workflow_conditions():
    """Debug the exact request conditions that cause the dual-question issue"""
    base_url = "http://localhost:8008"
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    
    print("Debugging IRIS Workflow Conditions")
    print("=" * 50)
    
    # Test 1: Image upload only
    print("\n1. Testing image upload with trigger_image_workflow=True...")
    
    test_image = create_test_image()
    session_id = f"debug_conditions_{int(time.time())}"
    
    upload_request = {
        "message": "Debug test image upload",
        "user_id": user_id,
        "session_id": session_id,
        "context_type": "property",
        "images": [{
            "data": test_image,
            "filename": "debug_test.png",
            "size": 1000,
            "type": "image/png"
        }],
        "trigger_image_workflow": True,
        "workflow_response": None  # Explicitly set to None
    }
    
    print(f"   Request conditions:")
    print(f"   - trigger_image_workflow: {upload_request['trigger_image_workflow']}")
    print(f"   - images: {len(upload_request['images'])}")
    print(f"   - workflow_response: {upload_request['workflow_response']}")
    print(f"   - session_id: {session_id}")
    
    response = requests.post(f"{base_url}/api/iris/unified-chat", 
                           json=upload_request, timeout=30)
    
    if response.status_code != 200:
        print(f"   ❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    data = response.json()
    workflow_questions = data.get("workflow_questions", [])
    
    print(f"   ✅ Response received")
    print(f"   - Workflow questions count: {len(workflow_questions)}")
    
    for i, q in enumerate(workflow_questions):
        print(f"   - Question {i}: {q.get('question')}")
        print(f"     Options: {q.get('options')}")
    
    if len(workflow_questions) == 1:
        print("   ✅ CORRECT: Only first question returned")
    else:
        print(f"   ❌ ERROR: Expected 1 question, got {len(workflow_questions)}")
        print("   This indicates both workflow blocks are executing")
    
    print(f"\n   Check backend logs for:")
    print(f"   - 'DEBUG: trigger_image_workflow=True'")
    print(f"   - 'IRIS processing workflow response' (should NOT appear)")
    print(f"   - 'Generated X workflow questions'")

if __name__ == "__main__":
    debug_workflow_conditions()