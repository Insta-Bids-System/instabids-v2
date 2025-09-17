"""
Test the search_google_business directly
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.coia.tools import COIATools

async def test_direct_search():
    """Test search_google_business directly"""
    print("Testing search_google_business directly...")
    
    # Initialize tools
    tools = COIATools()
    
    # Test with TurfGrass Artificial Solutions
    company_name = "TurfGrass Artificial Solutions"
    location = "South Florida"
    
    print(f"Searching for: {company_name} in {location}")
    
    # Call search_google_business directly
    result = await tools.search_google_business(company_name, location)
    
    print("\nDIRECT SEARCH RESULTS:")
    print("=" * 50)
    
    if result:
        for key, value in result.items():
            print(f"{key}: {value}")
    else:
        print("NO RESULTS RETURNED")

if __name__ == "__main__":
    asyncio.run(test_direct_search())