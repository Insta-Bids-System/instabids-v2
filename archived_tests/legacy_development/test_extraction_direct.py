#!/usr/bin/env python3
"""
Test GPT-5 extraction directly without streaming complexity.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gpt5_extraction():
    """Test GPT-5 extraction directly."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] No OpenAI API key found in environment")
        return
    
    print(f"[INFO] Using API key: {api_key[:20]}...")
    
    client = OpenAI(api_key=api_key)
    
    # Test message with lots of extractable info
    test_message = """
    I need someone to install a new deck in my backyard. We're thinking about a 
    20x15 foot composite deck. My budget is around $15,000 to $20,000. 
    We want it done before summer, maybe in April. The address is 123 Maple Street 
    in Austin, Texas 78701. My name is John Smith. My email is john.smith@example.com 
    and phone is 555-123-4567. We also want built-in lighting and maybe a pergola on one side.
    """
    
    extraction_prompt = f"""
    Extract the following information from this message:
    - project_type (what work needs to be done)
    - location_address (full address if provided)
    - budget_min and budget_max (as numbers)
    - timeline_start (when they want work to begin)
    - contact_name
    - contact_email
    - contact_phone
    - project_details (specific requirements)
    - urgency_level (emergency/urgent/standard/flexible)
    
    Message: {test_message}
    
    Return ONLY a JSON object with the extracted fields. If a field is not found, omit it.
    """
    
    print("[INFO] Calling GPT-4o for extraction...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Using GPT-4o which should work
            messages=[
                {"role": "system", "content": "You are an information extraction assistant. Extract data from messages and return JSON."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        result = response.choices[0].message.content
        print("[SUCCESS] Got response from GPT-4o")
        print("\nRaw response:")
        print(result)
        
        # Try to parse as JSON
        try:
            # Clean up response if needed
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()
            
            extracted = json.loads(result)
            print("\nParsed extraction:")
            print(json.dumps(extracted, indent=2))
            
            # Check extraction quality
            expected_fields = [
                "project_type", "location_address", "budget_min", "budget_max",
                "timeline_start", "contact_name", "contact_email", "contact_phone"
            ]
            
            found = sum(1 for field in expected_fields if field in extracted)
            print(f"\n[STATS] Extracted {found}/{len(expected_fields)} expected fields")
            
            if found >= 6:
                print("[SUCCESS] GPT-4o extraction is working well!")
            else:
                print("[WARNING] Extraction needs improvement")
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Could not parse JSON: {e}")
            
    except Exception as e:
        print(f"[ERROR] GPT call failed: {e}")
        if "Invalid API key" in str(e):
            print("[ERROR] API key is invalid")
        elif "timeout" in str(e).lower():
            print("[ERROR] Request timed out")

if __name__ == "__main__":
    print("Testing Direct GPT-4o Extraction...")
    print("=" * 60)
    test_gpt5_extraction()