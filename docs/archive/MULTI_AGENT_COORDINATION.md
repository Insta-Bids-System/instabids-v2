# Multi-Agent Development Coordination Rules

**Date**: July 31, 2025  
**Status**: 🚨 CRITICAL - ALL AGENTS MUST FOLLOW  

---

## 🚨 **EMERGENCY RULE: ONE FRONTEND ONLY**

### **THE PROBLEM WE JUST FIXED:**
- 4 agents were creating different frontends simultaneously
- Each frontend required different CORS ports
- User couldn't see work because wrong frontend/backend combination
- Complete chaos and wasted development time

### **THE SOLUTION:**
**ALL AGENTS USE SAME FRONTEND: `web/` directory ONLY**

---

## 📋 **MANDATORY WORKFLOW FOR ALL AGENTS**

### **Before Making ANY Frontend Changes:**

1. **Check Current State**: 
   ```bash
   cd web/
   npm run dev  # Note which port it uses
   ```

2. **Verify Backend Connection**:
   ```bash
   cd ai-agents/
   # Backend should be on port 8008 with CORS allowing ALL ports
   ```

3. **Component Development**:
   - ✅ **Edit existing components** in `web/src/components/`
   - ✅ **Edit existing pages** in `web/src/pages/`
   - ❌ **NEVER create new React apps**
   - ❌ **NEVER create new frontends**

---

## 🏗️ **ARCHITECTURE OVERVIEW**

```
SINGLE BACKEND (Port 8008)
├── CORS: Allows ALL localhost ports
├── API: Works with any frontend port
└── Data: Single source of truth

SINGLE FRONTEND (web/ directory)
├── Port: Any available (5173, 5174, 5186, etc.)
├── Components: Shared by all agents
├── Pages: Shared by all agents
└── Build: Single package.json
```

---

## 🔄 **COORDINATION PROTOCOLS**

### **Agent 1 (Frontend Flow):**
- **Focus**: Chat interfaces, bid card display
- **Files**: `web/src/components/chat/`, `web/src/components/BidCard*`
- **Coordination**: Check existing chat components before creating new

### **Agent 2 (Backend Core):**
- **Focus**: API endpoints, agent logic
- **Files**: `ai-agents/main.py`, `ai-agents/agents/`
- **Coordination**: Maintain single backend instance on port 8008

### **Agent 3 (Homeowner UX):**
- **Focus**: Dashboard, homeowner interfaces
- **Files**: `web/src/pages/Dashboard*`, `web/src/components/homeowner/`
- **Coordination**: Edit existing dashboard components

### **Agent 4 (Contractor UX):**
- **Focus**: Contractor interfaces, onboarding
- **Files**: `web/src/pages/contractor/`, `web/src/components/contractor/`
- **Coordination**: Edit existing contractor components

---

## ⚠️ **CONFLICT RESOLUTION**

### **Port Conflicts:**
- **Frontend ports**: Use any available - backend accepts all
- **Backend port**: Always 8008 - only one instance allowed

### **Component Conflicts:**
- **Before editing**: Check if another agent is working on same component
- **Large changes**: Coordinate in shared documentation
- **Testing**: Always test on single frontend instance

### **Data Conflicts:**
- **Single database**: All agents use same Supabase instance
- **API changes**: Update backend once, all frontends benefit
- **State management**: Use existing React context in `web/`

---

## 🧪 **TESTING PROTOCOL**

### **Every Agent Must Verify:**
1. **Backend Running**: `http://localhost:8008/health`
2. **Frontend Running**: `cd web/ && npm run dev`
3. **Connection Working**: Login with test.homeowner@instabids.com
4. **Changes Visible**: Verify your changes appear in the UI

### **Before Committing:**
1. **Full Build Test**: `cd web/ && npm run build`
2. **Backend Test**: All API endpoints working
3. **Integration Test**: Frontend + backend working together

---

## 📚 **QUICK REFERENCE**

### **Standard Commands:**
```bash
# Start backend (any agent can do this)
cd ai-agents/
python main.py

# Start frontend (use any available port)
cd web/
npm run dev

# Test connection
curl http://localhost:8008/api/bid-cards/homeowner/e6e47a24-95ad-4af3-9ec5-f17999917bc3
```

### **File Locations:**
- **Backend**: `ai-agents/main.py` (CORS allows all ports)
- **Frontend**: `web/src/` (single React app)
- **Components**: `web/src/components/` (shared by all agents)
- **Pages**: `web/src/pages/` (shared by all agents)

---

## 🎯 **SUCCESS METRICS**

- ✅ **One Backend**: Port 8008, accepts all frontend ports
- ✅ **One Frontend**: `web/` directory, any available port
- ✅ **All Agents Coordinated**: Working on same codebase
- ✅ **User Can See All Work**: Single interface shows all agent contributions
- ✅ **No More Port Conflicts**: CORS allows all localhost ports

---

## 🚨 **EMERGENCY CONTACT**

If you encounter conflicts or confusion:
1. **Stop all development**
2. **Check this document**
3. **Verify single backend/frontend rule**
4. **Coordinate with other agents through shared documentation**

**Remember**: The user should NEVER have to guess which frontend shows which agent's work. ONE FRONTEND SHOWS EVERYTHING.