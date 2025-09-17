"""
CIA AGENT CATEGORIZATION INTEGRATION
Provides the categorize_project tool for the CIA agent to use
"""

from .tool_definition import CATEGORIZATION_TOOL
from .tool_handler import handle_categorize_project, format_response_for_agent

# Export the tool definition for CIA agent
def get_categorization_tool():
    """Get the categorization tool definition for CIA agent"""
    return CATEGORIZATION_TOOL

# Export the handler function
async def handle_categorization_tool_call(tool_call_args: dict, bid_card_id: str) -> dict:
    """
    Handle a categorization tool call from CIA agent
    
    Args:
        tool_call_args: Arguments from the tool call (description, context)
        bid_card_id: Current bid card ID from CIA conversation
        
    Returns:
        Result dictionary with success status and response message
    """
    result = await handle_categorize_project(
        description=tool_call_args.get('description', ''),
        bid_card_id=bid_card_id,
        context=tool_call_args.get('context', '')
    )
    
    return result

def get_categorization_response(result: dict) -> str:
    """
    Format categorization result for CIA agent response
    
    Args:
        result: Result from handle_categorization_tool_call
        
    Returns:
        Natural language response for CIA to use
    """
    return format_response_for_agent(result)

# For import convenience
__all__ = [
    'get_categorization_tool',
    'handle_categorization_tool_call', 
    'get_categorization_response'
]