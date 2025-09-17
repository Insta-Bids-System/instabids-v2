#!/usr/bin/env python3
"""
Simple test for IRIS workflow questions without actual image processing
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8008"
IRIS_ENDPOINT = f"{BASE_URL}/api/iris/unified-chat"

def test_workflow_questions():
    """Test IRIS workflow questions with minimal image data"""
    
    print("\n" + "="*80)
    print("TESTING IRIS WORKFLOW QUESTIONS (SIMPLE)")
    print("="*80)
    
    # Use a tiny 1x1 transparent PNG to minimize processing
    tiny_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    # Prepare minimal request
    request_data = {
        "message": "Analyze this image",
        "user_id": "test-user",
        "session_id": "test-workflow",
        "context_type": "auto",
        "images": [{
            "data": tiny_image,
            "filename": "test.png",
            "size": 100,
            "type": "image/png"
        }],
        "trigger_image_workflow": True
    }
    
    print("\nRequest details:")
    print(f"- trigger_image_workflow: {request_data['trigger_image_workflow']}")
    print(f"- images count: {len(request_data['images'])}")
    
    try:
        print("\nSending request...")
        response = requests.post(
            IRIS_ENDPOINT,
            json=request_data,
            timeout=10  # Shorter timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check workflow questions
            workflow_questions = data.get('workflow_questions')
            
            print(f"\nWORKFLOW QUESTIONS RESULT:")
            print(f"- Type: {type(workflow_questions)}")
            print(f"- Value: {workflow_questions}")
            
            if workflow_questions:
                print(f"- Count: {len(workflow_questions)}")
                print("\nQuestions:")
                for q in workflow_questions:
                    print(f"  - {q.get('question')}")
                    print(f"    Options: {q.get('options')}")
            else:
                print("- NO WORKFLOW QUESTIONS RETURNED (BUG!)")
            
            # Show response keys
            print(f"\nResponse keys: {list(data.keys())}")
            
        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_workflow_questions()