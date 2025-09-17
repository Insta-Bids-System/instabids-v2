#!/usr/bin/env python3
"""
Debug environment variable loading
"""

import os
from dotenv import load_dotenv

def debug_env_loading():
    print("Environment Variable Loading Debug")
    print("=" * 50)
    
    # Show current working directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Check for .env files in different locations
    locations = [
        # Current directory
        ".env",
        # Parent directory (base)
        "../.env", 
        # Absolute path to base
        os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    ]
    
    for i, location in enumerate(locations, 1):
        abs_path = os.path.abspath(location)
        exists = os.path.exists(abs_path)
        print(f"{i}. {location} -> {abs_path}")
        print(f"   Exists: {exists}")
        
        if exists:
            print(f"   Loading from: {abs_path}")
            # Clear existing env vars first
            if 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
            load_dotenv(abs_path)
            key = os.getenv('OPENAI_API_KEY')
            if key:
                print(f"   OPENAI_API_KEY: {key[:20]}...")
            else:
                print("   OPENAI_API_KEY: Not found")
        print()
    
    print("Final environment check:")
    final_key = os.getenv('OPENAI_API_KEY')
    if final_key:
        print(f"OPENAI_API_KEY: {final_key[:20]}...")
    else:
        print("OPENAI_API_KEY: Not set")

if __name__ == "__main__":
    debug_env_loading()