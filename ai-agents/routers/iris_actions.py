"""
IRIS Agent Action Endpoints
These endpoints allow IRIS to perform real-time UI updates
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
import asyncio
from database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/iris/actions", tags=["iris-actions"])

class AgentAction(BaseModel):
    """Base model for agent actions"""
    request_id: str  # For idempotency
    agent_name: str = "IRIS"
    user_id: Optional[str] = None
    
class AddRepairItem(AgentAction):
    """Add a repair item to a bid card"""
    bid_card_id: str
    item: Dict[str, Any]
    
class UpdateBidCard(AgentAction):
    """Update bid card fields"""
    bid_card_id: str
    updates: Dict[str, Any]
    
class UpdatePotentialBidCard(AgentAction):
    """Update potential bid card fields"""
    potential_bid_card_id: str
    field_updates: Dict[str, Any]

class CreateBidCard(AgentAction):
    """Create a new bid card from scratch"""
    property_id: str
    bid_card_data: Dict[str, Any]

# Track processed requests for idempotency
processed_requests = set()

async def emit_agent_activity(
    entity_type: str,
    entity_id: str,
    agent_name: str,
    action: str,
    status: str,
    changed_fields: Optional[List[str]] = None,
    user_id: Optional[str] = None
):
    """Emit agent activity event for UI visualization via WebSocket"""
    # TEMPORARILY DISABLED: WebSocket causing hangs
    logger.info(f"Agent Activity: {agent_name} {status} {action} on {entity_type}:{entity_id}")
    
    # TODO: Fix WebSocket manager deadlock issue
    # from utils.websocket_manager import websocket_manager
    # await websocket_manager.broadcast_agent_activity(
    #     entity_type=entity_type,
    #     entity_id=entity_id,
    #     agent_name=agent_name,
    #     action=action,
    #     status=status,
    #     changed_fields=changed_fields,
    #     user_id=user_id
    # )

@router.post("/add-repair-item")
async def add_repair_item(request: AddRepairItem):
    """
    IRIS adds a repair item to a bid card
    Shows real-time UI updates with glowing effects
    """
    # Idempotency check
    if request.request_id in processed_requests:
        return {"status": "already_processed", "request_id": request.request_id}
    
    # Using global db instance
    
    try:
        # Emit "working" status
        await emit_agent_activity(
            entity_type="bid_card",
            entity_id=request.bid_card_id,
            agent_name="IRIS",
            action="adding_repair_item",
            status="working"
        )
        
        # Simulate processing time for visual effect
        await asyncio.sleep(1.5)
        
        # Get current bid card
        result = db.client.table('bid_cards').select('*').eq('id', request.bid_card_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Bid card not found")
            
        bid_card = result.data
        
        # Add the repair item
        new_item = {
            "id": f"item_{datetime.utcnow().timestamp()}",
            "bid_card_id": request.bid_card_id,
            "description": request.item.get("description"),
            "severity": request.item.get("severity", "medium"),
            "category": request.item.get("category"),
            "estimated_cost": request.item.get("estimated_cost"),
            "created_by": "IRIS",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insert into bid_card_items
        db.client.table('bid_card_items').insert(new_item).execute()
        
        # Update bid card modified timestamp
        db.client.table('bid_cards').update({
            "updated_at": datetime.utcnow().isoformat()
        }).eq('id', request.bid_card_id).execute()
        
        # Mark request as processed
        processed_requests.add(request.request_id)
        
        # Emit "completed" status
        await emit_agent_activity(
            entity_type="bid_card",
            entity_id=request.bid_card_id,
            agent_name="IRIS",
            action="added_repair_item",
            status="completed",
            changed_fields=["items"]
        )
        
        # Audit trail
        audit_entry = {
            "action": "add_repair_item",
            "agent": "IRIS",
            "entity_type": "bid_card",
            "entity_id": request.bid_card_id,
            "payload": request.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        db.client.table('agent_actions').insert(audit_entry).execute()
        
        return {
            "status": "success",
            "message": f"Added repair item to bid card",
            "item": new_item,
            "request_id": request.request_id
        }
        
    except Exception as e:
        # Emit error status
        await emit_agent_activity(
            entity_type="bid_card",
            entity_id=request.bid_card_id,
            agent_name="IRIS",
            action="add_repair_item_failed",
            status="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-bid-card")
async def update_bid_card(request: UpdateBidCard):
    """
    IRIS updates bid card fields
    Supports updating budget, timeline, urgency, etc.
    """
    if request.request_id in processed_requests:
        return {"status": "already_processed", "request_id": request.request_id}
    
    # Using global db instance
    
    try:
        # Emit working status
        await emit_agent_activity(
            entity_type="bid_card",
            entity_id=request.bid_card_id,
            agent_name="IRIS",
            action="updating_bid_card",
            status="working"
        )
        
        # Visual processing delay
        await asyncio.sleep(1.5)
        
        # Prepare updates
        updates = request.updates.copy()
        updates["updated_at"] = datetime.utcnow().isoformat()
        # Note: last_modified_by column doesn't exist in current schema
        
        # Update the bid card
        result = db.client.table('bid_cards').update(updates).eq('id', request.bid_card_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Bid card not found")
        
        # Mark as processed
        processed_requests.add(request.request_id)
        
        # Emit completed status with changed fields
        changed_fields = list(request.updates.keys())
        await emit_agent_activity(
            entity_type="bid_card",
            entity_id=request.bid_card_id,
            agent_name="IRIS",
            action="updated_bid_card",
            status="completed",
            changed_fields=changed_fields
        )
        
        # Audit trail
        audit_entry = {
            "action": "update_bid_card",
            "agent": "IRIS",
            "entity_type": "bid_card",
            "entity_id": request.bid_card_id,
            "payload": request.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        db.client.table('agent_actions').insert(audit_entry).execute()
        
        return {
            "status": "success",
            "message": f"Updated bid card fields: {', '.join(changed_fields)}",
            "updated_data": result.data[0],
            "request_id": request.request_id
        }
        
    except Exception as e:
        await emit_agent_activity(
            entity_type="bid_card",
            entity_id=request.bid_card_id,
            agent_name="IRIS",
            action="update_failed",
            status="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-potential-bid-card")
async def update_potential_bid_card(request: UpdatePotentialBidCard):
    """
    IRIS updates potential bid card fields during conversation
    """
    if request.request_id in processed_requests:
        return {"status": "already_processed", "request_id": request.request_id}
    
    # Using global db instance
    
    try:
        # Emit working status
        await emit_agent_activity(
            entity_type="potential_bid_card",
            entity_id=request.potential_bid_card_id,
            agent_name="IRIS",
            action="updating_potential_bid_card",
            status="working"
        )
        
        await asyncio.sleep(1)
        
        # Update potential bid card
        updates = request.field_updates.copy()
        updates["updated_at"] = datetime.utcnow().isoformat()
        # Don't set updated_by as it doesn't exist in schema
        
        result = db.client.table('potential_bid_cards').update(updates).eq('id', request.potential_bid_card_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Potential bid card not found")
        
        processed_requests.add(request.request_id)
        
        # Emit completed
        await emit_agent_activity(
            entity_type="potential_bid_card",
            entity_id=request.potential_bid_card_id,
            agent_name="IRIS",
            action="updated_potential_bid_card",
            status="completed",
            changed_fields=list(request.field_updates.keys())
        )
        
        return {
            "status": "success",
            "message": "Updated potential bid card",
            "updated_fields": list(request.field_updates.keys()),
            "request_id": request.request_id
        }
        
    except Exception as e:
        await emit_agent_activity(
            entity_type="potential_bid_card",
            entity_id=request.potential_bid_card_id,
            agent_name="IRIS",
            action="update_failed",
            status="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-bid-card")
async def create_bid_card(request: CreateBidCard):
    """
    IRIS creates a new bid card from scratch
    """
    if request.request_id in processed_requests:
        return {"status": "already_processed", "request_id": request.request_id}
    
    # Using global db instance
    
    try:
        # Emit working status (no entity ID yet)
        await emit_agent_activity(
            entity_type="bid_card",
            entity_id="new",
            agent_name="IRIS",
            action="creating_bid_card",
            status="working"
        )
        
        await asyncio.sleep(2)  # Longer for creation
        
        # Create the bid card
        bid_card_data = request.bid_card_data.copy()
        bid_card_data["property_id"] = request.property_id
        bid_card_data["created_by"] = "IRIS"
        bid_card_data["created_at"] = datetime.utcnow().isoformat()
        bid_card_data["status"] = "draft"
        
        result = db.client.table('bid_cards').insert(bid_card_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create bid card")
        
        new_bid_card = result.data[0]
        processed_requests.add(request.request_id)
        
        # Emit completed with actual ID
        await emit_agent_activity(
            entity_type="bid_card",
            entity_id=new_bid_card["id"],
            agent_name="IRIS",
            action="created_bid_card",
            status="completed"
        )
        
        return {
            "status": "success",
            "message": "Created new bid card",
            "bid_card": new_bid_card,
            "request_id": request.request_id
        }
        
    except Exception as e:
        await emit_agent_activity(
            entity_type="bid_card",
            entity_id="new",
            agent_name="IRIS",
            action="create_failed",
            status="error"
        )
        raise HTTPException(status_code=500, detail=str(e))