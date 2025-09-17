# Agent 6 Docker MCP Management Guide

## Critical Docker MCP Information

### Directory Structure & Paths
- **Docker MCP Server Directory**: `C:\Users\Not John Or Justin\Documents\docker-mcp`
- **Source Code**: `src\docker_mcp\`
  - `__init__.py` - Main entry point
  - `server.py` - MCP server implementation
  - `handlers.py` - Docker operation handlers
  - `docker_executor.py` - Docker command execution
- **Build Config**: `pyproject.toml`, `uv.lock`
- **Log Files**: `C:\Users\Not John Or Justin\AppData\Local\claude-cli-nodejs\Cache\C--Users-Not-John-Or-Justin\mcp-logs-docker\`
- **Config Location**: `C:\Users\Not John Or Justin\.claude.json`

### Startup Command
```bash
uv --directory C:/Users/Not John Or Justin/Documents/docker-mcp run docker-mcp
```

### Available MCP Docker Tools
- `mcp__docker__list-containers` - Lists all Docker containers
- `mcp__docker__get-logs` - Retrieves container logs
- `mcp__docker__create-container` - Creates new containers
- `mcp__docker__deploy-compose` - Deploys Docker Compose stacks

### Known Issues & Fixes

#### 1. ModuleNotFoundError Fix (RESOLVED)
- **Problem**: `extras.py` importing non-existent 'mcp_framework'
- **Solution**: Remove `extras.py` file
- **Status**: Fixed by another agent

#### 2. Unicode Encoding Fix (APPLIED)
- **Problem**: `get-logs` crashes with `UnicodeEncodeError` on Windows
- **Error**: `'charmap' codec can't encode character '\u279c'`
- **Root Cause**: Windows cp1252 encoding can't handle Unicode in Docker logs
- **Fix Location**: `handlers.py` lines 177-181
- **Fix Code**:
```python
# Ensure logs are properly encoded as UTF-8 string
if isinstance(logs, bytes):
    logs = logs.decode('utf-8', errors='replace')
elif not isinstance(logs, str):
    logs = str(logs)
```

### Docker Container Management

#### InstaBids Containers
- `instabids-instabids-frontend-1` - Frontend (port 5173)
- `instabids-instabids-backend-1` - Backend (port 8008)
- `instabids-supabase-1` - Database
- `instabids-mailhog-1` - Email testing

### Troubleshooting Steps

1. **Check Docker MCP Status**:
   - Use `/mcp` command to see server status
   - Look for "✘ failed" vs "✓ connected"

2. **View Error Logs**:
   - Navigate to log directory
   - Check latest log file for stack traces

3. **Restart Docker MCP**:
   - Use `/mcp` command
   - Select "Reconnect" option

4. **Test Functionality**:
   ```python
   # Test list containers
   mcp__docker__list-containers
   
   # Test get logs (should work after Unicode fix)
   mcp__docker__get-logs with container_name="instabids-instabids-frontend-1"
   ```

### Critical Rules
- **NEVER** create competing Docker processes
- **ALWAYS** use the Docker MCP tools for container management
- **CHECK** logs when tools fail or hang
- **APPLY** encoding fixes for Windows compatibility

### Memory Storage
This information is stored in Cipher memory under:
- "Docker MCP Server Management Information"
- "Docker MCP Unicode Encoding Fix Applied"

Access with: `mcp__cipher__ask_cipher` searching for "Docker MCP"