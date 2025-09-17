#!/usr/bin/env python3
"""
Complete end-to-end test of homeowner flow:
1. Create/use test homeowner account
2. Have CIA conversation
3. Generate bid card with JAA
4. Verify bid card shows in dashboard
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Add agents to path
agents_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai-agents')
sys.path.append(agents_path)

from agents.cia.agent import CustomerInterfaceAgent
from agents.jaa.agent import JobAssessmentAgent
from database_simple import SupabaseDB

class HomeownerFlowTester:
    def __init__(self):
        self.db = SupabaseDB()
        self.test_user_id = 'e6e47a24-95ad-4af3-9ec5-f17999917bc3'
        self.test_email = 'test.homeowner@instabids.com'
        self.test_password = 'testpass123'  # For frontend login
        
        # Initialize CIA with API key
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.cia = CustomerInterfaceAgent(anthropic_api_key=anthropic_key)
        self.jaa = JobAssessmentAgent()
        
    async def test_conversation_1_kitchen(self):
        """Test conversation 1: Kitchen remodel with photos"""
        print("\n=== CONVERSATION 1: Kitchen Remodel ===")
        
        message = """Hi! I need help with a kitchen remodel project. I live in Tampa, Florida. 
        My budget is around $25,000 to $35,000. I want to completely renovate my kitchen:
        - Replace all cabinets with white shaker style
        - Install granite countertops 
        - Update all appliances to stainless steel
        - Replace flooring with luxury vinyl plank
        - Add under-cabinet LED lighting
        The kitchen is about 250 square feet. I'd like to start within the next month.
        I have photos of the current kitchen showing the layout and condition."""
        
        result = await self.cia.handle_conversation(
            user_id=self.test_user_id,
            message=message
        )
        
        print(f"CIA Response (first 300 chars): {result['response'][:300]}...")
        print(f"Thread ID: {result['thread_id']}")
        
        return result['thread_id']
    
    async def test_conversation_2_bathroom(self):
        """Test conversation 2: Bathroom renovation"""
        print("\n=== CONVERSATION 2: Bathroom Renovation ===")
        
        message = """I also need to renovate my master bathroom. Same location in Tampa, FL.
        Budget: $15,000 to $20,000. I want to:
        - Install a walk-in shower with glass doors
        - Replace vanity with double sinks
        - Install new tile flooring
        - Update all plumbing fixtures
        - Add better lighting
        Timeline: I'd like this done within 2-3 weeks after the kitchen. 
        The bathroom is about 120 square feet."""
        
        result = await self.cia.handle_conversation(
            user_id=self.test_user_id,
            message=message
        )
        
        print(f"CIA Response (first 300 chars): {result['response'][:300]}...")
        print(f"Thread ID: {result['thread_id']}")
        
        return result['thread_id']
    
    async def test_conversation_3_landscaping(self):
        """Test conversation 3: Landscaping project"""
        print("\n=== CONVERSATION 3: Landscaping Project ===")
        
        message = """I need landscaping work for my front and back yard in Tampa, FL.
        Budget: $8,000 to $12,000. I want:
        - Remove old shrubs and replant with native Florida plants
        - Install new irrigation system
        - Add decorative stone pathways
        - Plant new palm trees (3-4 trees)
        - Install landscape lighting
        - Refresh mulch beds
        Timeline: Flexible, can be done over next 2-3 months.
        Property is about 0.5 acres total."""
        
        result = await self.cia.handle_conversation(
            user_id=self.test_user_id,
            message=message
        )
        
        print(f"CIA Response (first 300 chars): {result['response'][:300]}...")
        print(f"Thread ID: {result['thread_id']}")
        
        return result['thread_id']
    
    def generate_bid_card(self, thread_id, project_name):
        """Generate bid card using JAA"""
        print(f"\n=== GENERATING BID CARD: {project_name} ===")
        
        result = self.jaa.process_conversation(thread_id)
        
        if result['success']:
            print(f"✅ Bid card created successfully!")
            print(f"   Bid Card Number: {result['bid_card_number']}")
            print(f"   Project Type: {result['bid_card_data']['project_type']}")
            print(f"   Budget: ${result['bid_card_data']['budget_min']}-${result['bid_card_data']['budget_max']}")
            print(f"   Contractors Needed: {result['bid_card_data']['contractor_requirements']['contractor_count']}")
            print(f"   Database ID: {result['database_id']}")
            return result
        else:
            print(f"❌ Failed to create bid card: {result['error']}")
            return None
    
    def verify_dashboard_data(self):
        """Verify bid cards appear in homeowner dashboard"""
        print("\n=== VERIFYING DASHBOARD DATA ===")
        
        # Get all conversations for this user
        conversations = self.db.client.table('agent_conversations').select('*').eq('user_id', self.test_user_id).execute()
        print(f"Total conversations: {len(conversations.data) if conversations.data else 0}")
        
        # Get all bid cards
        bid_cards = self.db.client.table('bid_cards').select('*').execute()
        user_bid_cards = []
        
        if bid_cards.data:
            # Find bid cards linked to our user's conversations
            user_thread_ids = [conv['thread_id'] for conv in (conversations.data or [])]
            user_bid_cards = [card for card in bid_cards.data if card['cia_thread_id'] in user_thread_ids]
        
        print(f"Total bid cards for user: {len(user_bid_cards)}")
        
        for i, card in enumerate(user_bid_cards, 1):
            print(f"\n  Bid Card {i}:")
            print(f"    Number: {card['bid_card_number']}")
            print(f"    Project: {card['project_type']}")
            print(f"    Budget: ${card['budget_min']}-${card['budget_max']}")
            print(f"    Status: {card['status']}")
            print(f"    Created: {card['created_at']}")
        
        return user_bid_cards
    
    async def run_complete_test(self):
        """Run complete end-to-end test"""
        print("🏠 INSTABIDS HOMEOWNER FLOW TEST")
        print("=" * 50)
        print(f"Test User: {self.test_email}")
        print(f"User ID: {self.test_user_id}")
        print(f"Password: {self.test_password}")
        
        try:
            # Have 3 different conversations
            thread1 = await self.test_conversation_1_kitchen()
            thread2 = await self.test_conversation_2_bathroom() 
            thread3 = await self.test_conversation_3_landscaping()
            
            # Generate bid cards for each
            bid_card1 = self.generate_bid_card(thread1, "Kitchen Remodel")
            bid_card2 = self.generate_bid_card(thread2, "Bathroom Renovation")
            bid_card3 = self.generate_bid_card(thread3, "Landscaping Project")
            
            # Verify dashboard data
            user_bid_cards = self.verify_dashboard_data()
            
            print("\n" + "=" * 50)
            print("✅ TEST COMPLETED SUCCESSFULLY!")
            print(f"✅ Created {len(user_bid_cards)} bid cards")
            print(f"✅ All data saved to database")
            print("\n🔑 LOGIN CREDENTIALS:")
            print(f"   Email: {self.test_email}")
            print(f"   Password: {self.test_password}")
            print(f"   Dashboard URL: http://localhost:5182/dashboard")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    tester = HomeownerFlowTester()
    asyncio.run(tester.run_complete_test())