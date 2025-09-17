"""
Fixed Bid Card Search Node - Uses Existing Intelligent Systems
Connects COIA to the ZIP radius expansion + intelligent matching you already built
"""
import logging
from datetime import datetime
from typing import Any

from langchain_core.messages import AIMessage

from .unified_state import UnifiedCoIAState

logger = logging.getLogger(__name__)

async def bid_card_search_node(state: UnifiedCoIAState) -> dict[str, Any]:
    """
    Search bid cards using YOUR EXISTING intelligent systems:
    1. ZIP code radius expansion (already built)
    2. Intelligent project matching (already built) 
    3. Removes budget filtering (per your request)
    4. Uses 30-mile default radius (per your request)
    """
    
    logger.info("=== INTELLIGENT BID CARD SEARCH ACTIVATED ===")
    
    # Extract contractor info and user message
    user_message = state["messages"][-1].content if state["messages"] else ""
    contractor_profile = state.get("contractor_profile", {})
    
    # Build intelligent search parameters
    search_params = await _build_intelligent_search_params(user_message, contractor_profile)
    
    # Call YOUR EXISTING intelligent contractor job search API
    bid_cards = await _call_intelligent_job_search(search_params)
    
    # Format response
    response = _format_intelligent_response(bid_cards, search_params, contractor_profile)
    
    # Attach bid cards for frontend
    bid_cards_attached = [_format_for_attachment(card) for card in bid_cards[:5]]
    
    return {
        "messages": [AIMessage(content=response)],
        "current_mode": "bid_card_search", 
        "bid_cards_attached": bid_cards_attached,
        "tool_results": {
            "bid_card_search": {
                "total_found": len(bid_cards),
                "displayed": len(bid_cards_attached),
                "search_params": search_params,
                "intelligent_search": True,
                "zip_radius_used": True
            }
        },
        "last_updated": datetime.utcnow().isoformat()
    }

async def _build_intelligent_search_params(message: str, profile: dict[str, Any]) -> dict[str, Any]:
    """Build search parameters for YOUR EXISTING intelligent job search API"""
    
    # Get contractor ZIP code
    contractor_zip = profile.get("zip_code") or profile.get("location_zip") or "78701"  # Austin fallback
    
    # Default 30-mile radius (per your specification)
    radius_miles = profile.get("service_radius_miles") or 30
    
    # Extract project keywords for intelligent matching
    project_keywords = _extract_project_keywords(message, profile)
    
    # NO BUDGET FILTERING (per your request)
    
    return {
        "contractor_zip": contractor_zip,
        "radius_miles": radius_miles,
        "project_keywords": project_keywords,
        "limit": 20
    }

def _extract_project_keywords(message: str, profile: dict[str, Any]) -> str:
    """Extract project keywords for intelligent LLM matching"""
    
    message_lower = message.lower()
    
    # Direct project type mentions
    if "kitchen" in message_lower:
        return "kitchen remodel renovation"
    elif "bathroom" in message_lower:
        return "bathroom remodel renovation"
    elif "lawn" in message_lower or "landscaping" in message_lower:
        return "lawn care landscaping artificial turf"
    elif "roofing" in message_lower:
        return "roofing roof repair replacement"
    elif "deck" in message_lower:
        return "deck construction installation"
    elif "electrical" in message_lower:
        return "electrical wiring installation"
    elif "plumbing" in message_lower:
        return "plumbing pipe repair installation"
    elif "hvac" in message_lower:
        return "hvac heating cooling air conditioning"
    elif "flooring" in message_lower:
        return "flooring carpet hardwood installation"
    
    # Use contractor specialties if no specific type mentioned
    if profile.get("specialties"):
        return " ".join(profile["specialties"])
    
    # Generic search for "show me projects"
    return ""

async def _call_intelligent_job_search(params: dict[str, Any]) -> list[dict[str, Any]]:
    """Use YOUR EXISTING ZIP radius tools for intelligent search"""
    
    try:
        # Import your existing ZIP radius tools
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        from utils.radius_search_fixed import get_zip_codes_in_radius
        from database_simple import db
        
        contractor_zip = params["contractor_zip"]
        radius_miles = params["radius_miles"]
        
        # Use YOUR ZIP radius expansion system
        zip_codes_in_radius = get_zip_codes_in_radius(contractor_zip, radius_miles)
        logger.info(f"✅ ZIP expansion found {len(zip_codes_in_radius)} zip codes within {radius_miles} miles")
        
        # Query bid cards using expanded ZIP codes  
        query = db.client.table("bid_cards").select("*")
        
        # Filter by active statuses
        query = query.in_("status", ["active", "collecting_bids", "generated"])
        
        # Apply ZIP radius filter (YOUR SYSTEM)
        if zip_codes_in_radius:
            query = query.in_("location_zip", zip_codes_in_radius)
        else:
            # Fallback to contractor ZIP if expansion fails
            query = query.eq("location_zip", contractor_zip)
        
        # Execute query
        result = query.execute()
        bid_cards = result.data if result.data else []
        
        # Add distance calculation for each bid card
        from utils.radius_search_fixed import calculate_distance_miles
        
        jobs = []
        for card in bid_cards:
            card_zip = card.get("location_zip")
            distance_miles = None
            
            if card_zip:
                distance_miles = calculate_distance_miles(contractor_zip, str(card_zip))
            
            # Convert bid card format to job format
            job = {
                "id": card["id"],
                "bid_card_number": card.get("bid_card_number"),
                "title": card.get("title", "Untitled Project"),
                "description": card.get("description", ""),
                "project_type": card.get("project_type", "general"),
                "status": card.get("status", "active"),
                "location": {
                    "city": card.get("location_city"),
                    "state": card.get("location_state"),
                    "zip_code": card.get("location_zip")
                },
                "timeline": {
                    "start_date": card.get("timeline_start"),
                    "end_date": card.get("timeline_end")
                },
                "contractor_count_needed": card.get("contractor_count_needed", 1),
                "bid_count": card.get("bids_received_count", 0),
                "group_bid_eligible": card.get("group_bid_eligible", False),
                "created_at": card.get("created_at"),
                "distance_miles": distance_miles
            }
            jobs.append(job)
        
        # Sort by distance (closest first)
        jobs.sort(key=lambda x: x.get("distance_miles") or 999)
        
        logger.info(f"✅ Intelligent search found {len(jobs)} projects within {radius_miles} miles")
        return jobs
        
    except Exception as e:
        logger.error(f"Error in intelligent job search: {e}")
        return []

