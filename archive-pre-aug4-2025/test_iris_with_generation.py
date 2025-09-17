import requests
import json
import uuid
import time

def test_iris_with_image_generation():
    """Test Iris agent with actual image generation request"""
    
    print("TESTING IRIS WITH IMAGE GENERATION")
    print("="*50)
    
    iris_url = "http://localhost:8008/api/iris/chat"
    user_id = str(uuid.uuid4())
    
    # Message that should trigger image generation
    payload = {
        "message": "Can you generate a modern bathroom design with a floating vanity, good lighting, and white/gray colors?",
        "user_id": user_id,
        "board_id": None,
        "conversation_context": []
    }
    
    print(f"Homeowner ID: {user_id}")
    print(f"Message: {payload['message']}")
    print("\nSending image generation request to Iris...")
    
    try:
        response = requests.post(iris_url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n[SUCCESS] Iris responded!")
            
            # Check if image was generated
            if data.get('image_generated'):
                print(f"\n[IMAGE GENERATED]: YES")
                if data.get('image_url'):
                    print(f"Image URL: {data['image_url']}")
                if data.get('generation_id'):
                    print(f"Generation ID: {data['generation_id']}")
                if data.get('generation_status'):
                    print(f"Generation Status: {data['generation_status']}")
            else:
                print(f"\n[IMAGE GENERATED]: NO")
            
            print(f"\nResponse preview: {data.get('response', '')[:300]}...")
            print(f"\nAll response keys: {list(data.keys())}")
                    
        else:
            print(f"[ERROR] Status: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out after 60 seconds")
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")

if __name__ == "__main__":
    test_iris_with_image_generation()