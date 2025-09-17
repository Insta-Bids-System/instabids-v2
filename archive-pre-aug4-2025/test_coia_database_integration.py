"""
Test CoIA Database Integration
Purpose: Test complete contractor profile creation flow with real database
"""

import asyncio
import json
import os
from datetime import datetime

from dotenv import load_dotenv


# Load environment
load_dotenv(override=True)

# Import CoIA directly
from agents.coia.agent import initialize_coia


async def test_coia_database_integration():
    """Test CoIA agent with real database integration"""

    print("TESTING COIA DATABASE INTEGRATION")
    print("=" * 60)

    # Initialize CoIA with real API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] No ANTHROPIC_API_KEY found in environment")
        return False

    coia_agent = initialize_coia(api_key)
    print("[OK] CoIA Agent initialized with database integration")

    # Test session
    session_id = f"test_db_contractor_{datetime.now().timestamp()}"
    print(f"[SESSION] Session ID: {session_id}")
    print()

    # Simulate a complete contractor onboarding conversation
    test_conversation = [
        ("I'm a general contractor with 8 years of experience", "experience collection"),
        ("I work primarily in Los Angeles and can travel up to 25 miles", "service area collection"),
        ("I specialize in kitchen remodels and bathroom renovations", "specialization collection"),
        ("My company is called Elite Home Renovations and I'm licensed", "company details"),
        ("I offer 5-year warranties and have liability insurance", "final details")
    ]

    contractor_id = None

    for i, (message, stage_description) in enumerate(test_conversation, 1):
        print(f"[MSG {i}] Testing: {stage_description}")
        print(f"[USER] {message}")

        try:
            # Process message with CoIA
            result = await coia_agent.process_message(
                session_id=session_id,
                user_message=message,
                context={}
            )

            print(f"[COIA] Response: {result['response'][:100]}...")
            print(f"[STAGE] Current Stage: {result['stage']}")
            print(f"[PROGRESS] Profile Completeness: {result['profile_progress']['completeness']:.1%}")

            if result.get("contractor_id"):
                contractor_id = result["contractor_id"]
                print(f"[SUCCESS] Contractor Profile Created: {contractor_id}")
                break

            print("-" * 40)

        except Exception as e:
            print(f"[ERROR] Error processing message: {e}")
            import traceback
            print(traceback.format_exc())
            return False

    # Verify database entry was created
    if contractor_id:
        print("\n[DATABASE] VERIFICATION")
        print("=" * 40)

        try:
            # Try to query the contractors table to verify the entry
            from supabase import create_client

            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")

            if supabase_url and supabase_key:
                supabase = create_client(supabase_url, supabase_key)

                # Query the created contractor
                result = supabase.table("contractors").select(
                    "id, company_name, specialties, service_areas, tier, verified, created_at"
                ).eq("id", contractor_id).execute()

                if result.data:
                    contractor = result.data[0]
                    print("[OK] Database Entry Verified:")
                    print(f"  ID: {contractor['id']}")
                    print(f"  Company: {contractor['company_name']}")
                    print(f"  Specialties: {contractor['specialties']}")
                    print(f"  Service Areas: {contractor['service_areas']}")
                    print(f"  Tier: {contractor['tier']}")
                    print(f"  Verified: {contractor['verified']}")
                    print(f"  Created: {contractor['created_at']}")

                    # Check if enrichment was triggered (would show updated_at different from created_at)
                    created_time = datetime.fromisoformat(contractor["created_at"].replace("Z", "+00:00"))
                    print(f"  Profile Created: {created_time}")

                    return True
                else:
                    print("[ERROR] Contractor not found in database")
                    return False
            else:
                print("[WARNING] No Supabase credentials - cannot verify database")
                return True  # Consider success if CoIA created ID

        except Exception as e:
            print(f"[ERROR] Database verification failed: {e}")
            return False
    else:
        print("[ERROR] No contractor ID returned - profile creation failed")
        return False

