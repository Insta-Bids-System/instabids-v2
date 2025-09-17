import os
import requests
import json

# Load key from environment
from dotenv import load_dotenv
load_dotenv()

working_key = os.getenv("OPENAI_API_KEY")
if not working_key:
    print("Error: OPENAI_API_KEY not set in environment")
    exit(1)

# Test CIA streaming endpoint with RFI context
rfi_message = """[RFI CONTEXT] ABC Landscaping has requested pictures for your project.

They need the following information:
1. front yard
2. sprinkler system  
3. lawn condition

[PRIORITY: HIGH] This information is needed urgently.

I need help gathering pictures that a contractor requested."""

payload = {
    "messages": [
        {
            "role": "user",
            "content": rfi_message,
            "images": []
        }
    ],
    "conversation_id": f"rfi_test_working",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "max_tokens": 200,
    "model_preference": "gpt-4o"
}

print("Testing CIA with working OpenAI key...")
print("URL: http://localhost:8008/api/cia/stream")

# Patch the backend environment
import subprocess
subprocess.run([
    "docker", "exec", "instabids-instabids-backend-1", 
    "bash", "-c", f'export OPENAI_API_KEY="{working_key}"'
], capture_output=True)

try:
    response = requests.post(
        "http://localhost:8008/api/cia/stream", 
        json=payload, 
        stream=True, 
        timeout=30,
        headers={"Authorization": f"Bearer {working_key}"}
    )
    
    if response.status_code == 200:
        print("\n✅ SUCCESS! CIA streaming is working:")
        print("-" * 50)
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        if 'choices' in data:
                            content = data['choices'][0].get('delta', {}).get('content', '')
                            if content:
                                full_response += content
                                print(content, end='', flush=True)
                        elif 'error' in data:
                            print(f"\nError: {data['error']}")
                            break
                    except:
                        print(f"\nRaw: {data_str}")
        
        print(f"\n\n✅ RFI CONTEXT WORKING! Response length: {len(full_response)} chars")
        
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")