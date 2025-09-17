#!/usr/bin/env python3
"""
Stock Photo API Endpoints
Add these to your FastAPI app or router
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from agents.stock_photos.stock_photo_manager import StockPhotoManager

router = APIRouter(prefix="/api/stock-photos", tags=["stock-photos"])

# Initialize manager
manager = StockPhotoManager()

class StockPhotoUpload(BaseModel):
    project_type_slug: str
    photo_url: str
    alt_text: Optional[str] = None
    priority: int = 1

@router.get("/bid-card/{bid_card_id}/photo")
async def get_bid_card_photo(bid_card_id: str):
    """
    Get the appropriate photo for a bid card
    Returns homeowner photo if available, otherwise stock photo
    """
    photo_data = manager.get_bid_card_photo(bid_card_id)
    return {
        "bid_card_id": bid_card_id,
        "photo_url": photo_data.get('photo_url'),
        "source": photo_data.get('source'),
        "all_photos": photo_data.get('all_photos', [])
    }

@router.get("/project-type/{project_type}/stock-photo")
async def get_project_type_stock_photo(project_type: str):
    """Get stock photo for a specific project type"""
    photo_url = manager.get_stock_photo_for_project_type(project_type)
    if not photo_url:
        raise HTTPException(status_code=404, detail=f"No stock photo found for project type: {project_type}")
    
    return {
        "project_type": project_type,
        "stock_photo_url": photo_url
    }

@router.post("/upload")
async def upload_stock_photo(photo: StockPhotoUpload):
    """Upload a stock photo for a project type"""
    success = manager.upload_stock_photo(
        photo.project_type_slug,
        photo.photo_url,
        photo.alt_text,
        photo.priority
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload stock photo")
    
    return {
        "message": "Stock photo uploaded successfully",
        "project_type_slug": photo.project_type_slug
    }

@router.post("/bulk-upload")
async def bulk_upload_stock_photos(photos: List[StockPhotoUpload]):
    """Bulk upload stock photos"""
    photo_list = [photo.dict() for photo in photos]
    results = manager.bulk_upload_stock_photos(photo_list)
    
    return {
        "message": "Bulk upload complete",
        "results": results
    }

@router.put("/bid-card/{bid_card_id}/refresh-photo")
async def refresh_bid_card_photo(bid_card_id: str):
    """
    Refresh the stock photo for a bid card
    Only updates if no homeowner photos exist
    """
    success = manager.update_bid_card_stock_photo(bid_card_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update bid card stock photo")
    
    return {
        "message": "Bid card photo refreshed",
        "bid_card_id": bid_card_id
    }

@router.get("/missing-photos")
async def get_project_types_without_photos():
    """Get list of project types that don't have stock photos"""
    missing = manager.get_project_types_without_photos()
    
    return {
        "count": len(missing),
        "project_types": missing
    }

# Enhanced bid card response that includes stock photo fallback
@router.get("/bid-card/{bid_card_id}/enhanced")
async def get_enhanced_bid_card(bid_card_id: str):
    """
    Get bid card with intelligent photo selection
    Includes homeowner photos if available, otherwise stock photo
    """
    from database_simple import get_client
    
    supabase = get_client()
    
    # Get bid card
    result = supabase.table('bid_cards').select('*').eq('id', bid_card_id).single().execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Bid card not found")
    
    bid_card = result.data
    
    # Get photo data
    photo_data = manager.get_bid_card_photo(bid_card_id)
    
    # Enhance bid card with photo information
    bid_card['photos'] = {
        'hero_image_url': photo_data.get('photo_url'),
        'photo_source': photo_data.get('source'),
        'all_photos': photo_data.get('all_photos', []),
        'has_homeowner_photos': photo_data.get('source') in ['homeowner', 'homeowner_rfi'],
        'using_stock_photo': photo_data.get('source') == 'stock'
    }
    
    return bid_card