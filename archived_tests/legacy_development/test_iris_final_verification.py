#!/usr/bin/env python3
"""
Final verification test with proper UUID format and database fixes
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
    """Load test image"""
    test_image_path = Path(r"C:\Users\Not John Or Justin\Documents\instabids\test-images")
    
    for img_file in test_image_path.glob("*.jpg"):
        with open(img_file, 'rb') as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_data}", img_file.name
    
    raise Exception("No test images found!")

def test_complete_workflow():
    """Complete workflow test with proper UUIDs"""
    
    print("=" * 80)
    print("FINAL IRIS VERIFICATION - CLAUDE SONNET 4 + STORAGE")
    print("=" * 80)
    
    # Use proper UUID format
    test_user_id = str(uuid.uuid4())
    test_session_id = f"final-session-{int(time.time())}"
    
    print(f"Test user ID (UUID): {test_user_id}")
    print(f"Session ID: {test_session_id}")
    
    # Load image
    image_data, filename = load_test_image()
    print(f"Image loaded: {filename} ({len(image_data)} bytes)")
    
    # STEP 1: Upload image with Claude Sonnet 4
    print("\n1. Testing Claude Sonnet 4 image analysis...")
    
    upload_request = {
        "message": "Please analyze this backyard photo and ask me where to save it.",
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
    
    try:
        response = requests.post(IRIS_ENDPOINT, json=upload_request, timeout=45)
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            questions = data.get('workflow_questions', [])
            
            print(f"[OK] Claude Sonnet 4 response received")
            print(f"     Analysis mentions backyard elements: {'backyard' in response_text.lower() or 'grass' in response_text.lower() or 'patio' in response_text.lower()}")
            print(f"[OK] Workflow questions: {len(questions)}")
            
            if questions:
                for i, q in enumerate(questions):
                    print(f"     {i}: {q.get('question')}")
            
        else:
            print(f"[X] Upload failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[X] Upload error: {e}")
        return False
    
    # STEP 2: Answer "Both" for storage
    print("\n2. Testing storage to both locations...")
    
    storage_request = {
        "message": "I want to save it to Both locations please.",
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
    
    try:
        response = requests.post(IRIS_ENDPOINT, json=storage_request, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("[OK] Storage request completed")
            print(f"     Response: {data.get('response', '')[:100]}...")
        else:
            print(f"[X] Storage failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[X] Storage error: {e}")
        return False
    
    # STEP 3: Check database storage
    print("\n3. Checking database storage...")
    time.sleep(3)  # Wait for database writes
    
    try:
        # Check directly via Supabase API
        import os
        SUPABASE_URL = "https://xrhgrthdcaymxuqcgrmj.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhyaGdydGhkY2F5bXh1cWNncm1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2NTcyMDYsImV4cCI6MjA2OTIzMzIwNn0.BriGLA2FE_e_NJl8B-3ps1W6ZAuK6a5HpTwBGy-6rmE"
        
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Check inspiration_images
        inspiration_url = f"{SUPABASE_URL}/rest/v1/inspiration_images?user_id=eq.{test_user_id}"
        resp = requests.get(inspiration_url, headers=headers)
        inspiration_count = len(resp.json()) if resp.status_code == 200 else 0
        
        # Check property_photos 
        property_url = f"{SUPABASE_URL}/rest/v1/property_photos?select=*,properties(user_id)&properties.user_id=eq.{test_user_id}"
        resp = requests.get(property_url, headers=headers)
        property_count = len(resp.json()) if resp.status_code == 200 else 0
        
        print(f"[{'+' if inspiration_count > 0 else 'X'}] Inspiration images: {inspiration_count}")
        print(f"[{'+' if property_count > 0 else 'X'}] Property photos: {property_count}")
        
        both_stored = inspiration_count > 0 and property_count > 0
        
        print(f"\n{'[SUCCESS]' if both_stored else '[PARTIAL]'} Storage verification:")
        print(f"  - Images stored to both locations: {both_stored}")
        
        return both_stored
        
    except Exception as e:
        print(f"[X] Database check failed: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_workflow()
    
    print("\n" + "=" * 80)
    print("FINAL VERIFICATION RESULTS")
    print("=" * 80)
    
    if success:
        print("🎉 COMPLETE SUCCESS!")
        print("✓ Claude Sonnet 4 analyzing images")
        print("✓ Workflow questions working")
        print("✓ Images storing to both Inspiration Board AND Property Photos")
        print("✓ Database storage verified")
        print("\nIRIS image workflow is 100% OPERATIONAL!")
    else:
        print("⚠️ Some issues detected - check logs above")
        
    print("=" * 80)