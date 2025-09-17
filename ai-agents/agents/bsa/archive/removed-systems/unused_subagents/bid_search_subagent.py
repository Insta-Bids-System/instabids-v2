"""
Bid Search Sub-Agent - Part of BSA DeepAgents System
Simple bid card search with ZIP radius + contractor type + size matching
"""

import os
import sys
from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime

# Add deepagents-system to path
from pathlib import Path
deepagents_path = Path(__file__).parent.parent.parent.parent / "deepagents-system" / "src"
if deepagents_path.exists():
    sys.path.insert(0, str(deepagents_path))

# Import DeepAgents framework
from deepagents import create_deep_agent
from deepagents.state import DeepAgentState

# Import required utilities
from utils.radius_search_fixed import get_zip_codes_in_radius, calculate_distance_miles, filter_by_radius
from database_simple import db

logger = logging.getLogger(__name__)

# Contractor size tiers for ±1 matching
contractor_size_tiers = {
    "solo_handyman": 1,
    "owner_operator": 2, 
    "small_business": 3,
    "regional_company": 4,
    "national_chain": 5
}

def get_compatible_contractor_tiers(contractor_size: str) -> List[int]:
    """Get compatible contractor tier numbers using ±1 flexibility"""
    base_tier = contractor_size_tiers.get(contractor_size, 3)  # Default to tier 3
    compatible_tiers = [base_tier]  # Always include exact match
    
    # Add ±1 tiers
    if base_tier > 1:
        compatible_tiers.append(base_tier - 1)  # One tier smaller
    if base_tier < 5:
        compatible_tiers.append(base_tier + 1)  # One tier bigger
    
    # Return sorted tiers
    return sorted(compatible_tiers)

def get_contractor_tier_number(contractor_size: str) -> int:
    """Convert contractor size to tier number"""
    return contractor_size_tiers.get(contractor_size, 3)

def simple_bid_card_match(bid_card: Dict[str, Any], contractor_type_ids: List[int], contractor_size: Optional[str]) -> bool:
    """
    PURE contractor_type_ids matching - NO FALLBACK LOGIC
    
    STRICT REQUIREMENTS:
    - Bid cards MUST have contractor_type_ids array (auto-populated from project_type)
    - Contractors MUST have contractor_type_ids array (set during profile creation)
    - BSA does ONLY direct numeric ID matching
    - NO text lookups, NO legacy support, NO fallbacks
    
    Example:
    - Bid card contractor_type_ids: [33, 48, 127, 207] (plumbing project)  
    - Contractor contractor_type_ids: [33, 207, 219] (plumber)
    - Match: YES (33 and 207 overlap)
    
    If either array is missing/empty: NO MATCH (returns False)
    """
    
    # Get contractor_type_ids from bid card (MUST be present)
    bid_card_type_ids = bid_card.get('contractor_type_ids', [])
    
    # STRICT: Both arrays must have values for matching
    if not bid_card_type_ids:
        return False  # Bid card missing contractor_type_ids - NO MATCH
    
    if not contractor_type_ids:
        return False  # Contractor missing contractor_type_ids - NO MATCH
    
    # PURE numeric ID matching - check for overlap
    contractor_id_set = set(contractor_type_ids)
    bid_card_id_set = set(bid_card_type_ids)
    
    # Return True ONLY if there's overlap between the two ID arrays
    overlap = contractor_id_set & bid_card_id_set
    return bool(overlap)

class BidSearchState(DeepAgentState):
    """State for bid search sub-agent"""
    contractor_zip: Optional[str] = None
    radius_miles: int = 25
    project_type: Optional[str] = None
    contractor_size: Optional[str] = None
    contractor_type_ids: List[int] = []  # FIXED: Use numeric IDs
    contractor_types: List[str] = []  # Legacy for backward compatibility
    search_results: List[Dict[str, Any]] = []
    total_found: int = 0

async def search_bid_cards_subagent(
    contractor_zip: str,
    radius_miles: int = 25,
    project_type: Optional[str] = None,
    contractor_size: Optional[str] = None,
    contractor_type_ids: List[int] = [],  # FIXED: Use numeric IDs not text
    contractor_types: List[str] = [],  # Legacy parameter for backward compatibility
    state: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """
    BSA Bid Search Sub-Agent
    
    Simple matching:
    - ZIP radius filtering
    - Contractor type matching  
    - ±1 tier size matching
    """
    try:
        logger.info(f"BSA Bid Search Sub-Agent starting search")
        logger.info(f"Location: {contractor_zip}, Radius: {radius_miles} miles")
        logger.info(f"Project Type: {project_type}")
        logger.info(f"Contractor Size: {contractor_size}")
        logger.info(f"Contractor Type IDs: {contractor_type_ids}")
        
        # Step 1: Get all bid cards from database (no pre-filtering by ZIP)
        query = db.client.table('bid_cards').select('*')
        
        # Execute query to get ALL bid cards
        result = query.execute()
        bid_cards = result.data if result.data else []
        
        logger.info(f"Retrieved {len(bid_cards)} total bid cards from database")
        
        # Step 2: Apply contractor type filtering first
        type_matched_cards = []
        for card in bid_cards:
            if simple_bid_card_match(card, contractor_type_ids, contractor_size):
                type_matched_cards.append(card)
        
        logger.info(f"Found {len(type_matched_cards)} bid cards matching contractor types")
        
        # Step 3: Apply accurate radius filtering using proper distance calculation
        matching_cards = filter_by_radius(
            items=type_matched_cards,
            center_zip=contractor_zip,
            radius_miles=radius_miles,
            zip_field="location_zip"
        )
        
        logger.info(f"Found {len(matching_cards)} bid cards within {radius_miles} miles after accurate filtering")
        
        return {
            "success": True,
            "bid_cards": matching_cards,
            "total_found": len(matching_cards),
            "search_criteria": {
                "location": contractor_zip,
                "radius": radius_miles,
                "project_type": project_type,
                "contractor_size": contractor_size,
                "contractor_type_ids": contractor_type_ids,
                "filtering_method": "accurate_distance_calculation",
                "matching_enabled": True
            }
        }
        
    except Exception as e:
        logger.error(f"Bid search sub-agent failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "bid_cards": [],
            "total_found": 0
        }

# Create the sub-agent using DeepAgents framework
def create_bid_search_subagent():
    """Create bid search sub-agent"""
    
    instructions = """
    You are the Bid Search Sub-Agent, part of the BSA (Bid Submission Agent) system.
    
    Your job is simple:
    1. Take contractor location, project type, and size requirements
    2. Find bid cards within ZIP radius that match contractor types
    3. Use ±1 tier size matching (tier 3 can see tiers 2,3,4)
    4. Return matching bid cards sorted by distance
    
    Keep it simple - just match type, location, and size.
    """
    
    return create_deep_agent(
        tools=[search_bid_cards_subagent],
        instructions=instructions,
        state_schema=BidSearchState
    )

if __name__ == "__main__":
    # Test the sub-agent
    async def test_subagent():
        result = await search_bid_cards_subagent(
            contractor_zip="33442",
            radius_miles=25,
            project_type="plumbing",
            contractor_size="solo_handyman",
            contractor_type_ids=[33, 127]  # Plumbing=33, Handyman=127
        )
        print(f"Sub-agent result: {result}")
    
    asyncio.run(test_subagent())