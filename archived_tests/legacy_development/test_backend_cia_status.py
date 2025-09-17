#!/usr/bin/env python3
"""Check the backend's CIA agent status"""

import requests

def check_backend_cia_status():
    """Check if the backend has CIA agent properly initialized"""
    try:
        # Simple test to see what the backend returns for a minimal request
        response = requests.post(
            "http://localhost:8008/api/cia/chat",
            json={"message": "test", "session_id": "status_check"},
            timeout=5
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 503:
            print("[IDENTIFIED] Backend CIA agent not initialized - 503 Service Unavailable")
            return False
        elif "CIA agent not initialized" in response.text:
            print("[IDENTIFIED] Backend CIA agent not initialized - error message")
            return False
        elif response.status_code == 500:
            print("[IDENTIFIED] Backend CIA agent initialized but has runtime error")
            return True
        elif response.status_code == 200:
            print("[SUCCESS] Backend CIA agent working correctly")
            return True
        else:
            print(f"[UNKNOWN] Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Cannot reach backend: {e}")
        return False

if __name__ == "__main__":
    print("=== Backend CIA Agent Status Check ===")
    check_backend_cia_status()