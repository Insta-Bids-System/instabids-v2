"""
Inspiration Boards API - Handle inspiration board CRUD operations
"""

import os
import uuid
from datetime import datetime
from typing import Optional

# Load environment
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import Client, create_client


# Load from the instabids root directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

router = APIRouter()

# Initialize Supabase with service role key for RLS bypass
supabase_url = "https://xrhgrthdcaymxuqcgrmj.supabase.co"
supabase_service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhyaGdydGhkY2F5bXh1cWNncm1qIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzY1NzIwNiwiZXhwIjoyMDY5MjMzMjA2fQ.BH3hCDZUqUvCF0RL_50KXrNHWH7aWaZQKTqCTxLm8AI"
supabase: Client = create_client(supabase_url, supabase_service_key)

class InspirationBoardCreate(BaseModel):
    title: str
    description: Optional[str] = None
    room_type: Optional[str] = None
    user_id: str
    status: str = "collecting"
    is_demo: bool = False

class InspirationBoardResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    room_type: Optional[str]
    user_id: str
    status: str
    created_at: str
    updated_at: str
    image_count: int = 0

@router.get("/api/inspiration/boards", response_model=list[InspirationBoardResponse])
async def get_inspiration_boards(user_id: str):
    """
    Get all inspiration boards for a homeowner
    """
    try:
        # Get boards with image count
        result = supabase.table("inspiration_boards").select("""
            *,
            inspiration_images(count)
        """).eq("user_id", user_id).order("created_at", desc=True).execute()

        if result.data is None:
            return []

        # Transform the data to include image count
        boards = []
        for board in result.data:
            image_count = 0
            if board.get("inspiration_images") and isinstance(board["inspiration_images"], list):
                if len(board["inspiration_images"]) > 0 and "count" in board["inspiration_images"][0]:
                    image_count = board["inspiration_images"][0]["count"]

            boards.append(InspirationBoardResponse(
                id=board["id"],
                title=board["title"],
                description=board.get("description"),
                room_type=board.get("room_type"),
                user_id=board["user_id"],
                status=board["status"],
                created_at=board["created_at"],
                updated_at=board["updated_at"],
                image_count=image_count
            ))

        return boards

    except Exception as e:
        print(f"Error loading boards: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/inspiration/boards", response_model=InspirationBoardResponse)
async def create_inspiration_board(board_data: InspirationBoardCreate):
    """
    Create a new inspiration board
    """
    try:
        # Create board data
        board_id = f"demo_board_{datetime.now().timestamp()}" if board_data.is_demo else str(uuid.uuid4())

        new_board = {
            "id": board_id,
            "user_id": board_data.user_id,
            "title": board_data.title,
            "description": board_data.description,
            "room_type": board_data.room_type,
            "status": board_data.status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Insert into database
        result = supabase.table("inspiration_boards").insert(new_board).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create board")

        created_board = result.data[0]

        return InspirationBoardResponse(
            id=created_board["id"],
            title=created_board["title"],
            description=created_board.get("description"),
            room_type=created_board.get("room_type"),
            user_id=created_board["user_id"],
            status=created_board["status"],
            created_at=created_board["created_at"],
            updated_at=created_board["updated_at"],
            image_count=0
        )

    except Exception as e:
        print(f"Error creating board: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/inspiration/boards/{board_id}", response_model=InspirationBoardResponse)
async def get_inspiration_board(board_id: str):
    """
    Get a specific inspiration board
    """
    try:
        result = supabase.table("inspiration_boards").select("""
            *,
            inspiration_images(count)
        """).eq("id", board_id).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Board not found")

        board = result.data
        image_count = 0
        if board.get("inspiration_images") and isinstance(board["inspiration_images"], list):
            if len(board["inspiration_images"]) > 0 and "count" in board["inspiration_images"][0]:
                image_count = board["inspiration_images"][0]["count"]

        return InspirationBoardResponse(
            id=board["id"],
            title=board["title"],
            description=board.get("description"),
            room_type=board.get("room_type"),
            user_id=board["user_id"],
            status=board["status"],
            created_at=board["created_at"],
            updated_at=board["updated_at"],
            image_count=image_count
        )

    except Exception as e:
        print(f"Error getting board: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))
