#!/usr/bin/env python3
"""
Natural Multi-Turn CIA Conversation Testing
Test CIA agent with real conversation flows - no artificial limits
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

class CIAConversationTester:
    def __init__(self):
        self.base_url = "http://localhost:8008"
        self.conversation_id = None
        self.user_id = "test-user-001"
        
    async def start_conversation(self, persona_name):
        """Start a new conversation with the CIA"""
        self.conversation_id = f"conv-{persona_name}-{int(time.time())}"
        print(f"\nSTARTING CONVERSATION: {self.conversation_id}")
        print(f"PERSONA: {persona_name}")
        print("="*60)
        
    async def send_message(self, message):
        """Send message to CIA and capture streaming response"""
        if not self.conversation_id:
            raise ValueError("Must start conversation first")
            
        url = f"{self.base_url}/api/cia/stream"
        payload = {
            "messages": [{"role": "user", "content": message}],
            "conversation_id": self.conversation_id,
            "user_id": self.user_id
        }
        
        print(f"\nUSER: {message}")
        print("CIA: ", end="", flush=True)
        
        start_time = time.time()
        full_response = ""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"\nERROR {response.status}: {error_text}")
                        return None
                        
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                if data.get('content'):
                                    content = data['content']
                                    print(content, end="", flush=True)
                                    full_response += content
                                elif data.get('done'):
                                    break
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            print(f"\nCONNECTION ERROR: {e}")
            return None
            
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"\nResponse time: {response_time:.2f}s")
        return full_response
        
    async def natural_conversation(self, persona_name, conversation_flow):
        """Run a natural conversation with multiple turns"""
        await self.start_conversation(persona_name)
        
        turn_count = 0
        for user_message in conversation_flow:
            turn_count += 1
            print(f"\n--- TURN {turn_count} ---")
            
            response = await self.send_message(user_message)
            if not response:
                print(f"CONVERSATION FAILED AT TURN {turn_count}")
                break
                
            # Brief pause between turns (like real conversation)
            await asyncio.sleep(1)
            
        print(f"\nCONVERSATION COMPLETED: {turn_count} turns")
        return turn_count

async def main():
    tester = CIAConversationTester()
    
    # PERSONA 1: Budget-Conscious First-Time Renovator
    print("TESTING PERSONA 1: Budget-Conscious First-Time Renovator")
    budget_conscious_flow = [
        "Hi there! I'm looking to renovate my kitchen but I'm on a tight budget. Can you help?",
        "I'm thinking maybe $15,000 max? Is that realistic for a full kitchen?",
        "It's a pretty standard size - maybe 200 square feet. The cabinets are really dated from the 80s.",
        "What would you recommend I prioritize with that budget? New cabinets or appliances?",
        "I'm handy with basic stuff but I've never done anything this big. Do contractors usually work with homeowner help?",
        "That makes sense. How do I know if I'm getting a fair price? I don't want to overpay.",
        "What about the timeline? I host Thanksgiving every year so I'd need it done by November.",
        "Are there financing options if I need to go a bit over budget?",
        "This is really helpful! What's the next step to get started?",
        "Great! And what kind of contractors would you recommend for kitchen work?"
    ]
    
    await tester.natural_conversation("Budget-Conscious-Renovator", budget_conscious_flow)
    await asyncio.sleep(3)  # Pause between personas
    
    # PERSONA 2: Luxury-Focused Executive
    print("\n\nTESTING PERSONA 2: Luxury-Focused Executive")
    luxury_executive_flow = [
        "Hello. I need to completely redesign my home office. Money is not a concern - I want the best.",
        "I'm thinking $80,000 to $120,000 for a complete transformation. Custom everything.",
        "It's a 400 square foot room that currently has zero personality. I want it to wow clients.",
        "I need custom built-ins, high-end lighting, maybe a bar area, and the finest finishes.",
        "Timeline is critical - I have a major client presentation in 6 weeks. Can that work?",
        "Perfect. I also need this to be completely hassle-free. I travel constantly for work.",
        "What kind of guarantee do I get on the work? This needs to be absolutely perfect.",
        "I like that. What about design services? I need someone to handle the entire vision.",
        "Excellent. How quickly can we get started? I want the top contractors in the city.",
        "And what about permits and all that regulatory stuff? I assume you handle that?",
        "This sounds exactly what I need. Let's move forward immediately."
    ]
    
    await tester.natural_conversation("Luxury-Executive", luxury_executive_flow)
    await asyncio.sleep(3)
    
    # PERSONA 3: Cautious Retiree
    print("\n\nTESTING PERSONA 3: Cautious Retiree")
    cautious_retiree_flow = [
        "Good morning. My husband and I are looking to update our bathroom, but we're retired so we need to be careful.",
        "We've been in this house 30 years and the master bathroom really needs updating. It's getting hard to use.",
        "I'm worried about contractors though. We've heard so many horror stories from neighbors.",
        "The main issue is the shower - it's too high to step into safely. We need something accessible.",
        "Budget-wise, we're thinking maybe $25,000? Is that reasonable for a bathroom?",
        "We definitely want someone licensed and insured. How do we verify that?",
        "What about references? We'd want to talk to previous customers before deciding.",
        "Timeline isn't urgent - we want to take time to make the right choice. Quality over speed.",
        "Do contractors typically provide detailed written estimates? We like everything documented.",
        "This is a big decision for us. Can we take some time to think it over?",
        "You've been very patient with all our questions. What information do you need to get started?"
    ]
    
    await tester.natural_conversation("Cautious-Retiree", cautious_retiree_flow)
    print("\n\nALL PERSONA TESTING COMPLETE!")

if __name__ == "__main__":
    asyncio.run(main())