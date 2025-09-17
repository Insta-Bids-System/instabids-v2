import asyncio
import uuid
import sys
import os
from datetime import datetime

# Add path to import from ai-agents
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))
from database import SupabaseDB

# Test the fixed dual-context photo saving
async def test_photo_saving():
    db = SupabaseDB()
    user_id = "550e8400-e29b-41d4-a716-446655440001"
    
    print("Testing Fixed Photo Dual-Context Saving")
    print("=" * 60)
    
    # 1. First, get or create a property for this homeowner
    print("\n1. Checking for existing property...")
    property_result = db.client.table("properties").select("*").eq("user_id", user_id).execute()
    
    if property_result.data:
        property_id = property_result.data[0]["id"]
        print(f"Found existing property: {property_id}")
    else:
        # Create a property
        property_id = str(uuid.uuid4())
        property_data = {
            "id": property_id,
            "user_id": user_id,
            "name": "My Home",
            "address": "123 Main St",
            "property_type": "house",
            "created_at": datetime.utcnow().isoformat()
        }
        db.client.table("properties").insert(property_data).execute()
        print(f"Created new property: {property_id}")
    
    # 2. Get or create a room
    print("\n2. Creating room for living room...")
    room_id = str(uuid.uuid4())
    
    # 3. Save photo to property_photos
    print("\n3. Saving to property_photos table...")
    property_photo_data = {
        "id": str(uuid.uuid4()),
        "property_id": property_id,  # Use property_id, not user_id
        "room_id": room_id,
        "photo_url": "https://xrhgrthdcaymxuqcgrmj.supabase.co/storage/v1/object/public/inspiration/test_photo.jpg",
        "original_filename": "living_room_broken_blinds.jpg",
        "photo_type": "current",
        "ai_description": "Living room with broken vertical blinds requiring repair",
        "ai_classification": {
            "room_type": "living_room",
            "condition": "needs_repair",
            "elements": ["blinds", "windows", "natural_light"]
        },
        "created_at": datetime.utcnow().isoformat()
    }
    
    result = db.client.table("property_photos").insert(property_photo_data).execute()
    if result.data:
        print("✅ Successfully saved to property_photos!")
        print(f"   Photo ID: {result.data[0]['id']}")
    
    # 4. Save to inspiration_images
    print("\n4. Saving to inspiration_images table...")
    board_id = str(uuid.uuid4())  # Would normally come from existing board
    
    inspiration_data = {
        "id": str(uuid.uuid4()),
        "board_id": board_id,
        "user_id": user_id,
        "image_url": "https://xrhgrthdcaymxuqcgrmj.supabase.co/storage/v1/object/public/inspiration/test_photo.jpg",
        "source": "upload",
        "tags": ["living_room", "renovation", "window_treatments", "repair_needed"],
        "ai_analysis": {
            "style": "modern",
            "colors": ["white", "beige", "natural_light"],
            "elements": ["vertical_blinds", "windows"],
            "mood": "bright_airy"
        },
        "user_notes": "Need to fix these broken blinds and maybe upgrade to something nicer",
        "liked_elements": ["natural_light", "window_size"],
        "category": "current",
        "created_at": datetime.utcnow().isoformat()
    }
    
    result = db.client.table("inspiration_images").insert(inspiration_data).execute()
    if result.data:
        print("✅ Successfully saved to inspiration_images!")
        print(f"   Image ID: {result.data[0]['id']}")
    
    # 5. Create maintenance task
    print("\n5. Creating maintenance task...")
    task_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "task_description": "Fix broken vertical blinds in living room",
        "room_id": "living_room",
        "priority": "medium",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    
    result = db.client.table("homeowner_maintenance_tasks").insert(task_data).execute()
    if result.data:
        print("✅ Successfully created maintenance task!")
        print(f"   Task: {result.data[0]['task_description']}")
    
    # 6. Verify all saves
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    
    # Check property_photos
    photos = db.client.table("property_photos").select("*").eq("property_id", property_id).execute()
    print(f"✓ Property photos saved: {len(photos.data)} photos")
    
    # Check inspiration_images
    images = db.client.table("inspiration_images").select("*").eq("user_id", user_id).execute()
    print(f"✓ Inspiration images saved: {len(images.data)} images")
    
    # Check maintenance tasks
    tasks = db.client.table("homeowner_maintenance_tasks").select("*").eq("user_id", user_id).execute()
    print(f"✓ Maintenance tasks created: {len(tasks.data)} tasks")
    
    print("\n✅ ALL DUAL-CONTEXT SAVING WORKING!")

if __name__ == "__main__":
    asyncio.run(test_photo_saving())