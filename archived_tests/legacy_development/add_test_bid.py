#!/usr/bin/env python3
"""
Example of how to add a new contractor bid to a bid card
"""

import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from database_simple import DatabaseManager

def add_contractor_bid(bid_card_id: str, contractor_name: str, bid_amount: float):
    """Add a new contractor bid to a bid card"""
    
    db = DatabaseManager()
    
    # Get current bid card
    bid_card = db.supabase.table("bid_cards").select("*").eq("id", bid_card_id).execute()
    
    if not bid_card.data:
        print("Bid card not found!")
        return
    
    current_bid_doc = bid_card.data[0].get("bid_document", {})
    if isinstance(current_bid_doc, str):
        current_bid_doc = json.loads(current_bid_doc)
    
    # Get existing bids or create empty list
    submitted_bids = current_bid_doc.get("submitted_bids", [])
    
    # Create new bid
    new_bid = {
        "id": f"test-bid-{datetime.now().timestamp()}",
        "contractor_name": contractor_name,
        "bid_amount": bid_amount,
        "amount": bid_amount,  # Some places use 'amount' instead
        "submitted_at": datetime.now().isoformat(),
        "status": "submitted",
        "is_valid": True,
        "bid_content": f"Test bid from {contractor_name} for ${bid_amount}",
        "timeline_days": 14,
        "contractor_email": f"{contractor_name.lower().replace(' ', '')}@test.com",
        "submission_method": "test_script"
    }
    
    # Add to list
    submitted_bids.append(new_bid)
    
    # Update bid_document
    current_bid_doc["submitted_bids"] = submitted_bids
    current_bid_doc["bids_received_count"] = len(submitted_bids)
    
    # Save back to database
    result = db.supabase.table("bid_cards").update({
        "bid_document": current_bid_doc
    }).eq("id", bid_card_id).execute()
    
    if result.data:
        print(f"SUCCESS: Added bid from {contractor_name} for ${bid_amount}")
        print(f"Total bids now: {len(submitted_bids)}")
    else:
        print("Failed to update bid card")

if __name__ == "__main__":
    # Example: Add a new bid to the bathroom project
    bathroom_bid_card_id = "0c118f76-1b2d-47a9-9e35-d9b4a6f077da"
    
    print("Adding test bid to bathroom project...")
    add_contractor_bid(
        bid_card_id=bathroom_bid_card_id,
        contractor_name="Test Contractor Co",
        bid_amount=21000
    )
    
    print("\nNow when you talk to CIA, it will see 5 bathroom bids instead of 4!")