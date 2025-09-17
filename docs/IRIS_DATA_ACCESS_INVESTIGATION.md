# IRIS Agent Data Access Investigation
**Date**: August 12, 2025
**Purpose**: Complete documentation of what data IRIS automatically receives and uses

## 📊 Summary of Investigation

### **What IRIS Loads (6 Data Types)**
The IrisContextAdapter (`adapters/iris_context.py`) loads these 6 data types for every conversation:

1. **inspiration_boards** - From unified_conversation_memory (memory_type='inspiration_board')
2. **project_context** - From unified_conversations (entity_type='project')
3. **design_preferences** - From unified_conversation_memory (memory_type='design_preferences')
4. **previous_designs** - From unified_conversation_memory (memory_type='generated_design')
5. **conversations_from_other_agents** - From unified_conversations (CIA, HMA, CMA)
6. **photos_from_unified_system** - From unified_message_attachments

### **What IRIS Actually Uses (4 of 6)**
Analysis of `agents/iris/agent.py` shows IRIS only uses:

✅ **USES:**
- `inspiration_boards` - Lines 123-129
- `project_context` - Lines 132-137
- `design_preferences` - Lines 140-148
- `previous_designs` - Lines 151-153

❌ **DOESN'T USE:**
- `conversations_from_other_agents` - Loaded but never referenced
- `photos_from_unified_system` - Only used in retrieval method, not in responses

## 🔍 Database Investigation Results

### **Unified Conversations Data**
```sql
-- For users who have used IRIS:
- 67 IRIS conversations (design_inspiration)
- 48 project_setup conversations
- 3 agent_interaction conversations (CIA, IRIS, MESSAGING)
- 1 iris_inspiration conversation
```

### **Memory Types Stored**
```sql
-- Memory entries for IRIS users:
- 8 preference entries
- 7 fact entries
- 3 photo_reference entries
- 0 design_preferences entries (missing!)
- 0 inspiration_board entries (missing!)
```

### **Cross-Agent Conversations**
Most IRIS users have NO conversations from other agents:
- CIA conversations: 1 (agent_interaction type)
- Messaging conversations: 1 (agent_interaction type)
- HMA/CMA conversations: 0 (not found)
- Project setup: 48 (but minimal metadata)

## 🚨 Critical Findings

### **1. IRIS Context Bug (FIXED)**
- **Problem**: Was creating new conversations for every message
- **Fix Applied**: Modified `iris_chat_unified_fixed.py` to use `get_or_create_conversation_direct()`
- **Result**: Now maintains conversation context between messages ✅

### **2. Unused Data Loading**
IRIS loads but doesn't use:
- **conversations_from_other_agents** - 229-303 lines of code to load, never used
- **photos_from_unified_system** - 305-375 lines of code to load, minimally used

### **3. Missing Memory Types**
The database has NO:
- `design_preferences` memory entries (should be created by IRIS)
- `inspiration_board` memory entries (should track boards)
- `generated_design` memory entries (should track AI designs)

### **4. Limited Cross-Agent Integration**
- Most IRIS users have no CIA/Messaging conversations
- The `_get_conversations_from_other_agents` method loads empty data
- No real integration between agents despite the infrastructure

## 📈 What Actually Gets Loaded

### **Typical IRIS Session Data**
```python
{
    "inspiration_boards": [],  # Empty - no boards stored
    "project_context": {
        "project_available": False  # No projects linked
    },
    "design_preferences": {},  # Empty - not being saved
    "previous_designs": [],  # Empty - not being saved
    "conversations_from_other_agents": {
        "homeowner_conversations": [],  # Empty
        "messaging_conversations": [],  # Empty
        "project_conversations": []  # Some project_setup convos
    },
    "photos_from_unified_system": {
        "project_photos": [],
        "inspiration_photos": [],
        "message_attachments": []
    },
    "privacy_level": "homeowner_side_access"
}
```

## 🔧 Recommendations

### **1. Remove Unused Data Loading**
Remove from `IrisContextAdapter.get_inspiration_context()`:
- `_get_conversations_from_other_agents()` - Not used by IRIS
- Simplify `_get_photos_from_unified_system()` - Minimally used

### **2. Fix Memory Storage**
IRIS should actually save:
- Design preferences when discussed
- Inspiration board references
- Generated design concepts

### **3. Implement Cross-Agent Features**
If IRIS should use other agent data:
- Update `agent.py` to actually process `conversations_from_other_agents`
- Add logic to reference CIA project discussions
- Include messaging context in responses

### **4. Link Projects Properly**
- IRIS conversations should have `entity_id` = project_id
- This would enable proper project context loading

## 📝 Answer to User Question

**"What exactly is being automatically uploaded into the Iris agent when it begins to talk?"**

### **Current Reality:**
- **Almost nothing** - Most data structures return empty
- **No homeowner history** - Cross-agent conversations not linked
- **No saved preferences** - Memory types not being stored
- **No inspiration boards** - Despite infrastructure existing

### **What Should Be Happening:**
- User's design preferences from past conversations
- Photos from property documentation
- Context from CIA agent project discussions
- Previous inspiration boards and saved designs

### **Bottom Line:**
The infrastructure exists to provide rich context to IRIS, but:
1. The data isn't being saved properly
2. IRIS doesn't use most of what's loaded
3. Cross-agent integration is essentially non-functional

The system is **architecturally complete** but **functionally incomplete**.