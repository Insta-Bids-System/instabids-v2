# Homeowner ID to User ID Migration Plan
**Created**: January 13, 2025  
**Purpose**: Complete plan for migrating all homeowner_id references to user_id
**Scope**: 372+ references across 65+ files requiring updates

## 🎯 EXECUTIVE SUMMARY

**User Request**: "I'm not worried about backfilling any information... if you just changed it, won't it automatically work if the endpoints looking for it are changed?"

**Migration Strategy**: Simple code changes without data migration - change all homeowner_id references to user_id across the codebase and let the system work with existing data.

**Key Finding**: Found 372+ homeowner_id references across 65+ files in Python backend, TypeScript frontend, and test files.

---

## 📊 MIGRATION SCOPE ANALYSIS

### **🔍 Search Results Summary**
```
Python Files: ~200 references across 35+ files
TypeScript Files: ~150 references across 25+ files  
Test Files: ~22 references across 8+ files
Total: 372+ references across 65+ files
```

### **Critical Files for IRIS Agent (Priority 1)**
- `ai-agents/adapters/iris_context.py:150` - Fallback query using homeowner_id
- `ai-agents/adapters/homeowner_context.py:121-144` - Core adapter functions
- `web/src/types/bidCard.ts` - TypeScript interface definitions
- `web/src/contexts/HomeownerContext.tsx` - Frontend context provider

---

## 🗂️ COMPLETE FILE INVENTORY

### **🐍 PYTHON BACKEND FILES (Priority 1-2)**

#### **Core Adapters & Context (IRIS Critical)**
```
ai-agents/adapters/homeowner_context.py (Lines 121-144)
  - get_projects(homeowner_id: str)
  - get_bid_cards(homeowner_id: str)
  - get_user_memories(homeowner_id: str)

ai-agents/adapters/iris_context.py (Line 150)
  - Legacy fallback: eq("homeowner_id", user_id)
```

#### **API Routers & Endpoints**
```
ai-agents/routers/admin_search_api.py
  - get_bid_cards_by_homeowner()
  - search_homeowners()
  - Multiple homeowner_id filters

ai-agents/routers/cia_routes.py
  - 10+ references to homeowner_id in bid card creation
  - User context and project management

ai-agents/routers/contractor_proposals_api.py
  - Proposal filtering by homeowner_id
  - Access control logic

ai-agents/routers/unified_conversation_api.py
  - Conversation ownership checks
  - User permission validation

ai-agents/routers/bid_card_api.py
  - Bid card ownership and filtering
  - CRUD operations with homeowner_id

ai-agents/routers/jaa_routes.py
  - Job assessment with homeowner context
  - Bid card generation logic

ai-agents/routers/cia_potential_bid_cards.py (Lines 100-104)
  - homeowner_result = db.client.table("homeowners").select("id").eq("user_id", request.user_id)
  - potential_bid_card_data["homeowner_id"] = homeowner_result.data[0]["id"]
```

#### **Utility & Helper Files**
```
ai-agents/bid_card_utils.py
  - create_bid_card_with_defaults(homeowner_id)
  - Utility functions for bid card creation

ai-agents/database_simple.py  
  - Database helper functions
  - Query building with homeowner_id

ai-agents/project_utils.py
  - Project management utilities
  - homeowner_id associations
```

#### **Test Files**
```
ai-agents/test_*.py (Multiple files)
  - test_cia_claude_extraction.py
  - test_complete_bid_submission_workflow.py
  - test_*_api.py files
  - All contain homeowner_id test data
```

### **⚛️ TYPESCRIPT FRONTEND FILES (Priority 2)**

#### **Type Definitions**
```
web/src/types/bidCard.ts
  - interface BidCard { homeowner_id: string; }
  - interface BidCardResponse { homeowner_id: string; }

web/src/types/index.ts
  - Export/import of homeowner_id types
  - Shared interface definitions
```

