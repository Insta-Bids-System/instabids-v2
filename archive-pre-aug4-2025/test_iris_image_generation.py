import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_iris_image_generation():
    """Test Iris agent image generation capabilities"""
    
    print("TESTING IRIS IMAGE GENERATION")
    print("="*50)
    
    # Check if OpenAI API key is present
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"[SUCCESS] OpenAI API key found: {openai_key[:20]}...")
    else:
        print("[ERROR] OpenAI API key not found!")
        return
    
    # First, let's check if the image generation endpoint is working
    print("\nTesting image generation endpoint...")
    
    # Create a simple test payload (we'll use dummy IDs for now)
    test_payload = {
        "board_id": "test-board-123",
        "ideal_image_id": "ideal-123",
        "current_image_id": "current-123",
        "user_preferences": "Modern bathroom with floating vanity and good lighting"
    }
    
    try:
        # Test the actual image generation endpoint
        response = requests.post(
            "http://localhost:8008/api/image-generation/generate-dream-space",
            json=test_payload,
            timeout=45
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("[SUCCESS] Image generation endpoint responded!")
            print(json.dumps(data, indent=2))
        else:
            print(f"[ERROR] Image generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out after 45 seconds")
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")

if __name__ == "__main__":
    test_iris_image_generation()