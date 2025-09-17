import requests
import json
import time

# Create test bid card
bid_card_data = {
    'project_id': f'PROJ-REALTIME-{int(time.time())}',
    'contractor_id': 'CONT-TEST-123',
    'project_type': 'Bathroom Renovation',
    'status': 'discovery',
    'location': 'Real-Time Test Location',
    'timeline_weeks': 3,
    'budget_min': 8000,
    'budget_max': 12000,
    'homeowner_name': 'WebSocket Test User',
    'homeowner_email': 'websocket@test.com',
    'homeowner_phone': '555-9999',
    'contractor_name': 'Real-Time Contractor',
    'contractor_email': 'realtime@contractor.com',
    'contractor_phone': '555-8888',
    'items': [
        {
            'category': 'Materials',
            'description': 'Bathroom fixtures',
            'quantity': 1,
            'unit': 'set',
            'price_per_unit': 3000,
            'total_price': 3000
        }
    ],
    'notes': 'Testing WebSocket real-time updates - should appear instantly'
}

print('Creating bid card to test real-time updates...')
response = requests.post('http://localhost:8008/api/bid-cards/create', json=bid_card_data)
print(f'Status: {response.status_code}')
if response.status_code == 200:
    result = response.json()
    print(f'Created bid card ID: {result.get("bid_card_id")}')
    print('Check admin dashboard - it should appear immediately!')
else:
    print(f'Error: {response.text}')

# Now test updating the status
if response.status_code == 200:
    bid_card_id = result.get("bid_card_id")
    print(f'\nUpdating bid card {bid_card_id} status to "active"...')
    
    update_response = requests.put(
        f'http://localhost:8008/api/bid-cards/{bid_card_id}/status',
        json={'status': 'active'}
    )
    print(f'Update status: {update_response.status_code}')
    if update_response.status_code == 200:
        print('Status updated! Check dashboard for real-time update.')
    else:
        print(f'Update error: {update_response.text}')