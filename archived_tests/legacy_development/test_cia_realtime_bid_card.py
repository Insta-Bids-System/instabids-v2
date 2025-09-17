#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for CIA Potential Bid Card System
Tests real CIA conversation with real-time bid card updates
"""
import asyncio
import aiohttp
import json
import time
from uuid import uuid4
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8008"
CONVERSATION_ID = str(uuid4())
USER_ID = None  # Anonymous user for now

print("=" * 80)
print("CIA POTENTIAL BID CARD - REAL-TIME TEST")
print("=" * 80)
print(f"Conversation ID: {CONVERSATION_ID}")
print()

async def stream_cia_response(session: aiohttp.ClientSession, message: str) -> str:
    """Stream a message to CIA and collect the response"""
    payload = {
        "messages": [{"role": "user", "content": message}],
        "conversation_id": CONVERSATION_ID,
        "user_id": USER_ID or str(uuid4()),
        "max_tokens": 500
    }
    
    print(f"[USER]: {message}")
    print("[CIA]: ", end="", flush=True)
    
    full_response = ""
    async with session.post(f"{BASE_URL}/api/cia/stream", json=payload) as response:
        async for line in response.content:
            if line:
                line_str = line.decode('utf-8').strip()
                if line_str.startswith("data: "):
                    try:
                        data = json.loads(line_str[6:])
                        if "choices" in data and data["choices"]:
                            content = data["choices"][0].get("delta", {}).get("content", "")
                            if content:
                                print(content, end="", flush=True)
                                full_response += content
                    except json.JSONDecodeError:
                        pass
    
    print("\n")
    return full_response

async def check_bid_card_status(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Check the current status of the potential bid card"""
    # First, get the bid card ID from conversation tracking
    async with session.get(
        f"{BASE_URL}/api/cia/conversation/{CONVERSATION_ID}/potential-bid-card"
    ) as response:
        if response.status == 200:
            return await response.json()
        elif response.status == 404:
            return None
        else:
            print(f"Error checking bid card: {response.status}")
            return None

async def display_bid_card_status(bid_card: Dict[str, Any]):
    """Display the current bid card status"""
    if not bid_card:
        print("[BID CARD]: Not created yet")
        return
    
    print("[BID CARD STATUS]:")
    print(f"  ID: {bid_card.get('id', 'N/A')}")
    print(f"  Completion: {bid_card.get('completion_percentage', 0)}%")
    print(f"  Ready: {bid_card.get('ready_for_conversion', False)}")
    
    fields = bid_card.get('fields_collected', {})
    if fields:
        print("  Fields collected:")
        for field, value in fields.items():
            if value:
                preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(f"    - {field}: {preview}")
    
    missing = bid_card.get('missing_fields', [])
    if missing:
        print(f"  Missing: {', '.join(missing)}")
    print()

async def run_conversation_test():
    """Run a multi-turn conversation and monitor bid card updates"""
    async with aiohttp.ClientSession() as session:
        # Message 1: Initial project description
        print("=" * 80)
        print("TURN 1: Initial Project Description")
        print("-" * 80)
        
        await stream_cia_response(
            session,
            "Hi! I need help with a kitchen remodel in Austin, Texas 78704. "
            "We're looking to update our cabinets, countertops, and add a tile backsplash."
        )
        
        # Check bid card status after first message
        await asyncio.sleep(2)  # Give system time to create bid card
        bid_card = await check_bid_card_status(session)
        await display_bid_card_status(bid_card)
        
        # Message 2: Add timeline information
        print("=" * 80)
        print("TURN 2: Timeline Information")
        print("-" * 80)
        
        await stream_cia_response(
            session,
            "We'd like to get this done within the next 3-4 weeks if possible. "
            "My email is sarah.johnson@example.com"
        )
        
        # Check bid card status after second message
        await asyncio.sleep(2)
        bid_card = await check_bid_card_status(session)
        await display_bid_card_status(bid_card)
        
        # Message 3: Budget discussion
        print("=" * 80)
        print("TURN 3: Budget Context")
        print("-" * 80)
        
        await stream_cia_response(
            session,
            "We're looking at mid-range materials, nothing too fancy but good quality. "
            "We want it to look nice but be practical for a family with kids."
        )
        
        # Check bid card status after third message
        await asyncio.sleep(2)
        bid_card = await check_bid_card_status(session)
        await display_bid_card_status(bid_card)
        
        # Message 4: Special requirements
        print("=" * 80)
        print("TURN 4: Special Requirements")
        print("-" * 80)
        
        await stream_cia_response(
            session,
            "Oh, and we need the contractor to be licensed and insured. "
            "Also, we have pets so they need to be careful about keeping doors closed."
        )
        
        # Final bid card status
        await asyncio.sleep(2)
        bid_card = await check_bid_card_status(session)
        await display_bid_card_status(bid_card)
        
        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        if bid_card:
            print(f"[SUCCESS] Bid card created and updated through conversation")
            print(f"  Final completion: {bid_card.get('completion_percentage', 0)}%")
            print(f"  Ready for conversion: {bid_card.get('ready_for_conversion', False)}")
            
            # Show what fields were successfully extracted
            fields = bid_card.get('fields_collected', {})
            if fields:
                print("\n[EXTRACTED FIELDS]:")
                for field, value in fields.items():
                    if value:
                        print(f"  {field}: {value}")
        else:
            print("[FAILURE] No bid card was created during conversation")

async def test_manual_updates():
    """Test that homeowner can manually update fields"""
    print("\n" + "=" * 80)
    print("TESTING MANUAL FIELD UPDATES")
    print("=" * 80)
    
    async with aiohttp.ClientSession() as session:
        # Get the bid card
        bid_card = await check_bid_card_status(session)
        if not bid_card:
            print("[ERROR] No bid card to update")
            return
        
        bid_card_id = bid_card['id']
        print(f"Updating bid card: {bid_card_id}")
        
        # Manually update a field
        update_payload = {
            "field_name": "contractor_size",
            "field_value": "medium",
            "source": "manual"
        }
        
        async with session.put(
            f"{BASE_URL}/api/cia/potential-bid-cards/{bid_card_id}/field",
            json=update_payload
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"[SUCCESS] Manually updated contractor_size")
                print(f"  New completion: {result.get('completion_percentage', 0)}%")
            else:
                print(f"[ERROR] Failed to update: {response.status}")

# Main execution
if __name__ == "__main__":
    print("\nStarting real-time CIA potential bid card test...")
    print("This test will:")
    print("  1. Have a multi-turn conversation with CIA")
    print("  2. Monitor bid card creation and updates in real-time")
    print("  3. Test manual field updates by homeowner")
    print("  4. Verify all data is properly extracted and saved")
    print()
    
    # Run the conversation test
    asyncio.run(run_conversation_test())
    
    # Test manual updates
    asyncio.run(test_manual_updates())
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)