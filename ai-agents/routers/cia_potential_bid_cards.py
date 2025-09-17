"""
CIA Potential Bid Cards API - Real-time Conversational Bid Card Builder
Handles creation and updating of potential bid cards during CIA conversations
"""

import logging
import json
from datetime import datetime
from typing import Any, Optional, Dict, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import database_simple
from database_simple import db

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models
class CreatePotentialBidCardRequest(BaseModel):
    conversation_id: str
    session_id: str
    user_id: Optional[str] = None
    anonymous_user_id: Optional[str] = None
    title: Optional[str] = "New Project"

class UpdateFieldRequest(BaseModel):
    field_name: str
    field_value: Any
    confidence: Optional[float] = 1.0
    source: str = "conversation"  # "conversation" or "manual"

class PotentialBidCardResponse(BaseModel):
    id: str
    status: str
    completion_percentage: int
    fields_collected: Dict[str, Any]
    missing_fields: List[str]
    ready_for_conversion: bool
    created_at: str
    updated_at: str

# Field mapping for CIA conversation to potential_bid_cards
FIELD_MAPPING = {
    "project_type": "primary_trade",
    "service_type": "secondary_trades",
    "project_description": "user_scope_notes", 
    "project_name": "title",
    "zip_code": "zip_code",
    "email_address": "email_address",
    "timeline": "estimated_timeline",
    "urgency_level": "urgency_level",
    "contractor_size_preference": "contractor_size_preference",
    "budget_context": "budget_context",
    "materials": "materials_specified",
    "special_requirements": "special_requirements",
    "quality_expectations": "quality_expectations",
    "timeline_flexibility": "timeline_flexibility",
    # NEW: Exact date fields
    "bid_collection_deadline": "bid_collection_deadline",
    "project_completion_deadline": "project_completion_deadline", 
    "deadline_hard": "deadline_hard",
    "deadline_context": "deadline_context",
    # Service complexity classification fields
    "service_complexity": "service_complexity",
    "trade_count": "trade_count",
    "primary_trade": "primary_trade",
    "secondary_trades": "secondary_trades"
}

# Required fields for completion
REQUIRED_FIELDS = [
    "primary_trade",      # project_type
    "user_scope_notes",   # project_description  
    "zip_code",           # location
    "urgency_level",      # timeline
]

# Nice to have fields
NICE_TO_HAVE_FIELDS = [
    "contractor_size_preference",
    "budget_context", 
    "materials_specified",
    "special_requirements",
    "timeline_flexibility"
]

