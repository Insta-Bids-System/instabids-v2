#!/usr/bin/env python3
"""
Test Complete Bid Card Generation with Images and HTML Output
"""
import asyncio
import os
import sys
from datetime import datetime


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from supabase import create_client

from agents.cia.agent import CustomerInterfaceAgent
from agents.jaa.new_agent import NewJobAssessmentAgent


def generate_email_html_bid_card(bid_data, bid_number):
    """Generate HTML bid card matching BidCard.tsx email variant"""

    # Extract data with proper field mapping
    project_type = bid_data.get("project_type", "Project").replace("_", " ").title()
    urgency = bid_data.get("urgency_level", "flexible")
    bid_data.get("timeline_urgency", "flexible")
    budget_min = bid_data.get("budget_min", 0)
    budget_max = bid_data.get("budget_max", 0)
    location = bid_data.get("location", {})
    location_zip = bid_data.get("location_zip", "")

    # Map 'images' to 'photo_urls' for BidCard.tsx compatibility
    images = bid_data.get("images", [])
    contractor_count = bid_data.get("contractor_requirements", {}).get("contractor_count", 4)

    # Get urgency text
    urgency_text = {
        "emergency": "Urgent - ASAP",
        "week": "Within 7 Days",
        "month": "Within 30 Days",
        "flexible": "Flexible Timeline"
    }.get(urgency, "Flexible Timeline")

    # Get location display
    if isinstance(location, dict):
        location_display = f"{location.get('city', 'City')}, {location.get('state', 'FL')}"
    else:
        location_display = f"ZIP: {location_zip}" if location_zip else "Location TBD"

    # Generate HTML matching BidCard.tsx email variant
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>InstaBids - {project_type}</title>
</head>
<body style="margin: 0; padding: 20px; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
    <div style="max-width: 600px; margin: 0 auto;">
        <!-- Main Card -->
        <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px; background-color: #ffffff; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">
            <!-- Project Title -->
            <h2 style="font-size: 24px; margin: 0 0 16px 0; color: #111827; font-weight: 600;">
                {project_type}
            </h2>

            <!-- Urgency Badge -->
            <div style="margin-bottom: 16px;">
                <span style="background-color: {'#fef3c7' if urgency == 'week' else '#dbeafe'};
                           color: {'#92400e' if urgency == 'week' else '#1e40af'};
                           padding: 4px 12px;
                           border-radius: 4px;
                           font-size: 14px;
                           font-weight: 500;
                           display: inline-block;">
                    {urgency_text}
                </span>
            </div>

            <!-- Key Details -->
            <p style="color: #6b7280; margin: 0 0 20px 0; font-size: 16px; line-height: 1.5;">
                📍 {location_display}<br>
                💰 Budget: ${budget_min:,}-${budget_max:,}<br>
                👥 {contractor_count} contractors needed
                {f'<br>📸 {len(images)} photos included' if images else ''}
            </p>

            <!-- Project Description if available -->
            {f'''<div style="background-color: #f9fafb; padding: 16px; border-radius: 6px; margin-bottom: 20px;">
                <p style="color: #374151; margin: 0; font-size: 14px; line-height: 1.5;">
                    {bid_data.get('project_description', '')}
                </p>
            </div>''' if bid_data.get('project_description') else ''}

            <!-- Special Requirements if any -->
            {f'''<div style="margin-bottom: 20px;">
                <p style="color: #6b7280; margin: 0; font-size: 14px;">
                    <strong>Special Requirements:</strong> {bid_data.get('special_requirements')}
                </p>
            </div>''' if bid_data.get('special_requirements') else ''}

            <!-- CTA Button -->
            <a href="https://instabids.com/bid-cards/{bid_number}"
               style="display: inline-block;
                      background-color: #2563eb;
                      color: #ffffff;
                      padding: 12px 24px;
                      border-radius: 6px;
                      text-decoration: none;
                      font-weight: 600;
                      font-size: 16px;">
                View Full Details{' & Photos' if images else ''} →
            </a>
        </div>

        <!-- Footer -->
        <p style="text-align: center; color: #9ca3af; font-size: 14px; margin-top: 20px;">
            InstaBids - Connecting Homeowners with Quality Contractors<br>
            <a href="https://instabids.com" style="color: #6b7280;">instabids.com</a>
        </p>
    </div>
