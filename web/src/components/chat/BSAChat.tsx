"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Bot, Loader2, Send, TrendingUp, User, FileText } from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";

interface BSAChatProps {
  contractorId: string;
  onComplete?: (data: any) => void;
  groupPackageId?: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  contextInfo?: any;
  memoryUpdates?: any;
}

interface BSAContextInfo {
  total_context_items: number;
  has_profile: boolean;
  coia_conversations: number;
  enhanced_profile: boolean;
}

const BSAChat: React.FC<BSAChatProps> = ({
  contractorId,
  onComplete,
  groupPackageId,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: groupPackageId 
        ? "Hello! I'm BSA, your Bid Submission Agent. I see you've created a group bidding package! I'm here to help you create a comprehensive proposal for your group project that maximizes your efficiency and showcases the value of bundled services.\n\nLet me load your package details and contractor profile..."
        : "Hello! I'm BSA, your Bid Submission Agent. I'm here to help you create professional, winning bid proposals that showcase your expertise and experience.\n\nLet me load your contractor profile and bidding history...",
      timestamp: new Date(),
    },
  ]);

  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>(() => 
    `bsa_${contractorId}_${Date.now()}`
  );
  const [contextInfo, setContextInfo] = useState<BSAContextInfo | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load initial BSA context on mount
  useEffect(() => {
    const loadInitialContext = async () => {
      try {
        const contextUrl = groupPackageId 
          ? `/api/bsa/contractor/${contractorId}/context?group_package=${groupPackageId}`
          : `/api/bsa/contractor/${contractorId}/context`;
          
        const response = await fetch(contextUrl);
        if (response.ok) {
          const data = await response.json();
          setContextInfo({
            total_context_items: data.total_context_items,
            has_profile: data.has_profile,
            coia_conversations: data.coia_conversations,
            enhanced_profile: data.enhanced_profile || false
          });

          // Update initial message with context info
          let contextMessage;
          if (groupPackageId && data.group_package) {
            contextMessage = `I've loaded your group bidding package with ${data.group_package.selected_projects || 0} projects selected. The package offers a ${data.group_package.discount_percentage || 15}% group discount and covers ${data.group_package.category_name} services.\n\nI'm ready to help you create a compelling group proposal that highlights the efficiency and cost savings of bundled services. What aspects of your group proposal would you like to focus on?`;
          } else if (data.has_profile) {
            contextMessage = `I've loaded your contractor profile and found ${data.coia_conversations} previous conversations with our system. I have access to your bidding history, specialties, and past project experience.\n\nWhat type of project would you like help bidding on today?`;
          } else {
            contextMessage = `I'm ready to help you create professional bid proposals. Since this is our first conversation, I'll help you craft compelling bids that highlight your expertise.\n\nWhat type of project would you like help bidding on today?`;
          }

          setMessages(prev => prev.map(msg => 
            msg.id === "1" 
              ? { ...msg, content: contextMessage, contextInfo: data }
              : msg
          ));
        }
      } catch (error) {
        console.error("Error loading BSA context:", error);
        // Continue with default message if context loading fails
      }
    };

    if (contractorId) {
      loadInitialContext();
    }
  }, [contractorId, groupPackageId]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: inputMessage.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    // Create streaming assistant message
    const assistantMessageId = (Date.now() + 1).toString();

    try {
      const assistantMessage: Message = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setStreamingMessageId(assistantMessageId);

      // Call the BSA fast streaming endpoint
      const response = await fetch("/api/bsa/fast-stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          contractor_id: contractorId,
          message: userMessage.content,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Handle Server-Sent Events (SSE) streaming
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulatedResponse = "";
      let contextReceived = false;
      let completionData: any = null;

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                // Handle sub-agent status messages
                if (data.type === 'sub_agent_status') {
                  // Add sub-agent status message
                  const statusMessage: Message = {
                    id: `status_${Date.now()}`,
                    role: "assistant",
                    content: `🤖 ${data.message}`,
                    timestamp: new Date(),
                    isStreaming: false
                  };
                  
                  setMessages((prev) => [...prev.slice(0, -1), statusMessage, prev[prev.length - 1]]);
                }
                
                // Handle streaming chunks
                else if (data.choices && data.choices[0]?.delta?.content) {
                  accumulatedResponse += data.choices[0].delta.content;
                  
                  // Update the message with accumulated content
                  setMessages((prev) => {
                    return prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? { 
                            ...msg, 
                            content: accumulatedResponse,
                            isStreaming: true
                          }
                        : msg
                    );
                  });
                }
                
                // Handle bid cards found event
                else if (data.type === 'bid_cards_found') {
                  // Store bid cards and display them
                  const cards = data.bid_cards || [];
                  const metadata = data.search_metadata || {};
                  
                  // Add bid cards display to the message
                  let bidCardsMessage = `\n\n📋 **Found ${cards.length} matching projects:**\n\n`;
                  
                  cards.slice(0, 5).forEach((card, index) => {
                    bidCardsMessage += `**${index + 1}. ${card.title || 'Untitled Project'}**\n`;
                    bidCardsMessage += `   📍 Location: ${card.location?.city || card.location || 'Unknown'}\n`;
                    bidCardsMessage += `   💰 Budget: $${card.budget_min || 0} - $${card.budget_max || 0}\n`;
                    bidCardsMessage += `   🔨 Type: ${card.project_type || 'General'}\n\n`;
                  });
                  
                  if (cards.length > 5) {
                    bidCardsMessage += `_...and ${cards.length - 5} more projects_\n`;
                  }
                  
                  accumulatedResponse += bidCardsMessage;
                  
                  setMessages((prev) => {
                    return prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? { 
                            ...msg, 
                            content: accumulatedResponse,
                            isStreaming: true,
                            bidCards: cards,
                            searchMetadata: metadata
                          }
                        : msg
                    );
                  });
                }
                
                // Handle sub-agent results
                else if (data.type && ['search_results', 'market_analysis', 'bid_proposal', 'group_strategy'].includes(data.type)) {
                  // Display sub-agent results
                  const resultMessage = `✅ ${data.sub_agent?.replace('_', ' ')?.toUpperCase()}: Task completed successfully!`;
                  accumulatedResponse += `\n\n${resultMessage}`;
                  
                  setMessages((prev) => {
                    return prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? { 
                            ...msg, 
                            content: accumulatedResponse,
                            isStreaming: true
                          }
                        : msg
                    );
                  });
                }
                
                // Handle context info if provided
                if (data.context_info && !contextReceived) {
                  setContextInfo(data.context_info);
                  contextReceived = true;
                  completionData = data; // Store completion data for onComplete callback
                }
                
                // Handle completion
                if (data.status === 'complete') {
                  completionData = data; // Store completion data
                  break;
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e);
              }
            }
          }
        }
      }

      // Mark streaming as complete
      setMessages((prev) => {
        return prev.map((msg) => 
          msg.id === assistantMessageId 
            ? { 
                ...msg,
                content: accumulatedResponse || "I understand. Let me help you with that bid proposal.", 
                isStreaming: false
              } 
            : msg
        );
      });

      setStreamingMessageId(null);

      // Call onComplete if provided and we have useful data
      if (onComplete && completionData?.context_info) {
        onComplete(completionData);
      }

    } catch (error) {
      console.error("Error sending message to BSA:", error);

      // Show actual error instead of mock response
      const errorMessage = `I'm having trouble connecting to the server. Please check that the backend is running on port 8008. Error: ${error.message}`;

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: errorMessage,
                isStreaming: false,
              }
            : msg
        )
      );

      setStreamingMessageId(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Mock response generator removed - using real BSA API with proper backend URLs

  return (
    <div className="flex flex-col h-full min-h-[600px] bg-gray-900 rounded-2xl">
      {/* Context Status Bar */}
      {contextInfo && (
        <div className="p-3 border-b border-gray-700 bg-gray-800 rounded-t-2xl">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4">
              <span className="text-green-400 flex items-center gap-1">
                <FileText className="w-4 h-4" />
                BSA Context Loaded
              </span>
              <span className="text-white/70">
                {contextInfo.total_context_items} context items
              </span>
              {contextInfo.has_profile && (
                <span className="text-blue-400">Profile Available</span>
              )}
              {contextInfo.coia_conversations > 0 && (
                <span className="text-purple-400">
                  {contextInfo.coia_conversations} past conversations
                </span>
              )}
            </div>
            {contextInfo.enhanced_profile && (
              <div className="flex items-center gap-1 text-orange-400">
                <TrendingUp className="w-4 h-4" />
                Enhanced Profile
              </div>
            )}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : ""}`}
            >
              <div
                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.role === "user"
                    ? "bg-blue-600"
                    : "bg-gradient-to-r from-orange-500 to-red-500"
                }`}
              >
                {message.role === "user" ? (
                  <User className="w-4 h-4 text-white" />
                ) : (
                  <Bot className="w-4 h-4 text-white" />
                )}
              </div>

              <div className={`flex-1 max-w-[80%] ${message.role === "user" ? "text-right" : ""}`}>
                <div
                  className={`rounded-2xl px-4 py-3 ${
                    message.role === "user"
                      ? "bg-blue-600 text-white ml-auto"
                      : "bg-gray-800 text-white"
                  } ${message.role === "user" ? "max-w-fit ml-auto" : ""}`}
                >
                  <div className="whitespace-pre-wrap">
                    {message.content}
                    {message.isStreaming && (
                      <motion.span
                        animate={{ opacity: [1, 0] }}
                        transition={{ duration: 0.8, repeat: Infinity }}
                        className="inline-block w-2 h-4 bg-current ml-1"
                      />
                    )}
                  </div>
                </div>

                {/* Context info display for assistant messages */}
                {message.role === "assistant" && message.contextInfo && (
                  <div className="mt-2 text-xs text-white/50">
                    Context: {message.contextInfo.total_context_items} items loaded
                    {message.memoryUpdates && (
                      <span className="ml-2 text-green-400">
                        Memory updated
                      </span>
                    )}
                  </div>
                )}

                <div className="text-xs text-white/50 mt-1">
                  {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && !streamingMessageId && (
          <motion.div
            className="flex gap-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-r from-orange-500 to-red-500 flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="flex-1">
              <div className="bg-gray-800 rounded-2xl px-4 py-3 text-white">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>BSA is analyzing your request...</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Describe the project you'd like help bidding on..."
              disabled={isLoading}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none disabled:opacity-50"
            />
          </div>

          <button
            type="button"
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="flex-shrink-0 bg-gradient-to-r from-orange-600 to-red-600 text-white p-3 rounded-xl hover:from-orange-700 hover:to-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BSAChat;