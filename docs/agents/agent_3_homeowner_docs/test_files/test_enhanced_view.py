import requests
import json
import time

# Login as admin
print("Logging in as admin...")
login_response = requests.post('http://localhost:8008/api/admin/login', json={
    'email': 'info@jmholidaylighting.com',
    'password': 'InstaBids2025!',
    'remember_me': True
})

if login_response.status_code == 200:
    session_data = login_response.json()
    print(f"Login response: {json.dumps(session_data, indent=2)}")
    
    # Check if session is in the response
    if 'session' in session_data:
        session_id = session_data['session']['session_id']
    elif 'session_id' in session_data:
        session_id = session_data['session_id']
    else:
        # Try to extract from the data structure
        session_id = session_data.get('data', {}).get('session', {}).get('session_id') or session_data.get('data', {}).get('session_id')
    
    if not session_id:
        print("[FAIL] Could not find session_id in response")
        exit(1)
        
    print(f"[OK] Logged in successfully! Session ID: {session_id}")
    
    # Set headers for authenticated requests
    headers = {
        'Authorization': f'Bearer {session_id}',
        'Content-Type': 'application/json'
    }
    
    # Get enhanced bid cards
    print("\nFetching enhanced bid cards...")
    enhanced_response = requests.get(
        'http://localhost:8008/api/admin/bid-cards-enhanced',
        headers=headers
    )
    
    if enhanced_response.status_code == 200:
        bid_cards = enhanced_response.json()['bid_cards']
        print(f"[OK] Found {len(bid_cards)} enhanced bid cards")
        
        # Display sample enhanced data
        if bid_cards:
            sample = bid_cards[0]
            print(f"\nSample Enhanced Bid Card: {sample['id']}")
            print(f"Status: {sample['status']}")
            print(f"Project Budget: ${sample.get('project_budget', 0):,}")
            print(f"Timeline: {sample.get('project_timeline', 'N/A')}")
            print(f"Homeowner: {sample.get('homeowner_name', 'N/A')} ({sample.get('homeowner_email', 'N/A')})")
            print(f"Discovery Metrics:")
            print(f"  - Contractors Found: {sample.get('contractors_found', 0)}")
            print(f"  - Discovery Sources: {sample.get('discovery_sources', [])}")
            print(f"Outreach Progress:")
            print(f"  - Emails Sent: {sample.get('emails_sent', 0)}")
            print(f"  - Forms Filled: {sample.get('forms_filled', 0)}")
            print(f"  - Responses Received: {sample.get('responses_received', 0)}")
            print(f"Next Check-in: {sample.get('next_checkin', 'N/A')}")
    else:
        print(f"[FAIL] Failed to fetch enhanced bid cards: {enhanced_response.status_code}")
        print(enhanced_response.text)
else:
    print(f"[FAIL] Login failed: {login_response.status_code}")
    print(login_response.text)