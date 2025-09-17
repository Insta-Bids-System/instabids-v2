"""
Test _tavily_discover_contractor_pages directly
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.coia.tools import COIATools

async def test_tavily_discovery():
    """Test _tavily_discover_contractor_pages directly"""
    print("Testing _tavily_discover_contractor_pages...")
    
    # Initialize tools
    tools = COIATools()
    
    # Test with the actual website we found
    company_name = "TurfGrass Artificial Solutions"
    website_url = "https://www.southfloridaturfsolutions.com/about"
    location = "South Florida"
    
    print(f"Company: {company_name}")
    print(f"Website: {website_url}")
    print(f"Location: {location}")
    
    try:
        # Call the failing function directly
        result = await tools._tavily_discover_contractor_pages(company_name, website_url, location)
        
        print("\nTAVILY DISCOVERY RESULTS:")
        print("=" * 50)
        
        if result:
            for key, value in result.items():
                if isinstance(value, list):
                    print(f"{key}: {len(value)} items")
                    for i, item in enumerate(value[:2], 1):  # Show first 2
                        print(f"  {i}. {str(item)[:100]}...")
                else:
                    print(f"{key}: {value}")
        else:
            print("NO RESULTS RETURNED")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tavily_discovery())