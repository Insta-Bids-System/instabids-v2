#!/usr/bin/env python3
"""
Deep dive into how CIA agent context system works
Shows exactly how homeowner data flows into conversations
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from adapters.homeowner_context import HomeownerContextAdapter

def analyze_context_flow():
    print("=" * 80)
    print("CIA AGENT CONTEXT FLOW ANALYSIS")
    print("=" * 80)
    
    # Initialize adapter
    adapter = HomeownerContextAdapter()
    user_id = "11111111-1111-1111-1111-111111111111"
    
    # Get full context
    context = adapter.get_full_agent_context(user_id)
    
    print("\n1. WHAT DATA IS LOADED:")
    print("=" * 40)
    print(f"Categories loaded: {list(context.keys())}")
    print(f"\nData counts:")
    print(f"  - Bid cards: {len(context.get('bid_cards', []))}")
    print(f"  - Contractor bids: {len(context.get('contractor_bids', []))}")
    print(f"  - Conversations: {len(context.get('conversations', []))}")
    print(f"  - User memories: {len(context.get('user_memories', []))}")
    
    print("\n2. HOW IT'S STRUCTURED IN MEMORY:")
    print("=" * 40)
    print("The adapter returns a dictionary with these keys:")
    for key in context.keys():
        value = context[key]
        if isinstance(value, list):
            print(f"  {key}: List of {len(value)} items")
            if value and len(value) > 0:
                print(f"    First item keys: {list(value[0].keys()) if isinstance(value[0], dict) else 'not a dict'}")
        elif isinstance(value, dict):
            print(f"  {key}: Dictionary with {len(value)} keys")
        else:
            print(f"  {key}: {type(value).__name__}")
    
    print("\n3. HOW IT GETS INTO THE CONVERSATION:")
    print("=" * 40)
    print("In CIA agent.py line 834-874:")
    print("  1. Gets homeowner_context from state")
    print("  2. Builds context_info string with:")
    print("     - Homeowner profile")
    print("     - Bid cards (up to 3 shown)")
    print("     - Contractor bids (up to 5 shown)")
    print("     - User memories")
    print("     - Conversation history count")
    print("  3. APPENDS this to system_prompt")
    print("  4. System prompt + context goes to LLM")
    
    print("\n4. ACTUAL CONTEXT STRING THAT GETS ADDED:")
    print("=" * 40)
    
    # Simulate what CIA does at lines 834-874
    if context and len(context) > 3:
        context_info = "\n\n[HOMEOWNER CONTEXT (From Database):"
        
        if context.get("homeowner"):
            profile = context["homeowner"]
            context_info += f"\nHomeowner Profile Found: {profile.get('id', 'Unknown')}"
        
        if context.get("bid_cards"):
            bid_cards = context["bid_cards"]
            context_info += f"\n[BID CARDS]: {len(bid_cards)} previous project(s)"
            for card in bid_cards[:3]:
                context_info += f"\n  - {card.get('project_type', 'Unknown')}: {card.get('title', 'Untitled')}"
        
        if context.get("contractor_bids"):
            bids = context["contractor_bids"]
            context_info += f"\n[CONTRACTOR BIDS]: {len(bids)} bid(s) received from contractors"
            for bid in bids[:5]:
                amount = bid.get('amount') or bid.get('bid_amount', 'Unknown')
                contractor = bid.get('contractor_name', 'Unknown Contractor')
                context_info += f"\n  - ${amount} from {contractor}"
            context_info += f"\n\nIMPORTANT: When asked about bid amounts, provide these specific amounts to the homeowner."
        
        print(context_info)
    
    print("\n5. WHEN DOES THIS HAPPEN:")
    print("=" * 40)
    print("EVERY conversation turn:")
    print("  1. User sends message")
    print("  2. CIA loads FULL context via adapter.get_full_agent_context()")
    print("  3. Context appended to system prompt")
    print("  4. LLM sees: System Prompt + Context + Conversation History + User Message")
    print("  5. LLM generates response with awareness of all data")
    
    print("\n6. WHAT THE LLM ACTUALLY SEES:")
    print("=" * 40)
    print("Example prompt structure:")
    print("  [SYSTEM PROMPT - new_prompts.py]")
    print("  [HOMEOWNER CONTEXT - dynamically added]")
    print("  [CONVERSATION HISTORY - previous messages]")
    print("  [USER MESSAGE - current question]")
    
    print("\n7. DATA PERSISTENCE:")
    print("=" * 40)
    print("- Bid cards: Stored in bid_cards table")
    print("- Contractor bids: Stored as JSONB in bid_cards.bid_document.submitted_bids")
    print("- Conversations: Stored in unified_conversations table")
    print("- User memories: Stored in user_memories table")
    print("- All data persists across sessions")
    
    print("\n8. AUTOMATIC CONTEXT INJECTION:")
    print("=" * 40)
    print("YES - Every message automatically gets:")
    print("  - ALL bid cards for the user")
    print("  - ALL contractor bids (up to 5 shown in prompt)")
    print("  - ALL conversation history count")
    print("  - ALL user memories")
    print("The CIA doesn't need to 'look up' data - it's pre-loaded!")
    
    print("\n9. HOW TO TEST IF IT'S WORKING:")
    print("=" * 40)
    print("Ask the CIA:")
    print('  "What contractor bids do I have?"')
    print('  "Tell me about my bathroom project bids"')
    print('  "Which contractor offered $18,500?"')
    print("\nIf it can answer these, the context is working!")
    
    print("\n10. CURRENT ISSUES:")
    print("=" * 40)
    print("- CIA uses Anthropic API instead of OpenAI (authentication error)")
    print("- Context IS loaded but LLM call fails")
    print("- Once API is fixed, context will be fully available")

if __name__ == "__main__":
    analyze_context_flow()