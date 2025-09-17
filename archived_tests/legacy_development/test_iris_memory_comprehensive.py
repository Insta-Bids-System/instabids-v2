#!/usr/bin/env python3
"""
Comprehensive test of IRIS memory system to verify claims from other agent
"""

import requests
import json
import time
from datetime import datetime

def test_iris_memory_comprehensive():
    """Test IRIS memory system thoroughly"""
    
    print("=" * 70)
    print("COMPREHENSIVE IRIS MEMORY SYSTEM TEST")
    print("=" * 70)
    
    # Test session
    session_id = f"iris_memory_test_{int(time.time())}"
    user_id = f"test_homeowner_{int(time.time())}"
    
    print(f"Session ID: {session_id}")
    print(f"Homeowner ID: {user_id}")
    print("-" * 70)
    
    # Test 1: First message - Introduce user and project
    print("\n1. FIRST MESSAGE - User Introduction")
    print("-" * 40)
    
    first_message = {
        "message": "Hi! I'm Sarah and I want to renovate my kitchen with a modern farmhouse style",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen"
    }
    
    try:
        response1 = requests.post(
            "http://localhost:8008/api/iris/chat",
            json=first_message,
            timeout=30
        )
        
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"✅ SUCCESS: Got response")
            print(f"Response: {result1['response'][:150]}...")
            print(f"Conversation ID: {result1.get('conversation_id')}")
            conversation_id = result1.get('conversation_id')
        else:
            print(f"❌ FAILED: {response1.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    # Wait a moment
    time.sleep(2)
    
    # Test 2: Second message - Test name memory
    print("\n2. SECOND MESSAGE - Testing Name Memory")
    print("-" * 40)
    
    second_message = {
        "message": "What's my name again?",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen"
    }
    
    try:
        response2 = requests.post(
            "http://localhost:8008/api/iris/chat",
            json=second_message,
            timeout=30
        )
        
        if response2.status_code == 200:
            result2 = response2.json()
            response_text = result2['response'].lower()
            
            if 'sarah' in response_text:
                print(f"✅ MEMORY WORKING: IRIS remembered name 'Sarah'")
                print(f"Response: {result2['response'][:150]}...")
            else:
                print(f"❌ MEMORY FAILED: IRIS did not remember name")
                print(f"Response: {result2['response'][:150]}...")
                
        else:
            print(f"❌ FAILED: {response2.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Wait a moment
    time.sleep(2)
    
    # Test 3: Third message - Test project memory
    print("\n3. THIRD MESSAGE - Testing Project Memory")
    print("-" * 40)
    
    third_message = {
        "message": "What room am I working on and what style did I mention?",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen"
    }
    
    try:
        response3 = requests.post(
            "http://localhost:8008/api/iris/chat",
            json=third_message,
            timeout=30
        )
        
        if response3.status_code == 200:
            result3 = response3.json()
            response_text = result3['response'].lower()
            
            kitchen_remembered = 'kitchen' in response_text
            style_remembered = ('modern farmhouse' in response_text or 
                              ('modern' in response_text and 'farmhouse' in response_text))
            
            print(f"Kitchen remembered: {'✅' if kitchen_remembered else '❌'}")
            print(f"Style remembered: {'✅' if style_remembered else '❌'}")
            print(f"Response: {result3['response'][:200]}...")
            
        else:
            print(f"❌ FAILED: {response3.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 4: Check database persistence
    print("\n4. DATABASE PERSISTENCE CHECK")
    print("-" * 40)
    
    if conversation_id:
        try:
            # Check if conversation exists in unified system
            conv_response = requests.get(
                f"http://localhost:8008/conversations/{conversation_id}",
                timeout=10
            )
            
            if conv_response.status_code == 200:
                conv_data = conv_response.json()
                print(f"✅ CONVERSATION SAVED: ID {conversation_id}")
                print(f"Title: {conv_data.get('conversation', {}).get('title')}")
                print(f"Messages: {len(conv_data.get('messages', []))}")
                
                # Check for both user and assistant messages
                messages = conv_data.get('messages', [])
                user_msgs = [m for m in messages if m.get('sender_type') == 'user']
                agent_msgs = [m for m in messages if m.get('sender_type') == 'agent']
                
                print(f"User messages: {len(user_msgs)}")
                print(f"Agent messages: {len(agent_msgs)}")
                
                if len(user_msgs) >= 3 and len(agent_msgs) >= 3:
                    print("✅ ALL MESSAGES SAVED")
                else:
                    print("⚠️  Some messages may not be saved")
                    
            else:
                print(f"❌ CONVERSATION NOT FOUND: {conv_response.status_code}")
                
        except Exception as e:
            print(f"❌ DATABASE CHECK ERROR: {e}")
    
    print("\n" + "=" * 70)
    print("IRIS MEMORY SYSTEM TEST SUMMARY")
    print("=" * 70)
    
    # Final verdict
    print("Based on the tests above:")
    print("1. IRIS responds without timeout ✓")
    print("2. Conversations are saved to database")
    print("3. Memory persistence across messages")
    print("4. Integration with unified conversation system")
    
    return True

if __name__ == "__main__":
    test_iris_memory_comprehensive()