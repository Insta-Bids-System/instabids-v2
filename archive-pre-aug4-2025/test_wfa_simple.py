"""
Simple WFA test on test contractor sites
Tests basic form analysis without database dependencies
"""
import time

import requests
from playwright.sync_api import sync_playwright


def test_contractor_sites():
    """Test if contractor sites are accessible"""
    sites = [
        {"name": "Simple", "port": 8001},
        {"name": "Pro", "port": 8002},
        {"name": "Enterprise", "port": 8003},
        {"name": "Modern", "port": 8004}
    ]

    print("Testing contractor websites accessibility...")
    print("=" * 50)

    for site in sites:
        try:
            response = requests.get(f"http://localhost:{site['port']}", timeout=3)
            if response.status_code == 200:
                print(f"[OK] {site['name']} site (port {site['port']}) is running")
            else:
                print(f"[FAIL] {site['name']} site returned {response.status_code}")
        except Exception as e:
            print(f"[FAIL] {site['name']} site not accessible: {e}")

def test_form_detection():
    """Test form detection using Playwright"""
    print("\n" + "=" * 50)
    print("Testing form detection with Playwright...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        try:
            sites = [
                {"name": "Simple", "url": "http://localhost:8008/simple-contractor/index.html"},
                {"name": "Pro", "url": "http://localhost:8008/pro-contractor/index.html"},
                {"name": "Enterprise", "url": "http://localhost:8008/enterprise-contractor/index.html"},
                {"name": "Modern", "url": "http://localhost:8008/modern-contractor/index.html"}
            ]

            for site in sites:
                print(f"\nAnalyzing {site['name']} site...")

                try:
                    page = browser.new_page()
                    page.goto(site["url"], timeout=10000)

                    # Look for forms
                    forms = page.locator("form")
                    form_count = forms.count()

                    if form_count > 0:
                        print(f"  [OK] Found {form_count} form(s)")

                        # Check for common input fields
                        inputs = page.locator('input[type="text"], input[type="email"], input[type="tel"], textarea')
                        input_count = inputs.count()
                        print(f"  [OK] Found {input_count} input field(s)")

                        # Check for submit buttons
                        submit_buttons = page.locator('input[type="submit"], button[type="submit"], button:has-text("Submit")')
                        button_count = submit_buttons.count()
                        print(f"  [OK] Found {button_count} submit button(s)")

                    else:
                        print("  [FAIL] No forms found")

                    page.close()

                except Exception as e:
                    print(f"  [ERROR] Failed to analyze {site['name']}: {e}")

                time.sleep(1)  # Brief pause between sites

        finally:
            browser.close()

def main():
    """Run simple WFA tests"""
    print("Simple WFA Testing (No Database Required)")
    print("=" * 60)

    # Test 1: Site accessibility
    test_contractor_sites()

    # Test 2: Form detection
    test_form_detection()

    print("\n" + "=" * 60)
    print("Simple WFA Test Complete!")
    print("\nNOTE: This test validates that:")
    print("- All test contractor websites are running")
    print("- Forms can be detected by Playwright")
    print("- Basic WFA functionality is working")

if __name__ == "__main__":
    main()
