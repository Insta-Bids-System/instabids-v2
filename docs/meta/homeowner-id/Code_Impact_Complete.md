# Complete Code Impact Analysis - Homeowner ID to User ID Migration
**Created**: January 13, 2025  
**Purpose**: Detailed file-by-file code changes required for migration  
**Scope**: 372+ references across 65+ files

## 🚨 CRITICAL IRIS-BLOCKING CHANGES (DO THESE FIRST)

### **iris_context.py - THE MAIN BLOCKER**
```python
# ai-agents/adapters/iris_context.py:150
# CURRENT (BROKEN):
result = self.supabase.table("projects").select("*").eq("id", project_id).eq("homeowner_id", user_id).execute()

# CHANGE TO:
result = self.supabase.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()
```

### **homeowner_context.py - CORE ADAPTER**
```python
# ai-agents/adapters/homeowner_context.py

# Lines 121-144 - ALL FUNCTIONS NEED CHANGES:
def get_projects(self, homeowner_id: str) -> List[Dict[str, Any]]:
    # CHANGE TO: def get_projects(self, user_id: str)
    result = self.supabase.table("projects").select("*").eq("homeowner_id", homeowner_id).execute()
    # CHANGE TO: .eq("user_id", user_id)

def get_bid_cards(self, homeowner_id: str) -> List[Dict[str, Any]]:
    # CHANGE TO: def get_bid_cards(self, user_id: str)
    result = self.supabase.table("bid_cards").select("*").eq("homeowner_id", homeowner_id).execute()
    # CHANGE TO: .eq("user_id", user_id)

def get_user_memories(self, homeowner_id: str) -> List[Dict[str, Any]]:
    # CHANGE TO: def get_user_memories(self, user_id: str)
    result = self.supabase.table("user_memories").select("*").eq("homeowner_id", homeowner_id).execute()
    # CHANGE TO: .eq("user_id", user_id)
```

---

## 📁 COMPLETE FILE INVENTORY WITH LINE-BY-LINE CHANGES

### **🐍 PYTHON BACKEND FILES (35+ files, ~200 references)**

#### **1. ADAPTERS (Priority 1 - IRIS Critical)**

**ai-agents/adapters/homeowner_context.py**
- Lines 121-144: Change all function signatures and queries
- Line 121: `get_projects(homeowner_id: str)` → `get_projects(user_id: str)`
- Line 123: `.eq("homeowner_id", homeowner_id)` → `.eq("user_id", user_id)`
- Line 130: `get_bid_cards(homeowner_id: str)` → `get_bid_cards(user_id: str)`
- Line 132: `.eq("homeowner_id", homeowner_id)` → `.eq("user_id", user_id)`
- Line 139: `get_user_memories(homeowner_id: str)` → `get_user_memories(user_id: str)`
- Line 141: `.eq("homeowner_id", homeowner_id)` → `.eq("user_id", user_id)`

**ai-agents/adapters/iris_context.py**
- Line 150: `.eq("homeowner_id", user_id)` → `.eq("user_id", user_id)`

#### **2. ROUTERS/API ENDPOINTS (Priority 1)**

**ai-agents/routers/cia_potential_bid_cards.py**
```python
# Lines 100-104 - CRITICAL CHANGE
# CURRENT:
homeowner_result = db.client.table("homeowners").select("id").eq("user_id", request.user_id)
if homeowner_result.data:
    potential_bid_card_data["homeowner_id"] = homeowner_result.data[0]["id"]

# CHANGE TO:
potential_bid_card_data["user_id"] = request.user_id
```

**ai-agents/routers/admin_search_api.py**
- Multiple functions with homeowner_id filters
- `get_bid_cards_by_homeowner()` - change parameter and query
- `search_homeowners()` - refactor to search users directly
- All `.eq("homeowner_id", ...)` → `.eq("user_id", ...)`

**ai-agents/routers/bid_card_api.py**
- Bid card creation: `"homeowner_id": homeowner_id` → `"user_id": user_id`
- Query filters: `.eq("homeowner_id", ...)` → `.eq("user_id", ...)`
- Function parameters throughout

**ai-agents/routers/cia_routes.py**
- 10+ references to homeowner_id
- User context loading
- Project associations
- All need conversion to user_id

**ai-agents/routers/contractor_proposals_api.py**
- Proposal filtering by homeowner
- Access control checks
- Change all homeowner_id references

**ai-agents/routers/unified_conversation_api.py**
- Conversation ownership validation
- Permission checks
- Update to use user_id

**ai-agents/routers/jaa_routes.py**
- Job assessment context
- Bid card generation
- Update homeowner references

**ai-agents/routers/bid_card_lifecycle_routes.py**
- Lifecycle management
- Status updates
- Change homeowner_id filters

**ai-agents/routers/homeowner_onboarding_api.py**
- Onboarding flow
- Profile creation
- Update to use user_id directly

**ai-agents/routers/image_upload_api.py**
- Image associations
- Ownership checks
- Change homeowner_id joins

