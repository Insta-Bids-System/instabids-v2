#!/usr/bin/env python3
"""Test CIA endpoints after root .env fix"""

import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load from root .env
root_env = Path(__file__).parent / '.env'
if root_env.exists():
    load_dotenv(root_env, override=True)

# Test configuration
BASE_URL = "http://localhost:8008"

def test_backend_health():
    """Test if backend is responsive"""
    try:
        response = requests.get(f"{BASE_URL}", timeout=5)
        print(f"[SUCCESS] Backend responding on port 8008")
        return True
    except Exception as e:
        print(f"[FAILED] Backend not responding: {e}")
        return False

def test_cia_chat_endpoint():
    """Test CIA chat endpoint with simple message"""
    try:
        # Test data
        chat_data = {
            "message": "I need help planning a kitchen remodel",
            "session_id": "test_session_123",
            "user_id": "test_user_456",
            "project_id": None
        }
        
        print(f"Testing CIA chat with: {chat_data['message']}")
        
        response = requests.post(
            f"{BASE_URL}/api/cia/chat",
            json=chat_data,
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] CIA chat working!")
            print(f"Response: {data.get('response', 'No response')[:100]}...")
            print(f"Session ID: {data.get('session_id')}")
            print(f"Phase: {data.get('current_phase')}")
            return True
        else:
            print(f"[FAILED] CIA chat returned {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"[FAILED] CIA chat error: {e}")
        return False

def test_cia_conversation_history():
    """Test conversation history endpoint"""
    try:
        session_id = "test_session_123"
        
        response = requests.get(
            f"{BASE_URL}/api/cia/conversation/{session_id}",
            timeout=10
        )
        
        print(f"Conversation history status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] Conversation history working!")
            print(f"Messages: {data.get('total_messages', 0)}")
            return True
        else:
            print(f"[FAILED] Conversation history returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[FAILED] Conversation history error: {e}")
        return False

def main():
    print("=== CIA Endpoint Testing (Post Root .env Fix) ===")
    print()
    
    # Check environment
    openai_key = os.getenv("OPENAI_API_KEY")
    supabase_url = os.getenv("SUPABASE_URL")
    
    print(f"OPENAI_API_KEY: {'Found' if openai_key else 'Missing'}")
    print(f"SUPABASE_URL: {'Found' if supabase_url else 'Missing'}")
    print()
    
    # Run tests
    results = []
    
    print("1. Testing backend health...")
    results.append(test_backend_health())
    print()
    
    print("2. Testing CIA chat endpoint...")
    results.append(test_cia_chat_endpoint())
    print()
    
    print("3. Testing conversation history...")
    results.append(test_cia_conversation_history())
    print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"=== Test Summary ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("[SUCCESS] All CIA endpoints working with root .env!")
    else:
        print("[WARNING] Some endpoints still have issues")

if __name__ == "__main__":
    main()