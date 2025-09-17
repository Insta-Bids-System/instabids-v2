"""
FORCE WORKING TEST - MANUALLY SET THE CORRECT API KEY
"""
import os

# Load API keys from environment
from dotenv import load_dotenv
load_dotenv()

if not os.getenv('OPENAI_API_KEY'):
    print("Error: OPENAI_API_KEY not set in environment")
    exit(1)

print("FORCED API KEYS SET")
print(f"OpenAI key length: {len(os.environ['OPENAI_API_KEY'])}")
print(f"Tavily key length: {len(os.environ['TAVILY_API_KEY'])}")

# Test OpenAI directly
try:
    import openai
    client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Extract phone and email from: TurfGrass Solutions contact us at (954) 123-4567 or email@turfgrass.com"}],
        max_tokens=100
    )
    
    print("OPENAI SUCCESS:")
    print(response.choices[0].message.content)
    
except Exception as e:
    print(f"OPENAI FAILED: {e}")

# Test Tavily directly  
try:
    from tavily import TavilyClient
    client = TavilyClient(api_key=os.environ['TAVILY_API_KEY'])
    
    result = client.search("TurfGrass Artificial Solutions contact", max_results=1, include_raw_content=True)
    
    if result and result.get('results'):
        page = result['results'][0]
        print("TAVILY SUCCESS:")
        print(f"Title: {page['title']}")
        print(f"URL: {page['url']}")
        
        # Look for contact info
        content = page.get('raw_content', '') or page.get('content', '')
        print(f"Content length: {len(content)}")
        
        import re
        phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', content)
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        
        print(f"PHONES: {phones}")
        print(f"EMAILS: {emails}")
        
    else:
        print("TAVILY NO RESULTS")
        
except Exception as e:
    print(f"TAVILY FAILED: {e}")

print("\nIF BOTH WORK, COIA SHOULD WORK")