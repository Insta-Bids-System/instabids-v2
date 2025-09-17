#!/usr/bin/env python3
"""
Direct test of confirmation flow
"""

import asyncio
import os
import sys

# Add the ai-agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-agents'))

from agents.coia.intelligent_research_agent import IntelligentResearchCoIA
from agents.coia.state import coia_state_manager

async def test_confirmation_flow():
    """Test the full confirmation flow directly"""
    
    print("=== DIRECT CONFIRMATION FLOW TEST ===")
    
    # Initialize with API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: No Anthropic API key found")
        return
    
    # Create agent
    agent = IntelligentResearchCoIA(api_key)
    print("Agent created successfully")
    
    session_id = "test_confirmation_flow"
    
    # Step 1: Business name
    print("\n1. Sending business name...")
    result1 = await agent.process_message(
        session_id=session_id,
        user_message="I own JM Holiday Lighting in South Florida"
    )
    
    print(f"Stage 1: {result1.get('stage')}")
    print(f"Response preview: {result1.get('response', '')[:200]}...")
    
    # Check session state
    state = coia_state_manager.get_session(session_id)
    print(f"\nSession state after step 1:")
    print(f"- Current stage: {state.current_stage}")
    print(f"- Research completed: {state.research_completed}")
    print(f"- Has research_data: {hasattr(state, 'research_data')}")
    if hasattr(state, 'research_data'):
        print(f"- Company: {state.research_data.company_name}")
    
    # Step 2: Confirmation
    print("\n2. Sending confirmation...")
    result2 = await agent.process_message(
        session_id=session_id,
        user_message="Yes, that information looks correct"
    )
    
    print(f"Stage 2: {result2.get('stage')}")
    print(f"Contractor ID: {result2.get('contractor_id')}")
    print(f"Response preview: {result2.get('response', '')[:200]}...")
    
    # Final state check
    state = coia_state_manager.get_session(session_id)
    print(f"\nFinal session state:")
    print(f"- Current stage: {state.current_stage}")
    print(f"- Contractor ID: {getattr(state, 'contractor_id', 'None')}")

if __name__ == "__main__":
    # Load env
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run test
    asyncio.run(test_confirmation_flow())