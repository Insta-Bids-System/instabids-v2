#!/usr/bin/env python3
"""
Simple test to check CIA integration
"""

import asyncio
import sys
import os

# Add the ai-agents directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

async def test_simple():
    print("=== SIMPLE CIA INTEGRATION TEST ===")
    
    try:
        from agents.cia.potential_bid_card_integration import PotentialBidCardManager
        
        manager = PotentialBidCardManager()
        print("Bid card manager created")
        
        # Test direct API call
        bid_card_id = await manager.create_potential_bid_card(
            conversation_id="simple-test-123",
            session_id="simple-session-123"
        )
        
        if bid_card_id:
            print(f"SUCCESS: Bid card created with ID: {bid_card_id}")
            
            # Test updating
            success = await manager.update_field(
                bid_card_id=bid_card_id,
                field_name="project_type",
                field_value="kitchen renovation"
            )
            
            if success:
                print("SUCCESS: Field updated")
                
                # Get status
                status = await manager.get_bid_card_status(bid_card_id)
                if status:
                    print(f"Completion: {status.get('completion_percentage', 0)}%")
                
        else:
            print("FAILED: No bid card created")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple())