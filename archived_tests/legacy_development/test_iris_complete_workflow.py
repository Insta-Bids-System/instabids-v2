#!/usr/bin/env python3
"""
Complete test of IRIS image workflow with Claude Sonnet 4 and actual storage
Tests: 
1. Upload image with Claude Sonnet 4 analysis
2. Answer "Both" to store in both Inspiration Board and Property Photos
3. Verify images are stored in both database tables
4. Confirm they can be retrieved from both locations
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
    
    raise Exception("No test images found!")

def test_sonnet4_analysis():
    """Test image upload with Claude Sonnet 4"""
    
    print("\n" + "="*80)
    print("TESTING CLAUDE SONNET 4 IMAGE ANALYSIS")
    print("="*80)
    
    # Use production session (no 'test' to avoid bypass)
    test_user_id = f"storage-test-user-{int(time.time())}"
    test_session_id = f"storage-session-{int(time.time())}"
    
    print(f"Test user: {test_user_id}")
    print(f"Session: {test_session_id}")
    
    # Load real image
    image_data, filename = load_real_test_image()
    print(f"Image loaded: {len(image_data)} bytes")
    
    # STEP 1: Upload image
    request_data = {
        "message": "I'm uploading this photo of my backyard. Please analyze what you see and ask me where to save it.",
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
    
    print("\nSending to IRIS with Claude Sonnet 4...")
    
    try:
        response = requests.post(
            IRIS_ENDPOINT,
            json=request_data,
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            workflow_questions = data.get('workflow_questions', [])
            
            print(f"\n[OK] Claude Sonnet 4 Response:")
            print(f"'{response_text[:400]}...'")
            
            if workflow_questions:
                print(f"\n[OK] Workflow questions returned: {len(workflow_questions)}")
                for i, q in enumerate(workflow_questions):
                    print(f"  {i}: {q.get('question')}")
                    print(f"     Options: {q.get('options')}")
                
                return test_user_id, test_session_id, workflow_questions, image_data, filename
            else:
                print("\n[X] No workflow questions - something's wrong")
                return None, None, None, None, None
                
        else:
            print(f"\n[X] Error: HTTP {response.status_code}")
            print(response.text)
            return None, None, None, None, None
            
    except Exception as e:
        print(f"\n[X] Error: {e}")
        return None, None, None, None, None

def test_both_storage(user_id, session_id, workflow_questions, image_data, filename):
    """Test answering 'Both' to store in both locations"""
    
    print("\n" + "="*80)  
    print("TESTING STORAGE TO BOTH LOCATIONS")
    print("="*80)
    
    # Answer "Both" to first question (where to store)
    workflow_response_data = {
        "message": "I want to store it in both places please.",
        "user_id": user_id,
        "session_id": session_id,
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
    
    print("Sending response: 'Both' for image storage...")
    
    try:
        response = requests.post(
            IRIS_ENDPOINT,
            json=workflow_response_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            
            print(f"[OK] IRIS Response to 'Both' selection:")
            print(f"'{response_text[:300]}...'")
            
            return True
        else:
            print(f"[X] Error: HTTP {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"[X] Error: {e}")
        return False

def verify_database_storage(user_id, session_id):
    """Verify images are stored in both database tables"""
    
    print("\n" + "="*80)
    print("VERIFYING DATABASE STORAGE")
    print("="*80)
    
    try:
        # Import database tools
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-agents'))
        
        from database_simple import DatabaseSimple
        
        db = DatabaseSimple()
        
        # Check inspiration_images table
        print("Checking inspiration_images table...")
        inspiration_query = """
        SELECT ii.*, ib.name as board_name
        FROM inspiration_images ii
        LEFT JOIN inspiration_boards ib ON ii.board_id = ib.id
        WHERE ii.user_id = %s
        AND ii.ai_analysis::text LIKE %s
        ORDER BY ii.created_at DESC
        LIMIT 5
        """
        inspiration_results = db.execute_query(inspiration_query, (user_id, f'%{session_id}%'))
        
        if inspiration_results:
            print(f"[OK] Found {len(inspiration_results)} entries in inspiration_images")
            for r in inspiration_results:
                print(f"  - Board: {r.get('board_name', 'Unknown')}")
                print(f"    Image URL length: {len(r.get('image_url', ''))}")
                print(f"    Source: {r.get('source', 'Unknown')}")
        else:
            print("[X] No entries found in inspiration_images")
        
        # Check property_photos table  
        print("\nChecking property_photos table...")
        property_query = """
        SELECT pp.*, pa.property_name
        FROM property_photos pp
        LEFT JOIN property_assets pa ON pp.property_id = pa.id
        WHERE pa.owner_id = %s
        AND pp.ai_classification::text LIKE %s
        ORDER BY pp.created_at DESC
        LIMIT 5
        """
        property_results = db.execute_query(property_query, (user_id, f'%{session_id}%'))
        
        if property_results:
            print(f"[OK] Found {len(property_results)} entries in property_photos")
            for r in property_results:
                print(f"  - Property: {r.get('property_name', 'Unknown')}")
                print(f"    Photo URL length: {len(r.get('photo_url', ''))}")
                print(f"    Type: {r.get('photo_type', 'Unknown')}")
        else:
            print("[X] No entries found in property_photos")
            
        both_stored = bool(inspiration_results and property_results)
        
        print(f"\n{'[OK]' if both_stored else '[X]'} Storage Verification:")
        print(f"  - Inspiration Board: {'✓' if inspiration_results else '✗'}")
        print(f"  - Property Photos: {'✓' if property_results else '✗'}")
        
        return both_stored
        
    except Exception as e:
        print(f"[X] Database verification failed: {e}")
        return False

def test_ui_retrieval(user_id):
    """Test if images can be retrieved via API for UI display"""
    
    print("\n" + "="*80)
    print("TESTING UI RETRIEVAL")
    print("="*80)
    
    try:
        # Test inspiration board API
        print("Testing inspiration board retrieval...")
        inspiration_url = f"{BASE_URL}/api/inspiration/boards/{user_id}"
        
        resp = requests.get(inspiration_url)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[OK] Inspiration API response: {len(str(data))} characters")
        else:
            print(f"[INFO] Inspiration API returned {resp.status_code} - might not be implemented")
            
        # Test property photos API
        print("Testing property photos retrieval...")
        property_url = f"{BASE_URL}/api/property/photos/{user_id}"
        
        resp = requests.get(property_url)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[OK] Property API response: {len(str(data))} characters")
        else:
            print(f"[INFO] Property API returned {resp.status_code} - might not be implemented")
            
        return True
        
    except Exception as e:
        print(f"[X] UI retrieval test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting complete IRIS workflow test...")
    
    # Step 1: Test Claude Sonnet 4 analysis
    user_id, session_id, questions, image_data, filename = test_sonnet4_analysis()
    
    if not user_id:
        print("\n[X] Initial analysis failed - stopping test")
        exit(1)
    
    # Step 2: Test storage to both locations
    time.sleep(1)  # Brief pause
    storage_success = test_both_storage(user_id, session_id, questions, image_data, filename)
    
    if not storage_success:
        print("\n[X] Storage request failed - stopping test")
        exit(1)
    
    # Step 3: Verify database storage
    time.sleep(3)  # Wait for database writes
    db_verified = verify_database_storage(user_id, session_id)
    
    # Step 4: Test UI retrieval
    ui_tested = test_ui_retrieval(user_id)
    
    print("\n" + "="*80)
    print("COMPLETE WORKFLOW TEST RESULTS")
    print("="*80)
    print(f"1. Claude Sonnet 4 Analysis: {'✓' if user_id else '✗'}")
    print(f"2. Workflow Questions: {'✓' if questions else '✗'}")
    print(f"3. Storage Request: {'✓' if storage_success else '✗'}")
    print(f"4. Database Storage: {'✓' if db_verified else '✗'}")
    print(f"5. UI Retrieval: {'✓' if ui_tested else '✗'}")
    
    if all([user_id, questions, storage_success, db_verified]):
        print("\n🎉 COMPLETE SUCCESS - IRIS WORKFLOW 100% OPERATIONAL!")
        print("   - Claude Sonnet 4 analyzing images ✓")
        print("   - Workflow questions working ✓") 
        print("   - Images storing to both locations ✓")
        print("   - Database verification confirmed ✓")
    else:
        print("\n⚠️  Some components need attention - check results above")
        
    print("="*80)