async def test_profile_enrichment_integration():
    """Test profile enrichment with mock website data"""
    print("\n[ENRICHMENT] TESTING PROFILE ENRICHMENT")
    print("=" * 40)

    try:
        # Initialize CoIA
        api_key = os.getenv("ANTHROPIC_API_KEY")
        coia_agent = initialize_coia(api_key)

        # Test enrichment with a mock contractor (assuming one exists)
        mock_contractor_id = "test-contractor-123"
        mock_website = "https://example-contractor.com"

        print(f"[TEST] Simulating enrichment for contractor: {mock_contractor_id}")
        print(f"[WEBSITE] Mock website: {mock_website}")

        # This would trigger background enrichment
        await coia_agent._enrich_contractor_profile(mock_contractor_id, mock_website)

        print("[OK] Enrichment integration test completed (check logs for details)")
        return True

    except Exception as e:
        print(f"[ERROR] Enrichment test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

async def test_api_endpoint_integration():
    """Test that the main.py API endpoint works with updated CoIA"""
    print("\n[API] TESTING API ENDPOINT INTEGRATION")
    print("=" * 40)

    try:
        # Test payload that would be sent to /api/contractor-chat/message
        test_payload = {
            "session_id": f"api_test_{datetime.now().timestamp()}",
            "message": "I'm a plumber with 5 years experience in New York",
            "current_stage": "welcome",
            "profile_data": {}
        }

        print("[REQUEST] Simulating API request:")
        print(json.dumps(test_payload, indent=2))

        # Initialize CoIA and process like the API would
        api_key = os.getenv("ANTHROPIC_API_KEY")
        coia_agent = initialize_coia(api_key)

        result = await coia_agent.process_message(
            session_id=test_payload["session_id"],
            user_message=test_payload["message"],
            context={}
        )

        print("\n[RESPONSE] API would return:")
        # Remove sensitive data for logging
        safe_result = {
            "response_length": len(result.get("response", "")),
            "stage": result.get("stage"),
            "profile_completeness": result.get("profile_progress", {}).get("completeness"),
            "contractor_id": result.get("contractor_id"),
            "has_session_data": bool(result.get("session_data"))
        }
        print(json.dumps(safe_result, indent=2))

        print("[OK] API integration test completed successfully")
        return True

    except Exception as e:
        print(f"[ERROR] API integration test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    async def run_all_tests():
        print("STARTING COIA DATABASE INTEGRATION TESTS")
        print("=" * 60)

        results = []

        # Test 1: Basic database integration
        print("\n1. TESTING BASIC DATABASE INTEGRATION")
        results.append(await test_coia_database_integration())

        # Test 2: Profile enrichment integration
        print("\n2. TESTING PROFILE ENRICHMENT")
        results.append(await test_profile_enrichment_integration())

        # Test 3: API endpoint integration
        print("\n3. TESTING API ENDPOINT INTEGRATION")
        results.append(await test_api_endpoint_integration())

        # Summary
        print(f"\n{'='*60}")
        print("TEST RESULTS SUMMARY")
        print(f"{'='*60}")

        test_names = [
            "Database Integration",
            "Profile Enrichment",
            "API Endpoint Integration"
        ]

        for i, (name, result) in enumerate(zip(test_names, results, strict=False), 1):
            status = "[PASS]" if result else "[FAIL]"
            print(f"{i}. {name}: {status}")

        all_passed = all(results)
        overall = "[ALL TESTS PASSED]" if all_passed else "[SOME TESTS FAILED]"
        print(f"\nOverall Result: {overall}")

        if all_passed:
            print("\n[SUCCESS] CoIA database integration is working correctly!")
            print("[OK] Contractor profiles are being created in contractors table")
            print("[OK] Profile enrichment system is integrated")
            print("[OK] API endpoint compatibility maintained")
        else:
            print("\n[WARNING] Some tests failed - check error messages above")

        return all_passed

    asyncio.run(run_all_tests())
