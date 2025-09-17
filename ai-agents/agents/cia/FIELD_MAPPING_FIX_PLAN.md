# CIA Agent Field Mapping Fix Plan
**Created**: December 2024  
**Purpose**: Complete plan to fix broken field mappings between CIA tools and database  
**Critical Issue**: Tool 1 field mappings don't match actual database columns

## 🔴 CURRENT PROBLEMS IDENTIFIED

### Problem 1: Broken Field Mappings
- **17 fields** defined in Tool 1 (`update_bid_card`)
- **24+ mappings** in `potential_bid_card_integration.py`
- Many mappings point to **non-existent columns**
- Critical fields have **NO mappings at all**

### Problem 2: Wrong Column Names
| Tool Sends | Mapping Tries | Database Actually Has |
|------------|---------------|----------------------|
| `budget_min` | `budget_range_min` | `budget_min` ✅ |
| `budget_max` | `budget_range_max` | `budget_max` ✅ |
| `description` | `user_scope_notes` | `description` ✅ |
| `location_zip` | `zip_code` | `location_zip` ✅ |

### Problem 3: Missing Critical Mappings
These fields are extracted but CAN'T BE SAVED:
- `title` - REQUIRED field with no mapping
- `description` - REQUIRED field with wrong mapping
- `location_zip` - REQUIRED field with wrong mapping
- `urgency_level` - REQUIRED field with no mapping
- `contractor_count_needed` - REQUIRED field with no mapping

---

## 🎯 THE TWO-TOOL SYSTEM EXPLAINED

### Tool 1: `update_bid_card` (BROKEN - Needs Fix)
**Purpose**: Extract basic project information from conversation  
**Location**: `ai-agents/agents/cia/agent.py` (lines 44-93)  
**Fields**: 17 fields including title, description, location, budget, timeline  
**Problem**: Field mappings don't match database columns

### Tool 2: `categorize_project` (WORKING - Critical System)
**Purpose**: Classify project type and determine contractor types  
**Location**: `ai-agents/agents/project_categorization/`  
**Function**: Uses GPT-4o to match project to 1 of 200+ project types  
**Output**: `project_type_id` and `contractor_type_ids` array  
**Status**: ✅ WORKING PERFECTLY - This is why system still functions!

---

## 📁 FILES THAT NEED CHANGES

### 1. `ai-agents/agents/cia/potential_bid_card_integration.py`
**Lines to Change**: 59-127  
**Current Problem**: Wrong field mappings and ignored fields list  
**Fix Required**: Update field_mapping dictionary to match actual database columns

### 2. `ai-agents/agents/cia/agent.py`
**Lines to Change**: 44-93 (tool definition)  
**Current Problem**: Missing some important fields in tool definition  
**Fix Required**: Add missing fields that exist in database

### 3. `ai-agents/agents/cia/UNIFIED_PROMPT_FINAL.py`
**Lines to Change**: Field name references throughout  
**Current Problem**: Prompt uses inconsistent field names  
**Fix Required**: Update field names to match tool definition

### 4. `ai-agents/agents/cia/tool_handler.py` (CREATE NEW)
**Current Problem**: File doesn't exist but is imported  
**Fix Required**: Create this file to handle tool calls properly

---

## 🔧 DETAILED FIX IMPLEMENTATION

### FIX 1: Update Field Mappings
**File**: `potential_bid_card_integration.py`

```python
# REPLACE lines 59-111 with:
field_mapping = {
    # DIRECT MAPPINGS (no translation needed)
    "title": "title",
    "description": "description",
    "location_zip": "location_zip",
    "location_city": "location_city",
    "location_state": "location_state",
    "urgency_level": "urgency_level",
    "contractor_count_needed": "contractor_count_needed",
    "room_location": "room_location",
    "property_area": "property_area",
    "budget_min": "budget_min",  # FIXED: removed "range" prefix
    "budget_max": "budget_max",  # FIXED: removed "range" prefix
    "budget_context": "budget_context",
    "service_type": "service_type",
    "estimated_timeline": "estimated_timeline",
    "contractor_size_preference": "contractor_size_preference",
    "materials_specified": "materials_specified",
    "special_requirements": "special_requirements",
    "eligible_for_group_bidding": "eligible_for_group_bidding",
    "timeline_flexibility": "timeline_flexibility",
    "quality_expectations": "quality_expectations",
    "email_address": "email_address",
    "phone_number": "phone_number",
    "project_complexity": "project_complexity",
    "primary_trade": "primary_trade",
    "secondary_trades": "secondary_trades",
    "service_complexity": "service_complexity",
    "trade_count": "trade_count",
    "bid_collection_deadline": "bid_collection_deadline",
    "project_completion_deadline": "project_completion_deadline",
    "deadline_hard": "deadline_hard",
    "deadline_context": "deadline_context"
}

# DELETE lines 113-127 (ignored_fields section)
# REPLACE with validation against actual database columns:

# Valid database columns (from Supabase verification)
VALID_DB_COLUMNS = {
    "title", "description", "location_zip", "location_city", "location_state",
    "urgency_level", "contractor_count_needed", "room_location", "property_area",
    "budget_min", "budget_max", "budget_context", "service_type",
    "estimated_timeline", "contractor_size_preference", "materials_specified",
    "special_requirements", "eligible_for_group_bidding", "timeline_flexibility",
    "quality_expectations", "email_address", "phone_number", "primary_trade",
    "secondary_trades", "project_complexity", "service_complexity", "trade_count",
    "bid_collection_deadline", "project_completion_deadline", "deadline_hard",
    "deadline_context", "project_type", "contractor_type_ids"
}
```

