"""
FINAL TEST - COMPLETE WORKING COIA EXTRACTION
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load .env manually
env_path = Path(__file__).parent.parent.parent.parent / '.env'

openai_key = None
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                openai_key = line.split('=', 1)[1].strip()
                break

print("="*60)
print("FINAL WORKING COIA TEST")
print("="*60)

print(f"OpenAI key loaded: {bool(openai_key)}")
if openai_key:
    print(f"Key length: {len(openai_key)}")

# Set the environment variable
if openai_key:
    os.environ['OPENAI_API_KEY'] = openai_key

async def test_complete_extraction():
    """Test complete extraction with correct API key"""
    
    from agents.coia.tools import COIATools
    tools = COIATools()
    
    # Test extraction
    company_name = "TurfGrass Artificial Solutions"
    
    print(f"\nTesting complete extraction for: {company_name}")
    
    # Run complete web search
    result = await tools.web_search_company(company_name)
    
    print("\nFINAL RESULTS:")
    print("-" * 40)
    
    if result:
        # Check key fields
        fields = ['company_name', 'phone', 'email', 'services', 'years_in_business', 'extraction_method']
        
        for field in fields:
            value = result.get(field, 'MISSING')
            if value and value != 'MISSING':
                if isinstance(value, list):
                    print(f"{field}: {len(value)} items - {value[:2]}")
                else:
                    print(f"{field}: {value}")
            else:
                print(f"{field}: [MISSING]")
    else:
        print("NO RESULTS")

if __name__ == "__main__":
    asyncio.run(test_complete_extraction())