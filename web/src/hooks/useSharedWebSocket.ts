import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface SharedWebSocketState {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: any) => void;
  subscribe: (callback: (message: WebSocketMessage) => void) => () => void;
}

/**
 * Hook to use a shared WebSocket connection across all tabs/windows
 * This prevents the "WebSocket stampede" problem where every tab creates its own connection
 */
export function useSharedWebSocket(userId?: string): SharedWebSocketState {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const workerRef = useRef<SharedWorker | null>(null);
  const portRef = useRef<MessagePort | null>(null);
  const subscribersRef = useRef<Set<(message: WebSocketMessage) => void>>(new Set());

  // Initialize SharedWorker connection
  useEffect(() => {
    // DISABLED: SharedWorker causing connection flapping issues
    console.log('[SharedWebSocket] SharedWorker disabled - components should use WebSocketContext instead');
    return;
    
    // Check if SharedWorker is supported
    if (!window.SharedWorker) {
      console.warn('[SharedWebSocket] SharedWorker not supported, falling back to regular WebSocket');
      // TODO: Implement fallback to regular WebSocket
      return;
    }

    try {
      // Create SharedWorker instance
      console.log('[SharedWebSocket] Creating SharedWorker...');
      const worker = new SharedWorker('/shared-websocket-worker.js');
      workerRef.current = worker;
      portRef.current = worker.port;

      // Initialize debug metrics on window
      if (typeof window !== 'undefined') {
        (window as any).__WS_DEBUG__ = {
          activeSocketCount: 0,
          lastEvent: null,
          totalReconnects: 0,
          connectedPorts: 0
        };
      }

      // Handle messages from the SharedWorker
      worker.port.onmessage = (event) => {
        const { type, data } = event.data;

        switch (type) {
          case 'connected':
            console.log('[SharedWebSocket] Connected via SharedWorker');
            setIsConnected(true);
            // Update debug metrics
            if ((window as any).__WS_DEBUG__) {
              (window as any).__WS_DEBUG__.activeSocketCount = data?.activeSocketCount || 1;
              (window as any).__WS_DEBUG__.lastEvent = Date.now();
            }
            break;

          case 'disconnected':
            console.log('[SharedWebSocket] Disconnected');
            setIsConnected(false);
            // Update debug metrics
            if ((window as any).__WS_DEBUG__) {
              (window as any).__WS_DEBUG__.activeSocketCount = data?.activeSocketCount || 0;
              (window as any).__WS_DEBUG__.lastEvent = Date.now();
            }
            break;

          case 'message':
            // WebSocket message received
            setLastMessage(data);
            // Notify all subscribers
            subscribersRef.current.forEach(callback => {
              try {
                callback(data);
              } catch (error) {
                console.error('[SharedWebSocket] Subscriber error:', error);
              }
            });
            break;

          case 'error':
            console.error('[SharedWebSocket] Worker error:', data);
            break;

          case 'stats':
            console.log('[SharedWebSocket] Connection stats:', data);
            break;

          case 'ws:health':
            // Update debug metrics with health data
            if ((window as any).__WS_DEBUG__ && data?.data) {
              (window as any).__WS_DEBUG__.activeSocketCount = data.data.active || 0;
              (window as any).__WS_DEBUG__.totalReconnects = data.data.reconnects || 0;
              (window as any).__WS_DEBUG__.connectedPorts = data.data.ports || 0;
              (window as any).__WS_DEBUG__.lastEvent = Date.now();
            }
            break;
        }
      };

      // Start the worker
      worker.port.start();

      // Send initial configuration with user ID
      worker.port.postMessage({
        type: 'init',
        userId: userId || 'anonymous'
      });

      // Request connection status
      worker.port.postMessage({ type: 'status' });

    } catch (error) {
      console.error('[SharedWebSocket] Failed to create SharedWorker:', error);
    }

    // Cleanup on unmount
    return () => {
      if (portRef.current) {
        // Notify worker that this port is closing
        portRef.current.postMessage({ type: 'close' });
        portRef.current.close();
      }
    };
  }, [userId]);

  // Send message through SharedWorker
  const sendMessage = useCallback((message: any) => {
    if (portRef.current) {
      portRef.current.postMessage({
        type: 'send',
        data: message
      });
    } else {
      console.warn('[SharedWebSocket] Cannot send message - worker not initialized');
    }
  }, []);

  // Subscribe to WebSocket messages
  const subscribe = useCallback((callback: (message: WebSocketMessage) => void) => {
    subscribersRef.current.add(callback);

    // Return unsubscribe function
    return () => {
      subscribersRef.current.delete(callback);
    };
  }, []);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    subscribe
  };
}

/**
 * Hook to use shared WebSocket with automatic reconnection on user change
 */
export function useUserWebSocket(userId?: string): SharedWebSocketState {
  const webSocket = useSharedWebSocket(userId);
  const previousUserIdRef = useRef(userId);
  const portRef = useRef<MessagePort | null>(null);

  useEffect(() => {
    // If user ID changed, reinitialize connection
    if (previousUserIdRef.current !== userId && portRef.current) {
      console.log('[SharedWebSocket] User changed, reinitializing...');
      portRef.current?.postMessage({
        type: 'init',
        userId: userId || 'anonymous'
      });
      previousUserIdRef.current = userId;
    }
  }, [userId]);

  return webSocket;
}

/**
 * Hook for monitoring WebSocket connection health
 */
export function useWebSocketHealth(): { 
  isHealthy: boolean; 
  connectionCount: number;
  lastHeartbeat: Date | null;
} {
  const [isHealthy, setIsHealthy] = useState(true);
  const [connectionCount, setConnectionCount] = useState(0);
  const [lastHeartbeat, setLastHeartbeat] = useState<Date | null>(null);

  useEffect(() => {
    if (!window.SharedWorker) return;

    const worker = new SharedWorker('/shared-websocket-worker.js');
    
    const checkHealth = () => {
      worker.port.postMessage({ type: 'health' });
    };

    worker.port.onmessage = (event) => {
      if (event.data.type === 'health') {
        setIsHealthy(event.data.data.isConnected);
        setConnectionCount(event.data.data.connectedPorts);
        setLastHeartbeat(new Date());
      }
    };

    worker.port.start();

    // Check health immediately and then every 5 seconds
    checkHealth();
    const interval = setInterval(checkHealth, 5000);

    return () => {
      clearInterval(interval);
      worker.port.close();
    };
  }, []);

  return { isHealthy, connectionCount, lastHeartbeat };
}