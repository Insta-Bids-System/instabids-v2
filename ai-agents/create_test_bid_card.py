#!/usr/bin/env python3
"""
Create Test Bid Card for End-to-End Testing
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
from config.service_urls import get_backend_url

def create_test_bid_card():
    """Create a test bid card for integration testing"""
    
    print("CREATING TEST BID CARD FOR INTEGRATION TESTING")
    print("=" * 50)
    
    # Generate UUIDs for test data
    bid_card_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4()) 
    user_id = str(uuid.uuid4())
    
    print(f"Bid Card ID: {bid_card_id}")
    print(f"Project ID: {project_id}")
    print(f"Homeowner ID: {user_id}")
    
    # Test bid card data
    bid_card_data = {
        "id": bid_card_id,
        "project_id": project_id,
        "user_id": user_id,
        "title": "Kitchen Renovation with Intelligent Messaging Test",
        "description": "Complete kitchen remodel including cabinets, countertops, and appliances. This is a test project for the intelligent messaging system.",
        "budget_min": 15000,
        "budget_max": 25000,
        "timeline_start": datetime.now().isoformat(),
        "timeline_end": (datetime.now() + timedelta(days=30)).isoformat(),
        "timeline_flexibility": "flexible",
        "location_address": "123 Test Street", 
        "location_city": "Orlando",
        "location_state": "FL",
        "location_zip": "32801",
        "project_type": "kitchen renovation",
        "categories": ["kitchen", "cabinets", "countertops"],
        "requirements": ["licensed contractors only", "insurance required", "references needed"],
        "status": "active",
        "visibility": "public",
        "group_bid_eligible": False,
        "allows_questions": True,
        "requires_bid_before_message": False,
        "metadata": json.dumps({
            "test_data": True,
            "created_for": "intelligent_messaging_integration_test",
            "created_at": datetime.now().isoformat()
        })
    }
    
    try:
        # Try to create via API first
        response = requests.post(f"{get_backend_url()}/api/bid-cards", json=bid_card_data, timeout=30)
        
        if response.status_code == 200:
            print("SUCCESS: Bid card created via API")
            result = response.json()
            print(f"Created bid card: {result.get('id', 'unknown')}")
            return result.get('id', bid_card_id)
            
        else:
            print(f"API creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"API creation error: {e}")
    
    # Try direct database insertion
    print("\nTrying direct database insertion...")
    
    try:
        from database_simple import db
        
        # Insert test homeowner first
        homeowner_data = {
            "id": user_id,
            "user_id": user_id,  # Same as ID for simplicity
            "name": "Test Homeowner",
            "email": "test.homeowner@instabids.com",
            "phone": "+1-555-TEST-001",
            "address": "123 Test Street, Orlando, FL 32801",
            "created_at": datetime.now().isoformat()
        }
        
        db.client.table("homeowners").insert(homeowner_data).execute()
        print(f"Created test homeowner: {user_id}")
        
        # Insert test project
        project_data = {
            "id": project_id,
            "user_id": user_id,
            "name": "Kitchen Renovation Test Project", 
            "description": "Test project for intelligent messaging integration",
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        
        db.client.table("projects").insert(project_data).execute()
        print(f"Created test project: {project_id}")
        
        # Insert the bid card
        result = db.client.table("bid_cards").insert(bid_card_data).execute()
        
        if result.data:
            print(f"SUCCESS: Created test bid card {bid_card_id}")
            return bid_card_id
        else:
            print("FAILED: No data returned from bid card creation")
            return None
            
    except Exception as e:
        print(f"Database creation error: {e}")
        return None

def test_with_real_bid_card(bid_card_id):
    """Test intelligent messaging with real bid card"""
    
    if not bid_card_id:
        print("No bid card available for testing")
        return
    
    print(f"\nTESTING WITH REAL BID CARD: {bid_card_id}")
    print("-" * 50)
    
    # Test contact info blocking
    payload = {
        "content": "Hi! My email is john@contractor.com and phone is 555-123-4567. Please contact me directly.",
        "sender_type": "contractor",
        "sender_id": str(uuid.uuid4()),
        "bid_card_id": bid_card_id,
        "target_contractor_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(f"{get_backend_url()}/api/intelligent-messages/send", json=payload, timeout=45)
        result = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Content: '{payload['content'][:50]}...'")
        print(f"Approved: {result.get('approved', 'unknown')}")
        print(f"Decision: {result.get('agent_decision', 'unknown')}")
        print(f"Threats: {result.get('threats_detected', [])}")
        print(f"Message ID: {result.get('message_id', 'none')}")
        print(f"Error: {result.get('error', 'none')}")
        
        if not result.get('approved'):
            print("SUCCESS: Contact info correctly blocked with real bid card!")
        else:
            print("WARNING: Contact info not blocked")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    bid_card_id = create_test_bid_card()
    test_with_real_bid_card(bid_card_id)