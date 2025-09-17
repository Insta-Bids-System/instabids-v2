#!/usr/bin/env python3
"""
Test IRIS actual memory system - check if unified conversation system is working
"""

import requests
import json
import time

def test_iris_actual_memory_system():
    """Test what memory system IRIS is actually using"""
    
    print("TESTING IRIS ACTUAL MEMORY SYSTEM")
    print("=" * 50)
    
    # Use unique session for clear testing
    timestamp = int(time.time())
    user_id = f"test_homeowner_{timestamp}"
    session_id = f"iris_unified_test_{timestamp}"
    
    print(f"Testing with:")
    print(f"  Homeowner ID: {user_id}")
    print(f"  Session ID: {session_id}")
    print("-" * 50)
    
    # Test 1: Send message to IRIS
    print("\nSTEP 1: Send message to IRIS")
    
    iris_message = {
        "message": "Hi, I'm Sarah and I want to design a modern farmhouse kitchen with white cabinets",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen"
    }
    
    try:
        response = requests.post(
            "http://localhost:8008/api/iris/chat", 
            json=iris_message, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ IRIS responded successfully")
            print(f"Response: {result.get('response', '')[:150]}...")
            
            conversation_id = result.get('conversation_id')
            print(f"Conversation ID: {conversation_id}")
            
        else:
            print(f"❌ IRIS failed: Status {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR calling IRIS: {e}")
        return False
    
    time.sleep(2)
    
    # Test 2: Check unified conversations table
    print("\nSTEP 2: Check unified_conversations table")
    
    if conversation_id:
        try:
            # Try the unified conversation endpoint
            unified_response = requests.get(
                f"http://localhost:8008/api/conversations/{conversation_id}",
                timeout=10
            )
            
            if unified_response.status_code == 200:
                conv_data = unified_response.json()
                print("✅ Found conversation in unified system")
                print(f"Conversation type: {conv_data.get('conversation_type', 'unknown')}")
                print(f"Entity type: {conv_data.get('entity_type', 'unknown')}")
                print(f"Agent type: {conv_data.get('metadata', {}).get('agent_type', 'unknown')}")
                
                # Check messages
                messages = conv_data.get('messages', [])
                print(f"Messages found: {len(messages)}")
                
                user_msgs = [m for m in messages if m.get('sender_type') == 'user']
                agent_msgs = [m for m in messages if m.get('sender_type') == 'agent']
                
                print(f"  User messages: {len(user_msgs)}")
                print(f"  Agent messages: {len(agent_msgs)}")
                
                if agent_msgs:
                    print("  Sample agent message:", agent_msgs[0].get('content', '')[:100])
                
                # Check memory
                memory = conv_data.get('memory', [])
                print(f"Memory entries: {len(memory)}")
                
                if memory:
                    for mem in memory:
                        print(f"  Memory: {mem.get('memory_type')} - {mem.get('memory_key')}")
                
            else:
                print(f"❌ Unified conversation not found: Status {unified_response.status_code}")
                print(f"Error: {unified_response.text}")
                
        except Exception as e:
            print(f"❌ ERROR checking unified conversations: {e}")
    
    # Test 3: Send follow-up to test memory
    print("\nSTEP 3: Test memory with follow-up message")
    
    followup_message = {
        "message": "What's my name and what room am I designing?",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen"
    }
    
    try:
        followup_response = requests.post(
            "http://localhost:8008/api/iris/chat",
            json=followup_message,
            timeout=30
        )
        
        if followup_response.status_code == 200:
            followup_result = followup_response.json()
            response_text = followup_result.get('response', '').lower()
            
            print("✅ IRIS follow-up response received")
            
            # Check if IRIS remembered the name and room
            name_remembered = 'sarah' in response_text
            room_remembered = 'kitchen' in response_text
            style_remembered = 'farmhouse' in response_text or 'modern' in response_text
            
            print(f"Name memory (Sarah): {'✅ YES' if name_remembered else '❌ NO'}")
            print(f"Room memory (kitchen): {'✅ YES' if room_remembered else '❌ NO'}")  
            print(f"Style memory (modern farmhouse): {'✅ YES' if style_remembered else '❌ NO'}")
            
            print(f"Response excerpt: {followup_result.get('response', '')[:200]}...")
            
            if name_remembered and room_remembered:
                print("✅ IRIS MEMORY IS WORKING - Unified system operational")
            else:
                print("❌ IRIS MEMORY NOT WORKING - May not be using unified system")
                
        else:
            print(f"❌ Follow-up failed: Status {followup_response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR in follow-up test: {e}")
    
    # Test 4: Check what system IRIS is actually configured to use
    print("\nSTEP 4: Check IRIS configuration")
    
    try:
        # Look for IRIS endpoints and configuration
        health_response = requests.get("http://localhost:8008/", timeout=5)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            endpoints = health_data.get('endpoints', [])
            
            iris_endpoints = [ep for ep in endpoints if 'iris' in ep.lower()]
            print(f"IRIS endpoints available: {iris_endpoints}")
            
            if '/api/iris/' in endpoints:
                print("✅ IRIS API is registered in main backend")
            else:
                print("❌ IRIS API not found in main backend")
                
    except Exception as e:
        print(f"❌ ERROR checking configuration: {e}")
    
    print("\n" + "=" * 50)
    print("IRIS MEMORY SYSTEM TEST COMPLETE")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    test_iris_actual_memory_system()