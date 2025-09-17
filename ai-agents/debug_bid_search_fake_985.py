#!/usr/bin/env python3
"""
Debug the fake 985 bid cards issue
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from agents.coia.bid_card_search_node import search_bid_cards

async def debug_bid_search():
    """Debug where the fake 985 number comes from"""
    print("Debugging bid card search logic...")
    
    # Test 1: Simple search with status filter (should be ~109)
    simple_criteria = {
        "status": ["active", "collecting_bids", "generated"]
    }
    
    print("Testing search with status filter only...")
    try:
        results = await search_bid_cards(simple_criteria)
        print(f"Results count: {len(results)}")
        
        if len(results) > 200:
            print("ERROR: Returned way too many results - investigating...")
            
            # Check if we're getting duplicates
            ids = [card.get("id") for card in results if card.get("id")]
            unique_ids = set(ids)
            print(f"Unique IDs: {len(unique_ids)}")
            print(f"Total results: {len(results)}")
            print(f"Duplicates: {len(results) - len(unique_ids)}")
            
            # Show sample data
            print("Sample results:")
            for i, card in enumerate(results[:5]):
                card_id = card.get("id", "NO_ID")
                title = card.get("title", "NO_TITLE") 
                status = card.get("status", "NO_STATUS")
                project_type = card.get("project_type", "NO_TYPE")
                print(f"  {i+1}. ID:{card_id} | {title} | {status} | {project_type}")
        
        elif len(results) > 100:
            print("Results count seems reasonable")
            # Show some sample data
            for i, card in enumerate(results[:3]):
                title = card.get("title", "NO_TITLE")
                status = card.get("status", "NO_STATUS") 
                print(f"  {i+1}. {title} | {status}")
        
        else:
            print(f"Results count is low: {len(results)}")
            
    except Exception as e:
        print(f"Search failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_bid_search())