### FIX 2: Update Tool Definition
**File**: `agent.py` (lines 44-93)

Add these missing fields to the tool properties:
```python
# ADD after line 89 (before closing the properties object):
"phone_number": {
    "type": "string", 
    "description": "Contact phone number if provided"
},
"property_area": {
    "type": "string",
    "description": "Type of property (residential, commercial, apartment, etc.)"
},
"timeline_flexibility": {
    "type": "string",
    "enum": ["flexible", "somewhat_flexible", "strict"],
    "description": "How flexible the timeline is"
},
"quality_expectations": {
    "type": "string",
    "enum": ["basic", "standard", "premium", "luxury"],
    "description": "Quality level expected for the project"
},
"email_address": {
    "type": "string",
    "description": "Contact email address if provided"
}
```

### FIX 3: Create Missing Tool Handler
**File**: `tool_handler.py` (NEW FILE)

```python
"""
CIA Tool Handler
Handles tool calls from the CIA agent
"""

import logging
from typing import Dict, Any
from .potential_bid_card_integration import PotentialBidCardManager

logger = logging.getLogger(__name__)

class CIAToolHandler:
    """Handles CIA agent tool calls"""
    
    def __init__(self):
        self.bid_card_manager = PotentialBidCardManager()
    
    async def handle_update_bid_card(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle update_bid_card tool call
        
        Args:
            args: Tool call arguments including fields to update
            
        Returns:
            Result dictionary with success status
        """
        try:
            bid_card_id = args.get('bid_card_id')
            user_id = args.get('user_id')
            session_id = args.get('session_id')
            
            if not bid_card_id:
                # Create new bid card if needed
                bid_card_id = await self.bid_card_manager.create_potential_bid_card(
                    conversation_id=session_id,
                    session_id=session_id,
                    user_id=user_id
                )
            
            # Update fields
            updated_count = 0
            for field_name, field_value in args.items():
                if field_name not in ['bid_card_id', 'user_id', 'session_id']:
                    success = await self.bid_card_manager.update_bid_card_field(
                        bid_card_id=bid_card_id,
                        field_name=field_name,
                        field_value=field_value
                    )
                    if success:
                        updated_count += 1
            
            return {
                "success": True,
                "bid_card_id": bid_card_id,
                "fields_updated": updated_count,
                "message": f"Updated {updated_count} fields in bid card"
            }
            
        except Exception as e:
            logger.error(f"Error handling update_bid_card: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update bid card"
            }
```

---

## 📋 IMPLEMENTATION STEPS

### Step 1: Fix Field Mappings (PRIORITY 1)
1. Open `potential_bid_card_integration.py`
2. Replace field_mapping dictionary (lines 59-111)
3. Delete ignored_fields section (lines 113-127)
4. Add VALID_DB_COLUMNS set for validation

### Step 2: Update Tool Definition (PRIORITY 2)
1. Open `agent.py`
2. Add missing field definitions to tool properties
3. Ensure all fields match database column names

### Step 3: Create Tool Handler (PRIORITY 3)
1. Create new file `tool_handler.py`
2. Implement CIAToolHandler class
3. Test imports in `cia_routes_unified.py`

### Step 4: Test Complete Flow
1. Test Tool 1 field extraction and saving
2. Verify Tool 2 categorization still works
3. Check database for correct field values
4. Validate bid card conversion process

---

## ✅ SUCCESS CRITERIA

After implementing these fixes:
1. All 17 tool fields should save correctly to database
2. No more "budget_range_min" errors
3. Critical fields (title, description, location_zip) save properly
4. Tool 2 (categorize_project) continues working
5. Bid cards have complete information for contractor matching

---

## 🎯 WHY THIS MATTERS

**Current State**: Tool 2 (categorization) is saving the system by correctly classifying projects, but Tool 1 is losing critical project details due to broken mappings.

**After Fix**: Both tools work together perfectly:
- Tool 1: Saves all project details correctly
- Tool 2: Classifies project type for contractor matching
- Result: Complete bid cards with all information needed

---

## 📊 TESTING CHECKLIST

- [ ] Field mapping changes implemented
- [ ] Tool definition updated with missing fields
- [ ] Tool handler created and imported
- [ ] Test conversation extracts all fields
- [ ] Database shows correct field values
- [ ] Categorization tool still works
- [ ] Bid card conversion successful
- [ ] Contractor matching uses correct data

---

**END OF FIX PLAN**