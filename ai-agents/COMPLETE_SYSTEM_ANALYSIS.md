# COMPLETE CIA SYSTEM ANALYSIS
## The Truth About Prompts, Tools, and Database

Generated: August 27, 2025

---

## 🔍 THE CURRENT SITUATION

### 1. WHY ARE THERE 2 PROMPTS?

**SYSTEM_PROMPT** (2,125 chars):
- Created as "simplified" version
- HAS tool instructions: "Call update_bid_card AS SOON as you identify any project information"
- Focuses on extraction priorities
- Clean, direct, tool-focused

**OLD_SYSTEM_PROMPT** (12,289 chars):
- Original full business logic
- Has 12 Key Data Points system
- Has group bidding (15-25% savings)
- Has emergency handling
- NO TOOL INSTRUCTIONS AT ALL!

**WHAT'S BEING USED NOW:**
```python
# agent.py line 419-423
from agents.cia.prompts import OLD_SYSTEM_PROMPT
base_prompt = OLD_SYSTEM_PROMPT  # NO tool instructions!
```

**PROBLEM**: Using the prompt WITHOUT tool instructions but the tool still works because it's defined in the tools array!

---

## 📊 WHAT ACTUALLY EXISTS IN THE SYSTEM

### TOOL DEFINITION (agent.py)
19 fields defined in update_bid_card tool:
```
1. project_type → maps to primary_trade
2. service_type → Installation/Repair/Ongoing/etc
3. project_description → maps to user_scope_notes
4. budget_context → research stage
5. budget_range_min/max → dollar amounts
6. urgency_level → emergency/urgent/flexible
7. estimated_timeline → when needed
8. timeline_flexibility → boolean
9. zip_code → location
10. eligible_for_group_bidding → boolean
11. property_area → single family/condo
12. room_location → which room
13. materials_specified → preferences
14. special_requirements → permits/HOA
15. contractor_size_preference → small/large
16. quality_expectations → budget/premium
17. email_address → contact
```

### DATABASE REALITY CHECK
**SHOCKING DISCOVERY**: The potential_bid_cards table doesn't exist in the database!

```bash
# Checked database - NO potential_bid_cards table found!
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE '%bid%';
# Result: 0 rows
```

### HOW IT'S "WORKING" 
The PotentialBidCardManager (potential_bid_card_integration.py):
1. Maps tool fields to database fields
2. IGNORES fields that don't exist (lines 117-130)
3. Makes HTTP calls to backend endpoints
4. Backend probably creates/manages a different table structure

**Ignored fields** (not saved):
- property_type, property_size, current_condition
- location, location_context, contractor_requirements  
- urgency_reason, timeline_details
- uploaded_photos, photo_analyses
- phone_number

---

## 🎯 THE REAL MAPPING

### What OLD_SYSTEM_PROMPT Wants (12 Key Data Points):
1. Project Type ✅ → tool has it
2. Service Type ✅ → tool has it  
3. Project Description ✅ → tool has it
4. Budget Context ✅ → tool has it (NOT dollars!)
5. Timeline/Urgency ✅ → tool has it
6. Location ✅ → tool has it (zip_code)
7. Group Bidding ✅ → tool has it
8. Property Context ✅ → tool has it
9. Material Preferences ✅ → tool has it
10. Images/Photos ❌ → handled by IRIS
11. Special Requirements ✅ → tool has it
12. Intention Score ✅ → via contractor preferences

### What Tool Can Extract:
ALL 12 Key Data Points are covered!

### What Gets Saved:
UNKNOWN - depends on backend implementation since table doesn't exist in visible database

---

## ✅ THE SOLUTION: UNIFIED PROMPT

```python
# MERGE both prompts for complete functionality
UNIFIED_CIA_PROMPT = """You are Alex, a friendly and intelligent project assistant for InstaBids.

[Include all OLD_SYSTEM_PROMPT content for business logic...]

## TOOL USAGE INSTRUCTIONS
CRITICAL: Call the update_bid_card tool IMMEDIATELY when you learn ANY project information:
- Don't wait to collect everything
- Multiple calls are fine as you learn more  
- Update even partial information
- The user sees their bid card building in real-time!

When you identify project details, use the update_bid_card tool with these fields:
- project_type: What type of project (maps to primary_trade)
- service_type: Installation/Repair/Ongoing/Handyman/Appliance/Labor
- project_description: Detailed scope (maps to user_scope_notes)
- budget_context: Research stage NOT dollar amounts
- urgency_level: emergency/urgent/flexible/planning
- timeline_flexibility: Can timing be adjusted (boolean)
- zip_code: 5-digit zip code
- eligible_for_group_bidding: Good for neighbors (boolean)
[... rest of fields ...]

Remember: Every field you extract helps contractors provide better quotes!
"""
```

---

## 📝 SUMMARY OF ISSUES

1. **PROMPT CONFUSION**:
   - Using OLD_SYSTEM_PROMPT (no tool instructions)
   - Should merge both prompts for complete functionality

2. **DATABASE MYSTERY**:
   - potential_bid_cards table not visible in database
   - Tool maps fields but many get ignored
   - Backend handling storage differently

3. **FIELD MAPPING**:
   - Tool has all 12 Key Data Points ✅
   - But some fields ignored during save
   - Group bidding field exists but save status unknown

---

## 🚀 RECOMMENDED ACTIONS

1. **IMMEDIATE**: Create unified prompt combining business logic + tool instructions
2. **INVESTIGATE**: Where is bid card data actually stored?
3. **VERIFY**: Test actual database saves with real API calls
4. **FIX**: Ensure all critical fields (zip_code, group_bidding) are saved

The system IS extracting the right information but we need to verify it's actually being saved!