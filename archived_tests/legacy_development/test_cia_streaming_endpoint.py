#!/usr/bin/env python3
"""
Test CIA Agent's intelligent GPT-5 extraction via streaming endpoint.
"""

import asyncio
import json
import httpx
from datetime import datetime

async def test_cia_streaming():
    """Test intelligent GPT-5 extraction with streaming endpoint."""
    
    base_url = "http://localhost:8008"
    
    # Test conversation turns
    conversation_turns = [
        "I need someone to install a new deck in my backyard. We're thinking about a 20x15 foot composite deck.",
        "My budget is around $15,000 to $20,000. We want it done before summer, maybe in April.",
        "The address is 123 Maple Street in Austin, Texas 78701. My name is John Smith.",
        "Oh, I forgot to mention - we also want built-in lighting and maybe a pergola on one side.",
        "My email is john.smith@example.com and phone is 555-123-4567. Can contractors start next month?"
    ]
    
    user_id = "test-user-123"
    session_id = "test-session-789"
    
    collected_info = {}
    
    print("=" * 60)
    print("Testing CIA Intelligent GPT-5 Extraction via Streaming")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i, message in enumerate(conversation_turns, 1):
            print(f"\nTurn {i}: {message[:100]}...")
            
            try:
                # Send message to CIA streaming endpoint
                response = await client.post(
                    f"{base_url}/api/cia/stream",
                    json={
                        "user_id": user_id,
                        "message": message,
                        "session_id": session_id,
                        "stream": False  # Get full response, not SSE stream
                    }
                )
                
                if response.status_code == 200:
                    # Parse SSE response
                    content = response.text
                    lines = content.strip().split('\n')
                    
                    for line in lines:
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                
                                # Check for extracted info
                                if data.get('type') == 'extraction':
                                    extracted = data.get('data', {})
                                    print(f"[EXTRACTED] {json.dumps(extracted, indent=2)}")
                                    collected_info.update(extracted)
                                
                                # Check for AI response
                                elif data.get('type') == 'message':
                                    print(f"[AI RESPONSE] {data.get('content', '')[:200]}...")
                                
                                # Check for bid card updates
                                elif data.get('type') == 'bid_card_update':
                                    bid_card = data.get('data', {})
                                    print(f"[BID CARD] Progress: {bid_card.get('completion_percentage', 0)}%")
                                    if bid_card.get('fields'):
                                        print(f"   Fields: {list(bid_card['fields'].keys())}")
                                
                            except json.JSONDecodeError:
                                pass
                    
                else:
                    print(f"[ERROR] Status {response.status_code}")
                    print(f"   Response: {response.text[:500]}")
                
                # Small delay between turns
                await asyncio.sleep(1)
                
            except httpx.TimeoutException:
                print(f"[TIMEOUT] Request timed out (60s)")
            except Exception as e:
                print(f"[ERROR] {e}")
    
    print("\n" + "=" * 60)
    print("Final Collected Information:")
    print("=" * 60)
    print(json.dumps(collected_info, indent=2))
    
    # Check what was successfully extracted
    expected_fields = [
        "project_type", "location_address", "budget_min", "budget_max",
        "timeline_start", "contact_name", "contact_email", "contact_phone",
        "project_details", "urgency_level"
    ]
    
    print("\nField Extraction Summary:")
    extracted_count = 0
    for field in expected_fields:
        if field in collected_info or any(field in str(v) for v in collected_info.values() if isinstance(v, dict)):
            print(f"[OK] {field}: Found")
            extracted_count += 1
        else:
            print(f"[MISSING] {field}: Not extracted")
    
    success_rate = (extracted_count / len(expected_fields)) * 100
    
    print(f"\n[STATS] Extraction Success Rate: {success_rate:.1f}% ({extracted_count}/{len(expected_fields)} fields)")
    
    if success_rate >= 70:
        print("[SUCCESS] INTELLIGENT EXTRACTION WORKING!")
    elif success_rate >= 50:
        print("[PARTIAL] Extraction partially working")
    else:
        print("[WARNING] Extraction needs improvement")

if __name__ == "__main__":
    print("Starting CIA Streaming Test...")
    print("Backend should be running on http://localhost:8008")
    asyncio.run(test_cia_streaming())