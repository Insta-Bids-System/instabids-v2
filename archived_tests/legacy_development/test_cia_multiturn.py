import requests
import json
import time
import uuid

# Create a new conversation ID for testing
conversation_id = str(uuid.uuid4())
user_id = 'test_user_' + str(int(time.time()))

print(f'Starting multi-turn conversation test')
print(f'Conversation ID: {conversation_id}')
print(f'User ID: {user_id}')
print('=' * 80)

# Build conversation with multiple turns
messages = []

# Turn 1
messages.append({'role': 'user', 'content': 'I need help with a roof repair - there is significant damage from a recent storm'})
messages.append({'role': 'assistant', 'content': 'I understand you have storm damage to your roof. This sounds urgent. Let me help you get this resolved quickly.'})

# Turn 2  
messages.append({'role': 'user', 'content': 'Its extremely urgent - we have water leaking in. Our zip is 90210. The damaged area is about 400 sq ft of shingles blown off.'})
messages.append({'role': 'assistant', 'content': 'Emergency roof repair in 90210 with active water leakage - this is critical. 400 sq ft of damage is substantial.'})

# Turn 3
messages.append({'role': 'user', 'content': 'The house is a two-story colonial, about 3000 sq ft total. The roof is asphalt shingles, probably 15 years old.'})
messages.append({'role': 'assistant', 'content': 'Got it - two-story colonial home with 15-year-old asphalt shingle roof. This helps contractors understand the scope.'})

# Turn 4
messages.append({'role': 'user', 'content': 'My budget is around 8000-10000 dollars for the repair. I need this done within 48 hours if possible.'})
messages.append({'role': 'assistant', 'content': 'Budget of 8000-10000 with 48-hour emergency timeline noted. I will prioritize finding contractors who can respond immediately.'})

# Turn 5
messages.append({'role': 'user', 'content': 'Yes, I can provide photos. The damage is on the north side of the house. Some of the underlayment is exposed.'})
messages.append({'role': 'assistant', 'content': 'Exposed underlayment increases urgency - this needs immediate weather protection. North side damage noted.'})

# Turn 6
messages.append({'role': 'user', 'content': 'My email is john.smith@example.com and phone is 555-0123. The property address is 123 Main St, Beverly Hills, CA 90210.'})
messages.append({'role': 'assistant', 'content': 'Contact information received. Property at 123 Main St, Beverly Hills will help contractors provide accurate estimates.'})

# Turn 7
messages.append({'role': 'user', 'content': 'I also noticed some damage to the gutters and fascia board. Might need those replaced too.'})
messages.append({'role': 'assistant', 'content': 'Additional gutter and fascia damage noted. This will be included in the scope for contractors to assess.'})

# Turn 8 - Final user message
messages.append({'role': 'user', 'content': 'Is there anything else you need to know? I want to make sure contractors have all the info they need.'})

print('Sending conversation with 8 turns to CIA streaming endpoint...')
print()

# Make API call with all messages
response = requests.post(
    'http://localhost:8008/api/cia/stream',
    json={
        'messages': messages,
        'conversation_id': conversation_id,
        'user_id': user_id,
        'max_tokens': 500,
        'model_preference': 'gpt-4o'
    },
    timeout=60,
    stream=True
)

if response.status_code == 200:
    print('AI Response (streaming):')
    print('-' * 40)
    full_response = ''
    for line in response.iter_lines():
        if line:
            line_text = line.decode('utf-8')
            if line_text.startswith('data: '):
                try:
                    data = json.loads(line_text[6:])
                    if 'content' in data:
                        print(data['content'], end='', flush=True)
                        full_response += data['content']
                except:
                    pass
    print()
    print('-' * 40)
    print(f'Total response length: {len(full_response)} characters')
else:
    print(f'Error: {response.status_code}')
    print(response.text[:500])

print()
print('=' * 80)
print('Checking potential bid card...')

# Try to get the bid card using conversation ID
bid_card_response = requests.get(
    f'http://localhost:8008/api/cia/conversation/{conversation_id}/potential-bid-card'
)

if bid_card_response.status_code == 200:
    bid_card = bid_card_response.json()
    if bid_card:
        print(f'\nBid Card Fields Extracted:')
        print('-' * 40)
        skip_fields = ['id', 'conversation_id', 'created_at', 'updated_at']
        for field, value in bid_card.items():
            if value and field not in skip_fields:
                print(f'{field}: {value}')
        
        # Calculate completion percentage
        total_fields = 12  # Key fields for bid card
        filled_fields = sum(1 for k, v in bid_card.items() if v and k not in skip_fields)
        completion = (filled_fields / total_fields) * 100
        print(f'\nCompletion: {completion:.0f}%')
    else:
        print('No bid card data found')
else:
    print(f'Could not retrieve bid card: {bid_card_response.status_code}')

print()
print('=' * 80)
print('\nFULL CONVERSATION TRANSCRIPT:')
print('=' * 80)
for i, msg in enumerate(messages):
    role = "USER" if msg['role'] == 'user' else "AI"
    print(f'\n{role}: {msg["content"]}')

if full_response:
    print(f'\nAI (Final): {full_response}')