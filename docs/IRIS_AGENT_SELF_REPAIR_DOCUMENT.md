# IRIS Agent - Complete Self-Repair & Migration Document
**Date:** January 27, 2025  
**Status:** URGENT - Backend failing, frontend never tested  
**For:** IRIS Agent to diagnose and fix itself

## 🚨 CRITICAL SITUATION

**WHAT'S BROKEN:**
- Backend `/api/iris/` endpoints return 404 Not Found
- New unified conversation system not working
- Frontend integration completely untested
- User has never been able to actually chat with IRIS agent
- Previous migration attempts were pure "air coding"

**WHAT THE USER WANTS:**
- Working IRIS agent that can have actual conversations
- Frontend UI that connects to working backend
- Unified conversation system integration
- Test the complete flow end-to-end

## 📂 CURRENT FILE STRUCTURE

### Backend Files Created (May Have Errors)
```
ai-agents/
├── api/
│   ├── iris_chat_consolidated.py (OLD - was working before)
│   └── iris_chat_unified.py (NEW - failing import?)
├── agents/iris/
│   ├── agent.py (Original IRIS agent)
│   └── README.md
└── main.py (Updated to use iris_chat_unified)
```

### Database Tables
```sql
-- OLD SYSTEM (currently has 5 active conversations)
inspiration_conversations
inspiration_boards  
inspiration_images

-- NEW UNIFIED SYSTEM (working for CIA)
unified_conversations
unified_messages
unified_conversation_memory
unified_conversation_participants
```

### Frontend Integration
```
web/src/components/inspiration/IrisChat.tsx (exists but unknown status)
```

## 🔍 DIAGNOSIS NEEDED

### Backend Issues to Check:
1. **Import Error**: Does `iris_chat_unified.py` have syntax errors?
2. **Router Registration**: Is the unified router properly registered in main.py?
3. **Dependencies**: Are all required imports available?
4. **API Endpoints**: Do the unified endpoints match expected paths?

### Frontend Issues to Check:
1. **Component Status**: Does IrisChat.tsx exist and work?
2. **API Integration**: Does frontend call the right backend endpoints?
3. **UI Loading**: Can users actually access the IRIS chat interface?
4. **Real Chat Flow**: Can users send messages and get responses?

## 📋 REPAIR TASKS FOR IRIS AGENT

### Task 1: Fix Backend Import Issues
**Problem**: `/api/iris/` returns 404 Not Found despite being in main.py
**Actions Needed:**
1. Check `iris_chat_unified.py` for syntax/import errors
2. Verify router is properly defined and exported
3. Test backend starts without errors
4. Confirm endpoints are registered correctly

### Task 2: Test Basic API Functionality
**Test Commands:**
```bash
# Test backend is running
curl http://localhost:8008/

# Test IRIS endpoint exists
curl http://localhost:8008/api/iris/chat

# Test actual IRIS chat
curl -X POST http://localhost:8008/api/iris/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello IRIS","homeowner_id":"test-user"}'
```

### Task 3: Verify Frontend Integration
**Actions Needed:**
1. Navigate to http://localhost:5173 
2. Find IRIS chat interface (inspiration section?)
3. Try actual conversation with IRIS
4. Verify messages save and load correctly
5. Check browser network tab for API call errors

### Task 4: Test Complete User Flow
**End-to-End Test:**
1. User opens InstaBids frontend
2. Navigates to design inspiration section
3. Starts chat with IRIS
4. Sends: "I want to redesign my kitchen with modern farmhouse style"
5. IRIS responds intelligently
6. Conversation saves to unified system
7. User can continue conversation later

### Task 5: Unified System Migration
**Only if basic functionality works:**
1. Verify unified conversation API endpoints work
2. Test conversation persistence in unified tables
3. Migrate existing 5 inspiration_conversations if needed
4. Update frontend to use unified endpoints

## 📊 CURRENT STATUS SUMMARY

### What's Working:
- ✅ CIA Agent (migrated to unified system successfully)
- ✅ Unified conversation API (tested and working)
- ✅ Database schemas (unified tables exist)
- ✅ Frontend (loads at localhost:5173)

### What's Broken:
- ❌ IRIS backend endpoints (404 errors)
- ❌ IRIS frontend integration (never tested)
- ❌ Actual IRIS conversations (user can't chat)
- ❌ Unified system migration (depends on basic functionality)

### What's Unknown:
- ❓ IRIS frontend component status
- ❓ Exact import/syntax errors
- ❓ Whether old consolidated endpoint still works
- ❓ User experience and interface quality

## 🎯 SUCCESS CRITERIA

**Minimum Viable IRIS:**
1. User can access IRIS chat interface at http://localhost:5173
2. User can send message: "Help me design my kitchen"
3. IRIS responds with design guidance
4. Conversation appears in browser and saves to database

**Complete IRIS Migration:**
1. All above functionality working
2. Conversations save to unified_conversations table
3. IRIS integrates with unified conversation API
4. Existing conversations migrated if needed
5. Frontend uses unified endpoints

## 🔧 AVAILABLE RESOURCES

### Working Examples:
- **CIA Agent**: Successfully migrated, use as reference
- **Unified API**: Working endpoints at `/api/conversations/*`
- **Frontend**: React app running at localhost:5173

### Development Environment:
- **Backend**: Docker container `instabids-instabids-backend-1`
- **Frontend**: Docker container `instabids-instabids-frontend-1`
- **Database**: Supabase at localhost:5432
- **All containers running and accessible**

### Files to Reference:
```
ai-agents/routers/cia_routes.py (working unified example)
ai-agents/routers/unified_conversation_api.py (working API)
ai-agents/database_simple.py (working database integration)
```

## 💡 SUGGESTED APPROACH

1. **Start Simple**: Get basic IRIS chat working first (even with old system)
2. **Test Early**: Verify actual frontend conversation before complex migrations
3. **Fix Imports**: Resolve backend 404 errors before advanced features
4. **User First**: Prioritize working user experience over perfect architecture
5. **Migrate Later**: Only move to unified system after basic chat works

## 🚨 IMPORTANT NOTES

- **User Frustration**: Multiple failed attempts at "air coding" without testing
- **Real Testing Required**: Must verify actual user conversation flow
- **Backend Priority**: Fix 404 errors before any other work
- **Frontend Unknown**: Never confirmed IRIS UI actually exists/works
- **Working Examples Available**: CIA agent migration succeeded, use as template

---

**IRIS AGENT: Please diagnose the current situation, fix the immediate issues, and get a working conversation flow before attempting complex migrations.**