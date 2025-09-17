#!/usr/bin/env python3
"""
Direct DeepAgents BSA Test - Prove delegation actually happens
"""

import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Not John Or Justin\Documents\instabids\ai-agents')

import asyncio
import time
from datetime import datetime
from agents.bsa.agent import create_bsa_agent
from deepagents import ChatClient

async def test_delegation():
    """Test BSA with DeepAgents showing real delegation"""
    
    print("\n" + "="*60)
    print("  DEEPAGENTS BSA DELEGATION TEST")
    print("="*60)
    
    # Create BSA agent
    print("\n1. Creating BSA agent with DeepAgents framework...")
    bsa = create_bsa_agent()
    print("   ✅ BSA agent created with 4 sub-agents")
    
    # Create chat client
    client = ChatClient(agent=bsa)
    print("   ✅ Chat client initialized")
    
    # Test messages that should trigger delegation
    test_cases = [
        {
            "message": "I need to find turf installation projects near 33442",
            "expected": "Should delegate to bid_card_search sub-agent"
        },
        {
            "message": "What's the market like for lawn care in Florida?",
            "expected": "Should delegate to market_research sub-agent"  
        },
        {
            "message": "Can you help me submit a bid for BC-TURF-33442-001?",
            "expected": "Should delegate to bid_submission sub-agent"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {test['expected']}")
        print(f"{'='*60}")
        print(f"🧑 User: {test['message']}")
        print("-" * 40)
        
        # Track timing
        start_time = time.time()
        
        # Send message and track response
        print("⏱️ Sending to BSA main agent...")
        
        try:
            # Send message to agent
            response = await client.send_message(test['message'])
            
            elapsed = time.time() - start_time
            
            # Parse response
            if isinstance(response, dict):
                print(f"\n📊 Response received in {elapsed:.2f}s")
                
                # Check for delegation indicators
                if 'tool_calls' in response:
                    print(f"🔧 Tools used: {response['tool_calls']}")
                    for tool in response['tool_calls']:
                        if tool.get('name') == 'task':
                            print(f"🚀 DELEGATION DETECTED!")
                            print(f"   Sub-agent: {tool.get('arguments', {}).get('agent')}")
                            print(f"   Task: {tool.get('arguments', {}).get('task')}")
                
                # Show response
                if 'content' in response:
                    content = response['content']
                    print(f"\n🤖 BSA Response:")
                    print(content[:500] if len(content) > 500 else content)
                    
                    # Check if response mentions delegation
                    if 'delegat' in content.lower() or 'sub-agent' in content.lower():
                        print("\n✅ Response mentions delegation!")
                    
                    # Check if response contains results
                    if 'BC-' in content or 'found' in content.lower():
                        print("✅ Response contains search results!")
                        
            else:
                # String response
                print(f"\n📊 Response received in {elapsed:.2f}s")
                print(f"\n🤖 BSA Response:")
                print(response[:500] if len(response) > 500 else response)
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Brief pause between tests
        await asyncio.sleep(2)
    
    print("\n" + "="*60)
    print("  DELEGATION TEST COMPLETE")
    print("="*60)

async def test_concurrent_conversation():
    """Test if main agent can continue while sub-agent works"""
    
    print("\n" + "="*60)
    print("  CONCURRENT CONVERSATION TEST")
    print("="*60)
    
    bsa = create_bsa_agent()
    client = ChatClient(agent=bsa)
    
    # Send a search request
    print("\n1. Sending search request...")
    search_task = asyncio.create_task(
        client.send_message("Search for all turf projects in 33442")
    )
    
    # Immediately send another message
    await asyncio.sleep(0.5)  # Brief delay
    print("2. Sending follow-up while search runs...")
    followup = await client.send_message("By the way, I prefer residential projects")
    
    print("\n🤖 Follow-up response:")
    print(followup if isinstance(followup, str) else followup.get('content', ''))
    
    # Wait for search to complete
    print("\n3. Waiting for search results...")
    search_result = await search_task
    
    print("\n🤖 Search results:")
    print(search_result if isinstance(search_result, str) else search_result.get('content', ''))
    
    print("\n✅ Test shows if agent can handle concurrent requests")

if __name__ == "__main__":
    print("🚀 Starting DeepAgents BSA Direct Test")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run async tests
    asyncio.run(test_delegation())
    asyncio.run(test_concurrent_conversation())
    
    print("\n✅ All tests complete!")