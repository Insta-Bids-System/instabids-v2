# Landing Page Contractor Flow - Complete Design
**Date**: January 13, 2025
**Purpose**: Map out exact conversation flow and backend implementation for landing page contractor onboarding

## 🎯 USER STORY EXAMPLE

**User**: "Hey, I'm Justin, I own Shame Holiday Lighting. Do you guys have any bids for that?"

## 🔄 COMPLETE CONVERSATION FLOW

### **STAGE 1: Initial Contact & Business Identification**
```
USER: "Hey, I'm Justin, I own Shame Holiday Lighting. Do you guys have any bids for that?"

SYSTEM ACTIONS:
1. Extract business name: "Shame Holiday Lighting"
2. Extract user name: "Justin" 
3. Extract service type: "Holiday Lighting"

AGENT RESPONSE: 
"Hi Justin! I'd be happy to help you find holiday lighting projects. Let me quickly look up Shame Holiday Lighting to make sure I have the right business information."

BACKEND CALL: tools.search_google_business("Shame Holiday Lighting", "")
```

### **STAGE 2: Business Confirmation**
```
SYSTEM ACTIONS:
1. Google Business search returns business data
2. Extract location/zip code (e.g., 33442)
3. Extract phone number
4. Extract basic business info

AGENT RESPONSE:
"Great! I found Shame Holiday Lighting. Is this you?
- Location: [Address from Google Business]
- Phone: [Phone from Google Business] 
- Zip Code: 33442

Is this your business?"

USER: "Yes, that's me!"
```

### **STAGE 3: Deep Business Research & Profile Building**
```
SYSTEM ACTIONS:
1. Trigger web_search_company("Shame Holiday Lighting", "33442") 
2. Extract comprehensive business data (services, specialties, website info)
3. Build initial contractor profile
4. Save to contractors table (NOT contractor_leads - direct contractor)

AGENT RESPONSE:
"Perfect! I'm gathering some information about your services. I can see you specialize in holiday lighting. 

Based on your location at zip code 33442, how large of a radius would you like me to search for available projects? I can check for holiday lighting projects within 10, 25, or 50 miles of your location.

Also, do you offer any other services besides holiday lighting that you'd like me to include in the search?"
```

### **STAGE 4: Service Expansion & Radius Selection**
```
USER: "I also do outdoor lighting and landscape lighting. Check within 25 miles."

SYSTEM ACTIONS:
1. Update contractor profile with additional services
2. Set search radius to 25 miles
3. Search bid_cards for matching projects within radius

BACKEND CALL: tools.search_bid_cards(contractor_profile, "25_mile_radius")
```

### **STAGE 5: Bid Card Presentation**
```
AGENT RESPONSE:
"Excellent! I found [X] projects that match your services within 25 miles:

**HOLIDAY LIGHTING PROJECTS:**
1. Holiday Lighting Installation - $2,500-$4,000 budget (Boca Raton, FL)
2. Christmas Display Setup - $1,500-$3,000 budget (Delray Beach, FL)

**OUTDOOR LIGHTING PROJECTS:**  
3. Landscape Lighting Design - $3,000-$6,000 budget (Wellington, FL)

Would you like to see details on any of these projects, or shall I help you get set up to bid on them?"
```

### **STAGE 6: Account Creation & System Introduction**
```
USER: "Yes, show me the details and help me get set up!"

SYSTEM ACTIONS:
1. Create contractor account with email/temporary password
2. Save complete profile to contractors table
3. Generate contractor_id
4. Set up authentication

AGENT RESPONSE:
"Perfect! I'm creating your InstaBids contractor account right now.

**Why InstaBids is different:**
- Designed by contractors, for contractors
- No more Google Ads or Angie's List extortion
- Only pay when you're actually selected (90% less than typical customer acquisition)
- Direct homeowner conversations with measurements and details
- No unnecessary sales meetings - you get pre-qualified leads

I've created your account with:
- Email: [extracted/confirmed email]
- Temporary password: [generated password]

You can now view the full project details, message homeowners directly, and submit quotes. When you're selected for a project, you'll pay a small connection fee that's typically 90% less than your current customer acquisition costs.

Would you like me to show you the first project details, or would you prefer to explore the contractor portal?"
```

---

## 🛠️ BACKEND IMPLEMENTATION REQUIREMENTS

### **SYSTEM PROMPTS NEEDED**

