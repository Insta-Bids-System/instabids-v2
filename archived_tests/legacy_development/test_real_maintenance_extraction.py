#!/usr/bin/env python3
"""
Test script to demonstrate how maintenance issues are extracted from REAL photo AI analysis
This shows the actual data flow from uploaded photos → AI classification → maintenance issues
"""

import requests
import json
from datetime import datetime

def test_real_maintenance_extraction():
    """Test with the property that has actual AI-detected maintenance issues"""
    
    print("TESTING REAL MAINTENANCE ISSUE EXTRACTION")
    print("=" * 60)
    
    # Property with real AI-detected issues
    property_id = "d1ce83f1-900a-4677-bbdc-375db1f7bcca"
    
    print(f"Testing property: {property_id}")
    print("This property has REAL uploaded photos with AI-detected maintenance issues")
    print()
    
    # Test the API endpoint
    url = f"http://localhost:8008/api/properties/{property_id}/maintenance-issues"
    params = {"user_id": "test-user"}
    
    try:
        print("Making API call to extract maintenance issues...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            issues = response.json()
            
            if not issues:
                print("No maintenance issues found")
                return
                
            print(f"Found {len(issues)} maintenance issues from REAL photos:")
            print()
            
            for i, issue in enumerate(issues, 1):
                print(f"ISSUE #{i}:")
                print(f"   Photo: {issue['photo_filename']}")
                print(f"   Description: {issue['description']}")
                print(f"   Severity: {issue['severity']}")
                print(f"   Type: {issue['type']}")
                print(f"   Cost: {issue['estimated_cost']}")
                print(f"   Confidence: {issue['confidence']}")
                print(f"   Detected: {issue['detected_at']}")
                print()
                
            print("KEY POINT: These issues were extracted from:")
            print("   1. Real uploaded photos")
            print("   2. AI analysis (GPT-4o vision)")
            print("   3. Stored in property_photos.ai_classification.detected_issues")
            print("   4. Converted to structured maintenance issue format")
            
        else:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Could not connect to backend server (localhost:8008)")
        print("Make sure Docker containers are running:")
        print("   cd C:\\Users\\Not John Or Justin\\Documents\\instabids")
        print("   docker-compose up -d")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_real_maintenance_extraction()