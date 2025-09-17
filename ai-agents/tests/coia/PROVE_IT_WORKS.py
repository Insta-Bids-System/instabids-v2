"""
PROVE THE SYSTEM ACTUALLY WORKS - NO BULLSHIT
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)

print("="*60)
print("PROVING COIA SYSTEM ACTUALLY WORKS")
print("="*60)

# 1. Test Tavily directly
print("\n1. TESTING TAVILY DIRECTLY:")
try:
    from tavily import TavilyClient
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    result = client.search("TurfGrass Artificial Solutions South Florida", max_results=1, include_raw_content=True)
    
    if result and result.get('results'):
        page = result['results'][0]
        print(f"[OK] FOUND: {page['title']}")
        print(f"[OK] URL: {page['url']}")
        print(f"[OK] CONTENT: {len(page.get('content', ''))} chars")
        print(f"[OK] RAW CONTENT: {len(page.get('raw_content', ''))} chars")
        
        # Extract phone/email from raw content
        raw = page.get('raw_content', '') or page.get('content', '')
        
        import re
        phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', raw)
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', raw)
        
        print(f"[OK] PHONES FOUND: {phones}")
        print(f"[OK] EMAILS FOUND: {emails}")
        
    else:
        print("[FAIL] NO RESULTS")
        
except Exception as e:
    print(f"[ERROR] TAVILY ERROR: {e}")

# 2. Test OpenAI directly  
print("\n2. TESTING OPENAI DIRECTLY:")
try:
    import openai
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Extract company info: TurfGrass Artificial Solutions is a South Florida artificial turf installer. Phone: (954) 555-1234. Email: info@turfgrass.com"}],
        max_tokens=100
    )
    
    print(f"[OK] OPENAI WORKS: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"[ERROR] OPENAI ERROR: {e}")

print("\n" + "="*60)
print("IF BOTH WORK, THE COIA SYSTEM SHOULD WORK")
print("="*60)