"""
Simple test of the COIA API to debug the issue
"""
import asyncio
import aiohttp
import json

async def test_coia_simple():
    session_id = "debug-test-" + str(int(asyncio.get_event_loop().time()))
    
    messages = [
        "I am a General Contractor. Please show me available projects.",
        "Tell me more about the bathroom project.",
    ]
    
    async with aiohttp.ClientSession() as session:
        contractor_lead_id = None
        
        for i, message in enumerate(messages, 1):
            print(f"\n{'='*50}")
            print(f"TEST {i}: {message}")
            print('='*50)
            
            payload = {
                "message": message,
                "session_id": session_id
            }
            
            # Include contractor_lead_id if we have it from previous response
            if contractor_lead_id:
                payload["contractor_lead_id"] = contractor_lead_id
            
            print(f"Sending: {payload}")
            
            try:
                async with session.post("http://localhost:8008/api/coia/landing", json=payload) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"Success: {result.get('success')}")
                        print(f"Mode: {result.get('current_mode')}")
                        print(f"Response: {result.get('response', 'No response')[:200]}...")
                        
                        # Save contractor_lead_id for next request
                        contractor_lead_id = result.get("contractor_lead_id")
                        print(f"Contractor Lead ID: {contractor_lead_id}")
                        
                        if result.get('bidCards'):
                            print(f"SUCCESS: Bid Cards: {len(result['bidCards'])} found")
                        else:
                            print("ERROR: No bid cards")
                            
                    else:
                        error_text = await response.text()
                        print(f"ERROR {response.status}: {error_text[:500]}")
                        
            except Exception as e:
                print(f"EXCEPTION: {e}")
            
            if i < len(messages):
                print("Waiting 3 seconds...")
                await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(test_coia_simple())