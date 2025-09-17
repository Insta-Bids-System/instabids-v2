#!/usr/bin/env python3
"""
Debug script to see EXACTLY what's being sent to OpenAI
Including full system prompt, tools, and message structure
"""

import asyncio
import json
from agents.cia.agent import CustomerInterfaceAgent
from agents.cia.prompts import SYSTEM_PROMPT, get_conversation_prompt

async def debug_full_context():
    """Show exactly what CIA sends to OpenAI"""
    
    # Initialize agent
    agent = CustomerInterfaceAgent()
    
    print("="*80)
    print("FULL CIA AGENT CONTEXT SENT TO OPENAI")
    print("="*80)
    
    # 1. Show system prompt
    print("\n1. SYSTEM PROMPT:")
    print("-"*40)
    
    # Simulate context
    context = {
        "collected_info": {},
        "missing_fields": ["project_type", "location", "timeline"],
        "current_phase": "understanding",
        "new_user": True
    }
    other_projects = []
    
    # Get the full system prompt as it would be built
    base_prompt = SYSTEM_PROMPT
    conversation_guidance = get_conversation_prompt("understanding", context)
    
    full_system_prompt = f"{base_prompt}{conversation_guidance}"
    
    print(f"Length: {len(full_system_prompt)} characters")
    print("\nFIRST 500 CHARS:")
    print(full_system_prompt[:500])
    print("\n[...middle content...]")
    print("\nLAST 500 CHARS:")
    print(full_system_prompt[-500:])
    
    # 2. Show tools
    print("\n\n2. TOOLS PROVIDED:")
    print("-"*40)
    
    for i, tool in enumerate(agent.tools):
        print(f"\nTool {i+1}: {tool['function']['name']}")
        print(f"Description: {tool['function']['description']}")
        
        # Show parameters
        params = tool['function']['parameters']['properties']
        print(f"Parameters ({len(params)} fields):")
        for param_name in list(params.keys())[:5]:  # First 5 params
            param_info = params[param_name]
            print(f"  - {param_name}: {param_info.get('type', 'unknown')} - {param_info.get('description', '')[:50]}...")
        if len(params) > 5:
            print(f"  ... and {len(params) - 5} more fields")
    
    # 3. Show OpenAI call configuration
    print("\n\n3. OPENAI API CONFIGURATION:")
    print("-"*40)
    print(f"Model: gpt-4o")
    print(f"Temperature: 0.3")
    print(f"Max tokens: 1000")
    print(f"Tool choice: auto")
    
    # 4. Show example message structure
    print("\n\n4. EXAMPLE MESSAGE STRUCTURE:")
    print("-"*40)
    
    test_messages = [
        {"role": "system", "content": full_system_prompt},
        {"role": "user", "content": "I need my roof fixed"},
        {"role": "assistant", "content": "I'll help you with that. What's your location?"},
        {"role": "user", "content": "I'm in 90210"}
    ]
    
    print("Messages array structure:")
    for i, msg in enumerate(test_messages):
        if i == 0:
            print(f"  [{i}] role: {msg['role']}, content: <{len(msg['content'])} chars of system prompt>")
        else:
            print(f"  [{i}] role: {msg['role']}, content: '{msg['content']}'")
    
    # 5. Calculate total context size
    print("\n\n5. CONTEXT SIZE ANALYSIS:")
    print("-"*40)
    
    # Estimate token usage
    total_chars = len(full_system_prompt) + len(json.dumps(agent.tools))
    estimated_tokens = total_chars / 4  # Rough estimate
    
    print(f"System prompt: {len(full_system_prompt)} chars")
    print(f"Tools JSON: {len(json.dumps(agent.tools))} chars")
    print(f"Total context: {total_chars} chars")
    print(f"Estimated tokens: ~{int(estimated_tokens)} tokens")
    
    # 6. Show specific business logic rules
    print("\n\n6. KEY BUSINESS LOGIC IN PROMPT:")
    print("-"*40)
    
    business_rules = [
        "GROUP BIDDING",
        "EMERGENCY", 
        "BUDGET CONTEXT",
        "SERVICE TYPE",
        "15-25%",
        "neighbors",
        "coordinate",
        "flexible timing"
    ]
    
    for rule in business_rules:
        count = full_system_prompt.lower().count(rule.lower())
        print(f"'{rule}' mentioned: {count} times")

if __name__ == "__main__":
    asyncio.run(debug_full_context())