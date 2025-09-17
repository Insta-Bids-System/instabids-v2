#!/usr/bin/env python3
"""
Test IRIS functionality with JJ Thompson's actual user account
This will prove once and for all if IRIS is actually saving photos or just claiming to
"""

import requests
import json
import time
import base64
from datetime import datetime

# JJ Thompson's actual user ID from database
JJ_USER_ID = "01087874-747b-4159-8735-5ebb8715ff84"
BASE_URL = "http://localhost:8008"

def create_test_image():
    """Create a simple test image"""
    # Small 1x1 PNG
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82'
    return "data:image/png;base64," + base64.b64encode(png_data).decode('utf-8')

def check_database_before():
    """Check what's in database before test"""
    print("\n=== DATABASE CHECK BEFORE TEST ===")
    
    # Direct database check via API
    response = requests.post(
        f"{BASE_URL}/api/admin/query",
        json={
            "query": f"""
                SELECT COUNT(*) as photo_count
                FROM property_photos pp
                JOIN properties p ON pp.property_id = p.id
                WHERE p.user_id = '{JJ_USER_ID}'
            """
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Photos in database before test: {data}")
    else:
        print(f"Could not check database: {response.status_code}")
    
    return response.json() if response.status_code == 200 else None

def test_iris_photo_upload():
    """Test IRIS photo upload with JJ Thompson's user"""
    
    print("\n=== TESTING IRIS PHOTO UPLOAD FOR JJ THOMPSON ===")
    print(f"User ID: {JJ_USER_ID}")
    print(f"Timestamp: {datetime.now()}")
    
    # Check database before
    before_count = check_database_before()
    
    # Create unique session ID
    session_id = f"jj_test_{int(time.time())}"
    print(f"\nSession ID: {session_id}")
    
    # Step 1: Upload image with trigger_image_workflow
    print("\n1. Uploading test image...")
    
    test_image = create_test_image()
    
    upload_request = {
        "message": "Here's a photo of my roof that needs repair",
        "user_id": JJ_USER_ID,
        "session_id": session_id,
        "context_type": "property",
        "images": [{
            "data": test_image,
            "filename": f"roof_damage_{int(time.time())}.png",
            "size": 1000,
            "type": "image/png"
        }],
        "trigger_image_workflow": True
    }
    
    print("   Sending request to IRIS...")
    response = requests.post(
        f"{BASE_URL}/api/iris/unified-chat",
        json=upload_request,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"   ERROR: Request failed with status {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    data = response.json()
    print(f"   Success: {data.get('success')}")
    print(f"   Response preview: {data.get('response', '')[:200]}")
    
    # Check for workflow questions
    workflow_questions = data.get("workflow_questions", [])
    print(f"\n   Workflow questions received: {len(workflow_questions)}")
    
    if workflow_questions:
        # Step 2: Answer first workflow question (storage location)
        print("\n2. Answering storage location question...")
        first_question = workflow_questions[0]
        print(f"   Question: {first_question.get('question')}")
        print(f"   Options: {first_question.get('options')}")
        
        # Choose Property Photos
        answer_request = {
            "user_id": JJ_USER_ID,
            "session_id": session_id,
            "context_type": "property",
            "workflow_response": {
                "question_id": first_question.get("id"),
                "selected_option": "Property Photos"
            }
        }
        
        print("   Sending answer: Property Photos")
        response2 = requests.post(
            f"{BASE_URL}/api/iris/unified-chat",
            json=answer_request,
            timeout=30
        )
        
        if response2.status_code != 200:
            print(f"   ERROR: Answer failed with status {response2.status_code}")
            return False
            
        data2 = response2.json()
        print(f"   Success: {data2.get('success')}")
        
        # Check for second workflow question (room selection)
        workflow_questions2 = data2.get("workflow_questions", [])
        if workflow_questions2:
            print("\n3. Answering room selection question...")
            second_question = workflow_questions2[0]
            print(f"   Question: {second_question.get('question')}")
            print(f"   Options: {second_question.get('options')}")
            
            # Choose Exterior
            answer_request2 = {
                "user_id": JJ_USER_ID,
                "session_id": session_id,
                "context_type": "property",
                "workflow_response": {
                    "question_id": second_question.get("id"),
                    "selected_option": "Exterior"
                }
            }
            
            print("   Sending answer: Exterior")
            response3 = requests.post(
                f"{BASE_URL}/api/iris/unified-chat",
                json=answer_request2,
                timeout=30
            )
            
            if response3.status_code == 200:
                data3 = response3.json()
                print(f"   Success: {data3.get('success')}")
                print(f"   Response: {data3.get('response', '')[:200]}")
    
    # Step 4: Verify in database
    print("\n4. VERIFYING DATABASE STORAGE...")
    time.sleep(2)  # Give it time to save
    
    # Check via API endpoint
    verify_response = requests.post(
        f"{BASE_URL}/api/admin/query",
        json={
            "query": f"""
                SELECT 
                    pp.id,
                    pp.original_filename,
                    pp.room_id,
                    pp.created_at,
                    pr.room_type
                FROM property_photos pp
                JOIN properties p ON pp.property_id = p.id
                LEFT JOIN property_rooms pr ON pp.room_id = pr.id
                WHERE p.user_id = '{JJ_USER_ID}'
                AND pp.created_at > NOW() - INTERVAL '5 minutes'
                ORDER BY pp.created_at DESC
            """
        }
    )
    
    if verify_response.status_code == 200:
        results = verify_response.json()
        print("\n=== DATABASE VERIFICATION RESULTS ===")
        print(json.dumps(results, indent=2))
        
        if results and len(results) > 0:
            print("\n   SUCCESS: Photo found in database!")
            return True
        else:
            print("\n   FAILURE: No new photos in database!")
            return False
    else:
        print(f"\n   Could not verify: {verify_response.status_code}")
        return False

def check_iris_memory():
    """Check if IRIS has any memory of the conversation"""
    print("\n=== CHECKING IRIS MEMORY ===")
    
    response = requests.post(
        f"{BASE_URL}/api/admin/query",
        json={
            "query": f"""
                SELECT 
                    key,
                    value,
                    updated_at
                FROM unified_conversation_memory
                WHERE user_id = '{JJ_USER_ID}'
                ORDER BY updated_at DESC
                LIMIT 5
            """
        }
    )
    
    if response.status_code == 200:
        print("Memory entries:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Could not check memory: {response.status_code}")

if __name__ == "__main__":
    print("=" * 60)
    print("IRIS PHOTO STORAGE TEST - JJ THOMPSON")
    print("=" * 60)
    
    # Run the test
    success = test_iris_photo_upload()
    
    # Check memory
    check_iris_memory()
    
    # Final verdict
    print("\n" + "=" * 60)
    if success:
        print("TEST PASSED: Photo was saved to database")
    else:
        print("TEST FAILED: IRIS claims to save but doesn't actually save")
    print("=" * 60)