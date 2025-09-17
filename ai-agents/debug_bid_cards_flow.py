"""
Debug bid cards flow - Test why bid_cards_attached is null in API response
"""
import asyncio
import json
from agents.coia.unified_graph import invoke_coia_landing_page, create_unified_coia_system

async def test_bid_cards_flow():
    """Test the bid cards flow to see what's happening"""
    
    print("=== DEBUGGING BID CARDS FLOW ===")
    
    # Create the COIA app
    app = await create_unified_coia_system()
    
    # Test message that should trigger bid card search
    user_message = "I am a General Contractor specializing in kitchen remodeling and home renovations. My business is ABC Construction, I am John Smith the owner, and I am located in Miami, FL and have been in business for 8 years. Please show me available projects."
    session_id = "debug-bid-cards-123"
    
    print(f"Testing message: {user_message}")
    print(f"Session ID: {session_id}")
    print()
    
    # Call the landing page function directly
    result = await invoke_coia_landing_page(
        app=app,
        user_message=user_message,
        session_id=session_id
    )
    
    print("=== FULL RESULT ANALYSIS ===")
    print(f"Result type: {type(result)}")
    print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
    print()
    
    # Check for bid_cards_attached specifically
    bid_cards_attached = result.get("bid_cards_attached", "NOT_FOUND")
    print(f"bid_cards_attached: {bid_cards_attached}")
    print(f"bid_cards_attached type: {type(bid_cards_attached)}")
    if isinstance(bid_cards_attached, list):
        print(f"bid_cards_attached length: {len(bid_cards_attached)}")
        if bid_cards_attached:
            print(f"First bid card keys: {list(bid_cards_attached[0].keys())}")
    print()
    
    # Check for other potential bid card fields
    print("=== CHECKING FOR OTHER BID CARD FIELDS ===")
    for key, value in result.items():
        if "bid" in key.lower() or "card" in key.lower():
            print(f"{key}: {value} (type: {type(value)})")
    print()
    
    # Check current_mode 
    current_mode = result.get("current_mode", "NOT_FOUND")
    print(f"current_mode: {current_mode}")
    
    # Check tool_results
    tool_results = result.get("tool_results", {})
    print(f"tool_results: {tool_results}")
    if isinstance(tool_results, dict) and "bid_card_search" in tool_results:
        print(f"bid_card_search tool result: {tool_results['bid_card_search']}")
    print()
    
    # Check messages
    messages = result.get("messages", [])
    print(f"Messages count: {len(messages)}")
    if messages:
        last_message = messages[-1]
        print(f"Last message: {last_message}")
        if hasattr(last_message, 'content'):
            content = last_message.content
            print(f"Last message content length: {len(content)}")
            print(f"Last message content preview: {content[:200]}...")
    
    print()
    print("=== END DEBUG ===")

if __name__ == "__main__":
    asyncio.run(test_bid_cards_flow())