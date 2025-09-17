# 🚨 AGENT INSTRUCTIONS - WHERE TO FIND THINGS

## FOR ALL AGENTS: READ THIS FIRST

### The Problem We're Solving
You're right - we have documentation everywhere but agents don't know where to look. This file fixes that.

## 🎯 WHERE TO FIND API CONNECTIONS

### Frontend → Backend Connections Are In:
1. **Primary API Service**: `/web/src/services/api.ts`
   - Has CIA, COIA, JAA, contractor endpoints
   - Missing admin endpoints (that's why admin is confused)

2. **Messaging Service**: `/web/src/services/messaging.ts`
   - All messaging endpoints

3. **Supabase Direct**: `/web/src/lib/supabase.ts`
   - Direct database queries
   - Auth functions
   - Real-time subscriptions

4. **Component-Level Calls**: Search for `fetch("http://localhost:8008`
   - Admin components have hardcoded calls
   - Some components bypass the service layer

### Backend Endpoint Definitions Are In:
1. **Main Router**: `/ai-agents/main.py`
   - Shows all active routers (but has duplicates!)
   - Line 168-194 has the includes

2. **Router Files**: `/ai-agents/routers/*.py`
   - 27 different router files
   - Many duplicates (3 bid card routers, 2 admin routers)

3. **API Files**: `/ai-agents/api/*.py`
   - 11 additional API files
   - Some imported, some not

## 🔍 HOW TO FIND WHAT YOU NEED

### "I need to modify an admin endpoint"
1. Check `/web/src/components/admin/` for what the UI is calling
2. Check `/ai-agents/routers/admin_routes.py` for backend
3. NOTE: `admin_routes_enhanced.py` is ALSO active (duplicate!)

### "I need to modify messaging"
1. Frontend: `/web/src/services/messaging.ts`
2. Backend: `/ai-agents/routers/messaging_api.py`
3. Agent logic: `/ai-agents/agents/messaging_agent.py`

### "I need to modify bid cards"
1. Frontend: Multiple places (search for "bid-card")
2. Backend: WARNING - 3 active routers!
   - `bid_card_lifecycle_routes.py`
   - `bid_card_api_simple.py`
   - `bid_card_simple_lifecycle.py`

### "I need to find where an endpoint is defined"
```bash
# Search backend:
grep -r "endpoint_name" ai-agents/

# Search frontend calls:
grep -r "api/endpoint_name" web/src/
```

## 📁 DOCUMENTATION LOCATIONS

### System Architecture Docs:
`/ai-agents/AGENT_ENDPOINTS/COMPLETE_AGENT_OWNERSHIP_MAP.md`
- Shows all 186 endpoints and owners
- Maps agents to their endpoints
- Consolidation plan

### Agent-Specific Docs:
`/ai-agents/AGENT_ENDPOINTS/AGENT_2_ADMIN_ENDPOINTS.md`
- Agent 2's complete endpoint list

### Frontend-Backend Mapping:
`/ai-agents/AGENT_ENDPOINTS/FRONTEND_TO_BACKEND_API_MAP.md`
- What frontend actually calls
- What backend actually has

## ⚠️ CRITICAL WARNINGS

### Duplicate Routers Active in main.py:
- 3 bid card routers (should be 1)
- 2 admin routers (should be 1)
- Wrong messaging router imported

### Missing from API Service:
- Admin endpoints not in `/web/src/services/api.ts`
- That's why admin components use direct fetch()

### Database Connections:
- Some use Supabase client directly
- Some go through API endpoints
- No consistent pattern

## 🎬 WHAT TO DO

### For Any Task:
1. **FIRST**: Check if the feature already works
   - If yes, find where it's implemented
   - If no, check if endpoint exists unused

2. **SECOND**: Look in the right place
   - Frontend service files for API calls
   - Backend router files for endpoints
   - Don't create new if it exists

3. **THIRD**: Check for duplicates
   - Search for similar endpoint names
   - Check main.py for multiple imports
   - Consolidate don't duplicate

## 🔑 THE TRUTH

### The System WORKS But Is Messy:
- Most connections exist and function
- They're just scattered across many files
- Documentation exists but agents don't use it
- Duplicates cause confusion

### The Admin Panel Issue:
- Just ONE example of the larger problem
- Admin endpoints exist but are duplicated
- Frontend doesn't use central API service
- Agent 2 got confused by the duplication

### The Real Solution:
1. Agents need to know WHERE to look (this file)
2. Consolidate duplicates in backend
3. Add missing endpoints to API service
4. Create single source of truth

## 📍 START HERE

**For Agent 2 (Admin)**: Your endpoints are in `/ai-agents/routers/admin_routes.py` but ALSO `admin_routes_enhanced.py` (both active!)

**For Agent 1 (Frontend)**: API calls are in `/web/src/services/api.ts` but admin uses direct fetch()

**For All Agents**: Search before creating. It probably already exists somewhere.

---

**THIS FILE LOCATION**: `/AGENT_INSTRUCTIONS_WHERE_TO_FIND_THINGS.md`
Put this in your agent specification so you always know where to look!