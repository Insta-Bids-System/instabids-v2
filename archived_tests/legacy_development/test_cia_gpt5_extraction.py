#!/usr/bin/env python3
"""
Test CIA Agent's intelligent GPT-5 extraction with valid API key.
"""

import asyncio
import json
import httpx
from datetime import datetime

async def test_cia_intelligent_extraction():
    """Test intelligent GPT-5 extraction with multi-turn conversation."""
    
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
    project_id = "test-project-456"
    session_id = "test-session-789"
    
    collected_info = {}
    
    print("=" * 60)
    print("Testing CIA Intelligent GPT-5 Extraction")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i, message in enumerate(conversation_turns, 1):
            print(f"\nTurn {i}: {message[:100]}...")
            
            try:
                # Send message to CIA endpoint
                response = await client.post(
                    f"{base_url}/api/cia/conversation-unified",
                    json={
                        "user_id": user_id,
                        "message": message,
                        "project_id": project_id,
                        "session_id": session_id
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check if extraction happened
                    if "extracted_info" in result:
                        print(f"✅ Extracted info: {json.dumps(result['extracted_info'], indent=2)}")
                        collected_info.update(result['extracted_info'])
                    
                    # Check progressive updates
                    if "potential_bid_card" in result:
                        bid_card = result["potential_bid_card"]
                        print(f"📋 Bid card progress: {bid_card.get('completion_percentage', 0)}% complete")
                        if bid_card.get('fields'):
                            print(f"   Fields collected: {list(bid_card['fields'].keys())}")
                    
                    # Show AI response
                    if "response" in result:
                        print(f"🤖 AI: {result['response'][:200]}...")
                    
                else:
                    print(f"❌ Error: Status {response.status_code}")
                    print(f"   Response: {response.text[:500]}")
                
                # Small delay between turns
                await asyncio.sleep(1)
                
            except httpx.TimeoutException:
                print(f"⏱️ Request timed out (60s) - extraction might be too slow")
            except Exception as e:
                print(f"❌ Error: {e}")
    
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
    for field in expected_fields:
        if field in collected_info:
            print(f"✅ {field}: {collected_info[field]}")
        else:
            print(f"❌ {field}: Not extracted")
    
    # Calculate success rate
    extracted_count = sum(1 for field in expected_fields if field in collected_info)
    success_rate = (extracted_count / len(expected_fields)) * 100
    
    print(f"\n📊 Extraction Success Rate: {success_rate:.1f}% ({extracted_count}/{len(expected_fields)} fields)")
    
    if success_rate >= 70:
        print("✅ INTELLIGENT EXTRACTION WORKING!")
    else:
        print("⚠️ Extraction needs improvement")

if __name__ == "__main__":
    print("Starting CIA Intelligent GPT-5 Extraction Test...")
    print("Backend should be running on http://localhost:8008")
    asyncio.run(test_cia_intelligent_extraction())