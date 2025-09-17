#!/usr/bin/env python3
"""
Test the exact date extraction functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from routers.cia_routes_unified import extract_exact_dates

def test_date_extraction():
    print("Testing Date Extraction Function")
    print("=" * 50)
    
    test_cases = [
        "I need kitchen renovation, need all bids by Friday and project done before Christmas",
        "Can you get me quotes by next Tuesday? The work needs to be finished before my wedding on March 15th",
        "I want all bids in by end of week and the project must be complete by December 1st",
        "Need contractors to respond by Monday, project deadline is flexible",
        "Get me estimates ASAP, storm damage needs repair before next weekend"
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Input: {test_text}")
        
        try:
            result = extract_exact_dates(test_text)
            print(f"Output: {result}")
            
            if result:
                print("SUCCESS: Dates extracted successfully!")
                for key, value in result.items():
                    if value:
                        print(f"  - {key}: {value}")
            else:
                print("WARNING: No dates extracted")
                
        except Exception as e:
            print(f"ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("Date extraction test completed!")

if __name__ == "__main__":
    test_date_extraction()