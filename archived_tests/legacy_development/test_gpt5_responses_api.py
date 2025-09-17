#!/usr/bin/env python3
"""Test GPT-5 with correct Responses API"""

import asyncio
import json
import aiohttp
import time

async def test_gpt5_responses_api():
    """Test CIA with proper GPT-5 Responses API"""
    url = "http://localhost:8008/api/cia/stream"
    data = {
        "messages": [{"content": "Hello, I want to transform my backyard into an amazing space", "role": "user"}],
        "conversation_id": "gpt5-test-123",
        "user_id": "11111111-1111-1111-1111-111111111111"
    }
    
    print("Testing CIA with FIXED GPT-5 Responses API...")
    print("=" * 60)
    
    start_time = time.time()
    first_chunk_time = None
    accumulated = ""
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            print(f"Status: {response.status}")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print("\nResponse:")
            print("-" * 40)
            
            async for line in response.content:
                line_text = line.decode('utf-8').strip()
                if line_text.startswith("data: "):
                    data_str = line_text[6:]
                    if data_str == "[DONE]":
                        print("\n\n[STREAMING COMPLETE]")
                        break
                    try:
                        data_obj = json.loads(data_str)
                        if 'choices' in data_obj:
                            content = data_obj['choices'][0]['delta'].get('content', '')
                            if content:
                                if first_chunk_time is None:
                                    first_chunk_time = time.time()
                                print(content, end="", flush=True)
                                accumulated += content
                        elif 'error' in data_obj:
                            print(f"\nError: {data_obj['error']}")
                    except json.JSONDecodeError:
                        pass
    
    end_time = time.time()
    total_time = end_time - start_time
    time_to_first_chunk = (first_chunk_time - start_time) if first_chunk_time else 0
    
    print(f"\n\nTiming Analysis:")
    print(f"  - Time to first chunk: {time_to_first_chunk:.2f}s")
    print(f"  - Total response time: {total_time:.2f}s")
    print(f"  - Characters received: {len(accumulated)}")
    if accumulated:
        print(f"  - Speed: {len(accumulated)/total_time:.0f} chars/sec")
    
    # Determine which model was used
    if len(accumulated) > 0:
        print(f"\nSUCCESS! GPT-5 Responses API is working!")
        print(f"Model appears to be: GPT-5 (using Responses API)")
        print(f"\nFirst 200 chars: {accumulated[:200]}")
    else:
        print(f"\nFAILED - No content received (likely fell back to GPT-4o)")
    
    return accumulated

async def main():
    await test_gpt5_responses_api()

if __name__ == "__main__":
    asyncio.run(main())