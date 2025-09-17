import { useState, useEffect, useRef } from 'react';
import { useWebSocketContext } from '../context/WebSocketContext';

interface AgentActivity {
  entityType: 'bid_card' | 'potential_bid_card' | 'repair_item';
  entityId: string;
  agentName: string;
  action: string;
  status: 'working' | 'completed' | 'error';
  timestamp: number;
}

/**
 * Hook to show visual feedback when agents are modifying entities
 * Returns animation states for glowing, pulsing, and agent indicators
 * 
 * REAL-TIME ONLY: No mock data, no fallbacks.
 * Only shows activity when actual agent events occur via WebSocket.
 */
export function useAgentActivity(entityType: string, entityId: string) {
  const [isBeingModified, setIsBeingModified] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [lastChange, setLastChange] = useState<any>(null);
  const [highlightFields, setHighlightFields] = useState<Set<string>>(new Set());
  const activityTimeout = useRef<NodeJS.Timeout>();
  const highlightTimeout = useRef<NodeJS.Timeout>();

  // Real WebSocket integration using shared context
  const { subscribe } = useWebSocketContext();

  useEffect(() => {
    // Subscribe to agent activity events for this specific entity
    const unsubscribe = subscribe(`${entityType}-${entityId}`, (event) => {
      // Only handle events for this specific entity
      if (event.entityType === entityType && event.entityId === entityId) {
        if (event.status === 'working') {
          // Agent started working on this entity
          setIsBeingModified(true);
          setCurrentAgent(event.agentName);
          
          // Clear previous timeout
          if (activityTimeout.current) {
            clearTimeout(activityTimeout.current);
          }
          
          // Auto-clear after 30 seconds (failsafe)
          activityTimeout.current = setTimeout(() => {
            setIsBeingModified(false);
            setCurrentAgent(null);
          }, 30000);
        } else if (event.status === 'completed') {
          // Agent completed work - show success glow
          setIsBeingModified(false);
          setLastChange(event);
          
          // Highlight changed fields if provided
          if (event.changedFields && event.changedFields.length > 0) {
            setHighlightFields(new Set(event.changedFields));
            
            // Clear highlights after 3 seconds
            if (highlightTimeout.current) {
              clearTimeout(highlightTimeout.current);
            }
            highlightTimeout.current = setTimeout(() => {
              setHighlightFields(new Set());
            }, 3000);
          }
          
          // Clear agent indicator after 1 second
          setTimeout(() => {
            setCurrentAgent(null);
            setLastChange(null);
          }, 1000);
        }
      }
    });

    return () => {
      unsubscribe();
      if (activityTimeout.current) clearTimeout(activityTimeout.current);
      if (highlightTimeout.current) clearTimeout(highlightTimeout.current);
    };
  }, [entityType, entityId, subscribe]);


  return {
    isBeingModified,
    currentAgent,
    lastChange,
    highlightedFields: Array.from(highlightFields), // Convert Set to Array for easier usage
    // Helper classes for styling
    containerClass: isBeingModified 
      ? 'agent-working' 
      : lastChange 
        ? 'agent-completed' 
        : '',
    pulseClass: isBeingModified ? 'animate-pulse' : '',
    glowClass: lastChange ? 'animate-glow' : '',
  };
}

/**
 * Hook for field-level change highlighting
 */
export function useFieldHighlight(fieldName: string, value: any, duration = 2000) {
  const [isHighlighted, setIsHighlighted] = useState(false);
  const prevValue = useRef(value);
  const timeout = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // Detect value change
    if (JSON.stringify(prevValue.current) !== JSON.stringify(value)) {
      setIsHighlighted(true);
      prevValue.current = value;

      // Clear previous timeout
      if (timeout.current) {
        clearTimeout(timeout.current);
      }

      // Remove highlight after duration
      timeout.current = setTimeout(() => {
        setIsHighlighted(false);
      }, duration);
    }
  }, [value, duration]);

  useEffect(() => {
    return () => {
      if (timeout.current) clearTimeout(timeout.current);
    };
  }, []);

  return {
    isHighlighted,
    className: isHighlighted ? 'field-highlight' : '',
  };
}