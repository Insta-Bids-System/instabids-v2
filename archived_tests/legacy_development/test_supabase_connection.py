#!/usr/bin/env python3
"""Test Supabase connection with root .env"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load from root .env
root_env = Path(__file__).parent / '.env'
print(f"Loading from: {root_env}")
print(f"File exists: {root_env.exists()}")

if root_env.exists():
    load_dotenv(root_env, override=True)

# Get credentials
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

print(f"\nSUPABASE_URL: {url}")
print(f"SUPABASE_ANON_KEY: {key[:20]}...{key[-10:] if key else 'None'}")

# Test connection
try:
    client = create_client(url, key)
    # Simple test query
    result = client.table("bid_cards").select("id").limit(1).execute()
    print(f"\n[SUCCESS] Connection working!")
    print(f"Test query returned: {len(result.data)} records")
except Exception as e:
    print(f"\n[FAILED] {e}")
    
# Also check OpenAI key
openai_key = os.getenv("OPENAI_API_KEY")
print(f"\nOPENAI_API_KEY: {openai_key[:20] if openai_key else 'Not found'}...")