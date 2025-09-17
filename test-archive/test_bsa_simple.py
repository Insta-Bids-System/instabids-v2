"""
Simple BSA test with shorter timeout
"""
import requests
import json

# Test data
data = {
    "contractor_id": "22222222-2222-2222-2222-222222222222",
    "message": "Show me turf projects near 33442",
    "session_id": "simple-test"
}

print("Testing BSA with simple request...")

try:
    response = requests.post(
        "http://localhost:8008/api/bsa/unified-stream",
        json=data,
        stream=True,
        timeout=30  # Longer timeout
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("Events received:")
        count = 0
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        event_data = json.loads(line_str[6:])
                        if event_data.get('type') == 'search_results':
                            print(f"✅ SEARCH RESULTS: {len(event_data.get('bid_cards', []))} cards")
                        elif event_data.get('type') == 'sub_agent_status':
                            print(f"📋 STATUS: {event_data.get('message', '')}")
                        elif 'choices' in event_data:
                            content = event_data['choices'][0]['delta'].get('content', '')
                            if content.strip():
                                print(f"💬 MESSAGE: {content[:50]}...")
                        else:
                            print(f"📦 EVENT: {event_data.get('type', 'unknown')}")
                        
                        count += 1
                        if count > 20:  # Limit output
                            print("... (more events)")
                            break
                    except:
                        print(f"📄 RAW: {line_str[:50]}...")
        
        print(f"\nTotal events: {count}")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Exception: {e}")