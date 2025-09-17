import requests
import json
import uuid
import time

def create_homeowner_and_test_iris():
    """Create a real homeowner and test the Iris inspiration flow"""
    
    # Step 1: Create homeowner through CIA
    print("STEP 1: Creating homeowner through CIA conversation...")
    cia_url = "http://localhost:8008/api/cia/chat"
    
    # Generate proper IDs
    user_id = str(uuid.uuid4())
    session_id = f"homeowner-iris-test-{int(time.time())}"
    
    print(f"User ID: {user_id}")
    print(f"Session ID: {session_id}")
    
    # Have a bathroom renovation conversation
    messages = [
        "Hi, I need help with my bathroom renovation. The toilet is leaking and causing water damage.",
        "I'm in Chicago, zip code 60614. The leak is from the base of the toilet and the floor is warping.",
        "My name is Emily Chen and my email is emily.chen@example.com. I need this fixed within a week!"
    ]
    
    for i, msg in enumerate(messages):
        print(f"\nMessage {i+1}: {msg}")
        payload = {
            "message": msg,
            "user_id": user_id,
            "session_id": session_id
        }
        response = requests.post(cia_url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Ready for JAA: {data.get('ready_for_jaa')}")
            
            # Check if project was created
            if data.get('ready_for_jaa') and i == len(messages) - 1:
                print("\n✓ CIA conversation complete - ready for JAA")
                
                # Step 2: Check if homeowner profile was created
                print("\nSTEP 2: Checking homeowner profile...")
                # In a real scenario, we'd check the database here
                # For now, we'll proceed to Iris
                
                # Step 3: Test Iris conversation
                print("\nSTEP 3: Testing Iris inspiration agent...")
                iris_url = "http://localhost:8008/api/iris/chat"
                
                iris_messages = [
                    "Hi Iris! I'm working on my bathroom renovation and need some design inspiration.",
                    "I like modern, clean designs with white and gray colors. Maybe some plants too!",
                    "Can you generate some bathroom designs with a modern vanity and good lighting?"
                ]
                
                for j, iris_msg in enumerate(iris_messages):
                    print(f"\nIris Message {j+1}: {iris_msg}")
                    iris_payload = {
                        "message": iris_msg,
                        "user_id": user_id,  # Using user_id as user_id
                        "board_id": None,
                        "conversation_context": []
                    }
                    
                    iris_response = requests.post(iris_url, json=iris_payload)
                    
                    if iris_response.status_code == 200:
                        iris_data = iris_response.json()
                        print(f"Iris responded: {iris_data.get('message', '')[:100]}...")
                        
                        # Check if images were generated
                        if iris_data.get('images'):
                            print(f"✓ Generated {len(iris_data['images'])} inspiration images!")
                            for idx, img in enumerate(iris_data['images']):
                                print(f"  - Image {idx+1}: {img.get('url', 'No URL')}")
                    else:
                        print(f"✗ Iris error: {iris_response.status_code}")
                        print(iris_response.text)
                
                # Step 4: Check inspiration board
                print("\nSTEP 4: Checking inspiration board...")
                board_url = f"http://localhost:8008/api/inspiration/board/{user_id}"
                board_response = requests.get(board_url)
                
                if board_response.status_code == 200:
                    board_data = board_response.json()
                    if board_data.get('images'):
                        print(f"✓ Found {len(board_data['images'])} images on inspiration board!")
                    else:
                        print("✗ No images found on inspiration board")
                else:
                    print(f"✗ Could not fetch inspiration board: {board_response.status_code}")
                    
        else:
            print(f"✗ CIA error: {response.status_code}")
            print(response.text)
            break
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print(f"Homeowner ID: {user_id}")
    print(f"Session ID: {session_id}")
    print("Check the homeowner dashboard at http://localhost:5174/dashboard")
    print("="*60)

if __name__ == "__main__":
    create_homeowner_and_test_iris()