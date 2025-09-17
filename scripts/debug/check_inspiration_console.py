"""
Check browser console for errors on inspiration page
"""

import time
from playwright.sync_api import sync_playwright

def check_console_errors():
    print("Checking browser console for errors...")
    
    console_messages = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Capture console messages
        def log_console(msg):
            console_messages.append(f"{msg.type}: {msg.text}")
            print(f"CONSOLE {msg.type.upper()}: {msg.text}")
        
        page.on("console", log_console)
        
        try:
            # Login
            print("1. Logging in...")
            page.goto("http://localhost:3002/login")
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            
            demo_button = page.locator("button:has-text('Demo Homeowner Access')")
            if demo_button.count() > 0:
                demo_button.click()
                time.sleep(3)
            
            # Go to inspiration page and watch console
            print("2. Going to inspiration page...")
            page.goto("http://localhost:3002/dashboard/inspiration")
            page.wait_for_load_state('networkidle')
            time.sleep(5)
            
            # Check if page loaded
            print("3. Checking page state...")
            
            # Look for key elements without Unicode
            buttons = page.locator("button")
            print(f"Found {buttons.count()} buttons")
            
            # Try to find specific elements
            create_button = page.locator("button:has-text('New Board'), button:has-text('Create')")
            print(f"Create buttons: {create_button.count()}")
            
            chat_button = page.locator("button:has-text('Chat with Iris'), button:has-text('Iris')")
            print(f"Chat buttons: {chat_button.count()}")
            
            # Check if there's any content
            main_content = page.locator("main, [role='main'], .container")
            print(f"Main content areas: {main_content.count()}")
            
            if main_content.count() > 0:
                content_text = main_content.first.text_content()
                print(f"Content preview: {content_text[:200] if content_text else 'No text content'}")
            
            # Check network errors
            print("\n4. Network status:")
            print("Waiting for any network requests to complete...")
            time.sleep(3)
            
            page.screenshot(path="console-debug.png")
            print("Screenshot saved: console-debug.png")
            
            print("\nAll console messages:")
            for msg in console_messages:
                print(f"  {msg}")
            
            print("\nKeeping browser open for 15 seconds...")
            time.sleep(15)
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_console_errors()