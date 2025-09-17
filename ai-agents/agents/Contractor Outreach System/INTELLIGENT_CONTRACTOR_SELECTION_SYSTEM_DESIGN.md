# Intelligent Contractor Selection System - Complete Architecture
**Generated**: January 13, 2025  
**Purpose**: Design comprehensive AI-powered contractor discovery and validation system

## 🎯 THE REAL CHALLENGE

**Current Problem**: Simple hardcoded logic tries to find 10-15 contractors but fails because:
- Hardcoded Google search terms miss relevant contractors
- No geographic expansion when insufficient contractors found
- No contractor size/company type validation
- No intelligent research to verify contractor fits criteria
- No adaptive strategy when searches fail

**Need**: **GIANT INTELLIGENT SYSTEM** that can:
1. Intelligently research and find contractors
2. Validate each contractor against ALL bid card criteria
3. Expand search geographically and strategically when needed
4. Use multiple tools and data sources for comprehensive discovery
5. Go back-and-forth until exactly the right contractors are selected

---

## 🧠 INTELLIGENT CONTRACTOR SELECTION ARCHITECTURE

### **PHASE 1: INTELLIGENT PROJECT ANALYSIS**
```
┌─────────────────────────────────────────────────────────────┐
│                 GPT-4 PROJECT ANALYZER                     │
├─────────────────────────────────────────────────────────────┤
│ Input: Bid Card + Project Description                      │
│ Output: Intelligent Search Strategy                        │
│                                                             │
│ Analyzes:                                                   │
│ • Project complexity and specialization needs              │
│ • Contractor size requirements (solo vs enterprise)        │
│ • Quality/budget balance preferences                       │
│ • Urgency and timeline constraints                         │
│ • Local market terminology and search terms               │
│ • Geographic flexibility based on project type            │
└─────────────────────────────────────────────────────────────┘
```

**GPT-4 Generates:**
- **Smart Search Terms**: Not just "plumbing" but "emergency plumber", "residential plumbing repair", "kitchen plumbing specialist"  
- **Company Size Strategy**: "Need small local companies, avoid large franchises"
- **Geographic Strategy**: "Start 15-mile radius, expand to 25-mile if needed, prioritize nearby cities"
- **Quality Filters**: "Must have 4+ stars, 20+ reviews, established business"

### **PHASE 2: ADAPTIVE MULTI-SOURCE DISCOVERY**
```
┌─────────────────────────────────────────────────────────────┐
│              INTELLIGENT DISCOVERY ENGINE                   │
├─────────────────────────────────────────────────────────────┤
│ Tier 1: Database Search (AI-enhanced filtering)            │
│ Tier 2: Previous Contacts (intelligent re-engagement)      │
│ Tier 3: Multi-Source Web Discovery                         │
│                                                             │
│ ADAPTIVE EXPANSION LOGIC:                                   │
│ • Start: 15-mile radius, target ZIP + 3 neighboring ZIPs   │
│ • Expand: 25-mile radius, add 6 more ZIPs                  │
│ • Fallback: 40-mile radius, major metro area               │
│                                                             │
│ MULTI-SOURCE SEARCH:                                       │
│ • Google Places API (intelligent search terms)             │
│ • Google Business Profile research                         │
│ • Yelp Business API                                        │
│ • Website Analysis Tool (company size detection)           │
└─────────────────────────────────────────────────────────────┘
```

### **PHASE 3: INTELLIGENT CONTRACTOR VALIDATION**
```
┌─────────────────────────────────────────────────────────────┐
│            CONTRACTOR RESEARCH & VALIDATION                 │
├─────────────────────────────────────────────────────────────┤
│ For Each Discovered Contractor:                            │
│                                                             │
│ 1. COMPANY RESEARCH (Google Business Tool)                 │
│    • Verify business exists and is active                  │
│    • Extract services, specialties, service areas          │
│    • Get reviews, ratings, years in business               │
│    • Determine company size (solo vs team vs enterprise)   │
│                                                             │
│ 2. WEBSITE ANALYSIS & COMPANY SIZE DETECTION               │
│    • Analyze contractor website content and structure      │
│    • Detect company size indicators (team size, services)  │
│    • Extract specialties and service areas from website    │
│                                                             │
│ 3. PROJECT FIT ANALYSIS (GPT-4)                           │
│    • Does company size match bid card requirements?        │
│    • Do specialties align with project needs?              │
│    • Is service area compatible with project location?     │
│    • Does quality level match homeowner preferences?       │
│                                                             │
│ 4. CONTACT INFORMATION VALIDATION                          │
│    • Verify phone numbers are working                      │
│    • Extract email addresses from websites                 │
│    • Identify best outreach channels (email/form/phone)    │
└─────────────────────────────────────────────────────────────┘
```

