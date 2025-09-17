#!/usr/bin/env python3
"""
Simple test of BSA streaming without API dependencies
"""

import os
import sys
import asyncio

from dotenv import load_dotenv
load_dotenv()
# API key loaded from environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_streaming_with_fallback():
    """Test that fallback to basic search works when API is unavailable"""
    
    print("Testing BSA streaming with fallback logic...")
    print("-" * 50)
    
    # First, let's test the tool directly
    from agents.bsa.enhanced_tools import search_available_bid_cards
    
    print("\n1. Testing direct tool call:")
    result = search_available_bid_cards.invoke({
        "contractor_zip": "33442",
        "radius_miles": 30,
        "project_keywords": "turf"
    })
    
    if result.get("success"):
        print(f"   Tool found {len(result.get('bid_cards', []))} bid cards")
    else:
        print("   Tool failed")
    
    # Now test the streaming with fallback
    print("\n2. Testing streaming function (should fall back when API fails):")
    
    from agents.bsa.agent import process_contractor_input_streaming
    
    chunks = []
    bid_cards_found = False
    
    try:
        async for chunk in process_contractor_input_streaming(
            bid_card_id="test-123",
            contractor_id="test-456",
            input_type="text",
            input_data="Show me turf projects near 33442"
        ):
            chunk_type = chunk.get("type", "unknown")
            chunks.append(chunk_type)
            
            if chunk_type == "bid_cards_found":
                bid_cards_found = True
                cards = chunk.get("bid_cards", [])
                print(f"   BID_CARDS_FOUND event with {len(cards)} cards!")
                break
            elif chunk_type == "sub_agent_status":
                print(f"   Status: {chunk.get('message', '')}")
            
            # Stop after 20 chunks to avoid infinite loop
            if len(chunks) > 20:
                break
    
    except Exception as e:
        print(f"   Error: {e}")
    
    print(f"\n3. Results:")
    print(f"   Total chunks: {len(chunks)}")
    print(f"   Chunk types: {set(chunks)}")
    print(f"   bid_cards_found: {'YES' if bid_cards_found else 'NO'}")
    
    return bid_cards_found

if __name__ == "__main__":
    success = asyncio.run(test_streaming_with_fallback())
    print(f"\nFINAL RESULT: {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1)