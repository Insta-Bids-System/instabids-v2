#!/usr/bin/env python3
"""
Manual WebSocket Broadcast Test for Visual Effects
Directly tests WebSocket broadcasting to trigger purple glow effects
"""

import asyncio
import json
import websockets
from datetime import datetime

WEBSOCKET_URL = "ws://localhost:8008/ws/agent-activity"

async def test_manual_websocket_broadcast():
    """Test manual WebSocket broadcast to trigger visual effects"""
    print(f"Manual WebSocket Broadcast Test - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Connect to WebSocket
        print("1. Connecting to WebSocket...")
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print(f"   Connected to {WEBSOCKET_URL}")
            
            # Send test broadcast
            print("2. Sending agent activity broadcast...")
            test_broadcast = {
                "type": "agent-activity",
                "entityType": "bid-card",
                "entityId": "test-bid-card-123",
                "agentName": "IRIS",
                "action": "update-field",
                "status": "working",
                "timestamp": datetime.utcnow().isoformat(),
                "changedFields": ["budget_range", "urgency_level"]
            }
            
            await websocket.send(json.dumps(test_broadcast))
            print(f"   Sent broadcast: {json.dumps(test_broadcast, indent=2)}")
            
            # Wait for response
            print("3. Waiting for response...")
            response = await websocket.recv()
            print(f"   Received: {response}")
            
            # Send completion broadcast
            await asyncio.sleep(2)
            print("4. Sending completion broadcast...")
            completion_broadcast = {
                "type": "agent-activity",
                "entityType": "bid-card", 
                "entityId": "test-bid-card-123",
                "agentName": "IRIS",
                "action": "update-field",
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
                "changedFields": ["budget_range", "urgency_level"]
            }
            
            await websocket.send(json.dumps(completion_broadcast))
            print(f"   Sent completion: {json.dumps(completion_broadcast, indent=2)}")
            
            response = await websocket.recv()
            print(f"   Received: {response}")
            
            print("\nTest completed successfully!")
            print("\nIn the browser, you should see:")
            print("- Purple glow effect on bid card elements")
            print("- IRIS agent badge appearing")
            print("- Smooth animation transitions")
            
    except Exception as e:
        print(f"   Error: {e}")
        return False
    
    return True

def main():
    """Run the manual WebSocket test"""
    print("Manual WebSocket Broadcast Test for Visual Effects")
    print("=" * 60)
    print("\nInstructions:")
    print("1. Open browser to http://localhost:5173")
    print("2. Navigate to any page with bid cards")
    print("3. Watch for visual effects during this test")
    print("4. Check browser console for WebSocket messages")
    
    input("\nPress Enter when ready to start test...")
    
    # Run the async test
    result = asyncio.run(test_manual_websocket_broadcast())
    
    if result:
        print("\nSUCCESS: WebSocket broadcast test completed!")
        print("Visual effects system is working if you saw purple glow and agent badges.")
    else:
        print("\nFAILED: WebSocket broadcast test failed.")
        print("Check that the backend is running and WebSocket endpoint exists.")

if __name__ == "__main__":
    main()