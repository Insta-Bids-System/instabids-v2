#!/usr/bin/env python3
"""
Show EXACT Logic and Prompts for Contractor Sizing Decisions
Demonstrates what data goes into each sizing decision
"""
import json
from datetime import datetime


# REAL contractors with their scraped website data
CONTRACTORS_WITH_ENRICHMENT = [
    {
        "company_name": "JM Holiday Lighting Inc",
        "website_scraped": True,
        "scraped_content_length": 9442,
        "data_found": {
            "service_scope": "regional",  # Found "south florida" in text
            "has_warehouse": True,  # Found "warehouse" or "facility" in text
            "has_insurance": True,  # Found "insured" in text
            "has_employees": True,  # Found "team" or "employees" in text
            "commercial_focus": True,  # Found "commercial" in text
            "team_size": None,  # No specific number found
            "years_in_business": None  # No specific years found
        }
    },
    {
        "company_name": "Warriors for Light",
        "website_scraped": True,
        "scraped_content_length": 6892,
        "data_found": {
            "service_scope": "local",
            "has_insurance": True,  # "fully insured"
            "has_employees": True,  # "installers" mentioned
            "has_fleet": False,
            "has_warehouse": False,
            "commercial_focus": False,
            "team_size": None,
            "years_in_business": None
        }
    },
    {
        "company_name": "Reindeer Bros",
        "website_scraped": True,
        "scraped_content_length": 12455,
        "data_found": {
            "service_scope": "national",  # Found "nationwide" or similar
            "has_insurance": True,
            "commercial_focus": True,  # "commercial-grade LED"
            "minimum_price": 1500,  # "$1,500 minimum"
            "response_time": "24-48 hours",
            "team_size": None,
            "years_in_business": None
        }
    }
]


