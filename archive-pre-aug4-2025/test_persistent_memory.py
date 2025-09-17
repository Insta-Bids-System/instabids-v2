#!/usr/bin/env python3
"""
Test the persistent memory system for contractor conversations
"""

import asyncio
import os
import sys
import json

# Add the ai-agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-agents'))

from agents.coia.intelligent_research_agent import IntelligentResearchCoIA
from agents.coia.persistent_memory import persistent_coia_state_manager

async def test_persistent_memory():
    """Test persistent contractor memory system"""
    
    print("=== TESTING PERSISTENT CONTRACTOR MEMORY SYSTEM ===")
    print("-" * 70)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check for required API keys
    google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    print(f"Google Maps API Key: {'Found' if google_api_key else 'NOT FOUND'}")
    print(f"Anthropic API Key: {'Found' if anthropic_key else 'NOT FOUND'}")
    
    if not google_api_key or not anthropic_key:
        print("ERROR: Missing required API keys!")
        return
    
    # Create agent
    print("\nInitializing Intelligent Research CoIA with Persistent Memory...")
    agent = IntelligentResearchCoIA(anthropic_key)
    
    # Test 1: Create new contractor conversation
    print("\n" + "="*70)
    print("TEST 1: NEW CONTRACTOR CONVERSATION")
    print("="*70)
    
    session_id_1 = "test_persistent_memory_1"
    business_message = "I own JM Holiday Lighting in South Florida"
    
    print(f"Testing with: '{business_message}'")
    
    # Process the message (should create new conversation)
    result1 = await agent.process_message(
        session_id=session_id_1,
        user_message=business_message
    )
    
    print(f"\nStage: {result1.get('stage')}")
    print(f"Response (first 200 chars): {result1.get('response', '')[:200]}...")
    
    if result1.get('stage') == 'research_confirmation':
        print("[SUCCESS] Research completed and saved to persistent memory")
        
        # Confirm the research
        confirm_result = await agent.process_message(
            session_id=session_id_1,
            user_message="Yes, that's all correct"
        )
        
        print(f"Confirmation stage: {confirm_result.get('stage')}")
        if confirm_result.get('contractor_id'):
            print(f"Contractor ID created: {confirm_result.get('contractor_id')}")
    
    # Test 2: Simulate returning contractor (same business name, new session)
    print("\n" + "="*70)
    print("TEST 2: RETURNING CONTRACTOR (SAME BUSINESS)")
    print("="*70)
    
    session_id_2 = "test_persistent_memory_2"
    
    print(f"Testing returning contractor with same business: '{business_message}'")
    
    # Process the same business message in a new session
    result2 = await agent.process_message(
        session_id=session_id_2,
        user_message=business_message
    )
    
    print(f"\nStage: {result2.get('stage')}")
    print(f"Response (first 300 chars): {result2.get('response', '')[:300]}...")
    
    # Check if it detected returning contractor
    if 'returning' in result2.get('stage', ''):
        print("[SUCCESS] Detected returning contractor!")
        contractor_id = result2.get('contractor_id')
        if contractor_id:
            print(f"Contractor ID matched: {contractor_id}")
            
            # Get conversation history
            history = await persistent_coia_state_manager.get_contractor_history(contractor_id)
            print(f"Found {len(history)} previous conversations")
            for i, conv in enumerate(history):
                print(f"  {i+1}. {conv['session_id']} - {conv['current_stage']} ({conv['message_count']} messages)")
    else:
        print("[UNEXPECTED] Did not detect returning contractor")
    
    # Test 3: Load conversation state from database
    print("\n" + "="*70)
    print("TEST 3: CONVERSATION STATE PERSISTENCE")
    print("="*70)
    
    # Load the first conversation from database
    loaded_state = await persistent_coia_state_manager.memory.load_conversation_state(session_id_1)
    
    if loaded_state:
        print("[SUCCESS] Loaded conversation state from database")
        print(f"Session ID: {loaded_state.session_id}")
        print(f"Current stage: {loaded_state.current_stage}")
        print(f"Message count: {len(loaded_state.messages)}")
        print(f"Research completed: {loaded_state.research_completed}")
        if hasattr(loaded_state, 'research_data') and loaded_state.research_data:
            print(f"Company name: {loaded_state.research_data.company_name}")
            print(f"Phone: {loaded_state.research_data.phone}")
            print(f"Google listing URL: {loaded_state.research_data.google_listing_url}")
    else:
        print("[ERROR] Failed to load conversation state")
    
    # Test 4: Check returning contractor detection
    print("\n" + "="*70)
    print("TEST 4: RETURNING CONTRACTOR DETECTION")
    print("="*70)
    
    returning_id = await persistent_coia_state_manager.check_returning_contractor(
        "JM Holiday Lighting", 
        phone="(561) 573-7090", 
        email="info@jmholidaylighting.com"
    )
    
    if returning_id:
        print(f"[SUCCESS] Detected returning contractor by business data: {returning_id}")
    else:
        print("[INFO] No returning contractor detected (might be expected for first run)")
    
    print("\n" + "="*70)
    print("PERSISTENT MEMORY SYSTEM TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_persistent_memory())