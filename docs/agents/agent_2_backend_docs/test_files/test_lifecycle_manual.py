import sys
sys.path.append(r'C:\Users\Not John Or Justin\Documents\instabids\ai-agents')

from datetime import datetime, timezone
from uuid import uuid4
from database_simple import db
import time

# Create a bid card and move it through the full lifecycle
bid_card_number = f'BC-LIFECYCLE-{int(datetime.now().timestamp())}'
bid_card_id = str(uuid4())

print("=== BID CARD LIFECYCLE TEST ===")
print(f"Card Number: {bid_card_number}")
print(f"Card ID: {bid_card_id}")
print("\nThis test will move a bid card through all statuses.")
print("Watch the admin dashboard to see real-time updates!\n")

# Status progression
statuses = [
    ('generated', 'Creating initial bid card...'),
    ('discovery', 'Moving to discovery phase...'),
    ('active', 'Activating for contractor bidding...'),
    ('pending_award', 'Moving to pending award...'),
    ('awarded', 'Awarding to contractor...'),
    ('in_progress', 'Work in progress...'),
    ('completed', 'Marking as completed!')
]

# Create initial bid card
bid_card_data = {
    'id': bid_card_id,
    'bid_card_number': bid_card_number,
    'project_type': 'Full Kitchen Renovation',
    'title': 'Lifecycle Test - Watch Me Move!',
    'description': 'This card will move through all statuses automatically',
    'status': 'generated',
    'contractor_count_needed': 3,
    'budget_min': 25000,
    'budget_max': 35000,
    'location_city': 'San Francisco',
    'location_state': 'CA', 
    'location_zip': '94105',
    'urgency_level': 'week',
    'complexity_score': 7,
    'bid_count': 0,
    'interested_contractors': 0,
    'allows_questions': True,
    'requires_bid_before_message': True,
    'visibility': 'public',
    'created_at': datetime.now(timezone.utc).isoformat(),
    'updated_at': datetime.now(timezone.utc).isoformat()
}

try:
    # Create the bid card
    result = db.client.table('bid_cards').insert(bid_card_data).execute()
    if result.data:
        print("[CREATED] Bid card created successfully!")
        print(f"  Status: {result.data[0]['status']}")
        print("\nStarting lifecycle progression in 3 seconds...")
        time.sleep(3)
        
        # Move through each status
        for i, (status, message) in enumerate(statuses[1:], 1):
            print(f"\n[STEP {i}] {message}")
            
            # Update the status
            update_result = db.client.table('bid_cards').update({
                'status': status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', bid_card_id).execute()
            
            if update_result.data:
                print(f"  [OK] Status updated to: {status}")
                print("  --> Check dashboard for real-time update!")
                
                # Wait 5 seconds between status changes
                if i < len(statuses) - 1:
                    print("  Waiting 5 seconds before next status...")
                    time.sleep(5)
            else:
                print(f"  [FAIL] Failed to update status to {status}")
                
        print("\n[COMPLETE] Lifecycle test finished!")
        print("The bid card should have moved through all statuses in the dashboard.")
        
except Exception as e:
    print(f"[ERROR] {e}")