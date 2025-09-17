#!/usr/bin/env python3
"""
Test COIA Landing Page with JM Holiday Lighting
"""

import asyncio
import aiohttp
import json

async def test_coia_landing():
    """Test the landing page endpoint with JM Holiday Lighting"""
    
    url = "http://localhost:8008/api/coia/landing"
    
    # Test message about JM Holiday Lighting
    message = "Hi, this is JM Holiday Lighting. I saw your website and I'm interested in joining InstaBids."
    
    payload = {
        "message": message,
        "session_id": "test-jm-holiday-2",
        "thread_id": "test-jm-thread-2"
    }
    
    print(f"Testing COIA Landing Page Endpoint")
    print(f"Message: {message}")
    print(f"URL: {url}")
    print("-" * 50)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Set a reasonable timeout (30 seconds)
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with session.post(url, json=payload, timeout=timeout) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    # Read streaming response
                    full_response = ""
                    async for line in response.content:
                        if line:
                            decoded = line.decode('utf-8').strip()
                            if decoded.startswith("data: "):
                                data = decoded[6:]
                                if data != "[DONE]":
                                    try:
                                        chunk = json.loads(data)
                                        content = chunk.get("content", "")
                                        full_response += content
                                        print(content, end="", flush=True)
                                    except json.JSONDecodeError:
                                        pass
                    
                    print("\n" + "-" * 50)
                    print("Response complete!")
                    
                    # Check if Atlanta was mentioned
                    if "Atlanta" in full_response or "GA" in full_response or "Georgia" in full_response:
                        print("\n⚠️ WARNING: Response mentioned Atlanta/GA/Georgia - this is INCORRECT!")
                        print("JM Holiday Lighting is in Pompano Beach, FL")
                    
                    if "Pompano" in full_response or "Florida" in full_response or "FL" in full_response:
                        print("\n✅ SUCCESS: Response correctly identified Florida location!")
                        
                else:
                    text = await response.text()
                    print(f"Error: {text}")
                    
        except asyncio.TimeoutError:
            print("Request timed out after 30 seconds")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_coia_landing())