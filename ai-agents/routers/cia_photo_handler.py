"""
CIA Photo Handler - Manages photo uploads for potential bid cards
"""

import uuid
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from database_simple import db
except ImportError:
    from database import SupabaseDB
    db = SupabaseDB()

async def save_images_to_potential_bid_card(
    conversation_id: str,
    user_id: str,
    images: List[str]
) -> Optional[List[str]]:
    """
    Save images to potential bid card's photo_ids field
    Returns list of photo IDs that were saved
    """
    try:
        if not images:
            return None
            
        logger.info(f"Saving {len(images)} images for conversation {conversation_id}")
        
        # Find the potential bid card for this conversation
        tracking_result = db.client.table("cia_conversation_tracking").select(
            "potential_bid_card_id"
        ).eq("conversation_id", conversation_id).execute()
        
        if not tracking_result.data:
            logger.warning(f"No potential bid card found for conversation {conversation_id}")
            return None
            
        potential_bid_card_id = tracking_result.data[0]["potential_bid_card_id"]
        
        # Save each image to photo_storage table
        photo_ids = []
        for idx, image_data in enumerate(images):
            try:
                # Generate unique photo ID
                photo_id = str(uuid.uuid4())
                
                # Extract base64 data and metadata
                if image_data.startswith("data:"):
                    # Format: data:image/jpeg;base64,<data>
                    parts = image_data.split(",", 1)
                    if len(parts) == 2:
                        mime_info = parts[0].replace("data:", "")
                        base64_data = parts[1]
                        mime_type = mime_info.split(";")[0] if ";" in mime_info else "image/jpeg"
                    else:
                        base64_data = image_data
                        mime_type = "image/jpeg"
                else:
                    base64_data = image_data
                    mime_type = "image/jpeg"
                
                # Save to photo_storage table
                photo_record = {
                    "id": photo_id,
                    "user_id": user_id,
                    "url": f"data:{mime_type};base64,{base64_data[:100]}...",  # Store truncated for logging
                    "full_data": image_data,  # Store full data
                    "metadata": {
                        "source": "cia_chat",
                        "conversation_id": conversation_id,
                        "potential_bid_card_id": potential_bid_card_id,
                        "upload_timestamp": datetime.utcnow().isoformat(),
                        "mime_type": mime_type,
                        "index": idx
                    },
                    "created_at": datetime.utcnow().isoformat()
                }
                
                # Check if photo_storage table exists, if not store inline
                try:
                    result = db.client.table("photo_storage").insert(photo_record).execute()
                    if result.data:
                        photo_ids.append(photo_id)
                        logger.info(f"Saved photo {photo_id} to photo_storage")
                except Exception as storage_error:
                    logger.warning(f"photo_storage table not available: {storage_error}")
                    # Store inline in potential_bid_card instead
                    photo_ids.append(image_data)
                    
            except Exception as e:
                logger.error(f"Error saving individual photo: {e}")
                continue
        
        if photo_ids:
            # Update potential bid card with photo IDs
            try:
                # Get current photo_ids
                current_result = db.client.table("potential_bid_cards").select(
                    "photo_ids"
                ).eq("id", potential_bid_card_id).execute()
                
                current_photo_ids = []
                if current_result.data and current_result.data[0].get("photo_ids"):
                    current_photo_ids = current_result.data[0]["photo_ids"]
                    if not isinstance(current_photo_ids, list):
                        current_photo_ids = []
                
                # Append new photo IDs
                updated_photo_ids = current_photo_ids + photo_ids
                
                # Update potential bid card
                update_result = db.client.table("potential_bid_cards").update({
                    "photo_ids": updated_photo_ids,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", potential_bid_card_id).execute()
                
                if update_result.data:
                    logger.info(f"Updated potential bid card {potential_bid_card_id} with {len(photo_ids)} new photos")
                    
                    # Set cover photo if not already set
                    if photo_ids and not current_result.data[0].get("cover_photo_id"):
                        db.client.table("potential_bid_cards").update({
                            "cover_photo_id": photo_ids[0] if isinstance(photo_ids[0], str) and len(photo_ids[0]) == 36 else None
                        }).eq("id", potential_bid_card_id).execute()
                    
                    return photo_ids
                else:
                    logger.error("Failed to update potential bid card with photo IDs")
                    return None
                    
            except Exception as e:
                logger.error(f"Error updating potential bid card: {e}")
                return None
        
        return photo_ids
        
    except Exception as e:
        logger.error(f"Error saving images to potential bid card: {e}")
        return None

async def transfer_photos_to_bid_card(
    potential_bid_card_id: str,
    bid_card_id: str
) -> bool:
    """
    Transfer photos from potential bid card to official bid card
    """
    try:
        logger.info(f"Transferring photos from potential {potential_bid_card_id} to official {bid_card_id}")
        
        # Get photos from potential bid card
        potential_result = db.client.table("potential_bid_cards").select(
            "photo_ids, cover_photo_id"
        ).eq("id", potential_bid_card_id).execute()
        
        if not potential_result.data:
            logger.warning("No potential bid card found")
            return False
            
        photo_ids = potential_result.data[0].get("photo_ids", [])
        cover_photo_id = potential_result.data[0].get("cover_photo_id")
        
        if not photo_ids:
            logger.info("No photos to transfer")
            return True
            
        # Get current bid_document from official bid card
        bid_result = db.client.table("bid_cards").select(
            "bid_document"
        ).eq("id", bid_card_id).execute()
        
        if not bid_result.data:
            logger.error("Official bid card not found")
            return False
            
        bid_document = bid_result.data[0].get("bid_document", {})
        
        # Add photo_ids to bid_document
        bid_document["photo_ids"] = photo_ids
        bid_document["cover_photo_id"] = cover_photo_id
        
        # If photos are base64 data, also add to images array
        images = bid_document.get("images", [])
        for photo_id in photo_ids:
            if isinstance(photo_id, str) and photo_id.startswith("data:"):
                # This is inline base64 data
                images.append({
                    "url": photo_id,
                    "description": "Photo from CIA chat",
                    "uploaded_at": datetime.utcnow().isoformat(),
                    "source": "potential_bid_card_transfer"
                })
            elif isinstance(photo_id, str) and len(photo_id) == 36:
                # This is a UUID reference to photo_storage
                try:
                    photo_result = db.client.table("photo_storage").select(
                        "full_data, metadata"
                    ).eq("id", photo_id).execute()
                    
                    if photo_result.data:
                        images.append({
                            "url": photo_result.data[0]["full_data"],
                            "description": "Photo from CIA chat",
                            "uploaded_at": datetime.utcnow().isoformat(),
                            "source": "potential_bid_card_transfer",
                            "photo_storage_id": photo_id
                        })
                except Exception as e:
                    logger.warning(f"Could not retrieve photo {photo_id} from storage: {e}")
        
        bid_document["images"] = images
        
        # Update official bid card
        update_result = db.client.table("bid_cards").update({
            "bid_document": bid_document,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", bid_card_id).execute()
        
        if update_result.data:
            logger.info(f"Successfully transferred {len(photo_ids)} photos to official bid card")
            return True
        else:
            logger.error("Failed to update official bid card with photos")
            return False
            
    except Exception as e:
        logger.error(f"Error transferring photos: {e}")
        return False