**ai-agents/routers/inspiration_board_api.py**
- Board creation/retrieval
- `.eq("homeowner_id", ...)` → `.eq("user_id", ...)`

**ai-agents/routers/inspiration_conversation_api.py**
- Conversation filtering
- Update all homeowner_id references

**ai-agents/routers/inspiration_image_api.py**
- Image ownership
- Query filters

**ai-agents/routers/project_api.py**
- Project CRUD operations
- All homeowner_id fields

**ai-agents/routers/property_api.py**
- Property associations
- Update queries

**ai-agents/routers/referral_api.py**
- `referred_homeowner_id` → `referred_user_id`
- Update all referral tracking

**ai-agents/routers/vision_compositions_api.py**
- Composition ownership
- Query filters

#### **3. UTILITY FILES**

**ai-agents/bid_card_utils.py**
- `create_bid_card_with_defaults(homeowner_id)` → `create_bid_card_with_defaults(user_id)`
- Update all bid card creation logic

**ai-agents/database_simple.py**
- Helper functions for queries
- Update any homeowner_id building

**ai-agents/project_utils.py**
- Project management utilities
- Change homeowner associations

#### **4. AGENT FILES**

**ai-agents/agents/cia/agent.py**
- Remove homeowner_id conversion logic
- Use user_id throughout

**ai-agents/agents/iris/agent.py**
- Remove homeowner table joins
- Direct user_id usage

**ai-agents/agents/coia/agent.py**
- Verify cross-references
- Update any homeowner lookups

#### **5. TEST FILES (8+ files)**

**ai-agents/test_cia_claude_extraction.py**
- Update test data fixtures
- Change assertions

**ai-agents/test_complete_bid_submission_workflow.py**
- Update workflow test data
- Fix assertions

**ai-agents/test_homeowner_context_*.py**
- Update all context tests
- Fix mock data

**ai-agents/test_iris_*.py**
- Update IRIS test fixtures
- Fix inspiration tests

**ai-agents/test_messaging_agent_unified.py**
- Update messaging tests
- Fix user associations

**ai-agents/test_unified_api_direct.py**
- Update API tests
- Fix request/response data

---

### **⚛️ TYPESCRIPT FRONTEND FILES (25+ files, ~150 references)**

#### **1. TYPE DEFINITIONS (Priority 1)**

**web/src/types/bidCard.ts**
```typescript
// CHANGE ALL INTERFACES:
export interface BidCard {
  homeowner_id: string;  // CHANGE TO: user_id: string;
  // ... other fields
}

export interface BidCardResponse {
  homeowner_id: string;  // CHANGE TO: user_id: string;
  // ... other fields
}
```

**web/src/types/index.ts**
- Update all exported types
- Fix type imports

**web/src/types/project.ts**
- `homeowner_id: string` → `user_id: string`

**web/src/types/inspiration.ts**
- Update all inspiration types

#### **2. REACT CONTEXTS (Priority 1)**

**web/src/contexts/HomeownerContext.tsx**
```typescript
// Update state interface
interface HomeownerContextState {
  homeownerId: string;  // CHANGE TO: userId: string;
  // ...
}

// Update all references throughout file
```

**web/src/contexts/BidCardContext.tsx**
- Update bid card state
- Fix filter functions

#### **3. API SERVICES**

**web/src/services/api.ts**
```typescript
// Update all API calls:
getBidCardsByHomeowner(homeownerId: string)  
// CHANGE TO: getBidCardsByUser(userId: string)

// Update query parameters:
`/api/bid-cards?homeowner_id=${homeownerId}`
// CHANGE TO: `/api/bid-cards?user_id=${userId}`
```

**web/src/services/bidCardService.ts**
- Update all service methods
- Fix request payloads

**web/src/services/projectService.ts**
- Update project queries
- Fix ownership checks

#### **4. COMPONENTS**

