import sys
import os
import asyncio
import logging

# Configure logging to see our debug output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add paths
sys.path.insert(0, r'C:\Users\Not John Or Justin\Documents\instabids\ai-agents')
sys.path.insert(0, r'C:\Users\Not John Or Justin\Documents\instabids\deepagents-system\src')

async def test_gpt4_direct():
    """Direct test of BSA singleton with GPT-4 to see what's returned"""
    print("=== DIRECT BSA SINGLETON GPT-4 TEST ===")
    
    try:
        from agents.bsa.bsa_singleton import BSASingleton
        from deepagents.model import get_default_model
        
        print("SUCCESS: Imports successful")
        
        # Check the model configuration
        model = get_default_model()
        print(f"Model: {model.model_name}")
        print(f"API Key: {'Set' if model.openai_api_key else 'NOT Set'}")
        
        # Get singleton instance
        singleton = await BSASingleton.get_instance()
        print("SUCCESS: BSA singleton created")
        
        # Create minimal test state
        test_state = {
            "messages": [
                {"role": "user", "content": "Hello, can you help me find turf projects?"}
            ]
        }
        
        print("STARTING: Calling BSA singleton.invoke() directly...")
        
        # This should trigger our debug logging
        result = await singleton.invoke(test_state, "test-thread-gpt4-debug")
        
        print(f"SUCCESS: Result received: {type(result)}")
        print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict) and "messages" in result:
            print(f"Messages in result: {len(result['messages'])}")
            if result['messages']:
                last_msg = result['messages'][-1]
                print(f"Last message: {last_msg}")
                if isinstance(last_msg, dict):
                    content = last_msg.get('content', '')
                    print(f"Content length: {len(content)}")
                    print(f"Content preview: {content[:200]}...")
                else:
                    print(f"Last message type: {type(last_msg)}")
        
        return result
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_gpt4_direct())