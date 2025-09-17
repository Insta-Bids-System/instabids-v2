import requests
import json
import uuid

def test_claude_working():
    """Simple test to show Claude is working with credits"""
    
    print("TESTING CLAUDE WITH NEW CREDITS")
    print("="*50)
    
    url = "http://localhost:8008/api/cia/chat"
    user_id = str(uuid.uuid4())
    session_id = f"claude-test-{int(time.time())}"
    
    payload = {
        "message": "I need help renovating my kitchen. I want new cabinets and granite countertops in Chicago 60614. My budget is $25,000.",
        "user_id": user_id,
        "session_id": session_id
    }
    
    print(f"User ID: {user_id}")
    print(f"Message: {payload['message']}")
    print("\nSending to CIA agent...")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n[SUCCESS] Claude responded:")
            print(f"Phase: {data.get('current_phase')}")
            print(f"Ready for JAA: {data.get('ready_for_jaa')}")
            
            # Show extracted information
            if data.get('collected_info'):
                print(f"\n[EXTRACTED] CLAUDE EXTRACTED INFORMATION:")
                info = data['collected_info']
                for key, value in info.items():
                    if value and value != []:
                        print(f"  {key}: {value}")
            
            print(f"\n[RESPONSE] Response preview: {data.get('response', '')[:200]}...")
            
            # Check if this has real Claude analysis
            response_text = data.get('response', '')
            if 'lincoln park' in response_text.lower() or 'chicago' in response_text.lower():
                print(f"\n[VERIFIED] CLAUDE IS WORKING! - Location-aware response detected")
            else:
                print(f"\n[WARNING] May be fallback response")
                
        else:
            print(f"[ERROR] Status: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")

if __name__ == "__main__":
    import time
    test_claude_working()