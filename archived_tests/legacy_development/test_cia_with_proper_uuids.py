#!/usr/bin/env python3
"""
Test CIA agent with proper UUID formats
"""

import asyncio
import aiohttp
import json
import time
import uuid

async def test_single_message():
    """Test single message with proper UUIDs"""
    
    # Generate proper UUIDs
    conversation_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    url = "http://localhost:8008/api/cia/stream"
    payload = {
        "messages": [{"role": "user", "content": "Hi Alex! I need help renovating my kitchen. Can you help me figure out what this will involve?"}],
        "conversation_id": conversation_id,
        "user_id": user_id,
        "max_tokens": 200
    }
    
    print("=== CIA SINGLE MESSAGE TEST ===")
    print(f"URL: {url}")
    print(f"User ID: {user_id}")
    print(f"Conversation ID: {conversation_id}")
    print(f"Message: {payload['messages'][0]['content']}")
    print("\nResponse:")
    
    start_time = time.time()
    
    try:
        timeout = aiohttp.ClientTimeout(total=15)  # Shorter timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                print(f"Status: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"ERROR: {error_text}")
                    return None
                
                full_response = ""
                chunk_count = 0
                
                print("CIA Response: ", end="", flush=True)
                
                async for line in response.content:
                    chunk_count += 1
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            if data.get('choices') and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    print(content, end="", flush=True)
                                    full_response += content
                            elif data.get('done'):
                                print(f"\n[Stream completed after {chunk_count} chunks]")
                                break
                        except json.JSONDecodeError as e:
                            print(f"\n[JSON decode error in chunk {chunk_count}: {line[:100]}...]")
                            continue
                    elif line == "data: [DONE]":
                        print(f"\n[Stream completed after {chunk_count} chunks]")
                        break
                    elif line:
                        print(f"\n[Non-data line: {line[:50]}...]")
                        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"\n\nResponse Time: {response_time:.2f}s")
        print(f"Full Response: {full_response[:200]}..." if len(full_response) > 200 else full_response)
        
        return full_response
        
    except asyncio.TimeoutError:
        print(f"\n[TIMEOUT after 15 seconds]")
        return None
    except Exception as e:
        print(f"\n[ERROR: {e}]")
        return None

async def test_multi_turn_conversation():
    """Test multi-turn conversation if first message works"""
    print("\n\n=== MULTI-TURN CONVERSATION TEST ===")
    
    # Generate proper UUIDs for conversation
    conversation_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    url = "http://localhost:8008/api/cia/stream"
    
    # Conversation flow
    conversation = [
        "Hi! I want to renovate my bathroom but I'm on a budget. Can you help?",
        "It's a small bathroom, maybe 50 square feet. The main issue is it feels cramped and outdated.",
        "I'm thinking maybe $8,000 to $12,000? Is that realistic?",
        "Timeline-wise, I'm flexible. Maybe over the next 2-3 months?",
        "Perfect! What's the next step?"
    ]
    
    messages_history = []
    
    for turn, user_message in enumerate(conversation, 1):
        print(f"\n--- TURN {turn} ---")
        print(f"USER: {user_message}")
        
        # Add user message to history
        messages_history.append({"role": "user", "content": user_message})
        
        payload = {
            "messages": messages_history.copy(),
            "conversation_id": conversation_id,
            "user_id": user_id,
            "max_tokens": 150
        }
        
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"ERROR: {error_text}")
                        break
                    
                    print("CIA: ", end="", flush=True)
                    cia_response = ""
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                if data.get('choices') and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        print(content, end="", flush=True)
                                        cia_response += content
                                elif data.get('done'):
                                    break
                            except json.JSONDecodeError:
                                continue
                        elif line == "data: [DONE]":
                            break
                    
                    end_time = time.time()
                    print(f"\n[Response time: {end_time - start_time:.2f}s]")
                    
                    # Add CIA response to history
                    if cia_response:
                        messages_history.append({"role": "assistant", "content": cia_response})
                    else:
                        print("ERROR: No response received")
                        break
                    
                    # Brief pause between turns
                    await asyncio.sleep(1)
                    
        except asyncio.TimeoutError:
            print(f"[TIMEOUT in turn {turn}]")
            break
        except Exception as e:
            print(f"[ERROR in turn {turn}: {e}]")
            break
    
    print(f"\n=== CONVERSATION COMPLETED: {turn} turns ===")

async def main():
    print("Testing CIA Agent with Proper UUIDs")
    print("===================================")
    
    # Test 1: Single message
    result = await test_single_message()
    
    if result:
        print("\nSingle message test PASSED - proceeding to multi-turn test")
        await test_multi_turn_conversation()
    else:
        print("\nSingle message test FAILED - skipping multi-turn test")

if __name__ == "__main__":
    asyncio.run(main())