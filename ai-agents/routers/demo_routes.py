"""
Demo Routes - Demo and Test Pages
Owner: Shared (All agents can use for testing)
"""

import os
import sys

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse


# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database_simple import db
    print("[DEMO_ROUTES] Database connection initialized")
except Exception as e:
    print(f"[DEMO_ROUTES] Database import error: {e}")
    db = None

# Create router
router = APIRouter()

@router.get("/demo/wfa-rich-preview", response_class=HTMLResponse)
async def get_wfa_demo():
    """WFA Demo page showing form filling with rich preview links"""
    try:
        demo_path = os.path.join(os.path.dirname(__file__), "..", "templates", "demo_page.html")
        with open(demo_path, encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Demo page not found</h1>", status_code=404)

@router.get("/test/real-preview", response_class=HTMLResponse)
async def get_real_preview_test():
    """Real inline preview test page with JavaScript"""
    try:
        test_path = os.path.join(os.path.dirname(__file__), "..", "test_real_preview.html")
        with open(test_path, encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Test page not found</h1>", status_code=404)

# Inspiration Demo Endpoints
@router.get("/api/demo/inspiration/boards")
async def get_demo_boards(user_id: str = Query(...)):
    """Get demo inspiration boards for a homeowner - checks real data first, then demo data"""
    boards = []

    # First try to get real boards from database
    if db:
        try:
            result = db.client.table("inspiration_boards").select("*").eq("user_id", user_id).execute()
            if result.data:
                print(f"[DEMO_ROUTES] Found {len(result.data)} real boards for homeowner {user_id}")
                boards.extend(result.data)
        except Exception as e:
            print(f"[DEMO_ROUTES] Error getting real boards: {e}")

    # If no real boards found, add demo board
    if not boards:
        print(f"[DEMO_ROUTES] No real boards found, returning demo board for homeowner {user_id}")
        boards = [
            {
                "id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
                "title": "My Dream Kitchen Transformation",
                "description": "Transform my compact kitchen into a modern industrial space",
                "room_type": "kitchen",
                "user_id": user_id,
                "status": "organizing",
                "created_at": "2025-07-31T16:25:18.134Z",
                "updated_at": "2025-07-31T16:25:18.134Z",
                "image_count": 3
            }
        ]

    return boards

@router.get("/api/demo/inspiration/images")
async def get_demo_images(board_id: str = Query(...)):
    """Get demo inspiration images for a board - loads real database images"""
    images = []

    # First try to get real images from database
    if db:
        try:
            result = db.client.table("inspiration_images").select("*").eq("board_id", board_id).execute()
            if result.data:
                print(f"[DEMO_ROUTES] Found {len(result.data)} real images for board {board_id}")
                images.extend(result.data)
            else:
                print(f"[DEMO_ROUTES] No real images found for board {board_id}")
        except Exception as e:
            print(f"[DEMO_ROUTES] Error getting real images: {e}")

    # If no real images found, return demo images for the default board
    if not images and board_id == "26cf972b-83e4-484c-98b6-a5d1a4affee3":
        print(f"[DEMO_ROUTES] Returning hardcoded demo images for board {board_id}")
        return [
            {
                "id": "demo-current-1",
                "board_id": board_id,
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "image_url": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400",
                "thumbnail_url": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=200",
                "source": "url",
                "tags": ["kitchen", "current", "compact", "needs-update"],
                "ai_analysis": {
                    "description": "Compact kitchen with white cabinets and limited counter space",
                    "style": "Traditional builder-grade"
                },
                "user_notes": "My current kitchen - needs modernization",
                "category": "current",
                "position": 0,
                "created_at": "2025-07-31T16:25:18.134Z"
            },
            {
                "id": "demo-inspiration-1",
                "board_id": board_id,
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "image_url": "https://images.unsplash.com/photo-1565182999561-18d7dc61c393?w=400",
                "thumbnail_url": "https://images.unsplash.com/photo-1565182999561-18d7dc61c393?w=200",
                "source": "url",
                "tags": ["kitchen", "inspiration", "modern", "industrial"],
                "ai_analysis": {
                    "description": "Modern industrial kitchen with exposed elements",
                    "style": "Modern Industrial"
                },
                "user_notes": "Love the industrial styling!",
                "category": "ideal",
                "position": 1,
                "created_at": "2025-07-31T16:25:18.134Z"
            }
        ]

    return images
