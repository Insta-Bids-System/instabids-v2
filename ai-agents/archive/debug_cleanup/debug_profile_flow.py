#!/usr/bin/env python
"""
Debug the profile data flow through COIA system
Track exactly where profile data gets lost
"""

import asyncio
import json
import logging
import os

from dotenv import load_dotenv


# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

# Set up DETAILED logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def debug_profile_flow():
    """Debug the profile extraction and state flow"""

    from langgraph.checkpoint.memory import MemorySaver

    from agents.coia.unified_graph import create_unified_coia_system, invoke_coia_chat

    print("PROFILE FLOW DEBUG TEST")
    print("=" * 50)

    # Create system with in-memory checkpointer
    checkpointer = MemorySaver()
    app = await create_unified_coia_system(checkpointer)

    contractor_id = "debug_test"

    # Simple message with all profile data
    test_msg = "Hi, I'm Mike from Dallas HVAC Pro. We specialize in emergency HVAC repairs in Dallas, been in business 15 years."

    print(f"\nINPUT MESSAGE: {test_msg}")
    print("-" * 50)

    # Invoke the system
    result = await invoke_coia_chat(
        app=app,
        user_message=test_msg,
        session_id="debug_session",
        contractor_lead_id=contractor_id
    )

    print("\nRESULT ANALYSIS:")
    print("-" * 50)

    # Check what's in the result
    if result:
        # 1. Check messages
        messages = result.get("messages", [])
        print(f"Messages count: {len(messages)}")
        if messages:
            last_msg = messages[-1]
            print(f"Last message type: {type(last_msg)}")
            print(f"Last message content: {last_msg.content[:100]}...")

        # 2. Check profile data
        profile = result.get("contractor_profile", {})
        print(f"\nContractor Profile: {json.dumps(profile, indent=2) if profile else 'EMPTY'}")

        # 3. Check company name
        company = result.get("company_name")
        print(f"\nCompany Name: {company}")

        # 4. Check current mode
        mode = result.get("current_mode")
        print(f"Current Mode: {mode}")

        # 5. Check all keys in result
        print(f"\nAll result keys: {list(result.keys())}")

        # 6. Check for any profile-related keys
        profile_keys = [k for k in result.keys() if "profile" in k.lower()]
        print(f"Profile-related keys: {profile_keys}")

        # Now test if state persists
        print("\n" + "=" * 50)
        print("TESTING STATE PERSISTENCE")
        print("=" * 50)

        # Second call with same contractor_id
        test_msg2 = "Show me HVAC projects"
        print(f"\nSECOND MESSAGE: {test_msg2}")

        result2 = await invoke_coia_chat(
            app=app,
            user_message=test_msg2,
            session_id="debug_session2",  # Different session
            contractor_lead_id=contractor_id  # Same contractor
        )

        if result2:
            profile2 = result2.get("contractor_profile", {})
            print(f"\nProfile in second call: {json.dumps(profile2, indent=2) if profile2 else 'EMPTY'}")

            # Check if profile persisted
            if profile2:
                print("\nPROFILE PERSISTENCE CHECK:")
                print(f"Company name persisted: {'company_name' in profile2}")
                print(f"Years in business persisted: {'years_in_business' in profile2}")
                print(f"Service areas persisted: {'service_areas' in profile2}")
            else:
                print("\nFAILED: Profile did not persist!")
    else:
        print("ERROR: No result returned from invoke_coia_chat")

    return result

if __name__ == "__main__":
    asyncio.run(debug_profile_flow())
