#!/usr/bin/env python3
"""
Complete HomeownerProjectWorkspace Integration Test
Tests the full integration of the new workspace component
"""

import requests
import json

def test_integration():
    print("=== HOMEOWNER PROJECT WORKSPACE INTEGRATION TEST ===\n")
    
    # Test configuration
    backend_url = "http://localhost:8008"
    frontend_url = "http://localhost:5188"  # Latest frontend port
    test_user_id = "e6e47a24-95ad-4af3-9ec5-f17999917bc3"
    test_email = "test.homeowner@instabids.com"
    test_password = "testpass123"
    
    print("[TEST] CONFIGURATION:")
    print(f"   Backend: {backend_url}")
    print(f"   Frontend: {frontend_url}")
    print(f"   Test User: {test_email}")
    print(f"   User ID: {test_user_id}")
    print()
    
    # Step 1: Test Backend API
    print("[API] STEP 1: Testing Backend API...")
    try:
        response = requests.get(f"{backend_url}/api/bid-cards/homeowner/{test_user_id}", timeout=5)
        if response.ok:
            bid_cards = response.json()
            print(f"   [OK] API Success: {len(bid_cards)} bid cards found")
            
            if bid_cards:
                card = bid_cards[0]
                card_id = card['id']
                card_number = card['bid_card_number']
                project_type = card['project_type']
                
                print(f"   [CARD] First Card: {card_number}")
                print(f"   [PROJECT] Project: {project_type}")
                print(f"   [ID] Card ID: {card_id}")
                
                # Check data completeness
                extracted = card.get('bid_document', {}).get('all_extracted_data', {})
                images = extracted.get('images', [])
                description = extracted.get('project_description', '')
                
                print(f"   [IMAGES] Images: {len(images)} photos")
                print(f"   [DESC] Description: {'Yes' if description else 'No'}")
                
                return card_id, bid_cards
            else:
                print("   [ERROR] No bid cards found")
                return None, []
        else:
            print(f"   [ERROR] API Error: {response.status_code}")
            return None, []
    except Exception as e:
        print(f"   [ERROR] Request Failed: {e}")
        return None, []

def test_workspace_features(card_id, bid_cards):
    print("\n[WORKSPACE] STEP 2: Testing Workspace Features...")
    
    if not card_id:
        print("   [SKIP] Skipping - no bid cards available")
        return
    
    card = bid_cards[0]
    extracted = card.get('bid_document', {}).get('all_extracted_data', {})
    
    # Test data mapping for workspace
    print("   [DATA] Testing Data Mapping:")
    
    # Required fields for workspace
    required_fields = [
        'bid_card_number', 'project_type', 'budget_min', 'budget_max',
        'contractor_count_needed', 'urgency_level', 'status'
    ]
    
    missing_fields = []
    for field in required_fields:
        if field in card and card[field] is not None:
            print(f"      [OK] {field}: {card[field]}")
        else:
            print(f"      [MISSING] {field}: Missing")
            missing_fields.append(field)
    
    # Test extracted data fields
    print("   [EXTRACTED] Testing Extracted Data:")
    extracted_fields = [
        'project_description', 'location', 'material_preferences',
        'special_requirements', 'images', 'intention_score'
    ]
    
    for field in extracted_fields:
        value = extracted.get(field)
        if value:
            if field == 'images':
                print(f"      [OK] {field}: {len(value)} items")
            elif isinstance(value, list):
                print(f"      [OK] {field}: {len(value)} items")
            elif isinstance(value, dict):
                print(f"      [OK] {field}: {len(value)} keys")
            else:
                print(f"      [OK] {field}: {str(value)[:50]}...")
        else:
            print(f"      [EMPTY] {field}: Empty")
    
    return len(missing_fields) == 0

def test_navigation_routes():
    print("\n[ROUTES] STEP 3: Testing Navigation Routes...")
    
    routes_to_test = [
        "/login",
        "/dashboard", 
        "/bid-cards/test-id",  # Should work with our new route
        "/chat"
    ]
    
    frontend_url = "http://localhost:5188"
    
    for route in routes_to_test:
        try:
            response = requests.get(f"{frontend_url}{route}", timeout=3)
            if response.status_code == 200:
                print(f"   [OK] {route}: Accessible")
            else:
                print(f"   [WARN] {route}: Status {response.status_code}")
        except Exception as e:
            print(f"   [ERROR] {route}: Failed - {e}")

def main():
    print("[START] Starting Complete Integration Test...\n")
    
    # Test backend integration
    card_id, bid_cards = test_integration()
    
    # Test workspace data mapping
    if bid_cards:
        test_workspace_features(card_id, bid_cards)
    
    # Test navigation routes
    test_navigation_routes()
    
    print("\n" + "="*60)
    print("[MANUAL] TESTING INSTRUCTIONS:")
    print("="*60)
    print(f"1. [BROWSER] Open browser: http://localhost:5188")
    print(f"2. [LOGIN] Login: test.homeowner@instabids.com / testpass123")
    print(f"3. [DASHBOARD] Dashboard: Should show {len(bid_cards) if bid_cards else 0} bid cards")
    print(f"4. [CLICK] Click any bid card to open HomeownerProjectWorkspace")
    print("5. [TEST] Test workspace features:")
    print("   - Overview tab with project summary")
    print("   - Photo gallery with images") 
    print("   - Project details and statistics")
    print("   - Chat tab for modifications")
    print("   - Navigation back to dashboard")
    print("6. [VERIFY] Verify all data displays correctly")
    
    if bid_cards:
        card = bid_cards[0]
        print(f"\n[DIRECT] WORKSPACE LINK:")
        print(f"   http://localhost:5188/bid-cards/{card['id']}")
    
    print("\n" + "="*60)
    print("[COMPLETE] Integration test complete! Ready for manual testing.")
    print("="*60)

if __name__ == "__main__":
    main()