# System Instability Root Cause Analysis
**Date**: August 20, 2025
**Issue**: Intermittent failures, spinning tabs, inconsistent API responses

## 🔴 CRITICAL PROBLEMS IDENTIFIED

### 1. **WebSocket Connection Chaos**
- **Problem**: Multiple WebSocket connections opening/closing rapidly
- **Evidence**: Logs show connections opening and closing within seconds
- **Impact**: Each tab creates its own WebSocket, they're fighting for resources
- **Result**: Race conditions, dropped messages, incomplete state updates

### 2. **Vite Proxy Configuration Issue**
- **Problem**: `process.env.DOCKER_ENV` checked at BUILD time, not RUNTIME
- **Evidence**: Proxy tries to use localhost even in Docker environment
- **Impact**: Intermittent connection failures when containers restart with new IPs
- **Result**: Some requests work (cached), others fail (new connections)

### 3. **Container Network Instability**
- **Problem**: Backend container restarting changes internal Docker IP
- **Evidence**: Frontend tries to connect to old IP (172.18.0.6)
- **Impact**: Cached connections work, new ones fail
- **Result**: Inconsistent behavior across different components

### 4. **No Connection Pooling or Retry Logic**
- **Problem**: Frontend makes direct API calls without retry mechanism
- **Evidence**: Single failure = permanent spinning
- **Impact**: No recovery from transient network issues
- **Result**: User must manually refresh to recover

### 5. **Memory Leak in Frontend**
- **Problem**: Frontend using 150MB+ memory (high for React app)
- **Evidence**: `docker stats` shows 150.7MiB usage
- **Impact**: Old connections/listeners not being cleaned up
- **Result**: Performance degradation over time

## 🎯 WHY THIS HAPPENS

### The Cascade Effect:
1. User opens multiple tabs → Multiple WebSocket connections created
2. Backend handles some, drops others (connection limit/timing issues)
3. Dropped connections leave frontend in "waiting" state (spinning)
4. Meanwhile, some API calls succeed (those that get through)
5. React components re-render, create MORE connections
6. Old connections not cleaned up properly
7. Eventually, system is overwhelmed with orphaned connections

### The Docker Layer:
1. Containers restart (manually or due to errors)
2. Container gets new internal IP address
3. Vite proxy still has old IP cached
4. Some requests use old connection (fail), some create new (succeed)
5. Inconsistent behavior across the app

## ✅ IMMEDIATE FIXES

### 1. **Fix Vite Proxy Configuration**
```javascript
// vite.config.ts - FIXED VERSION
export default defineConfig(({ mode }) => {
  return {
    server: {
      proxy: {
        '/api': {
          // Always use service name in Docker
          target: 'http://instabids-backend:8008',
          changeOrigin: true,
          secure: false,
          configure: (proxy, options) => {
            proxy.on('error', (err, req, res) => {
              console.log('proxy error', err);
              // Retry logic here
            });
          }
        }
      }
    }
  }
});
```

### 2. **Add WebSocket Manager**
- Singleton WebSocket connection per browser (not per tab)
- Automatic reconnection on failure
- Message queueing during reconnection

### 3. **Add API Retry Logic**
```javascript
// api.ts - Add retry wrapper
async function apiCallWithRetry(fn, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i)));
    }
  }
}
```

### 4. **Container Health Checks**
```yaml
# docker-compose.yml
services:
  instabids-backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## 🚀 PERMANENT SOLUTIONS

### 1. **Use Static Backend URL**
Instead of relying on Docker service discovery, use host networking:
```yaml
services:
  instabids-backend:
    network_mode: "host"  # Use host network
    ports:
      - "8008:8008"
```

### 2. **Implement Connection Pool**
- Use a connection manager library (e.g., socket.io-client)
- Maintain single connection per browser session
- Share across all tabs using BroadcastChannel API

### 3. **Add Circuit Breaker Pattern**
- Detect failing services and stop trying
- Provide fallback UI (cached data, offline mode)
- Automatically resume when service recovers

### 4. **Proper Error Boundaries**
- Catch component errors
- Show meaningful error messages
- Provide retry buttons instead of infinite spinning

## 📋 ACTION ITEMS

### Immediate (Do Now):
1. ✅ Restart all containers fresh: `docker-compose down && docker-compose up -d`
2. ✅ Clear browser cache completely
3. ✅ Use only ONE browser tab for testing

### Short-term (This Week):
1. Fix Vite proxy configuration (remove environment check)
2. Add retry logic to API calls
3. Implement WebSocket singleton
4. Add health checks to docker-compose

### Long-term (This Month):
1. Implement proper connection pooling
2. Add circuit breaker pattern
3. Set up monitoring/alerting for connection issues
4. Consider moving to more stable architecture (e.g., Next.js with SSR)

## 🎬 HOW TO WORK WITH CURRENT SYSTEM

### Until fixes are implemented:
1. **Use single tab**: Don't open multiple tabs of the app
2. **Full refresh on issues**: Ctrl+Shift+R when things break
3. **Monitor containers**: Keep `docker logs -f instabids-instabids-backend-1` open
4. **Restart cleanly**: When in doubt: `docker-compose restart`
5. **Check connections**: `docker exec instabids-instabids-backend-1 netstat -an | grep 8008`

## 🔍 DEBUGGING COMMANDS

```bash
# Check if backend is actually responding
curl http://localhost:8008

# Check container health
docker ps

# Check active connections
docker exec instabids-instabids-backend-1 netstat -an | grep ESTABLISHED

# Monitor WebSocket issues
docker logs instabids-instabids-backend-1 --tail 100 -f | grep WebSocket

# Check memory usage
docker stats --no-stream
```

## SUMMARY

The root cause is a **poorly configured proxy system** combined with **no error recovery** and **WebSocket connection chaos**. The system works sometimes because cached connections succeed, but fails when new connections are needed. This creates the intermittent behavior you're experiencing.

The fix requires both immediate workarounds (single tab, manual refreshes) and proper architectural changes (connection pooling, retry logic, health checks).