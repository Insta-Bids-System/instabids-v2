"""
Image Upload API Router
Handles image uploads for contractor-homeowner communications
"""

import os
import uuid
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from config.service_urls import get_backend_url


try:
    from database_simple import db
except ImportError:
    from database import SupabaseDB
    db = SupabaseDB()

router = APIRouter(prefix="/api/images", tags=["images"])

# Allowed image types
ALLOWED_MIME_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp"
]

# Max file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

@router.post("/upload/conversation")
async def upload_conversation_image(
    conversation_id: str = Form(...),
    sender_type: str = Form(...),
    sender_id: str = Form(...),
    message: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    """Upload an image as part of a conversation message"""
    try:
        # Validate file type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
            )

        # Read file data
        file_data = await file.read()

        # Validate file size
        if len(file_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds maximum of 10MB"
            )

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_name = f"conversations/{conversation_id}/{timestamp}_{uuid.uuid4().hex[:8]}.{file_extension}"

        # Upload to Supabase Storage
        storage_response = db.client.storage.from_("project-images").upload(
            unique_name,
            file_data,
            {
                "content-type": file.content_type,
                "cache-control": "3600",
                "upsert": "false"
            }
        )

        # Get public URL
        public_url = db.client.storage.from_("project-images").get_public_url(unique_name)

        # Parse conversation_id to get bid_card_id and contractor_id
        # Format: {bid_card_id}_{contractor_id}
        parts = conversation_id.split('_')
        bid_card_id = parts[0] if parts else conversation_id
        contractor_id = parts[1] if len(parts) > 1 else None
        
        # Find or create the conversation
        if contractor_id:
            # Look up the conversation
            conv_result = db.client.table("conversations").select("id").eq(
                "bid_card_id", bid_card_id
            ).eq("contractor_id", contractor_id).execute()
            
            if conv_result.data and len(conv_result.data) > 0:
                actual_conversation_id = conv_result.data[0]["id"]
            else:
                # Create a new conversation if it doesn't exist
                new_conv = {
                    "id": str(uuid.uuid4()),
                    "bid_card_id": bid_card_id,
                    "user_id": sender_id if sender_type == "homeowner" else "11111111-1111-1111-1111-111111111111",
                    "contractor_id": contractor_id,
                    "contractor_alias": f"Contractor {contractor_id[0].upper()}",
                    "status": "active",
                    "homeowner_unread_count": 0,
                    "contractor_unread_count": 0
                }
                conv_create = db.client.table("conversations").insert(new_conv).execute()
                actual_conversation_id = new_conv["id"]
        else:
            # No contractor_id, use bid_card_id as conversation_id
            actual_conversation_id = bid_card_id
        
        # Create message with image attachment using messaging_system_messages table
        message_data = {
            "id": str(uuid.uuid4()),
            "conversation_id": actual_conversation_id,
            "sender_type": sender_type,
            "sender_id": sender_id,
            "original_content": message or f"Shared an image: {file.filename}",
            "filtered_content": message or f"Shared an image: {file.filename}",
            "content_filtered": False,
            "message_type": "text",  # Must be one of: text, system, bid_update, status_change
            "attachments": [{
                "url": public_url,
                "type": file.content_type,
                "name": file.filename,
                "size": len(file_data)
            }],
            "is_read": False,
            "created_at": datetime.utcnow().isoformat()
        }

        # Save message via UNIFIED MESSAGING SYSTEM
        import requests
        try:
            response = requests.post(f"{get_backend_url()}/api/conversations/message", json={
                "conversation_id": actual_conversation_id,
                "sender_type": sender_type,
                "sender_id": sender_id,
                "agent_type": None,
                "content": message or f"Shared an image: {file.filename}",
                "content_type": "text",
                "metadata": {
                    "attachments": message_data["attachments"],
                    "upload_type": "image",
                    "processed_by": "image_upload_api"
                }
            }, timeout=30)
            
            if response.ok:
                result_data = response.json()
                message_id = result_data.get("message_id")
            else:
                raise Exception(f"Unified API failed: {response.text}")
                
        except Exception as api_error:
            print(f"Image upload API error: {api_error}")
            return {"success": False, "error": str(api_error)}

        if message_id:
            # Update conversation's last message timestamp and increment unread count
            unread_field = "contractor_unread_count" if sender_type == "homeowner" else "homeowner_unread_count"
            
            # Get current unread count
            conv_data = db.client.table("conversations").select(unread_field).eq("id", actual_conversation_id).execute()
            current_count = conv_data.data[0][unread_field] if conv_data.data else 0
            
            # Update with incremented count
            db.client.table("conversations").update({
                "last_message_at": datetime.utcnow().isoformat(),
                unread_field: current_count + 1
            }).eq("id", actual_conversation_id).execute()

            return {
                "success": True,
                "message": "Image uploaded successfully",
                "image_url": public_url,
                "message_id": message_data["id"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save message with image"
            )

    except Exception as e:
        print(f"Error uploading image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading image: {e!s}"
        )


@router.post("/upload/bid-card")
async def upload_bid_card_image(
    bid_card_id: str = Form(...),
    uploader_type: str = Form(...),  # 'homeowner' or 'contractor'
    uploader_id: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    """Upload an image for a bid card (project photos)"""
    try:
        # Validate file type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not allowed"
            )

        # Read file data
        file_data = await file.read()

        # Validate file size
        if len(file_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds maximum of 10MB"
            )

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_name = f"bid-cards/{bid_card_id}/{timestamp}_{uuid.uuid4().hex[:8]}.{file_extension}"

        # Upload to Supabase Storage
        storage_response = db.client.storage.from_("project-images").upload(
            unique_name,
            file_data,
            {
                "content-type": file.content_type,
                "cache-control": "3600",
                "upsert": "false"
            }
        )

        # Get public URL
        public_url = db.client.storage.from_("project-images").get_public_url(unique_name)

        # Update bid card with new image
        bid_card = db.client.table("bid_cards").select("*").eq("id", bid_card_id).single().execute()

        if bid_card.data:
            bid_document = bid_card.data.get("bid_document", {})
            images = bid_document.get("images", [])
            images.append({
                "url": public_url,
                "description": description,
                "uploaded_by": uploader_id,
                "uploaded_by_type": uploader_type,
                "uploaded_at": datetime.utcnow().isoformat()
            })

            bid_document["images"] = images

            update_result = db.client.table("bid_cards").update({
                "bid_document": bid_document,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", bid_card_id).execute()

            if update_result.data:
                return {
                    "success": True,
                    "message": "Image uploaded successfully",
                    "image_url": public_url
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update bid card with image"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bid card not found"
            )

    except Exception as e:
        print(f"Error uploading bid card image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading image: {e!s}"
        )


@router.post("/upload/potential-bid-card")
async def upload_potential_bid_card_image(
    potential_bid_card_id: str = Form(...),
    conversation_id: str = Form(...),
    user_id: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    """Upload an image for a potential bid card during CIA conversation"""
    try:
        # Validate file type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
            )

        # Validate file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )

        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"potential_bid_card/{potential_bid_card_id}/{uuid4()}.{file_extension}"
        
        # Upload to Supabase storage
        from supabase import create_client
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase = create_client(url, key)
        
        upload_result = supabase.storage.from_("project-images").upload(
            unique_filename,
            file_content,
            {"content-type": file.content_type}
        )
        
        if upload_result.error:
            raise Exception(f"Storage upload failed: {upload_result.error}")
        
        # Get public URL
        public_url = supabase.storage.from_("project-images").get_public_url(unique_filename)
        image_url = public_url.public_url if hasattr(public_url, 'public_url') else str(public_url)

        # Update potential bid card with new image
        potential_bid_card = db.client.table("potential_bid_cards").select("*").eq("id", potential_bid_card_id).single().execute()

        if potential_bid_card.data:
            # Get existing photo_ids or initialize as empty array
            photo_ids = potential_bid_card.data.get("photo_ids", [])
            
            # Add new image info
            new_image_info = {
                "id": str(uuid4()),
                "url": image_url,
                "filename": file.filename,
                "description": description,
                "uploaded_by": user_id,
                "uploaded_at": datetime.utcnow().isoformat(),
                "conversation_id": conversation_id
            }
            
            photo_ids.append(new_image_info)
            
            # Update the potential bid card
            update_result = db.client.table("potential_bid_cards").update({
                "photo_ids": photo_ids,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", potential_bid_card_id).execute()
            
            if not update_result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update potential bid card with image"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Potential bid card not found"
            )

        return {
            "success": True,
            "image_url": image_url,
            "image_id": new_image_info["id"],
            "potential_bid_card_id": potential_bid_card_id,
            "total_images": len(photo_ids)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading potential bid card image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading image: {e!s}"
        )


@router.get("/conversation/{conversation_id}")
async def get_conversation_images(conversation_id: str):
    """Get all images from a conversation"""
    try:
        # Get all messages with attachments
        result = db.client.table("messages").select("*").eq(
            "conversation_id", conversation_id
        ).not_.is_("attachments", "null").order("created_at", desc=False).execute()

        images = []
        for message in result.data or []:
            for attachment in message.get("attachments", []):
                if attachment.get("type", "").startswith("image/"):
                    images.append({
                        "url": attachment["url"],
                        "name": attachment.get("name", "Image"),
                        "sender_type": message["sender_type"],
                        "sender_id": message["sender_id"],
                        "uploaded_at": message["created_at"],
                        "message_id": message["id"]
                    })

        return {
            "success": True,
            "images": images,
            "total": len(images)
        }

    except Exception as e:
        print(f"Error fetching conversation images: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching images: {e!s}"
        )


@router.get("/bid-card/{bid_card_id}")
async def get_bid_card_images(bid_card_id: str):
    """Get all images for a bid card"""
    try:
        result = db.client.table("bid_cards").select("bid_document").eq(
            "id", bid_card_id
        ).single().execute()

        if result.data:
            images = result.data.get("bid_document", {}).get("images", [])
            return {
                "success": True,
                "images": images,
                "total": len(images)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bid card not found"
            )

    except Exception as e:
        print(f"Error fetching bid card images: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching images: {e!s}"
        )


@router.delete("/{image_path:path}")
async def delete_image(image_path: str, user_id: str):
    """Delete an image from storage"""
    try:
        # Delete from Supabase Storage
        delete_response = db.client.storage.from_("project-images").remove([image_path])

        return {
            "success": True,
            "message": "Image deleted successfully"
        }

    except Exception as e:
        print(f"Error deleting image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting image: {e!s}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "success": True,
        "status": "healthy",
        "message": "Image upload API is running",
        "timestamp": datetime.utcnow().isoformat()
    }
