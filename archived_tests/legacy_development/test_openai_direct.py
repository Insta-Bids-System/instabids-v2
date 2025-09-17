#!/usr/bin/env python3
"""Direct test of OpenAI API key to verify it's working"""

import os
import asyncio
from openai import AsyncOpenAI
import dotenv

# Load environment variables
dotenv.load_dotenv()

async def test_openai_api():
    """Test the OpenAI API directly"""
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] No OPENAI_API_KEY found in environment")
        return False
    
    print(f"[OK] API Key found: {api_key[:20]}...")
    
    # Create client
    try:
        client = AsyncOpenAI(api_key=api_key)
        print("[OK] OpenAI client created successfully")
    except Exception as e:
        print(f"[ERROR] Failed to create OpenAI client: {e}")
        return False
    
    # Test with a simple completion
    try:
        print("\n🔍 Testing API with simple completion...")
        response = await client.chat.completions.create(
            model="gpt-4o",  # Using gpt-4o since gpt-5 might not exist
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'API is working' if you can read this."}
            ],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"[OK] API Response: {result}")
        
        # Show token usage
        if hasattr(response, 'usage'):
            print(f"[INFO] Tokens used: {response.usage.prompt_tokens} prompt + {response.usage.completion_tokens} completion")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] API call failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Check if it's an auth error
        if "401" in str(e) or "Unauthorized" in str(e) or "invalid" in str(e).lower():
            print("\n⚠️  This appears to be an authentication issue.")
            print("   The API key might be:")
            print("   - Invalid or expired")
            print("   - From a different OpenAI account")
            print("   - Missing required permissions")
        
        return False

async def test_gpt5_model():
    """Test if GPT-5 model exists"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return
    
    client = AsyncOpenAI(api_key=api_key)
    
    print("\n🔍 Testing GPT-5 model availability...")
    try:
        response = await client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
        print("✅ GPT-5 model is available!")
    except Exception as e:
        error_msg = str(e)
        if "model" in error_msg.lower() or "does not exist" in error_msg.lower():
            print("❌ GPT-5 model not found. Available models might be:")
            print("   - gpt-4o (latest)")
            print("   - gpt-4-turbo")
            print("   - gpt-3.5-turbo")
            print(f"\n   Full error: {error_msg}")
        else:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("OpenAI API Key Test")
    print("=" * 60)
    
    success = asyncio.run(test_openai_api())
    
    if success:
        asyncio.run(test_gpt5_model())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ RESULT: OpenAI API is working correctly!")
        print("\nThe issue is NOT with your API key.")
        print("The problem is likely with:")
        print("1. The model name (gpt-5 might not exist)")
        print("2. The async/await handling in the CIA agent")
        print("3. The streaming response implementation")
    else:
        print("❌ RESULT: OpenAI API is not working")
        print("\nPlease check your API key.")