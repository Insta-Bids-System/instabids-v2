#!/usr/bin/env python3
"""
Comprehensive multi-turn CIA conversation test
Tests 8-15 conversation turns to verify contextual bid card creation and updates
"""
import requests
import json
import uuid
import sys
import io
import time
from typing import List, Dict

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8008"

class CIAMultiTurnTester:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.user_id = "00000000-0000-0000-0000-000000000000"
        self.conversation_history = []
        self.bid_card_id = None
        
    def send_message_and_consume_stream(self, message: str) -> str:
        """Send message to CIA and consume full stream response"""
        print(f"\n🔄 [Turn {len(self.conversation_history) + 1}] USER: {message}")
        
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": message})
        
        request_data = {
            "messages": self.conversation_history,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "conversation_id": self.session_id
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/cia/stream",
                json=request_data,
                timeout=60,
                stream=True
            )
            
            if response.status_code == 200:
                # Consume entire stream until [DONE]
                content_chunks = []
                chunk_count = 0
                
                for line in response.iter_lines():
                    if line:
                        chunk_count += 1
                        line_str = line.decode()
                        
                        if line_str.startswith("data: "):
                            data_part = line_str[6:]
                            if data_part == "[DONE]":
                                break
                            elif data_part.strip():
                                try:
                                    chunk_data = json.loads(data_part)
                                    if "choices" in chunk_data:
                                        content = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                        if content:
                                            content_chunks.append(content)
                                except:
                                    pass
                
                assistant_response = "".join(content_chunks)
                print(f"🤖 ASSISTANT: {assistant_response}")
                
                # Add assistant response to history
                self.conversation_history.append({"role": "assistant", "content": assistant_response})
                
                return assistant_response
                
            else:
                print(f"❌ Request failed: {response.status_code}")
                return ""
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return ""
    
    def check_bid_card_status(self) -> Dict:
        """Check current bid card status and fields"""
        try:
            # Get bid card by conversation ID
            response = requests.get(
                f"{BASE_URL}/api/cia/conversation/{self.session_id}/potential-bid-card"
            )
            
            if response.status_code == 200:
                data = response.json()
                self.bid_card_id = data.get("id")
                return data
            else:
                return {}
                
        except Exception as e:
            print(f"❌ Error checking bid card: {e}")
            return {}
    
    def print_bid_card_summary(self, bid_card_data: Dict):
        """Print formatted bid card status"""
        if not bid_card_data:
            print("❌ No bid card found")
            return
            
        print(f"\n📋 BID CARD STATUS:")
        print(f"   ID: {bid_card_data.get('id', 'N/A')}")
        print(f"   Completion: {bid_card_data.get('completion_percentage', 0)}%")
        print(f"   Status: {bid_card_data.get('status', 'unknown')}")
        
        fields = bid_card_data.get('fields_collected', {})
        missing = bid_card_data.get('missing_fields', [])
        
        print(f"   Fields Collected ({len(fields)}):")
        for field, value in fields.items():
            if value not in [None, "", [], {}]:
                print(f"     ✅ {field}: {value}")
        
        if missing:
            print(f"   Missing Fields ({len(missing)}): {', '.join(missing)}")
        
        print(f"   Ready for Conversion: {bid_card_data.get('ready_for_conversion', False)}")

