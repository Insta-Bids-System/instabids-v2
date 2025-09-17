#!/usr/bin/env python3
"""
Simple test to verify date extraction and group bidding are working
"""

import requests
import json
import time

def test_simple_date_flow():
    print("Testing Simple Date Flow")
    print("=" * 40)
    
    base_url = "http://localhost:8008"
    
    # Test the date extraction function directly
    print("1. Testing Date Extraction Function")
    try:
        # Import the function directly
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))
        
        from routers.cia_routes_unified import extract_exact_dates
        
        test_text = "I need all bids by Friday December 20th and project done before February 14th"
        result = extract_exact_dates(test_text)
        
        print(f"Input: {test_text}")
        print(f"Output: {result}")
        
        if result:
            print("SUCCESS: Date extraction working")
            for key, value in result.items():
                if value:
                    print(f"  - {key}: {value}")
        else:
            print("WARNING: No dates extracted")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n2. Testing CIA Prompts for Group Bidding Priority")
    try:
        from agents.cia.prompts import SYSTEM_PROMPT
        
        if "Group Bidding" in SYSTEM_PROMPT and "15-25%" in SYSTEM_PROMPT:
            print("SUCCESS: Group bidding prominently featured in CIA prompts")
            
            # Find the group bidding section
            lines = SYSTEM_PROMPT.split('\n')
            for i, line in enumerate(lines):
                if "Group Bidding" in line:
                    print(f"  Line {i}: {line.strip()}")
                    break
        else:
            print("WARNING: Group bidding not prominently featured")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n3. Testing Database Schema for Date Fields")
    try:
        # Just verify the router has the field mapping
        from routers.cia_potential_bid_cards import FIELD_MAPPING
        
        date_fields = [
            'bid_collection_deadline', 
            'project_completion_deadline', 
            'deadline_hard', 
            'deadline_context'
        ]
        
        found_fields = []
        for field in date_fields:
            if field in FIELD_MAPPING:
                found_fields.append(field)
        
        if len(found_fields) == 4:
            print("SUCCESS: All 4 date fields configured in router")
            for field in found_fields:
                print(f"  - {field}: {FIELD_MAPPING[field]}")
        else:
            print(f"WARNING: Only {len(found_fields)}/4 date fields found")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "=" * 40)
    print("Simple date flow test completed!")

if __name__ == "__main__":
    test_simple_date_flow()