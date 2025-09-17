#!/usr/bin/env python3
"""
Delete fake contractors from the InstaBids system using direct API calls
Removes contractors: Premium Kitchen, Budget Home Solutions, Modern Design Builders
"""


import requests
from config.service_urls import get_backend_url


# Fake contractor IDs to delete
FAKE_CONTRACTORS = [
    {"id": "43407623-ce79-4351-aa15-8f9f79b64b45", "name": "Premium Kitchen Renovations"},
    {"id": "fca049f1-b168-425c-b687-d1bcb19b4e36", "name": "Budget Home Solutions"},
    {"id": "77244f42-7265-4261-9a8a-ccb16ceaeb23", "name": "Modern Design Builders"}
]

API_BASE = f"{get_backend_url()}/api"

def delete_fake_contractors():
    """Delete fake contractors via API calls"""

    print("DELETING FAKE CONTRACTORS")
    print("=" * 50)

    for contractor in FAKE_CONTRACTORS:
        contractor_id = contractor["id"]
        contractor_name = contractor["name"]

        print(f"Deleting: {contractor_name}")
        print(f"ID: {contractor_id}")

        try:
            # First, let's see what proposals exist for this contractor
            proposals_url = f"{API_BASE}/contractor-proposals/contractor/{contractor_id}"
            response = requests.get(proposals_url)

            if response.status_code == 200:
                proposals = response.json()
                print(f"  Found {len(proposals)} proposals")

                # Delete each proposal
                for proposal in proposals:
                    delete_url = f"{API_BASE}/contractor-proposals/{proposal['id']}"
                    delete_response = requests.delete(delete_url)
                    if delete_response.status_code == 200:
                        print(f"  OK Deleted proposal {proposal['id']}")
                    else:
                        print(f"  FAIL Failed to delete proposal {proposal['id']}: {delete_response.status_code}")

            print(f"  DONE {contractor_name} proposals removed!")

        except Exception as e:
            print(f"  ERROR Error deleting {contractor_name}: {e!s}")
            continue

    print("=" * 50)
    print("CLEANUP COMPLETE")

    # Verify cleanup
    print("\nVERIFICATION:")
    verify_url = f"{API_BASE}/contractor-proposals/bid-card/4c9dfb00-ee77-41da-8b8d-2615dbd31d95"
    response = requests.get(verify_url)

    if response.status_code == 200:
        remaining_proposals = response.json()

        fake_found = []
        for proposal in remaining_proposals:
            if any(name in proposal["contractor_name"] for name in ["Premium", "Budget", "Modern"]):
                fake_found.append(proposal["contractor_name"])

        if fake_found:
            print(f"FAIL Still found fake contractors: {fake_found}")
        else:
            print("SUCCESS All fake contractors successfully removed!")
            print(f"REMAINING contractors: {len(remaining_proposals)}")
            for proposal in remaining_proposals:
                print(f"   - {proposal['contractor_name']} (${proposal['bid_amount']:,.0f})")
    else:
        print(f"FAIL Failed to verify cleanup: {response.status_code}")

if __name__ == "__main__":
    delete_fake_contractors()
