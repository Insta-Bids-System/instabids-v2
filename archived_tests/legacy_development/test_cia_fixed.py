#!/usr/bin/env python3
"""Test CIA streaming after removing JSON schema requirement"""

import asyncio
import json
import aiohttp

async def test_cia_streaming():
    """Test the fixed CIA streaming endpoint"""
    url = "http://localhost:8008/api/cia/stream"
    data = {
        "messages": [{"content": "Hello, I want to renovate my backyard with a pool and deck", "role": "user"}],
        "conversation_id": "test-fixed-123",
        "user_id": "11111111-1111-1111-1111-111111111111"
    }
    
    print("Testing FIXED CIA endpoint streaming...")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            print(f"Status: {response.status}")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print("\nResponse:")
            print("-" * 40)
            
            accumulated = ""
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
                                print(content, end="", flush=True)
                                accumulated += content
                        elif 'error' in data_obj:
                            print(f"\nError: {data_obj['error']}")
                    except json.JSONDecodeError:
                        pass
            
            print(f"\n\nTotal characters received: {len(accumulated)}")
            
            if len(accumulated) > 0:
                print("\nSUCCESS! CIA is now streaming properly!")
                print("\nFirst 200 chars of response:")
                print(accumulated[:200])
            else:
                print("\nSTILL BROKEN - No content received")
            
            return accumulated

if __name__ == "__main__":
    asyncio.run(test_cia_streaming())