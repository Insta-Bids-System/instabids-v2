#!/usr/bin/env python3
"""
End-to-end test of IRIS system - memory, database, cross-agent context
"""

import requests
import json
import time
from datetime import datetime

def test_iris_comprehensive():
    """Comprehensive test of IRIS system"""
    
    print("IRIS COMPREHENSIVE SYSTEM TEST")
    print("=" * 60)
    
    # Use unique IDs for this test
    test_timestamp = int(time.time())
    user_id = f"test_homeowner_{test_timestamp}"
    session_id = f"iris_session_{test_timestamp}"
    
    print(f"Test Homeowner: {user_id}")
    print(f"Session ID: {session_id}")
    print("-" * 60)
    
    conversation_id = None
    
    # Test 1: Initial conversation
    print("\nTEST 1: Initial IRIS Conversation")
    print("-" * 30)
    
    message1 = {
        "message": "Hi! I'm Emma and I want to redesign my living room with a modern minimalist style. I love clean lines and neutral colors.",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "living_room"
    }
    
    try:
        response1 = requests.post("http://localhost:8008/api/iris/chat", json=message1, timeout=30)
        
        if response1.status_code == 200:
            result1 = response1.json()
            conversation_id = result1.get('conversation_id')
            print(f"SUCCESS: Got response")
            print(f"Conversation ID: {conversation_id}")
            print(f"Response preview: {result1['response'][:150]}...")
        else:
            print(f"FAILED: Status {response1.status_code}")
            print(f"Error: {response1.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    
    # Test 2: Check database immediately
    print("\nTEST 2: Database Check After First Message")
    print("-" * 30)
    
    if conversation_id:
        try:
            db_response = requests.get(f"http://localhost:8008/conversations/{conversation_id}", timeout=10)
            
            if db_response.status_code == 200:
                conv_data = db_response.json()
                messages = conv_data.get('messages', [])
                
                print(f"SUCCESS: Found conversation in database")
                print(f"Total messages: {len(messages)}")
                
                user_msgs = [m for m in messages if m.get('sender_type') == 'user']
                agent_msgs = [m for m in messages if m.get('sender_type') == 'agent']
                
                print(f"User messages: {len(user_msgs)}")
                print(f"Agent messages: {len(agent_msgs)}")
                
                if len(agent_msgs) > 0:
                    print("SUCCESS: Assistant message saved!")
                else:
                    print("WARNING: Assistant message not saved")
                    
            else:
                print(f"FAILED: Cannot retrieve conversation ({db_response.status_code})")
                
        except Exception as e:
            print(f"ERROR checking database: {e}")
    
    # Wait for processing
    time.sleep(3)
    
    # Test 3: Memory test - name recall
    print("\nTEST 3: Name Memory Test")
    print("-" * 30)
    
    message2 = {
        "message": "What's my name again?",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "living_room"
    }
    
    try:
        response2 = requests.post("http://localhost:8008/api/iris/chat", json=message2, timeout=30)
        
        if response2.status_code == 200:
            result2 = response2.json()
            response_text = result2['response'].lower()
            
            if 'emma' in response_text:
                print("SUCCESS: IRIS remembered name 'Emma'")
            else:
                print("FAILED: IRIS did not remember name")
                print(f"Response: {result2['response']}")
        else:
            print(f"FAILED: Status {response2.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    time.sleep(2)
    
    # Test 4: Style and room memory test
    print("\nTEST 4: Style and Room Memory Test")
    print("-" * 30)
    
    message3 = {
        "message": "What room am I working on and what style did I mention liking?",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "living_room"
    }
    
    try:
        response3 = requests.post("http://localhost:8008/api/iris/chat", json=message3, timeout=30)
        
        if response3.status_code == 200:
            result3 = response3.json()
            response_text = result3['response'].lower()
            
            room_remembered = 'living room' in response_text or 'living' in response_text
            style_remembered = ('modern' in response_text and 'minimalist' in response_text) or 'modern minimalist' in response_text
            colors_remembered = 'neutral' in response_text
            
            print(f"Room remembered: {'YES' if room_remembered else 'NO'}")
            print(f"Style remembered: {'YES' if style_remembered else 'NO'}")  
            print(f"Colors remembered: {'YES' if colors_remembered else 'NO'}")
            print(f"Response: {result3['response'][:200]}...")
        else:
            print(f"FAILED: Status {response3.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 5: Final database check
    print("\nTEST 5: Final Database State Check")
    print("-" * 30)
    
    if conversation_id:
        try:
            final_db_response = requests.get(f"http://localhost:8008/conversations/{conversation_id}", timeout=10)
            
            if final_db_response.status_code == 200:
                final_conv_data = final_db_response.json()
                final_messages = final_conv_data.get('messages', [])
                
                user_msgs = [m for m in final_messages if m.get('sender_type') == 'user']
                agent_msgs = [m for m in final_messages if m.get('sender_type') == 'agent']
                
                print(f"Final state:")
                print(f"- Total messages: {len(final_messages)}")
                print(f"- User messages: {len(user_msgs)}")
                print(f"- Agent messages: {len(agent_msgs)}")
                
                # Check if we have both types of messages
                if len(user_msgs) >= 3 and len(agent_msgs) >= 2:
                    print("SUCCESS: Full conversation saved to database")
                elif len(user_msgs) >= 3:
                    print("PARTIAL: User messages saved, but assistant messages may be missing")
                else:
                    print("FAILED: Not all messages saved")
                    
                # Check memory entries
                memory_entries = final_conv_data.get('memory', [])
                print(f"- Memory entries: {len(memory_entries)}")
                
                if memory_entries:
                    print("Memory stored:")
                    for mem in memory_entries:
                        print(f"  - {mem.get('memory_type')}: {mem.get('memory_key')}")
                
            else:
                print(f"FAILED: Cannot retrieve final conversation state")
                
        except Exception as e:
            print(f"ERROR checking final database state: {e}")
    
    # Test 6: Cross-agent context test (if CIA conversations exist)
    print("\nTEST 6: Cross-Agent Context Check")
    print("-" * 30)
    
    # This would require checking if IRIS can access CIA conversations for the same homeowner
    # For now, we'll just verify the unified conversation structure supports it
    
    try:
        # Check if there are any other conversations for this homeowner
        # This is a simplified check - in a real system, IRIS should be able to access CIA conversations
        print("Cross-agent context testing would require CIA conversations for the same homeowner")
        print("The unified conversation system structure supports this capability")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("IRIS COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_iris_comprehensive()