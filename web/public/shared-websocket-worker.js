// Shared WebSocket Worker - ONE connection for ALL tabs/windows
// With full instrumentation for monitoring

let ws = null;
let ports = [];
let reconnectTimer = null;
let backoffMs = 1000;
const MAX_BACKOFF = 30000;

// Debug metrics
let activeSocketCount = 0;
let totalReconnects = 0;
let connectionStartTime = null;
let lastConnectTime = null;
let consecutiveFailures = 0;

// Health heartbeat interval
let healthInterval = null;

function connect() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    console.log('[SharedWS] Already connected, skipping reconnect');
    return;
  }
  
  connectionStartTime = Date.now();
  console.log('[SharedWS] Connecting... (attempt #' + (totalReconnects + 1) + ')');
  console.log('[SharedWS] Active sockets before connect:', activeSocketCount);
  
  // Use localhost URL which will work both in dev and Docker
  // The frontend container can reach the backend through Docker network
  const wsUrl = `ws://localhost:8008/ws/agent-activity`;
  
  try {
    ws = new WebSocket(wsUrl);
    activeSocketCount = 1; // Mark as active
    
    ws.onopen = () => {
      const connectTime = Date.now() - connectionStartTime;
      lastConnectTime = Date.now();
      consecutiveFailures = 0;
      
      console.log(`[SharedWS] Connected in ${connectTime}ms!`);
      console.log('[SharedWS] Active sockets:', activeSocketCount);
      
      backoffMs = 1000; // Reset backoff
      
      broadcast({ 
        type: 'connected', 
        timestamp: Date.now(),
        connectTime: connectTime,
        activeSocketCount: activeSocketCount
      });
      
      sendHealthUpdate();
    };
    
    ws.onmessage = (event) => {
      broadcast({ 
        type: 'message', 
        data: event.data, 
        timestamp: Date.now() 
      });
    };
    
    ws.onerror = (error) => {
      consecutiveFailures++;
      console.error('[SharedWS] Error:', error);
      console.error('[SharedWS] Consecutive failures:', consecutiveFailures);
      
      broadcast({ 
        type: 'error', 
        error: error.message,
        consecutiveFailures: consecutiveFailures
      });
    };
    
    ws.onclose = (event) => {
      console.log('[SharedWS] Disconnected:', event.code, event.reason);
      activeSocketCount = 0; // Mark as inactive
      ws = null;
      
      broadcast({ 
        type: 'disconnected',
        code: event.code,
        reason: event.reason,
        activeSocketCount: activeSocketCount
      });
      
      sendHealthUpdate();
      
      // Exponential backoff with jitter
      const jitter = Math.random() * 1000;
      const delay = Math.min(backoffMs + jitter, MAX_BACKOFF);
      backoffMs = backoffMs * 2;
      totalReconnects++;
      
      console.log(`[SharedWS] Will reconnect in ${Math.round(delay)}ms (backoff: ${backoffMs}ms)`);
      
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connect, delay);
    };
  } catch (error) {
    console.error('[SharedWS] Failed to create WebSocket:', error);
    activeSocketCount = 0;
    sendHealthUpdate();
  }
}

function broadcast(message) {
  ports.forEach(port => {
    try {
      port.postMessage(message);
    } catch (e) {
      // Port might be closed
      console.error('[SharedWS] Failed to send to port:', e);
    }
  });
}

function sendHealthUpdate() {
  const health = {
    type: 'ws:health',
    data: {
      active: activeSocketCount,
      ports: ports.length,
      reconnects: totalReconnects,
      consecutiveFailures: consecutiveFailures,
      lastConnectTime: lastConnectTime,
      wsState: ws ? ws.readyState : -1,
      timestamp: Date.now()
    }
  };
  
  broadcast(health);
  
  // Also log to console for debugging
  console.log('[SharedWS] Health:', health.data);
}

function startHealthHeartbeat() {
  if (healthInterval) clearInterval(healthInterval);
  
  healthInterval = setInterval(() => {
    sendHealthUpdate();
  }, 2000); // Every 2 seconds
}

// Handle new tab/window connections
onconnect = (e) => {
  const port = e.ports[0];
  ports.push(port);
  
  console.log('[SharedWS] New client connected, total ports:', ports.length);
  console.log('[SharedWS] Active WebSocket connections:', activeSocketCount);
  
  port.onmessage = (event) => {
    const { type, data } = event.data || {};
    
    switch(type) {
      case 'send':
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify(data));
        } else {
          console.warn('[SharedWS] Cannot send - not connected');
        }
        break;
        
      case 'disconnect':
        // Remove this port from list
        ports = ports.filter(p => p !== port);
        console.log('[SharedWS] Client disconnected, remaining:', ports.length);
        
        // If no more clients, close the WebSocket
        if (ports.length === 0) {
          console.log('[SharedWS] No clients remaining, closing WebSocket');
          if (ws) {
            ws.close(1000, 'No clients');
            ws = null;
            activeSocketCount = 0;
          }
          clearInterval(healthInterval);
        }
        break;
        
      case 'status':
        port.postMessage({
          type: 'status',
          data: {
            isConnected: ws && ws.readyState === WebSocket.OPEN,
            connectedPorts: ports.length,
            activeSocketCount: activeSocketCount,
            totalReconnects: totalReconnects
          }
        });
        break;
        
      case 'health':
        sendHealthUpdate();
        break;
        
      case 'init':
        // Initial setup from client
        console.log('[SharedWS] Client init with userId:', data?.userId);
        break;
    }
  };
  
  // Send current connection status to new client
  if (ws && ws.readyState === WebSocket.OPEN) {
    port.postMessage({ 
      type: 'connected',
      activeSocketCount: activeSocketCount
    });
  } else {
    port.postMessage({ 
      type: 'disconnected',
      activeSocketCount: activeSocketCount
    });
  }
  
  // Send immediate health update to new client
  sendHealthUpdate();
  
  // Start connection if not already connected
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    connect();
  }
  
  // Start health heartbeat if not running
  if (!healthInterval) {
    startHealthHeartbeat();
  }
  
  port.start();
};