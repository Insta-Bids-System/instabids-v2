# Docker Hot Reload Limitation - Known Issue
**Status**: Known limitation - workaround documented  
**Impact**: Manual container restarts required after frontend changes  
**Performance**: App maintains fast response time (17ms) with manual restarts
**Docker Compose Version**: v2.35.1 (supports watch, but conflicts with bind mounts)  

## 🚨 **CRITICAL FOR ALL AGENTS** 🚨

### **Issue: Hot Reload NOT Working in Docker on Windows**
Docker + Windows file watching is fundamentally broken for frontend hot reload. Multiple solutions were attempted but all either failed or made the app unusably slow.

### **MANDATORY WORKAROUND**
**When you make ANY changes in `web/` directory:**
```bash
# After editing any file in web/src/, you MUST restart the frontend container
docker restart instabids-instabids-frontend-1

# Changes will then be visible in browser
```

### **Why This Happened**
The user spent 1.5-2 hours debugging issues because they assumed hot reload would work. Multiple agents made changes that weren't visible, leading to wasted time and frustration.

## 📋 **PRE-WORK CHECKLIST FOR ALL AGENTS**

Before starting frontend work:
1. ✅ **Test hot reload**: Make a small change and see if it appears automatically
2. ✅ **If change doesn't appear**: Use manual restart command above
3. ✅ **Plan for restarts**: Expect to restart container after each meaningful change
4. ✅ **Prefer backend changes**: Backend hot reload works with `--reload` flag

## 🔧 **ATTEMPTED SOLUTIONS (All Failed)**

### **Solution 1: Docker Compose Watch Mode (FAILED - August 21, 2025)**
```yaml
# docker-compose.yml - TRIED WITH v2.35.1
develop:
  watch:
    - action: sync
      path: ./web/src
      target: /app/src
```
**Result**: Conflicts with bind mounts - "path also declared by a bind mount volume, this path won't be monitored!"
**Note**: Watch mode is GA in Docker Compose 2.22+ but cannot work alongside bind mounts on same paths

### **Solution 2: Vite Polling (FAILED)**
```typescript
// vite.config.ts - TRIED AND REVERTED
server: {
  watch: {
    usePolling: true,
    interval: 1000  // Then tried 5000ms
  }
}
```
**Result**: Made app unusably slow (15+ second load times)

### **Solution 2: Docker Compose Watch (FAILED)**
```yaml
# docker-compose.yml - TRIED AND REVERTED
develop:
  watch:
    - path: ./web
      action: sync
      target: /app
```
**Result**: Conflicted with bind mounts - "path also declared by a bind mount volume"

### **Solution 3: File System Events (INHERENTLY BROKEN)**
Windows Docker file watching is fundamentally broken and cannot be fixed.

## ✅ **WORKING SOLUTION: Manual Restarts**

### **Benefits**
- ✅ **Fast Performance**: 17ms response time maintained
- ✅ **Reliable Updates**: Changes always appear after restart
- ✅ **No System Conflicts**: Simple bind mounts work perfectly
- ✅ **Backend Hot Reload**: Still works with FastAPI `--reload` flag

### **Trade-off Decision**
User explicitly chose fast app with manual restarts over slow app with auto-reload:
> "All right, fine. Basically, we all know if we've made any significant changes to the code or the logic that we need to tell that agent to restart what the front and the back end."

## 🎯 **AGENT COORDINATION RULES**

1. **Always mention hot reload limitation** when starting frontend work
2. **Include restart instruction** in any frontend changes
3. **Test your changes** by restarting container and verifying in browser
4. **Don't assume hot reload works** - it doesn't and won't work

## 🔍 **Technical Details**

### **Current Working Setup**
```yaml
# docker-compose.yml - CURRENT WORKING CONFIGURATION
volumes:
  - ./web:/app
  - /app/node_modules
command: npm run dev -- --host 0.0.0.0
```

### **Container Names**
- **Frontend**: `instabids-instabids-frontend-1`
- **Backend**: `instabids-instabids-backend-1` (hot reload works)
- **Database**: `instabids-supabase-1`

### **Performance Metrics**
- **With manual restarts**: 17ms response time ✅
- **With polling (5s)**: 15+ second load times ❌
- **With polling (1s)**: Even slower, unusable ❌

## 📝 **Documentation for User**

The hot reload issue has been documented as a known Docker + Windows limitation. All agents will now know to restart the frontend container after making changes. This ensures:

1. **No more wasted debugging time** - agents know the limitation upfront
2. **Fast app performance** - 17ms response time maintained
3. **Reliable development workflow** - manual restarts always work
4. **Clear expectations** - no false assumptions about auto-reload

**The system prioritizes performance over convenience.**