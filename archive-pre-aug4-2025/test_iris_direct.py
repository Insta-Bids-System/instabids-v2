import requests
import json
import uuid

def test_iris_direct():
    """Test Iris agent directly"""
    
    print("Testing Iris agent for design inspiration...")
    
    iris_url = "http://localhost:8008/api/iris/chat"
    user_id = str(uuid.uuid4())
    
    # Test messages to Iris
    test_messages = [
        "Hi Iris! I need help designing my bathroom",
        "I like modern style with white and gray colors",
        "Can you generate a bathroom design with a floating vanity and good lighting?"
    ]
    
    for i, message in enumerate(test_messages):
        print(f"\n{'='*60}")
        print(f"Message {i+1}: {message}")
        print('='*60)
        
        payload = {
            "message": message,
            "user_id": user_id,
            "board_id": None,
            "conversation_context": []
        }
        
        try:
            response = requests.post(iris_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\nIris Response: {data.get('message', '')}")
                print(f"\nFull response keys: {list(data.keys())}")
                
                # Check for generated images
                if 'images' in data and data['images']:
                    print(f"\n[SUCCESS] Generated {len(data['images'])} images!")
                    for idx, img in enumerate(data['images']):
                        print(f"  Image {idx+1}: {img}")
                else:
                    print("\nNo images in response")
                    
                # Check for image generation status
                if 'image_generated' in data:
                    print(f"Image generated: {data['image_generated']}")
                    
                if 'image_url' in data:
                    print(f"\n[SUCCESS] Generated image URL: {data['image_url']}")
                    
                if 'generation_id' in data:
                    print(f"Generation ID: {data['generation_id']}")
                    
                if 'generation_status' in data:
                    print(f"Generation status: {data['generation_status']}")
                    
            else:
                print(f"\n[ERROR] Status {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"\n[ERROR] Request failed: {e}")
    
    print(f"\n\nHomeowner ID for testing: {user_id}")
    print("Check inspiration board at http://localhost:5174/inspiration-demo")

if __name__ == "__main__":
    test_iris_direct()