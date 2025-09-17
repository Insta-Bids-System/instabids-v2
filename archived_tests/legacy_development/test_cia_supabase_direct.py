#!/usr/bin/env python3
"""Test CIA agent Supabase connection directly"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load from root .env
root_env = Path(__file__).parent / '.env'
print(f"Loading from: {root_env}")
print(f"File exists: {root_env.exists()}")

if root_env.exists():
    load_dotenv(root_env, override=True)

# Test the CIA agent initialization
try:
    # Import CIA agent
    import sys
    sys.path.append('ai-agents')
    
    from agents.cia.agent import CustomerInterfaceAgent
    
    # Get OpenAI key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("[FAILED] No OpenAI API key found")
        exit(1)
    
    print(f"OpenAI key: {openai_key[:20]}...")
    
    # Initialize CIA agent
    print("Initializing CIA agent...")
    cia = CustomerInterfaceAgent(openai_key)
    
    print("[SUCCESS] CIA agent initialized without errors!")
    
    # Test Supabase connection directly
    print("\nTesting Supabase connection from CIA agent...")
    try:
        result = cia.supabase.table("bid_cards").select("id").limit(1).execute()
        print(f"[SUCCESS] Supabase connection working from CIA agent!")
        print(f"Test query returned: {len(result.data)} records")
    except Exception as e:
        print(f"[FAILED] Supabase connection error: {e}")
        
except Exception as e:
    print(f"[FAILED] CIA agent initialization error: {e}")
    import traceback
    traceback.print_exc()