#!/usr/bin/env python3
"""
Test Iris conversation end-to-end after fixing timeout issues
"""

import requests
import json

def test_iris_conversation():
    """Test a real Iris conversation to verify timeout fixes"""
    
    print("🔄 Testing Iris conversation after timeout fixes...")
    
    # Test data
    test_request = {
        "message": "I want to redesign my kitchen with a modern farmhouse style",
        "user_id": "test_homeowner_123",
        "room_type": "kitchen",
        "session_id": "iris_test_session"
    }
    
    try:
        # Make API call to Iris
        print(f"📤 Sending request to Iris: {test_request['message']}")
        
        response = requests.post(
            "http://localhost:8008/api/iris/chat",
            json=test_request,
            timeout=30  # 30 second timeout
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Iris conversation working")
            print(f"💬 Response: {result['response'][:100]}...")
            print(f"💡 Suggestions: {result.get('suggestions', [])}")
            print(f"🔗 Session ID: {result.get('session_id')}")
            print(f"💾 Conversation ID: {result.get('conversation_id')}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout occurred - the self-referencing loop issue may still exist")
        return False
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        return False

def test_iris_openai_status():
    """Test if OpenAI API is working"""
    
    print("\n🔄 Testing OpenAI API status...")
    
    try:
        # Test basic health endpoint first
        health_response = requests.get("http://localhost:8008", timeout=10)
        print(f"📊 Backend health: {health_response.status_code}")
        
        # Check if OpenAI key is working by looking for specific response patterns
        test_request = {
            "message": "test",
            "user_id": "test_user",
        }
        
        response = requests.post(
            "http://localhost:8008/api/iris/chat",
            json=test_request,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '').lower()
            
            # Check if this is a fallback response or real AI response
            if any(phrase in response_text for phrase in [
                "i'm here to help you with your design inspiration",
                "tell me about your project",
                "what room are you working on"
            ]):
                print("⚠️  Using fallback responses (OpenAI API key issue or GPT models unavailable)")
                return "fallback"
            else:
                print("✅ OpenAI API working - received intelligent response")
                return "working"
        else:
            print(f"❌ API error: {response.status_code}")
            return "error"
            
    except Exception as e:
        print(f"❌ Error testing OpenAI status: {e}")
        return "error"

if __name__ == "__main__":
    print("Testing Iris system after timeout fixes")
    print("=" * 50)
    
    # Test OpenAI status first
    openai_status = test_iris_openai_status()
    
    # Test conversation
    conversation_success = test_iris_conversation()
    
    print("\n" + "=" * 50)
    print("📋 Test Results:")
    print(f"OpenAI API Status: {openai_status}")
    print(f"Conversation Success: {'✅ PASS' if conversation_success else '❌ FAIL'}")
    
    if conversation_success:
        print("\n🎉 Iris timeout issue appears to be FIXED!")
        print("The self-referencing HTTP loop has been resolved.")
    else:
        print("\n⚠️  Iris still has issues - timeout problem may persist.")