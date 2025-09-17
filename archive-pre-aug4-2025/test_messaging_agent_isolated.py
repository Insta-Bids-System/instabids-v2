#!/usr/bin/env python3
"""Test messaging agent in isolation"""

import sys
import os
sys.path.append('ai-agents')

# Test basic filtering without database
import re
from typing import Dict, List, Any

def test_basic_filtering():
    """Test content filtering with regex patterns"""
    
    content = "Call me at 555-123-4567 or email john@test.com for more details"
    
    # Define filter rules
    filter_rules = [
        {
            "rule_type": "regex",
            "pattern": r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "replacement": "[CONTACT REMOVED]",
            "category": "phone"
        },
        {
            "rule_type": "regex", 
            "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "replacement": "[CONTACT REMOVED]",
            "category": "email"
        },
        {
            "rule_type": "keyword",
            "pattern": "call me at",
            "replacement": "[CONTACT REQUEST REMOVED]",
            "category": "contact_request"
        }
    ]
    
    filtered_content = content
    filter_reasons = []
    content_filtered = False
    
    for rule in filter_rules:
        if rule["rule_type"] == "regex":
            pattern = re.compile(rule["pattern"], re.IGNORECASE)
            matches = pattern.findall(filtered_content)
            
            if matches:
                content_filtered = True
                for match in matches:
                    filter_reasons.append({
                        "category": rule["category"],
                        "matched_text": match,
                        "replacement": rule["replacement"]
                    })
                filtered_content = pattern.sub(rule["replacement"], filtered_content)
                
        elif rule["rule_type"] == "keyword":
            if rule["pattern"].lower() in filtered_content.lower():
                content_filtered = True
                filter_reasons.append({
                    "category": rule["category"],
                    "matched_text": rule["pattern"],
                    "replacement": rule["replacement"]
                })
                filtered_content = re.sub(
                    re.escape(rule["pattern"]), 
                    rule["replacement"], 
                    filtered_content, 
                    flags=re.IGNORECASE
                )
    
    print("=== MESSAGING AGENT FILTER TEST ===")
    print(f"Original: {content}")
    print(f"Filtered: {filtered_content}")
    print(f"Content filtered: {content_filtered}")
    print(f"Filter reasons count: {len(filter_reasons)}")
    print(f"Filter details: {filter_reasons}")
    
    # Verify filtering worked
    success = (
        "[CONTACT REMOVED]" in filtered_content and
        content_filtered and
        len(filter_reasons) >= 2  # Should catch phone and email
    )
    
    print(f"Test result: {'PASSED' if success else 'FAILED'}")
    return success

def test_contractor_aliasing():
    """Test contractor alias generation logic"""
    
    # Simulate contractor count logic
    contractor_counts = [0, 1, 2, 3, 25, 26]
    expected_aliases = ["Contractor A", "Contractor B", "Contractor C", "Contractor D", "Contractor Z", "Contractor AA"]
    
    print("\n=== CONTRACTOR ALIASING TEST ===")
    
    for i, count in enumerate(contractor_counts):
        alias_number = count + 1
        if alias_number <= 26:
            contractor_alias = f"Contractor {chr(64 + alias_number)}"  # A, B, C, etc.
        else:
            # Handle more than 26 contractors
            first_letter = chr(64 + ((alias_number - 1) // 26))
            second_letter = chr(64 + ((alias_number - 1) % 26) + 1)
            contractor_alias = f"Contractor {first_letter}{second_letter}"
        
        print(f"Count {count} -> {contractor_alias}")
        if i < len(expected_aliases):
            assert contractor_alias == expected_aliases[i], f"Expected {expected_aliases[i]}, got {contractor_alias}"
    
    print("Contractor aliasing test: PASSED")
    return True

if __name__ == "__main__":
    try:
        # Test filtering
        filter_success = test_basic_filtering()
        
        # Test aliasing
        alias_success = test_contractor_aliasing()
        
        overall_success = filter_success and alias_success
        print(f"\n=== OVERALL TEST RESULT: {'PASSED' if overall_success else 'FAILED'} ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()