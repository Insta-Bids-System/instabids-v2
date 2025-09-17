import requests
import json
import uuid
import time

def test_complete_homeowner_and_iris_flow():
    """Test complete CIA + Iris flow with Claude credits"""
    
    print("COMPLETE HOMEOWNER + IRIS FLOW TEST")
    print("="*60)
    
    # Step 1: Create homeowner with CIA
    print("\nSTEP 1: Creating homeowner with CIA...")
    cia_url = "http://localhost:8008/api/cia/chat"
    user_id = str(uuid.uuid4())
    session_id = f"complete-flow-{int(time.time())}"
    
    cia_payload = {
        "message": "Hi! I need help with my bathroom renovation. I want to replace the vanity, add new lighting, and retile. I'm in Chicago 60614 and my budget is around $8,000. My name is Jennifer Davis.",
        "user_id": user_id,
        "session_id": session_id
    }
    
    print(f"User: {user_id}")
    print(f"Message: {cia_payload['message']}")
    
    cia_response = requests.post(cia_url, json=cia_payload, timeout=45)
    
    if cia_response.status_code == 200:
        cia_data = cia_response.json()
        print(f"\n[CIA SUCCESS]")
        print(f"Phase: {cia_data.get('current_phase')}")
        print(f"Ready for JAA: {cia_data.get('ready_for_jaa')}")
        
        if cia_data.get('collected_info'):
            print(f"Extracted project info: {cia_data['collected_info'].get('project_type')}")
        
        # Step 2: Now test Iris for design inspiration
        print(f"\n{'='*60}")
        print("STEP 2: Getting design inspiration from Iris...")
        
        iris_url = "http://localhost:8008/api/iris/chat"
        iris_payload = {
            "message": "Hi Iris! I'm renovating my bathroom and need design inspiration. I like modern style with white and gray colors. Can you generate some bathroom designs with a floating vanity and good lighting?",
            "user_id": user_id,
            "board_id": None,
            "conversation_context": []
        }
        
        print(f"Iris message: {iris_payload['message']}")
        
        iris_response = requests.post(iris_url, json=iris_payload, timeout=30)
        
        if iris_response.status_code == 200:
            iris_data = iris_response.json()
            print(f"\n[IRIS SUCCESS]")
            
            if iris_data.get('image_generated'):
                print(f"Image generated: {iris_data['image_generated']}")
                if iris_data.get('image_url'):
                    print(f"Image URL: {iris_data['image_url'][:80]}...")
                print(f"Generation ID: {iris_data.get('generation_id')}")
                
            print(f"Response: {iris_data.get('response', '')[:100]}...")
            
        else:
            print(f"[IRIS ERROR] Status: {iris_response.status_code}")
            print(iris_response.text)
        
        print(f"\n{'='*60}")
        print("SUMMARY:")
        print(f"Homeowner ID: {user_id}")
        print(f"CIA Working: {'Yes' if cia_data.get('ready_for_jaa') else 'No'}")
        print(f"Iris Working: {'Yes' if iris_response.status_code == 200 else 'No'}")
        print(f"Image Generated: {'Yes' if iris_data.get('image_generated') else 'No'}")
        print("="*60)
        
    else:
        print(f"[CIA ERROR] Status: {cia_response.status_code}")
        print(cia_response.text)

if __name__ == "__main__":
    test_complete_homeowner_and_iris_flow()