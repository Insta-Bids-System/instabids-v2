#!/usr/bin/env python3
"""
Test conversation loading in the frontend using existing session data
"""
import asyncio
import sys
import os

# Add the ai-agents directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

async def test_frontend_conversation_loading():
    """Test conversation loading using a known working session"""
    
    try:
        from playwright.async_api import async_playwright
        
        # Use the session we know has 6 messages
        session_id_with_data = "session_1754084265525_75lgpyme4"
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            print("1. Setting up localStorage with existing session...")
            # Go to the page first
            await page.goto("http://localhost:5177")
            
            # Set the session ID in localStorage 
            await page.evaluate(f"localStorage.setItem('cia_session_id', '{session_id_with_data}')")
            
            print(f"2. Set session ID: {session_id_with_data}")
            
            # Reload to trigger conversation loading
            print("3. Reloading page to trigger conversation loading...")
            await page.reload()
            
            # Wait for page to load
            await page.wait_for_selector('textarea[placeholder*="Describe your project"]', timeout=10000)
            
            # Wait a bit for the conversation to load
            await page.wait_for_timeout(3000)
            
            # Check how many messages are displayed
            messages = await page.query_selector_all('.max-w-\\[70\\%\\]')
            print(f"4. Found {len(messages)} messages displayed on page")
            
            # Check what the session ID is
            current_session_id = await page.evaluate("() => localStorage.getItem('cia_session_id')")
            print(f"5. Current session ID: {current_session_id}")
            
            # Check console for any error messages
            console_logs = []
            page.on('console', lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
            
            # Wait a bit more to see if there are any console errors
            await page.wait_for_timeout(2000)
            
            # Print relevant console logs
            print("6. Console logs:")
            for log in console_logs[-10:]:  # Show last 10 logs
                if any(keyword in log.lower() for keyword in ['error', 'conversation', 'session', 'api']):
                    print(f"   {log}")
            
            # Test the API directly from the browser
            print("7. Testing API directly from browser...")
            api_test_result = await page.evaluate(f"""
                async () => {{
                    try {{
                        console.log('Testing API endpoint directly...');
                        const response = await fetch('http://localhost:8008/api/cia/conversation/{session_id_with_data}');
                        const data = await response.json();
                        console.log('API test result:', data);
                        return {{ success: true, messageCount: data.messages ? data.messages.length : 0, data: data }};
                    }} catch (error) {{
                        console.error('API test failed:', error);
                        return {{ success: false, error: error.message }};
                    }}
                }}
            """)
            
            print(f"8. API Test Result: {api_test_result}")
            
            if api_test_result.get('success'):
                api_message_count = api_test_result.get('messageCount', 0)
                ui_message_count = len(messages)
                
                print(f"9. API returned {api_message_count} messages")
                print(f"   UI is showing {ui_message_count} messages")
                
                if api_message_count > 0 and ui_message_count > 0:
                    print("✅ SUCCESS: Both API and UI have messages!")
                elif api_message_count > 0 and ui_message_count == 0:
                    print("❌ ISSUE: API has messages but UI is not showing them")
                    print("   This suggests a frontend loading issue")
                else:
                    print("❌ ISSUE: API is not returning messages")
            
            # Keep browser open for manual inspection
            print("10. Keeping browser open for 15 seconds for manual inspection...")
            await page.wait_for_timeout(15000)
            
            await browser.close()
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_frontend_conversation_loading())