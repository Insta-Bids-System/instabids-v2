# Non-Unified Agents Migration Plan
**Generated:** August 12, 2025  
**Purpose:** Identify and migrate agents still using non-unified memory systems  
**Priority:** HIGH - Ensure ALL agents use only unified memory system

## 🚨 CRITICAL FINDING: AGENTS NOT USING UNIFIED MEMORY SYSTEM

Based on comprehensive code analysis, I've identified agents and systems that are NOT using the unified memory system as required.

---

## 📊 COMPLIANCE STATUS

### ✅ COMPLIANT AGENTS (Using Unified Memory)
1. **CIA Agent** (`agents/cia/agent.py`)
   - **Status**: ✅ FULLY COMPLIANT
   - **Implementation**: Uses `universal_session_manager` (line 16)
   - **Tables Used**: `unified_conversations`, `unified_messages`, `unified_conversation_memory`

2. **IRIS Agent** (`agents/iris/agent.py`) 
   - **Status**: ✅ FULLY COMPLIANT
   - **Implementation**: Uses `UnifiedMemoryManager` (line 37-49)
   - **Tables Used**: `unified_conversations`, `unified_messages`, `unified_conversation_memory`

3. **COIA Agent** (`agents/coia/persistent_memory.py`)
   - **Status**: ✅ FULLY COMPLIANT (Migrated)
   - **Implementation**: Uses unified conversation system (lines 115, 144, 197)
   - **Tables Used**: `unified_conversations`, `unified_messages`, `unified_conversation_memory`

### ❌ NON-COMPLIANT SYSTEMS (Still Using Legacy Tables)

#### 1. **Intelligent Messaging Agent** (`agents/intelligent_messaging_agent.py`)
- **Issues Found**:
  - Line 536: Uses `conversations` table instead of `unified_conversations`
  - Line 778: Uses `conversations` table for contractor data
- **Impact**: Messaging system not integrated with unified memory
- **Risk Level**: HIGH - Active messaging system

#### 2. **Multiple API Endpoints & Adapters**
- **Files with Legacy Usage**:
  - `adapters/homeowner_context.py:67` - Uses `agent_conversations`
  - `api/bid_cards_simple.py:260` - Uses `agent_conversations`  
  - `api/projects.py:136,292,330` - Uses `agent_conversations`
  - `routers/homeowner_routes.py:137` - Uses `agent_conversations`
  - `routers/monitoring_routes.py:63,138` - Uses `agent_conversations`

#### 3. **JAA Agent** (`agents/jaa/agent.py`)
- **Issues Found**:
  - No memory persistence implementation found
  - Thread ID tracking but no unified memory integration
- **Impact**: Job assessment conversations not preserved
- **Risk Level**: MEDIUM - Functional but non-persistent

---

## 🎯 MIGRATION PLAN

### **Phase 1: Critical Messaging System (Priority 1)**

#### Target: `agents/intelligent_messaging_agent.py`
**Current Issue:**
```python
# Line 536 - WRONG TABLE
conversations_response = supabase.table("conversations").select("*").eq("bid_card_id", bid_card_id).execute()

# Line 778 - WRONG TABLE
conversations = supabase.table("conversations").select("contractor_id, contractor_alias").eq(
```

**Required Changes:**
```python
# REPLACE WITH:
conversations_response = supabase.table("unified_conversations").select("*").contains("metadata", {"bid_card_id": bid_card_id}).execute()

conversations = supabase.table("unified_conversations").select("*").contains("metadata", {"contractor_id": contractor_id}).execute()
```

### **Phase 2: API Endpoints Migration (Priority 2)**

#### Target Files to Update:
1. **`adapters/homeowner_context.py:67`**
   ```python
   # CURRENT (WRONG):
   result = self.supabase.table("agent_conversations").select(...)
   
   # REPLACE WITH:
   result = self.supabase.table("unified_conversations").select("*").eq("created_by", user_id).execute()
   ```

2. **`api/bid_cards_simple.py:260`**
   ```python  
   # CURRENT (WRONG):
   conversations_result = supabase.table("agent_conversations").select("thread_id").eq("user_id", homeowner_id).execute()
   
   # REPLACE WITH:
   conversations_result = supabase.table("unified_conversations").select("*").eq("created_by", homeowner_id).execute()
   ```

3. **`api/projects.py` (3 locations: lines 136, 292, 330)**
   - Replace all `agent_conversations` table usage with `unified_conversations`
   - Update query patterns to use `created_by` instead of `user_id`

### **Phase 3: JAA Agent Memory Integration (Priority 3)**

#### Target: `agents/jaa/agent.py`
**Add Memory Persistence:**
```python
# ADD TO __init__ method:
from services.universal_session_manager import universal_session_manager

# ADD conversation persistence in handle_conversation method:
async def create_bid_card(self, state: IntelligentJAAState) -> IntelligentJAAState:
    # ... existing code ...
    
    # SAVE CONVERSATION TO UNIFIED MEMORY
    await universal_session_manager.save_conversation(
        user_id=state.conversation_data.get("user_id"),
        session_id=state.thread_id,
        agent_type="JAA",
        conversation_data=state.conversation_data,
        extracted_data=state.extracted_data
    )
    
    return state
```

