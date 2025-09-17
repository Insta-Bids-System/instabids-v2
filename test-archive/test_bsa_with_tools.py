#!/usr/bin/env python3
"""
Test BSA with proper DeepAgents tool delegation
This should prove sub-agents can now actually search
"""

import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Not John Or Justin\Documents\instabids\ai-agents')

import asyncio
from agents.bsa.agent import create_bsa_agent
from langchain_core.messages import HumanMessage

async def test_bsa_with_tools():
    """Test BSA with real tools delegated to sub-agents"""
    
    print("\n" + "="*70)
    print("  BSA DEEPAGENTS WITH TOOLS TEST")
    print("="*70)
    
    # Create BSA agent with tools
    print("\n1. Creating BSA agent with tools...")
    bsa = create_bsa_agent()
    print("   ✅ BSA agent created with DeepAgents framework")
    
    # Test messages
    test_queries = [
        "Find turf and lawn projects near ZIP 33442",
        "Search for landscaping opportunities in Florida",
        "What bid cards are available for lawn care contractors?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {query}")
        print("="*70)
        
        # Create state for the agent
        state = {
            "messages": [HumanMessage(content=query)],
            "contractor_id": f"test-contractor-{i}",
            "location": {"zip": "33442"}
        }
        
        # Configuration for the agent
        config = {"configurable": {"thread_id": f"test_tools_{i}"}}
        
        try:
            print("\n⏱️ Invoking BSA agent...")
            result = await bsa.ainvoke(state, config)
            
            # Check the messages in the result
            messages = result.get("messages", [])
            print(f"\n📊 Got {len(messages)} messages in response")
            
            # Look for tool calls and responses
            tool_calls_found = False
            bid_cards_found = False
            
            for msg in messages:
                # Check for tool calls
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_calls_found = True
                    for tool_call in msg.tool_calls:
                        print(f"\n🔧 Tool Call Detected:")
                        print(f"   Name: {tool_call.get('name')}")
                        if tool_call.get('name') == 'task':
                            args = tool_call.get('args', {})
                            print(f"   Sub-agent: {args.get('subagent_type')}")
                            print(f"   Task: {args.get('description')[:100]}...")
                
                # Check content for bid cards
                if hasattr(msg, "content"):
                    content = str(msg.content)
                    if "BC-" in content or "bid card" in content.lower():
                        bid_cards_found = True
                        # Show a snippet
                        print(f"\n🤖 Response snippet:")
                        lines = content.split('\n')
                        for line in lines[:10]:
                            if line.strip():
                                print(f"   {line[:80]}")
            
            # Analysis
            print(f"\n📈 Analysis:")
            print(f"   Tool calls detected: {'YES ✅' if tool_calls_found else 'NO ❌'}")
            print(f"   Bid cards mentioned: {'YES ✅' if bid_cards_found else 'NO ❌'}")
            
            if tool_calls_found and not bid_cards_found:
                print("   ⚠️ Delegation happened but no results returned")
            elif tool_calls_found and bid_cards_found:
                print("   ✅ SUCCESSFUL DELEGATION WITH RESULTS!")
            elif not tool_calls_found:
                print("   ❌ No delegation detected - agent not using sub-agents")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

async def main():
    await test_bsa_with_tools()
    
    print("\n" + "="*70)
    print("  TEST COMPLETE")
    print("="*70)
    print("\nSUMMARY:")
    print("The BSA agent should now be delegating to sub-agents with real tools.")
    print("Sub-agents should have access to search_available_bid_cards and other tools.")
    print("If delegation works, we should see actual bid cards returned.")

if __name__ == "__main__":
    asyncio.run(main())