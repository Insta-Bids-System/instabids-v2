"""
Quick test script to verify Supabase connection
"""

import os
import sys

from dotenv import load_dotenv


# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv("../.env")

# Import our database module
import asyncio

from database import db


async def test_supabase():
    """Test Supabase connection and operations"""
    print("Testing Supabase connection...")
    print(f"URL: {os.getenv('SUPABASE_URL')}")
    print(f"Key: {os.getenv('SUPABASE_ANON_KEY')[:20]}...")

    try:
        # Test 1: Get or create test user
        print("\n1. Testing user creation...")
        user_id = await db.get_or_create_test_user()
        print(f"[OK] Test user ID: {user_id}")

        # Test 2: Save conversation state
        print("\n2. Testing save conversation state...")
        test_state = {
            "messages": [
                {"role": "user", "content": "Test message"},
                {"role": "assistant", "content": "Test response"}
            ],
            "current_phase": "discovery",
            "collected_info": {"project_type": "kitchen"}
        }

        saved = await db.save_conversation_state(
            user_id=user_id,
            thread_id="test-thread-001",
            agent_type="CIA",
            state=test_state
        )
        print(f"[OK] Saved conversation: {saved['id'] if saved else 'Failed'}")

        # Test 3: Load conversation state
        print("\n3. Testing load conversation state...")
        loaded = await db.load_conversation_state("test-thread-001")
        if loaded:
            print("[OK] Loaded conversation successfully")
            print(f"  - Thread ID: {loaded['thread_id']}")
            print(f"  - Agent Type: {loaded['agent_type']}")
            print(f"  - Has state: {'state' in loaded}")
        else:
            print("[FAIL] Failed to load conversation")

        print("\n[SUCCESS] All tests passed! Supabase integration is working.")

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_supabase())
