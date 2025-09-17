#!/usr/bin/env python3
"""Test REAL multi-turn CIA conversation with timing and state tracking"""

import asyncio
import json
import aiohttp
import time
from datetime import datetime

class CIAConversationTester:
    def __init__(self):
        self.url = "http://localhost:8008/api/cia/stream"
        self.conversation_id = f"multi-turn-test-{int(time.time())}"
        self.user_id = "11111111-1111-1111-1111-111111111111"
        self.transcript = []
        self.total_latency = 0
        self.turn_count = 0
        
    async def send_message(self, message: str, images: list = None):
        """Send a message and get response with timing"""
        self.turn_count += 1
        print(f"\n{'='*60}")
        print(f"TURN {self.turn_count} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        print(f"USER: {message}")
        print("-" * 40)
        
        start_time = time.time()
        
        data = {
            "messages": [{"content": message, "role": "user", "images": images or []}],
            "conversation_id": self.conversation_id,
            "user_id": self.user_id
        }
        
        accumulated = ""
        first_chunk_time = None
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json=data) as response:
                if response.status != 200:
                    print(f"ERROR: Status {response.status}")
                    return None
                
                print("CIA: ", end="", flush=True)
                
                async for line in response.content:
                    line_text = line.decode('utf-8').strip()
                    if line_text.startswith("data: "):
                        data_str = line_text[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data_obj = json.loads(data_str)
                            if 'choices' in data_obj:
                                content = data_obj['choices'][0]['delta'].get('content', '')
                                if content:
                                    if first_chunk_time is None:
                                        first_chunk_time = time.time()
                                    print(content, end="", flush=True)
                                    accumulated += content
                        except json.JSONDecodeError:
                            pass
        
        end_time = time.time()
        total_time = end_time - start_time
        time_to_first_chunk = (first_chunk_time - start_time) if first_chunk_time else 0
        
        print(f"\n\nTiming:")
        print(f"  - Time to first chunk: {time_to_first_chunk:.2f}s")
        print(f"  - Total response time: {total_time:.2f}s")
        print(f"  - Characters received: {len(accumulated)}")
        print(f"  - Speed: {len(accumulated)/total_time:.0f} chars/sec")
        
        self.total_latency += total_time
        self.transcript.append({
            "turn": self.turn_count,
            "user": message,
            "cia": accumulated,
            "latency": total_time,
            "first_chunk": time_to_first_chunk,
            "chars": len(accumulated)
        })
        
        return accumulated
    
    async def run_full_conversation(self):
        """Run a complete multi-turn conversation simulating a real homeowner"""
        print("\n" + "="*80)
        print("STARTING MULTI-TURN CIA CONVERSATION TEST")
        print(f"Session ID: {self.conversation_id}")
        print("="*80)
        
        # Turn 1: Initial greeting
        response = await self.send_message(
            "Hi, I need help with my backyard. It's a mess and I want to make it nice for summer"
        )
        await asyncio.sleep(1)  # Natural pause
        
        # Turn 2: Provide more details
        response = await self.send_message(
            "Well it's about 2000 sq ft, mostly dirt right now. I'm thinking maybe a deck and some landscaping. Maybe a pool if it's not too expensive"
        )
        await asyncio.sleep(1)
        
        # Turn 3: Timeline question
        response = await self.send_message(
            "I'd like to have it done by June for my daughter's graduation party. Is that realistic?"
        )
        await asyncio.sleep(1)
        
        # Turn 4: Budget discussion
        response = await self.send_message(
            "I was hoping to keep it under 50k but I could go up to 75k if it includes everything - the deck, landscaping, and a small pool"
        )
        await asyncio.sleep(1)
        
        # Turn 5: Location
        response = await self.send_message(
            "I'm in Austin, Texas. Near the Domain area if that helps"
        )
        await asyncio.sleep(1)
        
        # Turn 6: Contractor preference
        response = await self.send_message(
            "I'd prefer a mid-size company - not a huge corporation but also not just one guy. Someone reliable with a good team"
        )
        await asyncio.sleep(1)
        
        # Turn 7: Special requirements
        response = await self.send_message(
            "Do they handle permits? And I definitely want someone who's insured. Also, can they do lighting? I want it to look nice at night"
        )
        await asyncio.sleep(1)
        
        # Turn 8: Ready to proceed
        response = await self.send_message(
            "This sounds great! So what happens next? Do you create the bid card for me?"
        )
        
        # Print summary
        print("\n" + "="*80)
        print("CONVERSATION SUMMARY")
        print("="*80)
        print(f"Total turns: {self.turn_count}")
        print(f"Total time: {self.total_latency:.2f}s")
        print(f"Average response time: {self.total_latency/self.turn_count:.2f}s")
        print(f"Total characters exchanged: {sum(t['chars'] for t in self.transcript)}")
        
        # Check for bid card creation
        last_response = self.transcript[-1]['cia'] if self.transcript else ""
        if 'bid card' in last_response.lower():
            print("\nBID CARD MENTIONED - System appears to be creating bid card")
        else:
            print("\nNO BID CARD MENTION - System may not be creating bid card")
        
        # Save transcript
        with open(f'cia_transcript_{self.conversation_id}.json', 'w') as f:
            json.dump(self.transcript, f, indent=2)
        print(f"\nFull transcript saved to: cia_transcript_{self.conversation_id}.json")
        
        return self.transcript

async def main():
    tester = CIAConversationTester()
    await tester.run_full_conversation()

if __name__ == "__main__":
    asyncio.run(main())