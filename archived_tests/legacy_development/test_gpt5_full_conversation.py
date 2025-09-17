#!/usr/bin/env python3
"""Test full multi-turn CIA conversation with working GPT-5"""

import asyncio
import json
import aiohttp
import time
import uuid
from datetime import datetime

class GPT5ConversationTester:
    def __init__(self):
        self.url = "http://localhost:8008/api/cia/stream"
        # Use proper UUID for session to avoid database errors
        self.conversation_id = str(uuid.uuid4())
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
                            elif 'error' in data_obj:
                                print(f"\nERROR: {data_obj['error']}")
                                return None
                        except json.JSONDecodeError:
                            pass
        
        end_time = time.time()
        total_time = end_time - start_time
        time_to_first_chunk = (first_chunk_time - start_time) if first_chunk_time else 0
        
        print(f"\n\nTiming:")
        print(f"  - Time to first chunk: {time_to_first_chunk:.2f}s")
        print(f"  - Total response time: {total_time:.2f}s")
        print(f"  - Characters received: {len(accumulated)}")
        if accumulated:
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
    
    async def run_complete_conversation(self):
        """Run a complete multi-turn conversation to test all CIA features"""
        print("\n" + "="*80)
        print("TESTING COMPLETE CIA CONVERSATION WITH GPT-5")
        print(f"Session ID: {self.conversation_id}")
        print("="*80)
        
        # Turn 1: Initial greeting with project mention
        await self.send_message(
            "Hi! I want to completely renovate my backyard. It's currently just dirt and weeds."
        )
        await asyncio.sleep(2)
        
        # Turn 2: Provide project details
        await self.send_message(
            "It's about 1500 square feet. I'm thinking of adding a deck, some landscaping, maybe a fire pit, and possibly a small pool or hot tub."
        )
        await asyncio.sleep(2)
        
        # Turn 3: Timeline discussion
        await self.send_message(
            "I'd like to have it done by summer - maybe in about 4 months. Is that realistic for this kind of project?"
        )
        await asyncio.sleep(2)
        
        # Turn 4: Budget conversation
        await self.send_message(
            "My budget is flexible but I was hoping to keep it under $80,000. Could go up to $100k if it's really worth it."
        )
        await asyncio.sleep(2)
        
        # Turn 5: Location specifics
        await self.send_message(
            "I'm in Denver, Colorado. Specifically in the Highlands neighborhood. Do you need my exact address?"
        )
        await asyncio.sleep(2)
        
        # Turn 6: Contractor preferences
        await self.send_message(
            "I'd prefer a medium-sized company. Not a huge corporation but also someone with a proper team and insurance. Quality is more important than lowest price."
        )
        await asyncio.sleep(2)
        
        # Turn 7: Special requirements
        await self.send_message(
            "A few things: I have a dog so the yard needs to be pet-friendly. Also, I want good drainage because we get heavy rains. And I definitely want lighting for evening use."
        )
        await asyncio.sleep(2)
        
        # Turn 8: Ready to proceed
        await self.send_message(
            "This all sounds great! I'm ready to move forward. What's the next step? Do you create a bid card for me now?"
        )
        await asyncio.sleep(2)
        
        # Turn 9: Confirmation and signup
        await self.send_message(
            "Yes, I want to proceed with creating the bid card. How do I sign up and get this started?"
        )
        
        # Analysis
        print("\n" + "="*80)
        print("CONVERSATION ANALYSIS")
        print("="*80)
        
        # Performance metrics
        print(f"Total turns: {self.turn_count}")
        print(f"Total conversation time: {self.total_latency:.2f}s")
        print(f"Average response time: {self.total_latency/self.turn_count:.2f}s")
        print(f"Total characters: {sum(t['chars'] for t in self.transcript)}")
        
        # Fastest and slowest turns
        times = [t['latency'] for t in self.transcript]
        print(f"Fastest response: {min(times):.2f}s")
        print(f"Slowest response: {max(times):.2f}s")
        
        # Check conversation quality
        full_conversation = " ".join([t['cia'] for t in self.transcript])
        
        print(f"\n--- CONVERSATION QUALITY ANALYSIS ---")
        
        # Check for InstaBids messaging
        instabids_mentions = full_conversation.lower().count('instabids')
        print(f"InstaBids mentions: {instabids_mentions}")
        
        # Check for key concepts
        concepts = {
            'local economy': 'local' in full_conversation.lower() and 'economy' in full_conversation.lower(),
            'corporate middlemen': 'corporate' in full_conversation.lower(),
            'cost savings': 'save' in full_conversation.lower() or 'savings' in full_conversation.lower(),
            'bid card': 'bid card' in full_conversation.lower(),
            'contractor tiers': 'tier' in full_conversation.lower(),
            'AI capabilities': 'ai' in full_conversation.lower() or 'artificial' in full_conversation.lower()
        }
        
        for concept, present in concepts.items():
            status = "✅" if present else "❌"
            print(f"{status} {concept}: {'Present' if present else 'Missing'}")
        
        # Check for bid card creation
        bid_card_mentioned = any('bid card' in t['cia'].lower() for t in self.transcript[-3:])
        signup_mentioned = any('sign' in t['cia'].lower() for t in self.transcript[-2:])
        
        print(f"\n--- CONVERSION ANALYSIS ---")
        print(f"Bid card creation mentioned: {'✅ Yes' if bid_card_mentioned else '❌ No'}")
        print(f"Signup process mentioned: {'✅ Yes' if signup_mentioned else '❌ No'}")
        
        # Save detailed transcript
        with open(f'gpt5_transcript_{self.conversation_id}.json', 'w') as f:
            json.dump({
                'session_id': self.conversation_id,
                'total_turns': self.turn_count,
                'total_time': self.total_latency,
                'avg_response_time': self.total_latency/self.turn_count,
                'transcript': self.transcript,
                'analysis': {
                    'instabids_mentions': instabids_mentions,
                    'concepts_present': concepts,
                    'bid_card_mentioned': bid_card_mentioned,
                    'signup_mentioned': signup_mentioned
                }
            }, f, indent=2)
        
        print(f"\nFull transcript saved to: gpt5_transcript_{self.conversation_id}.json")
        
        return self.transcript

async def main():
    tester = GPT5ConversationTester()
    await tester.run_complete_conversation()

if __name__ == "__main__":
    asyncio.run(main())