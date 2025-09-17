#!/usr/bin/env python3
"""
Test BSA Intelligent Search Endpoint
"""

import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json

# Test the BSA intelligent search endpoint
url = "http://localhost:8008/api/bsa/intelligent-search"
payload = {
    "message": "Show me turf and lawn projects near ZIP 33442",
    "contractor_id": "test-contractor-001",
    "session_id": "test-session-intelligent"
}

print("Testing BSA Intelligent Search")
print("Message:", payload['message'])
print("-" * 50)

try:
    # Send request
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("\nResponse received!")
        print("Status:", data.get('status'))
        
        # Check for bid cards
        bid_cards = data.get('bid_cards', [])
        print(f"\nFound {len(bid_cards)} bid cards:")
        
        for bc in bid_cards[:5]:  # Show first 5
            print(f"  - {bc.get('bid_card_number')}: {bc.get('project_type')} in {bc.get('location_zip')}")
            print(f"    Status: {bc.get('status')}, Created: {bc.get('created_at')[:10] if bc.get('created_at') else 'N/A'}")
        
        # Show search metadata
        metadata = data.get('metadata', {})
        if metadata:
            print(f"\nSearch metadata:")
            print(f"  Total found: {metadata.get('total_found')}")
            print(f"  Search time: {metadata.get('search_time_ms')}ms")
            print(f"  LLM used: {metadata.get('llm_used')}")
    else:
        print(f"Error: Status {response.status_code}")
        print(response.text[:500])
        
except Exception as e:
    print(f"Error: {e}")