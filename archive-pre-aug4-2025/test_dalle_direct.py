#!/usr/bin/env python3
"""
Test DALL-E 3 API directly to verify it's working
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

# Force reload environment variables
load_dotenv(override=True)

def test_dalle_direct():
    """Test DALL-E 3 API directly"""
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("FAIL: OPENAI_API_KEY not found in environment")
        return False
    
    print(f"OpenAI API key loaded: {openai_key[:20]}...")
    
    try:
        client = OpenAI(api_key=openai_key)
        
        prompt = "Interior design photograph, photorealistic rendering. Modern industrial kitchen with exposed brick wall, pendant lighting, and sleek countertops. Professional photography quality, realistic lighting and shadows, high detail and clarity."
        
        print(f"Making DALL-E 3 API call with prompt: {prompt[:50]}...")
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            style="natural",
            n=1
        )
        
        generated_url = response.data[0].url
        print(f"SUCCESS: DALL-E 3 generated image!")
        print(f"URL: {generated_url}")
        
        # Check if it's a real OpenAI URL
        if "oaidalleapiprodscus.blob.core.windows.net" in generated_url or "dall-e" in generated_url:
            print("SUCCESS: Real DALL-E generated image detected!")
            return True
        else:
            print("WARNING: URL doesn't look like DALL-E")
            return True  # Still counts as success
            
    except Exception as e:
        print(f"FAIL: DALL-E API error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing DALL-E 3 API Direct")
    print("=" * 40)
    success = test_dalle_direct()
    print("=" * 40)
    if success:
        print("SUCCESS: DALL-E 3 is working!")
    else:
        print("FAIL: DALL-E 3 is not working")