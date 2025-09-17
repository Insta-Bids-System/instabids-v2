# COIA System - Main Files List
**Date**: August 14, 2025  
**Purpose**: Quick reference for all critical COIA system files

## 🎯 Core System Files

### **1. LangGraph Workflow & State**
- `agents/coia/unified_graph.py` - Main LangGraph workflow orchestration
- `agents/coia/unified_state.py` - State management and data models
- `agents/coia/langgraph_nodes.py` - All node implementations (conversation, research, etc.)

### **2. API & Routing**
- `routers/unified_coia_api.py` - REST API endpoints for all interfaces
- `main.py` - FastAPI app mounting at `/api/coia/`

### **3. Node Components**
- `agents/coia/extraction_node.py` - Company name extraction logic
- `agents/coia/mode_detector_fix.py` - Fixed mode detection logic
- `agents/coia/account_creation_fallback.py` - Account creation logic

### **4. Tools & Research**
- `agents/coia/tools.py` - Google Places API integration
- `agents/coia/tools_real.py` - Real MCP tool implementations

### **5. Memory & Persistence**
- `agents/coia/state_management/state_manager.py` - State persistence
- `agents/coia/state_management/memory_store.py` - Memory storage

### **6. Documentation**
- `ai-agents/LANDING_PAGE_CONTRACTOR_FLOW_DESIGN.md` - Complete flow design
- `docs/COIA_CONSOLIDATION_COMPLETE.md` - Consolidation documentation
- `docs/COMPLETE_COIA_SYSTEM_ANALYSIS.md` - System analysis

### **7. Test Files**
- `test_complete_coia_simplified.py` - 5-stage conversation test
- `test_coia_extraction.py` - Company name extraction test

## 📍 Current Status

### ✅ Working
- Company name extraction: "JM Holiday Lighting" correctly extracted
- Google Places API: Pompano Beach location found
- Research completion: All API calls successful
- State persistence: Using Supabase checkpointer

### ❌ Still Needs Fixing
- contractor_created flag never set to True
- Account creation node not being triggered
- Backend timeout issues during long operations

## 🔧 Quick Commands

```bash
# Test COIA landing page
curl -X POST http://localhost:8008/api/coia/landing \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi, I am Justin from JM Holiday Lighting", "session_id": "test-123"}'

# Check backend logs
docker logs instabids-instabids-backend-1 -f

# Restart backend
docker restart instabids-instabids-backend-1
```

## 🚀 Slash Command Usage

Save this list as `/coia-files` for quick access:
```
/coia-files - Show all main COIA system files
```