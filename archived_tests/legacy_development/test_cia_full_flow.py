#!/usr/bin/env python3
"""Test the complete CIA flow exactly as main.py does"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load from root .env
root_env = Path(__file__).parent / '.env'
if root_env.exists():
    load_dotenv(root_env, override=True)

# Add ai-agents to path like main.py does
sys.path.append('ai-agents')

try:
    # Import exactly like main.py
    from agents.cia.agent import CustomerInterfaceAgent
    from routers.cia_routes import set_cia_agent
    
    # Get API keys exactly like main.py
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    print(f"OpenAI key found: {bool(openai_api_key)}")
    print(f"Anthropic key found: {bool(anthropic_api_key)}")
    
    if openai_api_key:
        # Initialize exactly like main.py
        print("Initializing CIA agent with OpenAI (like main.py)...")
        cia_agent = CustomerInterfaceAgent(f"openai:{openai_api_key}")
        set_cia_agent(cia_agent)
        print("[SUCCESS] CIA agent initialized successfully with OpenAI GPT-4o API key")
        
        # Test a conversation like the endpoint does
        print("\nTesting conversation...")
        result = cia_agent.handle_conversation(
            user_id="test_user_456",
            message="I need help planning a kitchen remodel",
            images=[],
            session_id="test_session_123",
            existing_state=None,
            project_id=None
        )
        
        # This is async, so we need to handle it
        import asyncio
        if asyncio.iscoroutine(result):
            result = asyncio.run(result)
        
        print(f"[SUCCESS] CIA conversation result type: {type(result)}")
        print(f"Response: {result.get('response', 'No response')[:100]}...")
        
    else:
        print("[FAILED] No OpenAI API key found")
        
except Exception as e:
    print(f"[FAILED] Error: {e}")
    import traceback
    traceback.print_exc()