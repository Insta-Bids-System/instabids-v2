"""
FAST Mode Detector - No LLM calls needed
=========================================

This replaces the GPT-4o mode detection with instant regex matching.
Saves 2-3 seconds per request.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def fast_detect_mode(message: str, current_mode: str = None) -> str:
    """
    Instant mode detection without any LLM calls.
    
    Returns the mode in 0.001 seconds instead of 2-3 seconds.
    """
    message_lower = message.lower()
    
    # BID CARD SEARCH - High priority triggers
    bid_triggers = [
        "find project",
        "show project",
        "show me project",
        "show me available",
        "available project",
        "opportunities",
        "bid on",
        "what can i bid",
        "projects in my area",
        "projects near",
        "looking for project",
        "need project",
        "want to bid",
        "show me bid",
        "available bid",
        "projects i can bid"
    ]
    
    if any(trigger in message_lower for trigger in bid_triggers):
        logger.info(f"🎯 FAST: Triggered bid_card_search mode")
        return "bid_card_search"
    
    # RESEARCH - Business research triggers  
    research_triggers = [
        "research my",
        "find information",
        "look up my",
        "search for my",
        "gather data",
        "more about my business"
    ]
    
    if any(trigger in message_lower for trigger in research_triggers):
        logger.info(f"🔍 FAST: Triggered research mode")
        return "research"
    
    # ACCOUNT CREATION - Signup triggers
    account_triggers = [
        "create account",
        "sign up",
        "signup",
        "register",
        "join platform",
        "get started"
    ]
    
    if any(trigger in message_lower for trigger in account_triggers):
        logger.info(f"👤 FAST: Triggered account_creation mode")
        return "account_creation"
    
    # BID SUBMISSION - Bidding triggers
    bid_submit_triggers = [
        "submit bid",
        "place bid",
        "send proposal",
        "make an offer"
    ]
    
    if any(trigger in message_lower for trigger in bid_submit_triggers):
        logger.info(f"💰 FAST: Triggered bid_submission mode")
        return "bid_submission"
    
    # Default to conversation
    logger.info(f"💬 FAST: Defaulting to conversation mode")
    return "conversation"


def fast_extract_location(message: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fast location extraction without LLM.
    
    Extracts city, state, and radius from message.
    """
    import re
    
    location = {}
    message_lower = message.lower()
    
    # Check for Miami and other Florida cities
    florida_cities = {
        "miami": "Miami",
        "fort lauderdale": "Fort Lauderdale",
        "west palm beach": "West Palm Beach",
        "coral springs": "Coral Springs",
        "delray beach": "Delray Beach",
        "boca raton": "Boca Raton",
        "hollywood": "Hollywood",
        "pompano beach": "Pompano Beach"
    }
    
    for city_lower, city_proper in florida_cities.items():
        if city_lower in message_lower:
            location["city"] = city_proper
            location["state"] = "FL"
            break
    
    # Extract radius (e.g., "30 miles", "50 mile radius")
    radius_match = re.search(r'(\d+)\s*mile', message_lower)
    if radius_match:
        location["radius_miles"] = int(radius_match.group(1))
    elif not location.get("radius_miles"):
        location["radius_miles"] = 30  # Default 30 miles
    
    # Fall back to profile data
    if not location.get("city") and profile.get("city"):
        location["city"] = profile["city"]
    if not location.get("state") and profile.get("state"):
        location["state"] = profile["state"]
    
    return location


def fast_extract_project_types(message: str, profile: Dict[str, Any]) -> list:
    """
    Fast project type extraction without LLM.
    
    Returns list of matching project types.
    """
    message_lower = message.lower()
    project_types = []
    
    # Map keywords to project types in database
    keyword_map = {
        "holiday lighting": ["holiday lighting"],
        "christmas lights": ["holiday lighting"],
        "electrical": ["electrical"],
        "turf": ["turf", "artificial grass", "landscaping"],
        "artificial grass": ["turf", "artificial grass"],
        "landscaping": ["landscaping", "lawn care"],
        "bathroom": ["bathroom_remodel", "bathroom renovation"],
        "kitchen": ["kitchen_remodel", "kitchen renovation"],
        "deck": ["deck construction", "deck installation"],
        "hvac": ["hvac", "HVAC Installation"],
        "plumbing": ["plumbing"],
        "roofing": ["roofing", "roof repair"],
        "painting": ["painting", "interior painting", "exterior painting"],
        "flooring": ["flooring", "carpet", "hardwood"]
    }
    
    for keyword, types in keyword_map.items():
        if keyword in message_lower:
            project_types.extend(types)
    
    # Remove duplicates
    project_types = list(set(project_types))
    
    # Fall back to profile specialties
    if not project_types and profile.get("specialties"):
        project_types = profile["specialties"]
    
    return project_types


# Export for use in main COIA flow
__all__ = [
    'fast_detect_mode',
    'fast_extract_location', 
    'fast_extract_project_types'
]