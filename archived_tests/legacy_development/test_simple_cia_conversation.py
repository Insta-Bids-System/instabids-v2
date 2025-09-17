"""
Simple CIA conversation test to verify streaming and bid card creation
"""
import requests
import json
import time

def test_simple_conversation():
    session_id = f"test_{int(time.time())}"
    
    print("Testing simple CIA conversation...")
    print(f"Session ID: {session_id}")
    
    # Simple deck repair conversation
    message = "My deck is falling apart and needs to be rebuilt in ZIP 10001"
    
    request_data = {
        "messages": [{"role": "user", "content": message}],
        "user_id": "00000000-0000-0000-0000-000000000000",
        "session_id": session_id,
        "conversation_id": session_id
    }
    
    try:
        print("Sending message to CIA...")
        response = requests.post(
            "http://localhost:8008/api/cia/stream",
            json=request_data,
            timeout=15,
            stream=True
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("Response chunks:")
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if data.get('content'):
                                print(f"Chunk {chunk_count}: {data['content'][:50]}...")
                                chunk_count += 1
                                if chunk_count > 5:  # Limit output
                                    print("... (truncated)")
                                    break
                        except:
                            continue
            
            print(f"Received {chunk_count} chunks")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("Request timed out - CIA may be taking too long")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple_conversation()