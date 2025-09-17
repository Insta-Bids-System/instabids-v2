"""
My Bids API Router
Manages contractor's "My Bids" section with all bid cards they've interacted with
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from services.my_bids_tracker import my_bids_tracker
from database_simple import get_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/my-bids", tags=["My Bids"])

@router.get("/contractor/{contractor_id}")
async def get_contractor_my_bids(
    contractor_id: str,
    include_details: bool = True
) -> Dict[str, Any]:
    """
    Get all bid cards in a contractor's "My Bids" section
    
    Args:
        contractor_id: The contractor's ID
        include_details: Whether to include full bid card details
    
    Returns:
        Dictionary with My Bids summary and list of bid cards
    """
    try:
        # Load full My Bids context
        context = await my_bids_tracker.load_full_my_bids_context(contractor_id)
        
        # Get detailed bid cards if requested
        if include_details:
            my_bids = await my_bids_tracker.get_contractor_my_bids(
                contractor_id, 
                include_full_details=True
            )
            context['bid_cards'] = my_bids
        
        return {
            "success": True,
            "contractor_id": contractor_id,
            "summary": {
                "total_bids": context.get('total_my_bids', 0),
                "total_messages": context.get('total_messages', 0),
                "total_proposals": context.get('total_proposals', 0),
                "engagement_level": context.get('engagement_level', 'none'),
                "active_conversations": len(context.get('active_conversations', [])),
                "most_recent_interaction": context.get('most_recent_interaction')
            },
            "my_bids": context.get('bid_cards', []),
            "active_conversations": context.get('active_conversations', [])
        }
        
    except Exception as e:
        logger.error(f"Error getting My Bids for contractor {contractor_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class TrackInteractionRequest(BaseModel):
    contractor_id: str
    bid_card_id: str
    interaction_type: str
    details: Optional[Dict[str, Any]] = None

@router.post("/track-interaction")
async def track_bid_interaction(request: TrackInteractionRequest) -> Dict[str, Any]:
    """
    Track a contractor's interaction with a bid card
    
    Args:
        request: TrackInteractionRequest with contractor_id, bid_card_id, interaction_type, and optional details
    
    Returns:
        Success response
    """
    try:
        success = await my_bids_tracker.track_bid_interaction(
            contractor_id=request.contractor_id,
            bid_card_id=request.bid_card_id,
            interaction_type=request.interaction_type,
            details=request.details
        )
        
        if success:
            return {
                "success": True,
                "message": f"Tracked {request.interaction_type} interaction for bid card"
            }
        else:
            return {
                "success": False,
                "message": "Failed to track interaction"
            }
            
    except Exception as e:
        logger.error(f"Error tracking bid interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bid-card/{bid_card_id}/contractor/{contractor_id}")
async def get_bid_interaction_context(
    bid_card_id: str,
    contractor_id: str
) -> Dict[str, Any]:
    """
    Get full interaction context for a specific bid card and contractor
    
    Args:
        bid_card_id: The bid card ID
        contractor_id: The contractor's ID
    
    Returns:
        Complete interaction history and context
    """
    try:
        context = await my_bids_tracker.get_bid_interaction_context(
            contractor_id=contractor_id,
            bid_card_id=bid_card_id
        )
        
        return {
            "success": True,
            "bid_card_id": bid_card_id,
            "contractor_id": contractor_id,
            "has_interaction": context.get('has_interaction', False),
            "interaction_summary": context.get('interaction_summary'),
            "total_messages": len(context.get('messages', [])),
            "total_proposals": len(context.get('proposals', [])),
            "total_questions": len(context.get('questions', [])),
            "messages": context.get('messages', []),
            "proposals": context.get('proposals', []),
            "questions": context.get('questions', [])
        }
        
    except Exception as e:
        logger.error(f"Error getting bid interaction context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{contractor_id}")
async def get_my_bids_stats(contractor_id: str) -> Dict[str, Any]:
    """
    Get statistics about a contractor's My Bids activity
    
    Args:
        contractor_id: The contractor's ID
    
    Returns:
        Statistics and analytics about My Bids
    """
    try:
        supabase = get_client()
        
        # Get all My Bids records
        my_bids = supabase.table('contractor_my_bids').select('*').eq(
            'contractor_id', contractor_id
        ).execute()
        
        if not my_bids.data:
            return {
                "success": True,
                "contractor_id": contractor_id,
                "stats": {
                    "total_bid_cards": 0,
                    "viewed": 0,
                    "engaged": 0,
                    "quoted": 0,
                    "selected": 0,
                    "avg_interactions_per_bid": 0,
                    "most_active_project_type": None
                }
            }
        
        # Calculate statistics
        stats = {
            "total_bid_cards": len(my_bids.data),
            "viewed": len([b for b in my_bids.data if b['status'] == 'viewed']),
            "engaged": len([b for b in my_bids.data if b['status'] == 'engaged']),
            "quoted": len([b for b in my_bids.data if b['status'] == 'quoted']),
            "selected": len([b for b in my_bids.data if b['status'] == 'selected']),
            "avg_interactions_per_bid": sum(b['interaction_count'] for b in my_bids.data) / len(my_bids.data) if my_bids.data else 0
        }
        
        # Find most active project type
        project_types = {}
        for bid in my_bids.data:
            project_type = bid.get('project_type', 'unknown')
            project_types[project_type] = project_types.get(project_type, 0) + 1
        
        if project_types:
            stats['most_active_project_type'] = max(project_types, key=project_types.get)
        else:
            stats['most_active_project_type'] = None
        
        return {
            "success": True,
            "contractor_id": contractor_id,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting My Bids stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/remove/{contractor_id}/{bid_card_id}")
async def remove_from_my_bids(
    contractor_id: str,
    bid_card_id: str
) -> Dict[str, Any]:
    """
    Remove a bid card from contractor's My Bids (e.g., if they're no longer interested)
    
    Args:
        contractor_id: The contractor's ID
        bid_card_id: The bid card to remove
    
    Returns:
        Success response
    """
    try:
        supabase = get_client()
        
        # Delete the My Bids record
        result = supabase.table('contractor_my_bids').delete().eq(
            'contractor_id', contractor_id
        ).eq('bid_card_id', bid_card_id).execute()
        
        if result.data:
            return {
                "success": True,
                "message": "Bid card removed from My Bids"
            }
        else:
            return {
                "success": False,
                "message": "Bid card not found in My Bids"
            }
            
    except Exception as e:
        logger.error(f"Error removing from My Bids: {e}")
        raise HTTPException(status_code=500, detail=str(e))