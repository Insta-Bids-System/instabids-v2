# CONTRACTOR SYSTEM CLEANUP EXECUTION PLAN

**Date**: August 11, 2025  
**Status**: EXECUTION IN PROGRESS  
**Objective**: Remove ALL fake/deceptive contractor code, keep only real working systems

---

## 🔍 AUDIT RESULTS

### ✅ **REAL SYSTEMS TO KEEP**:
1. **`agents/coia/intelligent_research_agent.py`** - Real Google Places API (966 lines) ✅
2. **`agents/coia/unified_graph.py`** - Real LangGraph workflow (910 lines) ✅
3. **`routers/unified_coia_api.py`** - Complete REST API (777 lines) ✅
4. **Google API Key configured**: `AIzaSyBacJk_H4rpExmLiG1g8-nAGZJbSgC3IaA` ✅

### ❌ **FAKE SYSTEMS TO REMOVE**:
1. **`agents/coia/tools.py`** - Hardcoded fake data: "(561) 555-TURF"
2. **`agents/coia/simple_research_agent.py`** - Mock research data generator
3. **`routers/coia_api_fixed.py`** - Imports fake tools (currently in main.py)
4. **Mock data functions** in unified_graph.py

---

## 🗑️ REMOVAL ACTIONS

### Phase 1: Remove Fake Files
- [ ] Delete `agents/coia/tools.py` (fake hardcoded data)
- [ ] Delete `agents/coia/simple_research_agent.py` (mock generator)
- [ ] Archive `routers/coia_api_fixed.py` (fake system)

### Phase 2: Clean Mock Data from Real Files
- [ ] Remove `_get_mock_contractor_data()` from unified_graph.py
- [ ] Remove mock fallbacks from bid_card_search_node.py
- [ ] Clean any remaining hardcoded test data

### Phase 3: Connect Real Systems
- [ ] Change main.py import from coia_api_fixed to unified_coia_api
- [ ] Test Google Places API integration
- [ ] Verify all endpoints work with real data

### Phase 4: Final Verification
- [ ] Test complete real contractor flow
- [ ] Verify no fake data responses
- [ ] Document actual working capabilities

---

## 🎯 POST-CLEANUP SYSTEM

**What Will Work After Cleanup**:
- Real Google Places API business research
- Sophisticated LangGraph workflow with multiple interfaces
- Complete REST API with all missing endpoints (/api/coia/landing)
- Real MCP tool integrations (WebSearch, Supabase)
- Persistent memory with database storage

**What Will Be Gone Forever**:
- All hardcoded fake phone numbers/addresses
- Mock business data generators
- Fake tool responses
- Deceptive placeholder systems
- Any code that could mislead about capabilities

**Expected Result**: Clean, working contractor intelligence system with real Google API integration and authentic business research capabilities.