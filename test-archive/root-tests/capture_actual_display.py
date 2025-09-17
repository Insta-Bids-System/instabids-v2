#!/usr/bin/env python3
"""
Capture what's actually displayed on the demo board
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

print("CAPTURING ACTUAL DISPLAY")
print("=" * 50)

# Set up Chrome driver
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in background
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)

try:
    # Go to the site
    print("1. Navigating to http://localhost:5174...")
    driver.get("http://localhost:5174")
    time.sleep(2)
    
    # Click login as demo user
    print("2. Looking for demo login button...")
    demo_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login as Demo User')]"))
    )
    demo_button.click()
    print("   Clicked demo login")
    time.sleep(2)
    
    # Navigate to inspiration
    print("3. Looking for Inspiration link...")
    inspiration_link = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Inspiration')]"))
    )
    inspiration_link.click()
    print("   Navigated to Inspiration")
    time.sleep(3)
    
    # Take screenshot
    print("4. Taking screenshot...")
    driver.save_screenshot("Documents/instabids/actual_demo_display.png")
    print("   Screenshot saved to actual_demo_display.png")
    
    # Check for vision column
    print("5. Looking for My Vision column...")
    try:
        vision_elements = driver.find_elements(By.XPATH, "//h3[contains(text(), 'My Vision')]")
        if vision_elements:
            print("   FOUND: My Vision column exists")
            
            # Look for images in vision column
            vision_images = driver.find_elements(By.XPATH, "//div[h3[contains(text(), 'My Vision')]]//img")
            if vision_images:
                print(f"   FOUND: {len(vision_images)} images in My Vision column")
                for i, img in enumerate(vision_images):
                    src = img.get_attribute('src')
                    print(f"   Image {i+1} URL: {src[:80]}...")
                    if "oaidalleapi" in src:
                        print("   ✓ This is a DALL-E generated image!")
                    elif "unsplash" in src:
                        print("   ✗ This is still the Unsplash placeholder")
            else:
                print("   NO IMAGES found in My Vision column")
        else:
            print("   My Vision column NOT FOUND")
    except Exception as e:
        print(f"   Error checking vision column: {e}")
    
except Exception as e:
    print(f"ERROR: {e}")
    driver.save_screenshot("Documents/instabids/error_screenshot.png")
    
finally:
    driver.quit()
    
print("\n" + "=" * 50)
print("Check actual_demo_display.png to see what's displayed")