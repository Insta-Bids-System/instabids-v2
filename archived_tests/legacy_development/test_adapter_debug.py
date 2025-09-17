#!/usr/bin/env python3
"""
Test the HomeownerContextAdapter to see if it's loading contractor bids correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from adapters.homeowner_context import HomeownerContextAdapter

def test_adapter():
    print("Testing HomeownerContextAdapter...")
    
    adapter = HomeownerContextAdapter()
    print("Adapter initialized")
    
    # Test with known homeowner
    user_id = "11111111-1111-1111-1111-111111111111"
    print(f"\nTesting with user_id: {user_id}")
    
    # Get full context
    context = adapter.get_full_agent_context(user_id)
    print(f"\nContext loaded with {len(context)} categories:")
    for key in context.keys():
        print(f"  - {key}: {type(context[key])}")
    
    # Check bid cards
    bid_cards = context.get("bid_cards", [])
    print(f"\nFound {len(bid_cards)} bid cards:")
    for card in bid_cards:
        print(f"  - {card.get('bid_card_number')}: {card.get('project_type')} ({card.get('status')})")
    
    # Check contractor bids
    contractor_bids = context.get("contractor_bids", [])
    print(f"\nFound {len(contractor_bids)} contractor bids:")
    for bid in contractor_bids:
        amount = bid.get("bid_amount") or bid.get("amount")
        contractor = bid.get("contractor_name")
        project = bid.get("project_type")
        print(f"  - ${amount}: {contractor} for {project}")
    
    # Test specific bid card extraction
    if bid_cards:
        test_bid_card_id = bid_cards[0].get("id")
        print(f"\nTesting bid extraction for: {test_bid_card_id}")
        specific_bids = adapter.get_contractor_bids(test_bid_card_id)
        print(f"   Found {len(specific_bids)} bids for this card:")
        for bid in specific_bids:
            amount = bid.get("bid_amount") or bid.get("amount")
            contractor = bid.get("contractor_name")
            print(f"     - ${amount}: {contractor}")

if __name__ == "__main__":
    test_adapter()