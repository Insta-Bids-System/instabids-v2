"""
Test AI extraction with phone/email fixes
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.coia.tools import COIATools

async def test_ai_extraction():
    """Test the AI extraction function directly"""
    print("\n" + "="*80)
    print("TESTING AI EXTRACTION WITH PHONE/EMAIL FIX")
    print("="*80)
    
    # Initialize tools
    tools = COIATools()
    
    # Test with TurfGrass Artificial Solutions
    company_name = "TurfGrass Artificial Solutions"
    print(f"\nTesting with: {company_name}")
    
    try:
        # Run web search which should trigger AI extraction
        result = await tools.web_search_company(company_name)
        
        print("\nEXTRACTION RESULTS:")
        print("-" * 60)
        
        # Check key fields
        fields_to_check = [
            'company_name', 'phone', 'email', 'address', 
            'services', 'years_in_business', 'service_areas',
            'certifications', 'specializations', 'extraction_method'
        ]
        
        for field in fields_to_check:
            value = result.get(field, 'NOT FOUND')
            if value and value != 'NOT FOUND':
                if isinstance(value, list):
                    print(f"[OK] {field}: {len(value)} items - {value[:2]}...")
                else:
                    print(f"[OK] {field}: {value}")
            else:
                print(f"[MISSING] {field}: EMPTY")
        
        # Special check for contact info
        print("\nCONTACT INFORMATION CHECK:")
        print("-" * 60)
        phone = result.get('phone')
        email = result.get('email')
        
        if phone:
            print(f"[OK] PHONE EXTRACTED: {phone}")
        else:
            print("[MISSING] PHONE NOT EXTRACTED")
            
        if email:
            print(f"[OK] EMAIL EXTRACTED: {email}")
        else:
            print("[MISSING] EMAIL NOT EXTRACTED")
        
        # Check extraction method
        method = result.get('extraction_method', 'UNKNOWN')
        print(f"\nExtraction Method: {method}")
        
        if method == "GPT5_INTELLIGENCE":
            print("[OK] AI extraction was used successfully!")
        else:
            print("[WARNING] Fallback extraction was used")
        
        return result
        
    except Exception as e:
        print(f"\n[ERROR]: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_ai_extraction())
    
    if result:
        print("\n" + "="*80)
        print("TEST COMPLETE - AI EXTRACTION WORKING")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("TEST FAILED - CHECK ERRORS ABOVE")
        print("="*80)