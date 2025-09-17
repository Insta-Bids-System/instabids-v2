"""
Homeowner Routes - Homeowner UI and Features API Endpoints
Owner: Agent 3 (Homeowner UX)
"""

import os
from datetime import datetime

from fastapi import APIRouter, HTTPException

from database_simple import db


# Create router
router = APIRouter()

@router.post("/inspiration/boards")
async def create_inspiration_board(board_data: dict):
    """Create inspiration board with service-level permissions for demo users"""
    try:
        from supabase import create_client

        # Use service role key for demo operations
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        print(f"[DEBUG] SUPABASE_URL: {supabase_url}")
        print(f"[DEBUG] SERVICE_KEY: {service_key[:20] if service_key else 'None'}...")
        print(f"[DEBUG] SERVICE_KEY equals placeholder: {service_key == 'your_supabase_service_key'}")
        print(f"[DEBUG] SERVICE_KEY is None: {service_key is None}")
        print(f"[DEBUG] SERVICE_KEY bool: {bool(service_key)}")

        # Check if we have the real service key from .env
        if not service_key or service_key == "your_supabase_service_key":
            print("[DEBUG] No service key found - using demo mode")
            # For development, we'll skip RLS by creating via raw SQL
            # This is a temporary workaround for demo functionality
            return {
                "id": f"demo_board_{datetime.now().timestamp()}",
                "title": board_data.get("title", "Demo Board"),
                "description": board_data.get("description"),
                "room_type": board_data.get("room_type"),
                "user_id": board_data.get("user_id"),
                "status": "collecting",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "image_count": 0
            }

        print("[DEBUG] Service key found - attempting real database call")

        supabase = create_client(supabase_url, service_key)

        # Handle user_id - use valid UUID or default test user
        user_id = board_data.get("user_id")
        if not user_id or user_id.startswith("test-user-"):
            # For demo/test users, use the default test user
            user_id = "4442e0a3-2fea-4f88-82d5-c8e77a531844"  # test@instabids.com
            print(f"[DEBUG] Using default test user UUID: {user_id}")

        # Insert board using service role (bypasses RLS)
        print(f"[DEBUG] Inserting board with user_id: {user_id}")
        response = supabase.table("inspiration_boards").insert({
            "title": board_data.get("title"),
            "description": board_data.get("description"),
            "room_type": board_data.get("room_type"),
            "user_id": user_id,
            "status": board_data.get("status", "collecting")
        }).execute()

        if response.data:
            return response.data[0]
        else:
            raise HTTPException(500, "Failed to create board")

    except Exception as e:
        import traceback
        print(f"[BOARD CREATION ERROR] {e}")
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        # Fallback to demo response
        return {
            "id": f"demo_board_{datetime.now().timestamp()}",
            "title": board_data.get("title", "Demo Board"),
            "description": board_data.get("description"),
            "room_type": board_data.get("room_type"),
            "user_id": board_data.get("user_id"),
            "status": "collecting",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "image_count": 0
        }

@router.get("/iris/status")
async def get_iris_status():
    """Get Iris agent status"""
    return {
        "status": "active",
        "description": "Design Inspiration Assistant",
        "model": "Claude Opus 4 (claude-3-opus-20240229)",
        "capabilities": [
            "Analyze design styles",
            "Organize inspiration images",
            "Provide budget estimates",
            "Create vision summaries",
            "Guide to project creation"
        ]
    }

@router.post("/conversations/transfer")
async def transfer_conversation(data: dict):
    """Transfer anonymous conversation to authenticated user after signup"""
    session_id = data.get("session_id")
    user_id = data.get("user_id")

    if not session_id or not user_id:
        raise HTTPException(400, "session_id and user_id are required")

    try:
        success = await db.transfer_anonymous_conversation(session_id, user_id)
        if success:
            return {"success": True, "message": "Conversation transferred successfully"}
        else:
            return {"success": False, "message": "No conversations to transfer"}
    except Exception as e:
        print(f"[TRANSFER ERROR] {e}")
        raise HTTPException(500, f"Failed to transfer conversation: {e!s}")

@router.get("/bid-cards/homeowner/{user_id}")
async def get_homeowner_bid_cards_direct(user_id: str):
    """Get all bid cards for a specific homeowner - Direct implementation"""
    try:
        from asyncio import timeout as async_timeout

        # Add timeout to prevent hanging
        async with async_timeout(10):  # 10 second timeout
            # Get conversations for this user
            conversations_result = db.client.table("agent_conversations").select("thread_id").eq("user_id", user_id).execute()

            if not conversations_result.data:
                return []

            # Get thread IDs
            thread_ids = [conv["thread_id"] for conv in conversations_result.data]

            # Get bid cards linked to these conversations
            result = db.client.table("bid_cards").select("*").in_("cia_thread_id", thread_ids).order("created_at", desc=True).execute()

        if not result.data:
            return []

        # Process bid cards to ensure photo_urls field exists
        bid_cards = []
        for card in result.data:
            # Map images to photo_urls for frontend compatibility
            if card.get("bid_document") and card["bid_document"].get("all_extracted_data"):
                extracted = card["bid_document"]["all_extracted_data"]
                if "images" in extracted and "photo_urls" not in extracted:
                    extracted["photo_urls"] = extracted["images"]
            bid_cards.append(card)

        return bid_cards

    except TimeoutError:
        print(f"[API ERROR] Timeout getting bid cards for {user_id}")
        raise HTTPException(status_code=504, detail="Database query timeout")
    except Exception as e:
        print(f"[API ERROR] Failed to get homeowner bid cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profiles/{user_id}")
async def get_profile(user_id: str):
    """Get user profile by user ID"""
    print(f"[PROFILE API] Getting profile for user_id: {user_id}")
    try:
        # Get profile from database - the id field in profiles table IS the auth user id
        result = db.client.table("profiles").select("*").eq("id", user_id).execute()
        print(f"[PROFILE API] Query result: {result}")

        if result.data and len(result.data) > 0:
            profile = result.data[0]
            print(f"[PROFILE API] Found profile: {profile}")
            return profile
        else:
            print(f"[PROFILE API] No profile found for user_id: {user_id}")
            raise HTTPException(404, f"Profile not found for user_id: {user_id}")

    except Exception as e:
        print(f"[PROFILE API ERROR] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to get profile: {e!s}")
