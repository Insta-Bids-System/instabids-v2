#!/usr/bin/env python3
"""
Debug Iris Timeout Issues
Find and fix why Iris API calls are timing out
"""

import requests
import time
import os
from dotenv import load_dotenv
from config.service_urls import get_backend_url

load_dotenv()

BACKEND_URL = get_backend_url()
TEST_HOMEOWNER_ID = "bda3ab78-e034-4be7-8285-1b7be1bf1387"

def test_openai_direct():
    """Test OpenAI API directly"""
    print("1. TESTING OPENAI API DIRECTLY")
    print("-" * 40)
    
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: No OpenAI API key found")
            return False
        
        client = OpenAI(api_key=api_key)
        
        print(f"API Key: {api_key[:10]}...{api_key[-5:]}")
        
        # Test simple completion
        print("Testing simple OpenAI completion...")
        start_time = time.time()
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say hello in 5 words"}],
            max_tokens=50,
            timeout=15
        )
        
        end_time = time.time()
        
        print(f"SUCCESS: OpenAI responded in {end_time - start_time:.2f} seconds")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"ERROR: OpenAI direct test failed: {e}")
        return False

def test_iris_endpoint_minimal():
    """Test Iris endpoint with minimal payload"""
    print("\n2. TESTING IRIS ENDPOINT - MINIMAL")
    print("-" * 40)
    
    minimal_payload = {
        "message": "Hello",
        "user_id": TEST_HOMEOWNER_ID
    }
    
    try:
        print("Sending minimal request to Iris...")
        start_time = time.time()
        
        response = requests.post(
            f"{BACKEND_URL}/api/iris/chat",
            json=minimal_payload,
            timeout=20
        )
        
        end_time = time.time()
        
        if response.ok:
            print(f"SUCCESS: Iris responded in {end_time - start_time:.2f} seconds")
            data = response.json()
            print(f"Response: {data.get('response', '')[:100]}")
            return True
        else:
            print(f"ERROR: Iris returned {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        end_time = time.time()
        print(f"TIMEOUT: Iris did not respond within 20 seconds")
        print(f"Time elapsed: {end_time - start_time:.2f} seconds")
        return False
    except Exception as e:
        print(f"ERROR: Request failed: {e}")
        return False

def test_iris_fallback():
    """Test if Iris fallback system works when OpenAI is disabled"""
    print("\n3. TESTING IRIS FALLBACK SYSTEM")
    print("-" * 40)
    
    # We can't easily disable OpenAI, but we can test with invalid key scenario
    try:
        # This should trigger the fallback response system
        fallback_payload = {
            "message": "I love modern farmhouse style",
            "user_id": TEST_HOMEOWNER_ID,
            "room_type": "kitchen"
        }
        
        print("Testing with design-rich message...")
        response = requests.post(
            f"{BACKEND_URL}/api/iris/chat",
            json=fallback_payload,
            timeout=30
        )
        
        if response.ok:
            data = response.json()
            response_text = data.get('response', '')
            
            # Check if it's a fallback response (contains specific patterns)
            is_fallback = any(phrase in response_text for phrase in [
                "I love that you're exploring",
                "Let me help you understand",
                "I'd love to help you understand"
            ])
            
            if is_fallback:
                print("SUCCESS: Fallback response system working")
                print(f"Fallback response: {response_text[:150]}...")
            else:
                print("SUCCESS: Full AI response received")
                print(f"AI response: {response_text[:150]}...")
            
            return True
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: Fallback test failed: {e}")
        return False

def check_backend_health():
    """Check if backend is healthy"""
    print("\n4. BACKEND HEALTH CHECK")
    print("-" * 40)
    
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.ok:
            data = response.json()
            print(f"Backend Status: {data.get('status')}")
            endpoints = data.get('endpoints', [])
            iris_endpoint = '/api/iris/' in endpoints
            print(f"Iris endpoint available: {iris_endpoint}")
            return iris_endpoint
        else:
            print(f"Backend unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"Backend check failed: {e}")
        return False

def main():
    print("IRIS TIMEOUT DEBUGGING")
    print("=" * 50)
    
    results = []
    
    # Test 1: OpenAI direct
    result1 = test_openai_direct()
    results.append(("OpenAI Direct", result1))
    
    # Test 2: Backend health
    result2 = check_backend_health()
    results.append(("Backend Health", result2))
    
    if result2:  # Only test Iris if backend is healthy
        # Test 3: Iris minimal
        result3 = test_iris_endpoint_minimal()
        results.append(("Iris Minimal", result3))
        
        # Test 4: Iris fallback
        result4 = test_iris_fallback()
        results.append(("Iris Fallback", result4))
    
    # Results
    print("\n" + "=" * 50)
    print("DEBUGGING RESULTS")
    print("=" * 50)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
    
    # Diagnosis
    print("\nDIAGNOSIS:")
    if results[0][1]:  # OpenAI works
        if len(results) > 2 and not results[2][1]:  # Iris fails
            print("- OpenAI API is working")
            print("- Problem is in Iris endpoint implementation")
            print("- Likely: Iris timeout settings or error handling")
        elif len(results) > 2 and results[2][1]:  # Iris works
            print("- Everything is working!")
            print("- Previous timeouts may have been temporary")
    else:
        print("- OpenAI API is not working")
        print("- Check API key or OpenAI service status")
        print("- Iris should fall back to static responses")

if __name__ == "__main__":
    main()