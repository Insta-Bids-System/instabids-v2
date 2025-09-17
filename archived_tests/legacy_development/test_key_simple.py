import requests
import json

# Test CIA streaming endpoint with RFI context
payload = {
    "messages": [
        {
            "role": "user",
            "content": "Hello, I need help with my lawn project. Can you help me?",
            "images": []
        }
    ],
    "conversation_id": "test_working",
    "user_id": "test-user",
    "max_tokens": 100,
    "model_preference": "gpt-4o"
}

print("Testing CIA endpoint...")

try:
    response = requests.post(
        "http://localhost:8008/api/cia/stream", 
        json=payload, 
        stream=True, 
        timeout=15
    )
    
    if response.status_code == 200:
        print("SUCCESS! CIA is responding:")
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str == '[DONE]':
                        print("\nStream completed successfully!")
                        break
                    try:
                        data = json.loads(data_str)
                        if 'choices' in data:
                            content = data['choices'][0].get('delta', {}).get('content', '')
                            if content:
                                print(content, end='', flush=True)
                        elif 'error' in data:
                            print(f"Error in stream: {data['error']}")
                            break
                    except:
                        print(f"Raw data: {data_str}")
                        
    else:
        print(f"Failed: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")

print("\nTesting complete.")