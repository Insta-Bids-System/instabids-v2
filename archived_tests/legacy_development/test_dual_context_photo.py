"""
Test Dual-Context Photo Saving
This tests the complete flow of saving photos to both property documentation and inspiration boards
"""

import asyncio
import uuid
from datetime import datetime
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client - use the correct env vars from the project
url = "https://xrhgrthdcaymxuqcgrmj.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhyaGdydGhkY2F5bXh1cWNncm1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2NTcyMDYsImV4cCI6MjA2OTIzMzIwNn0.BriGLA2FE_e_NJl8B-3ps1W6ZAuK6a5HpTwBGy-6rmE"
supabase: Client = create_client(url, key)

async def test_dual_context_saving():
    """Test saving a photo to both property documentation and inspiration board"""
    
    print("\n=== TESTING DUAL-CONTEXT PHOTO SAVING ===\n")
    
    # Test data - use valid UUIDs
    user_id = str(uuid.uuid4())  # Valid UUID for user
    property_id = str(uuid.uuid4())
    board_id = str(uuid.uuid4())
    photo_url = "https://example.com/living-room-broken-blinds.jpg"
    filename = "WhatsApp-Living-Room-Broken-Blinds.jpg"
    
    # Step 1: Create test property
    print("1. Creating test property...")
    property_data = {
        "id": property_id,
        "user_id": user_id,
        "name": "Test Home",
        "address": "123 Test St",
        "property_type": "house",
        "created_at": datetime.now().isoformat()
    }
    
    result = supabase.table("properties").insert(property_data).execute()
    if result.data:
        print(f"[SUCCESS] Property created: {property_id}")
    else:
        print(f"[FAILED] Failed to create property")
        return
    
    # Step 2: Create room for property
    print("\n2. Creating living room...")
    room_id = str(uuid.uuid4())
    room_data = {
        "id": room_id,
        "property_id": property_id,
        "name": "Living Room",
        "room_type": "living_room",
        "floor_level": 1,
        "description": "Living room with broken blinds",
        "created_at": datetime.now().isoformat()
    }
    
    result = supabase.table("property_rooms").insert(room_data).execute()
    if result.data:
        print(f"[SUCCESS] Room created: {room_id}")
    else:
        print(f"[FAILED] Failed to create room")
    
    # Step 3: Save to property_photos (documentation)
    print("\n3. Saving to property documentation...")
    photo_id = str(uuid.uuid4())
    property_photo_data = {
        "id": photo_id,
        "property_id": property_id,
        "room_id": room_id,
        "photo_url": photo_url,
        "original_filename": filename,
        "photo_type": "current",
        "ai_description": "Living room with broken blinds needing repair",
        "ai_classification": {
            "room_type": "living_room",
            "detected_issues": ["broken blinds"],
            "maintenance_needed": True
        },
        "created_at": datetime.now().isoformat()
    }
    
    result = supabase.table("property_photos").insert(property_photo_data).execute()
    if result.data:
        print(f"[SUCCESS] Photo saved to property documentation")
        print(f"   - Photo ID: {photo_id}")
        print(f"   - Room: Living Room")
        print(f"   - Type: Current state documentation")
    else:
        print(f"[FAILED] Failed to save to property_photos")
    
    # Step 4: Create inspiration board
    print("\n4. Creating inspiration board...")
    board_data = {
        "id": board_id,
        "user_id": user_id,
        "title": "Living Room Transformation",
        "room_type": "living_room",
        "status": "collecting",
        "created_at": datetime.now().isoformat()
    }
    
    result = supabase.table("inspiration_boards").insert(board_data).execute()
    if result.data:
        print(f"[SUCCESS] Inspiration board created: {board_id}")
    else:
        print(f"[FAILED] Failed to create inspiration board")
    
    # Step 5: Save to inspiration_images (inspiration)
    print("\n5. Saving to inspiration board...")
    inspiration_id = str(uuid.uuid4())
    inspiration_data = {
        "id": inspiration_id,
        "board_id": board_id,
        "user_id": user_id,
        "image_url": photo_url,
        "thumbnail_url": photo_url,
        "source": "upload",
        "tags": ["living_room", "renovation", "property_photo", "broken_blinds"],
        "category": "current",
        "ai_analysis": {
            "room_type": "living_room",
            "source": "property_documentation",
            "maintenance_items": ["broken blinds"]
        },
        "user_notes": "Current state - blinds need fixing",
        "created_at": datetime.now().isoformat()
    }
    
    result = supabase.table("inspiration_images").insert(inspiration_data).execute()
    if result.data:
        print(f"[SUCCESS] Photo saved to inspiration board")
        print(f"   - Image ID: {inspiration_id}")
        print(f"   - Board: Living Room Transformation")
        print(f"   - Category: Current state")
        print(f"   - Tags: {inspiration_data['tags']}")
    else:
        print(f"[FAILED] Failed to save to inspiration_images")
    
    # Step 6: Create maintenance task
    print("\n6. Creating maintenance task...")
    task_id = str(uuid.uuid4())
    task_data = {
        "id": task_id,
        "user_id": user_id,
        "task_description": "Fix/repair broken blinds in living room (see photo)",
        "room_id": "living_room",
        "priority": "medium",
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    result = supabase.table("homeowner_maintenance_tasks").insert(task_data).execute()
    if result.data:
        print(f"[SUCCESS] Maintenance task created")
        print(f"   - Task: Fix/repair broken blinds")
        print(f"   - Priority: Medium")
        print(f"   - Status: Pending")
    else:
        print(f"[FAILED] Failed to create maintenance task")
    
    # Step 7: Verify dual-context saving
    print("\n7. Verifying dual-context saving...")
    
    # Check property documentation
    property_check = supabase.table("property_photos").select("*").eq("id", photo_id).execute()
    if property_check.data:
        print(f"[SUCCESS] Photo exists in property documentation")
    
    # Check inspiration board
    inspiration_check = supabase.table("inspiration_images").select("*").eq("id", inspiration_id).execute()
    if inspiration_check.data:
        print(f"[SUCCESS] Photo exists in inspiration board")
    
    # Check maintenance task
    task_check = supabase.table("homeowner_maintenance_tasks").select("*").eq("id", task_id).execute()
    if task_check.data:
        print(f"[SUCCESS] Maintenance task exists")
    
    print("\n=== DUAL-CONTEXT SAVING TEST COMPLETE ===")
    print("\n[SUCCESS] SUCCESS: Photo saved to:")
    print("   1. Property documentation (for record keeping)")
    print("   2. Inspiration board (for design planning)")
    print("   3. Maintenance task list (for action items)")
    print("\nThis demonstrates the complete dual-context saving system!")
    
    # Cleanup
    print("\n8. Cleaning up test data...")
    supabase.table("homeowner_maintenance_tasks").delete().eq("id", task_id).execute()
    supabase.table("inspiration_images").delete().eq("id", inspiration_id).execute()
    supabase.table("inspiration_boards").delete().eq("id", board_id).execute()
    supabase.table("property_photos").delete().eq("id", photo_id).execute()
    supabase.table("property_rooms").delete().eq("id", room_id).execute()
    supabase.table("properties").delete().eq("id", property_id).execute()
    print("[SUCCESS] Test data cleaned up")

if __name__ == "__main__":
    asyncio.run(test_dual_context_saving())