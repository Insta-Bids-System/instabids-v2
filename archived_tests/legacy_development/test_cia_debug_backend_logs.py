#!/usr/bin/env python3
"""
Test CIA streaming while monitoring backend logs for debugging
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

def test_cia_with_log_monitoring():
    """Test CIA streaming and provide timing for log monitoring"""
    
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    
    print("=" * 60)
    print("CIA STREAMING TEST WITH LOG MONITORING")
    print("=" * 60)
    print(f"Session ID: {session_id}")
    print(f"Time: {time.strftime('%H:%M:%S')}")
    print("\nMONITOR BACKEND LOGS FOR:")
    print(f"- '[CIA] Handling conversation - User: {user_id}'")
    print(f"- '[CIA] Created potential bid card:'")
    print(f"- 'CIA agent state management error:'")
    
    request_data = {
        "messages": [{"role": "user", "content": "I need deck repair in Manhattan 10001, budget around $5000"}],
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": session_id
    }
    
    print(f"\n[{time.strftime('%H:%M:%S')}] 1. Sending to CIA streaming endpoint...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/cia/stream",
            json=request_data,
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            print(f"[{time.strftime('%H:%M:%S')}] ✓ CIA streaming started")
            
            # Read a few chunks to let the backend process
            chunk_count = 0
            for chunk in response.iter_lines():
                if chunk:
                    chunk_count += 1
                    if chunk_count <= 3:  # Show first few chunks
                        print(f"  Chunk {chunk_count}: {chunk.decode()[:100]}...")
                    
                    if chunk_count >= 10:  # Stop after 10 chunks
                        break
            
            print(f"[{time.strftime('%H:%M:%S')}] ✓ Streaming completed, received {chunk_count} chunks")
            
            # Wait a moment for backend processing
            time.sleep(2)
            
            # Check for potential bid card
            print(f"\n[{time.strftime('%H:%M:%S')}] 2. Checking for potential bid card...")
            bid_card_response = requests.get(
                f"{BASE_URL}/api/cia/conversation/{session_id}/potential-bid-card"
            )
            
            if bid_card_response.status_code == 200:
                bid_card_data = bid_card_response.json()
                print("✓ POTENTIAL BID CARD FOUND!")
                print(f"  ID: {bid_card_data.get('id')}")
                print(f"  Completion: {bid_card_data.get('completion_percentage')}%")
                return True
            elif bid_card_response.status_code == 404:
                print("✗ No potential bid card found")
                print("\nDEBUG CHECKLIST:")
                print("1. Check backend logs for '[CIA] Handling conversation'")
                print("2. Check backend logs for '[CIA] Created potential bid card'")
                print("3. Check backend logs for 'CIA agent state management error'")
                print("4. Verify handle_conversation method is being called")
                return False
            else:
                print(f"✗ Error checking bid card: {bid_card_response.status_code}")
                return False
        else:
            print(f"✗ CIA streaming failed: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("Testing CIA streaming with backend log monitoring guidance")
    print("Watch backend logs in Docker for debugging information")
    
    success = test_cia_with_log_monitoring()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ CIA CREATES POTENTIAL BID CARDS")
    else:
        print("✗ CIA NOT CREATING BID CARDS - CHECK BACKEND LOGS")
        print("\nTo check backend logs:")
        print("docker logs instabids-instabids-backend-1 --tail 50")

if __name__ == "__main__":
    main()