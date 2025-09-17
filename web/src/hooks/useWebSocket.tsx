import { useCallback, useEffect, useRef, useState } from "react";
import { useAdminAuth } from "./useAdminAuth";

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

interface WebSocketHookOptions {
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  debug?: boolean;
}

interface WebSocketHookReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  sendMessage: (type: string, data: any) => void;
  lastMessage: WebSocketMessage | null;
  connect: () => void;
  disconnect: () => void;
  subscribe: (subscription: string) => void;
  unsubscribe: (subscription: string) => void;
}

export const useWebSocket = (options: WebSocketHookOptions = {}): WebSocketHookReturn => {
  const {
    autoConnect = false,
    reconnectAttempts = 5,
    reconnectDelay = 3000,
    debug = false,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);
  const subscriptionsRef = useRef<Set<string>>(new Set());

  const { session, isAuthenticated } = useAdminAuth();

  const log = useCallback(
    (message: string, data?: any) => {
      if (debug) {
        console.log(`[WebSocket] ${message}`, data || "");
      }
    },
    [debug]
  );

  const connect = useCallback(() => {
    if (!isAuthenticated || !session) {
      setError("Admin authentication required");
      return;
    }

    if (
      wsRef.current?.readyState === WebSocket.CONNECTING ||
      wsRef.current?.readyState === WebSocket.OPEN
    ) {
      log("Already connected or connecting");
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      // Build proper WebSocket URL to backend
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = import.meta.env.DEV ? window.location.host : window.location.host;
      const wsUrl = `${protocol}//${host}/ws/admin`;
      log("Connecting to WebSocket", wsUrl);

      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        log("WebSocket connected");

        // Send authentication message first
        if (session?.session_id) {
          const authMessage = {
            type: "auth",
            session_id: session.session_id,
            timestamp: new Date().toISOString(),
          };
          wsRef.current?.send(JSON.stringify(authMessage));
          log("Sent auth message", authMessage);
        }

        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        reconnectCountRef.current = 0;

        // Resubscribe to subscriptions after auth
        setTimeout(() => {
          subscriptionsRef.current.forEach((subscription) => {
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
              const message = {
                type: "subscribe",
                data: { subscription },
                timestamp: new Date().toISOString(),
              };
              wsRef.current.send(JSON.stringify(message));
            }
          });
        }, 100);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          log("Received message", message);
          setLastMessage(message);
        } catch (_err) {
          log("Error parsing message", event.data);
          setError("Failed to parse WebSocket message");
        }
      };

      wsRef.current.onclose = (event) => {
        log("WebSocket closed", { code: event.code, reason: event.reason });
        setIsConnected(false);
        setIsConnecting(false);

        // Attempt reconnection if not a clean close
        if (event.code !== 1000 && reconnectCountRef.current < reconnectAttempts) {
          const delay = Math.min(reconnectDelay * 2 ** reconnectCountRef.current, 30000);
          log(
            `Reconnecting in ${delay}ms (attempt ${reconnectCountRef.current + 1}/${reconnectAttempts})`
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectCountRef.current++;
            connect();
          }, delay);

          setError(
            `Connection lost. Reconnecting... (${reconnectCountRef.current}/${reconnectAttempts})`
          );
        } else if (reconnectCountRef.current >= reconnectAttempts) {
          setError("Failed to reconnect after maximum attempts");
        }
      };

      wsRef.current.onerror = (event) => {
        log("WebSocket error", event);
        setError("WebSocket connection error");
        setIsConnecting(false);
      };
    } catch (err) {
      log("Error creating WebSocket", err);
      setError("Failed to create WebSocket connection");
      setIsConnecting(false);
    }
  }, [isAuthenticated, session, reconnectAttempts, reconnectDelay, log]);

  const disconnect = useCallback(() => {
    log("Disconnecting WebSocket");

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, "Manual disconnect");
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
    setError(null);
    reconnectCountRef.current = 0;
  }, [log]);

  const sendMessage = useCallback(
    (type: string, data: any) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        log("Cannot send message - WebSocket not connected");
        setError("Cannot send message - not connected");
        return;
      }

      const message = {
        type,
        data,
        timestamp: new Date().toISOString(),
      };

      try {
        wsRef.current.send(JSON.stringify(message));
        log("Sent message", message);
      } catch (err) {
        log("Error sending message", err);
        setError("Failed to send message");
      }
    },
    [log]
  );

  const subscribe = useCallback(
    (subscription: string) => {
      subscriptionsRef.current.add(subscription);
      sendMessage("subscribe", { subscription });
      log("Subscribed to", subscription);
    },
    [sendMessage, log]
  );

  const unsubscribe = useCallback(
    (subscription: string) => {
      subscriptionsRef.current.delete(subscription);
      sendMessage("unsubscribe", { subscription });
      log("Unsubscribed from", subscription);
    },
    [sendMessage, log]
  );

  // Auto-connect effect
  useEffect(() => {
    if (autoConnect && isAuthenticated && !isConnected && !isConnecting) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, isAuthenticated, connect, disconnect, isConnected, isConnecting]);

  // Cleanup effect
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return {
    isConnected,
    isConnecting,
    error,
    sendMessage,
    lastMessage,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
  };
};

export default useWebSocket;
