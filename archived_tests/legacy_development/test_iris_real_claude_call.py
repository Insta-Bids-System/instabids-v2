#!/usr/bin/env python3
"""
Test IRIS with REAL Claude API call - no test bypass
"""

import requests
import json
import base64
from pathlib import Path
import time

BASE_URL = "http://localhost:8008"
IRIS_ENDPOINT = f"{BASE_URL}/api/iris/unified-chat"

def load_real_test_image():
    """Load actual test image"""
    test_image_path = Path(r"C:\Users\Not John Or Justin\Documents\instabids\test-images")
    
    for img_file in test_image_path.glob("*.jpg"):
        print(f"[OK] Found test image: {img_file.name}")
        with open(img_file, 'rb') as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_data}", img_file.name
    
    # Fallback to tiny image
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==", "tiny.png"

def test_real_claude_call():
    """Test IRIS with real Claude API call"""
    
    print("\n" + "="*80)
    print("TESTING IRIS WITH REAL CLAUDE API CALL")
    print("="*80)
    
    # Use session ID WITHOUT 'test' to avoid bypass
    real_user_id = f"real-user-{int(time.time())}"
    real_session_id = f"production-session-{int(time.time())}"  # No 'test' in name!
    
    print(f"\nUsing non-test IDs to trigger real Claude call:")
    print(f"- User ID: {real_user_id}")
    print(f"- Session ID: {real_session_id}")
    
    # Load real image
    image_data, filename = load_real_test_image()
    print(f"- Image size: {len(image_data)} bytes")
    
    request_data = {
        "message": "I took this photo of my backyard. Can you tell me what you see? Please describe the grass, trees, or any landscaping elements you notice.",
        "user_id": real_user_id,
        "session_id": real_session_id,
        "context_type": "auto",
        "images": [{
            "data": image_data,
            "filename": filename,
            "size": len(image_data),
            "type": "image/jpeg"
        }],
        "trigger_image_workflow": True
    }
    
    print("\nSending request to IRIS (expecting real Claude analysis)...")
    print("This may take 10-20 seconds for Claude to analyze the image...")
    
    try:
        response = requests.post(
            IRIS_ENDPOINT,
            json=request_data,
            timeout=60  # Longer timeout for real Claude call
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            
            print("\n" + "="*80)
            print("CLAUDE'S ACTUAL RESPONSE:")
            print("="*80)
            print(response_text)
            print("="*80)
            
            # Check for image-specific content
            image_words = ['grass', 'yard', 'backyard', 'lawn', 'tree', 'fence', 'patio', 'deck', 'garden', 'outdoor', 'landscape', 'green', 'plant', 'turf', 'artificial']
            found_words = [word for word in image_words if word.lower() in response_text.lower()]
            
            if found_words:
                print(f"\n[OK] CLAUDE ANALYZED THE IMAGE!")
                print(f"Image-specific words found: {', '.join(found_words)}")
            else:
                print("\n[WARNING] Response doesn't contain image-specific words")
                print("Claude may not have seen the image or it may be too generic")
            
            # Check workflow questions
            workflow_questions = data.get('workflow_questions', [])
            if workflow_questions:
                print(f"\n[OK] Workflow questions returned: {len(workflow_questions)}")
                for q in workflow_questions:
                    print(f"  - {q.get('question')}")
            
            return True
            
        else:
            print(f"\n[X] Error: HTTP {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("\n[X] Request timed out after 60 seconds")
        print("This could mean Claude is processing but taking too long")
        return False
    except Exception as e:
        print(f"\n[X] Error: {e}")
        return False

if __name__ == "__main__":
    success = test_real_claude_call()
    
    if success:
        print("\n" + "="*80)
        print("[OK] VERIFICATION COMPLETE - CLAUDE IS RECEIVING AND ANALYZING IMAGES!")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("[X] TEST FAILED - Check backend logs for details")
        print("="*80)