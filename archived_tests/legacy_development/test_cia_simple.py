#!/usr/bin/env python3
"""
Simple CIA agent test - direct agent call
"""
import asyncio
import sys
import os

# Add ai-agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from agents.cia.agent import CustomerInterfaceAgent
from database import create_supabase_client

async def main():
    # Initialize CIA agent
    supabase = create_supabase_client()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("No OpenAI API key found")
        return
    
    print(f"Initializing CIA with API key: {api_key[:20]}...")
    cia = CustomerInterfaceAgent(api_key=api_key, supabase=supabase)
    
    # Test direct conversation
    print("Testing direct CIA conversation...")
    
    try:
        result = await asyncio.wait_for(
            cia.handle_conversation(
                user_id="test-user",
                message="I need bathroom renovation in Manhattan 10001, budget $30,000",
                session_id="test-session",
                project_id=None,
                existing_state=None
            ),
            timeout=30.0
        )
        
        print("SUCCESS!")
        print(f"Response: {result.get('response', 'No response')[:200]}...")
        print(f"Collected info: {result.get('state', {}).get('collected_info', {})}")
        
    except asyncio.TimeoutError:
        print("TIMEOUT: CIA agent took longer than 30 seconds")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())