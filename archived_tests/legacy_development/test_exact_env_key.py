#!/usr/bin/env python3
"""
Test the exact OpenAI key from the .env file
"""

import asyncio
from openai import AsyncOpenAI
import time

async def test_exact_key():
    """Test with the exact key from .env file"""
    # Load key from environment
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set in environment")
        return
    
    print(f"Testing exact key from .env: {api_key[:25]}...")
    print(f"Key length: {len(api_key)}")
    print(f"Key format: {'OK' if api_key.startswith('sk-proj-') else 'BAD'}")
    
    client = AsyncOpenAI(api_key=api_key)
    
    try:
        print("\nTesting GPT-4o...")
        start_time = time.time()
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say 'API key is working' if you can respond"}],
            max_tokens=20
        )
        
        end_time = time.time()
        print(f"SUCCESS GPT-4o Response: {response.choices[0].message.content}")
        print(f"  Response time: {end_time - start_time:.2f}s")
        
    except Exception as e:
        print(f"ERROR GPT-4o: {e}")
        return False
    
    try:
        print("\nTesting GPT-5...")
        start_time = time.time()
        response = await client.chat.completions.create(
            model="gpt-5", 
            messages=[{"role": "user", "content": "Say 'GPT-5 is working' if you can respond"}],
            max_completion_tokens=20
        )
        
        end_time = time.time()
        print(f"SUCCESS GPT-5 Response: {response.choices[0].message.content}")
        print(f"  Response time: {end_time - start_time:.2f}s")
        
    except Exception as e:
        print(f"ERROR GPT-5: {e}")
        # GPT-5 might not be available, but GPT-4o working is enough
        
    return True

if __name__ == "__main__":
    asyncio.run(test_exact_key())