"""
Test with correct field names from the database schema
"""

import requests
import json

def test_correct_fields():
    bid_card_id = '4109e91e-4a8f-461f-a4e7-5a978c7f9655'
    base_url = 'http://localhost:8008'

    print('Testing with correct field names...')
    
    # Use the correct field names from the actual schema
    correct_fields = [
        ('budget_range_max', 50000),  # integer field
        ('estimated_timeline', '6-8 weeks'),  # varchar field
        ('project_complexity', 'Medium'),  # varchar field 
        ('contractor_size_preference', 'Medium to Large'),
        ('quality_expectations', 'High Quality')
    ]

    success_count = 0
    for field_name, field_value in correct_fields:
        payload = {
            'field_name': field_name,
            'field_value': field_value,
            'source': 'test_correction'
        }
        
        response = requests.put(f'{base_url}/api/cia/potential-bid-cards/{bid_card_id}/field', json=payload)
        print(f'{field_name}: {response.status_code}')
        if response.status_code == 200:
            success_count += 1
            print(f'  SUCCESS: {field_value}')
        else:
            try:
                error = response.json()
                print(f'  Error: {error}')
            except:
                print(f'  Error text: {response.text}')
    
    print(f'\nUpdated {success_count}/{len(correct_fields)} fields successfully')
    
    # Now check the bid card completion
    print('\nChecking bid card completion after corrections...')
    conversation_id = 'ui_test_conv_1755144639'
    
    response = requests.get(f'{base_url}/api/cia/conversation/{conversation_id}/potential-bid-card')
    if response.status_code == 200:
        bid_card = response.json()
        completion = bid_card.get('completion_percentage', 0)
        ready = bid_card.get('ready_for_conversion', False)
        
        print(f'Completion: {completion}%')
        print(f'Ready for conversion: {ready}')
        
        if completion > 70:
            print('[SUCCESS] High completion rate achieved!')
        
        return bid_card, ready
    else:
        print(f'Error checking bid card: {response.status_code}')
        return None, False

if __name__ == "__main__":
    test_correct_fields()