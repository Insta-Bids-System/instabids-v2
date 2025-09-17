#!/usr/bin/env python3
"""Debug CIA route initialization"""

import requests
import json

def test_backend_cia_agent():
    """Test if the backend has CIA agent properly initialized"""
    try:
        # Make a simple GET request to check if CIA routes are working
        response = requests.get("http://localhost:8008/api/cia/conversation/test_debug", timeout=5)
        
        print(f"CIA conversation route status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] CIA routes responding")
            print(f"Response: {data}")
        else:
            print(f"CIA route response: {response.text}")
            
        # Now try to check if we can get any debugging info from the backend
        # Let's try calling the conversation endpoint with a known session
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"[FAILED] Backend CIA routes error: {e}")
        return False

def test_manual_backend_debug():
    """Test by calling backend debug endpoint if it exists"""
    try:
        # Try to get backend status
        response = requests.get("http://localhost:8008/", timeout=5)
        print(f"Backend root status: {response.status_code}")
        
        # Try to call the CIA chat with more debugging
        chat_data = {
            "message": "test",
            "session_id": "debug_test",
            "user_id": "debug_user"
        }
        
        print("Calling CIA chat endpoint...")
        response = requests.post(
            "http://localhost:8008/api/cia/chat",
            json=chat_data,
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response text: {response.text[:500]}...")
        
    except Exception as e:
        print(f"Debug request failed: {e}")

if __name__ == "__main__":
    print("=== CIA Route Debugging ===")
    print()
    
    print("1. Testing conversation endpoint...")
    test_backend_cia_agent()
    print()
    
    print("2. Manual backend debugging...")
    test_manual_backend_debug()