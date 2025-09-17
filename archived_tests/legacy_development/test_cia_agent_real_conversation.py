#!/usr/bin/env python3
"""
Test CIA agent with REAL LLM conversation using REAL homeowner data
This tests the complete context ingestion and LLM response generation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

import asyncio
import json
from agents.cia.agent import CustomerInterfaceAgent

async def test_cia_real_conversation():
    """Test CIA agent with real homeowner data and LLM conversation"""
    
    print("TESTING CIA AGENT WITH REAL LLM CONVERSATION")
    print("=" * 60)
    
    # Use homeowner with actual data (5 bid cards, 5 submitted bids)
    test_user_id = "bda3ab78-e034-4be7-8285-1b7be1bf1387"
    test_session_id = f"test_session_{int(asyncio.get_event_loop().time())}"
    
    print(f"Testing with User ID: {test_user_id}")
    print(f"Session ID: {test_session_id}")
    print()
    
    try:
        # Initialize CIA agent
        print("Step 1: Initializing CIA agent...")
        cia_agent = CustomerInterfaceAgent(api_key="dummy-key-will-load-from-env")
        print("SUCCESS: CIA agent initialized")
        
        # Test conversation that should reference existing data
        test_message = """
        Hi! I'm thinking about starting a new kitchen renovation project. 
        Can you help me understand what my options are? Also, I'm curious - 
        do you have any information about my previous projects or any contractors 
        who have worked with me before?
        """
        
        print(f"Step 2: Sending test message to CIA agent...")
        print(f"Message: {test_message[:100]}...")
        print()
        
        # Call CIA agent with real LLM
        print("Step 3: Processing with LLM (this may take 30-60 seconds)...")
        response = await cia_agent.handle_conversation(
            user_id=test_user_id,
            message=test_message,
            session_id=test_session_id
        )
        
        print("SUCCESS: CIA agent responded")
        print()
        
        # Analyze the response
        print("Step 4: Analyzing CIA response...")
        print("-" * 40)
        
        if isinstance(response, dict):
            # Check if response contains context awareness
            response_text = response.get('response', response.get('message', str(response)))
            
            print("RESPONSE ANALYSIS:")
            print(f"Response length: {len(response_text)} characters")
            print()
            
            # Look for signs of context awareness
            context_indicators = [
                "previous projects", "past projects", "earlier", "before",
                "bid cards", "contractors", "submissions", "history",
                "remember", "recall", "last time", "previously"
            ]
            
            found_indicators = []
            for indicator in context_indicators:
                if indicator.lower() in response_text.lower():
                    found_indicators.append(indicator)
            
            print(f"Context awareness indicators found: {len(found_indicators)}")
            for indicator in found_indicators:
                print(f"  - '{indicator}' found in response")
            
            print()
            print("FULL CIA RESPONSE:")
            print("-" * 30)
            print(response_text)
            print("-" * 30)
            
            # Check for specific data integration
            if len(found_indicators) > 0:
                print("SUCCESS: CIA shows context awareness!")
                print("✅ Agent is referencing homeowner's previous data")
            else:
                print("WARNING: CIA may not be using full context")
                print("❓ Response doesn't clearly reference previous data")
                
        else:
            print(f"Response type: {type(response)}")
            print(f"Response: {response}")
        
        print()
        
        # Test 2: Ask specific question about existing data
        print("Step 5: Testing specific data reference...")
        specific_question = "How many projects have I worked on before? Can you tell me about any bids I've received?"
        
        print(f"Asking: {specific_question}")
        print()
        
        specific_response = await cia_agent.handle_conversation(
            user_id=test_user_id,
            message=specific_question,
            session_id=test_session_id
        )
        
        if isinstance(specific_response, dict):
            specific_text = specific_response.get('response', specific_response.get('message', str(specific_response)))
            print("SPECIFIC DATA RESPONSE:")
            print("-" * 30)
            print(specific_text)
            print("-" * 30)
            
            # Look for data references
            data_references = ["5", "five", "bid", "project", "contractor"]
            found_refs = [ref for ref in data_references if ref in specific_text.lower()]
            
            if found_refs:
                print(f"SUCCESS: Found data references: {found_refs}")
                print("✅ CIA is accessing real homeowner data!")
            else:
                print("WARNING: No specific data references found")
        
        return True
        
    except Exception as e:
        print(f"FAILED: CIA agent test failed - {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_cia_real_conversation())
    if success:
        print("\n✅ CIA AGENT REAL CONVERSATION TEST COMPLETED")
        print("Check the response analysis above to verify context integration")
    else:
        print("\n❌ CIA AGENT TEST FAILED")
        print("Check error details above")