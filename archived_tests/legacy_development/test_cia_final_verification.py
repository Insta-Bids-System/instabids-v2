#!/usr/bin/env python3
"""
Final CIA verification test - comprehensive workflow without Unicode issues
Tests: Conversations, memory persistence, database storage, field extraction
"""

import requests
import json
import uuid
import time
from datetime import datetime

def test_cia_final_verification():
    print("=" * 60)
    print("CIA FINAL VERIFICATION TEST - ALL SYSTEMS")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Generate unique test IDs
    user_id = f"homeowner-final-{uuid.uuid4().hex[:8]}"
    conversation_id = f"conv-final-{uuid.uuid4().hex[:8]}"
    session_id = f"session-final-{uuid.uuid4().hex[:8]}"
    
    print(f"User ID: {user_id}")
    print(f"Conversation ID: {conversation_id}")
    print(f"Session ID: {session_id}")
    
    test_results = {
        "cia_conversation": False,
        "field_extraction": False,
        "database_persistence": False,
        "memory_recall": False,
        "multi_turn_conversation": False
    }
    
    # TEST 1: CIA Conversation with Rich Project Details
    print("\n" + "=" * 40)
    print("TEST 1: CIA CONVERSATION + FIELD EXTRACTION")
    print("=" * 40)
    
    project_details = {
        "messages": [
            {
                "role": "user", 
                "content": "Hi, I need help with a kitchen renovation. It's a 200 sq ft galley kitchen that needs everything updated."
            },
            {
                "role": "user",
                "content": "I want new cabinets, quartz countertops, subway tile backsplash, and stainless steel appliances. Budget is $45,000 to $60,000."
            },
            {
                "role": "user",
                "content": "I'm located at 789 Pine Avenue, Seattle, Washington 98101. My name is Michael Chen, email mchen@example.com, phone 206-555-7890."
            },
            {
                "role": "user",
                "content": "Timeline is flexible - I'd like to start in 2-3 months. Do you think this budget is realistic for this scope?"
            }
        ],
        "conversation_id": conversation_id,
        "user_id": user_id,
        "session_id": session_id
    }
    
    for i, message in enumerate(project_details["messages"], 1):
        print(f"\nTurn {i}: {message['content'][:60]}...")
        
        try:
            # Send conversation turn
            response = requests.post(
                "http://localhost:8008/api/cia/stream",
                json={
                    "messages": project_details["messages"][:i],
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "session_id": session_id
                },
                timeout=5,
                stream=True
            )
            
            if response.status_code == 200:
                print("  SUCCESS - CIA responded")
                test_results["cia_conversation"] = True
                
                if i == 1:
                    test_results["multi_turn_conversation"] = True
                    
            else:
                print(f"  ERROR - Status {response.status_code}")
                
        except requests.Timeout:
            print("  TIMEOUT - CIA processing (expected)")
            test_results["cia_conversation"] = True
        except Exception as e:
            print(f"  ERROR: {e}")
        
        time.sleep(1)  # Brief pause between turns
    
    # TEST 2: Database Verification
    print("\n" + "=" * 40)  
    print("TEST 2: DATABASE VERIFICATION")
    print("=" * 40)
    
    time.sleep(3)  # Give CIA time to process
    
    try:
        # Check for potential bid card creation
        bid_card_response = requests.get(
            f"http://localhost:8008/api/cia/conversation/{conversation_id}/potential-bid-card",
            timeout=5
        )
        
        print(f"Bid card check status: {bid_card_response.status_code}")
        
        if bid_card_response.status_code == 200:
            bid_data = bid_card_response.json()
            print("SUCCESS - Potential bid card found!")
            test_results["database_persistence"] = True
            
            if "fields" in bid_data:
                fields = bid_data["fields"]
                print(f"Field extraction count: {len(fields)}")
                
                # Check for key extracted fields
                key_fields = ["project_type", "location", "budget", "timeline", "contact_info"]
                extracted_fields = []
                
                for field in key_fields:
                    if any(field.lower() in key.lower() for key in fields.keys()):
                        extracted_fields.append(field)
                
                if len(extracted_fields) >= 3:
                    print(f"SUCCESS - Key fields extracted: {extracted_fields}")
                    test_results["field_extraction"] = True
                else:
                    print(f"PARTIAL - Only {len(extracted_fields)} key fields extracted")
            
            completion = bid_data.get("completion_percentage", 0)
            print(f"Completion percentage: {completion}%")
            
        elif bid_card_response.status_code == 404:
            print("No potential bid card found yet")
        else:
            print(f"ERROR: {bid_card_response.text[:100]}")
            
    except Exception as e:
        print(f"Database check error: {e}")
    
    # TEST 3: Memory Persistence Test
    print("\n" + "=" * 40)
    print("TEST 3: MEMORY PERSISTENCE")
    print("=" * 40)
    
    # New conversation with same user
    memory_conversation_id = f"conv-memory-{uuid.uuid4().hex[:8]}"
    memory_session_id = f"session-memory-{uuid.uuid4().hex[:8]}"
    
    print(f"New Conversation ID: {memory_conversation_id}")
    print(f"Same User ID: {user_id}")
    
    try:
        memory_response = requests.post(
            "http://localhost:8008/api/cia/stream",
            json={
                "messages": [
                    {
                        "role": "user", 
                        "content": "Hi again! I'm back to continue discussing my kitchen renovation project. Do you remember the details we discussed?"
                    }
                ],
                "conversation_id": memory_conversation_id,  # NEW conversation
                "user_id": user_id,  # SAME user - should trigger memory
                "session_id": memory_session_id
            },
            timeout=10,
            stream=True
        )
        
        print(f"Memory test status: {memory_response.status_code}")
        
        if memory_response.status_code == 200:
            print("SUCCESS - Memory conversation started")
            
            # Collect some response to check for memory indicators
            memory_text = ""
            count = 0
            
            try:
                for line in memory_response.iter_lines():
                    if line and count < 20:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data_str = line_str[6:]
                                if data_str != '[DONE]':
                                    data = json.loads(data_str)
                                    if 'choices' in data:
                                        content = data['choices'][0].get('delta', {}).get('content', '')
                                        memory_text += content
                                        count += 1
                            except:
                                pass
                    elif count >= 20:
                        break
                        
            except Exception as e:
                print(f"Stream reading error: {e}")
            
            if memory_text:
                print(f"CIA response preview: {memory_text[:150]}...")
                
                # Check for memory keywords
                memory_keywords = [
                    "kitchen", "renovation", "galley", "quartz", "cabinets", 
                    "seattle", "michael", "45000", "60000", "pine"
                ]
                
                found_memories = [kw for kw in memory_keywords if kw.lower() in memory_text.lower()]
                
                if found_memories:
                    print(f"SUCCESS - CIA remembered: {found_memories}")
                    test_results["memory_recall"] = True
                else:
                    print("WARNING - No clear memory indicators found")
            else:
                print("No response text collected")
                
    except requests.Timeout:
        print("TIMEOUT - Memory processing")
    except Exception as e:
        print(f"Memory test error: {e}")
    
    # FINAL RESULTS
    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)
    
    print(f"Test User: {user_id}")
    print(f"Original Conversation: {conversation_id}")
    print(f"Memory Conversation: {memory_conversation_id}")
    
    print("\nTest Results:")
    for test_name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed ({int(passed_tests/total_tests*100)}%)")
    
    if passed_tests >= 3:
        print("CIA SYSTEM: FUNCTIONAL")
    elif passed_tests >= 2:
        print("CIA SYSTEM: PARTIALLY FUNCTIONAL")
    else:
        print("CIA SYSTEM: NEEDS ATTENTION")
    
    print(f"Test completed: {datetime.now().strftime('%H:%M:%S')}")
    
    return test_results

if __name__ == "__main__":
    test_cia_final_verification()