#### **Landing Page Agent System Prompt**
```
You are the InstaBids Landing Page Assistant, specifically designed to onboard contractors into our platform.

CORE MISSION: Convert visiting contractors into active InstaBids users through helpful, consultative conversation.

CONVERSATION FLOW:
1. Extract business name, owner name, and service type from initial message
2. Use Google Business search to find and confirm their business
3. Once confirmed, gather comprehensive business information via web search
4. Help them specify services and search radius for projects
5. Show relevant bid cards and explain InstaBids value proposition
6. Create their contractor account and guide them into the system

INSTABIDS VALUE PROPOSITION (weave into conversation naturally):
- "InstaBids was designed by contractors, for contractors"
- "Stop the extortion from Google Ads, Angie's List, and lead sellers"
- "Get connected directly to homeowners with real projects"
- "Only pay when you're selected - typically 90% less than customer acquisition costs"
- "No unnecessary sales meetings - get pre-qualified, detailed leads"
- "Message homeowners directly, get measurements, submit soft quotes"

TONE: Helpful, knowledgeable contractor who understands their pain points
GOAL: Make them feel understood and excited about InstaBids' approach
```

#### **Tool Orchestration Logic**
```
STAGE 1: Business Identification
- IF business_name extracted → search_google_business(business_name, "")
- WAIT for user confirmation before proceeding

STAGE 2: Business Confirmation  
- IF user confirms → web_search_company(business_name, location)
- Build initial contractor profile
- Ask about services and radius

STAGE 3: Project Search
- search_bid_cards(profile_with_services, radius)
- Present matching projects visually

STAGE 4: Account Creation
- create_contractor_account(complete_profile)
- Generate temporary credentials
- Save to contractors table (NOT contractor_leads)
```

### **DATABASE CHANGES NEEDED**

#### **Direct Contractor Table Storage**
```sql
-- Landing page contractors go directly to contractors table
-- Skip contractor_leads table entirely for landing page flow
INSERT INTO contractors (
    user_id, company_name, contact_name, phone, email, website,
    address, city, state, zip_code, specialties, 
    tier, verified, account_source
) VALUES (
    generated_user_id, business_name, owner_name, phone, email, website,
    address, city, state, zip, services_array,
    2, false, 'landing_page'  -- Tier 2, unverified, from landing page
)
```

### **API ENDPOINTS NEEDED**

#### **Enhanced Contractor Account Creation**
```python
POST /api/contractors/create-from-landing
{
    "business_profile": {...},
    "contact_info": {...},
    "services": [...],
    "search_radius": 25,
    "source": "landing_page"
}

Response: {
    "contractor_id": "uuid",
    "temporary_credentials": {
        "email": "extracted@email.com", 
        "password": "generated_temp_password"
    },
    "onboarding_status": "account_created"
}
```

---

## 🔧 IMMEDIATE TECHNICAL FIXES NEEDED

### **1. Remove License Search**
```python
# In langgraph_nodes.py research_node - REMOVE:
license_result = await tools.search_contractor_licenses(company_name, "FL")

# Replace with:
license_data = {"success": False, "skipped": True}
```

### **2. Optimize Web Search (Remove Playwright)**
```python
# In coia/tools.py - web_search_company method
# REMOVE: Playwright extraction steps
# KEEP: Tavily API calls only
# RESULT: Should drop from 58s to ~5-10s
```

### **3. Progressive Tool Usage**
```python
# Instead of running all 5 tools at once in research_node:
# 1. Google Business search (immediate)
# 2. Wait for user confirmation  
# 3. THEN run web search (only after confirmation)
# 4. Build profile incrementally
# 5. Search bid cards when user specifies radius
```

---

## ✅ SUCCESS CRITERIA 

**Landing Page Endpoint Must:**
1. ✅ Respond in under 10 seconds for initial Google Business search
2. ✅ Have natural conversation flow with confirmation steps
3. ✅ Present InstaBids value proposition naturally
4. ✅ Show actual bid cards from database
5. ✅ Create real contractor accounts (contractors table)
6. ✅ Generate temporary login credentials
7. ✅ Guide users into contractor portal

**Conversation Must Feel:**
- Natural and consultative
- Focused on contractor pain points
- Excited about InstaBids solution
- Professional but approachable
- Results in completed contractor onboarding

---

This is the complete flow that needs to be implemented for the landing page endpoint to work exactly as described.