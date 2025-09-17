import sys
import os
import asyncio
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add paths
sys.path.insert(0, r'C:\Users\Not John Or Justin\Documents\instabids\ai-agents')
sys.path.insert(0, r'C:\Users\Not John Or Justin\Documents\instabids\deepagents-system\src')

async def test_bsa_content_extraction():
    """Test BSA content extraction to see exactly what GPT-4 returns"""
    print("=== BSA CONTENT EXTRACTION DEBUG TEST ===")
    
    try:
        from agents.bsa.bsa_singleton import BSASingleton
        from database import SupabaseDB
        from adapters.contractor_context import ContractorContextAdapter
        from memory.contractor_ai_memory import ContractorAIMemory
        from services.my_bids_tracker import my_bids_tracker
        
        # Get BSA singleton
        singleton = await BSASingleton.get_instance()
        print("SUCCESS: BSA singleton created")
        
        # Build realistic state like the comprehensive test
        contractor_id = "87f93fbd-151d-4f17-9311-70ef9ba5256f"
        session_id = "content-extraction-debug"
        message = "show me available turf projects within 30 miles of ZIP code 33442"
        
        # Initialize context systems
        db = SupabaseDB()
        contractor_adapter = ContractorContextAdapter()
        ai_memory = ContractorAIMemory()
        
        print("Loading contractor context...")
        contractor_context = await asyncio.to_thread(
            contractor_adapter.get_contractor_context,
            contractor_id=contractor_id,
            session_id=session_id
        )
        print(f"Contractor context loaded: {len(str(contractor_context))} chars")
        
        print("Loading AI memory...")
        ai_memory_context = await ai_memory.get_memory_for_system_prompt(contractor_id)
        print(f"AI memory loaded: {len(ai_memory_context)} chars")
        
        print("Loading My Bids context...")
        my_bids_context = my_bids_tracker.load_full_my_bids_context(contractor_id)
        print(f"My Bids context loaded: {type(my_bids_context)}")
        
        # Create state exactly like the comprehensive test does
        state = {
            "messages": [{"role": "user", "content": message}],
            "contractor_id": contractor_id,
            "contractor_context": contractor_context,
            "ai_memory_context": ai_memory_context,
            "my_bids_context": my_bids_context,
            "session_id": session_id,
            "todos": [],
            "files": {}
        }
        
        print(f"State built with {len(state['messages'])} messages")
        print(f"Message content: {message}")
        
        thread_id = BSASingleton.get_thread_id(contractor_id, session_id)
        print(f"Using thread_id: {thread_id}")
        
        print("\n=== CALLING BSA SINGLETON INVOKE ===")
        result = await singleton.invoke(state, thread_id)
        
        print(f"\n=== ANALYZING RESULT STRUCTURE ===")
        print(f"Result type: {type(result)}")
        print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            print(f"Result has 'messages' key: {'messages' in result}")
            
            if "messages" in result:
                messages = result["messages"]
                print(f"Messages type: {type(messages)}")
                print(f"Number of messages: {len(messages) if messages else 0}")
                
                if messages:
                    print(f"\n=== ANALYZING ALL MESSAGES ===")
                    for i, msg in enumerate(messages):
                        print(f"Message {i}: Type={type(msg)}")
                        if isinstance(msg, dict):
                            print(f"  Keys: {list(msg.keys())}")
                            print(f"  Role: {repr(msg.get('role'))}")
                            content = msg.get('content', '')
                            print(f"  Content type: {type(content)}")
                            print(f"  Content length: {len(content) if content else 0}")
                            if content:
                                print(f"  Content preview: {repr(content[:100])}...")
                            else:
                                print(f"  NO CONTENT")
                        else:
                            print(f"  Raw message: {msg}")
                    
                    # Focus on the last message (should be assistant response)
                    print(f"\n=== FOCUSING ON LAST MESSAGE ===")
                    last_msg = messages[-1]
                    print(f"Last message type: {type(last_msg)}")
                    
                    if isinstance(last_msg, dict):
                        print(f"Last message keys: {list(last_msg.keys())}")
                        role = last_msg.get('role')
                        content = last_msg.get('content')
                        
                        print(f"Role: {repr(role)}")
                        print(f"Content type: {type(content)}")
                        print(f"Content value: {repr(content)}")
                        print(f"Content length: {len(content) if content else 0}")
                        
                        # Test the exact condition from BSA code
                        condition_result = (role == "assistant" and content)
                        print(f"\nCondition test (role == 'assistant' and content): {condition_result}")
                        
                        if condition_result:
                            print("SUCCESS: Content extraction should work!")
                            print(f"Would extract: {len(content)} chars")
                            print(f"Preview: {content[:200]}...")
                        else:
                            print("PROBLEM: Content extraction condition fails")
                            if role != "assistant":
                                print(f"  - Role mismatch: expected 'assistant', got {repr(role)}")
                            if not content:
                                print(f"  - No content: {repr(content)}")
                    else:
                        print(f"Last message is not dict: {last_msg}")
            else:
                print("No 'messages' key in result")
                print(f"Available keys: {list(result.keys())}")
        
        return result
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_bsa_content_extraction())