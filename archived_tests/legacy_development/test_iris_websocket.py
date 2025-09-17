#!/usr/bin/env python3
"""
Test IRIS WebSocket integration for real-time updates
"""

import asyncio
import requests
import json
import websockets
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8008"
WS_URL = "ws://localhost:8008/ws/agent-activity"

async def test_websocket_integration():
    """Test the WebSocket integration for agent activity."""
    
    print("="*60)
    print("IRIS WEBSOCKET INTEGRATION TEST")
    print("="*60)
    
    # Connect to WebSocket
    print("\n1. Connecting to WebSocket...")
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("   Connected to WebSocket!")
            
            # Listen for initial connection message
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(message)
            print(f"   Received: {data}")
            
            # Now trigger an IRIS action in another coroutine
            print("\n2. Triggering IRIS action...")
            
            # Send action request (will fail but should still broadcast "working" status)
            def send_action():
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/iris/actions/update-bid-card",
                        json={
                            "request_id": f"ws-test-{int(time.time())}",
                            "agent_name": "IRIS",
                            "bid_card_id": "303afce1-2de4-418a-bb9a-03775d89f62b",
                            "updates": {
                                "budget_min": 45000,
                                "budget_max": 65000
                            }
                        },
                        timeout=10
                    )
                    print(f"   Action response: {response.status_code}")
                except Exception as e:
                    print(f"   Action error: {e}")
            
            # Run action in background
            import threading
            thread = threading.Thread(target=send_action)
            thread.start()
            
            # Listen for agent activity events
            print("\n3. Listening for agent activity events...")
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(message)
                    
                    if data.get("type") == "agent-activity":
                        print(f"   AGENT EVENT: {data['agentName']} - {data['action']} - {data['status']}")
                        print(f"   Entity: {data['entityType']}:{data['entityId']}")
                        if data.get('changedFields'):
                            print(f"   Changed: {data['changedFields']}")
                        
                        # If we get a completed or error status, we're done
                        if data['status'] in ['completed', 'error']:
                            break
                    else:
                        print(f"   Other event: {data}")
                        
            except asyncio.TimeoutError:
                print("   No more events received (timeout)")
                
    except websockets.exceptions.WebSocketException as e:
        print(f"   WebSocket error: {e}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("WebSocket connection: TESTED")
    print("Agent activity events: CHECK ABOVE FOR RESULTS")
    print("\nNOTE: If no agent events received, check:")
    print("  1. WebSocket endpoint is configured in main.py")
    print("  2. IRIS actions router is imported and mounted")
    print("  3. Database connection is working")

if __name__ == "__main__":
    asyncio.run(test_websocket_integration())