def show_sizing_logic():
    """Show EXACTLY how each contractor was sized"""
    
    print("=" * 80)
    print("CONTRACTOR SIZING DECISION LOGIC")
    print("=" * 80)
    
    # Show the actual categorization logic
    print("\n[CATEGORIZATION RULES USED]")
    print("-" * 60)
    print("""
The system uses this EXACT logic (from categorize_based_on_enrichment function):

if enrichment.get("enrichment_complete"):
    # RULE 1: Large companies
    if team_size > 20 or scope in ["national", "statewide"]:
        return "regional_company"
    
    # RULE 2: Small businesses  
    elif team_size > 5 or (has_fleet and has_warehouse) or (commercial and years > 10):
        return "small_business"
    
    # RULE 3: Owner operators
    elif team_size > 1 or years > 3 or has_employees:
        return "owner_operator"
    
    # RULE 4: Solo operations
    else:
        return "solo_handyman"
else:
    # NO WEBSITE DATA - Use business indicators:
    if "inc" or "llc" in company_name:
        if "tree" or "landscaping" in name:
            return "small_business"  # Established service company
        return "owner_operator"  # Incorporated but likely smaller
    
    if "$1,500 minimum" in description:
        return "small_business"  # Higher minimums = larger
    
    if "concierge" in services:
        return "small_business"  # Premium service model
    
    return "owner_operator"  # Default
    """)
    
    print("\n[ACTUAL SIZING DECISIONS]")
    print("-" * 60)
    
    # Decision 1: JM Holiday Lighting Inc
    print("\n1. JM Holiday Lighting Inc")
    print("   DATA EXTRACTED FROM WEBSITE:")
    print("   - service_scope: 'regional' (found 'south florida')")
    print("   - has_warehouse: True (found 'warehouse/facility')")
    print("   - has_employees: True (found 'team/employees')")
    print("   - commercial_focus: True (found 'commercial')")
    print("   - team_size: None (no number found)")
    print("   - years_in_business: None (no years found)")
    print("\n   LOGIC PATH:")
    print("   - Check RULE 1: team_size > 20? NO (no team size)")
    print("   - Check RULE 1: scope in ['national', 'statewide']? NO ('regional')")
    print("   - Check RULE 2: team_size > 5? NO (no team size)")
    print("   - Check RULE 2: has_fleet AND has_warehouse? NO (no fleet mention)")
    print("   - Check RULE 2: commercial AND years > 10? NO (no years found)")
    print("   - Check RULE 3: has_employees? YES [OK]")
    print("   -> RESULT: owner_operator")
    
    print("\n2. Warriors for Light")
    print("   DATA EXTRACTED FROM WEBSITE:")
    print("   - service_scope: 'local'")
    print("   - has_insurance: True (found 'fully insured')")
    print("   - has_employees: True (found 'installers')")
    print("   - No fleet, warehouse, or team size found")
    print("\n   LOGIC PATH:")
    print("   - Check RULE 1: scope 'national/statewide'? NO ('local')")
    print("   - Check RULE 2: No fleet, no warehouse")
    print("   - Check RULE 3: has_employees? YES [MATCH]")
    print("   -> RESULT: owner_operator")
    
    print("\n3. Reindeer Bros")
    print("   DATA EXTRACTED FROM WEBSITE:")
    print("   - service_scope: 'national' [MATCH]")
    print("   - commercial_focus: True")
    print("   - $1,500 minimum pricing")
    print("\n   LOGIC PATH:")
    print("   - Check RULE 1: scope in ['national', 'statewide']? YES [MATCH]")
    print("   -> RESULT: regional_company")
    
    print("\n4. Real Tree Trimming & Landscaping Inc")
    print("   NO WEBSITE DATA (403 error)")
    print("\n   LOGIC PATH (using business indicators):")
    print("   - Company name contains 'Inc'? YES")
    print("   - Company name contains 'landscaping'? YES")
    print("   - Rule: Inc + landscaping = established service company")
    print("   -> RESULT: small_business")
    
    # Show the GPT-4 prompt that would be used
    print("\n" + "=" * 60)
    print("[GPT-4 PROMPT FOR INTELLIGENT SIZING]")
    print("=" * 60)
    
    gpt4_prompt = """
Analyze this contractor's size based on ACTUAL DATA from their website and Google:

WEBSITE DATA COLLECTED:
- Team size mentioned: {team_size}
- Years in business: {years_in_business}
- Service scope: {service_scope}
- Has fleet vehicles: {has_fleet}
- Has warehouse/facility: {has_warehouse}
- Commercial focus: {commercial_focus}
- Insurance mentioned: {has_insurance}
- Employees mentioned: {has_employees}

GOOGLE DATA:
- Company name: {company_name}
- Review count: {review_count}
- Rating: {rating}

Based on this REAL DATA (not guessing from review count), categorize as:
- solo_handyman: 1 person operation, no employees mentioned
- owner_operator: 2-5 person team, has employees but small
- small_business: 6-20 employees, fleet/warehouse, established
- regional_company: 20-100 employees, multiple locations, regional/statewide
- enterprise: 100+ employees, national presence

Return JSON with:
- size_category: The accurate size based on real data
- confidence: How confident you are (0-100)
- reasoning: Explain what specific data points led to this conclusion
- key_indicators: List the most important factors
    """
    
    print(gpt4_prompt)
    
    print("\n[EXAMPLE GPT-4 INPUT FOR JM HOLIDAY LIGHTING]")
    print("-" * 60)
    
    example_input = """
WEBSITE DATA COLLECTED:
- Team size mentioned: None
- Years in business: None
- Service scope: regional (South Florida)
- Has fleet vehicles: False
- Has warehouse/facility: True
- Commercial focus: True
- Insurance mentioned: True
- Employees mentioned: True

GOOGLE DATA:
- Company name: JM Holiday Lighting Inc
- Review count: Not available
- Rating: Not available
    """
    
    print(example_input)
    
    print("\n[EXPECTED GPT-4 RESPONSE]")
    print("-" * 60)
    
    expected_response = {
        "size_category": "owner_operator",
        "confidence": 75,
        "reasoning": "Has employees and warehouse facility suggesting established business, but regional scope (not statewide/national) and no specific team size mentioned suggests smaller operation. Commercial focus but no fleet vehicles indicates owner-operator with small team.",
        "key_indicators": [
            "Has employees (not solo)",
            "Has warehouse (established)",
            "Regional scope (not large company)",
            "No fleet mentioned (smaller operation)"
        ]
    }
    
    print(json.dumps(expected_response, indent=2))
    
    print("\n" + "=" * 80)
    print("SUMMARY: How Sizing Actually Works")
    print("=" * 80)
    print("""
1. ENRICHMENT FIRST: Scrape website for real data
2. EXTRACT INDICATORS: Look for team size, fleet, warehouse, scope
3. APPLY RULES: Use logical rules based on extracted data
4. GPT-4 BACKUP: For complex cases, use GPT-4 with ALL data
5. NO GUESSING: Only use review count if NO website available
    """)


if __name__ == "__main__":
    show_sizing_logic()