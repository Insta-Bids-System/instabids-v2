"""
Contractor WebSocket Routes - Real-time Notifications for Contractors
Handles bid card change notifications and other real-time updates
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from database_simple import db

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active contractor connections
contractor_connections: Dict[str, Set[WebSocket]] = {}
connection_lock = asyncio.Lock()


class ContractorWebSocketManager:
    """Manages WebSocket connections for contractors"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_lock = asyncio.Lock()
    
    async def connect(self, contractor_id: str, websocket: WebSocket):
        """Add a new contractor WebSocket connection"""
        await websocket.accept()
        
        async with self.connection_lock:
            if contractor_id not in self.active_connections:
                self.active_connections[contractor_id] = set()
            self.active_connections[contractor_id].add(websocket)
        
        logger.info(f"Contractor {contractor_id} connected via WebSocket")
        
        # Send initial connection confirmation
        await self.send_personal_message(
            contractor_id,
            {
                "type": "connection_established",
                "contractor_id": contractor_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Send any pending notifications
        await self.send_pending_notifications(contractor_id)
    
    async def disconnect(self, contractor_id: str, websocket: WebSocket):
        """Remove a contractor WebSocket connection"""
        async with self.connection_lock:
            if contractor_id in self.active_connections:
                self.active_connections[contractor_id].discard(websocket)
                if not self.active_connections[contractor_id]:
                    del self.active_connections[contractor_id]
        
        logger.info(f"Contractor {contractor_id} disconnected from WebSocket")
    
    async def send_personal_message(self, contractor_id: str, message: dict):
        """Send a message to all connections for a specific contractor"""
        if contractor_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[contractor_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to contractor {contractor_id}: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected websockets
            if disconnected:
                async with self.connection_lock:
                    self.active_connections[contractor_id] -= disconnected
                    if not self.active_connections[contractor_id]:
                        del self.active_connections[contractor_id]
    
    async def send_pending_notifications(self, contractor_id: str):
        """Send all unread notifications to a contractor"""
        try:
            # Get contractor_lead_id if exists
            lead_result = db.client.table("contractor_leads")\
                .select("id")\
                .eq("contractor_id", contractor_id)\
                .limit(1)\
                .execute()
            
            contractor_lead_id = lead_result.data[0]["id"] if lead_result.data else None
            
            # Get unread notifications
            query = db.client.table("notifications")\
                .select("*")\
                .eq("is_read", False)\
                .order("created_at", desc=True)
            
            # Add contractor filters
            if contractor_lead_id:
                query = query.or_(f"contractor_id.eq.{contractor_lead_id},metadata->>contractor_id.eq.{contractor_id}")
            else:
                query = query.eq("metadata->>contractor_id", contractor_id)
            
            notifications_result = query.execute()
            
            if notifications_result.data:
                for notification in notifications_result.data:
                    # Format notification for WebSocket
                    ws_message = {
                        "type": "notification",
                        "notification": {
                            "id": notification["id"],
                            "title": notification["title"],
                            "message": notification["message"],
                            "notification_type": notification.get("metadata", {}).get("notification_type", "general"),
                            "bid_card_id": notification.get("metadata", {}).get("bid_card_id"),
                            "action_url": notification.get("action_url"),
                            "created_at": notification["created_at"],
                            "is_read": notification["is_read"]
                        }
                    }
                    
                    await self.send_personal_message(contractor_id, ws_message)
                
                logger.info(f"Sent {len(notifications_result.data)} pending notifications to contractor {contractor_id}")
        
        except Exception as e:
            logger.error(f"Error sending pending notifications to {contractor_id}: {e}")
    
    async def broadcast_bid_card_change(self, bid_card_id: str, engaged_contractors: list, change_details: dict):
        """Broadcast bid card change notification to engaged contractors"""
        message = {
            "type": "bid_card_change",
            "bid_card_id": bid_card_id,
            "change_type": change_details.get("change_type", "update"),
            "description": change_details.get("description", "Bid card has been updated"),
            "timestamp": datetime.now().isoformat(),
            "action_url": f"/bid-cards/{bid_card_id}"
        }
        
        # Send to each engaged contractor
        for contractor_id in engaged_contractors:
            await self.send_personal_message(contractor_id, message)
        
        logger.info(f"Broadcast bid card change for {bid_card_id} to {len(engaged_contractors)} contractors")
    
    async def mark_notification_read(self, contractor_id: str, notification_id: str):
        """Mark a notification as read and send confirmation"""
        try:
            # Update notification in database
            result = db.client.table("notifications")\
                .update({"is_read": True, "read_at": datetime.now().isoformat()})\
                .eq("id", notification_id)\
                .execute()
            
            if result.data:
                # Send confirmation to contractor
                await self.send_personal_message(
                    contractor_id,
                    {
                        "type": "notification_marked_read",
                        "notification_id": notification_id,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                return True
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {e}")
        
        return False


# Create global manager instance
contractor_ws_manager = ContractorWebSocketManager()


@router.websocket("/ws/contractor/{contractor_id}")
async def contractor_websocket_endpoint(
    websocket: WebSocket,
    contractor_id: str
):
    """WebSocket endpoint for contractor real-time notifications"""
    await contractor_ws_manager.connect(contractor_id, websocket)
    
    try:
        while True:
            # Receive messages from contractor
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "ping":
                # Respond to ping with pong
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif data.get("type") == "mark_read":
                # Mark notification as read
                notification_id = data.get("notification_id")
                if notification_id:
                    await contractor_ws_manager.mark_notification_read(
                        contractor_id, 
                        notification_id
                    )
            
            elif data.get("type") == "subscribe":
                # Subscribe to specific bid card updates
                bid_card_id = data.get("bid_card_id")
                if bid_card_id:
                    # Store subscription (would need additional tracking)
                    await websocket.send_json({
                        "type": "subscribed",
                        "bid_card_id": bid_card_id,
                        "timestamp": datetime.now().isoformat()
                    })
            
    except WebSocketDisconnect:
        await contractor_ws_manager.disconnect(contractor_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for contractor {contractor_id}: {e}")
        await contractor_ws_manager.disconnect(contractor_id, websocket)


@router.get("/ws/contractor/{contractor_id}/status")
async def get_contractor_ws_status(contractor_id: str):
    """Check if a contractor has active WebSocket connections"""
    is_connected = contractor_id in contractor_ws_manager.active_connections
    connection_count = len(contractor_ws_manager.active_connections.get(contractor_id, set()))
    
    return {
        "contractor_id": contractor_id,
        "is_connected": is_connected,
        "connection_count": connection_count,
        "timestamp": datetime.now().isoformat()
    }


# Helper function to notify contractors from other parts of the system
async def notify_contractor_realtime(contractor_id: str, notification: dict):
    """Send a real-time notification to a contractor if they're connected"""
    await contractor_ws_manager.send_personal_message(contractor_id, {
        "type": "notification",
        "notification": notification
    })


# Helper function to broadcast bid card changes
async def broadcast_bid_card_change_to_contractors(bid_card_id: str, engaged_contractors: list, change_details: dict):
    """Broadcast bid card change to all engaged contractors"""
    await contractor_ws_manager.broadcast_bid_card_change(
        bid_card_id,
        engaged_contractors,
        change_details
    )