### **PHASE 4: STRATEGIC SEARCH EXPANSION**
```
┌─────────────────────────────────────────────────────────────┐
│              ADAPTIVE SEARCH STRATEGY                       │
├─────────────────────────────────────────────────────────────┤
│ EXPANSION TRIGGERS:                                         │
│ • < 5 qualified contractors found → Expand radius          │
│ • < 3 contractors with websites → Add phone-only           │
│ • No enterprise contractors → Include franchise chains     │
│ • No local contractors → Search neighboring cities         │
│                                                             │
│ SEARCH TERM EVOLUTION:                                      │
│ Round 1: "emergency plumber Orlando FL"                    │
│ Round 2: "residential plumbing repair Orlando"             │
│ Round 3: "plumbing services near Orlando FL"               │
│ Round 4: "plumber Winter Park FL" (neighboring city)       │
│                                                             │
│ GEOGRAPHIC EXPANSION:                                       │
│ Level 1: Target ZIP (32801) + 15-mile radius               │
│ Level 2: Add 3 neighboring ZIPs + 25-mile radius           │
│ Level 3: Add 6 metro ZIPs + 40-mile radius                 │
│ Level 4: Include neighboring counties                       │
└─────────────────────────────────────────────────────────────┘
```

### **PHASE 5: INTELLIGENT FINAL SELECTION**
```
┌─────────────────────────────────────────────────────────────┐
│                SMART CONTRACTOR SELECTION                   │
├─────────────────────────────────────────────────────────────┤
│ SELECTION CRITERIA (GPT-4 Powered):                        │
│                                                             │
│ 1. PROJECT ALIGNMENT SCORE                                 │
│    • Specialty match: Exact vs Related vs General          │
│    • Company size fit: Solo vs Small vs Large              │
│    • Service area coverage: Local vs Regional              │
│                                                             │
│ 2. QUALITY & TRUST SCORE                                   │
│    • Customer ratings and review quality                   │
│    • Business longevity and stability                      │
│    • License/insurance verification status                 │
│                                                             │
│ 3. OUTREACH SUCCESS PROBABILITY                            │
│    • Contact method availability (email/phone/website)     │
│    • Response likelihood based on business type            │
│    • Previous engagement history (if Tier 2)               │
│                                                             │
│ 4. DIVERSITY & OPTIMIZATION                                │
│    • Mix of company sizes per bid card preferences         │
│    • Geographic distribution for coverage                  │
│    • Range of price points and service levels              │
│                                                             │
│ FINAL OUTPUT:                                               │
│ • Exactly 10-15 contractors ranked by fit                  │
│ • Each with detailed research profile                      │
│ • Optimal outreach channel assignments                     │
│ • Expected response rate calculation                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 REQUIRED TOOLS & INTEGRATIONS

### **EXISTING TOOLS TO ENHANCE**
1. **Google Business Research Tool** (`google_business_research_tool.py`)
   - Currently exists but needs GPT-4 integration for intelligent search terms
   - Add company size detection logic
   - Add service area validation

2. **Radius Search Tool** (`radius_search_fixed.py`)  
   - Add adaptive expansion logic
   - Multi-ZIP search capability
   - Neighboring city discovery

### **NEW TOOLS NEEDED**

3. **Website Analysis Tool**
   - Scrape and analyze contractor websites
   - Detect company size indicators (team photos, staff pages, "about us")
   - Extract services, specialties, and coverage areas
   - Identify solo vs small team vs larger company

4. **Yelp Business API Integration**
   - Yelp Business API for additional contractor discovery
   - Cross-reference Google Places results with Yelp data
   - Enhanced review and rating information

5. **Contact Validation Tool**
   - Phone number verification service
   - Email extraction from websites
   - Contact method prioritization

6. **Intelligent Search Term Generator**
   - GPT-4 powered search term evolution
   - Local market terminology research
   - Project-specific search optimization

---

## 🌐 WEBSITE ANALYSIS TOOL - COMPANY SIZE DETECTION

### **Website Scraping & Analysis System**
```
┌─────────────────────────────────────────────────────────────┐
│                 WEBSITE ANALYSIS TOOL                      │
├─────────────────────────────────────────────────────────────┤
│ Input: Contractor website URL                              │
│ Output: Company size classification + business details     │
│                                                             │
│ ANALYSIS COMPONENTS:                                        │
│                                                             │
│ 1. PAGE STRUCTURE ANALYSIS                                 │
│    • "About Us" page content extraction                    │
│    • "Team" or "Staff" page detection                      │
│    • Service pages breadth and depth                       │
│    • Contact page complexity                               │
│                                                             │
│ 2. CONTENT INDICATORS                                       │
│    • Team photos and staff listings                        │
│    • Service area coverage (city vs multi-state)          │
│    • Project gallery size and scope                        │
│    • Years in business and company history                 │
│                                                             │
│ 3. BUSINESS SCALE INDICATORS                               │
│    • Multiple office locations                             │
│    • 24/7 emergency services                              │
│    • Commercial vs residential focus                       │
│    • Franchise or corporate branding                       │
│                                                             │
│ 4. GPT-4 CLASSIFICATION                                    │
│    • Analyze all extracted content                         │
│    • Classify: Solo, Small Team (2-10), Medium (11-50),   │
│      Large (50+), Enterprise/Franchise                     │
│    • Extract specialties and service areas                 │
│    • Assess quality level and target market               │
└─────────────────────────────────────────────────────────────┘
```

### **Company Size Detection Logic**
```python
def analyze_contractor_website(website_url, company_name):
    """Scrape and analyze website to determine company size and capabilities"""
    
    # Step 1: Scrape website content
    website_content = scrape_website_content(website_url)
    
    # Step 2: Extract key indicators
    indicators = {
        'team_members_mentioned': count_team_members(website_content),
        'office_locations': extract_locations(website_content),
        'service_areas': extract_service_coverage(website_content),
        'years_in_business': extract_business_age(website_content),
        'services_offered': extract_services_list(website_content),
        'commercial_focus': detect_commercial_services(website_content),
        'emergency_services': detect_24_7_services(website_content),
        'franchise_indicators': detect_franchise_branding(website_content)
    }
    
    # Step 3: GPT-4 analysis of website content
    gpt4_analysis = analyze_with_gpt4(website_content, indicators)
    
    return {
        'company_size': gpt4_analysis['size_classification'],  # solo/small/medium/large/enterprise
        'size_confidence': gpt4_analysis['confidence_score'],
        'team_size_estimate': gpt4_analysis['estimated_employees'],
        'business_type': gpt4_analysis['business_classification'],  # local/regional/franchise
        'specializations': gpt4_analysis['core_specialties'],
        'service_areas': gpt4_analysis['coverage_areas'],
        'target_market': gpt4_analysis['typical_customers'],  # residential/commercial/mixed
        'quality_indicators': gpt4_analysis['quality_signals']
    }
