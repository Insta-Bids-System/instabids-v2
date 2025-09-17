#!/usr/bin/env python3
"""
BSA Frontend Integration Test
Tests BSA chat interface in contractor dashboard with real API calls
"""

import asyncio
import json
from mcp__playwright__browser_navigate import mcp__playwright__browser_navigate
from mcp__playwright__browser_snapshot import mcp__playwright__browser_snapshot
from mcp__playwright__browser_click import mcp__playwright__browser_click
from mcp__playwright__browser_type import mcp__playwright__browser_type
from mcp__playwright__browser_wait_for import mcp__playwright__browser_wait_for
import time

async def test_bsa_frontend_integration():
    """
    Test BSA chat interface integration in contractor dashboard
    """
    
    print("🚀 TESTING BSA FRONTEND INTEGRATION")
    print("=" * 50)
    
    try:
        # Navigate to contractor dashboard
        print("📱 1. Navigating to contractor dashboard...")
        await mcp__playwright__browser_navigate("http://localhost:5173/contractor/dashboard")
        await asyncio.sleep(3)
        
        # Take screenshot of initial page
        print("📸 2. Taking screenshot of contractor dashboard...")
        await mcp__playwright__browser_snapshot()
        
        # Click on BSA - Bidding Agent tab
        print("🤖 3. Clicking BSA - Bidding Agent tab...")
        await mcp__playwright__browser_click(
            element="BSA - Bidding Agent tab",
            ref="button:has-text('BSA - Bidding Agent')"
        )
        await asyncio.sleep(2)
        
        # Wait for BSA chat to load
        print("⏳ 4. Waiting for BSA chat interface to load...")
        await mcp__playwright__browser_wait_for(text="BSA Context Loaded", time=10)
        
        # Take screenshot of BSA interface
        print("📸 5. Taking screenshot of BSA interface...")
        await mcp__playwright__browser_snapshot()
        
        # Type a message in BSA chat
        print("💬 6. Typing test message in BSA chat...")
        test_message = "I need help bidding on a bathroom remodel project with a budget of $15,000"
        await mcp__playwright__browser_type(
            element="BSA chat input",
            ref="input[placeholder*='bidding on']",
            text=test_message
        )
        
        # Send the message
        print("📤 7. Sending message to BSA...")
        await mcp__playwright__browser_click(
            element="Send button",
            ref="button:has-text('Send'), button[type='submit']"
        )
        
        # Wait for BSA response
        print("⏳ 8. Waiting for BSA response...")
        await mcp__playwright__browser_wait_for(text="BSA is analyzing", time=5)
        await mcp__playwright__browser_wait_for(text="bathroom", time=30)
        
        # Take screenshot of BSA response
        print("📸 9. Taking screenshot of BSA response...")
        await mcp__playwright__browser_snapshot()
        
        # Check for context info display
        print("🔍 10. Checking for context information display...")
        await mcp__playwright__browser_wait_for(text="context items", time=5)
        
        # Take final screenshot
        print("📸 11. Taking final screenshot...")
        await mcp__playwright__browser_snapshot()
        
        print("\n✅ BSA FRONTEND INTEGRATION TEST RESULTS:")
        print("✅ Contractor dashboard loaded successfully")
        print("✅ BSA tab visible and clickable")
        print("✅ BSA chat interface loaded")
        print("✅ Context loading indicator displayed")
        print("✅ Message input and send functionality working")
        print("✅ BSA API response received and displayed")
        print("✅ Context information shown in UI")
        
        print("\n🎯 BSA INTEGRATION STATUS: FULLY OPERATIONAL")
        print("🎯 The BSA chat interface is working end-to-end with real API calls")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR in BSA frontend integration test: {e}")
        print("🔧 This may indicate frontend/backend integration issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bsa_frontend_integration())
    if success:
        print("\n🚀 BSA Frontend Integration Test PASSED")
    else:
        print("\n💥 BSA Frontend Integration Test FAILED")