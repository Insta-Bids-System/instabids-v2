# Complete File Mapping - Contractor Search & Selection System
**Generated**: January 13, 2025
**Purpose**: Comprehensive mapping of all files involved in contractor discovery, selection, and campaign creation

## 🎯 CORE ORCHESTRATION FILES

### **1. Main Orchestrator**
**File**: `ai-agents/agents/orchestration/enhanced_campaign_orchestrator_radius_fixed.py`
- **MAIN FILE** - Mathematical calculations, contractor selection logic, Google Maps integration
- **Lines 232-295**: Sequential tier calculation with actual response rates
- **Lines 275-282**: Google Maps search term generation (NEEDS LLM ENHANCEMENT)
- **Lines 517-523**: Campaign creation after contractor selection
- **Lines 468-485**: Mathematical response rate calculation logic

### **2. Supporting Orchestration**
**File**: `ai-agents/agents/orchestration/timing_probability_engine.py`
- Mathematical response rate calculations (lines 232-295)
- Tier 1 (90%), Tier 2 (50%), Tier 3 (33%) response rate logic
- Sequential tier processing: Calculate Tier 1 first, then Tier 2, then Tier 3

**File**: `ai-agents/agents/orchestration/check_in_manager.py`
- Campaign monitoring and escalation logic
- 25%, 50%, 75% timeline check-ins
- Auto-escalation when insufficient responses

---

## 🔍 CONTRACTOR DISCOVERY FILES

### **3. Tier System Implementation**
**File**: `ai-agents/agents/cda/agent.py`
- Main CDA agent that calls tier systems
- Coordinates all tier searches sequentially

**File**: `ai-agents/agents/cda/tier1_matcher_v2.py`
- Tier 1 contractor matching (official platform contractors)
- Query: `contractors` table WHERE `tier = 1`
- Response rate: 90%

**File**: `ai-agents/agents/cda/tier2_reengagement.py` ⭐ **TIER 2 DEFINITION**
- **Definition**: Contractors contacted in last 6 months who didn't permanently decline
- **Source**: `contractor_outreach_attempts` table
- **Storage**: `contractor_leads` table (49 fields)
- **Response Rate**: 50% (higher than Tier 3 due to previous contact)
- **Query Logic**: Lines 25-50
```sql
SELECT * FROM contractor_outreach_attempts 
WHERE contacted_date > (NOW() - INTERVAL '6 months')
  AND response_status != 'permanently_declined'
  AND project_match_score > 0.7
  AND contractor within radius_miles of project location
```

**File**: `ai-agents/agents/cda/web_search_agent.py`
- Tier 3 web search logic (legacy - now uses Google Maps)

### **4. Geographic Filtering** ⭐ **CRITICAL**
**File**: `ai-agents/utils/radius_search_fixed.py`
- **15-mile radius constraint** - Hard-coded geographic limitation
- Uses haversine distance calculation for filtering
- **NO ZIP CODE EXPANSION** - Uses only bid card ZIP
- **NO RADIUS EXPANSION** - Does NOT expand if insufficient contractors
- Functions: `get_zip_coordinates()`, `filter_by_radius()`, `calculate_distance_miles()`

---

## 🗄️ DATABASE INTEGRATION FILES

### **5. Core Database Handler**
**File**: `ai-agents/database_simple.py`
- Main database connection and operations
- All Supabase table access goes through this file

### **6. Contractor Context Management**
**File**: `ai-agents/adapters/contractor_context.py`
- Contractor data handling between `contractors` and `contractor_leads` tables
- Table switching logic for unified contractor access

**File**: `ai-agents/adapters/lightweight_contractor_context.py`
- Simplified contractor operations for performance

---

## 🌐 GOOGLE MAPS INTEGRATION FILES

### **7. Google Business Search** ⭐ **GOOGLE MAPS API**
**File**: `ai-agents/agents/eaa/google_business_research_tool.py`
- **Contains actual Google Places API calls**
- Business discovery tool used for Tier 3 contractor search
- Function: `search_google_business(company_name, location)`
- Used by enhanced_campaign_orchestrator_radius_fixed.py lines 295-298

**Current Search Logic** (NEEDS LLM ENHANCEMENT):
```python
# Hardcoded search terms - NO AI decision making
search_variations = [
    f"{project_type}",           # "plumbing"
    f"{project_type} repair",    # "plumbing repair" 
    f"{project_type} service",   # "plumbing service"
    f"{project_type} contractor", # "plumbing contractor"
    f"emergency {project_type}",  # "emergency plumbing"
    f"{project_type} near me"    # "plumbing near me"
]
```

---

## 🏗️ CAMPAIGN MANAGEMENT FILES

### **8. Campaign Creation**
**File**: `ai-agents/agents/orchestration/campaign_orchestrator.py`
- Campaign creation and database operations
- Creates records in `outreach_campaigns` table
- Links contractors to campaigns via `campaign_contractors` table

### **9. Outreach Execution**
**File**: `ai-agents/agents/eaa/agent.py`
- Email outreach agent
- Reads from `campaign_contractors` table
- Creates `contractor_outreach_attempts` records

**File**: `ai-agents/agents/wfa/agent.py`
- Website form automation agent
- Handles website form submissions for contractors with websites

---

## 📊 API ENDPOINTS FILES

### **10. API Routes**
**File**: `ai-agents/routers/contractor_management_api.py`
- Contractor management endpoints
- GET `/api/contractor-management/contractors` - List with filtering
- GET `/api/contractor-management/contractors/{id}` - Detailed view

