#!/usr/bin/env python3
"""
Check the state format in database
"""
import os
from dotenv import load_dotenv
from supabase import create_client
import json

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Initialize Supabase client
supabase_url = "https://xrhgrthdcaymxuqcgrmj.supabase.co"
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(supabase_url, supabase_key)

# Get the most recent CIA conversation
response = supabase.table("agent_conversations").select("*").eq(
    "agent_type", "CIA"
).order("created_at", desc=True).limit(1).execute()

if response.data:
    conv = response.data[0]
    print(f"Thread ID: {conv.get('thread_id')}")
    print(f"Created: {conv.get('created_at')}")
    
    # Get the state field
    state_field = conv.get('state')
    print(f"\nState field type: {type(state_field)}")
    
    if isinstance(state_field, str):
        print("State is a string, length:", len(state_field))
        print("First 200 chars:", state_field[:200])
        
        # Try to parse it
        try:
            state_obj = json.loads(state_field)
            print("\nParsed successfully!")
            print(f"State keys: {list(state_obj.keys())}")
            
            # Check messages
            if 'messages' in state_obj:
                messages = state_obj['messages']
                print(f"\nMessages: {len(messages)}")
                for i, msg in enumerate(messages[:2]):
                    print(f"  Message {i+1}: {msg.get('role')} - {msg.get('content', '')[:50]}...")
            else:
                print("\nNo 'messages' key in state")
                
        except json.JSONDecodeError as e:
            print(f"\nJSON Parse Error: {e}")
            print("Looking for the error location...")
            
            # Try to find the issue
            if '"conversation_data":' in state_field:
                print("Found nested conversation_data - this might be double-encoded")
                
    elif isinstance(state_field, dict):
        print("State is already a dict!")
        print(f"Keys: {list(state_field.keys())}")
else:
    print("No CIA conversations found")