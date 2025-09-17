"""
BSA Subagent Router - Smart routing to avoid calling all 4 subagents
Routes to 0-1 subagents based on message intent
"""

import re
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BSASubagentRouter:
    """Routes messages to appropriate subagents based on intent"""
    
    # Keywords and patterns for each subagent
    BID_SEARCH_PATTERNS = [
        r'\b(find|search|show|list|available|near|opportunities|jobs?)\b',
        r'\b(bid cards?|looking for|what.{0,10}available)\b',
        r'\b(in my area|nearby|within \d+ miles?)\b',
        r'\b(new (projects?|work|opportunities))\b',
    ]
    
    # Patterns that indicate discussing existing "My Bids" projects (should NOT route to bid-search)
    MY_PROJECTS_PATTERNS = [
        r'\b(my (projects?|bids?|work|quotes?))\b',
        r'\b((projects?|work) I (quoted|bid|submitted))\b', 
        r'\b(the (kitchen|bathroom|plumbing|electrical) (project|work))\b',
        r'\b(tell me about|details of|status of|update on)\b.*\b(project|bid|quote)\b',
        r'\b(IBC-|bid card)\b',
    ]
    
    MARKET_RESEARCH_PATTERNS = [
        r'\b(price|pricing|cost|rate|market|competitive|competition|average)\b',
        r'\b(what.{0,10}(charge|bid)|how much|typical|going rate)\b',
        r'\b(market (analysis|research|trend)|competitor)\b',
    ]
    
    BID_SUBMISSION_PATTERNS = [
        r'\b(submit|send|create|write|prepare|proposal|bid)\b',
        r'\b(ready to (bid|submit)|want to (bid|submit))\b',
        r'\b(help.{0,10}(proposal|bid)|format|structure)\b',
    ]
    
    GROUP_BIDDING_PATTERNS = [
        r'\b(group|team|multiple|together|collaborate|partner)\b',
        r'\b(group (bid|project)|work together|team up)\b',
        r'\b(save|savings|discount|bulk)\b',
    ]
    
    @classmethod
    def route_message(cls, message: str, conversation_history: List[Dict] = None) -> List[str]:
        """
        Route message to appropriate subagent(s)
        
        Args:
            message: Current user message
            conversation_history: Previous conversation for context
            
        Returns:
            List of subagent names to invoke (0-1 typically)
        """
        message_lower = message.lower()
        subagents = []
        
        # FIRST: Check if asking about existing "My Bids" projects - should NOT use subagents
        if cls._matches_patterns(message_lower, cls.MY_PROJECTS_PATTERNS):
            logger.info(f"BSA Router: Detected My Projects query - main agent will handle directly: {message[:50]}...")
            return []  # Return empty - let main agent handle without subagents
        
        # Check for bid search intent (only for NEW projects)
        elif cls._matches_patterns(message_lower, cls.BID_SEARCH_PATTERNS):
            subagents.append("bid-search")
            logger.info(f"BSA Router: Routing to bid-search for new projects: {message[:50]}...")
        
        # Check for market research intent
        elif cls._matches_patterns(message_lower, cls.MARKET_RESEARCH_PATTERNS):
            subagents.append("market-research")
            logger.info(f"BSA Router: Routing to market-research based on: {message[:50]}...")
        
        # Check for bid submission intent
        elif cls._matches_patterns(message_lower, cls.BID_SUBMISSION_PATTERNS):
            # Check if we have context about a specific project
            if cls._has_project_context(conversation_history):
                subagents.append("bid-submission")
                logger.info(f"BSA Router: Routing to bid-submission based on: {message[:50]}...")
            else:
                # Need to search first
                subagents.append("bid-search")
                logger.info(f"BSA Router: Need project context first, routing to bid-search")
        
        # Check for group bidding intent
        elif cls._matches_patterns(message_lower, cls.GROUP_BIDDING_PATTERNS):
            subagents.append("group-bidding")
            logger.info(f"BSA Router: Routing to group-bidding based on: {message[:50]}...")
        
        # If no specific intent detected, let main agent handle
        if not subagents:
            logger.info(f"BSA Router: No specific subagent needed, main agent will handle")
        
        return subagents
    
    @classmethod
    def _matches_patterns(cls, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the patterns"""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def _has_project_context(cls, conversation_history: Optional[List[Dict]]) -> bool:
        """Check if conversation has project context for bidding"""
        if not conversation_history:
            return False
        
        # Look for bid card mentions or project details in recent messages
        recent_messages = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        
        for msg in recent_messages:
            content = msg.get("content", "").lower()
            if any(term in content for term in ["bid card", "project", "BC-", "budget", "timeline"]):
                return True
        
        return False
    
    @classmethod
    def should_use_planning(cls, message: str, conversation_history: Optional[List[Dict]] = None) -> bool:
        """
        Determine if planning tool should be used
        
        Complex multi-step requests need planning
        """
        message_lower = message.lower()
        
        # Complex requests that need planning
        complex_indicators = [
            r'\b(and then|after that|first|second|finally)\b',
            r'\b(multiple|several|all|comprehensive)\b',
            r'\b(analyze.{0,20}then|research.{0,20}submit)\b',
        ]
        
        # Check for multi-step request
        if cls._matches_patterns(message_lower, complex_indicators):
            return True
        
        # Check if multiple subagents would be called
        subagents = cls.route_message(message, conversation_history)
        if len(subagents) > 1:
            return True
        
        # Simple single-intent messages don't need planning
        return False
    
    @classmethod
    def get_routing_explanation(cls, message: str) -> str:
        """Get human-readable explanation of routing decision"""
        message_lower = message.lower()
        explanations = []
        
        if cls._matches_patterns(message_lower, cls.BID_SEARCH_PATTERNS):
            explanations.append("Searching for available projects")
        
        if cls._matches_patterns(message_lower, cls.MARKET_RESEARCH_PATTERNS):
            explanations.append("Analyzing market pricing")
        
        if cls._matches_patterns(message_lower, cls.BID_SUBMISSION_PATTERNS):
            explanations.append("Preparing bid proposal")
        
        if cls._matches_patterns(message_lower, cls.GROUP_BIDDING_PATTERNS):
            explanations.append("Exploring group bidding opportunities")
        
        if not explanations:
            return "Handling general contractor inquiry"
        
        return " and ".join(explanations)