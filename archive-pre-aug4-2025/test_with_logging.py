#!/usr/bin/env python3
"""
Test conversation and capture backend logs
"""
import asyncio
import requests
import subprocess
import time

async def test_with_backend_logging():
    """Test conversation while monitoring backend logs"""
    
    print("Testing conversation with backend monitoring...")
    print("IMPORTANT: Make sure your backend server is running in a separate terminal!")
    print("You should see log messages there showing the error.")
    print("")
    
    # Create a session ID 
    session_id = f"logged_test_{int(time.time())}"
    print(f"Session ID: {session_id}")
    print("")
    
    # Send test message
    message_data = {
        "message": "I need help with a kitchen renovation",
        "images": [],
        "session_id": session_id
    }
    
    print("Sending message to API...")
    print("WATCH YOUR BACKEND TERMINAL FOR ERROR MESSAGES!")
    print("")
    
    try:
        response = requests.post(
            "http://localhost:8008/api/cia/chat",
            json=message_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"API Response received")
            print(f"Response text: {result.get('response', '')[:100]}...")
        else:
            print(f"API Error: {response.status_code}")
            
    except Exception as e:
        print(f"Request failed: {e}")
        return
    
    # Check if it was saved
    await asyncio.sleep(1)
    
    print("\nChecking if conversation was saved...")
    history_response = requests.get(f"http://localhost:8008/api/cia/conversation/{session_id}")
    
    if history_response.status_code == 200:
        data = history_response.json()
        if data.get('total_messages', 0) > 0:
            print(f"SUCCESS: Found {data['total_messages']} messages in database!")
        else:
            print("FAILURE: No messages saved to database")
            print("\nCHECK YOUR BACKEND TERMINAL FOR THE ERROR MESSAGE!")
            print("Look for: '[CIA] Warning: Could not save to database: ...'")

if __name__ == "__main__":
    asyncio.run(test_with_backend_logging())