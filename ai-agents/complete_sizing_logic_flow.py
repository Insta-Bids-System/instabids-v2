#!/usr/bin/env python3
"""
COMPLETE CONTRACTOR SIZING LOGIC FLOW
Shows the EXACT logic from discovery to final categorization
"""

def show_complete_logic():
    """Display the complete logic flow"""
    
    print("=" * 80)
    print("COMPLETE CONTRACTOR SIZING LOGIC - EXACT IMPLEMENTATION")
    print("=" * 80)
    
    # STAGE 1: DISCOVERY
    print("\n[STAGE 1: DISCOVERY]")
    print("-" * 60)
    print("""
DISCOVERY SOURCES (3-Tier System):
1. Tier 1: Internal database (contractors table)
2. Tier 2: Previous contacts (contractor_leads table) 
3. Tier 3: Google Places API + Web Search

GOOGLE PLACES API CALL:
{
    "textQuery": "christmas light installation near 33442",
    "includedType": "contractor",
    "pageSize": 20,  # Get 20 at once
    "locationBias": {
        "circle": {
            "center": {"latitude": 26.3683, "longitude": -80.1289},
            "radius": 24140  # 15 miles in meters
        }
    }
}

Returns: Company names, websites, phone numbers, review counts
""")
    
    # STAGE 2: ENRICHMENT
    print("\n[STAGE 2: WEBSITE ENRICHMENT]")
    print("-" * 60)
    print("""
FOR EACH CONTRACTOR:
1. Try to scrape website URL
2. Extract text content from HTML
3. Look for specific indicators:

EXTRACTION PATTERNS (Python regex):
    
# Team size patterns
team_patterns = [
    r'(\\d+)\\+?\\s*(employees?|team members?|professionals?|technicians?|installers?)',
    r'team of (\\d+)',
    r'staff of (\\d+)'
]

# Years in business patterns  
year_patterns = [
    r'(since|established|serving since|in business since|founded in)\\s*(\\d{4})',
    r'(\\d+)\\+?\\s*years?\\s*(of experience|in business|serving)'
]

# Service scope detection
if "nationwide" in text or "national" in text:
    service_scope = "national"
elif "statewide" in text or "all of florida" in text:
    service_scope = "statewide"  
elif "south florida" in text or "tri-county" in text:
    service_scope = "regional"
else:
    service_scope = "local"

# Boolean indicators
has_fleet = "fleet" in text or "trucks" in text or "vehicles" in text
has_warehouse = "warehouse" in text or "facility" in text or "headquarters" in text
has_insurance = "insured" in text or "insurance" in text
has_employees = "employees" in text or "team" in text or "staff" in text
commercial_focus = "commercial" in text or "business" in text
""")
    
    # STAGE 3: CATEGORIZATION LOGIC
    print("\n[STAGE 3: CATEGORIZATION RULES]")
    print("-" * 60)
    print("""
def categorize_contractor(enrichment_data):
    '''EXACT categorization logic used'''
    
    if enrichment_data.get("enrichment_complete"):
        # WE HAVE WEBSITE DATA - Use it!
        team_size = enrichment_data.get("team_size", 0)
        years = enrichment_data.get("years_in_business", 0)
        scope = enrichment_data.get("service_scope", "local")
        has_fleet = enrichment_data.get("has_fleet", False)
        has_warehouse = enrichment_data.get("has_warehouse", False)
        has_employees = enrichment_data.get("has_employees", False)
        commercial = enrichment_data.get("commercial_focus", False)
        
        # RULE 1: Large companies (HIGHEST PRIORITY)
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
        # NO WEBSITE DATA - Use fallback logic
        company_name = contractor.get("company_name", "").lower()
        
        # Check business entity type
        if "inc" in company_name or "llc" in company_name:
            if "tree" in company_name or "landscaping" in company_name:
                return "small_business"  # Established service company
            return "owner_operator"  # Incorporated but likely smaller
        
        # Check service description
        if "$1,500 minimum" in contractor.get("minimum", ""):
            return "small_business"  # Higher minimums = larger
        
        if "concierge" in contractor.get("services", "").lower():
            return "small_business"  # Premium service model
        
        # LAST RESORT - Use review count
        review_count = contractor.get("google_review_count", 0)
        if review_count > 200:
            return "regional_company"
        elif review_count > 100:
            return "small_business"
        elif review_count > 20:
            return "owner_operator"
        else:
            return "solo_handyman"
""")
    
    # STAGE 4: SIZE FILTERING
    print("\n[STAGE 4: ±1 SIZE FLEXIBILITY]")
    print("-" * 60)
    print("""
SIZE HIERARCHY:
1. solo_handyman     (1 person)
2. owner_operator    (2-5 people) <- TARGET SIZE
3. small_business    (6-20 people)
4. regional_company  (20-100 people)
5. enterprise        (100+ people)

±1 FLEXIBILITY LOGIC:
target_size = "owner_operator"  # User preference: size 2

# Define acceptable sizes (one level up and down)
size_order = ["solo_handyman", "owner_operator", "small_business", "regional_company", "enterprise"]
target_index = size_order.index(target_size)

acceptable_sizes = [
    size_order[max(0, target_index - 1)],      # One size down
    size_order[target_index],                   # Target size
    size_order[min(4, target_index + 1)]        # One size up
]

# Result: ["solo_handyman", "owner_operator", "small_business"]

# Filter contractors
matching_contractors = [
    c for c in all_contractors 
    if c["size_category"] in acceptable_sizes
]
""")
    
    # STAGE 5: CAMPAIGN SELECTION
    print("\n[STAGE 5: FINAL SELECTION (5/10/15 RULE)]")
    print("-" * 60)
    print("""
CONTRACTOR SELECTION FOR CAMPAIGNS:
- Max 5 from Tier 1 (90% response rate expected)
- Max 10 from Tier 2 (50% response rate expected)  
- Max 15 from Tier 3 (33% response rate expected)

def select_contractors_for_campaign(matching_contractors, bids_needed=4):
    '''Select contractors using the 5/10/15 rule'''
    
    tier1 = [c for c in matching_contractors if c["tier"] == 1][:5]
    tier2 = [c for c in matching_contractors if c["tier"] == 2][:10]
    tier3 = [c for c in matching_contractors if c["tier"] == 3][:15]
    
    # Calculate expected responses
    expected_responses = (
        len(tier1) * 0.90 +  # 90% response rate
        len(tier2) * 0.50 +  # 50% response rate
        len(tier3) * 0.33    # 33% response rate
    )
    
    # Add more contractors if needed
    if expected_responses < bids_needed:
        print(f"WARNING: Expected {expected_responses} responses, need {bids_needed}")
        # Escalation logic would add more Tier 3 contractors
    
    return tier1 + tier2 + tier3
""")
    
    # REAL EXAMPLE
    print("\n[REAL EXAMPLE: JM Holiday Lighting Inc]")
    print("-" * 60)
    print("""
INPUT DATA:
- Company: "JM Holiday Lighting Inc"
- Website: "https://jmholidaylighting.com/"
- Location: Pompano Beach, FL (near 33442)

ENRICHMENT PROCESS:
1. Scrape website -> Success (9442 characters)
2. Search for team size -> NOT FOUND
3. Search for years -> NOT FOUND  
4. Check service scope -> FOUND "south florida" -> "regional"
5. Check for fleet -> NOT FOUND
6. Check for warehouse -> FOUND "warehouse" -> True
7. Check for employees -> FOUND "team" -> True
8. Check commercial -> FOUND "commercial" -> True

CATEGORIZATION LOGIC:
- Rule 1: team_size > 20? NO, scope = "regional" not "national/statewide" -> NO MATCH
- Rule 2: team_size > 5? NO, has_fleet AND warehouse? NO (no fleet) -> NO MATCH
- Rule 3: has_employees? YES -> MATCH!
- Result: "owner_operator"

SIZE FILTERING:
- Target: "owner_operator"
- Acceptable: ["solo_handyman", "owner_operator", "small_business"]
- JM Holiday Lighting = "owner_operator" -> MATCHES!

CAMPAIGN SELECTION:
- JM Holiday Lighting is Tier 3 (discovered via Google)
- Would be included in campaign if within first 15 Tier 3 contractors
""")
    
    # GPT-4 FALLBACK
    print("\n[GPT-4 INTELLIGENT FALLBACK]")
    print("-" * 60)
    print("""
When rules aren't sufficient, system uses GPT-4:

PROMPT TEMPLATE:
{
    "messages": [
        {
            "role": "system",
            "content": "You are an expert at analyzing contractor business size based on website data."
        },
        {
            "role": "user", 
            "content": '''
            Analyze this contractor's size based on ACTUAL DATA from their website:
            
            WEBSITE DATA COLLECTED:
            - Team size mentioned: {extracted_team_size or "None"}
            - Years in business: {extracted_years or "None"}
            - Service scope: {extracted_scope}
            - Has fleet vehicles: {has_fleet}
            - Has warehouse/facility: {has_warehouse}
            - Commercial focus: {commercial_focus}
            - Employees mentioned: {has_employees}
            
            Based on this REAL DATA (not guessing), categorize as:
            - solo_handyman: 1 person operation
            - owner_operator: 2-5 person team
            - small_business: 6-20 employees
            - regional_company: 20-100 employees
            - enterprise: 100+ employees
            
            Return JSON with size_category, confidence, reasoning, key_indicators
            '''
        }
    ],
    "model": "gpt-4",
    "temperature": 0.3,
    "response_format": {"type": "json_object"}
}
""")
    
    print("\n" + "=" * 80)
    print("SUMMARY: COMPLETE LOGIC FLOW")
    print("=" * 80)
    print("""
1. DISCOVER contractors via Google Places API (no size filtering)
2. ENRICH each with website scraping (extract real indicators)
3. CATEGORIZE using 4-rule system (or GPT-4 fallback)
4. FILTER by size preference (±1 flexibility)
5. SELECT for campaign using 5/10/15 rule
6. TRACK responses and escalate if needed

The system prioritizes REAL DATA over guessing!
""")

if __name__ == "__main__":
    show_complete_logic()