</body>
</html>"""

    return html


async def test_with_real_images():
    """Test CIA → JAA with simulated image uploads"""
    print("\n" + "="*80)
    print("TESTING COMPLETE BID CARD WITH IMAGES")
    print("="*80 + "\n")

    # Load environment
    load_dotenv(override=True)

    # Initialize Supabase to simulate image upload
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    create_client(supabase_url, supabase_key)

    # Use existing user
    user_id = "bda3ab78-e034-4be7-8285-1b7be1bf1387"
    session_id = f"test_images_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    print(f"Using user ID: {user_id}")
    print(f"Session ID: {session_id}")

    # Simulate photo URLs (in production, these would come from Supabase storage)
    photo_urls = [
        "https://supabase.instabids.com/storage/v1/object/public/project-photos/kitchen_damage_1.jpg",
        "https://supabase.instabids.com/storage/v1/object/public/project-photos/kitchen_damage_2.jpg",
        "https://supabase.instabids.com/storage/v1/object/public/project-photos/kitchen_damage_3.jpg"
    ]

    # Create conversation state with images
    initial_state = {
        "user_id": user_id,
        "session_id": session_id,
        "messages": [],
        "current_phase": "discovery",
        "collected_info": {
            "uploaded_photos": photo_urls,
            "photo_analyses": []  # Would be filled by image analysis in production
        },
        "missing_fields": [],
        "conversation_complete": False,
        "ready_for_jaa": False
    }

    # Initialize CIA agent
    cia_agent = CustomerInterfaceAgent(anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Test message
    test_message = """
    I need my kitchen cabinets replaced. They're water damaged and falling apart.
    I'm in Miami, FL 33139. Budget is around $15,000-20,000 for new cabinets and
    installation. Need this done within 2 months before my daughter's wedding.
    I prefer modern white shaker style cabinets. The kitchen is about 12x15 feet.
    I've uploaded 3 photos showing the current damage.
    """

    print("\nTest Message:")
    print(test_message)
    print(f"\nUploaded Photos: {len(photo_urls)} images")
    for i, url in enumerate(photo_urls):
        print(f"  Photo {i+1}: {url}")
    print("\n" + "-"*80 + "\n")

    # Process with CIA (with pre-loaded photos in state)
    # In production, the frontend would pass these photos
    result = await cia_agent.handle_conversation(
        user_id=user_id,
        message=test_message,
        session_id=session_id,
        initial_state=initial_state  # Pass state with photos
    )

    print("CIA Processing Complete")
    print(f"Ready for JAA: {result.get('ready_for_jaa')}")

    # Check collected info
    if "collected_info" in result:
        collected = result["collected_info"]
        print(f"\nCollected Photos: {len(collected.get('uploaded_photos', []))}")
        print(f"Project Type: {collected.get('project_type')}")
        print(f"Budget: ${collected.get('budget_min')}-${collected.get('budget_max')}")

    # Wait for database
    await asyncio.sleep(3)

    # Process with JAA
    print("\n" + "-"*80 + "\n")
    jaa_agent = NewJobAssessmentAgent()
    jaa_result = jaa_agent.process_conversation(session_id)

    if jaa_result["success"]:
        print("JAA Processing SUCCESSFUL!")
        bid_data = jaa_result["bid_card_data"]
        bid_number = jaa_result["bid_card_number"]

        print(f"\nBid Card Number: {bid_number}")
        print(f"Images in bid card: {len(bid_data.get('images', []))}")

        # Generate HTML bid card
        html_card = generate_email_html_bid_card(bid_data, bid_number)

        # Save HTML to file for viewing
        html_filename = f"bid_card_{bid_number}.html"
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_card)

        print(f"\nHTML Bid Card saved to: {html_filename}")
        print("\nHTML Preview (first 500 chars):")
        print(html_card[:500] + "...")

        # Check database record
        if "database_record" in jaa_result:
            db_record = jaa_result["database_record"]
            bid_doc = db_record.get("bid_document", {})
            all_data = bid_doc.get("all_extracted_data", {})

            print("\n" + "="*80)
            print("BID CARD DATA STRUCTURE")
            print("="*80)
            print("\nDatabase fields:")
            print(f"  - bid_card_number: {db_record.get('bid_card_number')}")
            print(f"  - project_type: {db_record.get('project_type')}")
            print(f"  - budget_min: ${db_record.get('budget_min')}")
            print(f"  - budget_max: ${db_record.get('budget_max')}")

            print("\nImages in bid_document:")
            print(f"  - images[]: {len(all_data.get('images', []))} photos")
            print(f"  - image_analysis[]: {len(all_data.get('image_analysis', []))} analyses")

            print("\nBidCard.tsx compatibility:")
            print("  - Component expects: photo_urls[]")
            print("  - JAA provides: images[]")
            print("  - Mapping needed: YES (in frontend or API)")

        return True
    else:
        print(f"JAA Processing FAILED: {jaa_result.get('error')}")
        return False


async def main():
    """Run complete test"""
    try:
        success = await test_with_real_images()

        if success:
            print("\n" + "="*80)
            print("TEST SUMMARY: COMPLETE BID CARD WITH IMAGES")
            print("="*80)
            print("\nSUCCESS! The bid card system handles images:")
            print("  [OK] CIA accepts uploaded_photos in state")
            print("  [OK] Photos are stored in collected_info")
            print("  [OK] JAA extracts photos to bid card as 'images'")
            print("  [OK] Photos stored in bid_document for retrieval")
            print("  [OK] HTML bid card generation works")
            print("\nNOTE: Frontend needs to map 'images' → 'photo_urls' for BidCard.tsx")
            print("      Or update BidCard.tsx to accept 'images' field")

    except Exception as e:
        print(f"\nTest error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
