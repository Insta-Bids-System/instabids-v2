"""
WebSocket Routes - Real-time Communication Endpoints
Owner: Shared (Used by multiple agents)
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from utils.websocket_manager import websocket_manager
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.websocket("/ws/realtime")
async def websocket_realtime_proxy(websocket: WebSocket):
    """Proxy WebSocket connection to OpenAI Realtime API with authentication"""
    from routes.realtime_proxy import websocket_endpoint
    await websocket_endpoint(websocket)

@router.websocket("/ws/agent-activity")
async def websocket_agent_activity(websocket: WebSocket):
    """WebSocket endpoint for real-time agent activity updates"""
    user_id = websocket.query_params.get("user_id")
    # The websocket_manager.connect() method handles accepting the connection
    await websocket_manager.connect(websocket, user_id)
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Echo back for connection testing
            await websocket_manager.send_personal_message({
                "type": "echo",
                "data": data
            }, websocket)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user_id)
        logger.info(f"Agent activity WebSocket disconnected for user: {user_id}")
