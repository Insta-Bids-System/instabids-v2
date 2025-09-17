# HOMEOWNER_ID MIGRATION - EXECUTABLE CHECKLIST
**Agent 6 (Codebase QA) - Step-by-Step Execution Guide**  
**Date**: August 13, 2025  
**Purpose**: Maintain context and verify each migration step systematically

## 🎯 **AGENT 6 CONTEXT PRESERVATION**

**I am Agent 6 (Codebase QA)** executing the homeowner_id → user_id migration based on combined research from Claude Code analysis + GPT-5 professional migration scripts.

**Key Context Stored in Cipher MCP**: Complete project overview, tool requirements, safety measures, and user approval for methodical execution.

---

## 📋 **PHASE 1: SAFE DATABASE MIGRATION**

### **Step 1.1: Pre-Migration Verification**
- [ ] **Action**: Verify current database state
- [ ] **Test**: 
```sql
-- Count current homeowner_id references
SELECT COUNT(*) as bid_cards_with_homeowner_id FROM bid_cards WHERE homeowner_id IS NOT NULL;
SELECT COUNT(*) as projects_with_homeowner_id FROM projects WHERE homeowner_id IS NOT NULL;
SELECT COUNT(*) as total_homeowners FROM homeowners;
```
- [ ] **Expected Result**: Numbers match expected data (should show current homeowner_id usage)
- [ ] **Verification**: Record baseline numbers for comparison
- [ ] **Checkpoint**: ✅ User approval to proceed

### **Step 1.2: Add user_id Columns**
- [ ] **Action**: Execute `01_add_user_id.sql`
- [ ] **Test**:
```sql
-- Verify user_id columns added
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'bid_cards' AND column_name = 'user_id';

SELECT column_name FROM information_schema.columns 
WHERE table_name = 'projects' AND column_name = 'user_id';

-- Verify indexes created
SELECT indexname FROM pg_indexes WHERE indexname LIKE 'idx_%_user_id';
```
- [ ] **Expected Result**: user_id columns exist, indexes created, all NULL initially
- [ ] **Verification**: All affected tables have user_id columns
- [ ] **Checkpoint**: ✅ User approval to proceed

### **Step 1.3: Backfill user_id Data**
- [ ] **Action**: Execute `02_backfill_user_id.sql`
- [ ] **Test**:
```sql
-- Verify no NULLs remain
SELECT COUNT(*) as null_user_ids FROM bid_cards WHERE user_id IS NULL;
SELECT COUNT(*) as null_user_ids FROM projects WHERE user_id IS NULL;

-- Verify data consistency (sample check)
SELECT p.id, p.homeowner_id, p.user_id, h.user_id as homeowner_user_id
FROM projects p 
JOIN homeowners h ON p.homeowner_id = h.id 
WHERE p.user_id != h.user_id
LIMIT 5;
```
- [ ] **Expected Result**: Zero NULL user_ids, zero inconsistencies
- [ ] **Verification**: Data correctly backfilled from homeowner_id sources
- [ ] **Checkpoint**: ✅ User approval to proceed

### **Step 1.4: Enforce NOT NULL Constraints**
- [ ] **Action**: Execute `03_enforce_not_null_and_constraints.sql`
- [ ] **Test**:
```sql
-- Verify NOT NULL constraints applied
SELECT is_nullable FROM information_schema.columns 
WHERE table_name = 'bid_cards' AND column_name = 'user_id';

-- Test constraint works (should fail)
-- INSERT INTO bid_cards (homeowner_id) VALUES (uuid_generate_v4());
```
- [ ] **Expected Result**: is_nullable = 'NO', test insert fails appropriately
- [ ] **Verification**: user_id now required on all tables
- [ ] **Checkpoint**: ✅ **PHASE 1 COMPLETE - SAFE TO PROCEED**

---

## 📋 **PHASE 2: CODE MIGRATION**

### **Step 2.1: PRIORITY 1 - Fix IRIS Agent (IMMEDIATE UNBLOCK)**

#### **Step 2.1a: Update homeowner_context.py**
- [ ] **Action**: Edit `adapters/homeowner_context.py`
- [ ] **Changes**: Remove homeowner_id conversion logic, use user_id directly
- [ ] **Test**:
```python
# Test IRIS context adapter
adapter = HomeownerContextAdapter()
context = adapter.get_unified_conversations(user_id="test-user-id")
# Should work without homeowner_id conversion
```
- [ ] **Expected Result**: No homeowner_id conversion errors
- [ ] **Verification**: IRIS adapter works with user_id directly

