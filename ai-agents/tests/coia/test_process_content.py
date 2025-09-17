"""
Test _process_tavily_content directly
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.coia.tools import COIATools

async def test_process_content():
    """Test the complete chain"""
    print("Testing complete extraction chain...")
    
    # Initialize tools
    tools = COIATools()
    
    # Test with the actual website we found
    company_name = "TurfGrass Artificial Solutions"
    website_url = "https://www.southfloridaturfsolutions.com/about"
    location = "South Florida"
    
    print(f"Company: {company_name}")
    print(f"Website: {website_url}")
    
    try:
        # Step 1: Get discovery data
        print("\n1. Getting Tavily discovery data...")
        tavily_data = await tools._tavily_discover_contractor_pages(company_name, website_url, location)
        print(f"   Found {len(tavily_data.get('discovered_pages', []))} pages")
        
        # Step 2: Process the content
        print("\n2. Processing Tavily content...")
        all_page_data = await tools._process_tavily_content(tavily_data, company_name)
        
        print("\nPROCESSED CONTENT RESULTS:")
        print("=" * 50)
        
        if all_page_data:
            for key, value in all_page_data.items():
                if isinstance(value, list):
                    print(f"{key}: {len(value)} items")
                    for item in value[:3]:  # Show first 3
                        print(f"  - {item}")
                else:
                    print(f"{key}: {value}")
        else:
            print("NO PROCESSED DATA RETURNED")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_process_content())