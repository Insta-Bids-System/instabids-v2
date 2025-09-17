#!/usr/bin/env python3
"""
Debug script to see EXACTLY what content is being fed to the AI
"""
import asyncio
import os
import sys
sys.path.append('/ai-agents')

from agents.coia.tools import COIATools

async def debug_ai_content():
    print("DEBUGGING: What content does the AI actually receive?")
    
    # Initialize COIA tools
    coia = COIATools()
    
    # Test with TurfGrass
    company_name = "TurfGrass Artificial Solutions"
    
    print(f"\n1. Testing web search for: {company_name}")
    
    # Call the actual web search
    result = await coia.web_search_company(company_name, "South Florida")
    
    print(f"\n2. RESULT KEYS: {list(result.keys())}")
    print(f"\n3. WEBSITE DATA KEYS: {list(result.get('website_data', {}).keys())}")
    
    # Show what the AI actually processed
    if 'website_data' in result:
        website_data = result['website_data']
        
        print(f"\n4. CONTENT SUMMARY:")
        print(f"   - Raw content length: {website_data.get('raw_content_length', 0)} characters")
        print(f"   - Content sources: {website_data.get('content_sources', [])}")
        print(f"   - Extraction method: {website_data.get('extraction_method', 'unknown')}")
        
        # Show if phone/email were found
        print(f"\n5. CONTACT INFO EXTRACTED:")
        print(f"   - Phone: {website_data.get('phone', 'NOT FOUND')}")
        print(f"   - Email: {website_data.get('email', 'NOT FOUND')}")
        
        # Show contact_methods if present
        if 'contact_methods' in website_data:
            contact_methods = website_data['contact_methods']
            print(f"   - Contact methods: {contact_methods}")
        
        print(f"\n6. BUSINESS DATA EXTRACTED:")
        print(f"   - Services: {len(website_data.get('services', []))} found")
        print(f"   - Years in business: {website_data.get('years_in_business', 'NOT FOUND')}")
        print(f"   - Service areas: {len(website_data.get('service_areas', []))} found")
    
    # THE CRITICAL CHECK: What's in extracted_info vs website_data?
    if 'extracted_info' in result:
        extracted_info = result['extracted_info']
        print(f"\n7. EXTRACTED_INFO (what goes to database):")
        print(f"   - Phone: {extracted_info.get('phone', 'NOT FOUND')}")
        print(f"   - Email: {extracted_info.get('email', 'NOT FOUND')}")
        print(f"   - Description: {extracted_info.get('description', 'NOT FOUND')}")
        print(f"   - Years in business: {extracted_info.get('years_in_business', 'NOT FOUND')}")
    
    print(f"\n8. THE MAPPING ISSUE:")
    print("   website_data has the phone/email from AI")
    print("   extracted_info is what gets saved to database")
    print("   The mapping between them is the problem!")

if __name__ == "__main__":
    asyncio.run(debug_ai_content())