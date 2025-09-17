"""
DEBUG WHAT KEYS ARE ACTUALLY BEING LOADED
"""
import os
from pathlib import Path
from dotenv import load_dotenv

print("="*60)
print("DEBUGGING API KEY LOADING")
print("="*60)

# Check environment first
print("1. ENVIRONMENT VARIABLES:")
print(f"   OPENAI_API_KEY from env: {os.getenv('OPENAI_API_KEY', 'NOT SET')}")
print(f"   TAVILY_API_KEY from env: {os.getenv('TAVILY_API_KEY', 'NOT SET')}")

# Load .env file
env_path = Path(__file__).parent.parent.parent.parent / '.env'
print(f"\n2. LOADING FROM: {env_path}")
print(f"   File exists: {env_path.exists()}")

if env_path.exists():
    load_dotenv(env_path)
    print("\n3. AFTER LOADING .ENV:")
    openai_key = os.getenv('OPENAI_API_KEY')
    tavily_key = os.getenv('TAVILY_API_KEY')
    
    print(f"   OPENAI_API_KEY: {openai_key[:20] if openai_key else 'NOT SET'}... (len: {len(openai_key) if openai_key else 0})")
    print(f"   TAVILY_API_KEY: {tavily_key[:20] if tavily_key else 'NOT SET'}... (len: {len(tavily_key) if tavily_key else 0})")
    
    # Manual file read
    print("\n4. MANUAL FILE READ:")
    with open(env_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if 'OPENAI_API_KEY=' in line:
                key_from_file = line.split('=', 1)[1].strip()
                print(f"   Line {line_num}: {key_from_file[:20]}... (len: {len(key_from_file)})")
            elif 'TAVILY_API_KEY=' in line:
                key_from_file = line.split('=', 1)[1].strip()
                print(f"   Line {line_num}: {key_from_file[:20]}... (len: {len(key_from_file)})")

# Test the COIA tools loading
print("\n5. COIA TOOLS LOADING:")
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from agents.coia.tools import COIATools
    tools = COIATools()
    print(f"   Tools loaded successfully")
except Exception as e:
    print(f"   ERROR: {e}")