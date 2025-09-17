#!/usr/bin/env python3
"""
Simple CIA endpoint test to verify it's working
"""

import asyncio
import aiohttp
import json
import time

async def test_simple_message():
    """Test simple message to CIA"""
    url = "http://localhost:8008/api/cia/stream"
    payload = {
        "messages": [{"role": "user", "content": "Hello, are you working?"}],
        "conversation_id": "test-simple-123",
        "user_id": "test-user-simple",
        "max_tokens": 100
    }
    
    print("Testing CIA endpoint...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    start_time = time.time()
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                print(f"Status: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"ERROR: {error_text}")
                    return
                
                print("Response chunks:")
                chunk_count = 0
                async for line in response.content:
                    chunk_count += 1
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            if data.get('content'):
                                print(f"Chunk {chunk_count}: {data['content']}", end="", flush=True)
                            elif data.get('done'):
                                print(f"\nDone received after chunk {chunk_count}")
                                break
                        except json.JSONDecodeError as e:
                            print(f"\nJSON decode error in chunk {chunk_count}: {e}")
                            print(f"Raw line: {line}")
                            continue
                    elif line:
                        print(f"\nNon-data line: {line}")
                        
    except asyncio.TimeoutError:
        print("Request timed out after 30 seconds")
    except Exception as e:
        print(f"Error: {e}")
    
    end_time = time.time()
    print(f"\nTotal time: {end_time - start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_simple_message())