**File**: `ai-agents/routers/campaign_routes.py`
- Campaign creation and monitoring APIs

**File**: `ai-agents/main.py`
- All API endpoints registered here
- Main FastAPI application on port 8008

---

## 🧪 TESTING FILES

### **11. Test Files**
**File**: `ai-agents/test_end_to_end_clean.py` ⭐ **MAIN TEST**
- Complete system testing of entire contractor pipeline
- Tests CIA → JAA → Enhanced Orchestrator → EAA → WFA

**File**: `ai-agents/test_enhanced_orchestrator_complete.py`
- Orchestrator-specific testing
- Mathematical calculation validation

**File**: `ai-agents/test_timing_system_complete.py`
- Mathematical calculations testing
- Response rate validation

---

## 📋 CONFIGURATION & MAPPING FILES

### **12. Project Type Mappings**
**Database Tables** (not files, but critical):
- `project_types` - Project definitions
- `contractor_types` - Contractor categories  
- `project_type_contractor_mappings` - Project→Contractor type mappings

**Used in**: `enhanced_campaign_orchestrator_radius_fixed.py:224-248`
- Function: `_get_valid_contractor_types()`
- Maps project types to valid contractor specialties

---

## 🗂️ DATABASE SCHEMA STRUCTURE

### **13. Core Database Tables Involved**

**CONTRACTOR STORAGE:**
- `contractors` (17 fields) - **Tier 1 contractors** - Official platform users
- `contractor_leads` (49 fields) - **Tier 2 & Tier 3 contractors** - Discovery results
- `potential_contractors` - Cached Google Maps discovery results

**CAMPAIGN MANAGEMENT:**
- `outreach_campaigns` - Campaign creation and management
- `campaign_contractors` - Contractor-to-campaign mapping table
- `campaign_check_ins` - Progress monitoring at 25%, 50%, 75%

**OUTREACH TRACKING:**
- `contractor_outreach_attempts` - All email/form/SMS outreach records
- `contractor_responses` - Contractor replies and engagement
- `contractor_engagement_summary` - Aggregated response metrics

**PROJECT MAPPINGS:**
- `project_types` - Project definitions
- `contractor_types` - Contractor categories
- `project_type_contractor_mappings` - Project→Contractor mappings

---

## 📁 ARCHIVED/LEGACY FILES (Referenced but not active)

### **14. Legacy Contractor Discovery**
**File**: `ai-agents/agents/cda/archive/agent_v2_optimized.py`
- Old CDA implementation (archived)

**File**: `ai-agents/agents/cda/archive/tier2_reengagement_v2.py`
- Old Tier 2 logic (archived)

**File**: `ai-agents/agents/cda/service_specific_matcher.py`
- Legacy matching logic (may still be referenced)

---

## 🎯 KEY FILE INTERACTIONS & FLOW

### **Primary Execution Flow:**
```
1. enhanced_campaign_orchestrator_radius_fixed.py → ORCHESTRATES EVERYTHING
   ↓
2. timing_probability_engine.py → Mathematical calculations (need 12-13 contractors)
   ↓
3. tier1_matcher_v2.py → Database Tier 1 search (contractors table)
   ↓
4. tier2_reengagement.py → Previous contacts search (contractor_outreach_attempts)
   ↓
5. google_business_research_tool.py → Google Maps API search (6 search variations)
   ↓
6. radius_search_fixed.py → 15-mile geographic filtering (haversine distance)
   ↓
7. campaign_orchestrator.py → Campaign creation (outreach_campaigns table)
   ↓
8. database_simple.py → All database operations
```

### **Critical Dependencies:**
- **Google Maps**: `google_business_research_tool.py` contains actual Google Places API calls
- **Geographic**: `radius_search_fixed.py` handles ALL 15-mile radius filtering
- **Mathematical**: `timing_probability_engine.py` calculates contractor quantities needed
- **Database**: `database_simple.py` connects to all contractor tables
- **Tier Definitions**: `tier2_reengagement.py` defines what Tier 2 contractors are

---

## 🚨 CRITICAL ISSUES IDENTIFIED

### **1. Google Search Logic Too Simple**
**Location**: `enhanced_campaign_orchestrator_radius_fixed.py:275-282`
**Current**: 6 hardcoded search term patterns
**Needed**: LLM to intelligently generate search terms based on:
- Project description specifics
- Local market terminology  
- Urgency level
- Previous search success rates

### **2. No Geographic Expansion**
**Location**: `radius_search_fixed.py`
**Issue**: System does NOT expand search if insufficient contractors found
**Current**: Hard 15-mile radius, single ZIP code
**Needed**: Intelligent radius expansion or multi-ZIP search

### **3. Selection → Campaign Flow**
**After Selection**:
1. Selected contractors → `campaign_contractors` table
2. Linked to `bid_card_id` via `outreach_campaigns`
3. Triggers EAA/WFA agents for automated outreach
4. Creates `contractor_outreach_attempts` records for tracking

---

## 📋 SUMMARY

**Total Files Involved**: 15+ core files across 6 different directories
**Main Orchestration**: `enhanced_campaign_orchestrator_radius_fixed.py`
**Critical Dependencies**: Google Maps API, Radius filtering, Mathematical calculations
**Database Tables**: 10+ tables involved in contractor lifecycle
**Key Enhancement Needed**: Google Maps search term generation via LLM

This system correctly calculates needing 12-13 contractors for 4 bids but needs enhancement in Google Maps search intelligence and geographic expansion logic.