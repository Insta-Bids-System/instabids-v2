#!/usr/bin/env python3
"""
Test conversation persistence using Playwright
"""
import asyncio
import sys
import os

# Add the ai-agents directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

async def test_conversation_persistence():
    """Test that conversation persists after page reload"""
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            print("Opening InstaBids homepage...")
            await page.goto("http://localhost:5177")
            
            # Wait for page to load
            await page.wait_for_selector('[data-testid="chat-input"], textarea[placeholder*="Describe your project"]', timeout=10000)
            print("Page loaded successfully")
            
            # Find the chat input
            chat_input = await page.query_selector('textarea[placeholder*="Describe your project"]')
            if not chat_input:
                print("ERROR: Chat input not found")
                await browser.close()
                return
            
            # Type a message
            test_message = "I need help with a kitchen renovation project"
            print(f"Typing message: {test_message}")
            await chat_input.fill(test_message)
            
            # Submit the message
            send_button = await page.query_selector('button[type="button"]:has(svg)')
            if send_button:
                await send_button.click()
                print("Message sent")
                
                # Wait for response
                await page.wait_for_timeout(3000)
                print("Waiting for response...")
                
                # Check if there are messages in the chat
                messages = await page.query_selector_all('.max-w-\\[70\\%\\]')
                print(f"Found {len(messages)} messages before reload")
                
                # Get session ID from localStorage
                session_id = await page.evaluate("() => localStorage.getItem('cia_session_id')")
                print(f"Session ID: {session_id}")
                
                # Reload the page
                print("Reloading page...")
                await page.reload()
                
                # Wait for page to reload
                await page.wait_for_selector('textarea[placeholder*="Describe your project"]', timeout=10000)
                await page.wait_for_timeout(2000)  # Give time for conversation to load
                
                # Check if session ID persisted
                new_session_id = await page.evaluate("() => localStorage.getItem('cia_session_id')")
                print(f"Session ID after reload: {new_session_id}")
                
                if session_id == new_session_id:
                    print("SUCCESS: Session ID persisted correctly")
                else:
                    print("ERROR: Session ID changed after reload")
                
                # Check if messages are still there
                messages_after = await page.query_selector_all('.max-w-\\[70\\%\\]')
                print(f"Found {len(messages_after)} messages after reload")
                
                if len(messages_after) > 1:  # Should have at least user message and assistant response
                    print("SUCCESS: Conversation persisted after page reload!")
                    
                    # Print message contents
                    for i, msg in enumerate(messages_after[:3]):  # Show first 3 messages
                        content = await msg.inner_text()
                        print(f"  Message {i+1}: {content[:100]}...")
                        
                else:
                    print("FAILURE: Conversation was not restored after reload")
            
            else:
                print("ERROR: Send button not found")
            
            # Keep browser open for inspection
            print("Keeping browser open for 10 seconds for inspection...")
            await page.wait_for_timeout(10000)
            
            await browser.close()
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_conversation_persistence())