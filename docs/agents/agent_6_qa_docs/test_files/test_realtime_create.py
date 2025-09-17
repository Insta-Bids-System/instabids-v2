import sys
sys.path.append(r'C:\Users\Not John Or Justin\Documents\instabids\ai-agents')

from datetime import datetime, timezone
from uuid import uuid4
from database_simple import db

# Create a new bid card directly in Supabase
bid_card_number = f'BC-REALTIME-{int(datetime.now().timestamp())}'
bid_card_data = {
    'id': str(uuid4()),
    'bid_card_number': bid_card_number,
    'project_type': 'Bathroom Renovation',
    'title': 'WebSocket Real-Time Test',
    'description': 'Testing if this appears instantly in admin dashboard',
    'status': 'discovery',
    'contractor_count_needed': 2,
    'budget_min': 8000,
    'budget_max': 12000,
    'location_city': 'Real-Time City',
    'location_state': 'RT',
    'location_zip': '12345',
    'urgency_level': 'week',
    'complexity_score': 5,
    'bid_count': 0,
    'interested_contractors': 0,
    'allows_questions': True,
    'requires_bid_before_message': True,
    'visibility': 'public',
    'created_at': datetime.now(timezone.utc).isoformat(),
    'updated_at': datetime.now(timezone.utc).isoformat()
}

print(f'Creating bid card {bid_card_number}...')
try:
    result = db.client.table('bid_cards').insert(bid_card_data).execute()
    if result.data:
        print(f'[SUCCESS] Created successfully!')
        print(f'   ID: {result.data[0]["id"]}')
        print(f'   Number: {result.data[0]["bid_card_number"]}')
        print(f'   Status: {result.data[0]["status"]}')
        print('\n[CHECK] Check the admin dashboard - it should appear IMMEDIATELY!')
        
        # Now update the status after a short delay
        import time
        print('\nWaiting 3 seconds then updating status...')
        time.sleep(3)
        
        update_result = db.client.table('bid_cards').update({
            'status': 'active',
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', result.data[0]['id']).execute()
        
        if update_result.data:
            print(f'[SUCCESS] Status updated to ACTIVE!')
            print('   The dashboard should show the status change in real-time!')
    else:
        print('[ERROR] Failed to create bid card')
except Exception as e:
    print(f'[ERROR] Error: {e}')