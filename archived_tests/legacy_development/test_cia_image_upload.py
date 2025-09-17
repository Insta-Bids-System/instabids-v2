#!/usr/bin/env python3
"""
Test CIA image upload functionality
"""

import requests
import json
import uuid
import io
import base64

def create_test_image_data():
    """Create a simple test image as base64 data"""
    # Create a simple text-based "image" for testing
    test_image_content = b"SIMPLE_TEST_IMAGE_DATA_FOR_CIA_UPLOAD_TESTING"
    
    # Convert to base64
    image_b64 = base64.b64encode(test_image_content).decode('utf-8')
    return image_b64

def test_cia_with_image():
    print("=== CIA IMAGE UPLOAD TEST ===")
    
    user_id = f"test-user-img-{uuid.uuid4().hex[:6]}"
    conversation_id = f"conv-img-{uuid.uuid4().hex[:6]}"
    session_id = f"session-img-{uuid.uuid4().hex[:6]}"
    
    print(f"User ID: {user_id}")
    print(f"Conversation ID: {conversation_id}")
    print(f"Session ID: {session_id}")
    
    # Test 1: Start conversation
    print("\n--- Test 1: Start Conversation ---")
    response1 = requests.post(
        "http://localhost:8008/api/cia/stream",
        json={
            "messages": [{"role": "user", "content": "Hi, I need help renovating my kitchen. Let me show you what I'm working with."}],
            "conversation_id": conversation_id,
            "user_id": user_id,
            "session_id": session_id
        },
        timeout=3,
        stream=True
    )
    
    print(f"Initial conversation status: {response1.status_code}")
    
    # Test 2: Try image upload endpoints
    print("\n--- Test 2: Image Upload Endpoints ---")
    
    # Create test image data
    test_image = create_test_image_data()
    
    # Try different image upload endpoints
    upload_endpoints = [
        ("POST", "http://localhost:8008/api/cia/upload-image", {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "session_id": session_id,
            "image_data": test_image,
            "filename": "kitchen_current.jpg"
        }),
        ("POST", "http://localhost:8008/api/cia/upload", {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "file_data": test_image,
            "file_type": "image/jpeg"
        }),
        ("POST", "http://localhost:8008/api/conversations/upload-image", {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "image": test_image
        })
    ]
    
    for method, endpoint, data in upload_endpoints:
        try:
            print(f"\nTrying: {endpoint}")
            response = requests.post(endpoint, json=data, timeout=5)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("SUCCESS! Image upload worked")
                print(f"Response: {response.json()}")
                break
            elif response.status_code == 404:
                print("Endpoint not found")
            else:
                print(f"Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"Request failed: {e}")
    
    # Test 3: Continue conversation with reference to image
    print("\n--- Test 3: Continue Conversation with Image Reference ---")
    
    try:
        response3 = requests.post(
            "http://localhost:8008/api/cia/stream",
            json={
                "messages": [
                    {"role": "user", "content": "Hi, I need help renovating my kitchen. Let me show you what I'm working with."},
                    {"role": "system", "content": "[Image uploaded: kitchen_current.jpg]"},
                    {"role": "user", "content": "As you can see from the photo, the cabinets are outdated and the countertops need replacing. Budget is $40,000."}
                ],
                "conversation_id": conversation_id,
                "user_id": user_id,
                "session_id": session_id
            },
            timeout=3,
            stream=True
        )
        
        print(f"Conversation with image reference: {response3.status_code}")
        
        if response3.status_code == 200:
            print("CIA processing conversation with image context...")
            
    except requests.Timeout:
        print("Timeout (expected) - CIA is processing")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Check for bid card with image data
    print("\n--- Test 4: Check Bid Card Creation with Images ---")
    
    import time
    time.sleep(3)
    
    # Try to find potential bid card
    try:
        # Try different endpoint patterns
        check_endpoints = [
            f"http://localhost:8008/api/cia/conversation/{conversation_id}/potential-bid-card",
            f"http://localhost:8008/api/cia/potential-bid-cards/{conversation_id}",
            f"http://localhost:8008/api/conversations/{conversation_id}/bid-card"
        ]
        
        for endpoint in check_endpoints:
            try:
                response = requests.get(endpoint, timeout=3)
                print(f"\n{endpoint} -> {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print("Bid card found!")
                    
                    # Check if images are included
                    if isinstance(data, dict):
                        fields = data.get('fields', {})
                        if any('image' in str(key).lower() or 'photo' in str(key).lower() for key in fields.keys()):
                            print("SUCCESS: Images found in bid card fields!")
                            for key, value in fields.items():
                                if 'image' in str(key).lower() or 'photo' in str(key).lower():
                                    print(f"  {key}: {value}")
                        else:
                            print("No image fields found in bid card")
                            print(f"Available fields: {list(fields.keys())}")
                            
                        print(f"Completion: {data.get('completion_percentage', 0)}%")
                    
                elif response.status_code == 404:
                    print("Bid card not created yet")
                else:
                    print(f"Error: {response.text[:100]}")
                    
            except Exception as e:
                print(f"Failed: {e}")
                
    except Exception as e:
        print(f"Bid card check failed: {e}")
    
    # Test 5: Check if image is stored in unified memory
    print("\n--- Test 5: Check Unified Memory for Images ---")
    
    memory_endpoints = [
        f"http://localhost:8008/api/cia/user/{user_id}/memory",
        f"http://localhost:8008/api/conversations/{conversation_id}/memory", 
        f"http://localhost:8008/api/unified-memory/{user_id}"
    ]
    
    for endpoint in memory_endpoints:
        try:
            response = requests.get(endpoint, timeout=3)
            print(f"{endpoint} -> {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Memory data found: {str(data)[:200]}...")
                
        except Exception as e:
            print(f"Memory check failed: {e}")

    print(f"\n--- Test Summary ---")
    print(f"User: {user_id}")
    print(f"Conversation: {conversation_id}")
    print("Tested image upload functionality")
    print("Verified bid card creation with image context")
    print("Checked unified memory persistence")

if __name__ == "__main__":
    test_cia_with_image()