#!/usr/bin/env python3
"""
Test the improved intelligent research agent with real Google Maps API
"""

import asyncio
import os
import sys
import json

# Add the ai-agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-agents'))

from agents.coia.intelligent_research_agent import IntelligentResearchCoIA
from agents.coia.state import coia_state_manager

async def test_real_research():
    """Test real research with Google Maps API"""
    
    print("=== TESTING REAL INTELLIGENT RESEARCH WITH GOOGLE MAPS API ===")
    print("-" * 70)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check for Google Maps API key
    google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    print(f"Google Maps API Key: {'Found' if google_api_key else 'NOT FOUND'}")
    print(f"Anthropic API Key: {'Found' if anthropic_key else 'NOT FOUND'}")
    
    if not google_api_key:
        print("\nERROR: Google Maps API key not found in environment!")
        return
    
    if not anthropic_key:
        print("\nERROR: Anthropic API key not found!")
        return
    
    # Create agent
    print("\nInitializing Intelligent Research CoIA...")
    agent = IntelligentResearchCoIA(anthropic_key)
    
    # Test with JM Holiday Lighting
    session_id = "test_real_research"
    business_message = "I own JM Holiday Lighting in South Florida"
    
    print(f"\nTesting with: '{business_message}'")
    print("-" * 70)
    
    # Process the message
    result = await agent.process_message(
        session_id=session_id,
        user_message=business_message
    )
    
    print("\n=== RESEARCH RESULTS ===")
    print(f"Stage: {result.get('stage')}")
    
    if result.get('stage') == 'research_confirmation':
        print("\n[SUCCESS] Research completed!")
        
        # Extract collected data
        collected = result.get('profile_progress', {}).get('collectedData', {})
        
        print("\n--- DISCOVERED DATA ---")
        print(f"Company Name: {collected.get('company_name')}")
        print(f"Phone: {collected.get('phone')}")
        print(f"Email: {collected.get('email')}")
        print(f"Website: {collected.get('website')}")
        print(f"Services: {collected.get('services')}")
        
        print("\n--- FULL RESPONSE ---")
        print(result.get('response'))
        
        # Check if phone number is consistent
        state = coia_state_manager.get_session(session_id)
        if hasattr(state, 'research_data'):
            print("\n--- STORED RESEARCH DATA ---")
            research = state.research_data
            print(f"Phone (stored): {research.phone}")
            print(f"Address: {research.address}")
            print(f"Google Rating: {getattr(research, 'google_rating', 'N/A')}")
            
    else:
        print(f"\n[UNEXPECTED] Got stage: {result.get('stage')}")
        print(f"Response: {result.get('response')}")
    
    # Test again to verify consistency
    print("\n\n=== TESTING CONSISTENCY (2nd call) ===")
    print("-" * 70)
    
    # Clear session to test fresh (skip this line - sessions is not exposed)
    
    result2 = await agent.process_message(
        session_id=session_id + "_2",
        user_message=business_message
    )
    
    if result2.get('stage') == 'research_confirmation':
        collected2 = result2.get('profile_progress', {}).get('collectedData', {})
        print(f"Phone (2nd call): {collected2.get('phone')}")
        
        # Compare phone numbers
        if collected.get('phone') == collected2.get('phone'):
            print("\n[SUCCESS] Phone numbers are CONSISTENT!")
        else:
            print("\n[WARNING] Phone numbers differ:")
            print(f"  1st call: {collected.get('phone')}")
            print(f"  2nd call: {collected2.get('phone')}")

if __name__ == "__main__":
    asyncio.run(test_real_research())