#### **React Contexts & Providers**
```
web/src/contexts/HomeownerContext.tsx
  - homeowner_id state management
  - Context provider for homeowner data

web/src/contexts/BidCardContext.tsx
  - Bid card state with homeowner_id references
  - Context hooks and providers
```

#### **Components & Pages**
```
web/src/components/admin/
  - AdminDashboard.tsx - homeowner_id in admin views
  - BidCardManagement.tsx - homeowner filtering
  - ContractorManagement.tsx - homeowner associations

web/src/components/bidcards/
  - BidCardList.tsx - homeowner_id filtering
  - BidCardDetail.tsx - homeowner ownership checks
  - BidCardForm.tsx - homeowner_id in form data

web/src/components/messaging/
  - MessagingInterface.tsx - homeowner_id in messaging
  - MessageThread.tsx - homeowner context

web/src/pages/
  - HomeownerDashboard.tsx - core homeowner functionality
  - BidCardPage.tsx - homeowner_id route parameters
  - AdminPage.tsx - homeowner management interface
```

#### **API & Services**
```
web/src/services/api.ts
  - API calls with homeowner_id parameters
  - Request/response handling

web/src/hooks/
  - useHomeowner.ts - homeowner_id hooks
  - useBidCards.ts - homeowner_id dependencies
```

---

## 🗺️ MIGRATION EXECUTION PLAN

### **Phase 1: Database Schema Changes (Optional)**
```sql
-- Add user_id columns to tables that only have homeowner_id
-- NOTE: User says "not worried about backfilling" so this may be skippable

-- Tables that may need user_id columns added:
-- bid_cards, projects, user_memories, etc.
-- Check existing schema first
```

### **Phase 2: Core Backend Changes (Priority 1)**

#### **Step 2.1: Adapter Layer (IRIS Critical)**
```python
# ai-agents/adapters/iris_context.py:150
# CHANGE FROM:
result = self.supabase.table("projects").select("*").eq("id", project_id).eq("homeowner_id", user_id).execute()

# CHANGE TO:
result = self.supabase.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()
```

```python
# ai-agents/adapters/homeowner_context.py:121-144
# CHANGE ALL FUNCTIONS:
def get_projects(self, user_id: str) -> List[Dict[str, Any]]:  # was homeowner_id
    result = self.supabase.table("projects").select("*").eq("user_id", user_id).execute()  # was homeowner_id

def get_bid_cards(self, user_id: str) -> List[Dict[str, Any]]:  # was homeowner_id  
    result = self.supabase.table("bid_cards").select("*").eq("user_id", user_id).execute()  # was homeowner_id
```

#### **Step 2.2: API Routes (Critical for All Agents)**
```python
# ai-agents/routers/cia_potential_bid_cards.py:100-104
# CHANGE FROM:
homeowner_result = db.client.table("homeowners").select("id").eq("user_id", request.user_id)
if homeowner_result.data:
    potential_bid_card_data["homeowner_id"] = homeowner_result.data[0]["id"]

# CHANGE TO:
potential_bid_card_data["user_id"] = request.user_id
```

#### **Step 2.3: Database Operations**
- Update all Supabase queries from `.eq("homeowner_id", ...)` to `.eq("user_id", ...)`  
- Update all dictionary keys from `"homeowner_id"` to `"user_id"`
- Update all function parameters from `homeowner_id: str` to `user_id: str`

### **Phase 3: Frontend TypeScript Changes (Priority 2)**

#### **Step 3.1: Type Definitions**
```typescript
// web/src/types/bidCard.ts
// CHANGE FROM:
interface BidCard {
  homeowner_id: string;
  // ...
}

// CHANGE TO:
interface BidCard {
  user_id: string;
  // ...
}
```

#### **Step 3.2: React Components**
```typescript
// Update all props, state, and API calls
// CHANGE FROM: homeowner_id
// CHANGE TO: user_id

// Update API calls
const response = await api.get(`/bid-cards?user_id=${userId}`);  // was homeowner_id
```

