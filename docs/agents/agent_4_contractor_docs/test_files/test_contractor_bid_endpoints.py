"""
Test the new contractor bid card endpoints
Agent 4 - Contractor UX
Tests bid card viewing, bid submission, and bid tracking
"""

import asyncio
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8008"

def test_get_bid_card_contractor_view():
    """Test getting a bid card from contractor perspective"""
    print("\n=== TEST: Get Bid Card Contractor View ===")
    
    # Use a test contractor ID
    contractor_id = "test-contractor-123"
    
    # First, let's search for available bid cards
    search_response = requests.get(f"{BASE_URL}/search")
    print(f"Search response status: {search_response.status_code}")
    
    if search_response.status_code == 200:
        search_data = search_response.json()
        bid_cards = search_data.get("bid_cards", [])
        print(f"Found {len(bid_cards)} bid cards")
        
        if bid_cards:
            # Get details for the first bid card
            bid_card_id = bid_cards[0]["id"]
            print(f"\nGetting details for bid card: {bid_card_id}")
            
            # Test the new contractor view endpoint
            detail_response = requests.get(
                f"{BASE_URL}/bid-cards/{bid_card_id}/contractor-view",
                params={"contractor_id": contractor_id}
            )
            
            print(f"Detail response status: {detail_response.status_code}")
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                print("\nBid Card Details:")
                print(f"- Title: {detail_data.get('title')}")
                print(f"- Project Type: {detail_data.get('project_type')}")
                print(f"- Budget: ${detail_data['budget_range']['min']}-${detail_data['budget_range']['max']}")
                print(f"- Location: {detail_data['location']['city']}, {detail_data['location']['state']}")
                print(f"- Bids Received: {detail_data.get('bids_received_count')}/{detail_data.get('contractor_count_needed')}")
                print(f"- Already Bid: {detail_data.get('has_submitted_bid')}")
                return bid_card_id
            else:
                print(f"ERROR: {detail_response.text}")
    
    return None


def test_submit_bid(bid_card_id, contractor_id="test-contractor-456"):
    """Test submitting a bid on a bid card"""
    print("\n=== TEST: Submit Bid ===")
    
    bid_data = {
        "bid_card_id": bid_card_id,
        "contractor_id": contractor_id,
        "bid_amount": 15000.00,
        "timeline_days": 14,
        "message": "I'm experienced in this type of project and can deliver high quality work on time.",
        "included_items": {
            "materials": True,
            "permits": True,
            "cleanup": True,
            "warranty": True
        },
        "payment_terms": "30% upfront, 40% midway, 30% completion"
    }
    
    print(f"Submitting bid for ${bid_data['bid_amount']} with {bid_data['timeline_days']} day timeline")
    
    response = requests.post(
        f"{BASE_URL}/contractor-bids",
        json=bid_data
    )
    
    print(f"Submit response status: {response.status_code}")
    
    if response.status_code == 200:
        bid_response = response.json()
        print("\nBid Submitted Successfully!")
        print(f"- Bid ID: {bid_response.get('id')}")
        print(f"- Status: {bid_response.get('status')}")
        print(f"- Submitted At: {bid_response.get('submitted_at')}")
        return True
    else:
        print(f"ERROR: {response.text}")
        return False


def test_get_my_bids(contractor_id="test-contractor-456"):
    """Test getting all bids for a contractor"""
    print("\n=== TEST: Get My Bids ===")
    
    response = requests.get(
        f"{BASE_URL}/contractor/my-bids",
        params={"contractor_id": contractor_id}
    )
    
    print(f"My bids response status: {response.status_code}")
    
    if response.status_code == 200:
        bids_data = response.json()
        my_bids = bids_data.get("bids", [])
        print(f"\nFound {bids_data.get('total', 0)} bids")
        
        for bid in my_bids[:3]:  # Show first 3 bids
            print(f"\nBid Details:")
            print(f"- Project: {bid.get('project_title')}")
            print(f"- Location: {bid['location']['city']}, {bid['location']['state']}")
            print(f"- Amount: ${bid.get('bid_amount')}")
            print(f"- Status: {bid.get('status')}")
            print(f"- Submitted: {bid.get('submitted_at')}")
    else:
        print(f"ERROR: {response.text}")


def test_duplicate_bid_prevention(bid_card_id, contractor_id="test-contractor-456"):
    """Test that contractors can't bid twice on same project"""
    print("\n=== TEST: Duplicate Bid Prevention ===")
    
    bid_data = {
        "bid_card_id": bid_card_id,
        "contractor_id": contractor_id,
        "bid_amount": 20000.00,
        "timeline_days": 10,
        "message": "Trying to bid again with different price",
        "included_items": {
            "materials": True,
            "permits": False,
            "cleanup": True,
            "warranty": False
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/contractor-bids",
        json=bid_data
    )
    
    print(f"Duplicate bid response status: {response.status_code}")
    
    if response.status_code == 400:
        print("SUCCESS: System correctly prevented duplicate bid")
        print(f"Error message: {response.json().get('detail')}")
        return True
    else:
        print("FAIL: System allowed duplicate bid")
        return False


def run_all_tests():
    """Run all contractor bid endpoint tests"""
    print("CONTRACTOR BID ENDPOINTS TEST SUITE")
    print("=" * 50)
    
    # Test 1: Get bid card details
    bid_card_id = test_get_bid_card_contractor_view()
    
    if bid_card_id:
        # Test 2: Submit a bid with a new contractor
        contractor_id = "test-contractor-456"
        bid_submitted = test_submit_bid(bid_card_id, contractor_id)
        
        if bid_submitted:
            # Test 3: Get my bids for same contractor
            test_get_my_bids(contractor_id)
            
            # Test 4: Try duplicate bid with same contractor
            test_duplicate_bid_prevention(bid_card_id, contractor_id)
    
    print("\n" + "=" * 50)
    print("TEST SUITE COMPLETE")


if __name__ == "__main__":
    # Make sure backend is running on port 8008
    try:
        health_check = requests.get(BASE_URL)  # Root endpoint for health check
        if health_check.status_code == 200:
            print("Backend is running. Starting tests...")
            run_all_tests()
        else:
            print("Backend health check failed")
    except Exception as e:
        print(f"ERROR: Backend not running on port 8008. Start it with: cd ai-agents && python main.py")
        print(f"Error details: {e}")