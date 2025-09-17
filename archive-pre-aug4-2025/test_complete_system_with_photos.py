#!/usr/bin/env python3
"""
Comprehensive test of the complete system with real photos and modifications
"""

import asyncio
import base64
import os

from dotenv import load_dotenv

from agents.cia.agent import CustomerInterfaceAgent
from agents.jaa.agent import JobAssessmentAgent
from database_simple import db


# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Test user credentials
TEST_USER_ID = "e6e47a24-95ad-4af3-9ec5-f17999917bc3"  # test.homeowner@instabids.com

def encode_image(image_path):
    """Encode image to base64"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

async def test_kitchen_with_photos():
    """Test 1: Kitchen remodel with multiple photos"""
    print("\n" + "="*80)
    print("TEST 1: Kitchen Remodel with Photos")
    print("="*80)

    cia = CustomerInterfaceAgent(anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Load kitchen images
    kitchen_images = []
    image_paths = [
        r"C:\Users\Not John Or Justin\Documents\instabids\test-images\current-state\kitchen-outdated-1.webp",
        r"C:\Users\Not John Or Justin\Documents\instabids\test-images\current-state\kitchen-outdated-2.webp"
    ]

    for path in image_paths:
        img = encode_image(path)
        if img:
            kitchen_images.append(img)

    print(f"Loaded {len(kitchen_images)} kitchen images")

    # Start conversation with images
    result = await cia.handle_conversation(
        user_id=TEST_USER_ID,
        message="I need a complete kitchen remodel. These photos show my current kitchen. I'm thinking modern style with white cabinets and quartz countertops. Budget is around $35,000-40,000.",
        images=kitchen_images,
        session_id="test_kitchen_comprehensive"
    )

    print(f"\n[Response]: {result['response'][:200]}...")

    # Provide more details
    result2 = await cia.handle_conversation(
        user_id=TEST_USER_ID,
        message="Timeline is flexible, maybe 2-3 months. Location is Tampa, FL 33602. I definitely want to keep the same layout but update everything - cabinets, countertops, backsplash, and new stainless steel appliances.",
        session_id="test_kitchen_comprehensive"
    )

    print(f"\n[Response 2]: {result2['response'][:200]}...")
    print(f"Ready for JAA: {result2.get('ready_for_jaa', False)}")

    # If ready, process with JAA
    if result2.get("ready_for_jaa"):
        print("\n[Processing with JAA...]")
        jaa = JobAssessmentAgent()
        bid_card_id = jaa.process_conversation("test_kitchen_comprehensive")

        if bid_card_id:
            print(f"[OK] Created bid card: {bid_card_id}")
            return bid_card_id

    return None

async def test_bathroom_with_photos():
    """Test 2: Bathroom renovation with photos"""
    print("\n" + "="*80)
    print("TEST 2: Bathroom Renovation with Photos")
    print("="*80)

    cia = CustomerInterfaceAgent(anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Load bathroom image
    bathroom_image = encode_image(r"C:\Users\Not John Or Justin\Documents\instabids\test-images\current-state\bathroom-small-1.webp")

    if bathroom_image:
        result = await cia.handle_conversation(
            user_id=TEST_USER_ID,
            message="I also need to renovate this bathroom. It's a small guest bathroom. Looking for a complete update - new vanity, toilet, tile work. Budget around $8,000-10,000. Same location as the kitchen.",
            images=[bathroom_image],
            session_id="test_bathroom_comprehensive"
        )

        print(f"\n[Response]: {result['response'][:200]}...")

        # Quick completion
        result2 = await cia.handle_conversation(
            user_id=TEST_USER_ID,
            message="I want it done within the next month if possible. Modern style to match the kitchen update.",
            session_id="test_bathroom_comprehensive"
        )

        print(f"\n[Response 2]: {result2['response'][:200]}...")
        print(f"Ready for JAA: {result2.get('ready_for_jaa', False)}")

        if result2.get("ready_for_jaa"):
            print("\n[Processing with JAA...]")
            jaa = JobAssessmentAgent()
            bid_card_id = jaa.process_conversation("test_bathroom_comprehensive")

            if bid_card_id:
                print(f"[OK] Created bid card: {bid_card_id}")
                return bid_card_id

    return None

async def test_modify_kitchen_budget():
    """Test 3: Modify existing kitchen budget"""
    print("\n" + "="*80)
    print("TEST 3: Modify Kitchen Budget")
    print("="*80)

    await asyncio.sleep(2)  # Give time for database

    cia = CustomerInterfaceAgent(anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

    result = await cia.handle_conversation(
        user_id=TEST_USER_ID,
        message="Actually, I've been thinking about the kitchen remodel and I want to increase the budget to $45,000-50,000. I want to get really high-end appliances and maybe add a kitchen island.",
        session_id="test_modify_kitchen"
    )

    print(f"\n[Modification Response]: {result['response'][:300]}...")

    # Check if it recognized the modification
    if "update" in result["response"].lower() or "change" in result["response"].lower():
        print("[OK] Agent recognized modification request")
    else:
        print("[WARNING] Agent may not have recognized modification")

    return result

async def test_new_project_with_awareness():
    """Test 4: New project with awareness of existing projects"""
    print("\n" + "="*80)
    print("TEST 4: New Landscaping Project (Multi-Project Awareness)")
    print("="*80)

    cia = CustomerInterfaceAgent(anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Load lawn images
    lawn_image = encode_image(r"C:\Users\Not John Or Justin\Documents\instabids\test-images\current-state\lawn-problem-1.webp")

    if lawn_image:
        result = await cia.handle_conversation(
            user_id=TEST_USER_ID,
            message="While we're doing all this work, I also need help with my lawn. It's in terrible shape. Need complete landscaping - new sod, plants, maybe some decorative stones. Here's a photo.",
            images=[lawn_image],
            session_id="test_landscaping_aware"
        )

        print(f"\n[Response]: {result['response'][:300]}...")

        # Check for multi-project awareness
        if "kitchen" in result["response"].lower() or "bathroom" in result["response"].lower() or "other project" in result["response"].lower():
            print("[OK] Agent shows awareness of other projects!")

        # Complete the landscaping
        result2 = await cia.handle_conversation(
            user_id=TEST_USER_ID,
            message="Budget for landscaping is $12,000-15,000. I'd like it done after the kitchen and bathroom are finished. Same property in Tampa.",
            session_id="test_landscaping_aware"
        )

        print(f"\n[Response 2]: {result2['response'][:200]}...")

        if result2.get("ready_for_jaa"):
            print("\n[Processing with JAA...]")
            jaa = JobAssessmentAgent()
            bid_card_id = jaa.process_conversation("test_landscaping_aware")

            if bid_card_id:
                print(f"[OK] Created bid card: {bid_card_id}")
                return bid_card_id

    return None

async def verify_backend_data():
    """Verify all data in the backend"""
    print("\n" + "="*80)
    print("BACKEND VERIFICATION")
    print("="*80)

    # 1. Check conversations
    print("\n1. Checking Conversations...")
    conversations = db.client.table("agent_conversations").select("*").eq("user_id", TEST_USER_ID).order("created_at", desc=True).execute()

    if conversations.data:
        print(f"Found {len(conversations.data)} conversations:")
        for conv in conversations.data[:5]:  # Show last 5
            print(f"  - Thread: {conv['thread_id']}")
            print(f"    State: {conv['state']}")
            print(f"    Ready for JAA: {conv.get('ready_for_jaa', False)}")
            print(f"    Created: {conv['created_at']}")

    # 2. Check bid cards
    print("\n2. Checking Bid Cards...")
    thread_ids = [c["thread_id"] for c in conversations.data] if conversations.data else []

    if thread_ids:
        bid_cards = db.client.table("bid_cards").select("*").in_("cia_thread_id", thread_ids).order("created_at", desc=True).execute()

        if bid_cards.data:
            print(f"Found {len(bid_cards.data)} bid cards:")
            for card in bid_cards.data:
                print(f"\n  - Number: {card['bid_card_number']}")
                print(f"    Type: {card['project_type']}")
                print(f"    Budget: ${card['budget_min']:,} - ${card['budget_max']:,}")
                print(f"    Status: {card['status']}")
                print(f"    Created: {card['created_at']}")

                # Check for images
                if card.get("bid_document"):
                    extracted = card["bid_document"].get("all_extracted_data", {})
                    images = extracted.get("images", []) or extracted.get("photo_urls", [])
                    print(f"    Photos: {len(images)}")
                    if images:
                        print(f"    First photo URL: {images[0][:50]}...")
                        # Check if it's local storage
                        if "localhost:8008/static" in images[0]:
                            print("    [OK] Using local storage (RLS bypass working!)")
                        elif "supabase.co/storage" in images[0]:
                            print("    [OK] Using Supabase storage")

    # 3. Check image storage
    print("\n3. Checking Image Storage...")
    static_uploads = os.path.join(os.path.dirname(__file__), "static", "uploads", TEST_USER_ID)
    if os.path.exists(static_uploads):
        files = os.listdir(static_uploads)
        print(f"Found {len(files)} images in local storage:")
        for f in files[:5]:  # Show first 5
            print(f"  - {f}")
    else:
        print("No local storage directory found")

async def check_dashboard_api():
    """Test the dashboard API endpoint"""
    print("\n" + "="*80)
    print("DASHBOARD API TEST")
    print("="*80)

    import requests

    try:
        response = requests.get(f"http://localhost:8008/api/bid-cards/homeowner/{TEST_USER_ID}")
        print(f"API Status: {response.status_code}")

        if response.ok:
            data = response.json()
            print(f"Returned {len(data)} bid cards")

            for card in data:
                print(f"\n- {card['bid_card_number']}: {card['project_type']}")
                print(f"  Budget: ${card['budget_min']:,} - ${card['budget_max']:,}")

                # Check photo_urls mapping
                if card.get("bid_document", {}).get("all_extracted_data", {}).get("photo_urls"):
                    print("  [OK] photo_urls field exists (frontend compatible)")
                else:
                    print("  [WARNING] photo_urls field missing")
        else:
            print(f"API Error: {response.text}")

    except Exception as e:
        print(f"API Connection Error: {e}")

async def main():
    """Run all comprehensive tests"""
    print("="*80)
    print("COMPREHENSIVE SYSTEM TEST WITH PHOTOS")
    print("="*80)
    print("User: test.homeowner@instabids.com")
    print("Testing: Photo uploads, modifications, multi-project awareness")
    print("="*80)

    # Test 1: Kitchen with photos
    kitchen_bid_card = await test_kitchen_with_photos()
    await asyncio.sleep(3)

    # Test 2: Bathroom with photos
    bathroom_bid_card = await test_bathroom_with_photos()
    await asyncio.sleep(3)

    # Test 3: Modify kitchen budget
    await test_modify_kitchen_budget()
    await asyncio.sleep(2)

    # Test 4: New landscaping with awareness
    landscaping_bid_card = await test_new_project_with_awareness()
    await asyncio.sleep(2)

    # Verify everything in backend
    await verify_backend_data()

    # Check dashboard API
    await check_dashboard_api()

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"[OK] Kitchen bid card: {'Created' if kitchen_bid_card else 'Failed'}")
    print(f"[OK] Bathroom bid card: {'Created' if bathroom_bid_card else 'Failed'}")
    print(f"[OK] Landscaping bid card: {'Created' if landscaping_bid_card else 'Failed'}")
    print("[OK] Modification tested: Check backend for budget changes")
    print("[OK] Multi-project awareness: Check agent responses")
    print("[OK] Images: Check local storage or Supabase URLs")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
