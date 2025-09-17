"""
Debug what the API result actually contains
"""
import asyncio
import json
from agents.coia.unified_graph import invoke_coia_landing_page, create_unified_coia_system

async def debug_api_result():
    """Check what invoke_coia_landing_page actually returns"""
    
    print("=== DEBUGGING API RESULT ===")
    
    # Create the COIA app
    app = await create_unified_coia_system()
    
    # Test message that should trigger bid card search
    user_message = "I am a General Contractor. Please show me available projects."
    session_id = "debug-api-result-123"
    
    print(f"Testing message: {user_message}")
    print(f"Session ID: {session_id}")
    print()
    
    try:
        # Call the landing page function directly (same as API)
        result = await invoke_coia_landing_page(
            app=app,
            user_message=user_message,
            session_id=session_id
        )
        
        print("=== INVOKE RESULT ANALYSIS ===")
        print(f"Result type: {type(result)}")
        
        if isinstance(result, dict):
            print(f"Result keys: {list(result.keys())}")
            print()
            
            # Check for bid_cards_attached specifically
            bid_cards_attached = result.get("bid_cards_attached")
            print(f"bid_cards_attached exists: {'bid_cards_attached' in result}")
            print(f"bid_cards_attached value: {bid_cards_attached}")
            print(f"bid_cards_attached type: {type(bid_cards_attached)}")
            print(f"bid_cards_attached bool: {bool(bid_cards_attached)}")
            print()
            
            # Check messages for text content
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    content = last_message.content
                    print(f"Message content contains projects: {'projects' in content.lower()}")
                    print(f"Message content contains found: {'found' in content.lower()}")
                    # Remove emojis to avoid Unicode errors
                    safe_content = ''.join(c for c in content if ord(c) < 128)
                    print(f"Safe message content: {safe_content[:200]}...")
                    print()
            
            # Print all keys that might contain bid cards
            print("=== ALL RESULT KEYS ===")
            for key, value in result.items():
                if isinstance(value, (list, dict)) and value:
                    print(f"{key}: {type(value)} (len={len(value) if hasattr(value, '__len__') else 'N/A'})")
                elif isinstance(value, str) and len(value) > 50:
                    print(f"{key}: str (len={len(value)})")
                else:
                    print(f"{key}: {value}")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_api_result())