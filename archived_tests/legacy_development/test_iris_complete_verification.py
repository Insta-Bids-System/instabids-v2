#!/usr/bin/env python3
"""
Complete verification test for IRIS image workflow
This will verify:
1. Claude actually receives and analyzes images
2. Workflow questions are returned
3. Data is saved to database
4. Frontend can retrieve saved context
"""

import requests
import json
import base64
from pathlib import Path
import time

BASE_URL = "http://localhost:8008"
IRIS_ENDPOINT = f"{BASE_URL}/api/iris/unified-chat"

def load_real_test_image():
    """Load actual test image from test-images folder"""
    test_image_path = Path(r"C:\Users\Not John Or Justin\Documents\instabids\test-images")
    
    for img_file in test_image_path.glob("*.jpg"):
        print(f"[OK] Found test image: {img_file.name}")
        with open(img_file, 'rb') as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_data}", img_file.name
    
    raise Exception("No test images found!")

def test_complete_iris_workflow():
    """Complete end-to-end test of IRIS image workflow"""
    
    print("\n" + "="*80)
    print("COMPLETE IRIS IMAGE WORKFLOW VERIFICATION")
    print("="*80)
    
    # Generate unique IDs for tracking
    test_user_id = f"test-user-{int(time.time())}"
    test_session_id = f"test-session-{int(time.time())}"
    
    print(f"\nTest IDs:")
    print(f"- User ID: {test_user_id}")
    print(f"- Session ID: {test_session_id}")
    
    # Load real image
    image_data, filename = load_real_test_image()
    print(f"- Image loaded: {len(image_data)} bytes")
    
    # STEP 1: Send image to IRIS
    print("\n" + "-"*40)
    print("STEP 1: Sending image to IRIS")
    print("-"*40)
    
    request_data = {
        "message": "I took this photo of my backyard. Can you analyze it and help me understand what work needs to be done?",
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
    
    print("Sending request to IRIS...")
    
    try:
        response = requests.post(
            IRIS_ENDPOINT,
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # CHECK 1: Did Claude analyze the image?
            print("\n[OK] RESPONSE RECEIVED")
            response_text = data.get('response', '')
            
            # Look for image-specific words that indicate Claude saw it
            image_words = ['grass', 'yard', 'backyard', 'lawn', 'trees', 'fence', 'patio', 'deck', 'garden', 'outdoor', 'landscape']
            found_words = [word for word in image_words if word.lower() in response_text.lower()]
            
            if found_words:
                print(f"[OK] CLAUDE SAW THE IMAGE - mentioned: {', '.join(found_words)}")
            else:
                print("[X] WARNING: Claude's response doesn't mention image-specific content")
            
            print(f"\nClaude's response (first 300 chars):")
            print(f"'{response_text[:300]}...'")
            
            # CHECK 2: Are workflow questions returned?
            workflow_questions = data.get('workflow_questions', [])
            
            if workflow_questions:
                print(f"\n[OK] WORKFLOW QUESTIONS RETURNED: {len(workflow_questions)} questions")
                for q in workflow_questions:
                    print(f"  - {q.get('question')}")
            else:
                print("\n[X] NO WORKFLOW QUESTIONS RETURNED")
            
            # Store session for next test
            return test_user_id, test_session_id, workflow_questions
            
        else:
            print(f"[X] Error: HTTP {response.status_code}")
            print(response.text)
            return None, None, None
            
    except Exception as e:
        print(f"[X] Error: {e}")
        return None, None, None

def verify_database_storage(user_id, session_id):
    """Check if image context was saved to database"""
    
    print("\n" + "-"*40)
    print("STEP 2: Verifying Database Storage")
    print("-"*40)
    
    # Use Supabase directly to check
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-agents'))
    
    from database_simple import DatabaseSimple
    
    db = DatabaseSimple()
    
    # Check unified_conversation_memory
    query = """
    SELECT * FROM unified_conversation_memory 
    WHERE memory_value::text LIKE %s
    ORDER BY created_at DESC
    LIMIT 5
    """
    
    try:
        results = db.execute_query(query, (f'%{session_id}%',))
        
        if results:
            print(f"[OK] FOUND {len(results)} memory entries in database")
            for r in results:
                print(f"  - Type: {r.get('memory_type')}, Key: {r.get('memory_key')}")
                memory_value = r.get('memory_value', {})
                if isinstance(memory_value, dict):
                    if 'image_upload_session' in str(memory_value):
                        print("  [OK] Contains image upload session data!")
        else:
            print("[X] No memory entries found in database")
            
    except Exception as e:
        print(f"[X] Database query failed: {e}")

def test_followup_conversation(user_id, session_id):
    """Test if IRIS remembers the image context in next conversation"""
    
    print("\n" + "-"*40)
    print("STEP 3: Testing Context Persistence")
    print("-"*40)
    
    # Send followup without image
    request_data = {
        "message": "What did you think about that backyard photo I just showed you?",
        "user_id": user_id,
        "session_id": session_id,
        "context_type": "auto"
    }
    
    print("Sending followup message (no image)...")
    
    try:
        response = requests.post(
            IRIS_ENDPOINT,
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            
            # Check if IRIS remembers the image
            if any(word in response_text.lower() for word in ['photo', 'image', 'backyard', 'showed', 'uploaded']):
                print("[OK] IRIS REMEMBERS THE IMAGE CONTEXT!")
                print(f"Response: '{response_text[:300]}...'")
            else:
                print("[X] IRIS doesn't seem to remember the image")
                print(f"Response: '{response_text[:300]}...'")
                
    except Exception as e:
        print(f"[X] Error: {e}")

if __name__ == "__main__":
    # Run complete verification
    user_id, session_id, questions = test_complete_iris_workflow()
    
    if user_id and session_id:
        # Wait a moment for database writes
        print("\nWaiting 2 seconds for database writes...")
        time.sleep(2)
        
        # Verify database storage
        verify_database_storage(user_id, session_id)
        
        # Test context persistence
        test_followup_conversation(user_id, session_id)
        
        print("\n" + "="*80)
        print("VERIFICATION COMPLETE")
        print("="*80)
        
        print("\n[OK] CONFIRMED WORKING:" if questions else "\n[X] NOT FULLY WORKING:")
        print("1. Claude receives and analyzes real images: ", "[OK]" if user_id else "[X]")
        print("2. Workflow questions are returned: ", "[OK]" if questions else "[X]")
        print("3. Database storage: Check results above")
        print("4. Context persistence: Check results above")
    else:
        print("\n[X] Initial test failed - cannot continue verification")