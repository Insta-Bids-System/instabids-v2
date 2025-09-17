#!/usr/bin/env python3
"""
Direct test of intelligent research agent
"""

import asyncio
import os
import sys

# Add the ai-agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-agents'))

from agents.coia.intelligent_research_agent import IntelligentResearchCoIA

async def test_direct():
    """Test the intelligent research agent directly"""
    
    print("=== DIRECT INTELLIGENT COIA TEST ===")
    
    # Initialize with API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: No Anthropic API key found")
        return
    
    print(f"API Key found: {api_key[:20]}...")
    
    # Create agent
    try:
        agent = IntelligentResearchCoIA(api_key)
        print("Agent created successfully")
    except Exception as e:
        print(f"ERROR creating agent: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test message processing
    try:
        result = await agent.process_message(
            session_id="test_direct",
            user_message="I own JM Holiday Lighting in South Florida"
        )
        
        print(f"\nResult:")
        print(f"Stage: {result.get('stage')}")
        print(f"Response: {result.get('response', '')[:200]}...")
        
    except Exception as e:
        print(f"ERROR processing message: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Load env
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run test
    asyncio.run(test_direct())