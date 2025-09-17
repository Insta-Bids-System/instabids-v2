"""
Test which fields failed and why
"""

import requests
import json

def test_failed_fields():
    bid_card_id = '4109e91e-4a8f-461f-a4e7-5a978c7f9655'
    base_url = 'http://localhost:8008'

    print('Testing field availability...')
    test_fields = [
        ('budget_max', '50000'),
        ('timeline_weeks', '6'), 
        ('property_type', 'Single Family Home')
    ]

    for field_name, field_value in test_fields:
        payload = {
            'field_name': field_name,
            'field_value': field_value,
            'source': 'test'
        }
        
        response = requests.put(f'{base_url}/api/cia/potential-bid-cards/{bid_card_id}/field', json=payload)
        print(f'{field_name}: {response.status_code}')
        if response.status_code != 200:
            try:
                error = response.json()
                print(f'  Error: {error}')
            except:
                print(f'  Error text: {response.text}')

if __name__ == "__main__":
    test_failed_fields()