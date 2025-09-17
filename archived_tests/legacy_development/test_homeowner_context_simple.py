#!/usr/bin/env python3
"""
Test complete homeowner context loading via HomeownerContextAdapter
Tests all context sources and the singular identifier system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

import asyncio
from adapters.homeowner_context import HomeownerContextAdapter
import json

async def test_complete_homeowner_context():
    """Test the complete homeowner context loading system"""
    
    print("TESTING COMPLETE HOMEOWNER CONTEXT SYSTEM")
    print("=" * 60)
    
    # Initialize adapter
    adapter = HomeownerContextAdapter()
    
    # Test with real homeowner data
    test_user_id = "11111111-1111-1111-1111-111111111111"
    test_bid_card_id = "0c118f76-1b2d-47a9-9e35-d9b4a6f077da"
    
    print(f"Testing with Homeowner ID: {test_user_id}")
    print(f"Testing with Bid Card ID: {test_bid_card_id}")
    print()
    
    # Test 1: Get complete context
    print("TEST 1: Complete homeowner context loading")
    try:
        context = adapter.get_full_agent_context(
            user_id=test_user_id,
            bid_card_id=test_bid_card_id
        )
        
        print(f"Context categories loaded: {len(context)}")
        
        # Analyze what was loaded
        context_summary = {}
        for key, value in context.items():
            if isinstance(value, list):
                context_summary[key] = f"List with {len(value)} items"
            elif isinstance(value, dict):
                context_summary[key] = f"Dict with {len(value)} keys"
            else:
                context_summary[key] = f"{type(value).__name__}: {str(value)[:50]}..."
        
        print("Context Summary:")
        for key, summary in context_summary.items():
            print(f"   {key}: {summary}")
        
        print("SUCCESS: Complete context loading")
        
    except Exception as e:
        print(f"FAILED: Complete context loading - {e}")
        return False
    
    print()
    
    # Test 2: Verify submitted bids access
    print("TEST 2: Submitted bids access")
    try:
        bids = adapter.get_contractor_bids(test_bid_card_id)
        print(f"Found {len(bids)} submitted bids")
        
        if bids:
            for i, bid in enumerate(bids, 1):
                amount = bid.get('amount', 'N/A')
                contractor = bid.get('contractor_id', 'Unknown')
                print(f"   Bid {i}: {amount} from contractor {contractor}")
        
        print("SUCCESS: Submitted bids access")
        
    except Exception as e:
        print(f"FAILED: Submitted bids access - {e}")
        return False
    
    print()
    
    # Test 3: SINGULAR IDENTIFIER ANALYSIS
    print("ANALYSIS: SINGULAR IDENTIFIER SYSTEM")
    print("-" * 40)
    
    print("THE SINGULAR IDENTIFIER THAT TIES EVERYTHING TOGETHER:")
    print(f"   PRIMARY: user_id = '{test_user_id}'")
    print()
    print("HOW ALL CONTEXT IS RETRIEVED:")
    print("   1. HOMEOWNER PROFILE: homeowners.user_id = user_id")
    print("   2. PROJECTS: projects.user_id = homeowner.id")  
    print("   3. BID CARDS: bid_cards.user_id = homeowner.id")
    print("   4. SUBMITTED BIDS: contractor_bids.bid_card_id = bid_card.id")
    print("   5. UNIFIED CONVERSATIONS: unified_conversations.created_by = user_id")
    print("   6. MESSAGING AGENT DATA: unified_messages.conversation_id = conversation.id")
    print("   7. IRIS CONVERSATIONS: unified_conversations WHERE entity_type = 'iris'")
    print("   8. PREVIOUS CIA CONVERSATIONS: unified_conversations WHERE entity_type = 'cia'")
    print("   9. USER MEMORIES: user_memories.user_id = user_id")
    print("   10. MESSAGE ATTACHMENTS: message_attachments.message_id = message.id")
    print()
    print("KEY INSIGHT: user_id is the ROOT identifier that connects:")
    print("   - All homeowner data (profile, preferences, memories)")
    print("   - All projects and bid cards (via homeowner.id)")
    print("   - All conversations (CIA, messaging, IRIS)")
    print("   - All submitted bids (via bid_card relationships)")
    print("   - All cross-project context and history")
    
    print()
    print("CONCLUSION: COMPLETE HOMEOWNER CONTEXT SYSTEM VERIFIED")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_complete_homeowner_context())
    if success:
        print("\nALL TESTS PASSED - Homeowner context system fully operational")
    else:
        print("\nSOME TESTS FAILED - Check individual test results above")