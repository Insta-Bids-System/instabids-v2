#!/usr/bin/env python3
"""
Check agent types in database
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Initialize Supabase client
supabase_url = "https://xrhgrthdcaymxuqcgrmj.supabase.co"
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_key:
    print("ERROR: Missing SUPABASE_SERVICE_ROLE_KEY")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

print("Checking agent types in database...")

try:
    # Get all unique agent types
    response = supabase.table("agent_conversations").select("agent_type").execute()
    
    if response.data:
        agent_types = set(conv.get('agent_type', 'N/A') for conv in response.data)
        print(f"\nFound {len(agent_types)} unique agent types:")
        for agent_type in sorted(agent_types):
            print(f"  - '{agent_type}'")
            
        # Count by agent type
        print("\nCount by agent type:")
        for agent_type in sorted(agent_types):
            count_response = supabase.table("agent_conversations").select("*", count="exact").eq("agent_type", agent_type).execute()
            print(f"  - '{agent_type}': {count_response.count}")
            
    else:
        print("No conversations found")
        
except Exception as e:
    print(f"ERROR: {e}")

# Also check for CIA specifically (case variations)
print("\nChecking for CIA variations:")
for variation in ["CIA", "cia", "Cia"]:
    try:
        response = supabase.table("agent_conversations").select("*", count="exact").eq("agent_type", variation).execute()
        print(f"  - '{variation}': {response.count}")
    except:
        print(f"  - '{variation}': ERROR")