#!/usr/bin/env python3
"""
Test CIA agent integration with potential bid cards
Direct test to verify the integration works
"""

import asyncio
import sys
import os

# Add the ai-agents directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

async def test_cia_integration():
    print("=== TESTING CIA AGENT INTEGRATION ===")
    
    try:
        # Import CIA agent
        from agents.cia.agent import CustomerInterfaceAgent
        
        # Get OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("ERROR: No OpenAI API key found")
            return
        
        print(f"[OK] OpenAI API key found: {openai_api_key[:10]}...")
        
        # Initialize CIA agent
        cia_agent = CustomerInterfaceAgent(openai_api_key)
        print("[OK] CIA agent initialized")
        
        # Test potential bid card manager
        if hasattr(cia_agent, 'bid_card_manager'):
            print("[OK] Bid card manager exists")
            
            # Test creating a bid card directly
            try:
                bid_card_id = await cia_agent.bid_card_manager.create_potential_bid_card(
                    conversation_id="test-direct-integration",
                    session_id="test-session-direct",
                    user_id=None
                )
                
                if bid_card_id:
                    print(f"[SUCCESS] Direct bid card creation: {bid_card_id}")
                    
                    # Test updating the bid card
                    test_info = {
                        "project_type": "kitchen renovation",
                        "location": "Seattle, WA",
                        "budget_range": "$40,000 - $60,000",
                        "timeline": "2-3 months"
                    }
                    
                    updated_count = await cia_agent.bid_card_manager.update_from_collected_info(
                        bid_card_id, test_info
                    )
                    
                    print(f"[SUCCESS] Field update: {updated_count} fields updated")
                    
                    # Get bid card status
                    status = await cia_agent.bid_card_manager.get_bid_card_status(bid_card_id)
                    if status:
                        print(f"[SUCCESS] Bid card status: {status.get('completion_percentage', 0)}% complete")
                        print(f"  Fields: {list(status.get('fields_collected', {}).keys())}")
                    
                else:
                    print("[FAILED] Direct bid card creation FAILED")
                    
            except Exception as e:
                print(f"[ERROR] Error in bid card operations: {e}")
                
        else:
            print("[ERROR] No bid card manager found")
            
        # Test a simple conversation to see if integration works
        print("\n--- Testing Conversation Integration ---")
        
        try:
            test_result = await cia_agent.handle_conversation(
                user_id="test-integration-user",
                message="I need help with a kitchen renovation. It's about 200 sq ft and needs new cabinets and countertops.",
                session_id="test-integration-session",
                existing_state=None,
                project_id=None
            )
            
            if test_result and 'potential_bid_card_id' in str(test_result):
                print("[SUCCESS] Conversation integration - bid card created")
            else:
                print("[FAILED] Conversation integration - no bid card created")
                print(f"  Result keys: {list(test_result.keys()) if isinstance(test_result, dict) else 'Not dict'}")
                
        except Exception as e:
            print(f"[ERROR] Error in conversation test: {e}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        print(f"[ERROR] Error initializing CIA agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cia_integration())