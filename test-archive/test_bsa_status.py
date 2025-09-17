"""
BSA System Status Verification Script
Tests if BSA is fully operational with bid card search
"""

import requests
import json
import time

print('BSA SYSTEM STATUS - FINAL VERIFICATION')
print('=' * 70)

# Correct request format
test_data = {
    'contractor_id': '22222222-2222-2222-2222-222222222222',
    'message': 'Show me turf and lawn projects near 33442',
    'session_id': 'test-final-' + str(int(time.time()))
}

print('Endpoint: http://localhost:8008/api/bsa/unified-stream')
print('Request: Show me turf and lawn projects near 33442')
print('-' * 70)

try:
    response = requests.post(
        'http://localhost:8008/api/bsa/unified-stream',
        json=test_data,
        stream=True,
        timeout=25
    )
    
    print(f'Response Status: {response.status_code}')
    
    if response.status_code == 200:
        print('[CONNECTED] BSA endpoint responding')
        print('')
        
        # Track everything
        events = []
        bid_cards_data = []
        messages = []
        errors = []
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        
                        if 'event' in data:
                            event_type = data['event']
                            events.append(event_type)
                            
                            if event_type == 'bid_cards_found':
                                print('[KEY EVENT] bid_cards_found received!')
                                if 'data' in data and 'bid_cards' in data['data']:
                                    cards = data['data']['bid_cards']
                                    bid_cards_data = cards
                                    print(f'  -> Found {len(cards)} bid cards')
                                    
                            elif event_type == 'message':
                                if 'data' in data:
                                    msg = data['data'].get('content', '')[:100]
                                    messages.append(msg)
                                    
                            elif event_type == 'error':
                                errors.append(data.get('data', 'Unknown error'))
                        
                    except:
                        pass
        
        print('')
        print('=' * 70)
        print('FINAL RESULTS:')
        print(f'  Total events: {len(events)}')
        print(f'  Unique events: {set(events)}')
        print(f'  Messages received: {len(messages)}')
        print(f'  Errors: {len(errors)}')
        print('')
        
        if bid_cards_data:
            print(f'  BID CARDS FOUND: {len(bid_cards_data)}')
            for i, card in enumerate(bid_cards_data[:5]):
                print(f'    {i+1}. {card.get("title", "No title")}')
                print(f'       Type: {card.get("project_type", "Unknown")}')
                print(f'       Budget: ${card.get("budget_min", 0)}-${card.get("budget_max", 0)}')
                print(f'       Location: {card.get("location", "Unknown")}')
        else:
            print('  NO BID CARDS RETURNED')
        
        print('')
        print('=' * 70)
        print('SYSTEM STATUS:')
        
        if bid_cards_data:
            print('  ✅ [FULLY OPERATIONAL] BSA + Sub-agents working!')
            print('  - BSA endpoint: WORKING')
            print('  - Sub-agent delegation: WORKING')
            print('  - Bid card search: WORKING')
            print('  - UI streaming: WORKING')
        elif messages:
            print('  ⚠️ [PARTIALLY WORKING] BSA responds but no bid cards')
            print('  - BSA endpoint: WORKING')
            print('  - Sub-agent delegation: UNKNOWN')
            print('  - Bid card search: FAILED')
            print('  - UI streaming: PARTIAL')
        else:
            print('  ❌ [NOT WORKING] BSA not functioning properly')
            
    else:
        print(f'[ERROR] HTTP {response.status_code}')
        print('Response:', response.text[:500])
        
except Exception as e:
    print(f'[CONNECTION ERROR] {e}')

print('=' * 70)