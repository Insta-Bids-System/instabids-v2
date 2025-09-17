#!/usr/bin/env python3
"""
Direct test of CoIA business extraction
"""

import sys
import os
import asyncio

# Add the ai-agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from agents.coia.simple_research_agent import SimpleResearchCoIA

async def test_direct_coia():
    """Test CoIA directly without API"""
    
    # Initialize CoIA
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if not anthropic_key:
        print("ERROR: ANTHROPIC_API_KEY not found")
        return
        
    coia = SimpleResearchCoIA(anthropic_key)
    
    print("Testing CoIA Direct Business Extraction")
    print("=" * 50)
    
    # Test message
    test_message = "I own JM Holiday Lighting in South Florida"
    print(f"Test message: '{test_message}'")
    
    # Test the extraction method directly
    business_info = coia._extract_business_info(test_message)
    print(f"Direct extraction result: {business_info}")
    
    # Test the full process_message method
    print("\nTesting full process_message...")
    import time
    unique_session_id = f"test_direct_{int(time.time())}"
    print(f"Using session ID: {unique_session_id}")
    
    result = await coia.process_message(
        session_id=unique_session_id,
        user_message=test_message
    )
    
    print(f"Full process result:")
    print(f"  Stage: {result.get('stage')}")
    print(f"  Response length: {len(result.get('response', ''))}")
    print(f"  Response preview: {result.get('response', '')[:200]}...")

if __name__ == "__main__":
    asyncio.run(test_direct_coia())