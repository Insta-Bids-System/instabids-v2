#!/usr/bin/env python3
"""
Comprehensive test of HomeownerContextAdapter to understand data loading issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from adapters.homeowner_context import HomeownerContextAdapter
import json

def test_comprehensive_adapter():
    print("=" * 80)
    print("COMPREHENSIVE HOMEOWNER CONTEXT ADAPTER TEST")
    print("=" * 80)
    
    adapter = HomeownerContextAdapter()
    print("Adapter initialized successfully\n")
    
    # Test with known homeowner
    user_id = "11111111-1111-1111-1111-111111111111"
    print(f"Testing with user_id: {user_id}\n")
    
    # Get full context without bid_card_id or conversation_id
    print("=" * 40)
    print("TEST 1: Full context without specific IDs")
    print("=" * 40)
    context = adapter.get_full_agent_context(user_id)
    
    # Print all categories
    print(f"\nContext contains {len(context)} categories:")
    for key, value in context.items():
        if isinstance(value, list):
            print(f"  {key}: List with {len(value)} items")
        elif isinstance(value, dict):
            print(f"  {key}: Dict with {len(value)} keys")
        else:
            print(f"  {key}: {type(value).__name__}")
    
    # Examine bid cards in detail
    print("\n" + "=" * 40)
    print("BID CARDS ANALYSIS")
    print("=" * 40)
    bid_cards = context.get("bid_cards", [])
    print(f"Total bid cards: {len(bid_cards)}")
    for card in bid_cards:
        print(f"\nBid Card: {card.get('bid_card_number')}")
        print(f"  ID: {card.get('id')}")
        print(f"  Type: {card.get('project_type')}")
        print(f"  Status: {card.get('status')}")
        
        # Check if bid_document exists
        bid_doc = card.get('bid_document')
        if bid_doc:
            if isinstance(bid_doc, str):
                try:
                    bid_doc = json.loads(bid_doc)
                except:
                    pass
            if isinstance(bid_doc, dict):
                submitted_bids = bid_doc.get('submitted_bids', [])
                if isinstance(submitted_bids, str):
                    try:
                        submitted_bids = json.loads(submitted_bids)
                    except:
                        submitted_bids = []
                print(f"  Submitted bids in bid_document: {len(submitted_bids) if isinstance(submitted_bids, list) else 0}")
    
    # Examine contractor bids in detail
    print("\n" + "=" * 40)
    print("CONTRACTOR BIDS ANALYSIS")
    print("=" * 40)
    contractor_bids = context.get("contractor_bids", [])
    print(f"Total contractor bids loaded: {len(contractor_bids)}")
    
    # Group bids by project
    bids_by_project = {}
    for bid in contractor_bids:
        project = bid.get('project_type') or bid.get('bid_card_number', 'Unknown')
        if project not in bids_by_project:
            bids_by_project[project] = []
        bids_by_project[project].append(bid)
    
    for project, bids in bids_by_project.items():
        print(f"\n{project}: {len(bids)} bids")
        for bid in bids:
            amount = bid.get('amount') or bid.get('bid_amount', 'Unknown')
            contractor = bid.get('contractor_name', 'Unknown')
            print(f"  - ${amount} from {contractor}")
    
    # Test individual bid card extraction
    print("\n" + "=" * 40)
    print("INDIVIDUAL BID CARD EXTRACTION TEST")
    print("=" * 40)
    
    for card in bid_cards:
        bid_card_id = card.get('id')
        if bid_card_id:
            print(f"\nExtracting bids for: {card.get('bid_card_number')}")
            individual_bids = adapter.get_contractor_bids(bid_card_id)
            print(f"  Direct extraction found: {len(individual_bids)} bids")
            
            # Show the actual bids
            for idx, bid in enumerate(individual_bids, 1):
                amount = bid.get('amount') or bid.get('bid_amount', 'Unknown')
                contractor = bid.get('contractor_name', 'Unknown')
                print(f"    {idx}. ${amount} - {contractor}")
    
    # Test conversations loading
    print("\n" + "=" * 40)
    print("CONVERSATIONS ANALYSIS")
    print("=" * 40)
    conversations = context.get("conversations", [])
    print(f"Total conversations: {len(conversations)}")
    for conv in conversations[:3]:  # Show first 3
        print(f"  - ID: {conv.get('id')}")
        print(f"    Agent: {conv.get('agent_type')}")
        print(f"    Created: {conv.get('created_at')}")
    
    # Test messages loading (if bid_card_id provided)
    print("\n" + "=" * 40)
    print("MESSAGES ANALYSIS")
    print("=" * 40)
    messages = context.get("messages", [])
    print(f"Total messages in context: {len(messages)}")
    
    # Test with specific bid card
    if bid_cards:
        first_bid_card_id = bid_cards[0].get('id')
        print(f"\nTesting with specific bid_card_id: {first_bid_card_id}")
        
        context_with_bid = adapter.get_full_agent_context(
            user_id=user_id,
            specific_bid_card_id=first_bid_card_id
        )
        
        messages_with_bid = context_with_bid.get("messages", [])
        print(f"Messages for bid card: {len(messages_with_bid)}")
        
        rfi_requests = context_with_bid.get("rfi_requests", [])
        print(f"RFI requests for bid card: {len(rfi_requests)}")
    
    # Check IRIS conversation data (if exists)
    print("\n" + "=" * 40)
    print("IRIS CONVERSATION CHECK")
    print("=" * 40)
    
    # Check if any conversations are from IRIS
    iris_conversations = [c for c in conversations if c.get('agent_type') == 'iris']
    print(f"IRIS conversations found: {len(iris_conversations)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY OF ISSUES")
    print("=" * 80)
    
    total_expected_bids = 7  # 4 bathroom + 3 kitchen
    total_found_bids = len(contractor_bids)
    
    print(f"Expected contractor bids: {total_expected_bids}")
    print(f"Actually loaded: {total_found_bids}")
    print(f"Missing: {total_expected_bids - total_found_bids}")
    
    if total_found_bids < total_expected_bids:
        print("\nPOSSIBLE ISSUES:")
        print("1. Bid extraction logic may be failing for some bid cards")
        print("2. bid_document JSON parsing might be incomplete")
        print("3. Some bid cards might not have bid_document populated correctly")

if __name__ == "__main__":
    test_comprehensive_adapter()