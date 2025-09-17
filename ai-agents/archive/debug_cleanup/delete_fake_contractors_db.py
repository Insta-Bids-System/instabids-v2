#!/usr/bin/env python3
"""
Delete fake contractors directly from Supabase database
Removes contractors: Premium Kitchen, Budget Home Solutions, Modern Design Builders
"""

import os

from dotenv import load_dotenv
from supabase import create_client


# Load environment variables
load_dotenv()

# Fake contractor names to delete (using LIKE queries)
FAKE_CONTRACTOR_PATTERNS = [
    "Premium Kitchen%",
    "Budget%",
    "Modern Design%"
]

def delete_fake_contractors():
    """Delete fake contractors directly from database"""

    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        print("ERROR: SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        return

    supabase = create_client(supabase_url, supabase_key)

    print("DELETING FAKE CONTRACTORS FROM DATABASE")
    print("=" * 50)

    # First, get all contractor proposals for the bid card to see what we have
    bid_card_id = "4c9dfb00-ee77-41da-8b8d-2615dbd31d95"

    try:
        # Get current proposals
        current_response = supabase.table("contractor_proposals").select("*").eq("bid_card_id", bid_card_id).execute()
        current_proposals = current_response.data

        print(f"Current proposals: {len(current_proposals)}")
        for proposal in current_proposals:
            print(f"  - {proposal['contractor_name']} (${proposal['bid_amount']:,.0f})")

        print("\nDeleting fake contractors...")

        # Delete proposals matching fake contractor patterns
        for pattern in FAKE_CONTRACTOR_PATTERNS:
            print(f"Deleting contractors matching: {pattern}")

            # Use ilike for case-insensitive pattern matching
            delete_response = supabase.table("contractor_proposals").delete().ilike("contractor_name", pattern).execute()

            if delete_response.data:
                print(f"  OK Deleted {len(delete_response.data)} proposals")
                for deleted in delete_response.data:
                    print(f"    - {deleted['contractor_name']}")
            else:
                print(f"  INFO No proposals found matching {pattern}")

        print("\nVERIFICATION:")

        # Verify deletion
        verify_response = supabase.table("contractor_proposals").select("*").eq("bid_card_id", bid_card_id).execute()
        remaining_proposals = verify_response.data

        fake_found = []
        for proposal in remaining_proposals:
            if any(word in proposal["contractor_name"].lower() for word in ["premium", "budget", "modern"]):
                fake_found.append(proposal["contractor_name"])

        if fake_found:
            print(f"FAIL Still found fake contractors: {fake_found}")
        else:
            print("SUCCESS All fake contractors successfully removed!")

        print(f"\nREMAINING contractors: {len(remaining_proposals)}")
        for proposal in remaining_proposals:
            print(f"   - {proposal['contractor_name']} (${proposal['bid_amount']:,.0f})")

    except Exception as e:
        print(f"ERROR: {e!s}")

if __name__ == "__main__":
    delete_fake_contractors()