```

### **GPT-4 Website Analysis Prompt**
```
Analyze this contractor's website content to determine their business size and capabilities:

COMPANY: {company_name}
WEBSITE CONTENT: {scraped_content}
INDICATORS FOUND: {extracted_indicators}

Please classify this contractor and return JSON with:

1. "size_classification": solo_operator | small_team | medium_company | large_company | enterprise_franchise
2. "confidence_score": 0-100 (confidence in classification)
3. "estimated_employees": Number estimate (1, 2-5, 6-15, 16-50, 50+)
4. "business_classification": local_contractor | regional_company | franchise_operation
5. "core_specialties": Array of main services offered
6. "coverage_areas": Geographic service coverage
7. "typical_customers": residential_only | commercial_only | mixed_clientele
8. "quality_indicators": Array of quality/professionalism signals

CLASSIFICATION GUIDELINES:
- Solo Operator: "I" language, single person, basic website, limited services
- Small Team: "We" language, team photos, 2-10 people, local focus
- Medium Company: Multiple specialties, established processes, 10-50 employees
- Large Company: Multiple locations, commercial focus, 50+ employees
- Enterprise/Franchise: Corporate branding, standardized processes, multi-market
```

---

## 🔄 COMPLETE WORKFLOW DESIGN

### **ITERATIVE DISCOVERY LOOP**
```python
def intelligent_contractor_discovery(bid_card_id, target_count=12):
    """Main intelligent discovery loop"""
    
    # Phase 1: Analyze project with GPT-4
    search_strategy = gpt4_analyze_project(bid_card)
    
    contractors_found = []
    search_radius = 15
    zip_expansion_level = 1
    search_term_round = 1
    
    while len(contractors_found) < target_count and search_radius <= 50:
        print(f"Search Round {search_term_round}: {search_radius}mi radius")
        
        # Phase 2: Intelligent multi-source discovery
        new_contractors = multi_source_discovery(
            search_strategy=search_strategy,
            radius=search_radius,
            zip_codes=get_zip_codes_for_level(zip_expansion_level),
            search_terms=generate_intelligent_search_terms(
                search_strategy, 
                search_term_round
            )
        )
        
        # Phase 3: Validate each contractor
        for contractor in new_contractors:
            validation_result = validate_contractor(contractor, bid_card)
            if validation_result.is_qualified:
                contractors_found.append({
                    **contractor,
                    **validation_result.research_data,
                    'qualification_score': validation_result.score
                })
        
        # Phase 4: Adaptive expansion logic
        if len(contractors_found) < target_count * 0.6:  # Less than 60% found
            if search_radius < 25:
                search_radius = 25  # Expand radius
            elif zip_expansion_level < 3:
                zip_expansion_level += 1  # Add more ZIPs
            else:
                search_term_round += 1  # Try different search terms
                search_radius += 10  # Keep expanding
        else:
            break  # Good progress, continue with current strategy
    
    # Phase 5: Intelligent final selection
    selected_contractors = gpt4_select_optimal_contractors(
        contractors_found, 
        bid_card, 
        target_count
    )
    
    return {
        'success': len(selected_contractors) >= target_count * 0.8,
        'contractors': selected_contractors,
        'research_summary': generate_search_summary(),
        'expansion_levels_used': {
            'max_radius': search_radius,
            'zip_expansion': zip_expansion_level,
            'search_rounds': search_term_round
        }
    }
