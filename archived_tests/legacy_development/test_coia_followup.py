"""
Test COIA follow-up conversation to debug the issue
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def test_coia_followup():
    print("=" * 60)
    print("TESTING COIA FOLLOW-UP CONVERSATION")
    print("=" * 60)
    
    api_url = "http://localhost:8008/api/coia/landing"
    session_id = f"followup-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    messages = [
        "I am a General Contractor. Please show me available projects.",
        "Tell me more about the bathroom renovation project.",
        "What tools and materials would I need for this project?",
        "How much experience do you have with plumbing work?"
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, message in enumerate(messages, 1):
            print(f"\n{'='*40}")
            print(f"MESSAGE {i}: {message}")
            print('='*40)
            
            payload = {
                "message": message,
                "session_id": session_id
            }
            
            print(f"Sending to {api_url}...")
            start_time = datetime.now()
            
            try:
                async with session.post(api_url, json=payload) as response:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    
                    print(f"Response received in {elapsed:.2f} seconds")
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"Success: {result.get('success')}")
                        print(f"Mode: {result.get('current_mode')}")
                        print(f"Response: {result.get('response', '')[:200]}...")
                        
                        if result.get('bidCards'):
                            print(f"Bid Cards: {len(result['bidCards'])} found")
                        else:
                            print("No bid cards in response")
                            
                    else:
                        error_text = await response.text()
                        print(f"ERROR: {response.status}")
                        print(f"Error text: {error_text[:500]}...")
                        
            except Exception as e:
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"EXCEPTION after {elapsed:.2f} seconds: {e}")
            
            # Wait between messages
            if i < len(messages):
                print("Waiting 2 seconds before next message...")
                await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(test_coia_followup())