### **Phase 4: Monitoring & Routes Update (Priority 4)**

#### Target Files:
- `routers/homeowner_routes.py:137`
- `routers/monitoring_routes.py:63,138`

**Changes Required:**
- Replace `agent_conversations` queries with `unified_conversations`
- Update filtering logic to use metadata fields
- Ensure monitoring works with unified system

---

## 🔍 VERIFICATION CHECKLIST

### Pre-Migration Verification:
- [ ] Backup current `conversations` and `agent_conversations` data
- [ ] Verify unified tables have all required fields
- [ ] Test unified API endpoints are functional
- [ ] Document data migration path for existing records

### Post-Migration Verification:
- [ ] All agents save to unified tables only
- [ ] No remaining references to `agent_conversations` table
- [ ] No remaining references to `conversations` table (non-unified)
- [ ] Cross-agent memory sharing works correctly
- [ ] Messaging system integrated with unified memory
- [ ] JAA conversations persist across sessions

---

## 🚨 DATA MIGRATION STRATEGY

### **Step 1: Legacy Data Preservation**
```sql
-- Backup existing data before migration
CREATE TABLE agent_conversations_backup AS SELECT * FROM agent_conversations;
CREATE TABLE conversations_backup AS SELECT * FROM conversations;
```

### **Step 2: Data Migration Scripts**
Create migration scripts to move existing data:
1. **Agent Conversations → Unified Conversations**
2. **Legacy Conversations → Unified Conversations**  
3. **Preserve all thread_id and session_id relationships**

### **Step 3: Gradual Migration**
- Implement dual-write (write to both old and new tables temporarily)
- Verify data consistency between systems
- Switch reads to unified tables
- Stop writes to legacy tables
- Remove legacy table dependencies

---

## 📋 IMPLEMENTATION TIMELINE

### **Week 1: Intelligent Messaging Agent**
- [ ] Update conversation table references
- [ ] Test messaging system with unified tables
- [ ] Verify bid card messaging integration

### **Week 2: API Endpoints**
- [ ] Update all homeowner context adapters
- [ ] Update bid card API endpoints
- [ ] Update project API endpoints
- [ ] Test all affected API routes

### **Week 3: JAA Agent Memory**
- [ ] Implement JAA unified memory integration
- [ ] Test job assessment conversation persistence
- [ ] Verify cross-agent data sharing

### **Week 4: Monitoring & Cleanup**  
- [ ] Update monitoring systems
- [ ] Remove all legacy table references
- [ ] Complete testing of unified system
- [ ] Documentation updates

---

## 🎯 SUCCESS CRITERIA

### **Mandatory Requirements:**
1. **Zero Legacy Table Usage**: No agent uses `agent_conversations` or `conversations` tables
2. **Full Unified Integration**: All agents write to and read from unified tables only
3. **Cross-Agent Compatibility**: All agents can access each other's conversation data
4. **Data Preservation**: No loss of existing conversation data during migration
5. **Performance Maintained**: No degradation in system performance

### **Testing Requirements:**
1. **End-to-End Testing**: Complete user journeys across all agents
2. **Cross-Agent Testing**: Verify agents can share conversation context
3. **Data Integrity Testing**: Verify all data migrates correctly
4. **Performance Testing**: Ensure unified system performs as well as legacy

---

## 📚 SUPPORTING DOCUMENTATION

### **Reference Documents:**
- `docs/meta/UnifiedMemoryMap.md` - Authoritative unified system documentation
- `docs/contractor_team/COIA_MIGRATION_INSTRUCTIONS.md` - Example migration pattern
- `docs/agent_6_central_docs/UNIFIED_MEMORY_SYSTEM_COMPLETE_MAP.md` - Complete system map

### **Key API Endpoints:**
- `POST /api/conversations/create` - Create unified conversations
- `POST /api/conversations/message` - Add messages to unified system
- `POST /api/conversations/memory` - Store agent memory in unified system

### **Database Tables:**
- `unified_conversations` - Master conversation records
- `unified_messages` - All conversation messages
- `unified_conversation_memory` - Agent memory and state
- `unified_conversation_participants` - Multi-party conversations

---

## ⚠️ CRITICAL WARNINGS

1. **DO NOT** start any new development using legacy tables (`agent_conversations`, `conversations`)
2. **DO NOT** extend functionality of non-unified agents before migration
3. **BACKUP ALL DATA** before starting migration process
4. **TEST THOROUGHLY** - unified memory system is critical infrastructure
5. **COORDINATE** with all agent teams during migration to avoid conflicts

---

**This migration plan ensures ALL agents use ONLY the unified memory system as originally intended. The mixed system approach creates data fragmentation and prevents proper cross-agent collaboration.**