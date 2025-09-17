#!/usr/bin/env python3
"""
SUPER SIMPLE LLM CONTRACTOR SIZING
Just dump all the data and let the LLM figure it out
"""

def create_super_simple_prompt(all_data: str) -> str:
    """
    The simplest possible prompt - just give everything to the LLM
    """
    
    prompt = f"""
{all_data}

Categorize this contractor:
1=solo, 2=owner_operator(2-5 people), 3=small_business(6-20), 4=regional(20-100), 5=enterprise(100+)

Return: size_number, reasoning (one sentence)
"""
    
    return prompt


def create_minimal_prompt_with_structure(company_name: str, google_data: str, website_content: str) -> str:
    """
    Minimal but structured prompt
    """
    
    prompt = f"""
Company: {company_name}
Google: {google_data}
Website: {website_content}

Size? 1=solo, 2=owner(2-5), 3=small(6-20), 4=regional(20-100), 5=enterprise(100+)
"""
    
    return prompt


def show_examples():
    """Show real examples with minimal prompts"""
    
    print("=" * 80)
    print("SUPER SIMPLE LLM SIZING PROMPTS")
    print("=" * 80)
    
    # Example 1: JM Holiday Lighting (REAL DATA)
    print("\n[EXAMPLE 1: JM Holiday Lighting - REAL DATA]")
    print("-" * 60)
    
    all_data = """
JM Holiday Lighting Inc
5051 NW 13th Ave, Pompano Beach FL
Google: 5 stars on Yelp, 162 Facebook likes
Website says: "Florida's premier installer", "all of South Florida", warehouse facility, commercial focus, multiple crews, 48-hour service guarantee
"""
    
    prompt = create_super_simple_prompt(all_data)
    print("PROMPT TO LLM:")
    print(prompt)
    
    print("\nEXPECTED LLM RESPONSE:")
    print("size_number: 3")
    print("reasoning: Warehouse facility, regional coverage, and 'premier installer' positioning indicates established small business.")
    
    # Example 2: Even simpler
    print("\n\n[EXAMPLE 2: ABSOLUTE MINIMAL]")
    print("-" * 60)
    
    prompt2 = """
Reindeer Bros - nationwide service, commercial LED, $1500 minimum
Size? 1=solo 2=small_team 3=small_biz 4=regional 5=national
"""
    
    print("PROMPT TO LLM:")
    print(prompt2)
    
    print("\nEXPECTED LLM RESPONSE:")
    print("4 - nationwide service and high minimums indicate regional/national company")
    
    # Example 3: Just paste everything
    print("\n\n[EXAMPLE 3: JUST DUMP EVERYTHING]")
    print("-" * 60)
    
    prompt3 = """
Mike's Christmas Lights (954)555-3333 Deerfield Beach 42 reviews 4.6 stars no website
What size? 1-5
"""
    
    print("PROMPT TO LLM:")
    print(prompt3)
    
    print("\nEXPECTED LLM RESPONSE:")
    print("2 - personal name and moderate reviews suggest owner-operator")
    
    # Show implementation
    print("\n\n" + "=" * 80)
    print("ACTUAL IMPLEMENTATION")
    print("=" * 80)
    
    print("""
async def size_contractor(company_data):
    # Step 1: Scrape everything you can find
    google_info = await get_google_data(company_data['name'])
    website_text = await scrape_website(company_data['website']) if company_data.get('website') else ""
    
    # Step 2: Dump it all into one string
    all_data = f'''
    {company_data['name']}
    {company_data.get('address', '')}
    Google: {google_info}
    Website: {website_text[:1000]}  # First 1000 chars
    '''
    
    # Step 3: Ask LLM
    prompt = f'''
    {all_data}
    
    Size? 1=solo 2=owner(2-5) 3=small(6-20) 4=regional(20-100) 5=enterprise(100+)
    '''
    
    response = await llm(prompt)
    return response
""")
    
    print("\n" + "=" * 80)
    print("THAT'S IT! SUPER SIMPLE!")
    print("=" * 80)
    print("""
Benefits:
- Under 10 lines of prompt
- LLM figures out what's important
- No complex rules to maintain
- Works with partial data
- Handles any language on website ("family-owned", "nationwide", etc.)
""")


if __name__ == "__main__":
    show_examples()