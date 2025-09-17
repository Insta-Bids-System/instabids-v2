"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Bot, Loader2, Send, TrendingUp, User, FileText } from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import { BidCardMarketplace } from "../bidcards/BidCardMarketplace";

interface EnhancedBSAChatProps {
  contractorId: string;
  onComplete?: (data: any) => void;
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

// Remove fake interface - use real bid card types

const EnhancedBSAChat: React.FC<EnhancedBSAChatProps> = ({
  contractorId,
  onComplete,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hello! I'm BSA, your Bid Submission Agent. I can help you:\n\n🔍 **Find Projects**: Search for bid opportunities near you\n💼 **Prepare Bids**: Create professional proposals\n📋 **Submit Bids**: Handle the complete bidding process\n\nLet me load your contractor profile and bidding history...",
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
  
  // State for triggering bid card search
  const [showBidMarketplace, setShowBidMarketplace] = useState(false);
  const [marketplaceFilters, setMarketplaceFilters] = useState<any>(null);

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
        const response = await fetch(`/api/bsa/contractor/${contractorId}/context`);
        if (response.ok) {
          const data = await response.json();
          setContextInfo({
            total_context_items: data.total_context_items,
            has_profile: data.has_profile,
            coia_conversations: data.coia_conversations,
            enhanced_profile: data.enhanced_profile || false
          });

          // Update initial message with context info
          const contextMessage = data.has_profile 
            ? `I've loaded your contractor profile and found ${data.coia_conversations} previous conversations with our system. I have access to your bidding history, specialties, and past project experience.\n\n🎯 **Ready to help you with:**\n• Finding bid opportunities in your area\n• Creating winning proposals\n• Managing your bidding pipeline\n\nWhat type of project would you like me to find for you?`
            : `I'm ready to help you find projects and create professional bid proposals. Since this is our first conversation, I'll help you discover opportunities and craft compelling bids.\n\n🎯 **I can help you:**\n• Search for projects by location and type\n• Create professional proposals\n• Submit competitive bids\n\nWhat type of project are you looking for? (e.g., "kitchen projects in 78701")`;

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
  }, [contractorId]);

  // Handle when real bid cards are found
  const handleBidCardsFound = (searchMetadata: any) => {
    setShowBidMarketplace(true);
    setMarketplaceFilters({
      project_types: searchMetadata.project_type ? [searchMetadata.project_type] : undefined,
      location: {
        zip_code: searchMetadata.contractor_zip,
        radius_miles: searchMetadata.radius
      }
    });
  };

  const detectBidCardRequest = (message: string): boolean => {
    const searchKeywords = [
      'find projects', 'show me projects', 'search projects', 'bid cards',
      'opportunities', 'jobs', 'work', 'available projects',
      'kitchen projects', 'bathroom projects', 'plumbing jobs',
      'turf jobs', 'artificial turf', 'landscaping jobs',
      'near me', 'in my area', 'within'
    ];
    
    const lowerMessage = message.toLowerCase();
    return searchKeywords.some(keyword => lowerMessage.includes(keyword));
  };

  const detectSearchQuestionRequest = (message: string): boolean => {
    const questionKeywords = [
      'what are you searching', 'what exactly are you searching',
      'what zip code', 'what location', 'what parameters',
      'what did you search', 'show me search', 'search details'
    ];
    
    const lowerMessage = message.toLowerCase();
    return questionKeywords.some(keyword => lowerMessage.includes(keyword));
  };

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

    // Check if this is a bid card search request or search question
    const isBidCardRequest = detectBidCardRequest(userMessage.content);
    const isSearchQuestion = detectSearchQuestionRequest(userMessage.content);

    // Handle direct questions about search parameters
    if (isSearchQuestion) {
      const searchInfoMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `I can show you exactly what I search for! When you ask me to find projects, I:\n\n🔍 **Extract from your message:**\n• **Project Type**: kitchen, bathroom, plumbing, landscaping (turf), roofing, electrical, hvac\n• **ZIP Code**: Any 5-digit number you mention (like 33442)\n• **Location Radius**: 30 miles from your ZIP code\n\n📋 **Search Parameters:**\n• **Status**: Only active projects accepting bids\n• **Results**: Up to 5 projects per search\n\n💡 **Example searches:**\n• "find turf jobs around 33442" → **landscaping** projects in **33442** (30 mile radius)\n• "kitchen projects in 78701" → **kitchen** projects in **78701** (30 mile radius)\n\nTry asking me to search for a specific project type and location!`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, searchInfoMessage]);
      setIsLoading(false);
      return;
    }

    if (isBidCardRequest) {
      // Actually search for bid cards and present them in chat
      try {
        // Extract project type from user message
        const lowerMessage = userMessage.content.toLowerCase();
        const extractedProjectType = lowerMessage.includes('kitchen') ? 'kitchen' : 
                                     lowerMessage.includes('bathroom') ? 'bathroom' :
                                     lowerMessage.includes('plumbing') ? 'plumbing' :
                                     lowerMessage.includes('turf') || lowerMessage.includes('artificial turf') ? 'landscaping' :
                                     lowerMessage.includes('lawn') || lowerMessage.includes('landscaping') ? 'landscaping' :
                                     lowerMessage.includes('roofing') || lowerMessage.includes('roof') ? 'roofing' :
                                     lowerMessage.includes('electrical') ? 'electrical' :
                                     lowerMessage.includes('hvac') || lowerMessage.includes('heating') || lowerMessage.includes('cooling') ? 'hvac' :
                                     null;
        
        // Extract ZIP code from user message (5 digits)
        const zipMatch = userMessage.content.match(/\b\d{5}\b/);
        const extractedZip = zipMatch ? zipMatch[0] : null;
        
        // Search for actual bid cards
        const searchParams = new URLSearchParams({
          ...(extractedProjectType && { project_types: extractedProjectType }),
          ...(extractedZip && { zip_code: extractedZip, radius_miles: '30' }),
          status: 'active,collecting_bids,ready',
          page: '1',
          page_size: '5'
        });

        const bidCardsResponse = await fetch(`/api/bid-cards/search?${searchParams}`);
        const bidCardsData = await bidCardsResponse.json();

        if (bidCardsData.bid_cards && bidCardsData.bid_cards.length > 0) {
          // Analyze each bid card and create intelligent summary
          const bidCardSummaries = bidCardsData.bid_cards.map((card: any, index: number) => {
            const timeRemaining = card.timeline?.end_date ? 
              Math.ceil((new Date(card.timeline.end_date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)) : 'Unknown';
            const bidCount = card.bid_count || 0;
            const budget = `$${card.budget_range?.min?.toLocaleString()}-${card.budget_range?.max?.toLocaleString()}`;
            
            return `**${index + 1}. ${card.title}**
📍 ${card.location?.city}, ${card.location?.state}
💰 Budget: ${budget}
⏰ ${timeRemaining > 0 ? `${timeRemaining} days remaining` : 'Deadline passed'}
👥 ${bidCount} bid${bidCount !== 1 ? 's' : ''} submitted
📋 ${card.description?.substring(0, 100)}...

*Project Type: ${card.project_type} | Status: ${card.status}*`;
          }).join('\n\n---\n\n');

          // Show what was actually searched
          const searchDetails = [];
          if (extractedProjectType) searchDetails.push(`**Project Type:** ${extractedProjectType}`);
          if (extractedZip) searchDetails.push(`**Location:** ${extractedZip} (30 mile radius)`);
          searchDetails.push(`**Status:** Active projects accepting bids`);
          
          const searchResultsMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: `Great! I found ${bidCardsData.bid_cards.length} projects matching your search:\n\n🔍 **Search Parameters:**\n${searchDetails.join('\n')}\n\n${bidCardSummaries}\n\n💡 **Ready to bid?** Click any project below in the bid cards section to submit your proposal or ask questions!`,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, searchResultsMessage]);

          // Also show the marketplace with filtered results
          handleBidCardsFound({
            project_type: extractedProjectType,
            contractor_zip: extractedZip || "78701",
            radius: 30
          });
        } else {
          // Show what was actually searched when no results found
          const searchDetails = [];
          if (extractedProjectType) searchDetails.push(`**Project Type:** ${extractedProjectType}`);
          if (extractedZip) searchDetails.push(`**Location:** ${extractedZip} (30 mile radius)`);
          searchDetails.push(`**Status:** Active projects accepting bids`);
          
          const noResultsMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: `I searched for projects but didn't find any active opportunities right now.\n\n🔍 **Search Parameters Used:**\n${searchDetails.join('\n')}\n\n💡 **Try:**\n• Expanding your search radius\n• Looking for different project types (kitchen, bathroom, roofing, landscaping, etc.)\n• Checking back later for new projects\n\nWould you like me to search for a different type of project or location?`,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, noResultsMessage]);
        }
      } catch (error) {
        console.error('Error searching bid cards:', error);
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: `I had trouble searching for projects right now. Let me try opening the marketplace instead so you can browse available opportunities.`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
        
        // Fallback to showing marketplace
        handleBidCardsFound({
          project_type: extractedProjectType,
          contractor_zip: extractedZip || "78701",
          radius: 30
        });
      }
      
      setIsLoading(false);
      return;
    }

    // Regular conversation flow
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
                if (data.type === "sub_agent_status") {
                  const statusMessage: Message = {
                    id: `status-${Date.now()}`,
                    role: "assistant",
                    content: data.message,
                    timestamp: new Date(),
                    isStreaming: false,
                  };
                  
                  setMessages((prev) => [...prev, statusMessage]);
                  
                  // Sub-agent status updates are displayed as messages in chat
                }
                
                // Handle bid card search results
                if (data.type === "bid_cards_found") {
                  // Show real bid marketplace with search results
                  handleBidCardsFound(data.search_metadata || {});
                  
                  // If we have bid cards, show them in a summary message
                  if (data.bid_cards && data.bid_cards.length > 0) {
                    const bidCardCount = data.bid_cards.length;
                    const searchTypes = data.search_metadata?.searched_types?.join(', ') || 'various project types';
                    
                    const searchResultMessage: Message = {
                      id: `search-result-${Date.now()}`,
                      role: "assistant",
                      content: `I found ${bidCardCount} projects matching "${searchTypes}". Check out the bid cards below! 👇`,
                      timestamp: new Date(),
                      isStreaming: false,
                    };
                    setMessages((prev) => [...prev, searchResultMessage]);
                  }
                }
                
                // Handle clarifying questions from intelligent search
                if (data.type === "clarifying_questions" && data.questions) {
                  const questionsMessage: Message = {
                    id: `questions-${Date.now()}`,
                    role: "assistant",
                    content: `${data.message || "To help refine future searches:"}\n\n${data.questions.map((q: string) => `• ${q}`).join('\n')}`,
                    timestamp: new Date(),
                    isStreaming: false,
                    metadata: {
                      type: "clarifying_questions"
                    }
                  };
                  setMessages((prev) => [...prev, questionsMessage]);
                }
                
                // Handle related services suggestions
                if (data.type === "related_services" && data.services) {
                  const servicesMessage: Message = {
                    id: `services-${Date.now()}`,
                    role: "assistant",
                    content: `${data.message || "You might also be interested in:"}\n\n${data.services.map((s: string) => `• ${s}`).join('\n')}\n\nWould you like me to search for any of these types of projects?`,
                    timestamp: new Date(),
                    isStreaming: false,
                  };
                  setMessages((prev) => [...prev, servicesMessage]);
                }
                
                // Handle streaming chunks
                if (data.choices && data.choices[0]?.delta?.content) {
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
                
                // Handle context info if provided
                if (data.context_info && !contextReceived) {
                  setContextInfo(data.context_info);
                  contextReceived = true;
                }
                
                // Handle completion
                if (data.status === 'complete') {
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
                content: accumulatedResponse || generateMockBSAResponse(userMessage.content), 
                isStreaming: false
              } 
            : msg
        );
      });

      setStreamingMessageId(null);

    } catch (error) {
      console.error("Error sending message to BSA:", error);

      // Mock response for development
      const mockResponse = generateMockBSAResponse(userMessage.content);

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: mockResponse,
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

  // Mock BSA response generator (remove when real backend is ready)
  const generateMockBSAResponse = (userInput: string) => {
    const input = userInput.toLowerCase();

    if (input.includes("kitchen") || input.includes("remodel")) {
      return `Excellent! Kitchen remodeling projects are great opportunities. I can help you:\n\n🔍 **Find kitchen projects** - Search by location and budget\n💼 **Prepare winning bids** - Professional proposal templates\n📋 **Submit efficiently** - Streamlined bidding process\n\nWould you like me to search for kitchen projects in your area? Just tell me your ZIP code or say "find kitchen projects near me".`;
    }

    if (input.includes("find") || input.includes("search") || input.includes("projects")) {
      return `I'll search for projects in your area. I'm opening the real bid card marketplace below where you can see actual projects with working "Submit Bid" and "Ask Questions" buttons.\n\nThese are real projects from homeowners looking for contractors like you!`;
    }

    return `I understand you'd like help with bidding. I can assist you with:\n\n🔍 **Project Search** - Find opportunities in your area\n💼 **Bid Preparation** - Create professional proposals\n📋 **Submission Process** - Handle the complete workflow\n\nWhat specific help do you need today?`;
  };

  return (
    <div className="flex flex-col h-full min-h-[800px] bg-gray-900 rounded-2xl">
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

      {/* Split Layout Container */}
      <div className="flex-1 flex flex-col min-h-0">
        
        {/* Chat Section - Top 60% */}
        <div className="flex-[3] flex flex-col min-h-0">
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
                  placeholder="Ask me to find projects or help with bidding..."
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

        {/* Bid Cards Section - Bottom 40% */}
        <div className="flex-[2] border-t border-gray-700 bg-white">
          {showBidMarketplace ? (
            <div className="h-full overflow-auto p-4">
              <BidCardMarketplace
                contractorId={contractorId}
                userType="contractor"
              />
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500">
              <div className="text-center">
                <p className="text-lg font-medium mb-2">No Projects Displayed</p>
                <p className="text-sm">Search for projects to see bid cards here</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedBSAChat;