/**
 * React Hook for Server-Sent Events (SSE) Chat Streaming
 * Provides real-time streaming chat responses with GPT-5/GPT-4o fallback
 */
import { useState, useEffect, useRef, useCallback } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

interface StreamChatRequest {
  messages: Message[];
  conversation_id: string;
  user_id: string;
  max_tokens?: number;
  model_preference?: 'gpt-5' | 'gpt-4o';
}

interface StreamMetrics {
  model_used: string;
  first_token_ms: number | null;
  total_time_ms: number;
  fallback_used: boolean;
  fallback_reason?: string;
}

interface UseSSEChatStreamOptions {
  onMessage?: (content: string) => void;
  onComplete?: (fullMessage: string, metrics: StreamMetrics) => void;
  onError?: (error: Error) => void;
  endpoint?: string;
}

interface UseSSEChatStreamReturn {
  streamMessage: (request: StreamChatRequest) => Promise<void>;
  currentMessage: string;
  isStreaming: boolean;
  isConnected: boolean;
  metrics: StreamMetrics | null;
  error: string | null;
  abort: () => void;
}

export const useSSEChatStream = (
  options: UseSSEChatStreamOptions = {}
): UseSSEChatStreamReturn => {
  const {
    onMessage,
    onComplete,
    onError,
    endpoint = '/api/cia/stream'
  } = options;

  const [currentMessage, setCurrentMessage] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [metrics, setMetrics] = useState<StreamMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const startTimeRef = useRef<number>(0);

  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsStreaming(false);
      setIsConnected(false);
    }
  }, []);

  const streamMessage = useCallback(async (request: StreamChatRequest) => {
    // Reset state
    setCurrentMessage('');
    setIsStreaming(true);
    setIsConnected(false);
    setError(null);
    setMetrics(null);
    startTimeRef.current = performance.now();

    // Create new AbortController
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache'
        },
        body: JSON.stringify(request),
        signal
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('No response body for streaming');
      }

      setIsConnected(true);
      
      // Create reader for the stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let accumulatedMessage = '';
      let firstTokenTime: number | null = null;
      let modelUsed = request.model_preference || 'gpt-5';
      let fallbackUsed = false;
      let fallbackReason: string | undefined;

      try {
        while (true) {
          const { value, done } = await reader.read();
          
          if (done) break;
          
          // Decode chunk and add to buffer
          buffer += decoder.decode(value, { stream: true });
          
          // Process complete SSE events
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer
          
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            
            const dataContent = line.slice(6).trim(); // Remove "data: "
            
            if (dataContent === '[DONE]') {
              // Stream completed
              const totalTime = performance.now() - startTimeRef.current;
              const streamMetrics: StreamMetrics = {
                model_used: modelUsed,
                first_token_ms: firstTokenTime,
                total_time_ms: Math.round(totalTime),
                fallback_used: fallbackUsed,
                fallback_reason: fallbackReason
              };
              
              setMetrics(streamMetrics);
              setIsStreaming(false);
              setIsConnected(false);
              
              if (onComplete) {
                onComplete(accumulatedMessage, streamMetrics);
              }
              
              // Cache invalidation could be added here if needed
              
              return;
            }
            
            try {
              const chunk = JSON.parse(dataContent);
              
              // Handle error responses
              if (chunk.error) {
                throw new Error(chunk.error + (chunk.details ? `: ${chunk.details}` : ''));
              }
              
              // Extract content from our backend stream format or OpenAI format
              const deltaContent = chunk.content || chunk.choices?.[0]?.delta?.content || '';
              
              if (deltaContent && chunk.type === 'message') {
                // Mark first token received
                if (firstTokenTime === null) {
                  firstTokenTime = performance.now() - startTimeRef.current;
                }
                
                accumulatedMessage += deltaContent;
                setCurrentMessage(accumulatedMessage);
                
                if (onMessage) {
                  onMessage(deltaContent);
                }
              }
              
              // Track model used and fallback status
              if (chunk.model) {
                modelUsed = chunk.model;
                fallbackUsed = modelUsed !== (request.model_preference || 'gpt-5');
              }
              
            } catch (parseError) {
              console.warn('Failed to parse SSE chunk:', dataContent, parseError);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
      
    } catch (err) {
      const error = err as Error;
      console.error('SSE streaming error:', error);
      
      setError(error.message);
      setIsStreaming(false);
      setIsConnected(false);
      
      if (onError && !signal.aborted) {
        onError(error);
      }
    } finally {
      abortControllerRef.current = null;
    }
  }, [endpoint, onMessage, onComplete, onError]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    streamMessage,
    currentMessage,
    isStreaming,
    isConnected,
    metrics,
    error,
    abort
  };
};