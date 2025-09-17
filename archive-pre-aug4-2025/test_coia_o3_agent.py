"""
Test COIA OpenAI O3 Agent - Agent 4 Contractor UX Testing
Purpose: Verify the actual COIA implementation and functionality
"""

import os
import asyncio
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append('C:\\Users\\Not John Or Justin\\Documents\\instabids\\ai-agents')

load_dotenv(override=True)

async def test_coia_o3_agent():
    """Test the COIA OpenAI O3 agent functionality"""
    print("=" * 60)
    print("AGENT 4 - COIA OpenAI O3 AGENT TEST")
    print("=" * 60)
    
    try:
        # Import the COIA agent
        from agents.coia.openai_o3_agent import OpenAIO3CoIA
        print("SUCCESS: Successfully imported OpenAIO3CoIA")
        
        # Initialize the agent
        coia = OpenAIO3CoIA()
        print("SUCCESS: Successfully initialized COIA agent")
        
        # Test basic conversation
        print("\nTEST: Testing contractor onboarding conversation...")
        session_id = "agent4_test_session_001"
        
        result = await coia.process_message(
            session_id,
            "Hi, I'm a plumber looking to join InstaBids as a contractor. I run Mike's Plumbing Services in Orlando, Florida."
        )
        
        print(f"SUCCESS: COIA Response received")
        print(f"   Stage: {result.get('stage', 'unknown')}")
        print(f"   Response length: {len(result.get('response', ''))}")
        print(f"   Contractor ID: {result.get('contractor_id', 'None')}")
        
        # Test follow-up message if in research confirmation
        if result.get('stage') == 'research_confirmation':
            print("\nTEST: Testing research confirmation...")
            result2 = await coia.process_message(
                session_id,
                "Yes, that information looks correct. Please create my profile."
            )
            
            print(f"SUCCESS: Confirmation Response received")
            print(f"   Final Stage: {result2.get('stage', 'unknown')}")
            print(f"   Contractor ID: {result2.get('contractor_id', 'None')}")
        
        print("\n" + "=" * 60)
        print("COIA O3 AGENT TEST: PASSED")
        print("=" * 60)
        return True
        
    except ImportError as e:
        print(f"ERROR: Import Error: {e}")
        print("   COIA agent may not be properly installed")
        return False
        
    except Exception as e:
        print(f"ERROR: Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_coia_o3_agent())
    print(f"\nFINAL RESULT: {'SUCCESS' if success else 'FAILED'}")