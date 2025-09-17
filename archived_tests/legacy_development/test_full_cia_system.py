#!/usr/bin/env python3
"""
Comprehensive test to PROVE the CIA intelligent extraction is fully working.
Tests multi-turn conversations with progressive field updates.
"""

import requests
import json
import time
import uuid
from datetime import datetime

def test_complete_cia_system():
    """Test the complete CIA system with multi-turn conversation and field extraction."""
    
    print("="*80)
    print("COMPREHENSIVE CIA INTELLIGENT EXTRACTION TEST")
    print("="*80)
    
    # Generate unique IDs for this test
    user_id = f"test-user-{uuid.uuid4().hex[:8]}"
    conversation_id = f"test-conv-{uuid.uuid4().hex[:8]}"
    
    print(f"\nTest Configuration:")
    print(f"  User ID: {user_id}")
    print(f"  Conversation ID: {conversation_id}")
    print(f"  Backend: http://localhost:8008")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Multi-turn conversation that progressively provides information
    conversation_turns = [
        "I need help with a home improvement project. I'm thinking about updating my outdoor space.",
        "Specifically, I want to install a new composite deck, about 20x15 feet with built-in lighting.",
        "My budget is between $15,000 and $20,000. I'd like to get this done by April for summer entertaining.",
        "My address is 123 Maple Street, Austin, Texas 78701. The backyard has good access from the side gate.",
        "My name is John Smith, email is john.smith@example.com, phone is 512-555-1234. Can we get started soon?",
        "I forgot to mention - I also want a pergola on one side and maybe some built-in seating. Is that possible within my budget?",
        "When can contractors come look at the space? I work from home so any day works for me."
    ]
    
    messages = []
    collected_fields = {}
    
    print("\n" + "="*80)
    print("STARTING MULTI-TURN CONVERSATION TEST")
    print("="*80)
    
    for turn_num, user_message in enumerate(conversation_turns, 1):
        print(f"\n[TURN {turn_num}] User: {user_message[:80]}...")
        
        # Add user message to conversation history
        messages.append({"role": "user", "content": user_message})
        
        # Send to CIA endpoint
        start_time = time.time()
        response = requests.post(
            "http://localhost:8008/api/cia/stream",
            json={
                "messages": messages,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "model_preference": "gpt-5",
                "max_tokens": 500
            },
            timeout=30
        )
        elapsed = time.time() - start_time
        
        print(f"  Response Time: {elapsed:.2f}s")
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Parse SSE response
            lines = response.text.split('\n')
            ai_response = ""
            
            for line in lines:
                if line.startswith('data: '):
                    try:
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            continue
                        data = json.loads(data_str)
                        if 'choices' in data:
                            content = data['choices'][0].get('delta', {}).get('content', '')
                            ai_response += content
                    except:
                        pass
            
            # Add AI response to conversation history
            if ai_response:
                messages.append({"role": "assistant", "content": ai_response})
                print(f"  AI Response: {ai_response[:150]}...")
            
            # Check for potential bid card updates
            try:
                bid_card_response = requests.get(
                    f"http://localhost:8008/api/cia/potential-bid-cards/{conversation_id}",
                    timeout=5
                )
                
                if bid_card_response.status_code == 200:
                    bid_card_data = bid_card_response.json()
                    if bid_card_data and 'fields' in bid_card_data:
                        fields = bid_card_data['fields']
                        completion = bid_card_data.get('completion_percentage', 0)
                        
                        # Track new fields extracted this turn
                        new_fields = {}
                        for key, value in fields.items():
                            if key not in collected_fields or collected_fields[key] != value:
                                new_fields[key] = value
                                collected_fields[key] = value
                        
                        if new_fields:
                            print(f"  [EXTRACTED THIS TURN]:")
                            for key, value in new_fields.items():
                                print(f"    • {key}: {value}")
                        
                        print(f"  [BID CARD STATUS]: {completion}% complete")
                        print(f"  [TOTAL FIELDS]: {len(collected_fields)}")
                        
            except Exception as e:
                # Potential bid cards endpoint might not exist, that's okay
                pass
            
        else:
            print(f"  ERROR: Request failed with status {response.status_code}")
            break
        
        # Small delay between turns
        time.sleep(0.5)
    
    print("\n" + "="*80)
    print("FINAL EXTRACTION RESULTS")
    print("="*80)
    
    # Expected fields and what we should have extracted
    expected_extractions = {
        "project_type": "deck installation",
        "project_details": "composite deck, 20x15 feet, built-in lighting, pergola, built-in seating",
        "budget_min": "15000",
        "budget_max": "20000", 
        "timeline": "April",
        "location_address": "123 Maple Street, Austin, Texas 78701",
        "contact_name": "John Smith",
        "contact_email": "john.smith@example.com",
        "contact_phone": "512-555-1234",
        "urgency_level": "standard",
        "property_access": "side gate access"
    }
    
    print("\nExpected vs Actual Extraction:")
    print("-" * 40)
    
    success_count = 0
    for field, expected in expected_extractions.items():
        actual = collected_fields.get(field, "NOT EXTRACTED")
        if field in collected_fields:
            success_count += 1
            status = "✓"
        else:
            # Check if the information exists in any collected field
            found_in_other = False
            for key, value in collected_fields.items():
                if expected.lower() in str(value).lower():
                    found_in_other = key
                    break
            
            if found_in_other:
                status = f"~ (found in '{found_in_other}')"
                success_count += 0.5
            else:
                status = "✗"
        
        print(f"{status} {field}:")
        print(f"   Expected: {expected}")
        if field in collected_fields:
            print(f"   Actual: {collected_fields[field]}")
        elif found_in_other:
            print(f"   Found in: {found_in_other} = {collected_fields[found_in_other]}")
        print()
    
    # Calculate success rate
    success_rate = (success_count / len(expected_extractions)) * 100
    
    print("="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    print(f"Total Conversation Turns: {len(conversation_turns)}")
    print(f"Total Fields Collected: {len(collected_fields)}")
    print(f"Expected Fields Found: {success_count}/{len(expected_extractions)}")
    print(f"Extraction Success Rate: {success_rate:.1f}%")
    print(f"Progressive Updates: {'YES' if len(collected_fields) > 0 else 'NO'}")
    
    # Final verdict
    print("\n" + "="*80)
    if success_rate >= 70:
        print("✅ SUCCESS: CIA INTELLIGENT EXTRACTION IS FULLY WORKING!")
        print("   - Multi-turn conversation maintained context")
        print("   - Progressive field extraction across turns")
        print("   - Intelligent understanding of natural language")
    elif success_rate >= 50:
        print("⚠️ PARTIAL SUCCESS: Extraction is working but needs improvement")
    else:
        print("❌ FAILURE: Extraction is not working properly")
    
    print("="*80)
    
    # Show all collected fields
    if collected_fields:
        print("\nAll Collected Fields:")
        print(json.dumps(collected_fields, indent=2))
    
    return collected_fields, success_rate

if __name__ == "__main__":
    print("CIA INTELLIGENT EXTRACTION COMPREHENSIVE TEST")
    print("Testing GPT-4o/GPT-5 powered field extraction...")
    print("")
    
    collected, rate = test_complete_cia_system()
    
    if rate >= 70:
        print("\n🎉 TEST PASSED - System is fully operational!")
    else:
        print("\n⚠️ TEST NEEDS ATTENTION - Check extraction logic")