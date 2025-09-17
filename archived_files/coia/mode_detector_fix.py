"""
FIXED Mode Detector for COIA that ACTUALLY triggers the right modes
"""

import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

def detect_mode_simple(user_message: str, contractor_profile: Dict[str, Any] = None) -> str:
    """
    INTELLIGENT mode detection - let the AI handle the complexity
    Focus on INTENT, not hardcoded patterns
    """
    message_lower = user_message.lower()
    
    # RESEARCH TRIGGERS - Simple, broad patterns for business introductions
    research_indicators = [
        # Business introduction patterns
        "i am", "i'm", "we are", "we're", "my company", "our company", 
        "my business", "our business", "i own", "we own", "i run", "we run",
        
        # Contact info sharing (suggests they're a contractor)
        "@", "phone", "email", "website", "contact",
        
        # Industry terms
        "contractor", "business", "company", "years in business", 
        "specialize", "install", "provide", "services"
    ]
    
    # Check if this looks like a business introduction
    research_score = sum(1 for indicator in research_indicators if indicator in message_lower)
    
    if research_score >= 1:  # Even single indicator suggests contractor introduction on landing page
        logger.info(f"🎯 RESEARCH MODE TRIGGERED by business introduction (score: {research_score})")
        return "research"
    
    # ACCOUNT CREATION - Clear intent to create account
    if any(phrase in message_lower for phrase in ["create account", "sign up", "register", "get started"]):
        logger.info(f"🏗️ ACCOUNT_CREATION MODE TRIGGERED")
        return "account_creation"
    
    # BID CARD SEARCH - Looking for projects
    if any(phrase in message_lower for phrase in ["find projects", "show projects", "opportunities", "bid on"]):
        logger.info(f"🔍 BID_CARD_SEARCH MODE TRIGGERED")
        return "bid_card_search"
    
    # Default to conversation - let AI handle the intelligence
    logger.info(f"💬 CONVERSATION MODE - AI will determine next steps")
    return "conversation"


async def fixed_mode_detector_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fixed mode detector that actually triggers the right modes for landing page
    Prevents infinite loops while still enabling research functionality
    """
    try:
        logger.info("FIXED MODE DETECTOR: Analyzing user message for landing page")
        
        messages = state.get("messages", [])
        if not messages:
            return {
                "current_mode": "conversation",
                "mode_detector_decision": "conversation"
            }
        
        # Get last user message
        last_message = messages[-1]
        if hasattr(last_message, "content"):
            user_message = last_message.content
        else:
            user_message = str(last_message)
        
        contractor_profile = state.get("contractor_profile", {})
        interface = state.get("interface", "chat")
        mode_detector_visits = state.get("mode_detector_visits", 0)
        
        logger.info(f"Analyzing message: {user_message[:100]}...")
        logger.info(f"Interface: {interface}, Mode detector visits: {mode_detector_visits}")
        
        # PREVENT INFINITE LOOPS: Only allow research once per session
        research_completed = state.get("research_completed", False)
        if research_completed:
            logger.info("Research already completed - defaulting to conversation")
            detected_mode = "conversation"
        elif mode_detector_visits >= 3:
            logger.info(f"Too many mode detector visits ({mode_detector_visits}) - defaulting to conversation")
            detected_mode = "conversation"
        else:
            # Use the smart detection logic
            detected_mode = detect_mode_simple(user_message, contractor_profile)
        
        logger.info(f"FIXED MODE DETECTOR DECISION: {detected_mode}")
        
        # Track previous mode to prevent loops
        current_mode = state.get("current_mode", "conversation")
        
        return {
            "previous_mode": current_mode,  # Save current as previous
            "current_mode": detected_mode,
            "mode_detector_decision": detected_mode,
            "mode_detector_visits": mode_detector_visits + 1
        }
        
    except Exception as e:
        logger.error(f"Error in fixed mode detector: {e}")
        return {
            "current_mode": "conversation",
            "mode_detector_decision": "conversation"
        }