```

### **CONTRACTOR VALIDATION WORKFLOW**
```python
def validate_contractor(contractor, bid_card):
    """Comprehensive contractor validation"""
    
    # Step 1: Business research
    business_research = google_business_tool.research_contractor(
        company_name=contractor['company_name'],
        location=contractor['location']
    )
    
    # Step 2: Website analysis for company size detection
    website_analysis = website_analysis_tool.analyze_contractor_website(
        website_url=contractor.get('website'),
        company_name=contractor['company_name']
    )
    
    # Step 3: GPT-4 project fit analysis
    fit_analysis = gpt4_analyze_contractor_fit(
        contractor=contractor,
        business_data=business_research,
        project_requirements=bid_card
    )
    
    # Step 4: Contact validation
    contact_validation = validate_contact_methods(contractor)
    
    qualification_score = calculate_qualification_score(
        business_research,
        website_analysis, 
        fit_analysis,
        contact_validation
    )
    
    return ValidationResult(
        is_qualified=qualification_score >= 70,
        score=qualification_score,
        research_data={
            'business_profile': business_research,
            'website_analysis': website_analysis,
            'project_fit': fit_analysis,
            'contact_methods': contact_validation
        }
    )
```

---

## 🚨 CRITICAL IMPLEMENTATION REQUIREMENTS

### **1. LLM Integration Points**
- **Project Analysis**: GPT-4 analyzes bid card for intelligent search strategy
- **Search Term Generation**: GPT-4 creates contextual, market-specific search terms  
- **Contractor Validation**: GPT-4 evaluates contractor-to-project fit
- **Final Selection**: GPT-4 optimizes contractor mix and ranking

### **2. Adaptive Logic Requirements**
- **Geographic Expansion**: Intelligent radius and ZIP code expansion
- **Search Term Evolution**: Modify search terms based on results
- **Quality Threshold Adjustment**: Lower standards if premium contractors unavailable
- **Source Diversification**: Try different discovery sources when one fails

### **3. Data Integration Requirements**
- **Core APIs**: Google Places, Yelp Business API
- **Website Scraping**: Automated website analysis for company size detection
- **Real-time Validation**: Phone/email verification during discovery
- **Business Intelligence**: Company size, service areas, specialties from websites
- **Historical Data**: Previous outreach results for optimization

### **4. Performance Requirements**
- **Iterative Processing**: Handle 3-5 search expansion rounds
- **Parallel Processing**: Validate multiple contractors simultaneously  
- **Caching Strategy**: Cache business research to avoid repeated API calls
- **Timeout Management**: Complete discovery within 2-3 minutes maximum

---

## 📋 IMPLEMENTATION PHASES

### **Phase 1: Enhanced Search Strategy (Week 1)**
- Integrate GPT-4 into search term generation
- Add adaptive radius expansion logic
- Implement multi-ZIP code discovery

### **Phase 2: Website Analysis & Validation System (Week 2)**
- Build website scraping and analysis tool
- Add company size detection from website content
- Implement GPT-4 project fit analysis

### **Phase 3: Intelligent Selection Logic (Week 3)**  
- Create GPT-4 powered final selection system
- Add contractor mix optimization
- Implement outreach channel assignment

### **Phase 4: Multi-Source Discovery (Week 4)**
- Integrate Yelp Business API
- Add contact method validation
- Optimize parallel processing performance

### **Phase 5: Testing & Optimization (Week 5)**
- End-to-end testing with real bid cards
- Performance optimization and caching
- Production deployment and monitoring

---

This system would be a **comprehensive AI-powered contractor discovery and validation engine** that can intelligently find, research, validate, and select the exact contractors needed for any bid card - automatically expanding search strategies and using multiple tools until the perfect contractor mix is achieved.