#### **Step 2.1b: Update IRIS Agent**
- [ ] **Action**: Edit `agents/iris/agent.py`
- [ ] **Changes**: Remove homeowner_id references, use user_id throughout
- [ ] **Test**:
```bash
# Test IRIS functionality
curl -X POST http://localhost:8008/api/iris/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user-id", "message": "test inspiration"}'
```
- [ ] **Expected Result**: IRIS responds without ID conversion errors
- [ ] **Verification**: IRIS agent fully functional
- [ ] **Checkpoint**: ✅ **IRIS FIXED - IMMEDIATE WIN ACHIEVED**

### **Step 2.2: PRIORITY 2 - Update Core Agents**

#### **Step 2.2a: Update CIA Agent**
- [ ] **Action**: Edit `agents/cia/agent.py`
- [ ] **Changes**: Use user_id in bid card creation, remove homeowner_id logic
- [ ] **Test**:
```python
# Test CIA bid card creation
result = cia_agent.handle_conversation(
    user_id="test-user-id",
    message="I need landscaping work done"
)
# Check bid card uses user_id
```
- [ ] **Expected Result**: Bid cards created with user_id, not homeowner_id
- [ ] **Verification**: CIA creates bid cards correctly with user_id

#### **Step 2.2b: Update JAA Agent**
- [ ] **Action**: Edit `agents/jaa/agent.py`
- [ ] **Changes**: Use user_id in bid card database operations
- [ ] **Test**:
```sql
-- After JAA creates bid card, verify user_id used
SELECT user_id, homeowner_id FROM bid_cards ORDER BY created_at DESC LIMIT 1;
```
- [ ] **Expected Result**: New bid cards have user_id populated correctly
- [ ] **Verification**: JAA agent updated to user_id system
- [ ] **Checkpoint**: ✅ Core agents migrated

### **Step 2.3: PRIORITY 3 - Update Critical API Routes**

#### **Step 2.3a: Update bid_card_api.py (11 references)**
- [ ] **Action**: Edit `routers/bid_card_api.py`
- [ ] **Changes**: Replace homeowner_id filters with user_id
- [ ] **Test**:
```bash
# Test bid card API endpoints
curl "http://localhost:8008/api/bid-cards?user_id=test-user-id"
```
- [ ] **Expected Result**: API returns bid cards filtered by user_id
- [ ] **Verification**: Bid card API works with user_id

#### **Step 2.3b: Update intelligent_messaging_api.py (12 references)**
- [ ] **Action**: Edit `routers/intelligent_messaging_api.py`
- [ ] **Changes**: Replace homeowner_id in message filters with user_id
- [ ] **Test**:
```bash
# Test messaging API
curl -X POST http://localhost:8008/api/messaging/send \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user-id", "message": "test message"}'
```
- [ ] **Expected Result**: Messages processed with user_id correctly
- [ ] **Verification**: Messaging API updated

#### **Step 2.3c: Update cia_routes.py (3 references)**
- [ ] **Action**: Edit `routers/cia_routes.py`
- [ ] **Changes**: Update CIA API endpoints to use user_id
- [ ] **Test**:
```bash
# Test CIA routes
curl -X POST http://localhost:8008/api/cia/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user-id", "message": "test conversation"}'
```
- [ ] **Expected Result**: CIA API works with user_id
- [ ] **Verification**: CIA routes updated
- [ ] **Checkpoint**: ✅ Critical API routes migrated

### **Step 2.4: PRIORITY 4 - Frontend Updates**

#### **Step 2.4a: Update TypeScript Types**
- [ ] **Action**: Edit `web/src/types/bidCard.ts` and related type files
- [ ] **Changes**: Replace homeowner_id with user_id in interfaces
- [ ] **Test**: TypeScript compilation should pass
- [ ] **Expected Result**: No TypeScript errors, clean compilation
- [ ] **Verification**: Frontend types updated

#### **Step 2.4b: Update API Client Functions**
- [ ] **Action**: Edit `web/src/services/api.ts`
- [ ] **Changes**: Update API calls to send user_id instead of homeowner_id
- [ ] **Test**: Frontend API calls should work
- [ ] **Expected Result**: Frontend communicates with backend using user_id
- [ ] **Verification**: API integration working
- [ ] **Checkpoint**: ✅ **PHASE 2 COMPLETE - ALL CODE MIGRATED**

---

## 📋 **PHASE 3: FINAL CLEANUP**

### **Step 3.1: Comprehensive Testing**
- [ ] **Action**: Run complete system test
- [ ] **Test**:
```bash
# Test end-to-end workflow
1. CIA conversation → bid card creation
2. IRIS inspiration board interaction  
3. Messaging system functionality
4. Frontend bid card display
```
- [ ] **Expected Result**: All systems work with user_id exclusively
- [ ] **Verification**: Complete functionality confirmed
- [ ] **Checkpoint**: ✅ User approval for final cleanup

