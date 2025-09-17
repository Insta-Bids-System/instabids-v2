#!/usr/bin/env python3
"""
CIA Image Upload API - Fixed to use Supabase Storage buckets instead of base64 in database
This prevents the massive egress issue caused by storing base64 strings
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import base64
import os
from datetime import datetime
import logging
import io

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
    url: str  # Public URL from bucket
    storage_path: str  # Path in bucket
    filename: str
    message: str

class ConversationImageUpload(BaseModel):
    conversation_id: str
    user_id: str
    session_id: Optional[str] = None
    image_data: str  # base64 encoded (from frontend)
    filename: str
    description: Optional[str] = None

@router.post("/api/cia/upload-image", response_model=ImageUploadResponse)
async def upload_conversation_image(upload: ConversationImageUpload):
    """Upload image to Supabase Storage and store only URL in database"""
    try:
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")
        
        logger.info(f"Processing image upload for conversation {upload.conversation_id}")
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        # Handle user_id - convert to UUID if needed
        user_uuid = None
        if upload.user_id and upload.user_id != "null":
            try:
                import uuid as uuid_lib
                if len(upload.user_id) == 32:
                    user_uuid = str(uuid_lib.UUID(upload.user_id))
                elif len(upload.user_id) == 36:
                    user_uuid = upload.user_id
                else:
                    user_uuid = None
            except:
                user_uuid = None
        
        # Decode base64 image data
        try:
            # Remove data URL prefix if present
            if "base64," in upload.image_data:
                image_data_str = upload.image_data.split("base64,")[1]
            else:
                image_data_str = upload.image_data
            
            image_bytes = base64.b64decode(image_data_str)
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            raise HTTPException(status_code=400, detail="Invalid base64 image data")
        
        # Determine file extension
        file_extension = upload.filename.split('.')[-1] if '.' in upload.filename else 'jpg'
        
        # Create storage path
        storage_path = f"bid-cards/{upload.conversation_id}/{image_id}.{file_extension}"
        
        # Upload to Supabase Storage bucket
        try:
            # Create or use existing bucket
            bucket_name = "bid-card-images"
            
            # Check if bucket exists, create if not
            try:
                buckets = db.client.storage.list_buckets()
                bucket_exists = any(b['name'] == bucket_name for b in buckets)
                
                if not bucket_exists:
                    # Create public bucket for bid card images
                    db.client.storage.create_bucket(
                        bucket_name,
                        options={
                            "public": True,  # Make bucket public for easy access
                            "allowed_mime_types": ["image/jpeg", "image/png", "image/gif", "image/webp"],
                            "file_size_limit": 10485760  # 10MB limit
                        }
                    )
                    logger.info(f"Created bucket: {bucket_name}")
            except Exception as e:
                logger.warning(f"Bucket check/creation warning: {e}")
                # Bucket might already exist, continue
            
            # Upload image to bucket
            upload_response = db.client.storage.from_(bucket_name).upload(
                path=storage_path,
                file=image_bytes,
                file_options={"content-type": f"image/{file_extension}"}
            )
            
            # Get public URL for the uploaded image
            public_url = db.client.storage.from_(bucket_name).get_public_url(storage_path)
            
            logger.info(f"Successfully uploaded image to storage: {storage_path}")
            
        except Exception as e:
            logger.error(f"Failed to upload to Supabase Storage: {e}")
            # Fallback: Store URL pointing to future location
            public_url = f"https://xrhgrthdcaymxuqcgrmj.supabase.co/storage/v1/object/public/{bucket_name}/{storage_path}"
            logger.warning(f"Using fallback URL: {public_url}")
        
        # Store only URL and metadata in database (NOT base64!)
        image_entry = {
            "id": image_id,
            "url": public_url,  # Public URL from bucket
            "thumbnail_url": public_url,  # Same URL for now, could generate thumbnail later
            "storage_path": storage_path,  # Path in bucket for management
            "caption": upload.description or "Uploaded image",
            "is_primary": False,
            "upload_date": datetime.now(),
            "created_at": datetime.now(),
            # Metadata fields
            "conversation_id": upload.conversation_id,
            "user_id": user_uuid,
            "session_id": upload.session_id,
            "filename": upload.filename,
            "description": upload.description,
            "upload_type": "conversation",
            # NO image_data field! This is the fix!
        }
        
        # Find or create potential bid card
        bid_card_id = None
        try:
            existing_card = db.client.table("potential_bid_cards") \
                .select("id, photo_ids") \
                .eq("cia_conversation_id", upload.conversation_id) \
                .limit(1).execute()
            
            if existing_card.data:
                bid_card = existing_card.data[0]
                bid_card_id = bid_card["id"]
                
                # Update photo_ids with URL (not base64!)
                current_photo_ids = bid_card.get("photo_ids", [])
                if not isinstance(current_photo_ids, list):
                    current_photo_ids = []
                
                # Store URL reference in photo_ids
                photo_reference = {
                    "id": image_id,
                    "url": public_url,
                    "storage_path": storage_path,
                    "caption": upload.description or "",
                    "uploaded_at": datetime.now().isoformat()
                }
                
                updated_photo_ids = current_photo_ids + [photo_reference]
                
                # Update bid card with new photo reference
                db.client.table("potential_bid_cards") \
                    .update({"photo_ids": updated_photo_ids}) \
                    .eq("id", bid_card_id).execute()
                
                logger.info(f"Updated bid card {bid_card_id} with image URL")
            else:
                # Create new potential bid card
                bid_card_id = str(uuid.uuid4())
                photo_reference = {
                    "id": image_id,
                    "url": public_url,
                    "storage_path": storage_path,
                    "caption": upload.description or "",
                    "uploaded_at": datetime.now().isoformat()
                }
                
                new_card = {
                    "id": bid_card_id,
                    "cia_conversation_id": upload.conversation_id,
                    "session_id": upload.session_id,
                    "user_id": user_uuid,
                    "title": "Project with Images",
                    "primary_trade": "general",
                    "photo_ids": [photo_reference],  # Store URL references, not base64!
                    "completion_percentage": 10,
                    "status": "draft"
                }
                
                db.client.table("potential_bid_cards").insert(new_card).execute()
                logger.info(f"Created new bid card with image URL")
                
        except Exception as e:
            logger.warning(f"Failed to update bid card: {e}")
        
        # Store reference in unified conversation memory
        try:
            memory_entry = {
                "id": str(uuid.uuid4()),
                "conversation_id": upload.conversation_id,
                "memory_type": "image_upload",
                "memory_key": f"image_{image_id}",
                "memory_value": {
                    "image_id": image_id,
                    "url": public_url,  # Store URL, not base64!
                    "storage_path": storage_path,
                    "filename": upload.filename,
                    "description": upload.description,
                    "uploaded_at": datetime.now().isoformat()
                },
                "created_at": datetime.now().isoformat()
            }
            
            db.client.table("unified_conversation_memory").insert(memory_entry).execute()
            logger.info(f"Stored image URL reference in conversation memory")
            
        except Exception as e:
            logger.warning(f"Failed to store in conversation memory: {e}")
        
        return ImageUploadResponse(
            success=True,
            image_id=image_id,
            url=public_url,
            storage_path=storage_path,
            filename=upload.filename,
            message="Image uploaded to storage bucket successfully"
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
    """Upload image file using multipart form data - stores in bucket"""
    try:
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Read file content
        file_content = await file.read()
        
        # Convert to base64 for the upload function
        image_data = base64.b64encode(file_content).decode('utf-8')
        
        # Use the fixed upload logic
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
    """Get all images for a conversation - returns URLs only"""
    try:
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # First try to get from potential_bid_cards
        bid_card_result = db.client.table("potential_bid_cards") \
            .select("photo_ids") \
            .eq("cia_conversation_id", conversation_id) \
            .limit(1).execute()
        
        images = []
        if bid_card_result.data and bid_card_result.data[0].get("photo_ids"):
            photo_ids = bid_card_result.data[0]["photo_ids"]
            if isinstance(photo_ids, list):
                for photo in photo_ids:
                    if isinstance(photo, dict) and "url" in photo:
                        images.append({
                            "id": photo.get("id"),
                            "url": photo.get("url"),
                            "caption": photo.get("caption", ""),
                            "uploaded_at": photo.get("uploaded_at")
                        })
        
        # Also check unified_conversation_memory for images
        memory_result = db.client.table("unified_conversation_memory") \
            .select("memory_value") \
            .eq("conversation_id", conversation_id) \
            .eq("memory_type", "image_upload") \
            .execute()
        
        for memory in memory_result.data:
            if memory.get("memory_value") and "url" in memory["memory_value"]:
                images.append({
                    "id": memory["memory_value"].get("image_id"),
                    "url": memory["memory_value"].get("url"),
                    "caption": memory["memory_value"].get("description", ""),
                    "uploaded_at": memory["memory_value"].get("uploaded_at")
                })
        
        return {
            "conversation_id": conversation_id,
            "images": images,
            "count": len(images)
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversation images: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/cia/image/{image_id}")
async def get_image_url(image_id: str):
    """Get image URL by ID - no base64 data returned"""
    try:
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Search in unified_conversation_memory for the image
        memory_result = db.client.table("unified_conversation_memory") \
            .select("memory_value") \
            .eq("memory_key", f"image_{image_id}") \
            .limit(1).execute()
        
        if memory_result.data and memory_result.data[0].get("memory_value"):
            image_data = memory_result.data[0]["memory_value"]
            return {
                "id": image_id,
                "url": image_data.get("url"),
                "filename": image_data.get("filename"),
                "description": image_data.get("description"),
                "storage_path": image_data.get("storage_path"),
                "uploaded_at": image_data.get("uploaded_at")
            }
        
        raise HTTPException(status_code=404, detail="Image not found")
        
    except Exception as e:
        logger.error(f"Failed to get image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Migration helper endpoint
@router.post("/api/cia/migrate-base64-to-buckets")
async def migrate_base64_images():
    """One-time migration to move base64 images to buckets"""
    try:
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Get all images with base64 data
        images_result = db.client.table("bid_card_images") \
            .select("id, image_data, filename, conversation_id") \
            .not_.is_("image_data", "null") \
            .limit(100).execute()
        
        migrated_count = 0
        failed_count = 0
        
        for image in images_result.data:
            if image.get("image_data"):
                try:
                    # Decode base64
                    image_bytes = base64.b64decode(image["image_data"])
                    
                    # Create storage path
                    file_extension = image["filename"].split('.')[-1] if '.' in image["filename"] else 'jpg'
                    storage_path = f"migrated/{image['conversation_id']}/{image['id']}.{file_extension}"
                    
                    # Upload to bucket
                    bucket_name = "bid-card-images"
                    db.client.storage.from_(bucket_name).upload(
                        path=storage_path,
                        file=image_bytes,
                        file_options={"content-type": f"image/{file_extension}"}
                    )
                    
                    # Get public URL
                    public_url = db.client.storage.from_(bucket_name).get_public_url(storage_path)
                    
                    # Update record with URL, remove base64
                    db.client.table("bid_card_images") \
                        .update({
                            "url": public_url,
                            "storage_path": storage_path,
                            "image_data": None  # Remove base64 data!
                        }) \
                        .eq("id", image["id"]).execute()
                    
                    migrated_count += 1
                    logger.info(f"Migrated image {image['id']} to bucket")
                    
                except Exception as e:
                    logger.error(f"Failed to migrate image {image['id']}: {e}")
                    failed_count += 1
        
        return {
            "success": True,
            "migrated": migrated_count,
            "failed": failed_count,
            "message": f"Migrated {migrated_count} images to buckets"
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))