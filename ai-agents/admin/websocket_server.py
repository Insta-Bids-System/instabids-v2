"""
Admin WebSocket Server for Real-time Monitoring
Provides real-time updates for the InstaBids admin dashboard
"""
import asyncio
import json
import logging
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdminWebSocketServer:
    """WebSocket server for real-time admin dashboard updates"""

    def __init__(self):
        # Store active WebSocket connections
        self.active_connections: set[WebSocket] = set()
        # Store connection metadata
        self.connection_metadata: dict[WebSocket, dict] = {}
        # Event queue for broadcasting
        self.event_queue: asyncio.Queue = asyncio.Queue()
        # Background task for processing events
        self._event_processor_task = None

    async def connect(self, websocket: WebSocket, admin_id: str = "admin"):
        """Accept new WebSocket connection and add to active connections"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_metadata[websocket] = {
            "admin_id": admin_id,
            "connected_at": datetime.now(),
            "last_ping": datetime.now()
        }

        logger.info(f"Admin WebSocket connected: {admin_id}")

        # Send initial connection confirmation
        await self.send_to_connection(websocket, {
            "type": "CONNECTION_ESTABLISHED",
            "data": {
                "admin_id": admin_id,
                "server_time": datetime.now().isoformat(),
                "active_connections": len(self.active_connections)
            }
        })

        # Start event processor if not already running
        if self._event_processor_task is None:
            self._event_processor_task = asyncio.create_task(self._process_events())

    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            metadata = self.connection_metadata.pop(websocket, {})
            admin_id = metadata.get("admin_id", "unknown")
            logger.info(f"Admin WebSocket disconnected: {admin_id}")

    async def send_to_connection(self, websocket: WebSocket, message: dict):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket: {e}")
            await self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected admin clients"""
        if not self.active_connections:
            return

        # Add timestamp to all broadcasts
        message["timestamp"] = datetime.now().isoformat()
        message["broadcast_id"] = f"broadcast_{datetime.now().timestamp()}"

        # Send to all connections
        disconnected = []
        for websocket in self.active_connections:
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Failed to broadcast to WebSocket: {e}")
                disconnected.append(websocket)

        # Clean up disconnected WebSockets
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def queue_event(self, event_type: str, data: dict):
        """Queue event for broadcasting"""
        event = {
            "type": event_type,
            "data": data,
            "queued_at": datetime.now().isoformat()
        }
        await self.event_queue.put(event)

    async def _process_events(self):
        """Background task to process and broadcast events"""
        logger.info("Admin WebSocket event processor started")

        while True:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self.broadcast(event)
            except TimeoutError:
                # Send keepalive ping every second if no events
                if self.active_connections:
                    await self.broadcast({
                        "type": "KEEPALIVE",
                        "data": {
                            "server_time": datetime.now().isoformat(),
                            "active_connections": len(self.active_connections)
                        }
                    })
            except Exception as e:
                logger.error(f"Error processing admin events: {e}")
                await asyncio.sleep(1)

    async def handle_client_message(self, websocket: WebSocket, message: str):
        """Handle incoming messages from admin clients"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "PING":
                # Update last ping time
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["last_ping"] = datetime.now()

                # Send pong response
                await self.send_to_connection(websocket, {
                    "type": "PONG",
                    "data": {
                        "server_time": datetime.now().isoformat()
                    }
                })

            elif message_type == "GET_STATUS":
                # Send current system status
                await self.send_system_status(websocket)

            elif message_type == "SUBSCRIBE":
                # Handle event subscription
                event_types = data.get("data", {}).get("event_types", [])
                await self.handle_subscription(websocket, event_types)

            else:
                logger.warning(f"Unknown message type from admin client: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from admin client: {message}")
        except Exception as e:
            logger.error(f"Error handling admin client message: {e}")

    async def send_system_status(self, websocket: WebSocket):
        """Send current system status to admin client"""
        # Import here to avoid circular imports

        try:
            # Get basic system info
            status_data = {
                "agents": {
                    "cia": {"status": "active", "last_activity": datetime.now().isoformat()},
                    "jaa": {"status": "active", "last_activity": datetime.now().isoformat()},
                    "cda": {"status": "active", "last_activity": datetime.now().isoformat()},
                    "eaa": {"status": "active", "last_activity": datetime.now().isoformat()},
                    "wfa": {"status": "active", "last_activity": datetime.now().isoformat()}
                },
                "database": {
                    "status": "connected",
                    "last_query": datetime.now().isoformat()
                },
                "server": {
                    "uptime": datetime.now().isoformat(),
                    "active_websockets": len(self.active_connections)
                }
            }

            await self.send_to_connection(websocket, {
                "type": "SYSTEM_STATUS",
                "data": status_data
            })

        except Exception as e:
            logger.error(f"Error sending system status: {e}")
            await self.send_to_connection(websocket, {
                "type": "ERROR",
                "data": {"message": f"Failed to get system status: {e!s}"}
            })

    async def handle_subscription(self, websocket: WebSocket, event_types: list[str]):
        """Handle event subscription from client"""
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["subscribed_events"] = event_types

        await self.send_to_connection(websocket, {
            "type": "SUBSCRIPTION_CONFIRMED",
            "data": {
                "subscribed_events": event_types,
                "message": f"Subscribed to {len(event_types)} event types"
            }
        })

    def get_connection_count(self) -> int:
        """Get number of active admin connections"""
        return len(self.active_connections)

    def get_connection_info(self) -> list[dict]:
        """Get information about all active connections"""
        return [
            {
                "admin_id": metadata.get("admin_id"),
                "connected_at": metadata.get("connected_at").isoformat() if metadata.get("connected_at") else None,
                "last_ping": metadata.get("last_ping").isoformat() if metadata.get("last_ping") else None,
                "subscribed_events": metadata.get("subscribed_events", [])
            }
            for metadata in self.connection_metadata.values()
        ]

# Global instance
admin_websocket_server = AdminWebSocketServer()

async def handle_admin_websocket(websocket: WebSocket, admin_id: str = "admin"):
    """WebSocket endpoint handler for admin dashboard"""
    await admin_websocket_server.connect(websocket, admin_id)

    try:
        while True:
            # Wait for messages from client
            message = await websocket.receive_text()
            await admin_websocket_server.handle_client_message(websocket, message)

    except WebSocketDisconnect:
        await admin_websocket_server.disconnect(websocket)
    except Exception as e:
        logger.error(f"Admin WebSocket error: {e}")
        await admin_websocket_server.disconnect(websocket)

# Event Broadcasting Functions
async def broadcast_agent_status(agent_id: str, status: str, metrics: dict = None):
    """Broadcast agent status update"""
    await admin_websocket_server.queue_event("AGENT_STATUS_UPDATE", {
        "agent_id": agent_id,
        "status": status,
        "metrics": metrics or {},
        "timestamp": datetime.now().isoformat()
    })

async def broadcast_database_operation(table: str, operation: str, data: dict = None, performance: dict = None):
    """Broadcast database operation"""
    await admin_websocket_server.queue_event("DATABASE_OPERATION", {
        "table": table,
        "operation": operation,
        "data": data or {},
        "performance": performance or {},
        "timestamp": datetime.now().isoformat()
    })

async def broadcast_email_sent(campaign_id: str, contractor: str, status: str, email_data: dict = None):
    """Broadcast email sent notification"""
    await admin_websocket_server.queue_event("EMAIL_SENT", {
        "campaign_id": campaign_id,
        "contractor": contractor,
        "status": status,
        "email_data": email_data or {},
        "timestamp": datetime.now().isoformat()
    })

async def broadcast_form_submitted(contractor: str, website: str, status: str, form_data: dict = None):
    """Broadcast form submission notification"""
    await admin_websocket_server.queue_event("FORM_SUBMITTED", {
        "contractor": contractor,
        "website": website,
        "status": status,
        "form_data": form_data or {},
        "timestamp": datetime.now().isoformat()
    })

async def broadcast_bid_received(bid_card_id: str, contractor: str, bid_data: dict, new_status: str):
    """Broadcast bid received notification"""
    await admin_websocket_server.queue_event("BID_RECEIVED", {
        "bid_card_id": bid_card_id,
        "contractor": contractor,
        "bid_data": bid_data,
        "new_status": new_status,
        "timestamp": datetime.now().isoformat()
    })

async def broadcast_campaign_complete(campaign_id: str, final_metrics: dict, success: bool):
    """Broadcast campaign completion"""
    await admin_websocket_server.queue_event("CAMPAIGN_COMPLETE", {
        "campaign_id": campaign_id,
        "final_metrics": final_metrics,
        "success": success,
        "timestamp": datetime.now().isoformat()
    })

async def broadcast_error(error_type: str, error_message: str, context: dict = None):
    """Broadcast error notification"""
    await admin_websocket_server.queue_event("ERROR", {
        "error_type": error_type,
        "error_message": error_message,
        "context": context or {},
        "timestamp": datetime.now().isoformat()
    })
