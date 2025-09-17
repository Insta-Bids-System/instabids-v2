"""
SHARED CATEGORIZATION TOOL HANDLER
Processes categorize_project tool calls from CIA and IRIS agents
"""

import logging
from typing import Dict, Any
from .simple_categorization_tool import categorize_and_save_project, format_response_for_agent

logger = logging.getLogger(__name__)

async def handle_categorize_project(
    description: str,
    bid_card_id: str,
    context: str = "",
    agent_type: str = "CIA"
) -> Dict[str, Any]:
    """
    Handle categorization tool call from CIA or IRIS agents
    
    Args:
        description: Full project description from conversation
        bid_card_id: ID of bid card to categorize and potentially update
        context: Additional context (urgency, photo analysis, etc.)
        agent_type: Which agent is calling (CIA/IRIS)
    
    Returns:
        Dictionary with categorization results and next steps
    """
    return await categorize_and_save_project(
        description=description,
        bid_card_id=bid_card_id,
        context=context
    )

# For import convenience
__all__ = ['handle_categorize_project', 'format_response_for_agent']