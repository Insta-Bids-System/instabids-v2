"""
API endpoints for bid card images
"""

from fastapi import APIRouter, HTTPException
from database_simple import db
import json

router = APIRouter(prefix="/api/bid-cards", tags=["bid-card-images"])

@router.get("/{bid_card_id}/images")
async def get_bid_card_images(bid_card_id: str):
    """
    Get all images associated with a bid card including RFI photos and project images
    """
    try:
        supabase_client = db.client
        
        # Get the bid card with its bid_document
        bid_card_result = supabase_client.table("bid_cards").select("*").eq("id", bid_card_id).execute()
        
        if not bid_card_result.data:
            raise HTTPException(status_code=404, detail="Bid card not found")
        
        bid_card = bid_card_result.data[0]
        bid_document = bid_card.get("bid_document", {})
        
        # Extract RFI photos
        rfi_photos = bid_document.get("rfi_photos", [])
        
        # Extract project images (could be stored in different places)
        project_images = bid_document.get("project_images", [])
        
        # Also check if there are images in the project_photos table
        try:
            project_photos_result = supabase_client.table("project_photos").select("*").eq("project_id", bid_card_id).execute()
            project_photos = project_photos_result.data or []
            
            # Convert project_photos format to match our expected format
            for photo in project_photos:
                project_images.append({
                    "url": photo.get("url", ""),
                    "filename": photo.get("filename", "Unknown"),
                    "type": photo.get("photo_type", "project_image"),
                    "description": photo.get("description", "")
                })
        except Exception as e:
            print(f"Error fetching project photos: {e}")
            # Continue without project photos if there's an error
        
        return {
            "bid_card_id": bid_card_id,
            "bid_card_number": bid_card.get("bid_card_number", ""),
            "rfi_photos": rfi_photos,
            "project_images": project_images,
            "total_images": len(rfi_photos) + len(project_images)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching bid card images: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{bid_card_id}/rfi-photos")
async def get_bid_card_rfi_photos(bid_card_id: str):
    """
    Get only RFI photos for a specific bid card
    """
    try:
        supabase_client = db.client
        
        # Get the bid card with its bid_document
        bid_card_result = supabase_client.table("bid_cards").select("bid_document").eq("id", bid_card_id).execute()
        
        if not bid_card_result.data:
            raise HTTPException(status_code=404, detail="Bid card not found")
        
        bid_document = bid_card_result.data[0].get("bid_document", {})
        rfi_photos = bid_document.get("rfi_photos", [])
        
        return {
            "bid_card_id": bid_card_id,
            "rfi_photos": rfi_photos,
            "count": len(rfi_photos)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching RFI photos: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{bid_card_id}/project-images")
async def get_bid_card_project_images(bid_card_id: str):
    """
    Get only project images for a specific bid card
    """
    try:
        supabase_client = db.client
        
        # Get images from bid_document
        bid_card_result = supabase_client.table("bid_cards").select("bid_document").eq("id", bid_card_id).execute()
        project_images = []
        
        if bid_card_result.data:
            bid_document = bid_card_result.data[0].get("bid_document", {})
            project_images = bid_document.get("project_images", [])
        
        # Also check project_photos table
        try:
            project_photos_result = supabase_client.table("project_photos").select("*").eq("project_id", bid_card_id).execute()
            project_photos = project_photos_result.data or []
            
            # Add project_photos to the list
            for photo in project_photos:
                project_images.append({
                    "url": photo.get("url", ""),
                    "filename": photo.get("filename", "Unknown"),
                    "type": photo.get("photo_type", "project_image"),
                    "description": photo.get("description", "")
                })
        except Exception as e:
            print(f"Error fetching project photos: {e}")
        
        return {
            "bid_card_id": bid_card_id,
            "project_images": project_images,
            "count": len(project_images)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching project images: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")