### **Step 3.2: Remove homeowner_id Columns**
- [ ] **Action**: Execute `05_drop_homeowner_id_columns.sql`
- [ ] **Test**:
```sql
-- Verify homeowner_id columns removed
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'bid_cards' AND column_name = 'homeowner_id';
```
- [ ] **Expected Result**: No homeowner_id columns found
- [ ] **Verification**: Legacy columns removed
- [ ] **Checkpoint**: ✅ **BREAKING CHANGE APPLIED**

### **Step 3.3: Remove homeowners Table**
- [ ] **Action**: Execute `06_drop_homeowners_table.sql`
- [ ] **Test**:
```sql
-- Verify homeowners table removed
SELECT table_name FROM information_schema.tables 
WHERE table_name = 'homeowners';
```
- [ ] **Expected Result**: No homeowners table found
- [ ] **Verification**: Legacy table removed

### **Step 3.4: Update Security Policies**
- [ ] **Action**: Execute `07_policies_rls.sql`
- [ ] **Test**:
```sql
-- Verify RLS policies use user_id
SELECT policyname, cmd, qual FROM pg_policies 
WHERE tablename IN ('projects', 'bid_cards', 'inspiration_boards');
```
- [ ] **Expected Result**: Policies reference user_id, not homeowner_id
- [ ] **Verification**: Security policies updated
- [ ] **Checkpoint**: ✅ **PHASE 3 COMPLETE**

---

## 🧪 **FINAL SYSTEM VERIFICATION**

### **Complete End-to-End Test**
- [ ] **Test 1**: User registration → profile creation (user_id generated)
- [ ] **Test 2**: CIA conversation → bid card creation (uses user_id)
- [ ] **Test 3**: IRIS inspiration → board creation (uses user_id)
- [ ] **Test 4**: Messaging system → conversations (uses user_id)
- [ ] **Test 5**: Frontend display → all data shows correctly
- [ ] **Expected Result**: All systems work seamlessly with user_id
- [ ] **Verification**: Migration 100% successful

### **Performance Verification**
- [ ] **Test**: Query performance comparison
```sql
-- Before: Required JOIN
EXPLAIN ANALYZE SELECT * FROM bid_cards bc 
JOIN homeowners h ON bc.homeowner_id = h.id 
WHERE h.user_id = 'test-id';

-- After: Direct filter
EXPLAIN ANALYZE SELECT * FROM bid_cards 
WHERE user_id = 'test-id';
```
- [ ] **Expected Result**: Faster queries without JOINs
- [ ] **Verification**: Performance improved

---

## 🎯 **SUCCESS CRITERIA CHECKLIST**

- [ ] ✅ IRIS agent functionality restored (no more ID conversion errors)
- [ ] ✅ All agents use user_id exclusively (CIA, JAA, IRIS, Messaging)
- [ ] ✅ All API routes updated to user_id (15+ routers)
- [ ] ✅ Frontend components use user_id (TypeScript types updated)
- [ ] ✅ Zero homeowner_id references in codebase (372 references eliminated)
- [ ] ✅ Unified memory system continues working (confirmed unaffected)
- [ ] ✅ Database performance improved (no more JOIN operations)
- [ ] ✅ Complete system testing passed (end-to-end workflows)

---

## 🚨 **EMERGENCY ROLLBACK PROCEDURES**

### **Phase 1-2 Rollback (homeowner_id columns still exist)**
```sql
-- Revert to homeowner_id usage temporarily
-- Update application code to use homeowner_id columns
-- Both systems available for rollback
```

### **Phase 3 Rollback (homeowner_id removed - requires restoration)**
```sql
-- Re-run 01-03 scripts to restore dual system
-- Restore homeowner_id columns from backups
-- Update application code back to homeowner_id
```

---

## 📞 **CONTEXT RECOVERY COMMANDS**

**If I lose context, run these commands:**

1. **Read migration plan**: `C:\Users\Not John Or Justin\Documents\instabids\docs\HOMEOWNER_ID_ELIMINATION_COMPLETE_PLAN.md`

2. **Check current progress**: Use this checklist and mark completed items

3. **Query Cipher memory**:
```
mcp__cipher__ask_cipher: "What is the status of the homeowner_id migration project?"
```

4. **Verify database state**:
```sql
-- Check if user_id columns exist
SELECT column_name FROM information_schema.columns WHERE column_name = 'user_id';

-- Check if homeowner_id columns still exist  
SELECT column_name FROM information_schema.columns WHERE column_name = 'homeowner_id';
```

5. **Test system functionality**:
```bash
# Test IRIS agent
curl -X POST http://localhost:8008/api/iris/chat

# Test CIA agent
curl -X POST http://localhost:8008/api/cia/chat
```

**This checklist maintains complete context and provides step-by-step verification for safe, methodical migration execution.**