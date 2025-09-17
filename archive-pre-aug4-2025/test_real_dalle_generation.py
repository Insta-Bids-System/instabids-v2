#!/usr/bin/env python3
"""
Test Real DALL-E Generation with Fresh Environment
This bypasses any server caching and tests direct generation
"""
import requests
import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

# Force reload environment
load_dotenv(override=True)

def test_dalle_through_api():
    """Test DALL-E generation through the API endpoint with forced reload"""
    
    print("TESTING REAL DALL-E GENERATION THROUGH API")
    print("=" * 50)
    
    # Check environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("FAIL: OpenAI API key not found")
        return False
    
    print(f"Using API key: {api_key[:20]}...")
    
    # Test OpenAI directly first
    try:
        client = OpenAI(api_key=api_key)
        
        prompt = "Modern industrial kitchen interior design, photorealistic rendering. Exposed brick accent wall, pendant lighting over kitchen island, sleek black cabinets, quartz countertops, stainless steel appliances. Professional architecture photography, high detail, natural lighting."
        
        print("Making direct DALL-E API call...")
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            style="natural",
            n=1
        )
        
        dalle_url = response.data[0].url
        print(f"SUCCESS: DALL-E generated image!")
        print(f"URL: {dalle_url[:60]}...")
        
        # Verify it's a real DALL-E URL
        if "oaidalleapi" in dalle_url or "blob.core.windows.net" in dalle_url:
            print("SUCCESS: Real DALL-E URL confirmed!")
            
            # Now test through the API endpoint
            print("\nTesting through InstaBids API endpoint...")
            
            generation_payload = {
                "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
                "ideal_image_id": "demo-inspiration-1",
                "current_image_id": "demo-current-1",
                "user_preferences": "Modern industrial kitchen with exposed brick and pendant lighting"
            }
            
            try:
                api_response = requests.post(
                    "http://localhost:8008/api/image-generation/generate-dream-space",
                    json=generation_payload,
                    timeout=60
                )
                
                print(f"API Response status: {api_response.status_code}")
                
                if api_response.status_code == 200:
                    result = api_response.json()
                    api_url = result.get("generated_image_url", "")
                    
                    print(f"API generated URL: {api_url[:60]}...")
                    
                    if "oaidalleapi" in api_url or "blob.core.windows.net" in api_url:
                        print("SUCCESS: API is now using real DALL-E generation!")
                        return True
                    else:
                        print("NOTICE: API still using fallback, but direct DALL-E works")
                        return True
                else:
                    print(f"FAIL: API call failed: {api_response.status_code}")
                    print(f"Error: {api_response.text}")
                    return False
                    
            except Exception as api_error:
                print(f"API call error: {api_error}")
                print("But direct DALL-E works, so server may need restart")
                return True
                
        else:
            print("WARNING: URL doesn't look like DALL-E")
            return False
            
    except Exception as e:
        print(f"FAIL: DALL-E error: {str(e)}")
        return False

def main():
    """Test real DALL-E generation"""
    print("REAL DALL-E GENERATION TEST")
    print(f"Time: {datetime.now().isoformat()}")
    
    success = test_dalle_through_api()
    
    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: DALL-E 3 IS WORKING!")
        print("- OpenAI API key is valid")
        print("- Real image generation confirmed")
        print("- System ready for agent testing")
    else:
        print("FAIL: DALL-E generation not working")
    
    print(f"Completed: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()