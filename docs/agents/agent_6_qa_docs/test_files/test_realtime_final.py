import sys
sys.path.append(r'C:\Users\Not John Or Justin\Documents\instabids\ai-agents')

from datetime import datetime, timezone
from uuid import uuid4
from database_simple import db
import time

# Create multiple bid cards to test real-time updates
print("Creating multiple bid cards to test real-time dashboard updates...\n")

statuses = ['discovery', 'active', 'discovery']
project_types = ['Kitchen Remodel', 'Deck Installation', 'Home Addition']

for i, (status, project_type) in enumerate(zip(statuses, project_types)):
    bid_card_number = f'BC-LIVE-TEST-{int(datetime.now().timestamp())}-{i}'
    bid_card_data = {
        'id': str(uuid4()),
        'bid_card_number': bid_card_number,
        'project_type': project_type,
        'title': f'Real-Time Test #{i+1}',
        'description': f'Live test card {i+1} - should appear instantly',
        'status': status,
        'contractor_count_needed': 3,
        'budget_min': 10000 + (i * 5000),
        'budget_max': 20000 + (i * 5000),
        'location_city': 'Test City',
        'location_state': 'CA',
        'location_zip': '94105',
        'urgency_level': 'week',
        'complexity_score': 5 + i,
        'bid_count': 0,
        'interested_contractors': 0,
        'allows_questions': True,
        'requires_bid_before_message': True,
        'visibility': 'public',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    try:
        result = db.client.table('bid_cards').insert(bid_card_data).execute()
        if result.data:
            print(f'[CREATED] {bid_card_number}')
            print(f'  Type: {project_type}')
            print(f'  Status: {status}')
            print(f'  Budget: ${bid_card_data["budget_min"]:,} - ${bid_card_data["budget_max"]:,}')
            print()
        
        # Wait 2 seconds between creations to see them appear one by one
        if i < len(statuses) - 1:
            time.sleep(2)
            
    except Exception as e:
        print(f'[ERROR] Failed to create card {i+1}: {e}')

print("\n[DONE] Check the admin dashboard - all cards should have appeared in real-time!")