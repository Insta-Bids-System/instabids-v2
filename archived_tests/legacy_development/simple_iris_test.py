#!/usr/bin/env python3
"""
Simple test of Iris conversation after fixing timeout issues
"""

import requests
import json

def test_iris():
    """Test a simple Iris conversation"""
    
    print("Testing Iris conversation after timeout fixes...")
    
    test_request = {
        "message": "I want to redesign my kitchen with a modern farmhouse style",
        "user_id": "test_homeowner_123",
        "room_type": "kitchen"
    }
    
    try:
        print("Sending request to Iris...")
        
        response = requests.post(
            "http://localhost:8008/api/iris/chat",
            json=test_request,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Iris conversation working!")
            print(f"Response: {result['response'][:200]}...")
            if result.get('suggestions'):
                print(f"Suggestions: {len(result['suggestions'])} provided")
            return True
        else:
            print(f"ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("TIMEOUT: Self-referencing loop issue may still exist")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_iris()
    if success:
        print("\nRESULT: Iris timeout issue appears FIXED!")
    else:
        print("\nRESULT: Iris still has timeout issues")