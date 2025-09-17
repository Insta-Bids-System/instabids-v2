"""
Test CIA agent directly to diagnose timeout issue
"""
import os
import sys
import asyncio
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# Add ai-agents to path
sys.path.append('ai-agents')

from agents.cia.agent import CustomerInterfaceAgent

async def test_cia_direct():
    """Test CIA agent with direct API call"""
    print("Starting CIA direct test...")
    
    # Get API key
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if not anthropic_key:
        print("FAILED: No ANTHROPIC_API_KEY found")
        return False
    
    print(f"SUCCESS: API key found: {anthropic_key[:20]}...")
    
    # Initialize CIA agent
    print("Initializing CIA agent...")
    try:
        cia = CustomerInterfaceAgent(anthropic_key)
        print("SUCCESS: CIA agent initialized")
    except Exception as e:
        print(f"FAILED: CIA initialization failed: {e}")
        return False
    
    # Test simple conversation
    print("Testing conversation...")
    start_time = time.time()
    try:
        result = await cia.handle_conversation(
            user_id="test_user",
            message="I need help with my bathroom renovation",
            session_id="test_session"
        )
        end_time = time.time()
        print(f"SUCCESS: Conversation completed in {end_time - start_time:.2f} seconds")
        print(f"Response: {result.get('response', 'No response')[:100]}...")
        return True
    except Exception as e:
        end_time = time.time()
        print(f"FAILED: Conversation failed after {end_time - start_time:.2f} seconds")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_cia_direct())
    if success:
        print("\nSUCCESS: CIA DIRECT TEST PASSED")
    else:
        print("\nFAILED: CIA DIRECT TEST FAILED")