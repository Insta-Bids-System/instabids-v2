#!/usr/bin/env python3
"""
Test BSA Sub-Agent Delegation - Verify DeepAgents framework working
"""

import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json
import time

print("\n" + "="*60)
print("  BSA SUB-AGENT DELEGATION TEST")
print("="*60)

# First verify bid cards exist
print("\n1. Verifying bid cards exist in database...")
url = "http://localhost:8008/api/bsa/intelligent-search"
payload = {
    "message": "Show me turf projects near 33442",
    "contractor_id": "test-contractor",
    "session_id": "verify-1"
}

response = requests.post(url, json=payload)
if response.status_code == 200:
    data = response.json()
    bid_cards = data.get('bid_cards', [])
    print(f"   ✅ Found {len(bid_cards)} bid cards in database")
    for bc in bid_cards[:3]:
        print(f"      - {bc.get('bid_card_number')}")

# Now test the unified-stream endpoint with delegation
print("\n2. Testing BSA unified-stream with sub-agent delegation...")
url = "http://localhost:8008/api/bsa/unified-stream"

test_messages = [
    "I need to find turf installation projects near 33442",
    "Search for lawn care bid cards in my area",
    "Show me available landscaping opportunities"
]

for i, message in enumerate(test_messages, 1):
    print(f"\n   Test {i}: {message}")
    print("   " + "-"*40)
    
    payload = {
        "contractor_id": f"test-contractor-{i}",
        "message": message,
        "session_id": f"delegation-test-{i}"
    }
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=10)
        
        # Track what happens
        statuses_seen = []
        chunks_received = 0
        error_found = None
        delegation_detected = False
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        
                        # Track statuses
                        if 'status' in data:
                            status = data['status']
                            if status not in statuses_seen:
                                statuses_seen.append(status)
                                print(f"      📊 {status}")
                        
                        # Track chunks
                        if 'chunk' in data:
                            chunks_received += 1
                            # Check for delegation keywords
                            chunk = data['chunk']
                            if 'delegat' in chunk.lower() or 'sub-agent' in chunk.lower():
                                delegation_detected = True
                        
                        # Track errors
                        if 'error' in data:
                            error_found = data['error']
                            
                    except json.JSONDecodeError:
                        pass
        
        # Report results
        if error_found:
            print(f"      ❌ Error: {error_found}")
        elif chunks_received > 0:
            print(f"      ✅ Received {chunks_received} response chunks")
            if delegation_detected:
                print(f"      ✅ Sub-agent delegation detected!")
        else:
            print(f"      ⚠️ No response chunks received")
            
    except requests.exceptions.Timeout:
        print(f"      ⏱️ Request timed out (might be processing)")
    except Exception as e:
        print(f"      ❌ Error: {e}")

print("\n" + "="*60)
print("  TEST COMPLETE")
print("="*60)