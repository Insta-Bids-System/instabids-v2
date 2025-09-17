"""
Simple test for messaging system content filtering
"""

import re
from typing import Dict, List, Any

def test_content_filtering():
    """Test content filtering without database dependencies"""
    
    print("Testing Content Filtering")
    print("=" * 50)
    
    # Define filter rules
    filter_rules = [
        {"rule_type": "regex", "pattern": r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", 
         "replacement": "[PHONE REMOVED]", "severity": "high", "category": "phone"},
        {"rule_type": "regex", "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
         "replacement": "[EMAIL REMOVED]", "severity": "high", "category": "email"},
        {"rule_type": "regex", "pattern": r"@[A-Za-z0-9_]+",
         "replacement": "[SOCIAL HANDLE REMOVED]", "severity": "medium", "category": "social_media"},
        {"rule_type": "keyword", "pattern": "instagram.com/",
         "replacement": "[SOCIAL LINK REMOVED]", "severity": "medium", "category": "social_media"},
        {"rule_type": "keyword", "pattern": "call me at",
         "replacement": "[CONTACT REQUEST REMOVED]", "severity": "high", "category": "contact_request"},
    ]
    
    # Test messages
    test_messages = [
        "Hi, I'm interested in your project. Call me at 555-123-4567",
        "My email is john@contractor.com",
        "Follow me @contractorjohn on Instagram",
        "Visit instagram.com/myprofile for portfolio",
        "You can call me at my office number",
        "Contact: (555) 987-6543 or contractor@email.com",
    ]
    
    for message in test_messages:
        filtered = message
        filter_applied = False
        
        for rule in filter_rules:
            if rule["rule_type"] == "regex":
                pattern = re.compile(rule["pattern"], re.IGNORECASE)
                if pattern.search(filtered):
                    filtered = pattern.sub(rule["replacement"], filtered)
                    filter_applied = True
            elif rule["rule_type"] == "keyword":
                if rule["pattern"].lower() in filtered.lower():
                    filtered = re.sub(
                        re.escape(rule["pattern"]), 
                        rule["replacement"], 
                        filtered, 
                        flags=re.IGNORECASE
                    )
                    filter_applied = True
        
        print(f"\nOriginal: {message}")
        print(f"Filtered: {filtered}")
        print(f"Changed: {'Yes' if filter_applied else 'No'}")
    
    print("\nContent filtering test complete!")

if __name__ == "__main__":
    test_content_filtering()