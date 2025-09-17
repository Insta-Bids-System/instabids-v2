#!/usr/bin/env python3
"""
Create Supabase Storage buckets for InstaBids image storage
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Try both .env locations
if not os.getenv('SUPABASE_URL'):
    load_dotenv(Path(__file__).parent / '.env')

from supabase import create_client

def create_buckets():
    """Create storage buckets in Supabase"""
    
    # Get credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print(f"ERROR: Missing credentials")
        print(f"SUPABASE_URL: {'Set' if url else 'Not set'}")
        print(f"SUPABASE_SERVICE_ROLE_KEY: {'Set' if key else 'Not set'}")
        print(f"Checked .env at: {env_path}")
        return False
    
    print(f"Creating buckets for project: {url}")
    
    # Create client with service role key for admin access
    client = create_client(url, key)
    
    # Define buckets to create
    buckets = [
        {'name': 'property-photos', 'public': True},
        {'name': 'inspiration-images', 'public': True},
        {'name': 'bid-card-images', 'public': True}
    ]
    
    created = 0
    for bucket_config in buckets:
        bucket_name = bucket_config['name']
        try:
            # Try to list files in bucket (will fail if doesn't exist)
            client.storage.from_(bucket_name).list()
            print(f"[EXISTS] Bucket '{bucket_name}' already exists")
        except:
            try:
                # Create bucket
                result = client.storage.create_bucket(
                    bucket_name,
                    {'public': bucket_config['public']}
                )
                print(f"[CREATED] Bucket '{bucket_name}' created successfully")
                created += 1
            except Exception as e:
                if "already exists" in str(e):
                    print(f"[EXISTS] Bucket '{bucket_name}' already exists")
                else:
                    print(f"[ERROR] Failed to create bucket '{bucket_name}': {e}")
                    return False
    
    print(f"\nSummary: {created} new buckets created, {len(buckets) - created} already existed")
    print("All required buckets are now available!")
    return True

if __name__ == "__main__":
    success = create_buckets()
    sys.exit(0 if success else 1)