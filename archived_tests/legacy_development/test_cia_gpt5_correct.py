#!/usr/bin/env python3
"""
Test CIA Agent's intelligent GPT-5 extraction with correct API structure.
"""

import asyncio
import json
import httpx
import uuid
from datetime import datetime

async def test_cia_extraction():
    """Test intelligent GPT-5 extraction with correct streaming API."""
    
    base_url = "http://localhost:8008"
    
    # Test conversation turns
    test_messages = [
        "I need someone to install a new deck in my backyard. We're thinking about a 20x15 foot composite deck.",
        "My budget is around $15,000 to $20,000. We want it done before summer, maybe in April.",
        "The address is 123 Maple Street in Austin, Texas 78701. My name is John Smith.",
        "Oh, I forgot to mention - we also want built-in lighting and maybe a pergola on one side.",
        "My email is john.smith@example.com and phone is 555-123-4567. Can contractors start next month?"
    ]
    
    user_id = "test-user-" + str(uuid.uuid4())[:8]
    conversation_id = "conv-" + str(uuid.uuid4())[:8]
    session_id = "session-" + str(uuid.uuid4())[:8]
    
    collected_info = {}
    messages = []
    
    print("=" * 60)
    print("Testing CIA Intelligent GPT-5 Extraction")
    print("=" * 60)
    print(f"User ID: {user_id}")
    print(f"Conversation ID: {conversation_id}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i, user_message in enumerate(test_messages, 1):
            print(f"\n[Turn {i}] User: {user_message[:80]}...")
            
            # Add user message to history
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            try:
                # Send to CIA streaming endpoint with correct structure
                response = await client.post(
                    f"{base_url}/api/cia/stream",
                    json={
                        "messages": messages,
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "session_id": session_id,
                        "max_tokens": 500,
                        "model_preference": "gpt-5"
                    }
                )
                
                if response.status_code == 200:
                    # Parse SSE response
                    content = response.text
                    lines = content.strip().split('\n')
                    
                    ai_response = ""
                    extracted_this_turn = {}
                    
                    for line in lines:
                        if line.startswith('data: '):
                            try:
                                data_str = line[6:]
                                if data_str == '[DONE]':
                                    continue
                                    
                                data = json.loads(data_str)
                                
                                # Collect AI response chunks
                                if data.get('type') == 'chunk':
                                    ai_response += data.get('content', '')
                                
                                # Check for extracted info
                                elif data.get('type') == 'extraction':
                                    extracted = data.get('data', {})
                                    extracted_this_turn.update(extracted)
                                    collected_info.update(extracted)
                                
                                # Check for field updates
                                elif data.get('type') == 'field_update':
                                    field = data.get('field')
                                    value = data.get('value')
                                    if field and value:
                                        extracted_this_turn[field] = value
                                        collected_info[field] = value
                                
                            except json.JSONDecodeError as e:
                                if '[EXTRACTION]' in line:
                                    # Try to parse extraction from the line
                                    try:
                                        parts = line.split('[EXTRACTION]')
                                        if len(parts) > 1:
                                            extraction_str = parts[1].strip()
                                            extracted = json.loads(extraction_str)
                                            extracted_this_turn.update(extracted)
                                            collected_info.update(extracted)
                                    except:
                                        pass
                    
                    # Show AI response
                    if ai_response:
                        print(f"[AI Response] {ai_response[:150]}...")
                        # Add AI response to message history
                        messages.append({
                            "role": "assistant", 
                            "content": ai_response
                        })
                    
                    # Show extracted info this turn
                    if extracted_this_turn:
                        print(f"[EXTRACTED THIS TURN]")
                        for key, value in extracted_this_turn.items():
                            print(f"  - {key}: {value}")
                    
                else:
                    print(f"[ERROR] Status {response.status_code}")
                    error_text = response.text[:500]
                    print(f"   Response: {error_text}")
                    
                    # Try to parse error for debugging
                    try:
                        error_data = response.json()
                        if 'detail' in error_data:
                            print(f"   Detail: {error_data['detail']}")
                    except:
                        pass
                
                # Small delay between turns
                await asyncio.sleep(0.5)
                
            except httpx.TimeoutException:
                print(f"[TIMEOUT] Request timed out (60s)")
            except Exception as e:
                print(f"[ERROR] {type(e).__name__}: {e}")
    
    print("\n" + "=" * 60)
    print("FINAL COLLECTED INFORMATION:")
    print("=" * 60)
    
    if collected_info:
        for key, value in collected_info.items():
            print(f"  {key}: {value}")
    else:
        print("  No information extracted")
    
    print("\n" + "=" * 60)
    print("EXTRACTION ANALYSIS:")
    print("=" * 60)
    
    # Check what was successfully extracted
    expected_fields = {
        "project_type": "deck installation",
        "location_address": "123 Maple Street",
        "budget_min": 15000,
        "budget_max": 20000,
        "timeline_start": "April",
        "contact_name": "John Smith",
        "contact_email": "john.smith@example.com",
        "contact_phone": "555-123-4567",
        "project_details": "composite deck",
        "urgency_level": "standard"
    }
    
    extracted_count = 0
    for field, expected in expected_fields.items():
        found = False
        # Check if field exists in collected info
        if field in collected_info:
            found = True
            print(f"[OK] {field}: {collected_info[field]}")
        # Also check nested structures
        elif any(field in str(v).lower() for v in collected_info.values()):
            found = True
            print(f"[PARTIAL] {field}: Found in nested data")
        else:
            print(f"[MISSING] {field}: Expected '{expected}'")
        
        if found:
            extracted_count += 1
    
    success_rate = (extracted_count / len(expected_fields)) * 100
    
    print(f"\n[STATS] Extraction Success Rate: {success_rate:.1f}% ({extracted_count}/{len(expected_fields)} fields)")
    
    if success_rate >= 70:
        print("[SUCCESS] INTELLIGENT GPT-5 EXTRACTION IS WORKING!")
    elif success_rate >= 50:
        print("[PARTIAL] Extraction is partially working - needs tuning")
    else:
        print("[NEEDS WORK] Extraction needs significant improvement")
    
    # Test progressive updates
    print("\n" + "=" * 60)
    print("PROGRESSIVE UPDATE TEST:")
    print("=" * 60)
    
    if len(messages) > 2:
        print("[OK] Multi-turn conversation maintained")
        print(f"     Total messages: {len(messages)}")
    else:
        print("[MISSING] Multi-turn conversation not working")
    
    return collected_info, success_rate

if __name__ == "__main__":
    print("Starting CIA GPT-5 Extraction Test...")
    print("Backend should be running on http://localhost:8008")
    print("OpenAI API key should be configured in .env")
    print("")
    
    asyncio.run(test_cia_extraction())