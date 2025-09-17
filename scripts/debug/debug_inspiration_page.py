"""
Debug the inspiration page to see what elements exist
"""

import time
from playwright.sync_api import sync_playwright

def debug_inspiration_page():
    print("Debugging inspiration page...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # 1. Login
            print("1. Logging in...")
            page.goto("http://localhost:3002/login")
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            
            # Click Demo Homeowner Access
            demo_button = page.locator("button:has-text('Demo Homeowner Access')")
            if demo_button.count() > 0:
                demo_button.click()
                print("SUCCESS: Logged in")
                time.sleep(3)
            else:
                print("FAILED: No demo login button")
                return
            
            # 2. Go to Design Inspiration
            print("2. Going to Design Inspiration...")
            page.goto("http://localhost:3002/dashboard/inspiration")
            page.wait_for_load_state('networkidle')
            time.sleep(3)
            
            # 3. Debug page content
            print("3. Debugging page content...")
            
            # Get page title
            title = page.title()
            print(f"Page title: {title}")
            
            # Get all text content
            body_text = page.locator("body").text_content()
            print(f"Body text (first 500 chars): {body_text[:500]}")
            
            # Look for key elements
            print("\n--- Looking for key elements ---")
            
            # Headers
            headers = page.locator("h1, h2, h3")
            print(f"Headers found: {headers.count()}")
            for i in range(min(headers.count(), 5)):
                header_text = headers.nth(i).text_content()
                print(f"  Header {i+1}: '{header_text}'")
            
            # Buttons
            buttons = page.locator("button")
            print(f"Buttons found: {buttons.count()}")
            for i in range(min(buttons.count(), 10)):
                button_text = buttons.nth(i).text_content()
                if button_text and button_text.strip():
                    print(f"  Button {i+1}: '{button_text.strip()}'")
            
            # Divs with classes
            divs = page.locator("div[class]")
            print(f"Divs with classes found: {divs.count()}")
            
            # Look for loading states
            loading = page.locator("[class*='loading'], [class*='spinner'], .animate-spin")
            print(f"Loading elements: {loading.count()}")
            
            # Look for error messages
            errors = page.locator("[class*='error'], .text-red")
            print(f"Error elements: {errors.count()}")
            
            # Check network requests
            print("\n--- Network Analysis ---")
            
            # Take screenshot
            page.screenshot(path="debug-inspiration-page.png", full_page=True)
            print("Screenshot saved: debug-inspiration-page.png")
            
            print("\nBrowser staying open for 20 seconds for manual inspection...")
            time.sleep(20)
            
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="debug-error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    debug_inspiration_page()