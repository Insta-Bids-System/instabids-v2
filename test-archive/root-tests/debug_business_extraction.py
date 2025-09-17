#!/usr/bin/env python3
"""
Debug Business Name Extraction
Test the regex patterns used to extract business names
"""

import re

def extract_business_info(message: str):
    """Extract business name from message - copied from simple_research_agent.py"""
    message_lower = message.lower()
    
    # Look for business name patterns
    patterns = [
        r"i own (.+?)(?:\s+in\s+|\s*$)",
        r"my business is (.+?)(?:\s+in\s+|\s*$)",  
        r"my company is (.+?)(?:\s+in\s+|\s*$)",
        r"i run (.+?)(?:\s+in\s+|\s*$)",
        r"(.+?)\s+in\s+[\w\s]+",  # "JM Holiday Lighting in South Florida"
    ]
    
    business_name = None
    for i, pattern in enumerate(patterns):
        print(f"Testing pattern {i+1}: {pattern}")
        match = re.search(pattern, message_lower)
        if match:
            business_name = match.group(1).strip()
            print(f"  Found match: '{business_name}'")
            # Clean up common words
            business_name = re.sub(r'\b(a|the|my|our)\b', '', business_name).strip()
            print(f"  After cleanup: '{business_name}'")
            if len(business_name) > 3:  # Valid business name
                print(f"  Valid business name: '{business_name}'")
                break
            else:
                print(f"  Too short, continuing...")
                business_name = None
        else:
            print(f"  No match")
    
    # Look for website in message
    website_match = re.search(r'(https?://[\w\.-]+|[\w\.-]+\.com)', message)
    website = website_match.group(1) if website_match else None
    
    if business_name:
        return {
            'business_name': business_name.title(),
            'website': website
        }
    
    return None

def test_business_extraction():
    """Test business name extraction with various inputs"""
    
    test_messages = [
        "I own JM Holiday Lighting in South Florida",
        "My business is ABC Construction",
        "I run Mike's Plumbing in Dallas",
        "My company is Elite Roofing",
        "JM Holiday Lighting in South Florida",
        "I own a small construction company",
        "I have JM Holiday Lighting business",
    ]
    
    print("Testing Business Name Extraction")
    print("=" * 50)
    
    for i, message in enumerate(test_messages):
        print(f"\nTest {i+1}: '{message}'")
        print("-" * 30)
        
        result = extract_business_info(message)
        
        if result:
            print(f"SUCCESS: Extracted business info:")
            print(f"  Business Name: {result['business_name']}")
            print(f"  Website: {result.get('website', 'None found')}")
        else:
            print("FAILED: No business information extracted")

if __name__ == "__main__":
    test_business_extraction()