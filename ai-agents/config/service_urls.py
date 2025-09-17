"""
Centralized service URL configuration for InstaBids backend.

This module provides a single source of truth for all backend service URLs,
preventing hardcoded URLs throughout the codebase and enabling easy
configuration changes between development, staging, and production environments.
"""

import os

# Get backend URL from environment variable or use default
# In Docker, this should be set to the container name
# In local development, this should be localhost
BACKEND_HOST = os.getenv("BACKEND_HOST", "localhost")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8008")
BACKEND_PROTOCOL = os.getenv("BACKEND_PROTOCOL", "http")

# Construct the base backend URL
BACKEND_URL = f"{BACKEND_PROTOCOL}://{BACKEND_HOST}:{BACKEND_PORT}"

# WebSocket URL for real-time connections
WS_PROTOCOL = "wss" if BACKEND_PROTOCOL == "https" else "ws"
WS_URL = f"{WS_PROTOCOL}://{BACKEND_HOST}:{BACKEND_PORT}"

# Service endpoints
class ServiceEndpoints:
    """Centralized service endpoints for all backend services."""
    
    # Base URLs
    API_BASE = f"{BACKEND_URL}/api"
    WS_BASE = f"{WS_URL}/ws"
    
    # CIA Agent endpoints
    CIA_STREAM = f"{API_BASE}/cia/stream"
    CIA_CHAT = f"{API_BASE}/cia/chat"
    CIA_POTENTIAL_BID_CARDS = f"{API_BASE}/cia/potential-bid-cards"
    
    # JAA Agent endpoints
    JAA_UPDATE = f"{API_BASE}/jaa/update"  # Append /{bid_card_id}
    JAA_PROCESS = f"{API_BASE}/jaa/process"
    
    # COIA Agent endpoints
    COIA_CHAT = f"{API_BASE}/coia/chat"
    COIA_LANDING = f"{API_BASE}/coia/landing"
    COIA_STATE = f"{API_BASE}/coia/state"
    
    # Messaging endpoints
    MESSAGING_SEND = f"{API_BASE}/messaging/send"
    MESSAGING_FILTER = f"{API_BASE}/messaging/filter"
    
    # WebSocket endpoints
    WS_ADMIN = f"{WS_BASE}/admin"
    WS_AGENT_ACTIVITY = f"{WS_BASE}/agent-activity"
    
    @classmethod
    def get_jaa_update_url(cls, bid_card_id: str) -> str:
        """Get the JAA update URL for a specific bid card."""
        return f"{cls.JAA_UPDATE}/{bid_card_id}"
    
    @classmethod
    def get_backend_url(cls) -> str:
        """Get the base backend URL."""
        return BACKEND_URL
    
    @classmethod
    def get_ws_url(cls) -> str:
        """Get the base WebSocket URL."""
        return WS_URL

# Export for easy access
get_backend_url = ServiceEndpoints.get_backend_url
get_ws_url = ServiceEndpoints.get_ws_url
get_jaa_update_url = ServiceEndpoints.get_jaa_update_url