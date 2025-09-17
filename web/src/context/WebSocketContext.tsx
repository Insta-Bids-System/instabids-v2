import React, { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { buildWsUrl, WS_ENDPOINTS } from '../config/api';
import { useSharedWebSocket } from '../hooks/useSharedWebSocket';

interface AgentActivityEvent {
  type: 'agent-activity';
  entityType: string;
  entityId: string;
  agentName: string;
  action: string;
  status: 'working' | 'completed' | 'error';
  timestamp: string;
  changedFields: string[];
}

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface WebSocketContextType {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  subscribe: (id: string, callback: (event: AgentActivityEvent) => void) => () => void;
  sendMessage: (message: any) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
  userId?: string;
  useSharedWorker?: boolean; // Enable SharedWorker pattern
}

/**
 * WebSocket Provider - Single WebSocket connection shared across all components
 * Can use SharedWorker pattern to share connection across all tabs/windows
 */
export function WebSocketProvider({ children, userId, useSharedWorker = false }: WebSocketProviderProps) {
  // Use SharedWorker pattern if enabled
  const sharedWebSocket = useSharedWorker ? useSharedWebSocket(userId) : null;
  
  // Regular WebSocket state (used when SharedWorker is disabled)
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const subscribersRef = useRef<Map<string, (event: AgentActivityEvent) => void>>(new Map());
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000;
  const isConnectingRef = useRef(false);
  const isMountedRef = useRef(true);

  const connect = () => {
    // Prevent multiple connection attempts
    if (!isMountedRef.current || isConnectingRef.current) {
      return;
    }
    
    if (wsRef.current?.readyState === WebSocket.CONNECTING || 
        wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    isConnectingRef.current = true;

    // Always pass a user_id, even if it's "anonymous"
    const params = { user_id: userId || 'anonymous' };
    const wsUrl = buildWsUrl(WS_ENDPOINTS.AGENT_ACTIVITY, params);
    
    try {
      console.log('[WebSocket] Connecting to:', wsUrl);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (isMountedRef.current) {
          setIsConnected(true);
          reconnectAttemptsRef.current = 0;
          isConnectingRef.current = false;
          console.log('[WebSocket] Connected successfully');
        }
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Handle agent activity events
          if (message.type === 'agent-activity') {
            const agentEvent = message as AgentActivityEvent;
            
            // Notify all subscribers
            subscribersRef.current.forEach((callback) => {
              callback(agentEvent);
            });
          }
        } catch (error) {
          console.error('[WebSocket] Error parsing message:', error);
        }
      };

      ws.onclose = (event) => {
        isConnectingRef.current = false;
        if (isMountedRef.current) {
          setIsConnected(false);
          console.log('[WebSocket] Disconnected, code:', event.code, 'reason:', event.reason);
          
          // Attempt reconnection if not a clean close and component is still mounted
          if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts && isMountedRef.current) {
            const delay = Math.min(reconnectDelay * Math.pow(2, reconnectAttemptsRef.current), 30000);
            console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})`);
            
            reconnectTimeoutRef.current = setTimeout(() => {
              if (isMountedRef.current) {
                reconnectAttemptsRef.current++;
                connect();
              }
            }, delay);
          }
        }
      };

      ws.onerror = (error) => {
        if (isMountedRef.current) {
          console.error('[WebSocket] Connection error:', error);
          setIsConnected(false);
        }
        isConnectingRef.current = false;
      };

    } catch (error) {
      console.error('[WebSocket] Failed to create connection:', error);
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    
    setIsConnected(false);
    reconnectAttemptsRef.current = 0;
  };

  useEffect(() => {
    isMountedRef.current = true;
    
    // Only connect regular WebSocket if not using SharedWorker
    if (!useSharedWorker) {
      // Small delay to avoid React StrictMode double-mount issues
      const connectTimeout = setTimeout(() => {
        if (isMountedRef.current) {
          connect();
        }
      }, 100);
      
      return () => {
        clearTimeout(connectTimeout);
        isMountedRef.current = false;
        if (!useSharedWorker) {
          disconnect();
        }
      };
    }
    
    return () => {
      isMountedRef.current = false;
    };
  }, [userId, useSharedWorker]);
  
  // Subscribe to SharedWorker messages if enabled
  useEffect(() => {
    if (useSharedWorker && sharedWebSocket) {
      const unsubscribe = sharedWebSocket.subscribe((message) => {
        // Handle agent activity events
        if (message.type === 'agent-activity') {
          const agentEvent = message as AgentActivityEvent;
          // Notify all subscribers
          subscribersRef.current.forEach((callback) => {
            callback(agentEvent);
          });
        }
      });
      
      return unsubscribe;
    }
  }, [useSharedWorker, sharedWebSocket]);

  const subscribe = (id: string, callback: (event: AgentActivityEvent) => void) => {
    subscribersRef.current.set(id, callback);
    
    // Return unsubscribe function
    return () => {
      subscribersRef.current.delete(id);
    };
  };

  const sendMessage = (message: any) => {
    if (useSharedWorker && sharedWebSocket) {
      sharedWebSocket.sendMessage(message);
    } else if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('[WebSocket] Cannot send message - not connected');
    }
  };

  const value: WebSocketContextType = {
    isConnected: useSharedWorker ? (sharedWebSocket?.isConnected || false) : isConnected,
    lastMessage: useSharedWorker ? (sharedWebSocket?.lastMessage || null) : lastMessage,
    subscribe,
    sendMessage
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

/**
 * Hook to use the WebSocket context
 */
export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
}