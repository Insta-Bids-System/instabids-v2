#!/usr/bin/env python3
"""Test RFI photo update using MCP Supabase tools directly"""

import json
from datetime import datetime

def test_rfi_photo_update_mcp():
    """Test adding RFI photos to bid card via MCP Supabase"""
    
    bid_card_id = "36214de5-a068-4dcc-af99-cf33238e7472"
    
    print("=" * 80)
    print("TESTING RFI PHOTO UPDATE VIA MCP SUPABASE")
    print("=" * 80)
    
    # Get current bid card from previous query - it has a kitchen remodel with bids
    print("Current bid card: Kitchen remodel project (contractor_selected status)")
    print("Project has: Cabinet replacement, quartz countertops, stainless appliances")
    
    # Create RFI photo data to add
    rfi_photos = [
        {
            "photo_id": "rfi_kitchen_001",
            "filename": "current_kitchen_overview.jpg",
            "uploaded_at": datetime.utcnow().isoformat(),
            "contractor_request": "Selected contractor requested current kitchen photos",
            "description": "Current kitchen layout before renovation",
            "source": "rfi_response",
            "type": "before_photos"
        },
        {
            "photo_id": "rfi_kitchen_002", 
            "filename": "cabinet_condition.jpg",
            "uploaded_at": datetime.utcnow().isoformat(),
            "contractor_request": "Selected contractor needs cabinet condition assessment",
            "description": "Current cabinet condition and hardware",
            "source": "rfi_response",
            "type": "detail_photos"
        },
        {
            "photo_id": "rfi_kitchen_003",
            "filename": "electrical_outlets.jpg",
            "uploaded_at": datetime.utcnow().isoformat(),
            "contractor_request": "Selected contractor needs electrical outlet locations",
            "description": "Current electrical outlet positions for appliance planning",
            "source": "rfi_response",
            "type": "electrical_reference"
        }
    ]
    
    # Get current bid document (from previous query)
    current_document = {
        "ai_analysis": {
            "location": {"city": None, "state": None, "address": None, "zip_code": None, "property_type": None},
            "budget_max": 50000,
            "budget_min": 35000
        },
        "generated_at": "2025-08-01T03:06:43.097471",
        "submitted_bids": [
            {"id": "c517a67a-fda5-4206-a61b-3b5ee394ea2d", "status": "accepted", "bid_amount": 28000},
            {"id": "3709b30f-99cf-44c4-9795-dd4df81acfed", "status": "rejected", "bid_amount": 31000},
            {"id": "be25334d-230a-4aa7-84f2-ee4e41d45b88", "status": "rejected", "bid_amount": 26500}
        ],
        "bid_card_number": "IBC-20250801030643",
        "bids_target_met": True,
        "bids_received_count": 3
    }
    
    # Add RFI photos to the document
    current_document["rfi_photos"] = rfi_photos
    current_document["rfi_photos_count"] = len(rfi_photos)
    current_document["last_rfi_update"] = datetime.utcnow().isoformat()
    current_document["rfi_context"] = {
        "request_source": "selected_contractor",
        "contractor_name": "Test Kitchen Contractor 1",
        "request_type": "additional_photos",
        "photos_provided": len(rfi_photos)
    }
    
    # Update via MCP
    print("\n1. UPDATING BID CARD WITH RFI PHOTOS VIA MCP:")
    print(f"Adding {len(rfi_photos)} RFI photos...")
    
    # Show what we're adding
    for i, photo in enumerate(rfi_photos, 1):
        print(f"   Photo {i}: {photo['filename']} - {photo['description']}")
    
    update_payload = {
        "bid_document": current_document,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    print(f"\n2. PAYLOAD SIZE: {len(json.dumps(update_payload))} characters")
    print("3. UPDATE WILL BE EXECUTED VIA MCP TOOL")
    
    return {
        "bid_card_id": bid_card_id,
        "rfi_photos": rfi_photos,
        "update_payload": update_payload
    }

if __name__ == "__main__":
    result = test_rfi_photo_update_mcp()
    
    print("\n" + "=" * 80)
    print("✅ RFI PHOTO TEST DATA PREPARED")
    print(f"Bid Card: {result['bid_card_id']}")
    print(f"Photos: {len(result['rfi_photos'])} RFI photos ready")
    print("Ready for MCP Supabase update...")
    print("=" * 80)