import requests
import json
import time

# Test BSA with GPT-4 configuration after model migration
print("=== COMPREHENSIVE BSA GPT-4 TEST ===")
print("Testing BSA after migration from 'gpt-4o' to 'gpt-4'")
start_time = time.time()

try:
    response = requests.post('http://localhost:8008/api/bsa/fast-stream', json={
        'contractor_id': '87f93fbd-151d-4f17-9311-70ef9ba5256f',
        'message': 'show me available turf projects within 30 miles of ZIP code 33442',
        'session_id': 'test-gpt4-comprehensive-verification'
    }, timeout=20, stream=True)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("\n=== BSA STREAMING RESPONSE (GPT-4) ===")
        full_response = ""
        chunk_count = 0
        status_messages = []
        error_found = False
        
        for line in response.iter_lines():
            if line:
                try:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = json.loads(line_str[6:])
                        chunk_count += 1
                        
                        # Track status messages
                        if 'status' in data:
                            status_messages.append(data['status'])
                            print(f"[{data['status']}]: {data.get('message', '')}")
                        
                        # Track content
                        elif 'choices' in data and data['choices']:
                            content = data['choices'][0].get('delta', {}).get('content', '')
                            if content:
                                full_response += content
                                print(content, end='', flush=True)
                        
                        # Check for errors
                        elif 'error' in data:
                            print(f"\nERROR: {data['error']}")
                            error_found = True
                        
                        # Check for completion
                        elif 'done' in data:
                            print("\n\n=== RESPONSE COMPLETE ===")
                            break
                            
                except Exception as parse_err:
                    print(f"\nParse error: {parse_err}")
                    continue
        
        elapsed = time.time() - start_time
        print(f"\n=== COMPREHENSIVE TEST RESULTS ===")
        print(f"Total time: {elapsed:.2f} seconds")
        print(f"Chunks received: {chunk_count}")
        print(f"Response length: {len(full_response)} chars")
        print(f"Status flow: {' -> '.join(status_messages)}")
        print(f"Errors found: {error_found}")
        
        # Evaluate GPT-4 migration results (Unicode-safe)
        if error_found:
            print("ERROR MIGRATION INCOMPLETE - BSA has errors with GPT-4")
        elif len(full_response) > 100:
            print("SUCCESS GPT-4 MIGRATION SUCCESSFUL - BSA generating content!")
            if elapsed < 10.0:
                print(f"SUCCESS PERFORMANCE GOOD: Response in {elapsed:.2f} seconds")
            else:
                print(f"SLOW: Response took {elapsed:.2f} seconds")
        elif len(full_response) == 0:
            print("ERROR EMPTY RESPONSE ISSUE - GPT-4 not generating content")
            print("Need to investigate DeepAgents configuration")
        else:
            print("PROGRESS PARTIAL SUCCESS - Some content but may need verification")
            
        # Check for location-specific content
        location_indicators = ['33442', 'turf', 'projects', 'available', 'mile']
        found_indicators = [ind for ind in location_indicators if ind.lower() in full_response.lower()]
        
        if found_indicators:
            print(f"SUCCESS LOCATION SEARCH WORKING: Found {found_indicators}")
        else:
            print("ERROR LOCATION SEARCH MAY BE BROKEN")
            
        print(f"\n=== RESPONSE PREVIEW (first 300 chars) ===")
        print(full_response[:300] + "..." if len(full_response) > 300 else full_response or "NO CONTENT")
        
    else:
        print(f"HTTP Error: Status {response.status_code}")
        print(response.text[:300])
        
except Exception as e:
    elapsed = time.time() - start_time
    print(f"Request failed after {elapsed:.2f} seconds: {e}")

print("\n=== TEST COMPLETE ===")
print("Migration from 'gpt-4o' to 'gpt-4' verification finished")