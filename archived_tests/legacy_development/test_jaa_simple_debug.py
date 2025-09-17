#!/usr/bin/env python3
"""DEBUG: Test JAA endpoint with minimal payload"""

import requests
import json
import time

def test_jaa_simple():
    print("=" * 50)
    print("DEBUGGING JAA ENDPOINT")
    print("=" * 50)
    
    # Use the real bid card we found
    bid_card_id = "36214de5-a068-4dcc-af99-cf33238e7472"
    
    # Minimal payload to test
    minimal_payload = {
        "update_type": "test_update",
        "source": "debug_test"
    }
    
    print(f"Testing JAA endpoint: PUT /jaa/update/{bid_card_id}")
    print(f"Payload: {json.dumps(minimal_payload, indent=2)}")
    
    try:
        print("\nSending request...")
        start_time = time.time()
        
        response = requests.put(
            f"http://localhost:8008/jaa/update/{bid_card_id}",
            json=minimal_payload,
            timeout=30  # Shorter timeout for debugging
        )
        
        elapsed = time.time() - start_time
        print(f"Response time: {elapsed:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS!")
            print(f"Result: {json.dumps(result, indent=2)}")
            return True
        else:
            print("FAILED!")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"TIMEOUT after {elapsed:.2f} seconds")
        return False
    except requests.exceptions.ConnectionError:
        print("CONNECTION ERROR - Backend not responding")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def check_backend_health():
    print("\n" + "=" * 50)
    print("CHECKING BACKEND HEALTH")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8008/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("Backend is running:")
            print(f"Service: {data.get('service')}")
            print(f"Version: {data.get('version')}")
            print("Available endpoints:")
            for endpoint in data.get('endpoints', []):
                print(f"  - {endpoint}")
            return True
        else:
            print(f"Backend unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"Backend health check failed: {e}")
        return False

if __name__ == "__main__":
    # Check backend first
    backend_ok = check_backend_health()
    
    if backend_ok:
        print("\nProceedingwith JAA test...")
        jaa_ok = test_jaa_simple()
        
        if jaa_ok:
            print("\n✅ JAA ENDPOINT IS WORKING")
        else:
            print("\n❌ JAA ENDPOINT HAS ISSUES")
    else:
        print("\n❌ BACKEND NOT AVAILABLE")