@router.post("/potential-bid-cards", response_model=PotentialBidCardResponse)
async def create_potential_bid_card(request: CreatePotentialBidCardRequest):
    """
    Create a new potential bid card for CIA conversation tracking
    """
    try:
        logger.info(f"Creating potential bid card for conversation {request.conversation_id}")
        
        # Create potential bid card record
        potential_bid_card_data = {
            "title": request.title,
            "primary_trade": "general",  # Default to 'general' until CIA extracts specific trade
            "status": "draft",
            "created_by": "cia",
            "cia_thread_id": request.conversation_id,  # Fixed: column is cia_thread_id not cia_conversation_id
            "session_id": request.session_id,
            "completion_percentage": 0,
            "ready_for_conversion": False
        }
        
        # Set user_id if user is authenticated and exists in homeowners table
        if request.user_id and request.user_id != "00000000-0000-0000-0000-000000000000":
            # Check if user exists in homeowners table and get their homeowner ID
            # The constraint requires potential_bid_cards.user_id to reference homeowners.id (not homeowners.user_id)
            user_check = db.client.table("homeowners").select("id, user_id").eq("user_id", request.user_id).execute()
            if user_check.data:
                homeowner_id = user_check.data[0]["id"]  # This is the homeowner's ID (not user_id)
                potential_bid_card_data["user_id"] = homeowner_id  # Foreign key references homeowners.id
                logger.info(f"Found homeowner ID {homeowner_id} for user_id {request.user_id}")
            else:
                logger.info(f"User {request.user_id} not found in homeowners table - creating anonymous bid card")
        
        # Insert potential bid card
        result = db.client.table("potential_bid_cards").insert(potential_bid_card_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create potential bid card")
        
        potential_bid_card_id = result.data[0]["id"]
        
        # Create conversation tracking record
        tracking_data = {
            "conversation_id": request.conversation_id,
            "session_id": request.session_id,
            "potential_bid_card_id": potential_bid_card_id,
            "user_id": request.user_id if request.user_id != "00000000-0000-0000-0000-000000000000" else None,
            "anonymous_user_id": request.anonymous_user_id,
            "fields_collected": {},
            "completion_percentage": 0,
            "status": "active"
        }
        
        tracking_result = db.client.table("cia_conversation_tracking").insert(tracking_data).execute()
        
        if not tracking_result.data:
            logger.warning("Failed to create conversation tracking record")
        
        logger.info(f"Created potential bid card {potential_bid_card_id} for conversation {request.conversation_id}")
        
        return PotentialBidCardResponse(
            id=potential_bid_card_id,
            status="draft",
            completion_percentage=0,
            fields_collected={},
            missing_fields=REQUIRED_FIELDS.copy(),
            ready_for_conversion=False,
            created_at=result.data[0]["created_at"],
            updated_at=result.data[0]["updated_at"]
        )
        
    except Exception as e:
        logger.error(f"Error creating potential bid card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/potential-bid-cards/{bid_card_id}/field")
async def update_field(bid_card_id: str, request: UpdateFieldRequest):
    """
    Update a single field in the potential bid card during conversation
    """
    try:
        logger.info(f"Updating field {request.field_name} in bid card {bid_card_id}")
        
        # Map CIA field names to database column names
        db_field_name = FIELD_MAPPING.get(request.field_name, request.field_name)
        
        # Prepare update data
        update_data = {
            db_field_name: request.field_value,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Handle special field types
        if request.field_name in ["materials", "special_requirements"] and isinstance(request.field_value, str):
            # Convert single string to array
            update_data[db_field_name] = [request.field_value]
        elif request.field_name == "service_type" and isinstance(request.field_value, str):
            # Convert single service type to array
            update_data[db_field_name] = [request.field_value]
        
        # Update the potential bid card
        result = db.client.table("potential_bid_cards").update(update_data).eq("id", bid_card_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Potential bid card not found")
        
        # Calculate completion percentage
        completion_info = await calculate_completion_percentage(bid_card_id)
        
        # Update completion percentage
        db.client.table("potential_bid_cards").update({
            "completion_percentage": completion_info["percentage"],
            "ready_for_conversion": completion_info["ready_for_conversion"]
        }).eq("id", bid_card_id).execute()
        
        # Update conversation tracking
        await update_conversation_tracking(bid_card_id, request.field_name, completion_info)
        
        logger.info(f"Updated field {request.field_name} in bid card {bid_card_id} - {completion_info['percentage']}% complete")
        
        return {
            "success": True,
            "field_updated": request.field_name,
            "completion_percentage": completion_info["percentage"],
            "ready_for_conversion": completion_info["ready_for_conversion"],
            "missing_fields": completion_info["missing_fields"]
        }
        
    except Exception as e:
        logger.error(f"Error updating field {request.field_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/potential-bid-cards/{bid_card_id}")
async def get_potential_bid_card(bid_card_id: str):
    """
    Get current state of potential bid card for live preview
    """
    try:
        # Get potential bid card
        result = db.client.table("potential_bid_cards").select("*").eq("id", bid_card_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Potential bid card not found")
        
        bid_card = result.data[0]
        
        # Calculate completion info
        completion_info = await calculate_completion_percentage(bid_card_id)
        
        # Get conversation tracking info
        tracking_result = db.client.table("cia_conversation_tracking").select("*").eq("potential_bid_card_id", bid_card_id).execute()
        
        tracking_data = tracking_result.data[0] if tracking_result.data else {}
        
        # Format response for frontend
        fields_collected = {}
        for field_name, db_field in FIELD_MAPPING.items():
            if bid_card.get(db_field) is not None:
                fields_collected[field_name] = bid_card[db_field]
        
        return {
            "id": bid_card_id,
            "status": bid_card.get("status", "draft"),
            "completion_percentage": completion_info["percentage"],
            "fields_collected": fields_collected,
            "missing_fields": completion_info["missing_fields"],
            "ready_for_conversion": completion_info["ready_for_conversion"],
            "created_at": bid_card.get("created_at"),
            "updated_at": bid_card.get("updated_at"),
            "conversation_id": tracking_data.get("conversation_id"),
            "session_id": tracking_data.get("session_id"),
            "photo_ids": bid_card.get("photo_ids", []),
            "cover_photo_id": bid_card.get("cover_photo_id"),
            "bid_card_preview": {
                "title": bid_card.get("title", "New Project"),
                "project_type": bid_card.get("primary_trade"),
                "description": bid_card.get("user_scope_notes"),
                "location": bid_card.get("zip_code"),
                "timeline": bid_card.get("urgency_level"),
                "contractor_preference": bid_card.get("contractor_size_preference"),
                "special_notes": bid_card.get("special_requirements", []),
                "uploaded_photos": bid_card.get("photo_ids", [])
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting potential bid card {bid_card_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/potential-bid-cards")
async def get_user_potential_bid_cards(user_id: str):
    """Get all potential bid cards for a user that haven't been converted yet"""
    try:
        # Get unconverted potential bid cards for this user
        result = db.client.table("potential_bid_cards").select("*").eq(
            "user_id", user_id
        ).neq(
            "status", "converted"
        ).order(
            "created_at", desc=False
        ).execute()
        
        if result.data:
            # Calculate completion for each card
            bid_cards = []
            for card in result.data:
                completion_info = await calculate_completion_percentage(card["id"])
                card["completion_info"] = completion_info
                bid_cards.append(card)
            
            return {
                "success": True,
                "bid_cards": bid_cards,
                "count": len(bid_cards)
            }
        
        return {
            "success": True,
            "bid_cards": [],
            "count": 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching user potential bid cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/{conversation_id}/potential-bid-card")
async def get_potential_bid_card_by_conversation(conversation_id: str):
    """
    Get potential bid card by conversation ID for CIA agent use
    """
    try:
        # Find tracking record by conversation ID
        tracking_result = db.client.table("cia_conversation_tracking").select("potential_bid_card_id").eq("conversation_id", conversation_id).execute()
        
        if not tracking_result.data:
            # Return 404 properly - don't raise inside try block
            logger.info(f"No potential bid card found for conversation {conversation_id}")
            raise HTTPException(status_code=404, detail="No potential bid card found for this conversation")
        
        bid_card_id = tracking_result.data[0]["potential_bid_card_id"]
        
        # Use the main get endpoint
        return await get_potential_bid_card(bid_card_id)
        
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error getting potential bid card for conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/potential-bid-cards/{bid_card_id}/convert-to-bid-card")
async def convert_to_bid_card(bid_card_id: str):
    """
    Convert potential bid card to official bid card when user signs up
    """
    try:
        logger.info(f"Converting potential bid card {bid_card_id} to official bid card")
        
        # Get potential bid card
        result = db.client.table("potential_bid_cards").select("*").eq("id", bid_card_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Potential bid card not found")
        
        potential_bid_card = result.data[0]
        
        # Ensure it's ready for conversion
        completion_info = await calculate_completion_percentage(bid_card_id)
        if not completion_info["ready_for_conversion"]:
            raise HTTPException(status_code=400, detail=f"Bid card not ready for conversion. Missing: {', '.join(completion_info['missing_fields'])}")
        
        # Check if user is authenticated (has user_id)
        if not potential_bid_card.get("user_id"):
            raise HTTPException(status_code=400, detail="User must be authenticated to convert to official bid card")
        
        # Create official bid card directly with proper data structure
        import uuid
        from datetime import datetime
        
        # Generate bid card number
        bid_card_number = f"BC-LIVE-{int(datetime.now().timestamp())}"
        
        # Map urgency levels from potential_bid_cards to bid_cards constraints
        urgency_mapping = {
            "low": "month",       # low urgency → month timeline
            "medium": "week",     # medium urgency → week timeline  
            "high": "urgent",     # high urgency → urgent timeline
            "urgent": "urgent",   # urgent → urgent
            "emergency": "emergency"  # emergency → emergency
        }
        
        # Get the urgency level and map it
        potential_urgency = potential_bid_card.get("urgency_level", "medium")
        mapped_urgency = urgency_mapping.get(potential_urgency, "week")
        
        # Prepare bid card data for direct database insertion - transfer ALL collected data
        bid_card_data = {
            "id": str(uuid.uuid4()),
            "bid_card_number": bid_card_number,
            "project_type": potential_bid_card.get("primary_trade", "general"),
            "title": potential_bid_card.get("title", "New Project"),
            "description": potential_bid_card.get("user_scope_notes", ""),
            "urgency_level": mapped_urgency,  # Use mapped urgency value
            "user_id": potential_bid_card["user_id"],
            "contractor_count_needed": 4,  # Default
            "status": "generated",
            "complexity_score": potential_bid_card.get("project_complexity", "simple") == "complex" and 5 or 3,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            
            # Transfer location data (using actual bid_cards columns)
            "location_zip": potential_bid_card.get("zip_code"),
            "location_address": potential_bid_card.get("location_address", ""),
            "location_city": potential_bid_card.get("location_city", ""),
            "location_state": potential_bid_card.get("location_state", ""),
            
            # Transfer timeline preferences (using actual columns)
            "timeline_flexibility": potential_bid_card.get("timeline_flexibility", "flexible"),
            
            # Use categories array for project classification  
            "categories": [potential_bid_card.get("primary_trade", "general")] + potential_bid_card.get("secondary_trades", []),
            
            # Use requirements array for special requirements
            "requirements": potential_bid_card.get("special_requirements", []) + potential_bid_card.get("materials_specified", []),
            
            # Set budget ranges if collected
            "budget_min": potential_bid_card.get("budget_range_min"),
            "budget_max": potential_bid_card.get("budget_range_max"),
            
            # Enhanced bid_document with ALL collected potential bid card data
            "bid_document": {
                # Core project details
                "project_description": potential_bid_card.get("user_scope_notes", ""),
                "room_location": potential_bid_card.get("room_location"),
                "property_area": potential_bid_card.get("property_area"),
                
                # Location information
                "location": potential_bid_card.get("zip_code", ""),
                "location_details": {
                    "zip_code": potential_bid_card.get("zip_code"),
                    "address": potential_bid_card.get("location_address"),
                    "city": potential_bid_card.get("location_city"), 
                    "state": potential_bid_card.get("location_state"),
                    "radius_miles": potential_bid_card.get("location_radius_miles")
                },
                
                # Contact information
                "contact_information": {
                    "email": potential_bid_card.get("email_address"),
                    "phone": potential_bid_card.get("phone_number")
                },
                
                # Complete project requirements
                "project_requirements": {
                    "primary_trade": potential_bid_card.get("primary_trade"),
                    "secondary_trades": potential_bid_card.get("secondary_trades", []),
                    "special_requirements": potential_bid_card.get("special_requirements", []),
                    "materials_specified": potential_bid_card.get("materials_specified", []),
                    "quality_expectations": potential_bid_card.get("quality_expectations"),
                    "contractor_size_preference": potential_bid_card.get("contractor_size_preference"),
                    "project_complexity": potential_bid_card.get("project_complexity"),
                    "requires_general_contractor": potential_bid_card.get("requires_general_contractor"),
                    "component_type": potential_bid_card.get("component_type")
                },
                
                # Timeline and scheduling
                "timeline_preferences": {
                    "urgency_level": mapped_urgency,
                    "timeline_flexibility": potential_bid_card.get("timeline_flexibility"),
                    "estimated_timeline": potential_bid_card.get("estimated_timeline"),
                    "seasonal_constraint": potential_bid_card.get("seasonal_constraint"),
                    "budget_context": potential_bid_card.get("budget_context")
                },
                
                # Budget information
                "budget_details": {
                    "budget_range_min": potential_bid_card.get("budget_range_min"),
                    "budget_range_max": potential_bid_card.get("budget_range_max"),
                    "budget_context": potential_bid_card.get("budget_context")
                },
                
                # Project relationships and grouping
                "project_relationships": {
                    "parent_project_id": potential_bid_card.get("parent_project_id"),
                    "related_project_ids": potential_bid_card.get("related_project_ids", []),
                    "bundle_group_id": potential_bid_card.get("bundle_group_id"),
                    "eligible_for_group_bidding": potential_bid_card.get("eligible_for_group_bidding")
                },
                
                # Visual content
                "media": {
                    "photo_ids": potential_bid_card.get("photo_ids", []),
                    "cover_photo_id": potential_bid_card.get("cover_photo_id")
                },
                
                # AI analysis data
                "ai_analysis": potential_bid_card.get("ai_analysis", {}),
                "last_ai_analysis_at": potential_bid_card.get("last_ai_analysis_at"),
                
                # Conversion metadata
                "conversion_metadata": {
                    "converted_from_potential_id": bid_card_id,
                    "conversion_timestamp": datetime.utcnow().isoformat(),
                    "completion_percentage_at_conversion": potential_bid_card.get("completion_percentage", 0),
                    "priority": potential_bid_card.get("priority"),
                    "created_by": potential_bid_card.get("created_by"),
                    "cia_conversation_id": potential_bid_card.get("cia_conversation_id"),
                    "session_id": potential_bid_card.get("session_id")
                }
            }
        }
        
        # Create official bid card directly in database
        result = db.client.table("bid_cards").insert(bid_card_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create official bid card")
        
        official_bid_card = result.data[0]
        official_bid_card_id = official_bid_card["id"]
        
        # Transfer photos if available
        if potential_bid_card.get("photo_ids"):
            try:
                from .cia_photo_handler import transfer_photos_to_bid_card
                photo_transfer_result = await transfer_photos_to_bid_card(
                    bid_card_id, official_bid_card_id
                )
                if photo_transfer_result:
                    logger.info(f"Successfully transferred photos to official bid card {official_bid_card_id}")
            except Exception as photo_error:
                logger.error(f"Error transferring photos: {photo_error}")
        
        # Update potential bid card to mark as converted
        db.client.table("potential_bid_cards").update({
            "status": "converted",
            "converted_to_bid_card_id": official_bid_card_id,
            "ready_for_conversion": True,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", bid_card_id).execute()
        
        # Update conversation tracking
        db.client.table("cia_conversation_tracking").update({
            "status": "converted",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("potential_bid_card_id", bid_card_id).execute()
        
        logger.info(f"Successfully converted potential bid card {bid_card_id} to official bid card {official_bid_card['id']}")
        
        # Trigger contractor discovery pipeline
        campaign_error = False
        try:
            from agents.orchestration.enhanced_campaign_orchestrator import (
                EnhancedCampaignOrchestrator,
                CampaignRequest
            )
            
            # Calculate timeline in hours (default to 168 hours = 1 week if not specified)
            timeline_hours = 168  # Default 1 week
            if official_bid_card.get("urgency_level"):
                urgency_map = {
                    "emergency": 24,
                    "urgent": 72,
                    "week": 168,
                    "month": 720,
                    "flexible": 720
                }
                timeline_hours = urgency_map.get(official_bid_card["urgency_level"], 168)
            
            # Create campaign request
            campaign_request = CampaignRequest(
                bid_card_id=official_bid_card["id"],
                project_type=official_bid_card.get("project_type", "general"),
                location={
                    "city": official_bid_card.get("location_city"),
                    "state": official_bid_card.get("location_state"),
                    "zip": official_bid_card.get("location_zip")
                },
                timeline_hours=timeline_hours,
                urgency_level=official_bid_card.get("urgency_level", "week"),
                bids_needed=official_bid_card.get("contractor_count_needed", 4)
            )
            
            # Start contractor discovery asynchronously
            orchestrator = EnhancedCampaignOrchestrator()
            
            # Run in background - don't wait for completion
            import asyncio
            asyncio.create_task(orchestrator.create_intelligent_campaign(campaign_request))
            
            logger.info(f"Triggered contractor discovery for bid card {official_bid_card['id']}")
            
        except Exception as e:
            # Don't fail the conversion if orchestration fails
            logger.error(f"Failed to trigger contractor discovery: {e}")
            campaign_error = True
            # Continue - conversion was successful even if discovery didn't start
        
        return {
            "success": True,
            "potential_bid_card_id": bid_card_id,
            "official_bid_card_id": official_bid_card_id,
            "bid_card_id": official_bid_card_id,  # For backward compatibility
            "bid_card_number": official_bid_card.get("bid_card_number"),
            "status": "converted",
            "message": "Potential bid card successfully converted to official bid card",
            "contractor_discovery": "initiated" if not campaign_error else "failed to start"
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions as-is (like 400 auth errors)
        raise
    except Exception as e:
        logger.error(f"Error converting potential bid card {bid_card_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/potential-bid-cards/{bid_card_id}")
async def delete_potential_bid_card(bid_card_id: str):
    """
    Delete a potential bid card and its associated tracking data
    """
    try:
        logger.info(f"Deleting potential bid card {bid_card_id}")
        
        # Delete conversation tracking first (foreign key constraint)
        tracking_result = db.client.table("cia_conversation_tracking").delete().eq(
            "potential_bid_card_id", bid_card_id
        ).execute()
        
        # Delete the potential bid card
        result = db.client.table("potential_bid_cards").delete().eq("id", bid_card_id).execute()
        
        # Check if the operation succeeded by looking at the response
        # For DELETE operations, success means no exception was raised
        logger.info(f"Delete operation result: {result}")
        
        # Trust the DELETE operation if no exception was raised
        # Supabase returns 200 OK for successful DELETE operations
        
        logger.info(f"Successfully deleted potential bid card {bid_card_id}")
        
        return {
            "success": True,
            "message": "Potential bid card deleted successfully",
            "deleted_id": bid_card_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting potential bid card {bid_card_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def calculate_completion_percentage(bid_card_id: str) -> Dict[str, Any]:
    """
    Calculate completion percentage and determine if ready for conversion
    """
    try:
        # Get potential bid card
        result = db.client.table("potential_bid_cards").select("*").eq("id", bid_card_id).execute()
        
        if not result.data:
            return {"percentage": 0, "ready_for_conversion": False, "missing_fields": REQUIRED_FIELDS.copy()}
        
        bid_card = result.data[0]
        
        # Check required fields
        filled_required = 0
        missing_required = []
        
        for field in REQUIRED_FIELDS:
            value = bid_card.get(field)
            if value is not None and value != "" and value != []:
                filled_required += 1
            else:
                missing_required.append(field)
        
        # Check nice-to-have fields
        filled_nice_to_have = 0
        for field in NICE_TO_HAVE_FIELDS:
            value = bid_card.get(field)
            if value is not None and value != "" and value != []:
                filled_nice_to_have += 1
        
        # Calculate percentage
        total_fields = len(REQUIRED_FIELDS) + len(NICE_TO_HAVE_FIELDS)
        filled_fields = filled_required + filled_nice_to_have
        percentage = int((filled_fields / total_fields) * 100)
        
        # Ready for conversion if all required fields are filled
        ready_for_conversion = len(missing_required) == 0
        
        return {
            "percentage": percentage,
            "ready_for_conversion": ready_for_conversion,
            "missing_fields": missing_required,
            "filled_required": filled_required,
            "filled_optional": filled_nice_to_have
        }
        
    except Exception as e:
        logger.error(f"Error calculating completion percentage: {e}")
        return {"percentage": 0, "ready_for_conversion": False, "missing_fields": REQUIRED_FIELDS.copy()}

async def update_conversation_tracking(bid_card_id: str, field_name: str, completion_info: Dict[str, Any]):
    """
    Update conversation tracking with latest field update
    """
    try:
        tracking_data = {
            "last_field_updated": field_name,
            "completion_percentage": completion_info["percentage"],
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Update fields_collected with current status
        tracking_result = db.client.table("cia_conversation_tracking").select("fields_collected").eq("potential_bid_card_id", bid_card_id).execute()
        
        if tracking_result.data:
            fields_collected = tracking_result.data[0].get("fields_collected", {})
            fields_collected[field_name] = {
                "updated_at": datetime.utcnow().isoformat(),
                "source": "conversation"
            }
            tracking_data["fields_collected"] = fields_collected
        
        db.client.table("cia_conversation_tracking").update(tracking_data).eq("potential_bid_card_id", bid_card_id).execute()
        
    except Exception as e:
        logger.error(f"Error updating conversation tracking: {e}")
        # Don't fail the main operation if tracking fails
        pass