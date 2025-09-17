#!/usr/bin/env python3
"""
Simple test of IRIS conversational flows and image categorization
"""

import requests
import json
import time

def test_iris_conversational_flows():
    """Test IRIS conversational flows and image categorization"""
    
    print("IRIS CONVERSATIONAL FLOWS TEST")
    print("=" * 50)
    
    # Test session
    session_id = f"iris_test_{int(time.time())}"
    user_id = f"homeowner_{int(time.time())}"
    
    print(f"Session: {session_id}")
    print(f"Homeowner: {user_id}")
    print("-" * 50)
    
    # Test 1: Current space analysis
    print("\nTEST 1: Current Space Image Analysis")
    
    current_space_msg = {
        "message": "Here are photos of my current kitchen. What needs to change?",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen",
        "image_category": "current",
        "uploaded_images": ["mock_current_kitchen_image.jpg"]
    }
    
    try:
        response1 = requests.post("http://localhost:8008/api/iris/chat", json=current_space_msg, timeout=30)
        
        if response1.status_code == 200:
            result1 = response1.json()
            print("SUCCESS: IRIS processed current space images")
            print(f"Response: {result1['response'][:150]}...")
            
            # Check for current space context in response
            response_text = result1['response'].lower()
            if any(phrase in response_text for phrase in ['current', 'existing', 'what you have']):
                print("GOOD: IRIS recognized current space context")
            else:
                print("NOTE: Current space context may not be explicit")
                
            conversation_id = result1.get('conversation_id')
        else:
            print(f"FAILED: Status {response1.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    
    time.sleep(3)
    
    # Test 2: Ideal inspiration analysis
    print("\nTEST 2: Ideal Inspiration Image Analysis")
    
    ideal_inspiration_msg = {
        "message": "Now here's my dream kitchen inspiration - this modern farmhouse style is exactly what I want!",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen",
        "image_category": "ideal", 
        "uploaded_images": ["mock_inspiration_kitchen.jpg"]
    }
    
    try:
        response2 = requests.post("http://localhost:8008/api/iris/chat", json=ideal_inspiration_msg, timeout=30)
        
        if response2.status_code == 200:
            result2 = response2.json()
            print("SUCCESS: IRIS processed ideal inspiration images")
            print(f"Response: {result2['response'][:150]}...")
            
            # Check for inspiration/ideal context
            response_text = result2['response'].lower()
            if any(phrase in response_text for phrase in ['inspiration', 'dream', 'ideal', 'modern farmhouse']):
                print("GOOD: IRIS recognized ideal inspiration context")
            else:
                print("NOTE: Ideal inspiration context may not be explicit")
                
        else:
            print(f"FAILED: Status {response2.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    time.sleep(3)
    
    # Test 3: Compare current vs ideal
    print("\nTEST 3: Current vs Ideal Comparison")
    
    comparison_msg = {
        "message": "Can you help me understand the differences between my current kitchen and my inspiration? What are the key changes I should make?",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen"
    }
    
    try:
        response3 = requests.post("http://localhost:8008/api/iris/chat", json=comparison_msg, timeout=30)
        
        if response3.status_code == 200:
            result3 = response3.json()
            print("SUCCESS: IRIS provided comparison analysis")
            print(f"Response: {result3['response'][:200]}...")
            
            # Check for comparison elements
            response_text = result3['response'].lower()
            current_ref = any(phrase in response_text for phrase in ['current', 'existing', 'what you have now'])
            ideal_ref = any(phrase in response_text for phrase in ['inspiration', 'dream', 'want', 'modern farmhouse'])
            
            print(f"References current space: {'YES' if current_ref else 'NO'}")
            print(f"References ideal vision: {'YES' if ideal_ref else 'NO'}")
            
            if current_ref and ideal_ref:
                print("EXCELLENT: IRIS successfully integrated both contexts")
            elif current_ref or ideal_ref:
                print("GOOD: IRIS referenced at least one context")
            else:
                print("NOTE: IRIS may not be explicitly comparing contexts")
                
        else:
            print(f"FAILED: Status {response3.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 4: Check fallback response with tags
    print("\nTEST 4: Auto-Tag Generation Test")
    
    tag_test_msg = {
        "message": "I uploaded some modern minimalist bathroom inspiration with white subway tiles and black fixtures",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "bathroom",
        "image_category": "ideal",
        "uploaded_images": ["mock_bathroom_inspiration.jpg"]
    }
    
    try:
        response4 = requests.post("http://localhost:8008/api/iris/chat", json=tag_test_msg, timeout=30)
        
        if response4.status_code == 200:
            result4 = response4.json()
            print("SUCCESS: IRIS processed bathroom inspiration")
            
            # Check for tag-related content
            response_text = result4['response']
            
            expected_elements = ['modern', 'minimalist', 'bathroom', 'white', 'subway', 'tiles', 'black', 'fixtures']
            found_elements = [elem for elem in expected_elements if elem.lower() in response_text.lower()]
            
            print(f"Design elements mentioned: {found_elements}")
            
            if len(found_elements) >= 4:
                print("EXCELLENT: IRIS recognized multiple design elements")
            elif len(found_elements) >= 2:
                print("GOOD: IRIS recognized some design elements")
            else:
                print("NOTE: IRIS may not be extracting specific elements")
                
        else:
            print(f"FAILED: Status {response4.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 5: Database persistence check
    print("\nTEST 5: Database Persistence Check")
    
    if conversation_id:
        try:
            db_response = requests.get(f"http://localhost:8008/conversations/{conversation_id}", timeout=10)
            
            if db_response.status_code == 200:
                conv_data = db_response.json()
                messages = conv_data.get('messages', [])
                
                print(f"SUCCESS: Found conversation with {len(messages)} messages")
                
                user_msgs = [m for m in messages if m.get('sender_type') == 'user']
                agent_msgs = [m for m in messages if m.get('sender_type') == 'agent']
                
                print(f"User messages: {len(user_msgs)}")
                print(f"Agent messages: {len(agent_msgs)}")
                
                if len(agent_msgs) >= 2:
                    print("EXCELLENT: Multiple agent responses saved")
                elif len(agent_msgs) >= 1:
                    print("GOOD: At least one agent response saved")
                else:
                    print("WARNING: Agent responses may not be saving")
                    
                # Check for memory entries
                memory_entries = conv_data.get('memory', [])
                print(f"Memory entries: {len(memory_entries)}")
                
            else:
                print(f"WARNING: Cannot retrieve conversation ({db_response.status_code})")
                
        except Exception as e:
            print(f"ERROR checking database: {e}")
    
    print("\n" + "=" * 50)
    print("IRIS CONVERSATIONAL FLOWS TEST COMPLETE")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    test_iris_conversational_flows()