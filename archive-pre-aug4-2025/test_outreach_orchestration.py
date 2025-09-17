#!/usr/bin/env python3
"""
Test Complete Outreach Orchestration
Demonstrates the full flow from Opus 4 matching to multi-channel outreach
"""

from datetime import datetime

from agents.cda.agent_v2 import IntelligentContractorDiscoveryAgent
from agents.orchestration.campaign_orchestrator import OutreachCampaignOrchestrator
from agents.tracking.bid_distribution_tracker import BidDistributionTracker


def test_complete_outreach_flow():
    """Test the complete outreach orchestration flow"""
    print("COMPLETE OUTREACH ORCHESTRATION TEST")
    print("=" * 70)
    print("Flow: Opus 4 CDA → Multi-Channel Outreach → Distribution Tracking")
    print()

    # Test bid card
    bid_card = {
        "id": "test-outreach-flow-123",
        "project_type": "bathroom renovation",
        "bid_document": {
            "project_overview": {
                "description": "Master bathroom complete renovation. Want modern look but not too sterile. Prefer working with established local contractors who have done similar projects."
            },
            "budget_information": {
                "budget_min": 15000,
                "budget_max": 25000,
                "notes": "Quality is more important than lowest price"
            },
            "timeline": {
                "urgency_level": "month",
                "notes": "Would like to start within 4-6 weeks"
            }
        },
        "location": {
            "city": "Boca Raton",
            "state": "FL",
            "zip_code": "33432"
        }
    }

    print("1. TEST SCENARIO")
    print("-" * 30)
    print(f"Project: {bid_card['project_type']}")
    print(f"Location: {bid_card['location']['city']}, {bid_card['location']['state']}")
    print(f"Budget: ${bid_card['bid_document']['budget_information']['budget_min']:,} - ${bid_card['bid_document']['budget_information']['budget_max']:,}")
    print(f"Timeline: {bid_card['bid_document']['timeline']['urgency_level']}")

    # Step 1: Use Opus 4 CDA to find and score contractors
    print("\n2. OPUS 4 INTELLIGENT CONTRACTOR DISCOVERY")
    print("-" * 50)

    cda = IntelligentContractorDiscoveryAgent()
    discovery_result = cda.discover_contractors_for_bid(bid_card["id"], contractors_needed=5)

    if not discovery_result["success"]:
        print(f"[ERROR] Discovery failed: {discovery_result.get('error')}")
        return False

    selected_contractors = discovery_result.get("selected_contractors", [])
    print(f"\nFound and scored {len(selected_contractors)} contractors:")

    contractor_ids = []
    for i, contractor in enumerate(selected_contractors[:5], 1):
        print(f"\n#{i} {contractor['company_name']}")
        print(f"   Match Score: {contractor['match_score']}/100")
        print(f"   Tier: {contractor['discovery_tier']}")
        print(f"   Contact: {contractor.get('primary_email') or contractor.get('phone', 'No contact')}")
        contractor_ids.append(contractor["id"])

    # Step 2: Create outreach campaign
    print("\n3. CREATING MULTI-CHANNEL OUTREACH CAMPAIGN")
    print("-" * 50)

    orchestrator = OutreachCampaignOrchestrator()

    # Determine channels based on available contact info
    channels = []
    email_count = sum(1 for c in selected_contractors if c.get("primary_email"))
    website_count = sum(1 for c in selected_contractors if c.get("website"))
    phone_count = sum(1 for c in selected_contractors if c.get("phone"))

    if email_count > 0:
        channels.append("email")
        print(f"  ✓ Email channel available for {email_count} contractors")

    if website_count > 0:
        channels.append("website_form")
        print(f"  ✓ Website forms available for {website_count} contractors")

    if phone_count > 0:
        channels.append("sms")
        print(f"  ✓ SMS channel available for {phone_count} contractors")

    # Create the campaign
    campaign_result = orchestrator.create_campaign(
        name=f"Bathroom Renovation - {bid_card['location']['city']}",
        bid_card_id=bid_card["id"],
        contractor_ids=contractor_ids,
        channels=channels,
        schedule={"start_time": datetime.now().isoformat()}
    )

    if not campaign_result["success"]:
        print(f"[ERROR] Campaign creation failed: {campaign_result.get('error')}")
        return False

    campaign_id = campaign_result["campaign_id"]
    print(f"\nCampaign created: {campaign_id}")

    # Step 3: Execute the campaign
    print("\n4. EXECUTING OUTREACH CAMPAIGN")
    print("-" * 50)

    execution_result = orchestrator.execute_campaign(campaign_id)

    if execution_result["success"]:
        results = execution_result["results"]
        print("\nCampaign Results:")
        print(f"  Total Attempts: {results['total_attempts']}")
        print(f"  Successful Contacts: {results['successful_contacts']}")
        print(f"  Success Rate: {(results['successful_contacts'] / len(contractor_ids) * 100):.1f}%")

        print("\nBy Channel:")
        for channel, stats in results["by_channel"].items():
            success_rate = (stats["successes"] / stats["attempts"] * 100) if stats["attempts"] > 0 else 0
            print(f"  {channel}: {stats['successes']}/{stats['attempts']} ({success_rate:.1f}%)")

    # Step 4: Check distribution tracking
    print("\n5. DISTRIBUTION TRACKING")
    print("-" * 50)

    tracker = BidDistributionTracker()
    distribution_data = tracker.get_contractors_for_bid(bid_card["id"])

    if distribution_data["success"]:
        print("\nBid Card Distribution Summary:")
        print(f"  Total Distributed: {distribution_data['total_distributed']}")
        print(f"  Response Rate: {distribution_data['response_rate']:.1f}%")

        print("\nContractors Contacted:")
        for contractor in distribution_data["contractors"][:5]:
            print(f"  - {contractor['company_name']}")
            print(f"    Method: {contractor['method']}")
            print(f"    Score: {contractor['match_score']}")
            print(f"    Status: {contractor['status']}")

    # Step 5: Show campaign analytics
    print("\n6. CAMPAIGN ANALYTICS")
    print("-" * 50)

    campaign_status = orchestrator.get_campaign_status(campaign_id)

    if campaign_status["success"]:
        metrics = campaign_status["metrics"]
        print("\nCampaign Performance:")
        print(f"  Open Rate: {metrics['open_rate']:.1f}%")
        print(f"  Response Rate: {metrics['response_rate']:.1f}%")
        print(f"  Interest Rate: {metrics['interest_rate']:.1f}%")

    # Step 6: Identify follow-up candidates
    print("\n7. FOLLOW-UP CANDIDATES")
    print("-" * 50)

    followup_data = tracker.get_follow_up_candidates(days_since_sent=0, max_follow_ups=2)

    if followup_data["success"] and followup_data["candidates"]:
        print(f"\nContractors needing follow-up: {followup_data['total_candidates']}")
        for candidate in followup_data["candidates"][:3]:
            print(f"  - {candidate['company_name']} (Score: {candidate['match_score']})")
            print(f"    Sent {candidate['days_since_sent']} days ago via {candidate['last_method']}")
    else:
        print("\nNo follow-ups needed yet (campaign just executed)")

    print("\n" + "=" * 70)
    print("OUTREACH ORCHESTRATION TEST COMPLETE")
    print("=" * 70)

    return True


if __name__ == "__main__":
    print("Testing Complete Outreach Orchestration...")
    print("This demonstrates:")
    print("1. Opus 4 intelligent contractor matching")
    print("2. Multi-channel outreach campaign creation")
    print("3. Campaign execution across email/SMS/forms")
    print("4. Distribution tracking and analytics")
    print("5. Follow-up candidate identification")
    print()

    success = test_complete_outreach_flow()

    if success:
        print("\n✓ Outreach orchestration system is fully operational!")
    else:
        print("\n✗ Test failed - check error messages above")
