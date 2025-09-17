import { useEffect, useRef, useState } from 'react';
import { buildWsUrl, WS_ENDPOINTS } from '../config/api';

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

/**
 * Real-time WebSocket hook for agent activity events
 * Connects to backend WebSocket and receives live agent updates
 */
export function useWebSocket(userId?: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const subscribersRef = useRef<Map<string, (event: AgentActivityEvent) => void>>(new Map());

  useEffect(() => {
    const params = userId ? { user_id: userId } : undefined;
    const wsUrl = buildWsUrl(WS_ENDPOINTS.AGENT_ACTIVITY, params);
    
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket connected for agent activity');
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
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected');
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [userId]);

  const subscribe = (id: string, callback: (event: AgentActivityEvent) => void) => {
    subscribersRef.current.set(id, callback);
    
    return () => {
      subscribersRef.current.delete(id);
    };
  };

  const sendMessage = (message: any) => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  return {
    isConnected,
    lastMessage,
    subscribe,
    unsubscribe: subscribe, // For backward compatibility - subscribe returns unsubscribe
    sendMessage
  };
}