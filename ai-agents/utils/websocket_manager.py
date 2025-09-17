"""
WebSocket Manager for Real-time Agent Updates
Broadcasts agent activity events to connected clients
"""

import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and broadcasts agent activity"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store all connections for global broadcasts
        self.all_connections: Set[WebSocket] = set()
        
    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.all_connections.add(websocket)
        
        if user_id:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            
        logger.info(f"WebSocket connected for user: {user_id or 'anonymous'}")
        
        # Send connection confirmation
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str = None):
        """Remove a WebSocket connection"""
        self.all_connections.discard(websocket)
        
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
        logger.info(f"WebSocket disconnected for user: {user_id or 'anonymous'}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.all_connections.discard(websocket)
    
    async def send_user_message(self, message: dict, user_id: str):
        """Send message to all connections for a specific user"""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(conn, user_id)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        if not self.all_connections:
            return
            
        disconnected = []
        for connection in self.all_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.all_connections.discard(conn)
    
    async def broadcast_agent_activity(
        self,
        entity_type: str,
        entity_id: str,
        agent_name: str,
        action: str,
        status: str,
        changed_fields: list = None,
        user_id: str = None
    ):
        """Broadcast agent activity event"""
        event = {
            "type": "agent-activity",
            "entityType": entity_type,
            "entityId": entity_id,
            "agentName": agent_name,
            "action": action,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "changedFields": changed_fields or []
        }
        
        # Send to specific user if provided
        if user_id:
            await self.send_user_message(event, user_id)
        else:
            # Broadcast to all
            await self.broadcast(json.dumps(event))

# Global instance
websocket_manager = WebSocketManager()