# 🐳 Docker MCP Setup for InstaBids
**Solves**: Multiple frontend issues, Playwright visibility problems, agent coordination

## 🚨 **What This Fixes:**
- ✅ **No More Multiple Frontends**: Single containerized frontend
- ✅ **Better Playwright Testing**: Clear container visibility  
- ✅ **Agent Coordination**: All agents use same containerized stack
- ✅ **Predictable Ports**: No more port conflicts
- ✅ **Isolated Development**: Clean, reproducible environments

## 📋 **Quick Setup (5 minutes)**

### 1. Add Docker MCP to Your Configuration

**Option A: Merge with existing config**
Add this to your `~/.claude.json` or Claude Desktop config:
```json
{
  "mcpServers": {
    "docker-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\Not John Or Justin\\Documents\\docker-mcp",
        "run",
        "docker-mcp"
      ]
    }
  }
}
```

**Option B: Use provided config**
Copy from: `C:\Users\Not John Or Justin\Documents\instabids\docker-mcp-config.json`

### 2. Setup Environment Variables
```bash
cd C:\Users\Not John Or Justin\Documents\instabids
copy .env.example .env
# Edit .env with your actual Supabase and API keys
```

### 3. Start the Stack
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f instabids-frontend
docker-compose logs -f instabids-backend
```

## 🎯 **Services & Ports**
- **Frontend**: http://localhost:5173 (React/Vite)
- **Backend**: http://localhost:8008 (FastAPI + AI Agents)
- **Database**: localhost:5432 (Supabase Postgres)
- **Email Testing**: http://localhost:8080 (MailHog UI)

## 🧪 **Testing with Playwright**
```bash
# Run Playwright tests in container
docker-compose --profile testing run playwright-tests

# Or run specific tests
docker-compose --profile testing run playwright-tests npx playwright test --grep "frontend"
```

## 🔧 **Development Workflow**

### Frontend Changes
```bash
# Frontend runs with live reload
# Edit files in ./web/ and see changes instantly at localhost:5173
```

### Backend Changes  
```bash
# Restart backend after changes
docker-compose restart instabids-backend
```

### Agent Coordination
All agents now work with the containerized stack:
- Agent 1 (Frontend): Uses localhost:5173
- Agent 2 (Backend): Uses localhost:8008  
- Agent 3-6: All use same containerized services
- Playwright MCP: Targets localhost:5173 with better visibility

## 🐛 **Troubleshooting**

### Container Issues
```bash
# View all containers
docker-compose ps

# Check logs
docker-compose logs [service-name]

# Restart specific service
docker-compose restart [service-name]

# Rebuild containers
docker-compose build [service-name]
```

### Port Conflicts
```bash
# Check what's using ports
netstat -ano | findstr ":5173"
netstat -ano | findstr ":8008"

# Stop conflicting processes or change ports in docker-compose.yml
```

### Database Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d supabase
```

## 🚀 **Benefits Achieved**

### Before Docker MCP:
- ❌ Multiple frontends created accidentally
- ❌ Playwright can't see main issues clearly
- ❌ Port conflicts between agents
- ❌ Inconsistent development environments

### After Docker MCP:
- ✅ Single frontend at predictable port (5173)
- ✅ Playwright tests target clear container URLs
- ✅ All agents coordinate through same stack
- ✅ Isolated, reproducible environments
- ✅ Better debugging and log visibility

## 📝 **Next Steps**
1. ✅ Docker MCP configured and working
2. ✅ InstaBids stack containerized  
3. 🔄 Test Playwright with containers
4. 🔄 Update agent workflows to use containers
5. 🔄 Resume TypeScript cleanup with better coordination

## 💡 **Pro Tips**
- Use `docker-compose up -d` for background services
- Use `docker-compose logs -f [service]` for live log monitoring
- Edit code normally - containers have live reload
- Use Docker MCP commands in Claude for container management

---
**Status**: Ready for testing ✅