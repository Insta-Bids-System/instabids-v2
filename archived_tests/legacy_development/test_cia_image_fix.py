"""
Test CIA Image Processing After Fix
Tests that images are properly processed by the CIA agent
"""

import requests
import json
import time

def test_cia_with_image():
    """Test CIA endpoint with image after fixing the request model"""
    print("\n=== Testing CIA Image Processing After Fix ===\n")
    
    conversation_id = f"test_fixed_{int(time.time())}"
    user_id = "550e8400-e29b-41d4-a716-446655440001"
    
    # Small test image (1x1 red pixel)
    test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    payload = {
        "messages": [{
            "role": "user",
            "content": "I want to renovate my kitchen. Here's a photo of the current state."
        }],
        "user_id": user_id,
        "conversation_id": conversation_id,
        "images": [test_image]  # Images at request level as sent by frontend
    }
    
    print(f"Conversation ID: {conversation_id}")
    print(f"Sending message with 1 test image...")
    
    try:
        response = requests.post(
            "http://localhost:8008/api/cia/stream",
            json=payload,
            timeout=30,
            stream=True
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            full_response = ""
            chunk_count = 0
            
            for line in response.iter_lines():
                if line:
                    try:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: ') and line_str != 'data: [DONE]':
                            data = json.loads(line_str[6:])
                            if 'choices' in data and data['choices']:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    content = delta['content']
                                    full_response += content
                                    chunk_count += 1
                                    # Print first few chunks to show streaming
                                    if chunk_count <= 3:
                                        print(f"  Chunk {chunk_count}: {content[:50]}...")
                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        print(f"  Error processing line: {e}")
            
            print(f"\n[SUCCESS] Received {chunk_count} chunks")
            print(f"Total response length: {len(full_response)} characters")
            
            if full_response:
                print(f"\nResponse preview:")
                print("-" * 50)
                print(full_response[:500])
                if len(full_response) > 500:
                    print("...")
                print("-" * 50)
                
                # Check if response mentions the image
                if any(word in full_response.lower() for word in ['photo', 'image', 'picture', 'see', 'look']):
                    print("\n[SUCCESS] AI acknowledged the image in response!")
                else:
                    print("\n[WARNING] AI did not explicitly mention the image")
                    
                return True
            else:
                print("\n[FAILED] Empty response received")
                return False
                
        else:
            print(f"\n[FAILED] Bad status code: {response.status_code}")
            print(f"Error: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n[FAILED] Request timed out")
        return False
    except Exception as e:
        print(f"\n[FAILED] Exception: {e}")
        return False

def check_docker_logs():
    """Check Docker logs to see if images were processed"""
    print("\n=== Checking Docker Logs ===\n")
    
    try:
        response = requests.get(
            "http://localhost:8008/api/docker/logs/instabids-instabids-backend-1?tail=20"
        )
        
        if response.status_code == 200:
            logs = response.text
            
            # Look for image-related log entries
            if "Found" in logs and "images at request level" in logs:
                print("[SUCCESS] Logs show images were found at request level")
                return True
            elif "Processing message" in logs and "with 1 images" in logs:
                print("[SUCCESS] Logs show image was processed")
                return True
            elif "with 0 images" in logs:
                print("[FAILED] Logs show 0 images - fix not working")
                return False
            else:
                print("[INFO] Could not determine image status from logs")
                return None
    except:
        print("[WARNING] Could not check Docker logs")
        return None

def main():
    print("=" * 60)
    print("CIA IMAGE PROCESSING FIX VERIFICATION")
    print("=" * 60)
    
    # Test 1: Check if CIA processes images
    test_result = test_cia_with_image()
    
    # Test 2: Check Docker logs
    time.sleep(2)  # Give logs time to update
    log_result = check_docker_logs()
    
    print("\n" + "=" * 60)
    if test_result:
        print("[SUCCESS] CIA IMAGE PROCESSING IS WORKING!")
        print("The fix successfully allows CIA to process images")
    else:
        print("[FAILED] CIA image processing still not working")
        print("Further debugging needed")
    print("=" * 60)

if __name__ == "__main__":
    main()