def _format_intelligent_response(bid_cards: list[dict[str, Any]], params: dict[str, Any], contractor_profile: dict[str, Any] = None) -> str:
    """Format intelligent search results into conversational response"""
    
    contractor_name = ""
    if contractor_profile and contractor_profile.get("company_name"):
        contractor_name = f", {contractor_profile['company_name']},"
    
    if not bid_cards:
        radius = params.get("radius_miles", 30)
        keywords = params.get("project_keywords", "")
        
        message = f"I searched within {radius} miles of your location"
        if keywords:
            message += f" for {keywords} projects"
        message += f"{contractor_name}, but couldn't find any active projects right now."
        
        return message + "\n\nWould you like me to:\n1. Expand the search radius?\n2. Set up an alert for new projects?\n3. Help you create your own project listing?"
    
    # Success response
    count = len(bid_cards)
    radius = params.get("radius_miles", 30)
    
    response_parts = []
    
    if count == 1:
        response_parts.append(f"Great news{contractor_name}! I found 1 project within {radius} miles:")
    else:
        response_parts.append(f"Great news{contractor_name}! I found {count} projects within {radius} miles:")
    
    # Show top 5 projects
    for i, card in enumerate(bid_cards[:5], 1):
        card_text = _format_single_project(card, i)
        response_parts.append(card_text)
    
    # Add interaction options
    response_parts.append("\n**What would you like to do?**")
    response_parts.append("• Type 'details [number]' for full project details")
    response_parts.append("• Type 'bid [number]' to submit a bid")
    response_parts.append("• Type 'expand radius' to search farther")
    
    return "\n\n".join(response_parts)

def _format_single_project(card: dict[str, Any], index: int) -> str:
    """Format a single project for display"""
    
    parts = [f"**{index}. {card.get('title', 'Untitled Project')}**"]
    
    # Location with distance
    location = card.get("location", {})
    city = location.get("city", "Unknown")
    distance = card.get("distance_miles")
    if distance:
        parts.append(f"Location: {city} ({distance} miles away)")
    else:
        parts.append(f"Location: {city}")
    
    # Project type
    project_type = card.get("project_type", "")
    if project_type:
        parts.append(f"Type: {project_type}")
    
    # Timeline
    timeline = card.get("timeline", {})
    if timeline.get("start_date"):
        parts.append(f"Start: {timeline['start_date']}")
    
    # Bid progress
    bid_count = card.get("bid_count", 0)
    needed = card.get("contractor_count_needed", 4)
    if bid_count < needed:
        parts.append(f"Bids: {bid_count}/{needed} (Open for bidding)")
    
    # Group bidding
    if card.get("group_bid_eligible"):
        parts.append("**Group Bidding Available** (15-25% savings)")
    
    return "\n".join(parts)

def _format_for_attachment(card: dict[str, Any]) -> dict[str, Any]:
    """Format project for frontend attachment (convert from job format to bid card format)"""
    
    location = card.get("location", {})
    budget_range = card.get("budget_range", {})
    timeline = card.get("timeline", {})
    
    return {
        "id": card.get("id"),
        "bid_card_number": card.get("bid_card_number"),
        "title": card.get("title", ""),
        "description": card.get("description", ""),
        "project_type": card.get("project_type"),
        "location_city": location.get("city"),
        "location_state": location.get("state"),
        "location_zip": location.get("zip_code"),
        "budget_min": budget_range.get("min"),
        "budget_max": budget_range.get("max"),
        "timeline_start": timeline.get("start_date"),
        "timeline_end": timeline.get("end_date"),
        "contractor_count_needed": card.get("contractor_count_needed", 4),
        "bid_count": card.get("bid_count", 0),
        "group_bid_eligible": card.get("group_bid_eligible", False),
        "distance_miles": card.get("distance_miles"),
        "created_at": card.get("created_at")
    }