#!/usr/bin/env python3
"""
LLM-BASED CONTRACTOR SIZING
Let the LLM make the decision with all available data
"""
import json
from typing import Dict, Any

def create_llm_sizing_prompt(contractor: Dict[str, Any], website_data: Dict[str, Any]) -> str:
    """
    Create a comprehensive prompt for LLM to categorize contractor size
    """
    
    prompt = f"""You are an expert at analyzing contractor business size. Categorize this contractor based on ALL available data.

CONTRACTOR INFORMATION:
Company Name: {contractor.get('company_name', 'Unknown')}
Website: {contractor.get('website', 'No website')}
Phone: {contractor.get('phone', 'Not provided')}
Location: {contractor.get('city', '')}, {contractor.get('state', '')}
Google Reviews: {contractor.get('google_review_count', 0)} reviews
Google Rating: {contractor.get('google_rating', 'N/A')} stars

WEBSITE DATA EXTRACTED:
{json.dumps(website_data, indent=2) if website_data else 'No website data available'}

WEBSITE TEXT SNIPPETS (if available):
{website_data.get('content_preview', 'No content available')}

SIZE CATEGORIES (choose one):
- solo_handyman: 1 person operation, works alone, no employees
- owner_operator: 2-5 person team, owner works on jobs with small crew
- small_business: 6-20 employees, established business with office/warehouse
- regional_company: 20-100 employees, multiple locations or large service area
- enterprise: 100+ employees, corporation with multiple divisions

IMPORTANT SIZING GUIDELINES:
1. Prioritize website data over review counts
2. "Team" or "employees" mentioned = at least owner_operator
3. Fleet/warehouse/facility = likely small_business or larger
4. National/statewide service = regional_company or larger
5. High minimum prices ($1,500+) = established business
6. Years in business matters (10+ years = more established)
7. Commercial focus = typically larger operation
8. Inc/LLC alone doesn't mean large (many solo operators incorporate)

Analyze all data and provide:
1. size_category: Your chosen category
2. confidence: 0-100 score
3. key_factors: List the most important data points that influenced your decision
4. reasoning: Brief explanation of your logic

Return as JSON."""
    
    return prompt


def create_simple_llm_prompt(contractor_data: str) -> str:
    """
    Even simpler version - just paste everything and let LLM figure it out
    """
    
    prompt = f"""Categorize this contractor's business size:

{contractor_data}

Categories:
- solo_handyman (1 person)
- owner_operator (2-5 people)
- small_business (6-20 people)
- regional_company (20-100 people)
- enterprise (100+ people)

Look for: team size, employees, fleet, warehouse, years in business, service area, commercial focus.
If website mentions "team" or "employees" -> at least owner_operator.
If national/statewide service -> at least regional_company.

Return JSON with: size_category, confidence, reasoning"""
    
    return prompt


