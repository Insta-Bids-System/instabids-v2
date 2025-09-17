#!/usr/bin/env python3
"""
Debug where the API response with 985 bid cards is coming from
"""
import requests
import json
from config.service_urls import get_backend_url

def debug_api_response():
    """Debug the API response to find the source of fake 985 bid cards"""
    
    test_message = {
        "message": "show me available projects",
        "session_id": f"debug_985_{int(__import__('time').time())}",
        "contractor_lead_id": "debug_contractor_001"
    }
    
    print("Testing COIA chat API response structure...")
    
    try:
        response = requests.post(
            f'{get_backend_url()}/api/coia/chat',
            json=test_message,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"Response keys: {list(data.keys())}")
            
            # Check different bid card sources
            sources = {
                "bid_cards_attached": data.get("bid_cards_attached", []),
                "bidCards": data.get("bidCards", []), 
                "tool_results.bid_card_search": data.get("tool_results", {}).get("bid_card_search", {}),
                "messages": data.get("messages", [])
            }
            
            print("\n=== BID CARD SOURCES ===")
            for source_name, source_data in sources.items():
                if isinstance(source_data, list):
                    print(f"{source_name}: {len(source_data)} items")
                    if len(source_data) > 0:
                        # Show first item structure
                        first_item = source_data[0]
                        if isinstance(first_item, dict):
                            print(f"  Sample keys: {list(first_item.keys())[:5]}")
                elif isinstance(source_data, dict):
                    print(f"{source_name}: {source_data}")
                else:
                    print(f"{source_name}: {type(source_data)} - {str(source_data)[:100]}")
            
            # Check current mode
            current_mode = data.get("current_mode", "unknown")
            print(f"\nCurrent mode: {current_mode}")
            
            # Check success status
            success = data.get("success", "unknown")
            print(f"Success: {success}")
            
            # If there's a large list, investigate structure
            large_lists = [(name, source) for name, source in sources.items() 
                          if isinstance(source, list) and len(source) > 100]
            
            if large_lists:
                print(f"\n=== INVESTIGATING LARGE LISTS ===")
                for name, large_list in large_lists:
                    print(f"\n{name} has {len(large_list)} items")
                    
                    # Check for duplicates
                    if len(large_list) > 0 and isinstance(large_list[0], dict):
                        ids = [item.get("id") for item in large_list if item.get("id")]
                        unique_ids = set(ids)
                        print(f"  Unique IDs: {len(unique_ids)}")
                        print(f"  Duplicates: {len(large_list) - len(unique_ids)}")
                        
                        # Show sample items
                        print("  Sample items:")
                        for i, item in enumerate(large_list[:3]):
                            if isinstance(item, dict):
                                item_id = item.get("id", "NO_ID")
                                title = item.get("title", "NO_TITLE")
                                print(f"    {i+1}. {item_id}: {title}")
            
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_api_response()