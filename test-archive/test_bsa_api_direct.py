#!/usr/bin/env python3
"""
Direct BSA API Test - Testing sub-agent delegation via API endpoint
"""

import os
import sys

# Set UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import requests
import json
import time
from datetime import datetime

def test_bsa_api():
    """Test BSA API with real sub-agent delegation"""
    
    print("\n" + "="*60)
    print("  BSA API TEST - PROVING SUB-AGENT WORKS")
    print("="*60)
    
    # API endpoint
    url = "http://localhost:8008/api/bsa/unified-stream"
    
    # Test messages
    test_messages = [
        "I'm a contractor looking for turf and lawn projects near ZIP 33442",
        "Show me available bid cards for lawn care projects",
        "Find turf installation opportunities in my area"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n🧑 TEST {i}: {message}")
        print("-" * 50)
        
        # Prepare request
        payload = {
            "contractor_id": "test-contractor-001",
            "message": message,
            "session_id": f"test-session-{i}"
        }
        
        try:
            # Send request
            start_time = time.time()
            response = requests.post(url, json=payload, stream=True)
            
            # Process streaming response
            print("🤖 BSA Response:")
            full_response = ""
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            
                            # Print status updates
                            if 'status' in data:
                                print(f"  📊 Status: {data['status']} - {data.get('message', '')}")
                            
                            # Collect response chunks
                            if 'chunk' in data:
                                chunk = data['chunk']
                                full_response += chunk
                                print(chunk, end='', flush=True)
                            
                            # Check for delegation
                            if 'tools' in data:
                                print(f"\n  🔧 Tools used: {data['tools']}")
                            
                            # Show completion
                            if 'completed' in data:
                                elapsed = time.time() - start_time
                                print(f"\n  ✅ Completed in {elapsed:.1f}s")
                                
                        except json.JSONDecodeError:
                            pass
            
            print(f"\n  📝 Full Response Length: {len(full_response)} chars")
            
            # Check if response contains bid cards
            if "BC-" in full_response or "bid card" in full_response.lower():
                print("  ✅ Response contains bid card references!")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print("\n" + "="*60)
        time.sleep(2)  # Delay between tests

if __name__ == "__main__":
    print("🚀 Starting BSA API Direct Test...")
    print(f"📅 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if backend is running
    try:
        health = requests.get("http://localhost:8008/health")
        if health.status_code == 200:
            print("✅ Backend is running on port 8008")
        else:
            print("⚠️ Backend returned status:", health.status_code)
    except:
        print("❌ Backend not running! Start with: cd ai-agents && python main.py")
        exit(1)
    
    test_bsa_api()
    print("\n✅ All tests completed!")