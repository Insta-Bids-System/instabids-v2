"""
OpenAI Realtime API WebSocket Proxy

This proxy handles authentication for the browser client since browser WebSocket
doesn't support custom headers.
"""

import asyncio
import logging
import os
import traceback
from typing import Optional

import websockets
import websockets.client
from fastapi import WebSocket, WebSocketDisconnect


logger = logging.getLogger(__name__)

class RealtimeProxy:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.openai_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.client_ws: Optional[WebSocket] = None

    async def connect_to_openai(self, model: str = "gpt-4o-realtime-preview-2024-12-17"):
        """Connect to OpenAI Realtime API with authentication"""
        uri = f"wss://api.openai.com/v1/realtime?model={model}"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "OpenAI-Beta": "realtime=v1"
        }

        try:
            self.openai_ws = await websockets.connect(uri, extra_headers=headers)
            logger.info("Connected to OpenAI Realtime API")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI: {e}")
            return False

    async def handle_openai_to_client(self):
        """Forward messages from OpenAI to client"""
        try:
            async for message in self.openai_ws:
                if self.client_ws:
                    await self.client_ws.send_text(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("OpenAI connection closed")
        except Exception as e:
            logger.error(f"Error forwarding from OpenAI: {e}")

    async def handle_client_to_openai(self):
        """Forward messages from client to OpenAI"""
        try:
            while True:
                message = await self.client_ws.receive_text()
                if self.openai_ws:
                    await self.openai_ws.send(message)
        except WebSocketDisconnect:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"Error forwarding to OpenAI: {e}")

    async def handle_connection(self, websocket: WebSocket):
        """Handle a client WebSocket connection"""
        logger.info("Client connected to WebSocket proxy")
        self.client_ws = websocket
        await websocket.accept()
        logger.info("WebSocket accepted")

        # Connect to OpenAI
        if not await self.connect_to_openai():
            logger.error("Failed to connect to OpenAI")
            await websocket.close(code=1011, reason="Failed to connect to OpenAI")
            return

        # Create tasks for bidirectional message forwarding
        openai_task = asyncio.create_task(self.handle_openai_to_client())
        client_task = asyncio.create_task(self.handle_client_to_openai())

        try:
            # Wait for either task to complete (connection closed)
            done, pending = await asyncio.wait(
                [openai_task, client_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()

        finally:
            # Clean up connections
            if self.openai_ws:
                await self.openai_ws.close()
            if self.client_ws:
                await self.client_ws.close()

# Create a singleton proxy instance
realtime_proxy = RealtimeProxy()

async def websocket_endpoint(websocket: WebSocket):
    """FastAPI WebSocket endpoint for Realtime API proxy"""
    try:
        proxy = RealtimeProxy()  # Create new instance for each connection
        await proxy.handle_connection(websocket)
    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")
        logger.error(traceback.format_exc())
        await websocket.close(code=1011, reason=str(e))
