#!/usr/bin/env python3
"""
Test CIA streaming by consuming the ENTIRE stream to ensure state management runs
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

def test_cia_full_stream_consumption():
    """Test CIA streaming by consuming the ENTIRE stream"""
    
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    
    print("=" * 60)
    print("CIA FULL STREAM CONSUMPTION TEST")
    print("=" * 60)
    print(f"Session ID: {session_id}")
    print(f"Time: {time.strftime('%H:%M:%S')}")
    
    request_data = {
        "messages": [{"role": "user", "content": "I need deck repair in Manhattan 10001, budget around $5000"}],
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": session_id
    }
    
    print(f"\n[{time.strftime('%H:%M:%S')}] 1. Sending to CIA streaming endpoint...")
    print("CONSUMING ENTIRE STREAM to ensure state management runs...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/cia/stream",
            json=request_data,
            timeout=60,  # Longer timeout for full stream
            stream=True
        )
        
        if response.status_code == 200:
            print(f"[{time.strftime('%H:%M:%S')}] ✓ CIA streaming started")
            
            # Read ALL chunks until [DONE]
            chunk_count = 0
            done_received = False
            
            for chunk in response.iter_lines():
                if chunk:
                    chunk_count += 1
                    chunk_str = chunk.decode()
                    
                    # Show progress every 10 chunks
                    if chunk_count % 10 == 0:
                        print(f"  Processed {chunk_count} chunks...")
                    
                    # Check for [DONE] marker
                    if "[DONE]" in chunk_str:
                        done_received = True
                        print(f"  ✓ Received [DONE] marker at chunk {chunk_count}")
                        break
            
            print(f"[{time.strftime('%H:%M:%S')}] ✓ Stream consumed completely")
            print(f"  Total chunks: {chunk_count}")
            print(f"  [DONE] received: {done_received}")
            
            if done_received:
                print("  State management SHOULD have run after [DONE]")
            else:
                print("  WARNING: [DONE] not received - stream may have been cut off")
            
            # Wait a moment for async state management to complete
            print(f"\n[{time.strftime('%H:%M:%S')}] Waiting 3 seconds for async state management...")
            time.sleep(3)
            
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
                print("\nThe stream was consumed fully but bid card still not created.")
                print("Check backend logs for 'Starting CIA agent state management...'")
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
    print("Testing CIA streaming with FULL stream consumption")
    print("This ensures the state management code actually runs")
    
    success = test_cia_full_stream_consumption()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ CIA CREATES POTENTIAL BID CARDS (AFTER FULL STREAM)")
    else:
        print("✗ CIA NOT CREATING BID CARDS (EVEN WITH FULL STREAM)")
        print("\nCheck backend logs for:")
        print("- 'Starting CIA agent state management...'")
        print("- '[CIA] Handling conversation'")
        print("- '[CIA] Created potential bid card'")

if __name__ == "__main__":
    main()