### **Phase 4: Test File Updates (Priority 3)**
```python
# Update all test files to use user_id instead of homeowner_id
# Search and replace in all test_*.py files
# Update test data objects and assertions
```

---

## 🔧 IMPLEMENTATION STRATEGY

### **Systematic Search & Replace Pattern**

#### **Python Files:**
```python
# Function signatures
homeowner_id: str → user_id: str

# Database queries  
.eq("homeowner_id", value) → .eq("user_id", value)
.filter("homeowner_id", "eq", value) → .filter("user_id", "eq", value)

# Dictionary keys
["homeowner_id"] → ["user_id"]
{"homeowner_id": value} → {"user_id": value}

# Variable names
homeowner_id = → user_id =
```

#### **TypeScript Files:**
```typescript
// Interface properties
homeowner_id: string → user_id: string

// Object properties
homeowerId → userId
homeowner_id → user_id

// API parameters
?homeowner_id= → ?user_id=
```

### **Validation Strategy**
1. **File-by-file verification** after each change
2. **Test after each major component** (adapters, routers, types)
3. **IRIS agent testing** after adapter changes
4. **End-to-end testing** after all changes

---

## ⚠️ RISK MITIGATION

### **Potential Issues**
1. **Database schema mismatches** - Some tables may not have user_id columns
2. **Foreign key constraints** - References to homeowner_id in related tables
3. **Data type mismatches** - UUID vs string format differences
4. **Missing indexes** - user_id columns may not be indexed

### **Mitigation Strategies**
1. **Database schema check first** - Query all tables for existing user_id columns
2. **Gradual rollout** - Test IRIS agent first, then expand
3. **Rollback plan** - Keep backup of original files
4. **Comprehensive testing** - Test all affected endpoints and components

---

## 🎯 SUCCESS CRITERIA

### **IRIS Agent Working**
- ✅ IRIS agent loads inspiration context without homeowner_id errors
- ✅ Project context retrieval works with user_id
- ✅ No more "homeowner_id conversion logic causing errors"

### **System Integration**  
- ✅ All API endpoints work with user_id parameters
- ✅ Frontend components display data correctly
- ✅ Database queries return expected results
- ✅ No breaking changes to existing functionality

### **Data Consistency**
- ✅ User can access their projects and bid cards
- ✅ Cross-agent functionality preserved
- ✅ Admin dashboard continues working

---

## 📋 IMPLEMENTATION CHECKLIST

### **Phase 1: Preparation**
- [ ] Database schema analysis - check which tables have user_id columns
- [ ] Backup all files before changes
- [ ] Create test plan for IRIS agent verification

### **Phase 2: Core Backend (Priority 1)**
- [ ] Update `ai-agents/adapters/iris_context.py:150`
- [ ] Update `ai-agents/adapters/homeowner_context.py` functions
- [ ] Update `ai-agents/routers/cia_potential_bid_cards.py:100-104`
- [ ] Test IRIS agent after each adapter change
- [ ] Update remaining router files systematically

### **Phase 3: Frontend TypeScript (Priority 2)**  
- [ ] Update `web/src/types/bidCard.ts` interfaces
- [ ] Update `web/src/contexts/HomeownerContext.tsx`
- [ ] Update API service calls in `web/src/services/api.ts`
- [ ] Update React components systematically
- [ ] Test frontend functionality after each major component

### **Phase 4: Testing & Validation (Priority 3)**
- [ ] Update all test files
- [ ] Run comprehensive test suite
- [ ] Verify IRIS agent functionality end-to-end
- [ ] Verify admin dashboard functionality
- [ ] Verify bid card creation and management

### **Phase 5: Documentation Update**
- [ ] Update API documentation
- [ ] Update agent integration guides
- [ ] Update this migration plan with results

---

**Total Estimated Effort**: 372+ individual changes across 65+ files
**Critical Path**: IRIS agent functionality (adapters and core routes)
**User Expectation**: "Just change the code references" - no complex data migration needed