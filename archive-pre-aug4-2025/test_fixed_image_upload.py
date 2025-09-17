#!/usr/bin/env python3
"""
Test the fixed image upload functionality
"""

import asyncio
import base64
import os

from dotenv import load_dotenv

from agents.cia.agent import CustomerInterfaceAgent


# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Test user credentials
TEST_USER_ID = "e6e47a24-95ad-4af3-9ec5-f17999917bc3"

def encode_image(image_path):
    """Encode image to base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

async def test_image_upload_with_storage():
    """Test that images are uploaded to storage instead of sent as base64"""
    print("\n" + "="*50)
    print("TEST: Image Upload to Storage")
    print("="*50)

    cia = CustomerInterfaceAgent(anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Load a single kitchen image
    kitchen_image = encode_image(r"C:\Users\Not John Or Justin\Documents\instabids\test-images\current-state\kitchen-outdated-1.webp")

    # Send with image
    result = await cia.handle_conversation(
        user_id=TEST_USER_ID,
        message="I need a kitchen remodel. Here's a photo of my current kitchen. Budget is around $30,000.",
        images=[kitchen_image],
        session_id="test_storage_upload"
    )

    print(f"\nAgent Response: {result['response']}")

    # Check if images were stored as URLs
    if "state" in result and "collected_info" in result["state"]:
        photos = result["state"]["collected_info"].get("uploaded_photos", [])
        if photos:
            print("\n✅ SUCCESS: Images uploaded to storage!")
            print(f"Number of URLs: {len(photos)}")
            for idx, url in enumerate(photos):
                print(f"URL {idx+1}: {url}")
                # Check if it's a proper Supabase storage URL
                if "supabase.co/storage" in url:
                    print("✅ Valid Supabase storage URL")
                else:
                    print("❌ Not a Supabase storage URL")
        else:
            print("\n❌ FAIL: No photos found in collected_info")

    return result

async def test_bid_card_modification():
    """Test modifying an existing kitchen bid card"""
    print("\n" + "="*50)
    print("TEST: Bid Card Modification")
    print("="*50)

    cia = CustomerInterfaceAgent(anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Try to modify kitchen budget
    result = await cia.handle_conversation(
        user_id=TEST_USER_ID,
        message="I want to update my kitchen remodel budget to $40,000-50,000. The original quote was too low for what I want.",
        session_id="test_modify_kitchen_fixed"
    )

    print(f"\nAgent Response: {result['response']}")

    # Check if modification was successful
    if "modification" in result["response"].lower() or "updated" in result["response"].lower():
        print("\n✅ Agent recognized modification request")
    else:
        print("\n❌ Agent did not recognize modification request")

    return result

async def main():
    """Run all tests"""
    print("Testing Fixed Image Upload and Bid Card Modifications")
    print("User: test.homeowner@instabids.com")

    # Test 1: Image upload to storage
    await test_image_upload_with_storage()

    await asyncio.sleep(2)

    # Test 2: Bid card modification
    await test_bid_card_modification()

    print("\n" + "="*50)
    print("Tests completed!")
    print("Check Supabase Storage for uploaded images")
    print("Check bid cards table for updated budgets")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
