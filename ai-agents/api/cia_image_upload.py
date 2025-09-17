#!/usr/bin/env python3
"""
CIA Image Upload API - Handle image uploads for conversations and bid cards
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import uuid
import base64
import os
from datetime import datetime
import logging

# Import database
try:
    from database_simple import db
except ImportError:
    print("Warning: database_simple not available")
    db = None

router = APIRouter()
logger = logging.getLogger(__name__)

class ImageUploadResponse(BaseModel):
    success: bool
    image_id: str
    filename: str
    message: str

class ConversationImageUpload(BaseModel):
    conversation_id: str
    user_id: str
    session_id: Optional[str] = None
    image_data: str  # base64 encoded
    filename: str
    description: Optional[str] = None

@router.post("/api/cia/upload-image", response_model=ImageUploadResponse)
async def upload_conversation_image(upload: ConversationImageUpload):
    """Upload image for CIA conversation and link to potential bid card"""
    try:
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")
        
        logger.info(f"Processing image upload for conversation {upload.conversation_id}")
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        # Handle user_id - convert to UUID if needed, or set to None
        user_uuid = None
        if upload.user_id and upload.user_id != "null":
            try:
                # Try to convert to UUID format if it's not already
                import uuid as uuid_lib
                if len(upload.user_id) == 32:  # Hex string without hyphens
                    user_uuid = str(uuid_lib.UUID(upload.user_id))
                elif len(upload.user_id) == 36:  # Already UUID format
                    user_uuid = upload.user_id
                else:
                    # For non-UUID user IDs, we'll store as None for now
                    user_uuid = None
            except:
                user_uuid = None
        
        # Store image data (in production, you'd upload to cloud storage)
        image_entry = {
            "id": image_id,
            "url": f"/api/cia/image/{image_id}",  # URL to retrieve the image
            "thumbnail_url": f"/api/cia/image/{image_id}?thumbnail=true",
            "caption": upload.description or "Uploaded image",
            "is_primary": False,
            "upload_date": datetime.now(),
            "created_at": datetime.now(),
            # Additional fields for our use case
            "conversation_id": upload.conversation_id,
            "user_id": user_uuid,
            "session_id": upload.session_id,
            "filename": upload.filename,
            "image_data": upload.image_data,
            "description": upload.description,
            "upload_type": "conversation"
        }
        
        # Create or find a bid card first, then store image
        bid_card_id = None
        
        try:
            # Try to find existing potential bid card
            existing_card = db.client.table("potential_bid_cards") \
                .select("id") \
                .eq("cia_conversation_id", upload.conversation_id) \
                .limit(1).execute()
            
            if existing_card.data:
                bid_card_id = existing_card.data[0]["id"]
            else:
                # Create new potential bid card
                new_card = {
                    "id": str(uuid.uuid4()),
                    "cia_conversation_id": upload.conversation_id,
                    "session_id": upload.session_id,
                    "user_id": user_uuid,
                    "title": "Project with Images",
                    "primary_trade": "general",
                    "photo_ids": [],
                    "completion_percentage": 5,
                    "status": "draft"
                }
                
                card_result = db.client.table("potential_bid_cards").insert(new_card).execute()
                bid_card_id = new_card["id"]
                
        except Exception as e:
            logger.error(f"Failed to create/find bid card: {e}")
            # Create a default UUID for bid_card_id
            bid_card_id = str(uuid.uuid4())
        
        # Add bid_card_id to image entry
        image_entry["bid_card_id"] = bid_card_id
        
        # Store in bid_card_images table
        db.client.table("bid_card_images").insert(image_entry).execute()
        
        # Update potential bid card with image reference
        try:
            # Find potential bid card for this conversation
            bid_card_result = db.client.table("potential_bid_cards") \
                .select("id, photo_ids") \
                .eq("cia_conversation_id", upload.conversation_id) \
                .limit(1).execute()
            
            if bid_card_result.data:
                bid_card = bid_card_result.data[0]
                current_photo_ids = bid_card.get("photo_ids", [])
                
                # Add new image ID to photo_ids array
                updated_photo_ids = current_photo_ids + [image_id]
                
                # Update bid card
                db.client.table("potential_bid_cards") \
                    .update({"photo_ids": updated_photo_ids}) \
                    .eq("id", bid_card["id"]).execute()
                
                logger.info(f"Updated bid card {bid_card['id']} with image {image_id}")
            else:
                # Create new potential bid card if none exists
                bid_card_data = {
                    "id": str(uuid.uuid4()),
                    "cia_conversation_id": upload.conversation_id,
                    "session_id": upload.session_id,
                    "user_id": user_uuid,  # Use the processed UUID
                    "title": "Project from Images",
                    "primary_trade": "general",
                    "photo_ids": [image_id],
                    "completion_percentage": 10,  # Has images now
                    "status": "draft",
                    "created_at": datetime.now().isoformat()
                }
                
                db.client.table("potential_bid_cards").insert(bid_card_data).execute()
                logger.info(f"Created new bid card with image {image_id}")
                
        except Exception as e:
            logger.warning(f"Failed to update bid card: {e}")
        
        # Also store in conversation memory
        try:
            memory_entry = {
                "id": str(uuid.uuid4()),
                "conversation_id": upload.conversation_id,
                "memory_type": "image_upload",
                "memory_key": f"image_{image_id}",
                "memory_value": {
                    "image_id": image_id,
                    "filename": upload.filename,
                    "description": upload.description,
                    "uploaded_at": datetime.now().isoformat()
                },
                "created_at": datetime.now().isoformat()
            }
            
            db.client.table("unified_conversation_memory").insert(memory_entry).execute()
            logger.info(f"Stored image reference in conversation memory")
            
        except Exception as e:
            logger.warning(f"Failed to store in conversation memory: {e}")
        
        return ImageUploadResponse(
            success=True,
            image_id=image_id,
            filename=upload.filename,
            message="Image uploaded successfully and linked to conversation"
        )
        
    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

@router.post("/api/cia/upload-file")
async def upload_file_multipart(
    file: UploadFile = File(...),
    conversation_id: str = Form(...),
    user_id: str = Form(...),
    session_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """Upload image file using multipart form data"""
    try:
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Read file content
        file_content = await file.read()
        
        # Convert to base64
        image_data = base64.b64encode(file_content).decode('utf-8')
        
        # Use the existing upload logic
        upload_data = ConversationImageUpload(
            conversation_id=conversation_id,
            user_id=user_id,
            session_id=session_id,
            image_data=image_data,
            filename=file.filename or "uploaded_image.jpg",
            description=description
        )
        
        return await upload_conversation_image(upload_data)
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@router.get("/api/cia/conversation/{conversation_id}/images")
async def get_conversation_images(conversation_id: str):
    """Get all images for a conversation"""
    try:
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Get images from bid_card_images
        images_result = db.client.table("bid_card_images") \
            .select("id, filename, description, created_at") \
            .eq("conversation_id", conversation_id) \
            .order("created_at", desc=True).execute()
        
        return {
            "conversation_id": conversation_id,
            "images": images_result.data,
            "count": len(images_result.data)
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversation images: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/cia/image/{image_id}")
async def get_image_data(image_id: str):
    """Get image data by ID"""
    try:
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Get image from database
        image_result = db.client.table("bid_card_images") \
            .select("*") \
            .eq("id", image_id) \
            .limit(1).execute()
        
        if not image_result.data:
            raise HTTPException(status_code=404, detail="Image not found")
        
        image = image_result.data[0]
        
        return {
            "id": image["id"],
            "filename": image["filename"],
            "description": image.get("description"),
            "image_data": image["image_data"],
            "created_at": image["created_at"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get image: {e}")
        raise HTTPException(status_code=500, detail=str(e))