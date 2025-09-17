#!/usr/bin/env python3
"""
Bid Card Utilities
Helper functions for bid card creation and management
"""

import time
from typing import Any

import database_simple


def generate_bid_card_number(prefix: str = "CLAUDE") -> str:
    """
    Generate a unique bid card number following the pattern BC-[PREFIX]-[TIMESTAMP]
    
    Args:
        prefix: Project prefix (default: "CLAUDE" for Claude-created cards)
    
    Returns:
        str: Unique bid card number like "BC-CLAUDE-1754347994"
    """
    timestamp = int(time.time() * 1000)  # Use milliseconds for better uniqueness
    return f"BC-{prefix.upper()}-{timestamp}"


def create_bid_card_with_defaults(project_data: dict[str, Any]) -> dict[str, Any]:
    """
    Create a bid card with all required fields and intelligent defaults
    
    Args:
        project_data: Basic project information
        
    Returns:
        Dict containing the created bid card data
    """
    # Generate required bid card number
    bid_card_number = generate_bid_card_number()

    # Set up bid card with required fields and intelligent defaults
    # Valid urgency levels: week, emergency, month, flexible
    bid_card_data = {
        "bid_card_number": bid_card_number,
        "project_type": project_data.get("project_type", "general_renovation"),
        "title": project_data.get("title", "New Project"),
        "description": project_data.get("description", ""),
        "urgency_level": project_data.get("urgency_level", "week"),  # Fixed: use valid urgency level
        "status": "generated",
        "contractor_count_needed": project_data.get("contractor_count_needed", 3),
        "complexity_score": project_data.get("complexity_score", 3),
        "budget_min": project_data.get("budget_min"),
        "budget_max": project_data.get("budget_max"),
        "timeline_start": project_data.get("timeline_start"),
        "timeline_end": project_data.get("timeline_end"),  # Fixed: use timeline_end not timeline_duration
        "timeline_flexibility": project_data.get("timeline_flexibility"),
        "location_city": project_data.get("location_city"),
        "location_state": project_data.get("location_state"),
        "location_zip": project_data.get("location_zip"),
        "location_address": project_data.get("location_address"),
        "requirements": project_data.get("requirements") if isinstance(project_data.get("requirements"), list)
                       else [project_data.get("requirements")] if project_data.get("requirements")
                       else None,  # Fixed: requirements must be array
        "cia_thread_id": project_data.get("cia_thread_id")
    }

    # Remove None values to let database defaults take effect
    bid_card_data = {k: v for k, v in bid_card_data.items() if v is not None}

    try:
        db = database_simple.get_client()
        result = db.table("bid_cards").insert(bid_card_data).execute()

        if result.data:
            # Track the bid card creation event
            try:
                from routers.bid_card_event_tracker import EventTracker
                import asyncio
                
                bid_card_id = result.data[0]["id"]
                asyncio.create_task(EventTracker.track_event(
                    bid_card_id=bid_card_id,
                    event_type="bid_card_created",
                    description=f"Bid card {bid_card_number} created",
                    details={
                        "project_type": project_data.get("project_type"),
                        "urgency_level": project_data.get("urgency_level", "standard"),
                        "contractor_count_needed": project_data.get("contractor_count_needed", 4),
                        "user_id": project_data.get("user_id"),
                        "status": "generated"
                    },
                    created_by=project_data.get("user_id"),
                    created_by_type="homeowner" if project_data.get("user_id") else "system"
                ))
            except Exception as e:
                print(f"Warning: Could not track bid card creation event: {e}")
            
            return {
                "success": True,
                "bid_card": result.data[0],
                "bid_card_number": bid_card_number,
                "message": "Bid card created successfully"
            }
        else:
            return {
                "success": False,
                "error": "Failed to create bid card - no data returned"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Database error: {e!s}",
            "bid_card_data": bid_card_data  # For debugging
        }


def test_bid_card_creation():
    """
    Test bid card creation with various scenarios
    """
    print("Testing bid card creation utility...")

    # Test 1: Minimal data
    print("\n1. Testing minimal bid card creation:")
    result1 = create_bid_card_with_defaults({
        "project_type": "kitchen_remodel",
        "title": "Test Kitchen Renovation",
        "description": "Simple kitchen update for testing"
    })
    print(f"Result: {result1['success']}")
    if result1["success"]:
        print(f"Created bid card: {result1['bid_card_number']}")
    else:
        print(f"Error: {result1['error']}")

    # Test 2: Full data
    print("\n2. Testing complete bid card creation:")
    result2 = create_bid_card_with_defaults({
        "project_type": "bathroom_remodel",
        "title": "Master Bathroom Renovation",
        "description": "Complete bathroom overhaul including shower, vanity, and flooring",
        "urgency_level": "emergency",  # Fixed: use valid urgency level
        "contractor_count_needed": 4,
        "complexity_score": 5,
        "budget_min": 15000,
        "budget_max": 25000,
        "requirements": ["Demolition", "plumbing", "electrical", "tiling", "fixtures"],
        "location_city": "Seattle",
        "location_state": "WA",
        "location_zip": "98101"
    })
    print(f"Result: {result2['success']}")
    if result2["success"]:
        print(f"Created bid card: {result2['bid_card_number']}")
        print(f"ID: {result2['bid_card']['id']}")
    else:
        print(f"Error: {result2['error']}")

    # Test 3: Edge case - empty data
    print("\n3. Testing edge case with minimal data:")
    result3 = create_bid_card_with_defaults({})
    print(f"Result: {result3['success']}")
    if result3["success"]:
        print(f"Created bid card: {result3['bid_card_number']}")
    else:
        print(f"Error: {result3['error']}")

    return [result1, result2, result3]


if __name__ == "__main__":
    test_bid_card_creation()
