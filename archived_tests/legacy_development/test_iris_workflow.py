#!/usr/bin/env python3
"""
Test IRIS unified agent with image workflow questions
Testing if workflow questions are properly returned in the response
"""

import requests
import json
import base64
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8008"
IRIS_ENDPOINT = f"{BASE_URL}/api/iris/unified-chat"

def load_test_image():
    """Load a test image and convert to base64"""
    # Using a simple test pattern (you can replace with actual image path)
    test_image_path = Path(r"C:\Users\Not John Or Justin\Documents\instabids\test-images")
    
    # Find first image in test-images folder
    for img_file in test_image_path.glob("*"):
        if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
            print(f"Found test image: {img_file.name}")
            with open(img_file, 'rb') as f:
                image_data = f.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                # Create proper data URL
                if img_file.suffix.lower() in ['.jpg', '.jpeg']:
                    media_type = 'image/jpeg'
                elif img_file.suffix.lower() == '.png':
                    media_type = 'image/png'
                else:
                    media_type = 'image/gif'
                return f"data:{media_type};base64,{base64_data}"
    
    print("No test images found, using placeholder")
    # Return a tiny 1x1 transparent PNG as fallback
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

def test_iris_workflow_questions():
    """Test IRIS with image upload and workflow questions"""
    
    print("\n" + "="*80)
    print("TESTING IRIS WORKFLOW QUESTIONS")
    print("="*80)
    
    # Load test image
    image_data = load_test_image()
    
    # Prepare request with image and workflow trigger
    request_data = {
        "message": "I'm uploading an image. Please analyze it and ask me where to put it.",
        "user_id": "test-user-123",
        "session_id": "test-session-workflow",
        "context_type": "auto",
        "images": [{
            "data": image_data,
            "filename": "test-image.jpg",
            "size": 50000,
            "type": "image/jpeg"
        }],
        "trigger_image_workflow": True  # This should trigger workflow questions
    }
    
    print("\nRequest summary:")
    print(f"- Message: {request_data['message']}")
    print(f"- Images: {len(request_data['images'])} image(s)")
    print(f"- Trigger workflow: {request_data['trigger_image_workflow']}")
    print(f"- Session ID: {request_data['session_id']}")
    
    print("\nSending request to IRIS...")
    
    try:
        response = requests.post(
            IRIS_ENDPOINT,
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n" + "-"*40)
            print("RESPONSE RECEIVED")
            print("-"*40)
            
            # Check workflow questions
            workflow_questions = data.get('workflow_questions', [])
            
            print(f"\n🔍 WORKFLOW QUESTIONS CHECK:")
            print(f"   - Type: {type(workflow_questions)}")
            print(f"   - Count: {len(workflow_questions)}")
            
            if workflow_questions:
                print("\n✅ WORKFLOW QUESTIONS FOUND:")
                for i, q in enumerate(workflow_questions, 1):
                    print(f"\n   Question {i}:")
                    print(f"   - Text: {q.get('question', 'N/A')}")
                    print(f"   - Options: {q.get('options', [])}")
                    print(f"   - Callback: {q.get('callback', 'N/A')}")
            else:
                print("\n❌ NO WORKFLOW QUESTIONS IN RESPONSE")
                print("   This is the bug we're trying to fix!")
            
            # Show other response data
            print(f"\n📝 Response text: {data.get('response', 'N/A')[:200]}...")
            
            # Check if Claude saw the image
            response_text = data.get('response', '').lower()
            if any(word in response_text for word in ['image', 'photo', 'picture', 'backyard', 'grass', 'yard']):
                print("\n✅ Claude appears to have analyzed the image")
            else:
                print("\n⚠️ Claude may not have seen the image")
            
            # Show full response for debugging
            print("\n" + "-"*40)
            print("FULL RESPONSE DATA:")
            print("-"*40)
            print(json.dumps(data, indent=2))
            
        else:
            print(f"\n❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\n⏱️ Request timed out after 30 seconds")
        print("This might mean IRIS is processing but taking too long")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_iris_workflow_questions()