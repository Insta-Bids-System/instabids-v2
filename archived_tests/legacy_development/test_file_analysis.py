#!/usr/bin/env python3
"""
Test File Analysis System - Real End-to-End Test
Tests the file review queue system with actual file uploads
"""

import requests
import json
from pathlib import Path

# Test data
BID_CARD_ID = "78c3f7cb-64d8-496e-b396-32b24d790252"
CONTRACTOR_ID = "22222222-2222-2222-2222-222222222222"
BACKEND_URL = "http://localhost:8008"

def test_clean_file():
    """Test uploading a clean file (should not be flagged)"""
    print("\nTEST 1: Clean file upload")
    
    clean_file = Path("C:/Users/Not John Or Justin/Documents/instabids/clean_proposal.pdf")
    
    if not clean_file.exists():
        print("Clean test file not found")
        return False
    
    # Submit bid with clean file
    with open(clean_file, 'rb') as f:
        files = {'files': ('clean_proposal.pdf', f, 'application/pdf')}
        data = {
            'bid_card_id': BID_CARD_ID,
            'contractor_id': CONTRACTOR_ID,
            'amount': '25000',
            'timeline_start': '2025-02-01T00:00:00Z',
            'timeline_end': '2025-03-15T00:00:00Z',
            'proposal': 'Clean proposal without contact info'
        }
        
        response = requests.post(f"{BACKEND_URL}/api/bid-cards-simple/submit-bid", 
                               files=files, data=data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Check if file was flagged
    if response.status_code == 200:
        result = response.json()
        flagged_files = result.get('flagged_files', [])
        
        if len(flagged_files) == 0:
            print("CLEAN FILE: Correctly passed through - not flagged")
            return True
        else:
            print(f"CLEAN FILE: Incorrectly flagged - {flagged_files}")
            return False
    else:
        print(f"API Error: {response.status_code} - {response.text}")
        return False

def test_contact_file():
    """Test uploading a file with contact info (should be flagged)"""
    print("\nTEST 2: File with contact info")
    
    contact_file = Path("C:/Users/Not John Or Justin/Documents/instabids/test_bid_proposal.pdf")
    
    if not contact_file.exists():
        print("Contact test file not found")
        return False
    
    # Submit bid with contact file
    with open(contact_file, 'rb') as f:
        files = {'files': ('test_bid_proposal.pdf', f, 'application/pdf')}
        data = {
            'bid_card_id': BID_CARD_ID,
            'contractor_id': CONTRACTOR_ID,
            'amount': '30000',
            'timeline_start': '2025-02-01T00:00:00Z',
            'timeline_end': '2025-03-15T00:00:00Z',
            'proposal': 'Proposal with contact information'
        }
        
        response = requests.post(f"{BACKEND_URL}/api/bid-cards-simple/submit-bid", 
                               files=files, data=data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Check if file was flagged
    if response.status_code == 200:
        result = response.json()
        flagged_files = result.get('flagged_files', [])
        
        if len(flagged_files) > 0:
            print("CONTACT FILE: Correctly flagged for review")
            print(f"   Flagged reason: {flagged_files[0].get('reason')}")
            print(f"   Confidence: {flagged_files[0].get('confidence')}")
            return True
        else:
            print("CONTACT FILE: Should have been flagged but wasn't")
            return False
    else:
        print(f"API Error: {response.status_code} - {response.text}")
        return False

def check_review_queue():
    """Check the file review queue"""
    print("\nCHECKING REVIEW QUEUE")
    
    response = requests.get(f"{BACKEND_URL}/api/file-review/queue?status=pending")
    
    if response.status_code == 200:
        queue = response.json()
        print(f"Review queue has {len(queue)} pending items")
        
        for item in queue:
            print(f"   - {item.get('file_name')} (confidence: {item.get('confidence_score')})")
            print(f"     Reason: {item.get('flagged_reason')}")
        
        return len(queue)
    else:
        print(f"Queue check failed: {response.status_code} - {response.text}")
        return 0

def check_review_stats():
    """Check review queue statistics"""
    print("\nCHECKING REVIEW STATS")
    
    response = requests.get(f"{BACKEND_URL}/api/file-review/stats")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"Review Stats:")
        print(f"   - Pending: {stats.get('pending')}")
        print(f"   - Approved: {stats.get('approved')}")
        print(f"   - Rejected: {stats.get('rejected')}")
        print(f"   - Total: {stats.get('total')}")
        return stats
    else:
        print(f"Stats check failed: {response.status_code} - {response.text}")
        return {}

def main():
    """Run all tests"""
    print("TESTING FILE ANALYSIS SYSTEM")
    print("=" * 50)
    
    # Test clean file
    clean_result = test_clean_file()
    
    # Test contact file  
    contact_result = test_contact_file()
    
    # Check review queue
    queue_count = check_review_queue()
    
    # Check stats
    stats = check_review_stats()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print(f"   Clean file test: {'PASS' if clean_result else 'FAIL'}")
    print(f"   Contact file test: {'PASS' if contact_result else 'FAIL'}")
    print(f"   Review queue items: {queue_count}")
    
    if clean_result and contact_result:
        print("\nALL TESTS PASSED - FILE ANALYSIS SYSTEM WORKING!")
        return True
    else:
        print("\nSOME TESTS FAILED - SYSTEM NEEDS DEBUGGING")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)