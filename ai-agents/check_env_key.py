import os
from dotenv import load_dotenv

# Load env
load_dotenv()

# Read from env file directly
with open('.env', 'r') as f:
    for line in f:
        if line.startswith('OPENAI_API_KEY='):
            file_key = line.strip().split('=', 1)[1]
            print(f"Key from .env file: ...{file_key[-10:]}")
            break

# Get from environment
env_key = os.getenv("OPENAI_API_KEY")
if env_key:
    print(f"Key from os.getenv: ...{env_key[-10:]}")
else:
    print("No OPENAI_API_KEY in environment")

# Check if they match
if env_key and file_key:
    if env_key == file_key:
        print("Keys match!")
    else:
        print("Keys DO NOT match!")