**web/src/components/admin/**
- AdminDashboard.tsx - Update homeowner filters
- BidCardManagement.tsx - Fix queries
- ContractorManagement.tsx - Update associations
- UserManagement.tsx - Remove homeowner references

**web/src/components/bidcards/**
- BidCardList.tsx - Update filter props
- BidCardDetail.tsx - Fix ownership checks
- BidCardForm.tsx - Update form data
- BidCardFilters.tsx - Fix filter fields

**web/src/components/messaging/**
- MessagingInterface.tsx - Update user context
- MessageThread.tsx - Fix user associations
- MessageComposer.tsx - Update sender info

**web/src/components/projects/**
- ProjectList.tsx - Update queries
- ProjectDetail.tsx - Fix ownership
- ProjectForm.tsx - Update creation data

#### **5. PAGES**

**web/src/pages/HomeownerDashboard.tsx**
- Core dashboard functionality
- Update all user references

**web/src/pages/BidCardPage.tsx**
- Route parameters
- Query updates

**web/src/pages/AdminPage.tsx**
- Admin user management
- Remove homeowner table refs

**web/src/pages/ProjectPage.tsx**
- Project ownership
- Update filters

#### **6. HOOKS**

**web/src/hooks/useHomeowner.ts**
```typescript
// Rename or update:
export const useHomeowner = () => {
  const { homeownerId } = useContext(HomeownerContext);
  // CHANGE TO: const { userId } = useContext(UserContext);
  
  // Update all API calls
}
```

**web/src/hooks/useBidCards.ts**
- Update dependencies
- Fix query parameters

---

## 🔄 SYSTEMATIC REPLACEMENT PATTERNS

### **Python Pattern Replacements:**
```python
# 1. Function signatures
def function_name(homeowner_id: str) → def function_name(user_id: str)

# 2. Supabase queries
.eq("homeowner_id", value) → .eq("user_id", value)
.filter("homeowner_id", "eq", value) → .filter("user_id", "eq", value)

# 3. Dictionary keys
data["homeowner_id"] → data["user_id"]
{"homeowner_id": value} → {"user_id": value}

# 4. Variable names
homeowner_id = something → user_id = something

# 5. SQL strings
"WHERE homeowner_id = %s" → "WHERE user_id = %s"

# 6. Homeowner table joins (REMOVE ENTIRELY)
.table("homeowners").select("id").eq("user_id", ...) → REMOVE
```

### **TypeScript Pattern Replacements:**
```typescript
// 1. Interface properties
homeowner_id: string → user_id: string
homeownerId: string → userId: string

// 2. Object properties
{ homeowner_id: value } → { user_id: value }
{ homeownerId: value } → { userId: value }

// 3. Function parameters
(homeownerId: string) → (userId: string)

// 4. API query strings
?homeowner_id=${value} → ?user_id=${value}

// 5. State variables
const [homeownerId, setHomeownerId] → const [userId, setUserId]

// 6. Props
homeownerId={value} → userId={value}
```

---

## 📊 MIGRATION METRICS

### **Total Changes Required:**
- **Python files**: 35+ files, ~200 individual changes
- **TypeScript files**: 25+ files, ~150 individual changes  
- **Test files**: 8+ files, ~22 individual changes
- **SQL migrations**: 7 files (already complete)
- **Total**: 372+ code changes across 65+ files

### **Critical Path (Must Do First):**
1. `iris_context.py:150` - Unblocks IRIS agent
2. `homeowner_context.py` - Core adapter functions
3. `cia_potential_bid_cards.py:100-104` - Bid card creation
4. TypeScript type definitions - Frontend compatibility

### **Estimated Effort:**
- **Database migration**: 1-2 hours (SQL scripts ready)
- **Backend Python changes**: 3-4 hours (systematic replacement)
- **Frontend TypeScript changes**: 2-3 hours (type updates + components)
- **Testing & validation**: 2-3 hours
- **Total**: 8-12 hours for complete migration

---

## ✅ VALIDATION CHECKLIST

### **After Each Component:**
- [ ] Code compiles without errors
- [ ] No TypeScript type errors
- [ ] API endpoints return data
- [ ] Database queries work

### **After Backend Changes:**
- [ ] IRIS agent loads without homeowner_id errors
- [ ] CIA agent creates bid cards successfully
- [ ] Admin API returns correct data
- [ ] All routers tested with Postman/curl

### **After Frontend Changes:**
- [ ] TypeScript compilation successful
- [ ] Components render without errors
- [ ] API calls work correctly
- [ ] User can access their data

### **End-to-End Tests:**
- [ ] User can create projects
- [ ] User can create bid cards
- [ ] IRIS agent provides inspiration
- [ ] Admin dashboard shows all data
- [ ] Messaging system works
- [ ] Referral tracking works

---

## 🚀 IMPLEMENTATION ORDER

### **Phase 1: Database (Prerequisites)**
1. Run `01_add_user_id.sql` - Add columns
2. Run `02_backfill_user_id.sql` - Populate data
3. Verify no NULLs remain
4. Run `03_enforce_not_null_and_constraints.sql`

### **Phase 2: Backend Critical Path (Unblock IRIS)**
1. Fix `iris_context.py:150` - The main blocker
2. Fix `homeowner_context.py` - Core adapter
3. Fix `cia_potential_bid_cards.py:100-104`
4. Test IRIS agent works

### **Phase 3: Backend Systematic (All Routers)**
1. Update all router files alphabetically
2. Update utility files
3. Update agent files
4. Run backend tests

### **Phase 4: Frontend Types First**
1. Update `types/bidCard.ts`
2. Update `types/index.ts`
3. Update all type definitions
4. Fix TypeScript errors

### **Phase 5: Frontend Components**
1. Update contexts
2. Update services/api
3. Update components
4. Update pages
5. Update hooks

### **Phase 6: Testing & Validation**
1. Run all test suites
2. Manual testing of critical paths
3. Admin dashboard verification
4. End-to-end user flows

### **Phase 7: Cleanup**
1. Run `05_drop_homeowner_id_columns.sql`
2. Run `06_drop_homeowners_table.sql`
3. Run `07_policies_rls.sql`
4. Remove any dead code

---

**This completes the detailed code impact analysis. Combined with the existing SQL migration scripts in `DB_Migrations/`, this provides a complete implementation guide for the homeowner_id → user_id migration.**