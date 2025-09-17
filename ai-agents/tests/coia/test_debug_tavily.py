"""
Direct test to see if Tavily is even working
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load .env file
env_path = Path(__file__).parent.parent.parent.parent / '.env'
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")

# Check if Tavily API key is loaded
tavily_key = os.getenv("TAVILY_API_KEY")
print(f"TAVILY_API_KEY loaded: {bool(tavily_key)}")
if tavily_key:
    print(f"Key length: {len(tavily_key)}, starts with: {tavily_key[:10]}")

# Try to use Tavily directly
try:
    from tavily import TavilyClient
    print("Tavily library imported successfully")
    
    if tavily_key:
        client = TavilyClient(api_key=tavily_key)
        print("Tavily client created")
        
        # Do a real search
        print("\nSearching for: TurfGrass Artificial Solutions South Florida")
        result = client.search("TurfGrass Artificial Solutions South Florida", max_results=3)
        
        if result and result.get('results'):
            print(f"Found {len(result['results'])} results:")
            for i, item in enumerate(result['results'], 1):
                print(f"\n{i}. {item.get('title', 'No title')}")
                print(f"   URL: {item.get('url', 'No URL')}")
                print(f"   Content: {item.get('content', 'No content')[:200]}...")
        else:
            print("No results found")
    else:
        print("Cannot test - no API key")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()