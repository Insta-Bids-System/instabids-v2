#!/usr/bin/env python3
"""Test RFI flow with CIA agent"""

import requests
import json
import asyncio

def test_rfi_streaming():
    """Test the streaming endpoint with RFI context"""
    
    url = "http://localhost:8008/api/cia/stream"
    
    # Create request with RFI context embedded in the message
    rfi_context = {
        "rfi_id": "test-rfi-123",
        "bid_card_id": "test-bid-card",
        "contractor_name": "ABC Landscaping",
        "request_type": "pictures",
        "specific_items": ["front yard", "sprinkler system", "lawn condition"],
        "priority": "high"
    }
    
    # Format the RFI message similar to what the frontend would send
    rfi_message = f"""[RFI CONTEXT] ABC Landscaping has requested pictures for your project.

They need the following information:
1. front yard
2. sprinkler system
3. lawn condition

[PRIORITY: HIGH] This information is needed urgently.

I need help gathering pictures that a contractor requested."""

    payload = {
        "messages": [
            {
                "role": "user",
                "content": rfi_message,
                "images": []
            }
        ],
        "conversation_id": f"rfi_test_{asyncio.get_event_loop().time()}",
        "user_id": "550e8400-e29b-41d4-a716-446655440001",  # Demo homeowner
        "max_tokens": 500,
        "model_preference": "gpt-4o"
    }
    
    print("Testing RFI flow with streaming endpoint...")
    print(f"Sending message with RFI context")
    print(f"URL: {url}")
    print(f"Message preview: {rfi_message[:200]}...")
    
    try:
        # Make streaming request
        response = requests.post(url, json=payload, stream=True, timeout=30)
        
        if response.status_code == 200:
            print("\n✅ Streaming response received:")
            print("-" * 50)
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        if data_str == '[DONE]':
                            print("\n[Stream Complete]")
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_response += content
                                    print(content, end='', flush=True)
                            elif 'error' in data:
                                print(f"\n❌ Error in stream: {data['error']}")
                                break
                        except json.JSONDecodeError:
                            # Might be an error message
                            print(f"\nRaw data: {data_str}")
            
            print("\n" + "-" * 50)
            print(f"\n📝 Full Response Length: {len(full_response)} characters")
            
            # Check if response acknowledges RFI context
            rfi_keywords = ["photo", "picture", "contractor", "landscaping", "yard", "sprinkler"]
            acknowledged = any(keyword.lower() in full_response.lower() for keyword in rfi_keywords)
            
            if acknowledged:
                print("✅ Response appears to acknowledge RFI context!")
            else:
                print("⚠️ Response may not have acknowledged RFI context")
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_rfi_streaming()