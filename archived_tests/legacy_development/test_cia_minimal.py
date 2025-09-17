#!/usr/bin/env python3
"""
Minimal test to find the actual timeout issue
"""
import asyncio
import os
from openai import AsyncOpenAI

async def test_openai():
    """Test if OpenAI API itself works"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No API key")
        return
    
    print(f"Testing OpenAI with key: {api_key[:20]}...")
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        # Test simple completion
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        
        print(f"SUCCESS: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        return False

async def test_extraction():
    """Test if GPT extraction works"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No API key")
        return
        
    print("Testing extraction...")
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        extraction_prompt = """Extract project details from: "I need bathroom renovation in Manhattan 10001, budget $30,000"
        
        Return JSON:
        {
            "project_type": "...",
            "location": "...",
            "zip_code": "...",
            "budget": ...
        }"""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": extraction_prompt}],
            max_tokens=200,
            temperature=0
        )
        
        print(f"EXTRACTION SUCCESS: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"EXTRACTION FAILED: {e}")
        return False

async def main():
    print("=== MINIMAL CIA DEBUGGING ===")
    
    # Test 1: Basic OpenAI
    print("\nTest 1: OpenAI API")
    await test_openai()
    
    # Test 2: Extraction
    print("\nTest 2: GPT Extraction")
    await test_extraction()

if __name__ == "__main__":
    asyncio.run(main())