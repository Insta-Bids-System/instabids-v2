#!/usr/bin/env python3
"""Test database_simple import and connection"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load from root .env
root_env = Path(__file__).parent / '.env'
if root_env.exists():
    load_dotenv(root_env, override=True)

try:
    # Test import path
    import sys
    sys.path.append('ai-agents')
    
    print("Testing database_simple import...")
    from database_simple import db
    print("[SUCCESS] database_simple imported successfully!")
    
    # Test database connection
    print("Testing database connection...")
    result = db.client.table("bid_cards").select("id").limit(1).execute()
    print(f"[SUCCESS] Database connection working!")
    print(f"Test query returned: {len(result.data)} records")
    
    # Test the get_or_create_test_user function
    print("\nTesting get_or_create_test_user...")
    import asyncio
    user_id = asyncio.run(db.get_or_create_test_user())
    print(f"[SUCCESS] Test user: {user_id}")
    
except Exception as e:
    print(f"[FAILED] Database error: {e}")
    import traceback
    traceback.print_exc()