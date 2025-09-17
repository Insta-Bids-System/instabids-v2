#!/usr/bin/env python3
"""
Final Test: Bid Card with Images - CIA → JAA → HTML
"""
import asyncio
import os
import sys
from datetime import datetime


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.cia.agent import CustomerInterfaceAgent
from agents.jaa.new_agent import NewJobAssessmentAgent


def generate_html_bid_card(bid_data, bid_number):
    """Generate HTML bid card for email/SMS"""

    # Extract data
    project_type = bid_data.get("project_type", "Project").replace("_", " ").title()
    urgency = bid_data.get("urgency_level", "flexible")
    budget_min = bid_data.get("budget_min", 0)
    budget_max = bid_data.get("budget_max", 0)
    location_zip = bid_data.get("location_zip", "")

    # Get images (JAA provides as 'images', BidCard.tsx expects 'photo_urls')
    images = bid_data.get("images", [])
    contractor_count = bid_data.get("contractor_requirements", {}).get("contractor_count", 4)

    # Get urgency text
    urgency_text = {
        "emergency": "Urgent - ASAP",
        "week": "Within 7 Days",
        "month": "Within 30 Days",
        "flexible": "Flexible Timeline"
    }.get(urgency, "Flexible Timeline")

    # Generate simple HTML
    html = f"""
    <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px; background-color: #ffffff; font-family: -apple-system, sans-serif;">
        <h2 style="font-size: 24px; margin-bottom: 16px; color: #111827;">
            {project_type}
        </h2>
        <div style="margin-bottom: 16px;">
            <span style="background-color: #fef3c7; color: #92400e; padding: 4px 12px; border-radius: 4px; font-size: 14px;">
                {urgency_text}
            </span>
        </div>
        <p style="color: #6b7280; margin-bottom: 16px;">
            Location: ZIP {location_zip}<br>
            Budget: ${budget_min:,}-${budget_max:,}<br>
            Looking for: {contractor_count} contractors<br>
            {'Photos: ' + str(len(images)) + ' included' if images else 'No photos'}
        </p>
        <a href="https://instabids.com/bid-cards/{bid_number}"
           style="display: inline-block; background-color: #2563eb; color: #ffffff; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600;">
            View Full Details{' & Photos' if images else ''} →
        </a>
    </div>
    """

    return html


async def test_images_flow():
    """Test complete flow with images"""
    print("\n" + "="*80)
    print("TESTING BID CARD WITH IMAGES")
    print("="*80 + "\n")

    # Use existing user
    user_id = "bda3ab78-e034-4be7-8285-1b7be1bf1387"
    session_id = f"test_img_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Simulate photo URLs
    photo_urls = [
        "https://supabase.instabids.com/storage/v1/object/public/project-photos/kitchen_1.jpg",
        "https://supabase.instabids.com/storage/v1/object/public/project-photos/kitchen_2.jpg",
        "https://supabase.instabids.com/storage/v1/object/public/project-photos/kitchen_3.jpg"
    ]

    # Initialize CIA agent
    cia_agent = CustomerInterfaceAgent(anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Test message
    test_message = """
    I need my kitchen cabinets replaced. They're water damaged and falling apart.
    I'm in Miami, FL 33139. Budget is around $15,000-20,000 for new cabinets.
    Need this done within 2 months. I've uploaded 3 photos showing the damage.
    """

    print("Test Message:")
    print(test_message)
    print(f"\nImages provided: {len(photo_urls)}")
    for i, url in enumerate(photo_urls):
        print(f"  Photo {i+1}: {url}")

    # Process with CIA (pass images parameter)
    print("\n" + "-"*80)
    print("PROCESSING WITH CIA...")

    result = await cia_agent.handle_conversation(
        user_id=user_id,
        message=test_message,
        images=photo_urls,  # Pass images here
        session_id=session_id
    )

    # Check if images were collected
    if "state" in result and "collected_info" in result["state"]:
        collected = result["state"]["collected_info"]
        collected_photos = collected.get("uploaded_photos", [])
        print(f"\nCIA collected {len(collected_photos)} photos")
        print(f"Project type: {collected.get('project_type')}")
        print(f"Budget: ${collected.get('budget_min')}-${collected.get('budget_max')}")
        print(f"Ready for JAA: {result.get('ready_for_jaa')}")

    # Wait for database
    await asyncio.sleep(3)

    # Process with JAA
    print("\n" + "-"*80)
    print("PROCESSING WITH JAA...")

    jaa_agent = NewJobAssessmentAgent()
    jaa_result = jaa_agent.process_conversation(session_id)

    if jaa_result["success"]:
        print("JAA Processing SUCCESSFUL!")
        bid_data = jaa_result["bid_card_data"]
        bid_number = jaa_result["bid_card_number"]

        # Check images in bid card
        bid_images = bid_data.get("images", [])
        print(f"\nBid Card Number: {bid_number}")
        print(f"Images in bid card: {len(bid_images)}")

        # Generate HTML
        html_card = generate_html_bid_card(bid_data, bid_number)

        # Save HTML
        html_filename = f"bid_card_{bid_number}_with_images.html"
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_card)

        print(f"\nHTML Bid Card saved to: {html_filename}")

        # Summary
        print("\n" + "="*80)
        print("SUMMARY: IMAGE HANDLING IN BID CARDS")
        print("="*80)

        # Check complete flow
        cia_photos = result.get("state", {}).get("collected_info", {}).get("uploaded_photos", [])
        jaa_images = bid_data.get("images", [])

        print(f"\n1. Photos provided to CIA: {len(photo_urls)}")
        print(f"2. Photos stored by CIA: {len(cia_photos)}")
        print(f"3. Images extracted by JAA: {len(jaa_images)}")
        print("4. HTML bid card generated: YES")

        if len(photo_urls) == len(cia_photos) == len(jaa_images):
            print("\nSUCCESS: All images flow through the system correctly!")
        else:
            print("\nWARNING: Image count mismatch in flow")

        # Note about BidCard.tsx
        print("\nNOTE FOR FRONTEND:")
        print("- JAA provides: bid_data['images']")
        print("- BidCard.tsx expects: bidCard.photo_urls")
        print("- Solution: Map 'images' to 'photo_urls' when creating bidCard object")

        return True
    else:
        print(f"JAA Processing FAILED: {jaa_result.get('error')}")
        return False


async def main():
    """Run test"""
    try:
        await test_images_flow()
    except Exception as e:
        print(f"\nTest error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
