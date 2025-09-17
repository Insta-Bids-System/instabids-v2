/**
 * Streaming COIA Chat Component with GPT-5 Token Streaming
 * Implements real-time token-by-token rendering using Server-Sent Events
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface ProfileData {
  company_name: string;
  services: string[];
  website: string;
  completeness_score: number;
}

interface BidCard {
  id: string;
  title: string;
  budget_range: string;
  location: string;
  match_score: number;
}

interface StreamingCOIAChatProps {
  sessionId: string;
  contractorId?: string;
  onProfileUpdate?: (profile: ProfileData) => void;
  onBidCardsFound?: (bidCards: BidCard[]) => void;
}

export const StreamingCOIAChat: React.FC<StreamingCOIAChatProps> = ({
  sessionId,
  contractorId,
  onProfileUpdate,
  onBidCardsFound
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState('');
  const [toolStatus, setToolStatus] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStreamingMessage, scrollToBottom]);

  // Initialize with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        id: 'welcome',
        type: 'assistant',
        content: "Hi! I'm COIA, your AI contractor onboarding assistant. I can help you get set up on InstaBids by researching your business and finding matching projects. What's your business name?",
        timestamp: new Date()
      }]);
    }
  }, [messages.length]);

  const sendMessage = async (message: string) => {
    if (!message.trim() || isStreaming) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: message.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentInput('');
    setIsStreaming(true);
    setCurrentStreamingMessage('');
    setToolStatus('');

    // Create streaming assistant message
    const assistantMessage: Message = {
      id: `assistant-${Date.now()}`,
      type: 'assistant', 
      content: '',
      timestamp: new Date(),
      isStreaming: true
    };

    setMessages(prev => [...prev, assistantMessage]);

    try {
      // Create abort controller for this request
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      // Start Server-Sent Events stream
      const response = await fetch('/api/ai/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message.trim(),
          session_id: sessionId,
          contractor_id: contractorId,
          interface: 'chat'
        }),
        signal: abortController.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body reader');
      }

      setIsConnected(true);
      let accumulatedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              switch (data.type) {
                case 'connected':
                  console.log('Stream connected');
                  break;
                  
                case 'processing':
                  setToolStatus(data.content);
                  break;
                  
                case 'tool_call':
                  setToolStatus(data.content);
                  break;
                  
                case 'response_start':
                  setToolStatus('');
                  break;
                  
                case 'token':
                  accumulatedContent += data.content;
                  setCurrentStreamingMessage(accumulatedContent);
                  break;
                  
                case 'metadata':
                  // Handle profile and bid card data
                  if (data.metadata?.profile && onProfileUpdate) {
                    onProfileUpdate(data.metadata.profile);
                  }
                  if (data.metadata?.bid_cards && onBidCardsFound) {
                    onBidCardsFound(data.metadata.bid_cards);
                  }
                  break;
                  
                case 'complete':
                  // Finalize the streaming message
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantMessage.id 
                      ? { ...msg, content: accumulatedContent, isStreaming: false }
                      : msg
                  ));
                  setCurrentStreamingMessage('');
                  setToolStatus('');
                  setIsStreaming(false);
                  break;
                  
                case 'error':
                  console.error('Stream error:', data.content);
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantMessage.id 
                      ? { ...msg, content: `Error: ${data.content}`, isStreaming: false }
                      : msg
                  ));
                  setCurrentStreamingMessage('');
                  setToolStatus('');
                  setIsStreaming(false);
                  break;
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }

      reader.releaseLock();
      
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Stream aborted');
      } else {
        console.error('Error sending message:', error);
        setMessages(prev => prev.map(msg => 
          msg.id === assistantMessage.id 
            ? { ...msg, content: `Error: Unable to connect to AI assistant. Please try again.`, isStreaming: false }
            : msg
        ));
      }
      setCurrentStreamingMessage('');
      setToolStatus('');
      setIsStreaming(false);
    } finally {
      setIsConnected(false);
      abortControllerRef.current = null;
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(currentInput);
  };

  const stopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-blue-600 text-white p-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">COIA Assistant</h2>
          <p className="text-blue-200 text-sm">AI-Powered Contractor Onboarding</p>
        </div>
        <div className="flex items-center space-x-2">
          {isConnected && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm">Streaming</span>
            </div>
          )}
          {isStreaming && (
            <button
              onClick={stopStreaming}
              className="bg-red-500 hover:bg-red-600 px-3 py-1 rounded text-sm"
            >
              Stop
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl rounded-lg px-4 py-3 ${
                message.type === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border shadow-sm'
              }`}
            >
              <div className="whitespace-pre-wrap">
                {message.isStreaming ? currentStreamingMessage : message.content}
              </div>
              {message.isStreaming && (
                <div className="mt-2 flex items-center space-x-2 text-gray-500">
                  <div className="w-1 h-1 bg-gray-400 rounded-full animate-pulse"></div>
                  <div className="w-1 h-1 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-1 h-1 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Tool Status */}
        {toolStatus && (
          <div className="flex justify-start">
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600"></div>
                <span className="text-yellow-800 text-sm">{toolStatus}</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            placeholder="Tell me about your business..."
            disabled={isStreaming}
            className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={isStreaming || !currentInput.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-lg transition-colors"
          >
            {isStreaming ? 'Streaming...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default StreamingCOIAChat;