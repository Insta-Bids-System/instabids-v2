#!/usr/bin/env python3
"""Test specific database operations that CIA uses"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load from root .env
root_env = Path(__file__).parent / '.env'
if root_env.exists():
    load_dotenv(root_env, override=True)

# Add ai-agents to path
sys.path.append('ai-agents')

async def test_database_operations():
    """Test the specific database operations that CIA chat uses"""
    try:
        from database_simple import db
        
        print("1. Testing load_conversation_state...")
        result = await db.load_conversation_state("test_session_123")
        print(f"[SUCCESS] load_conversation_state: {type(result)}")
        
        print("\n2. Testing save_conversation_state...")
        result = await db.save_conversation_state(
            user_id="test_user_456",
            thread_id="test_session_123", 
            agent_type="CIA",
            state={"messages": [{"role": "user", "content": "test"}]}
        )
        print(f"[SUCCESS] save_conversation_state: {type(result)}")
        
        print("\n3. Testing get_or_create_test_user...")
        user_id = await db.get_or_create_test_user()
        print(f"[SUCCESS] get_or_create_test_user: {user_id}")
        
        print("\n4. Testing direct Supabase query...")
        result = db.client.table("bid_cards").select("id").limit(1).execute()
        print(f"[SUCCESS] Direct query: {len(result.data)} records")
        
    except Exception as e:
        print(f"[FAILED] Database operation error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Database Operations Testing ===")
    asyncio.run(test_database_operations())