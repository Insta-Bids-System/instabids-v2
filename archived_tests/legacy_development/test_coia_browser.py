"""
Test COIA in browser with Playwright to see bid cards
"""
import asyncio
from playwright.async_api import async_playwright
import time

async def test_coia_browser():
    print("=" * 60)
    print("TESTING COIA BID CARDS IN BROWSER")
    print("=" * 60)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}"))
        
        # Navigate to contractor page
        print("\nNavigating to contractor page...")
        await page.goto("http://localhost:5173/contractor")
        
        # Wait for page to load
        await page.wait_for_timeout(2000)
        
        # Take initial screenshot
        await page.screenshot(path="coia_initial.png")
        print("Initial screenshot saved as coia_initial.png")
        
        # Type message asking for projects
        print("\nTyping message to ask for projects...")
        textarea = await page.wait_for_selector("textarea", timeout=5000)
        await textarea.fill("I am a General Contractor. Please show me available projects.")
        
        # Submit message
        print("Submitting message...")
        await page.keyboard.press("Enter")
        
        # Wait for response
        print("Waiting for response...")
        await page.wait_for_timeout(10000)  # Wait 10 seconds for response
        
        # Take screenshot after response
        await page.screenshot(path="coia_response.png")
        print("Response screenshot saved as coia_response.png")
        
        # Check for bid cards
        bid_cards = await page.query_selector_all(".bid-card")
        print(f"\nFound {len(bid_cards)} bid card elements")
        
        # Get page content
        content = await page.content()
        if "BC-" in content:
            print("Bid card numbers found in page content!")
        else:
            print("No bid card numbers found in page content")
        
        # Keep browser open for manual inspection
        print("\nBrowser will stay open for 30 seconds for manual inspection...")
        await page.wait_for_timeout(30000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_coia_browser())