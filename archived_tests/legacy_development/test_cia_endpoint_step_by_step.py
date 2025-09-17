#!/usr/bin/env python3
"""Test CIA endpoint step by step to find the exact failure point"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load from root .env
root_env = Path(__file__).parent / '.env'
if root_env.exists():
    load_dotenv(root_env, override=True)

# Add ai-agents to path
sys.path.append('ai-agents')

async def test_cia_endpoint_flow():
    """Mimic the exact flow that happens in the CIA chat endpoint"""
    try:
        # Step 1: Import and initialize exactly like main.py
        print("Step 1: Importing CIA agent and routes...")
        from agents.cia.agent import CustomerInterfaceAgent
        from routers.cia_routes import set_cia_agent
        from database_simple import db
        
        # Step 2: Get API key like main.py
        print("Step 2: Getting API keys...")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("[FAILED] No OpenAI API key")
            return
        
        # Step 3: Initialize CIA agent like main.py
        print("Step 3: Initializing CIA agent...")
        cia_agent = CustomerInterfaceAgent(f"openai:{openai_api_key}")
        set_cia_agent(cia_agent)
        print("[SUCCESS] CIA agent initialized and set")
        
        # Step 4: Prepare chat data like the endpoint
        print("Step 4: Preparing chat data...")
        user_id = "test_user_456"
        session_id = f"anon_{datetime.now().timestamp()}"
        message = "I need help planning a kitchen remodel"
        
        # Step 5: Load existing conversation like the endpoint does
        print("Step 5: Loading existing conversation...")
        existing_conversation = await db.load_conversation_state(session_id)
        existing_state = existing_conversation.get("state", {}) if existing_conversation else None
        print(f"[SUCCESS] Loaded conversation: {type(existing_state)}")
        
        # Step 6: Call CIA agent like the endpoint does
        print("Step 6: Calling CIA agent...")
        result = await cia_agent.handle_conversation(
            user_id=user_id,
            message=message,
            images=[],
            session_id=session_id,
            existing_state=existing_state,
            project_id=None
        )
        print(f"[SUCCESS] CIA agent call completed: {type(result)}")
        
        # Step 7: Save conversation state like the endpoint does
        print("Step 7: Saving conversation state...")
        if "state" in result:
            await db.save_conversation_state(
                user_id=user_id,
                thread_id=session_id,
                agent_type="CIA",
                state=result["state"]
            )
            print("[SUCCESS] Conversation state saved")
        
        print(f"\nFinal result: {result.get('response', 'No response')[:100]}...")
        
    except Exception as e:
        print(f"[FAILED] Error at step: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== CIA Endpoint Step-by-Step Testing ===")
    asyncio.run(test_cia_endpoint_flow())