def show_real_examples():
    """Show how this would work with real contractors"""
    
    print("=" * 80)
    print("LLM-BASED CONTRACTOR SIZING EXAMPLES")
    print("=" * 80)
    
    # Example 1: JM Holiday Lighting
    print("\n[EXAMPLE 1: JM Holiday Lighting Inc]")
    print("-" * 60)
    
    contractor = {
        "company_name": "JM Holiday Lighting Inc",
        "website": "https://jmholidaylighting.com/",
        "phone": "(954) 482-6800",
        "city": "Pompano Beach",
        "state": "FL",
        "google_review_count": 0,  # Not available
        "google_rating": None
    }
    
    website_data = {
        "enrichment_complete": True,
        "content_length": 9442,
        "team_size": None,  # Couldn't extract specific number
        "years_in_business": None,  # Couldn't extract
        "service_scope": "regional",  # Found "south florida"
        "has_fleet": False,  # No mention found
        "has_warehouse": True,  # Found "warehouse"
        "has_employees": True,  # Found "team"
        "commercial_focus": True,  # Found "commercial"
        "has_insurance": True,  # Found "insured"
        "content_preview": "JM Holiday Lighting provides professional holiday lighting installation throughout South Florida. Our team handles commercial and residential properties with our warehouse facility..."
    }
    
    prompt = create_llm_sizing_prompt(contractor, website_data)
    
    print("PROMPT TO LLM:")
    print(prompt)
    
    print("\n" + "=" * 60)
    print("EXPECTED LLM RESPONSE:")
    print("-" * 60)
    
    expected_response = {
        "size_category": "owner_operator",
        "confidence": 75,
        "key_factors": [
            "Has employees/team mentioned but no specific count",
            "Has warehouse facility",
            "Regional service area (not national)",
            "Commercial focus but no fleet vehicles",
            "Incorporated business (Inc)"
        ],
        "reasoning": "Website mentions 'team' indicating multiple people, has warehouse suggesting established operation, but limited to regional area and no fleet vehicles mentioned suggests smaller operation. Likely owner with 2-5 employees."
    }
    
    print(json.dumps(expected_response, indent=2))
    
    # Example 2: No website data
    print("\n\n[EXAMPLE 2: Mike's Christmas Lights - No Website]")
    print("-" * 60)
    
    contractor_no_site = {
        "company_name": "Mike's Christmas Lights",
        "website": None,
        "phone": "(954) 555-3333",
        "city": "Deerfield Beach",
        "state": "FL",
        "google_review_count": 42,
        "google_rating": 4.6
    }
    
    prompt2 = create_llm_sizing_prompt(contractor_no_site, {})
    
    print("PROMPT TO LLM:")
    print(prompt2[:500] + "...")  # Truncated for readability
    
    print("\nEXPECTED LLM RESPONSE:")
    expected_response2 = {
        "size_category": "owner_operator",
        "confidence": 60,
        "key_factors": [
            "Personal name in business (Mike's)",
            "42 Google reviews (moderate activity)",
            "No website (smaller operations often lack websites)",
            "Local service area"
        ],
        "reasoning": "Personal name suggests owner-operated business. Review count indicates active but not large-scale operation. Lack of website common for smaller contractors. Likely Mike with 1-3 helpers."
    }
    
    print(json.dumps(expected_response2, indent=2))
    
    # Show simplified version
    print("\n\n[SIMPLIFIED PROMPT VERSION]")
    print("-" * 60)
    
    all_data = """
    Company: Reindeer Bros
    Website: https://reindeerbros.com
    Found on website: "nationwide service", "commercial-grade LED", "$1,500 minimum"
    Reviews: Not found
    """
    
    simple_prompt = create_simple_llm_prompt(all_data)
    print("SIMPLE PROMPT:")
    print(simple_prompt)
    
    print("\nEXPECTED RESPONSE:")
    print(json.dumps({
        "size_category": "regional_company",
        "confidence": 85,
        "reasoning": "Nationwide service indicates large operation. $1,500 minimum and commercial-grade equipment suggests established business with significant resources."
    }, indent=2))


def show_api_implementation():
    """Show how to implement this with actual API calls"""
    
    print("\n\n" + "=" * 80)
    print("API IMPLEMENTATION")
    print("=" * 80)
    
    print("""
# With OpenAI GPT-4:
async def categorize_with_gpt4(contractor, website_data):
    import openai
    
    prompt = create_llm_sizing_prompt(contractor, website_data)
    
    response = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert at analyzing contractor business size."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,  # Low temperature for consistency
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

# With Anthropic Claude:
async def categorize_with_claude(contractor, website_data):
    import anthropic
    
    prompt = create_llm_sizing_prompt(contractor, website_data)
    
    response = await anthropic.messages.create(
        model="claude-3-opus-20240229",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500
    )
    
    # Parse JSON from Claude's response
    json_str = response.content[0].text
    return json.loads(json_str)

# Usage in your system:
async def process_contractor(contractor):
    # Step 1: Try to enrich from website
    website_data = await scrape_website(contractor.get('website'))
    
    # Step 2: Let LLM categorize with ALL data
    categorization = await categorize_with_gpt4(contractor, website_data)
    
    # Step 3: Use the result
    contractor['size_category'] = categorization['size_category']
    contractor['sizing_confidence'] = categorization['confidence']
    contractor['sizing_reasoning'] = categorization['reasoning']
    
    return contractor
""")
    
    print("\n" + "=" * 80)
    print("BENEFITS OF LLM-BASED APPROACH")
    print("=" * 80)
    print("""
1. SIMPLER: No complex if/else rules to maintain
2. SMARTER: LLM can understand context and nuance
3. FLEXIBLE: Handles edge cases automatically
4. EXPLAINABLE: Returns reasoning for each decision
5. CONSISTENT: Low temperature ensures similar results
6. ADAPTABLE: Just update the prompt for new requirements

The LLM can understand things like:
- "Family-owned for 3 generations" -> established business
- "Just me and my truck" -> solo_handyman
- "Our fleet of 15 vehicles" -> small_business or larger
- "Serving all 50 states" -> enterprise
- "Owner-operated since 2019" -> owner_operator
""")


if __name__ == "__main__":
    show_real_examples()
    show_api_implementation()