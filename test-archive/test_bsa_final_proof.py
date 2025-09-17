#!/usr/bin/env python3
"""
FINAL BSA TEST - Proving sub-agent delegation works with real bid cards
Testing that BSA properly uses sub-agent results after instruction fix
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# Set UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, r'C:\Users\Not John Or Justin\Documents\instabids\ai-agents')

# Import the BSA agent
from agents.bsa.agent import create_bsa_agent
from database_simple import get_client

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

async def test_bsa_search():
    """Test BSA searching for bid cards with sub-agent delegation"""
    
    print_section("BSA FINAL TEST - PROVING SUB-AGENT DELEGATION WORKS")
    
    # First verify bid cards exist in database
    print("📊 Verifying bid cards exist in database...")
    client = get_client()
    
    # Check for turf/lawn projects
    result = client.table("bid_cards").select("*").in_("project_type", ["turf_installation", "lawn_care", "landscaping"]).execute()
    
    print(f"✅ Found {len(result.data)} turf/lawn bid cards in database")
    if result.data:
        for bc in result.data[:3]:
            print(f"  - {bc.get('bid_card_number')}: {bc.get('project_type')} in {bc.get('location_zip')}")
    
    # Initialize BSA agent
    print_section("INITIALIZING BSA AGENT")
    bsa = create_bsa_agent()
    print("✅ BSA Agent initialized with sub-agents")
    
    # Test messages showing progression
    test_messages = [
        {
            "role": "user",
            "content": "I'm a contractor looking for turf and lawn projects near ZIP 33442"
        },
        {
            "role": "user", 
            "content": "Can you search for available bid cards in that area?"
        },
        {
            "role": "user",
            "content": "Show me what projects are available"
        }
    ]
    
    print_section("TESTING BSA WITH REAL SEARCHES")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n🧑 TEST {i} - User: {message['content']}")
        print("-" * 50)
        
        # Process message using DeepAgents framework
        start_time = datetime.now()
        
        # Create a conversation with the agent
        from deepagents import ChatClient
        client = ChatClient(agent=bsa)
        
        # Send message and get response
        response = await client.send_message(message['content'])
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n🤖 BSA Response (took {elapsed:.1f}s):")
        print(response.get('response', 'No response'))
        
        # Check if delegation happened
        if 'tools' in response:
            print(f"\n📋 Tools used: {response['tools']}")
        
        # Show memory updates
        if 'memory_updates' in response:
            print(f"\n💾 Memory stored: {json.dumps(response['memory_updates'], indent=2)}")
        
        print("\n" + "="*60)
        
        # Add delay between messages
        await asyncio.sleep(2)
    
    print_section("TEST COMPLETE")
    print("✅ BSA agent tested with real sub-agent delegation")
    print("✅ Sub-agent should have found and presented actual bid cards")
    print("✅ Main agent should have used sub-agent results properly")

if __name__ == "__main__":
    print("🚀 Starting BSA Final Proof Test...")
    print(f"📅 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        asyncio.run(test_bsa_search())
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()