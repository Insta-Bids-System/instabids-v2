"""
Test CoIA (Contractor Interface Agent) Integration
Purpose: Test the complete contractor onboarding chat flow with Claude Opus 4
"""

import asyncio
import json
from datetime import datetime

# Import CoIA directly
from agents.coia.agent import initialize_coia
from agents.coia.state import coia_state_manager


async def test_coia_integration():
    """Test CoIA agent with mock contractor conversations"""

    print("TESTING COIA (Contractor Interface Agent) INTEGRATION")
    print("=" * 60)

    # Initialize CoIA with demo key (will use fallback if no real API key)
    api_key = "demo_key"  # Replace with real key for full testing
    coia_agent = initialize_coia(api_key)

    print("[OK] CoIA Agent initialized")
    print(f"[API] Using API key: {api_key[:10]}...")

    # Test session
    session_id = f"test_contractor_{datetime.now().timestamp()}"
    print(f"[SESSION] Session ID: {session_id}")
    print()

    # Test conversation flow
    test_messages = [
        "I'm a general contractor with 8 years of experience",
        "I work primarily in Los Angeles and travel up to 25 miles",
        "I specialize in kitchen remodels and offer 5-year warranties on all work"
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"[MSG {i}] Test Message: {message}")

        try:
            # Process message with CoIA
            result = await coia_agent.process_message(
                session_id=session_id,
                user_message=message,
                context={}
            )

            print(f"[COIA] Response: {result['response'][:100]}...")
            print(f"[STAGE] Stage: {result['stage']}")
            print(f"[PROGRESS] Profile Completeness: {result['profile_progress']['completeness']:.1%}")
            print(f"[PROJECTS] Matching Projects: {result['profile_progress']['matchingProjects']}")

            if result.get("contractor_id"):
                print(f"[COMPLETE] Contractor Profile Created: {result['contractor_id']}")

            print("-" * 40)

        except Exception as e:
            print(f"[ERROR] Error processing message: {e}")
            import traceback
            print(traceback.format_exc())
            print()

    # Test state management
    print("\n[TEST] TESTING STATE MANAGEMENT")
    print("=" * 40)

    state = coia_state_manager.get_session(session_id)
    if state:
        print("[OK] Session state found")
        print(f"[STAGE] Current stage: {state.current_stage}")
        print(f"[MESSAGES] Messages: {len(state.messages)}")
        print(f"[PROGRESS] Profile completeness: {state.profile.calculate_completeness():.1%}")
        print(f"[PROFILE] Profile data: {json.dumps(state.profile.to_dict(), indent=2)}")
    else:
        print("[ERROR] No session state found")

    print("\n[COMPLETE] COIA INTEGRATION TEST COMPLETE")
    return True

async def test_api_endpoint_simulation():
    """Simulate API endpoint testing"""
    print("\n[API] SIMULATING API ENDPOINT TESTING")
    print("=" * 40)

    # This would be the payload sent to /api/contractor-chat/message
    test_payload = {
        "session_id": f"api_test_{datetime.now().timestamp()}",
        "message": "I'm a plumber with 5 years experience",
        "current_stage": "welcome",
        "profile_data": {}
    }

    print("[REQUEST] API Request Payload:")
    print(json.dumps(test_payload, indent=2))

    # Initialize CoIA for API simulation
    api_key = "demo_key"
    coia_agent = initialize_coia(api_key)

    try:
        result = await coia_agent.process_message(
            session_id=test_payload["session_id"],
            user_message=test_payload["message"],
            context={
                "current_stage": test_payload["current_stage"],
                "profile_data": test_payload["profile_data"]
            }
        )

        print("\n[RESPONSE] API Response:")
        print(json.dumps(result, indent=2, default=str))

    except Exception as e:
        print(f"[ERROR] API simulation error: {e}")
        import traceback
        print(traceback.format_exc())

    return True

if __name__ == "__main__":
    asyncio.run(test_coia_integration())
    asyncio.run(test_api_endpoint_simulation())
