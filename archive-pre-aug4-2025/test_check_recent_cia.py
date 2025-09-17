#!/usr/bin/env python3
"""
Check recent CIA conversations
"""
import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Initialize Supabase client
supabase_url = "https://xrhgrthdcaymxuqcgrmj.supabase.co"
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_key:
    print("ERROR: Missing SUPABASE_SERVICE_ROLE_KEY")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

print("Checking recent CIA conversations...")

try:
    # Get recent CIA conversations (last 24 hours)
    one_day_ago = (datetime.now() - timedelta(days=1)).isoformat()
    
    response = supabase.table("agent_conversations").select("*").eq(
        "agent_type", "CIA"
    ).gte("created_at", one_day_ago).order("created_at", desc=True).execute()
    
    if response.data:
        print(f"\nFound {len(response.data)} CIA conversations in last 24 hours:")
        for conv in response.data[:5]:  # Show first 5
            print(f"\n  Thread: {conv.get('thread_id')}")
            print(f"  User: {conv.get('user_id')}")
            print(f"  Created: {conv.get('created_at')}")
            
            # Check if it has actual messages
            state_str = conv.get('state', '{}')
            if state_str:
                import json
                try:
                    state = json.loads(state_str)
                    messages = state.get('messages', [])
                    print(f"  Messages: {len(messages)}")
                    if messages:
                        print(f"  First message: {messages[0].get('content', '')[:50]}...")
                except:
                    print("  Messages: ERROR parsing state")
    else:
        print("No CIA conversations found in last 24 hours")
        
    # Check for our test sessions specifically
    print("\n\nChecking for our test sessions...")
    test_patterns = ["real_test_session%", "session_test%", "test_session%"]
    
    for pattern in test_patterns:
        response = supabase.table("agent_conversations").select("*").eq(
            "agent_type", "CIA"
        ).ilike("thread_id", pattern).execute()
        
        if response.data:
            print(f"\nFound {len(response.data)} sessions matching '{pattern}':")
            for conv in response.data[:3]:
                print(f"  - {conv.get('thread_id')}: {conv.get('created_at')}")
                
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    print(traceback.format_exc())