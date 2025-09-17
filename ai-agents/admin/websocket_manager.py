"""
Admin Dashboard WebSocket Manager
Handles real-time connections for admin clients with authentication and broadcasting
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import WebSocket


logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types for admin dashboard"""
    BID_CARD_UPDATE = "bid_card_update"
    AGENT_STATUS = "agent_status"
    DATABASE_OPERATION = "database_operation"
    EMAIL_EVENT = "email_event"
    FORM_SUBMISSION = "form_submission"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_METRIC = "performance_metric"
    CAMPAIGN_UPDATE = "campaign_update"
    CONNECTION_STATUS = "connection_status"


class AdminWebSocketConnection:
    """Individual admin WebSocket connection"""

    def __init__(self, websocket: WebSocket, client_id: str, admin_user_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.admin_user_id = admin_user_id
        self.connected_at = datetime.now()
        self.last_ping = time.time()
        self.subscriptions: set[str] = set()

    async def send_message(self, message: dict) -> bool:
        """Send message to this connection"""
        try:
            await self.websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {self.client_id}: {e}")
            return False

    async def ping(self) -> bool:
        """Send ping to check connection health"""
        try:
            ping_message = {
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            }
            success = await self.send_message(ping_message)
            if success:
                self.last_ping = time.time()
            return success
        except Exception:
            return False


class AdminWebSocketManager:
    """Manages WebSocket connections for admin dashboard with real-time broadcasting"""

    def __init__(self):
        self.active_connections: dict[str, AdminWebSocketConnection] = {}
        self.message_queue: list[dict] = []
        self.max_queue_size = 1000
        self.ping_interval = 30  # seconds
        self.connection_timeout = 60  # seconds

        # Statistics
        self.messages_sent = 0
        self.connections_total = 0

    async def connect(self, websocket: WebSocket, client_id: str, admin_user_id: str) -> bool:
        """Register new admin WebSocket connection (already accepted)"""
        try:
            # WebSocket is already accepted in the route handler
            connection = AdminWebSocketConnection(websocket, client_id, admin_user_id)
            self.active_connections[client_id] = connection
            self.connections_total += 1

            # Send welcome message
            welcome_message = {
                "type": MessageType.CONNECTION_STATUS.value,
                "data": {
                    "status": "connected",
                    "client_id": client_id,
                    "admin_user_id": admin_user_id,
                    "connected_at": connection.connected_at.isoformat(),
                    "active_connections": len(self.active_connections)
                }
            }

            await connection.send_message(welcome_message)

            # Broadcast to other admins
            await self.broadcast_to_others({
                "type": MessageType.CONNECTION_STATUS.value,
                "data": {
                    "status": "admin_joined",
                    "admin_user_id": admin_user_id,
                    "active_connections": len(self.active_connections)
                }
            }, exclude_client=client_id)

            logger.info(f"Admin {admin_user_id} connected as {client_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect admin WebSocket {client_id}: {e}")
            return False

    async def disconnect(self, client_id: str) -> bool:
        """Remove admin WebSocket connection"""
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            admin_user_id = connection.admin_user_id

            # Remove connection
            del self.active_connections[client_id]

            # Broadcast to other admins
            await self.broadcast_to_others({
                "type": MessageType.CONNECTION_STATUS.value,
                "data": {
                    "status": "admin_left",
                    "admin_user_id": admin_user_id,
                    "active_connections": len(self.active_connections)
                }
            }, exclude_client=client_id)

            logger.info(f"Admin {admin_user_id} disconnected ({client_id})")
            return True

        return False

    async def broadcast_message(self, message_type: MessageType, data: dict,
                              target_subscription: Optional[str] = None) -> int:
        """Broadcast message to all connected admin clients"""
        message = {
            "type": message_type.value,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        # Add to message queue for debugging
        self.message_queue.append(message)
        if len(self.message_queue) > self.max_queue_size:
            self.message_queue.pop(0)

        sent_count = 0
        failed_connections = []

        # Use list() to create a snapshot of items to avoid iteration issues
        for client_id, connection in list(self.active_connections.items()):
            # Check subscription filter
            if target_subscription and target_subscription not in connection.subscriptions:
                continue

            success = await connection.send_message(message)
            if success:
                sent_count += 1
                self.messages_sent += 1
            else:
                failed_connections.append(client_id)

        # Clean up failed connections safely
        for client_id in failed_connections:
            logger.error(f"Failed to send message to {client_id}")
            await self.disconnect(client_id)

        return sent_count

    async def broadcast_to_others(self, message: dict, exclude_client: str) -> int:
        """Broadcast message to all admin clients except one"""
        sent_count = 0
        failed_connections = []

        for client_id, connection in self.active_connections.items():
            if client_id == exclude_client:
                continue

            success = await connection.send_message(message)
            if success:
                sent_count += 1
            else:
                failed_connections.append(client_id)

        # Clean up failed connections
        for client_id in failed_connections:
            await self.disconnect(client_id)

        return sent_count

    async def subscribe_client(self, client_id: str, subscription: str) -> bool:
        """Add subscription filter for client"""
        if client_id in self.active_connections:
            self.active_connections[client_id].subscriptions.add(subscription)
            logger.info(f"Client {client_id} subscribed to {subscription}")
            return True
        return False

    async def unsubscribe_client(self, client_id: str, subscription: str) -> bool:
        """Remove subscription filter for client"""
        if client_id in self.active_connections:
            self.active_connections[client_id].subscriptions.discard(subscription)
            logger.info(f"Client {client_id} unsubscribed from {subscription}")
            return True
        return False

    async def send_to_client(self, client_id: str, message_type: MessageType, data: dict) -> bool:
        """Send message to specific admin client"""
        if client_id in self.active_connections:
            message = {
                "type": message_type.value,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            return await self.active_connections[client_id].send_message(message)

        return False

    async def health_check(self) -> dict:
        """Check health of all connections and clean up stale ones"""
        current_time = time.time()
        stale_connections = []
        healthy_connections = 0

        for client_id, connection in self.active_connections.items():
            # Check if connection is stale
            if current_time - connection.last_ping > self.connection_timeout:
                stale_connections.append(client_id)
            else:
                # Ping active connections
                ping_success = await connection.ping()
                if ping_success:
                    healthy_connections += 1
                else:
                    stale_connections.append(client_id)

        # Clean up stale connections
        for client_id in stale_connections:
            await self.disconnect(client_id)

        return {
            "active_connections": len(self.active_connections),
            "healthy_connections": healthy_connections,
            "cleaned_up": len(stale_connections),
            "total_messages_sent": self.messages_sent,
            "total_connections": self.connections_total
        }

    def get_connection_stats(self) -> dict:
        """Get WebSocket connection statistics"""
        return {
            "active_connections": len(self.active_connections),
            "total_connections": self.connections_total,
            "messages_sent": self.messages_sent,
            "queue_size": len(self.message_queue),
            "connections": [
                {
                    "client_id": client_id,
                    "admin_user_id": conn.admin_user_id,
                    "connected_at": conn.connected_at.isoformat(),
                    "last_ping": conn.last_ping,
                    "subscriptions": list(conn.subscriptions)
                }
                for client_id, conn in self.active_connections.items()
            ]
        }

    async def broadcast_bid_card_update(self, bid_card_id: str, status: str,
                                      progress: dict, additional_data: dict = None):
        """Convenience method for bid card updates"""
        data = {
            "bid_card_id": bid_card_id,
            "status": status,
            "progress": progress,
            **(additional_data or {})
        }

        return await self.broadcast_message(MessageType.BID_CARD_UPDATE, data)

    async def broadcast_agent_status(self, agent_name: str, status: str,
                                   response_time: float, additional_data: dict = None):
        """Convenience method for agent status updates"""
        data = {
            "agent": agent_name,
            "status": status,
            "response_time": response_time,
            "last_activity": datetime.now().isoformat(),
            **(additional_data or {})
        }

        return await self.broadcast_message(MessageType.AGENT_STATUS, data)

    async def broadcast_system_alert(self, alert_type: str, message: str,
                                   severity: str = "warning", additional_data: dict = None):
        """Convenience method for system alerts"""
        data = {
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            **(additional_data or {})
        }

        return await self.broadcast_message(MessageType.SYSTEM_ALERT, data)

    async def broadcast_database_operation(self, operation: str, table: str,
                                         record_id: str, additional_data: dict = None):
        """Convenience method for database operation updates"""
        data = {
            "operation": operation,
            "table": table,
            "record_id": record_id,
            "timestamp": datetime.now().isoformat(),
            **(additional_data or {})
        }

        return await self.broadcast_message(MessageType.DATABASE_OPERATION, data)

    async def broadcast_to_all(self, message: dict) -> int:
        """Broadcast message to all connected admin clients (compatibility method)"""
        # Extract message type from the message
        message_type = message.get("type", "system_alert")
        data = message.get("data", {})

        # Map string type to MessageType enum if possible
        try:
            msg_type = MessageType(message_type)
        except ValueError:
            # Default to system alert if type not recognized
            msg_type = MessageType.SYSTEM_ALERT

        return await self.broadcast_message(msg_type, data)


# Global WebSocket manager instance
admin_websocket_manager = AdminWebSocketManager()


async def start_websocket_health_check():
    """Background task to periodically check WebSocket health"""
    while True:
        try:
            health_stats = await admin_websocket_manager.health_check()
            logger.info(f"WebSocket health check: {health_stats}")

            # Broadcast health stats to admin clients
            await admin_websocket_manager.broadcast_message(
                MessageType.PERFORMANCE_METRIC,
                {
                    "metric_type": "websocket_health",
                    "data": health_stats
                }
            )

        except Exception as e:
            logger.error(f"WebSocket health check failed: {e}")

        # Wait before next check
        await asyncio.sleep(admin_websocket_manager.ping_interval)


# Usage example for integration
async def example_usage():
    """Example of how to use the WebSocket manager"""

    # Broadcast bid card update
    await admin_websocket_manager.broadcast_bid_card_update(
        bid_card_id="bc-12345",
        status="collecting_bids",
        progress={"current": 2, "target": 5, "percentage": 40}
    )

    # Broadcast agent status
    await admin_websocket_manager.broadcast_agent_status(
        agent_name="CIA",
        status="online",
        response_time=0.8
    )

    # Broadcast system alert
    await admin_websocket_manager.broadcast_system_alert(
        alert_type="agent_failure",
        message="EAA Agent is not responding",
        severity="error"
    )
