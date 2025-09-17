# Docker MCP Tools Documentation
**Last Updated**: August 5, 2025
**Status**: FULLY OPERATIONAL with timeout fixes applied

## Overview
The Docker MCP tool provides 22+ specialized tools for managing Docker containers, with 8 InstaBids-specific debugging tools. All tools now include proper timeout handling to prevent hanging.

## Generic Docker Tools (14 tools)

### Container Management
1. **create-container** - Create a new standalone Docker container
2. **deploy-compose** - Deploy a Docker Compose stack
3. **list-containers** - List all Docker containers
4. **get-logs** - Retrieve the latest logs for a specified Docker container
5. **container-stats** - Get real-time stats for a container (CPU, memory, network)
6. **exec-command** - Execute a command inside a running container
7. **inspect-container** - Get detailed information about a container
8. **restart-container** - Restart a Docker container
9. **stop-container** - Stop a running Docker container
10. **start-container** - Start a stopped Docker container
11. **remove-container** - Remove a stopped container
12. **container-health** - Get health check status of a container
13. **container-ports** - Get port mappings for a container
14. **container-env** - Get environment variables from a container

### Network & Image Management
15. **list-networks** - List all Docker networks
16. **inspect-network** - Get detailed information about a Docker network
17. **list-images** - List all Docker images

## InstaBids-Specific Tools (8 tools) ✨

### System Health Monitoring
18. **check-instabids-health** - Comprehensive health check of all InstaBids services
   - Checks Frontend, Backend, Supabase, and MailHog containers
   - Detects WebSocket errors and admin panel issues
   - **Timeout**: 3 seconds per container

### WebSocket Testing
19. **test-websocket-connections** - Test WebSocket connections for admin panel and bid updates
   - Parameters: `test_type` (admin/bid-updates/messaging/all)
   - Detects connection issues and missing parameters
   - **Timeout**: 5 seconds

### Bid Card Monitoring
20. **monitor-bid-cards** - Monitor bid card system health and recent activity
   - Parameters: `minutes` (default: 5)
   - Tracks API activity, errors, and conversions
   - **Timeout**: 5 seconds

### API Endpoint Testing
21. **check-api-endpoints** - Test critical API endpoints for responsiveness
   - Parameters: `endpoint_group` (auth/projects/messaging/admin/iris/all)
   - Checks success/error rates for endpoints
   - **Timeout**: 5 seconds

### Database Connectivity
22. **check-database-connections** - Verify database connectivity and recent query performance
   - Monitors Supabase requests and connection pool issues
   - **Timeout**: 5 seconds

### Error Analysis
23. **analyze-error-logs** - Analyze recent error logs across all services
   - Parameters: `minutes` (default: 10), `service` (frontend/backend/all)
   - Shows first 5 errors from each service
   - **Timeout**: 5 seconds per service

### Real-time Updates
24. **check-realtime-updates** - Verify real-time update systems (polling, WebSockets) are working
   - Checks HTTP polling and WebSocket connections
   - **Timeout**: 5 seconds

### Messaging System
25. **test-messaging-system** - Test messaging system including filters and contractor aliases
   - Monitors messaging API, LangGraph agent, and content filtering
   - **Timeout**: 5 seconds

## Usage Examples

```bash
# Check overall system health
mcp__docker__check-instabids-health

# Test admin WebSocket specifically
mcp__docker__test-websocket-connections with test_type="admin"

# Monitor bid cards from last 10 minutes
mcp__docker__monitor-bid-cards with minutes=10

# Check all API endpoints
mcp__docker__check-api-endpoints with endpoint_group="all"

# Analyze backend errors from last 5 minutes
mcp__docker__analyze-error-logs with minutes=5, service="backend"
```

## Key Fixes Applied

### 1. Timeout Implementation
All InstaBids-specific tools now use `asyncio.wait_for` with 5-second timeouts to prevent hanging when Docker logs are slow to retrieve.

### 2. UTF-8 Encoding
All log retrieval includes proper UTF-8 decoding with error replacement to handle special characters.

### 3. Removed `since` Parameter
Replaced problematic `since=f"{minutes}m"` with `tail=100` or `tail=200` to avoid Docker API timeouts.

## Known Issues

### Admin WebSocket Error
The backend logs show a critical error:
```
TypeError: AdminWebSocketManager.broadcast_to_others() missing 1 required positional argument: 'exclude_client'
```
This needs to be fixed in the backend code at `/app/admin/websocket_manager.py` line 131.

## Benefits Over Generic Docker Commands

1. **InstaBids-Aware**: Tools understand the specific services and their relationships
2. **Error Detection**: Automatically detects known issues like WebSocket errors
3. **Timeout Protection**: Won't hang indefinitely like raw Docker commands
4. **Aggregated Views**: Combines information from multiple sources for comprehensive health checks
5. **Pattern Recognition**: Uses regex to find specific errors and patterns in logs

## Next Steps

1. Fix the admin WebSocket error in the backend code
2. Add more specific bid card lifecycle monitoring
3. Create a dashboard that uses these tools for real-time monitoring
4. Add automated alerting based on error patterns detected