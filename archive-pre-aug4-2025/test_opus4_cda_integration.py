#!/usr/bin/env python3
"""
Test Opus 4 CDA Integration with Main API
Verifies the new intelligent CDA is working on port 8003
"""

import time

import requests


def test_opus4_cda_api():
    """Test the Opus 4 CDA through the API"""
    base_url = "http://localhost:8008"

    print("TESTING OPUS 4 CDA INTEGRATION")
    print("=" * 60)

    # 1. Check API health
    print("\n1. Checking API health...")
    try:
        response = requests.get(f"{base_url}/")
        health = response.json()
        print(f"   API Status: {health['status']}")
        print(f"   CDA Status: {health['agents']['cda']}")

        if health["agents"]["cda"] != "active":
            print("   [ERROR] CDA agent is not active!")
            return False
    except Exception as e:
        print(f"   [ERROR] Cannot connect to API: {e}")
        print("   Make sure the server is running: cd ai-agents && python main.py")
        return False

    # 2. Get agent status details
    print("\n2. Getting CDA agent details...")
    try:
        response = requests.get(f"{base_url}/api/agents/status")
        agents = response.json()
        cda_info = agents["cda"]
        print(f"   Description: {cda_info['description']}")
        print(f"   Model: {cda_info['model']}")
    except Exception as e:
        print(f"   [ERROR] Failed to get agent status: {e}")

    # 3. Test CDA discovery with a test bid card
    print("\n3. Testing Opus 4 contractor discovery...")

    # Create a test bid card ID (in real usage, this would come from JAA)
    test_bid_card_id = f"test-opus4-api-{int(time.time())}"

    # First, we need to create a test bid card in the database
    # For this test, we'll assume it exists or use a known test ID

    try:
        print(f"   Discovering contractors for bid card: {test_bid_card_id}")
        print("   Requesting 5 contractors with Opus 4 intelligent matching...")

        response = requests.post(
            f"{base_url}/api/cda/discover/{test_bid_card_id}",
            params={"contractors_needed": 5}
        )

        if response.status_code == 200:
            result = response.json()

            if result["success"]:
                print("\n   ✓ Discovery successful!")
                print(f"   Contractors found: {result['contractors_found']}")
                print(f"   Processing time: {result.get('processing_time_ms', 0)}ms")

                # Show tier breakdown
                if "tier_breakdown" in result:
                    print("\n   Tier Breakdown:")
                    for tier, data in result["tier_breakdown"].items():
                        print(f"      {tier}: {data['count']} contractors")

                # Show selected contractors with Opus 4 scores
                if "selected_contractors" in result:
                    print("\n   Selected Contractors (Opus 4 Scored):")
                    for i, contractor in enumerate(result["selected_contractors"][:5], 1):
                        print(f"\n   #{i} {contractor.get('company_name', 'Unknown')}")
                        print(f"      Match Score: {contractor.get('match_score', 0)}/100")
                        print(f"      Tier: {contractor.get('discovery_tier', 'Unknown')}")
                        print(f"      Reasoning: {contractor.get('selection_reasoning', 'N/A')[:100]}...")

                        # Show contact info
                        contact = []
                        if contractor.get("primary_email"):
                            contact.append(f"Email: {contractor['primary_email']}")
                        if contractor.get("phone"):
                            contact.append(f"Phone: {contractor['phone']}")
                        if contractor.get("website"):
                            contact.append(f"Web: {contractor['website']}")

                        if contact:
                            print(f"      Contact: {', '.join(contact)}")

                # Show Opus 4 analysis if available
                if result.get("opus4_analysis"):
                    print("\n   Opus 4 Bid Analysis:")
                    analysis = result["opus4_analysis"]
                    if isinstance(analysis, dict):
                        for key, value in list(analysis.items())[:3]:
                            print(f"      {key}: {value}")
                    else:
                        print(f"      {str(analysis)[:200]}...")

                return True
            else:
                print(f"   [ERROR] Discovery failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   [ERROR] API returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("   [ERROR] Cannot connect to API server")
        print("   Make sure the server is running: cd ai-agents && python main.py")
        return False
    except Exception as e:
        print(f"   [ERROR] Failed to test discovery: {e}")
        return False

    # 4. Test cache endpoint
    print("\n4. Testing discovery cache...")
    try:
        response = requests.get(f"{base_url}/api/cda/cache/{test_bid_card_id}")

        if response.status_code == 200:
            response.json()
            print("   ✓ Cache data retrieved successfully")
        elif response.status_code == 404:
            print("   ✓ No cache found (expected for new bid card)")
        else:
            print(f"   [WARNING] Unexpected cache response: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Failed to test cache: {e}")


def main():
    print("This test verifies the Opus 4 CDA integration in the main API")
    print("Prerequisites:")
    print("1. API server running on port 8003")
    print("2. ANTHROPIC_API_KEY set in .env")
    print("3. GOOGLE_MAPS_API_KEY set in .env")
    print("4. Supabase connection configured")
    print()

    # Wait a moment for user to read
    time.sleep(2)

    success = test_opus4_cda_api()

    if success:
        print("\n" + "=" * 60)
        print("✓ OPUS 4 CDA INTEGRATION TEST PASSED")
        print("=" * 60)
        print("\nThe intelligent CDA with Opus 4 is now active in the main API!")
        print("\nCapabilities:")
        print("- Understands nuanced bid requirements")
        print("- Scores contractors based on bid-specific criteria")
        print("- Provides reasoning for each selection")
        print("- Integrates with existing 3-tier discovery system")
    else:
        print("\n" + "=" * 60)
        print("✗ OPUS 4 CDA INTEGRATION TEST FAILED")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("1. Ensure the API server is running: cd ai-agents && python main.py")
        print("2. Check that ANTHROPIC_API_KEY is set in .env")
        print("3. Verify GOOGLE_MAPS_API_KEY is set in .env")
        print("4. Check Supabase connection in .env")


if __name__ == "__main__":
    main()
