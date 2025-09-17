#!/usr/bin/env python3
"""
Delete fake contractors from the InstaBids system
Removes contractors: Premium Kitchen, Budget Home Solutions, Modern Design Builders
"""

import asyncio

from database_simple import SupabaseDB


# Fake contractor IDs to delete
FAKE_CONTRACTOR_IDS = [
    "43407623-ce79-4351-aa15-8f9f79b64b45",  # Premium Kitchen Renovations
    "fca049f1-b168-425c-b687-d1bcb19b4e36",  # Budget Home Solutions
    "77244f42-7265-4261-9a8a-ccb16ceaeb23",  # Modern Design Builders
]

FAKE_CONTRACTOR_NAMES = [
    "Premium Kitchen Renovations",
    "Budget Home Solutions",
    "Modern Design Builders"
]

async def delete_fake_contractors():
    """Delete fake contractors and all related data"""
    db = SupabaseDB()

    print("🚨 DELETING FAKE CONTRACTORS")
    print("=" * 50)

    for i, contractor_id in enumerate(FAKE_CONTRACTOR_IDS):
        contractor_name = FAKE_CONTRACTOR_NAMES[i]
        print(f"Deleting: {contractor_name} (ID: {contractor_id})")

        try:
            # 1. Delete contractor proposals
            proposals_deleted = await db.delete_data(
                "contractor_proposals",
                {"contractor_id": contractor_id}
            )
            print(f"  ✅ Deleted {len(proposals_deleted) if proposals_deleted else 0} proposals")

            # 2. Delete contractor responses
            responses_deleted = await db.delete_data(
                "contractor_responses",
                {"contractor_id": contractor_id}
            )
            print(f"  ✅ Deleted {len(responses_deleted) if responses_deleted else 0} responses")

            # 3. Delete conversations
            conversations_deleted = await db.delete_data(
                "conversations",
                {"contractor_id": contractor_id}
            )
            print(f"  ✅ Deleted {len(conversations_deleted) if conversations_deleted else 0} conversations")

            # 4. Delete messages (via conversation)
            # This will be handled by cascade delete if FK constraints exist

            # 5. Delete bid card views
            views_deleted = await db.delete_data(
                "bid_card_views",
                {"contractor_id": contractor_id}
            )
            print(f"  ✅ Deleted {len(views_deleted) if views_deleted else 0} bid card views")

            # 6. Delete contractor engagement events
            engagement_deleted = await db.delete_data(
                "bid_card_engagement_events",
                {"contractor_id": contractor_id}
            )
            print(f"  ✅ Deleted {len(engagement_deleted) if engagement_deleted else 0} engagement events")

            # 7. Delete from contractors table if exists
            contractor_deleted = await db.delete_data(
                "contractors",
                {"id": contractor_id}
            )
            print(f"  ✅ Deleted {len(contractor_deleted) if contractor_deleted else 0} contractor records")

            print(f"  🎉 {contractor_name} completely removed!")

        except Exception as e:
            print(f"  ❌ Error deleting {contractor_name}: {e!s}")
            continue

    print("=" * 50)
    print("✅ CLEANUP COMPLETE")

    # Verify cleanup
    print("\n🔍 VERIFICATION:")
    remaining_proposals = await db.fetch_data(
        "contractor_proposals",
        {"bid_card_id": "4c9dfb00-ee77-41da-8b8d-2615dbd31d95"}
    )

    fake_found = []
    for proposal in remaining_proposals:
        if any(name in proposal["contractor_name"] for name in ["Premium", "Budget", "Modern"]):
            fake_found.append(proposal["contractor_name"])

    if fake_found:
        print(f"❌ Still found fake contractors: {fake_found}")
    else:
        print("✅ All fake contractors successfully removed!")
        print(f"📊 Remaining contractors: {len(remaining_proposals)}")
        for proposal in remaining_proposals:
            print(f"   - {proposal['contractor_name']}")

if __name__ == "__main__":
    asyncio.run(delete_fake_contractors())
