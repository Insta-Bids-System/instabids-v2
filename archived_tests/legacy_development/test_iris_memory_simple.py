#!/usr/bin/env python3
"""
Simple test of IRIS memory system
"""

import requests
import json
import time

def test_iris_memory():
    """Test IRIS memory system"""
    
    print("IRIS MEMORY SYSTEM TEST")
    print("=" * 50)
    
    # Test session
    session_id = f"iris_test_{int(time.time())}"
    user_id = f"homeowner_{int(time.time())}"
    
    print(f"Session: {session_id}")
    print(f"Homeowner: {user_id}")
    print("-" * 50)
    
    # Test 1: First message
    print("\n1. First message - introduce Sarah")
    
    msg1 = {
        "message": "Hi! I'm Sarah and I want a modern farmhouse kitchen",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen"
    }
    
    try:
        response1 = requests.post("http://localhost:8008/api/iris/chat", json=msg1, timeout=30)
        
        if response1.status_code == 200:
            result1 = response1.json()
            print("SUCCESS: Got response")
            print(f"Response: {result1['response'][:100]}...")
            conversation_id = result1.get('conversation_id')
        else:
            print(f"FAILED: {response1.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    
    time.sleep(2)
    
    # Test 2: Check name memory
    print("\n2. Second message - test name memory")
    
    msg2 = {
        "message": "What's my name?",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen"
    }
    
    try:
        response2 = requests.post("http://localhost:8008/api/iris/chat", json=msg2, timeout=30)
        
        if response2.status_code == 200:
            result2 = response2.json()
            response_text = result2['response'].lower()
            
            if 'sarah' in response_text:
                print("SUCCESS: IRIS remembered name 'Sarah'")
            else:
                print("FAILED: IRIS did not remember name")
            
            print(f"Response: {result2['response'][:100]}...")
        else:
            print(f"FAILED: {response2.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    time.sleep(2)
    
    # Test 3: Check project memory
    print("\n3. Third message - test project memory")
    
    msg3 = {
        "message": "What room and style did I mention?",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen"
    }
    
    try:
        response3 = requests.post("http://localhost:8008/api/iris/chat", json=msg3, timeout=30)
        
        if response3.status_code == 200:
            result3 = response3.json()
            response_text = result3['response'].lower()
            
            kitchen_remembered = 'kitchen' in response_text
            style_remembered = 'modern' in response_text and 'farmhouse' in response_text
            
            print(f"Kitchen remembered: {'YES' if kitchen_remembered else 'NO'}")
            print(f"Style remembered: {'YES' if style_remembered else 'NO'}")
            print(f"Response: {result3['response'][:150]}...")
        else:
            print(f"FAILED: {response3.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 4: Check database
    print("\n4. Database persistence check")
    
    if conversation_id:
        try:
            conv_response = requests.get(f"http://localhost:8008/conversations/{conversation_id}", timeout=10)
            
            if conv_response.status_code == 200:
                conv_data = conv_response.json()
                messages = conv_data.get('messages', [])
                print(f"SUCCESS: Found conversation with {len(messages)} messages")
                
                user_msgs = [m for m in messages if m.get('sender_type') == 'user']
                agent_msgs = [m for m in messages if m.get('sender_type') == 'agent']
                
                print(f"User messages: {len(user_msgs)}")
                print(f"Agent messages: {len(agent_msgs)}")
                
            else:
                print(f"FAILED: Conversation not found ({conv_response.status_code})")
                
        except Exception as e:
            print(f"ERROR checking database: {e}")
    
    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    test_iris_memory()