# CRITICAL MISMATCHES FOUND
## System Prompt vs Tool Definition vs Database

Generated: August 27, 2025

---

## 🚨 MAJOR PROBLEMS DISCOVERED

### 1. **WRONG SYSTEM PROMPT BEING REFERENCED**

The agent is using `OLD_SYSTEM_PROMPT` (12,289 chars with full business logic) but:
- `SYSTEM_PROMPT` (2,125 chars) mentions `update_bid_card` tool explicitly
- `OLD_SYSTEM_PROMPT` does NOT mention `update_bid_card` tool at all!

**Current Code (agent.py:419-423):**
```python
# Import OLD_SYSTEM_PROMPT which has all the business logic
from agents.cia.prompts import OLD_SYSTEM_PROMPT

# Use the FULL business logic prompt with 12 Key Data Points
base_prompt = OLD_SYSTEM_PROMPT  # This has group bidding, emergency handling, etc.
```

**Problem**: OLD_SYSTEM_PROMPT never tells the AI to use update_bid_card!

---

### 2. **TOOL DEFINITION vs DATABASE SCHEMA MISMATCHES**

#### Tool Has (19 fields):
```
✅ project_type → maps to primary_trade
✅ service_type → NEW FIELD
✅ project_description → maps to user_scope_notes  
✅ budget_context → NEW FIELD (not dollar amounts!)
✅ budget_range_min/max → in DB
✅ urgency_level → in DB
✅ estimated_timeline → in DB
✅ timeline_flexibility → NEW FIELD (boolean)
✅ zip_code → NOT IN DATABASE!
✅ eligible_for_group_bidding → NOT IN DATABASE!
✅ property_area → NOT IN DATABASE!
✅ room_location → NOT IN DATABASE!
✅ materials_specified → NOT IN DATABASE!
✅ special_requirements → NOT IN DATABASE!
✅ contractor_size_preference → NOT IN DATABASE!
✅ quality_expectations → NOT IN DATABASE!
✅ email_address → NOT IN DATABASE!
```

#### Database Has (from models):
```
✅ id, user_id, created_at, updated_at
✅ title → NOT IN TOOL!
✅ primary_trade → tool calls it project_type
✅ budget_range_min/max
✅ estimated_timeline
✅ urgency_level  
✅ user_scope_notes → tool calls it project_description
✅ ai_analysis
✅ completion_percentage
```

---

## 📊 THE CRITICAL MISMATCHES

### Missing from Database (11 fields!):
1. **service_type** - Critical enum field
2. **budget_context** - Research stage tracking
3. **timeline_flexibility** - Boolean for flexibility
4. **zip_code** - CRITICAL location field!
5. **eligible_for_group_bidding** - 15-25% savings feature!
6. **property_area** - Property type
7. **room_location** - Which room
8. **materials_specified** - Material preferences
9. **special_requirements** - Permits/HOA
10. **contractor_size_preference** - Matching criteria
11. **quality_expectations** - Quality level
12. **email_address** - Contact info

### Missing from Tool:
1. **title** - Project title field
2. **ai_analysis** - AI insights field

---

## 🔴 WHY IT'S "WORKING" BUT NOT REALLY

The system appears to work because:
1. The AI mentions group bidding in conversation (from OLD_SYSTEM_PROMPT)
2. BUT it's NOT saving group bidding eligibility to database!
3. The AI extracts fields but many aren't being saved
4. The tool is trying to save fields that don't exist in DB

**This explains why:**
- Tests show 6/8 checks passing (conversation mentions things)
- But database likely missing critical data
- Tool calls might be failing silently for non-existent fields

---

## ✅ REQUIRED FIXES

### Fix 1: Update System Prompt Reference
```python
# EITHER:
# Option A: Add tool instructions to OLD_SYSTEM_PROMPT
OLD_SYSTEM_PROMPT = """...[existing]...

IMPORTANT: Call the update_bid_card tool whenever you learn new project details!
"""

# OR Option B: Merge both prompts
base_prompt = OLD_SYSTEM_PROMPT + "\n\n" + SYSTEM_PROMPT
```

### Fix 2: Database Schema Updates
Need to add these columns to potential_bid_cards table:
```sql
ALTER TABLE potential_bid_cards ADD COLUMN service_type TEXT;
ALTER TABLE potential_bid_cards ADD COLUMN budget_context TEXT;
ALTER TABLE potential_bid_cards ADD COLUMN timeline_flexibility BOOLEAN;
ALTER TABLE potential_bid_cards ADD COLUMN zip_code TEXT;
ALTER TABLE potential_bid_cards ADD COLUMN eligible_for_group_bidding BOOLEAN;
ALTER TABLE potential_bid_cards ADD COLUMN property_area TEXT;
ALTER TABLE potential_bid_cards ADD COLUMN room_location TEXT;
ALTER TABLE potential_bid_cards ADD COLUMN materials_specified TEXT;
ALTER TABLE potential_bid_cards ADD COLUMN special_requirements TEXT;
ALTER TABLE potential_bid_cards ADD COLUMN contractor_size_preference TEXT;
ALTER TABLE potential_bid_cards ADD COLUMN quality_expectations TEXT;
ALTER TABLE potential_bid_cards ADD COLUMN email_address TEXT;
```

### Fix 3: Update Tool Definition
Add missing database fields:
```python
"title": {
    "type": "string",
    "description": "Project title"
}
```

---

## 🎯 SUMMARY

**The system is PARTIALLY working:**
- ✅ Business logic in conversation (from OLD_SYSTEM_PROMPT)
- ⚠️ Tool being called but prompt doesn't mention it
- ❌ Many extracted fields NOT saved to database
- ❌ Critical fields like zip_code, group_bidding not in DB

**This is why tests show good conversation but bid card might be incomplete!**