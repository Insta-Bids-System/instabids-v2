"""
Test IRIS photo upload with actual storage to property_photos table
"""

import requests
import json
import base64
from datetime import datetime

# Create a simple test image (1x1 red pixel)
test_image_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAQNJ3FQAAAABJRU5ErkJggg=="

# Test with workflow response to trigger storage
url = "http://localhost:8008/api/iris/unified-chat"

# Step 1: Upload image with workflow trigger
print("Step 1: Uploading image with workflow trigger...")
payload = {
    "message": "I'm uploading 1 image. Please analyze and ask me where to put it.",
    "user_id": "11111111-1111-1111-1111-111111111111",
    "session_id": f"test-session-{int(datetime.now().timestamp())}",
    "property_id": "d1ce83f1-900a-4677-bbdc-375db1f7bcca",
    "images": [{
        "data": test_image_base64,
        "filename": "backyard_test.jpg",
        "size": 1000,
        "type": "image/jpeg"
    }],
    "trigger_image_workflow": True
}

response = requests.post(url, json=payload)
print(f"Response status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Success: {data.get('success')}")
    print(f"Response preview: {data.get('response', '')[:300]}")
    print(f"Workflow questions: {data.get('workflow_questions', [])}")
    
    # Step 2: Select "Property Photos" option
    if data.get('workflow_questions'):
        print("\nStep 2: Selecting 'Property Photos' option...")
        session_id = payload['session_id']
        
        workflow_payload = {
            "message": "For question 1, I choose: Property Photos",
            "user_id": "11111111-1111-1111-1111-111111111111",
            "session_id": session_id,
            "property_id": "d1ce83f1-900a-4677-bbdc-375db1f7bcca",
            "workflow_response": {
                "question_index": 0,
                "selected_option": "Property Photos"
            },
            "images": [{
                "data": test_image_base64,
                "filename": "backyard_test.jpg",
                "size": 1000,
                "type": "image/jpeg"
            }]
        }
        
        response2 = requests.post(url, json=workflow_payload)
        print(f"Response status: {response2.status_code}")
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"Success: {data2.get('success')}")
            print(f"Response: {data2.get('response', '')[:500]}")
            
            # Step 3: Verify photo was saved
            print("\nStep 3: Checking if photo was saved to database...")
            import os
            from supabase import create_client
            
            supabase_url = "https://xrhgrthdcaymxuqcgrmj.supabase.co"
            supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhyaGdydGhkY2F5bXh1cWNncm1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2NTcyMDYsImV4cCI6MjA2OTIzMzIwNn0.BriGLA2FE_e_NJl8B-3ps1W6ZAuK6a5HpTwBGy-6rmE"
            
            supabase = create_client(supabase_url, supabase_key)
            
            # Check property_photos table
            result = supabase.table("property_photos").select("*").order("created_at", desc=True).limit(5).execute()
            
            if result.data:
                print(f"Found {len(result.data)} recent photos:")
                for photo in result.data:
                    print(f"  - ID: {photo.get('id')}")
                    print(f"    Filename: {photo.get('original_filename')}")
                    print(f"    Created: {photo.get('created_at')}")
                    print(f"    Description: {photo.get('ai_description')}")
            else:
                print("No photos found in property_photos table")
        else:
            print(f"Error: {response2.text}")
else:
    print(f"Error: {response.text}")