def run_comprehensive_conversation_test():
    """Run comprehensive multi-turn conversation test"""
    print("=" * 80)
    print("🧪 CIA MULTI-TURN CONVERSATION TEST")
    print("=" * 80)
    print("Testing 8-15 conversation turns with contextual bid card updates")
    
    tester = CIAMultiTurnTester()
    print(f"Session ID: {tester.session_id}")
    
    # Conversation scenario: Kitchen remodel project
    conversation_turns = [
        # Turn 1: Initial project introduction
        "I'm thinking about remodeling my kitchen",
        
        # Turn 2: Project scope expansion
        "It's a complete gut renovation - cabinets, countertops, flooring, everything. The current kitchen is from the 1980s and really needs updating.",
        
        # Turn 3: Location and property details
        "I'm in Manhattan, zip code 10001. It's a 2-bedroom condo, about 1200 square feet total with the kitchen being maybe 150 square feet.",
        
        # Turn 4: Budget discussion
        "I'm hoping to keep the budget around $40,000 to $60,000 if possible. Is that realistic for a full renovation?",
        
        # Turn 5: Timeline and urgency
        "I'd like to get this done by spring, so maybe 3-4 months from now. It's not super urgent but I want to start planning soon.",
        
        # Turn 6: Material preferences
        "I love the modern farmhouse style - white shaker cabinets, quartz countertops, maybe subway tile backsplash. And I definitely want stainless steel appliances.",
        
        # Turn 7: Special requirements
        "One important thing - I work from home a lot, so I need to make sure there's minimal disruption. Maybe we can do it in phases?",
        
        # Turn 8: Contractor preferences
        "I'd prefer contractors who have experience with condo renovations and can work around my schedule. Licenses and insurance are definitely important.",
        
        # Turn 9: Additional considerations
        "Oh, and I should mention - the building has strict noise restrictions. Work can only happen between 9 AM and 5 PM on weekdays.",
        
        # Turn 10: Final details
        "I think that covers most of it. When can we start getting some quotes from contractors?",
        
        # Turn 11: Follow-up question
        "Actually, one more thing - do you think I should also consider updating the electrical? The current setup might be old.",
        
        # Turn 12: Refinement
        "And what about permits? Will the contractors handle that or do I need to get them myself?",
        
        # Turn 13: Group bidding interest
        "I heard about group bidding - is that something that would work for a kitchen remodel?",
        
        # Turn 14: Timeline flexibility
        "If group bidding could save money, I'd be willing to wait a bit longer. Maybe push the timeline to 4-5 months.",
        
        # Turn 15: Final confirmation
        "Alright, I think I'm ready to see what contractors are available. This sounds like a great approach!"
    ]
    
    # Execute conversation turns
    for i, message in enumerate(conversation_turns, 1):
        print(f"\n{'='*20} TURN {i} {'='*20}")
        
        # Send message and get response
        response = tester.send_message_and_consume_stream(message)
        
        # Wait for state management to complete
        time.sleep(2)
        
        # Check bid card status after this turn
        bid_card_data = tester.check_bid_card_status()
        tester.print_bid_card_summary(bid_card_data)
        
        # Progress check
        completion = bid_card_data.get('completion_percentage', 0)
        fields_count = len(bid_card_data.get('fields_collected', {}))
        
        print(f"\n📊 PROGRESS: {completion}% complete, {fields_count} fields collected")
        
        # Brief pause between turns
        time.sleep(1)
    
    # Final comprehensive analysis
    print(f"\n{'='*80}")
    print("🎯 FINAL ANALYSIS")
    print(f"{'='*80}")
    
    final_bid_card = tester.check_bid_card_status()
    if final_bid_card:
        print("✅ CONVERSATION COMPLETED SUCCESSFULLY")
        tester.print_bid_card_summary(final_bid_card)
        
        # Detailed field analysis
        fields = final_bid_card.get('fields_collected', {})
        print(f"\n📋 DETAILED FIELD ANALYSIS:")
        
        expected_fields = [
            'project_type', 'project_description', 'zip_code', 'budget_range',
            'timeline', 'urgency', 'materials', 'special_requirements',
            'contractor_preferences', 'timeline_flexibility'
        ]
        
        for field in expected_fields:
            value = fields.get(field)
            status = "✅" if value not in [None, "", [], {}] else "❌"
            print(f"   {status} {field}: {value}")
        
        # Success metrics
        completion = final_bid_card.get('completion_percentage', 0)
        ready = final_bid_card.get('ready_for_conversion', False)
        
        print(f"\n🎯 SUCCESS METRICS:")
        print(f"   Final Completion: {completion}%")
        print(f"   Ready for Conversion: {ready}")
        print(f"   Fields Collected: {len(fields)}")
        print(f"   Conversation Turns: {len(conversation_turns)}")
        
        if completion >= 70 and len(fields) >= 6:
            print(f"\n🎉 TEST PASSED: High-quality bid card created through multi-turn conversation!")
            return True
        else:
            print(f"\n⚠️  TEST PARTIAL: Bid card created but needs more information")
            return False
    else:
        print("❌ TEST FAILED: No bid card created during conversation")
        return False

def main():
    print("🚀 Starting comprehensive CIA multi-turn conversation test")
    print("This will test 15 conversation turns with contextual bid card building")
    
    success = run_comprehensive_conversation_test()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 COMPREHENSIVE TEST PASSED!")
        print("✅ CIA agent successfully builds contextual bid cards through multi-turn conversations")
        print("✅ State management working correctly")
        print("✅ Field extraction and updates functioning properly")
    else:
        print("❌ COMPREHENSIVE TEST FAILED!")
        print("⚠️  Check CIA conversation flow and bid card field extraction")

if __name__ == "__main__":
    main()