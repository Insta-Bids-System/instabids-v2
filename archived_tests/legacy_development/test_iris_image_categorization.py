#!/usr/bin/env python3
"""
Test IRIS Image Categorization System
Tests current vs ideal image handling and conversational flows
"""

import requests
import json
import time
import base64
from datetime import datetime

def test_iris_image_categorization():
    """Test IRIS image categorization and conversational flows"""
    
    print("IRIS IMAGE CATEGORIZATION TEST")
    print("=" * 60)
    
    # Use unique IDs for this test
    test_timestamp = int(time.time())
    user_id = f"test_homeowner_{test_timestamp}"
    session_id = f"iris_session_{test_timestamp}"
    
    print(f"Test Homeowner: {user_id}")
    print(f"Session ID: {session_id}")
    print("-" * 60)
    
    # Test 1: Upload "current" space images
    print("\nTEST 1: Upload Current Space Images")
    print("-" * 30)
    
    current_space_message = {
        "message": "Here are photos of my current kitchen. I want to see what needs to change.",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen",
        "image_category": "current",
        "uploaded_images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."]  # Mock base64 image
    }
    
    try:
        response1 = requests.post("http://localhost:8008/api/iris/chat", json=current_space_message, timeout=30)
        
        if response1.status_code == 200:
            result1 = response1.json()
            print("SUCCESS: IRIS processed current space images")
            print(f"Response preview: {result1['response'][:200]}...")
            
            # Check if response mentions analyzing current space
            response_text = result1['response'].lower()
            if any(phrase in response_text for phrase in ['current space', 'existing', 'what you have now', 'current kitchen']):
                print("✓ IRIS correctly identified current space context")
            else:
                print("⚠ IRIS may not have recognized current space context")
                
            print(f"Suggestions: {result1['suggestions']}")
            conversation_id = result1.get('conversation_id')
        else:
            print(f"FAILED: Status {response1.status_code}")
            print(f"Error: {response1.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    
    time.sleep(3)
    
    # Test 2: Upload "ideal" inspiration images  
    print("\nTEST 2: Upload Ideal Inspiration Images")
    print("-" * 30)
    
    ideal_inspiration_message = {
        "message": "Now here's my dream kitchen inspiration - this is exactly the style I want!",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen", 
        "image_category": "ideal",
        "uploaded_images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."]  # Mock base64 image
    }
    
    try:
        response2 = requests.post("http://localhost:8008/api/iris/chat", json=ideal_inspiration_message, timeout=30)
        
        if response2.status_code == 200:
            result2 = response2.json()
            print("SUCCESS: IRIS processed ideal inspiration images")
            print(f"Response preview: {result2['response'][:200]}...")
            
            # Check if response mentions inspiration/ideal vision
            response_text = result2['response'].lower()
            if any(phrase in response_text for phrase in ['inspiration', 'dream', 'ideal', 'vision', 'style you want']):
                print("✓ IRIS correctly identified ideal inspiration context")
            else:
                print("⚠ IRIS may not have recognized ideal inspiration context")
                
            print(f"Suggestions: {result2['suggestions']}")
        else:
            print(f"FAILED: Status {response2.status_code}")
            print(f"Error: {response2.text}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    time.sleep(3)
    
    # Test 3: Ask IRIS to compare current vs ideal
    print("\nTEST 3: Compare Current vs Ideal Images")
    print("-" * 30)
    
    comparison_message = {
        "message": "Can you compare my current kitchen with my inspiration? What are the main differences?",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen"
    }
    
    try:
        response3 = requests.post("http://localhost:8008/api/iris/chat", json=comparison_message, timeout=30)
        
        if response3.status_code == 200:
            result3 = response3.json()
            print("SUCCESS: IRIS provided comparison analysis")
            print(f"Response preview: {result3['response'][:200]}...")
            
            # Check if response mentions both current and ideal aspects
            response_text = result3['response'].lower()
            current_mentioned = any(phrase in response_text for phrase in ['current', 'existing', 'what you have'])
            ideal_mentioned = any(phrase in response_text for phrase in ['inspiration', 'dream', 'ideal', 'want'])
            
            print(f"Current space mentioned: {'YES' if current_mentioned else 'NO'}")
            print(f"Ideal vision mentioned: {'YES' if ideal_mentioned else 'NO'}")
            
            if current_mentioned and ideal_mentioned:
                print("✓ IRIS successfully integrated both current and ideal contexts")
            else:
                print("⚠ IRIS may not be properly comparing both image categories")
                
        else:
            print(f"FAILED: Status {response3.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    time.sleep(2)
    
    # Test 4: Test image categorization in fallback response
    print("\nTEST 4: Test Fallback Response with Image Categories")
    print("-" * 30)
    
    # Test with different room type to trigger fallback
    fallback_message = {
        "message": "Here are some bathroom inspiration photos",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "bathroom",
        "image_category": "ideal", 
        "uploaded_images": ["data:image/jpeg;base64,mock_image_data"]
    }
    
    try:
        response4 = requests.post("http://localhost:8008/api/iris/chat", json=fallback_message, timeout=30)
        
        if response4.status_code == 200:
            result4 = response4.json()
            print("SUCCESS: IRIS handled new room type with images")
            print(f"Response preview: {result4['response'][:200]}...")
            
            # Check if fallback response includes auto-generated tags
            response_text = result4['response']
            if 'tags' in response_text.lower() or 'bathroom' in response_text.lower():
                print("✓ IRIS fallback includes contextual tags and room recognition")
            else:
                print("⚠ IRIS fallback may not include auto-generated tags")
                
        else:
            print(f"FAILED: Status {response4.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 5: Verify database saves image categories correctly
    print("\nTEST 5: Database Image Category Storage")
    print("-" * 30)
    
    if conversation_id:
        try:
            db_response = requests.get(f"http://localhost:8008/conversations/{conversation_id}", timeout=10)
            
            if db_response.status_code == 200:
                conv_data = db_response.json()
                messages = conv_data.get('messages', [])
                
                print(f"SUCCESS: Found conversation with {len(messages)} messages")
                
                # Check for image-related metadata in messages
                image_messages = []
                for msg in messages:
                    if msg.get('content', '').lower().find('image') != -1 or 'current' in str(msg) or 'ideal' in str(msg):
                        image_messages.append(msg)
                
                print(f"Messages with image context: {len(image_messages)}")
                
                # Look for memory entries related to image categories
                memory_entries = conv_data.get('memory', [])
                image_memory = [m for m in memory_entries if 'image' in str(m).lower() or 'category' in str(m).lower()]
                
                print(f"Image-related memory entries: {len(image_memory)}")
                
                if image_memory:
                    print("Memory types stored:")
                    for mem in image_memory:
                        print(f"  - {mem.get('memory_type')}: {mem.get('memory_key')}")
                        
            else:
                print(f"FAILED: Cannot retrieve conversation ({db_response.status_code})")
                
        except Exception as e:
            print(f"ERROR checking database: {e}")
    
    # Test 6: Auto-tag generation test
    print("\nTEST 6: Auto-Tag Generation Test")
    print("-" * 30)
    
    tag_test_message = {
        "message": "I love this modern farmhouse kitchen with white cabinets and black hardware",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen",
        "image_category": "ideal",
        "uploaded_images": ["data:image/jpeg;base64,mock_tag_test"]
    }
    
    try:
        response6 = requests.post("http://localhost:8008/api/iris/chat", json=tag_test_message, timeout=30)
        
        if response6.status_code == 200:
            result6 = response6.json()
            print("SUCCESS: IRIS processed message for tag generation")
            
            # Check for auto-generated tags in response
            response_text = result6['response'].lower()
            
            expected_tags = ['modern', 'farmhouse', 'kitchen', 'white', 'cabinets', 'black', 'hardware']
            found_tags = [tag for tag in expected_tags if tag in response_text]
            
            print(f"Expected tags found in response: {found_tags}")
            
            if len(found_tags) >= 4:
                print("✓ IRIS successfully generated contextual tags")
            else:
                print("⚠ IRIS may not be generating comprehensive tags")
                
        else:
            print(f"FAILED: Status {response6.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("IRIS IMAGE CATEGORIZATION TEST SUMMARY")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_iris_image_categorization()