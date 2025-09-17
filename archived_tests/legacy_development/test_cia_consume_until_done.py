#!/usr/bin/env python3
"""
Test CIA by consuming stream until [DONE] to ensure state management runs
"""
import requests
import json
import uuid
import sys
import io
import time

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8008"

def test_cia_until_done():
    """Test CIA streaming by consuming until [DONE] marker"""
    
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    
    print("=" * 60)
    print("CIA CONSUME UNTIL [DONE] TEST")
    print("=" * 60)
    print(f"Session ID: {session_id}")
    print(f"Time: {time.strftime('%H:%M:%S')}")
    
    request_data = {
        "messages": [{"role": "user", "content": "I need deck repair in 10001"}],
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": session_id
    }
    
    print(f"\n[{time.strftime('%H:%M:%S')}] Sending request...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/cia/stream",
            json=request_data,
            timeout=45,  # Longer timeout
            stream=True
        )
        
        if response.status_code == 200:
            print(f"[{time.strftime('%H:%M:%S')}] ✓ Streaming started")
            
            # Read until [DONE] - this is critical
            chunk_count = 0
            found_done = False
            content_chunks = []
            
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    line_str = line.decode()
                    
                    # Show progress
                    if chunk_count % 20 == 0:
                        print(f"  Chunk {chunk_count}...")
                    
                    # Look for content
                    if line_str.startswith("data: "):
                        data_part = line_str[6:]  # Remove "data: "
                        if data_part == "[DONE]":
                            found_done = True
                            print(f"  ✓ Found [DONE] at chunk {chunk_count}")
                            break
                        elif data_part.strip():
                            try:
                                chunk_data = json.loads(data_part)
                                if "choices" in chunk_data:
                                    content = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if content:
                                        content_chunks.append(content)
                            except:
                                pass
            
            full_response = "".join(content_chunks)
            print(f"\n[{time.strftime('%H:%M:%S')}] Stream completed")
            print(f"  Total chunks: {chunk_count}")
            print(f"  [DONE] found: {found_done}")
            print(f"  Response length: {len(full_response)} chars")
            
            if found_done:
                print("  ✓ State management should have run after [DONE]")
                
                # Wait for state management to complete
                print(f"\n[{time.strftime('%H:%M:%S')}] Waiting 5 seconds for state management...")
                time.sleep(5)
                
                # Check for bid card
                print(f"\n[{time.strftime('%H:%M:%S')}] Checking for potential bid card...")
                bid_card_response = requests.get(
                    f"{BASE_URL}/api/cia/conversation/{session_id}/potential-bid-card"
                )
                
                if bid_card_response.status_code == 200:
                    bid_card_data = bid_card_response.json()
                    print("✓ POTENTIAL BID CARD CREATED!")
                    print(f"  ID: {bid_card_data.get('id')}")
                    print(f"  Completion: {bid_card_data.get('completion_percentage')}%")
                    return True
                else:
                    print("✗ No potential bid card found")
                    print(f"  Status: {bid_card_response.status_code}")
                    return False
            else:
                print("  ✗ [DONE] not found - stream incomplete")
                return False
                
        else:
            print(f"✗ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("Testing CIA by consuming stream until [DONE] marker")
    success = test_cia_until_done()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ SUCCESS: CIA CREATES POTENTIAL BID CARDS!")
    else:
        print("✗ FAILED: CIA still not creating bid cards")
        print("Check logs for 'Starting CIA agent state management...'")

if __name__ == "__main__":
    main()