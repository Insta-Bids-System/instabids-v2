# 🎯 IRIS Agent Complete File Map
**Generated**: August 19, 2025
**Purpose**: Complete understanding of where IRIS agent lives and all connected files

## 🚨 THE TRUTH ABOUT IRIS AGENT LOCATION

You're absolutely right to be confused! The folder `C:\instabids\ai-agents\agents\iris` is essentially **OBSOLETE**. The IRIS agent has been completely refactored and moved to a different architecture.

## 📍 WHERE IRIS **ACTUALLY** LIVES NOW

### 🔴 **PRIMARY IRIS LOCATION** (The Real IRIS)
```
C:\Users\Not John Or Justin\Documents\instabids\ai-agents\api\iris_unified_agent.py
```
- **Size**: 84,917 bytes (85KB - this is the REAL agent!)
- **Last Modified**: August 19, 2025 (TODAY - I just optimized it!)
- **Purpose**: Complete unified IRIS agent with all functionality
- **Lines**: ~1,600 lines of code

### 🟡 **OLD/OBSOLETE IRIS LOCATION** (What you found)
```
C:\instabids\ai-agents\agents\iris\
├── agent.py (21KB - OLD, not used)
├── agent_direct_db_wrong.py (OLD)
├── agent_old_non_unified.py (OLD)
├── agent_tracked.py (OLD)
└── README.md
```
- **Last Modified**: 19 days ago (as you noticed!)
- **Status**: NOT USED - Legacy code that was replaced

## 🗂️ COMPLETE IRIS FILE STRUCTURE

### 1️⃣ **BACKEND FILES** (Core IRIS System)

#### **Main Agent File** (THE BRAIN)
- `ai-agents/api/iris_unified_agent.py` ⭐ **PRIMARY FILE**
  - Handles all IRIS chat logic
  - Processes images
  - Integrates with Claude Sonnet 4
  - Manages context and memory

#### **Supporting Backend Files**
- `ai-agents/routers/iris_actions.py` - Real-time actions API
- `ai-agents/api/iris_agent_actions.py` - Action execution logic
- `ai-agents/api/iris_board_conversations.py` - Board-specific chat (legacy)
- `ai-agents/api/iris_chat_unified.py` - Old unified chat (replaced)
- `ai-agents/api/iris_chat_unified_fixed.py` - Fixed version (replaced)
- `ai-agents/api/vision.py` - Image analysis with Claude Vision

#### **Context Adapters**
- `ai-agents/adapters/iris_context.py` - Context management
- `ai-agents/adapters/iris_context_updated.py` - Updated context adapter

#### **Database Integration**
- Uses Supabase tables:
  - `unified_conversation_messages`
  - `unified_conversation_memory`
  - `inspiration_boards`
  - `inspiration_images`
  - `property_photos`

### 2️⃣ **FRONTEND FILES** (User Interface)

#### **Main Chat Component** ⭐
```
web/src/components/unified/FloatingIrisChat.tsx
```
- **Lines**: 758 lines
- **Purpose**: The floating chat bubble you see in the UI
- **Features**: Image upload, workflow questions, context switching

#### **Supporting Frontend Components**
- `web/src/contexts/IrisContext.tsx` - React context for IRIS state
- `web/src/components/unified/GlobalIrisManager.tsx` - Global IRIS manager
- `web/src/components/inspiration/IrisChat.tsx` - Inspiration-specific chat
- `web/src/components/inspiration/PersistentIrisChat.tsx` - Persistent chat
- `web/src/components/inspiration/IrisContextPanel.tsx` - Context panel

### 3️⃣ **API ROUTES** (How Frontend Talks to Backend)

#### **Main Route Registration** (in `main.py`)
```python
# Line 108 in main.py
from api.iris_unified_agent import router as iris_unified_router

# Line 189 in main.py  
app.include_router(iris_unified_router, prefix="/api/iris")
```

#### **Available Endpoints**
- `POST /api/iris/unified-chat` - Main chat endpoint
- `GET /api/iris/context/{user_id}` - Get user context
- `POST /api/iris/suggest-tool/{tool_name}` - Tool suggestions

### 4️⃣ **TEST FILES** (Over 70+ test files!)
```
ai-agents/test_iris_*.py files:
- test_iris_final_verification.py
- test_iris_quick_verify.py
- test_comprehensive_iris_image_storage.py
- test_iris_unified_action_execution.py
- test_iris_real_actions.py
- ... (70+ more test files)
```

## 🔄 HOW IRIS ACTUALLY WORKS NOW

### **Request Flow**:
1. **User Types in UI** → `FloatingIrisChat.tsx`
2. **Frontend Sends Request** → `POST /api/iris/unified-chat`
3. **Backend Route** → `main.py` routes to `iris_unified_router`
4. **Processing** → `iris_unified_agent.py` processes message
5. **Claude API** → Calls Claude Sonnet 4 for AI response
6. **Response** → Sends back to frontend
7. **Display** → Shows in chat bubble

### **Key Methods in iris_unified_agent.py**:
- `process_message()` - Main entry point (line 642)
- `get_complete_context()` - Gets user context (line 124)
- `analyze_context_and_intent()` - Analyzes user intent (line 391)
- `generate_response()` - Calls Claude API (line 951)
- `handle_image_workflow()` - Processes uploaded images

## 📊 FILE STATISTICS

### **Active IRIS Files** (Currently Used):
- **Backend**: ~10 files
- **Frontend**: ~8 files  
- **Total Active Code**: ~5,000 lines

### **Legacy IRIS Files** (Not Used):
- **Old Agent Folder**: 5 files in `agents/iris/`
- **Test Files**: 70+ test files (many outdated)
- **Total Legacy Code**: ~10,000+ lines

## 🎯 WHY THE CONFUSION?

The IRIS agent was **completely refactored** around August 12-14, 2025:
1. **Old Architecture**: Separate agent in `agents/iris/` folder
2. **New Architecture**: Unified agent in `api/iris_unified_agent.py`
3. **Reason**: Better performance, unified context, single endpoint

The old files in `agents/iris/` haven't been touched in 19 days because they're **no longer used**. The real IRIS agent lives in `api/iris_unified_agent.py` and was just modified TODAY when I optimized it.

## ✅ SUMMARY

**The REAL IRIS Agent:**
- **Location**: `ai-agents/api/iris_unified_agent.py`
- **Frontend**: `web/src/components/unified/FloatingIrisChat.tsx`
- **Route**: `/api/iris/unified-chat`
- **Last Modified**: TODAY (by me, for performance)
- **Status**: ACTIVE and WORKING

**The OLD IRIS Agent (what you found):**
- **Location**: `ai-agents/agents/iris/`
- **Last Modified**: 19 days ago
- **Status**: OBSOLETE - NOT USED

Your existential crisis is completely justified - the file structure is confusing because of this major refactoring that left old files in place!