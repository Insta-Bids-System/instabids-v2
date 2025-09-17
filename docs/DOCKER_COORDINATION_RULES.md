# 🐳 DOCKER COORDINATION RULES - ALL AGENTS
**Status**: ACTIVE SYSTEM - August 5, 2025
**Priority**: MANDATORY - ALL AGENTS MUST FOLLOW

## 🚨 **CRITICAL: THE OLD CHAOS IS OVER**

### **❌ NEVER DO THIS ANYMORE:**
```bash
npm run dev                    # NO - Creates competing frontend
python main.py                 # NO - Creates competing backend  
cd frontend && npm start       # NO - Wrong directory
cd web && npm run dev          # NO - Bypasses Docker coordination
```

### **✅ ALWAYS DO THIS:**
```bash
# 1. Start Docker stack (if not running)
cd C:\Users\Not John Or Justin\Documents\instabids
docker-compose up -d

# 2. Verify services
curl http://localhost:5173    # Frontend
curl http://localhost:8008    # Backend

# 3. Make your changes to local files
# 4. Changes appear instantly via live reload
```

## 🎯 **THE NEW AGENT RULES**

### **Agent 1 (Frontend Flow):**
```typescript
// OLD: Started own dev server
npm run dev  // Created chaos

// NEW: Use Docker frontend
// 1. Edit files in web/src/
// 2. Changes appear instantly at localhost:5173
// 3. All other agents see your changes immediately
// 4. Use Playwright MCP to test localhost:5173
```

### **Agent 2 (Backend Core):**  
```python
# OLD: Started own main.py
python main.py  // Created conflicts

# NEW: Use Docker backend
# 1. Edit files in ai-agents/
# 2. Restart container: docker-compose restart instabids-backend
# 3. All endpoints available at localhost:8008
# 4. All other agents can test immediately
```

### **Agent 3 (Homeowner UX):**
```bash
# OLD: Confused about which frontend to use
# NEW: Always use localhost:5173
# - Your UI changes appear instantly
# - Test Iris at localhost:5173/inspiration
# - No more port confusion
```

### **Agent 4 (Contractor UX):**
```bash
# OLD: Created own contractor portal
# NEW: Build in the unified frontend
# - Edit web/src/pages/contractor/
# - Test at localhost:5173/contractor
# - Integrated with same backend/database
```

### **Agent 5 (Marketing):**
```bash
# OLD: Couldn't find services to measure
# NEW: Everything at predictable URLs
# - Analytics at localhost:8008/api/analytics
# - Frontend at localhost:5173
# - Consistent data collection
```

### **Agent 6 (QA/Testing):**
```bash
# OLD: Had to hunt for services across ports
# NEW: Monitor single stack
# - Frontend: localhost:5173
# - Backend: localhost:8008  
# - Database: localhost:5432
# - Perfect system visibility
```

## 🔄 **HOW LIVE RELOAD WORKS**

### **Frontend Changes (Instant):**
```bash
# 1. Edit any file in web/src/
# 2. Vite detects change in container
# 3. Browser auto-refreshes
# 4. Change visible in <3 seconds
```

### **Backend Changes (Fast Restart):**
```bash
# 1. Edit any file in ai-agents/
# 2. Restart container: docker-compose restart instabids-backend
# 3. New backend code active
# 4. All endpoints updated
```

### **Database Changes (Immediate):**
```bash
# 1. Database always at localhost:5432
# 2. All agents query same data
# 3. Changes visible immediately
# 4. No synchronization issues
```

## 📍 **PREDICTABLE URLS (MEMORIZE THESE)**

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | React app (all pages) |
| Backend API | http://localhost:8008 | All 50+ endpoints |
| Admin Dashboard | http://localhost:5173/admin | Admin interface |
| API Documentation | http://localhost:8008/docs | Swagger docs |
| Database | localhost:5432 | PostgreSQL |
| Email Testing | http://localhost:8080 | MailHog UI |

## 🧪 **TESTING REVOLUTION**

### **Before Docker:**
```bash
Agent 1: "My frontend is on port 5174"
Agent 2: "My backend is on port 8009"  
Agent 3: "Which port has the latest UI?"
Agent 4: "I can't find the contractor portal"
Result: Chaos, confusion, wasted time
```

### **After Docker:**
```bash
All Agents: "Frontend is localhost:5173, backend is localhost:8008"
Result: Perfect coordination, instant testing
```

## 🚀 **IMMEDIATE BENEFITS YOU'LL SEE**

### **1. No More Port Hunting:**
```bash
# Always the same:
Frontend: localhost:5173
Backend: localhost:8008
```

### **2. Instant Cross-Agent Testing:**
```bash
# Agent 1 makes UI change
# Agent 2 can test it immediately at localhost:5173
# Agent 3 can build on it right away
```

### **3. Perfect Playwright Testing:**
```javascript
// Always works, always finds elements:
await page.goto('http://localhost:5173');
await page.click('[data-testid="bid-card"]');
```

### **4. Unified Development:**
```bash
# All agents work on the SAME:
- Frontend codebase (web/)
- Backend codebase (ai-agents/)  
- Database (localhost:5432)
- No more version conflicts
```

## ⚡ **QUICK START CHECKLIST**

- [ ] Run `docker-compose up -d` 
- [ ] Verify frontend at localhost:5173
- [ ] Verify backend at localhost:8008
- [ ] Make a small change to test live reload
- [ ] Confirm change appears in browser
- [ ] NEVER start separate dev servers again

---

**🎉 RESULT: Multi-agent development goes from chaotic to coordinated!**

**All 6 agents now work on the SAME stack with INSTANT feedback.**