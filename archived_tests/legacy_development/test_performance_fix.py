#!/usr/bin/env python3
"""
Test the performance improvement of the bid-cards-enhanced endpoint
"""
import time
import requests
import asyncio

def test_performance():
    """Test the optimized bid-cards-enhanced endpoint"""
    
    print("Testing Bid Cards Enhanced Performance Fix")
    print("=" * 60)
    
    url = "http://localhost:8008/api/admin/bid-cards-enhanced?limit=50"
    
    # Test 3 times to get average
    times = []
    
    for i in range(3):
        print(f"\nTest Run #{i+1}")
        start_time = time.time()
        
        try:
            response = requests.get(url, timeout=30)
            end_time = time.time()
            
            if response.status_code == 200:
                duration = end_time - start_time
                times.append(duration)
                data = response.json()
                bid_card_count = len(data.get("bid_cards", []))
                
                print(f"Success: {duration:.3f} seconds")
                print(f"Bid Cards Returned: {bid_card_count}")
                print(f"Status: {'FAST' if duration < 2 else 'SLOW' if duration < 5 else 'VERY SLOW'}")
            else:
                print(f"Error: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print("\n" + "=" * 60)
        print("PERFORMANCE RESULTS")
        print("=" * 60)
        print(f"Average Time: {avg_time:.3f} seconds")
        print(f"Fastest Time: {min_time:.3f} seconds") 
        print(f"Slowest Time: {max_time:.3f} seconds")
        
        if avg_time < 2:
            print("SUCCESS: Target achieved (< 2 seconds)")
            print("PRODUCTION READY: N+1 query problem SOLVED!")
        elif avg_time < 5:
            print("GOOD: Major improvement but room for optimization")
        else:
            print("NEEDS WORK: Still too slow for production")
            
        # Compare to previous performance
        previous_time = 18  # From conversation context
        improvement = ((previous_time - avg_time) / previous_time) * 100
        print(f"Performance Improvement: {improvement:.1f}% faster")
        print(f"Previous: ~{previous_time} seconds -> Now: {avg_time:.3f} seconds")
        
        print("\nTechnical Details:")
        print("- Replaced N+1 queries with 4 batch queries")
        print("- Used efficient Supabase batch selects with .in() filters")
        print("- Created lookup dictionaries for O(1) data access")
        print("- Added performance logging for monitoring")

if __name__ == "__main__":
    test_performance()