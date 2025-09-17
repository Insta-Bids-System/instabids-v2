import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, Bot, CheckCircle, Loader2, MessageCircle, Send, User } from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import toast from "react-hot-toast";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface COIASession {
  session_id: string;
  bid_card_id: string;
  contractor_lead_id?: string;
  profile_completeness: number;
  contractor_profile?: any;
}

const ContractorCOIAOnboarding: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user, profile } = useAuth();
  
  // Get parameters from URL
  const bidToken = searchParams.get("bid");
  const source = searchParams.get("source") || "direct";
  
  // Session management for anonymous-to-authenticated flow
  const [sessionId, setSessionId] = useState(() => {
    const existingSessionId = localStorage.getItem("coia_session_id");
    if (existingSessionId) return existingSessionId;
    const newSessionId = `anon_contractor_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem("coia_session_id", newSessionId);
    localStorage.setItem("coia_session_type", "anonymous");
    return newSessionId;
  });
  const [hasTriggeredMigration, setHasTriggeredMigration] = useState(false);
  
  // State
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [session, setSession] = useState<COIASession | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Auto-migrate sessions when user signs up
  useEffect(() => {
    const handleSessionMigration = async () => {
      if (user?.id && sessionId.startsWith('anon_contractor_') && !hasTriggeredMigration && 
          user.id !== "00000000-0000-0000-0000-000000000000") {
        
        setHasTriggeredMigration(true);
        
        try {
          const response = await fetch('/conversations/migrate-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              anonymous_session_id: sessionId,
              authenticated_user_id: user.id
            })
          });
          
          if (response.ok) {
            const result = await response.json();
            toast.success('Your contractor profile conversation has been saved to your account!');
            
            // Update to authenticated session
            const newSessionId = `auth_contractor_${user.id}`;
            setSessionId(newSessionId);
            localStorage.setItem("coia_session_id", newSessionId);
            localStorage.setItem("coia_session_type", "authenticated");
            
            console.log(`Migrated ${result.migrated_conversations} contractor conversations`);
          } else {
            console.error('Session migration failed:', response.statusText);
          }
        } catch (error) {
          console.error('Session migration failed:', error);
        }
      }
    };
    
    handleSessionMigration();
  }, [user?.id, sessionId, hasTriggeredMigration]);

  // Initialize COIA session on mount
  useEffect(() => {
    initializeCOIASession();
  }, [bidToken]);

  const initializeCOIASession = async () => {
    try {
      setIsInitializing(true);
      
      if (!bidToken) {
        // Generic contractor onboarding (no bid card)
        const sessionId = `web-generic-${Date.now()}`;
        
        setSession({
          session_id: sessionId,
          bid_card_id: "",
          contractor_lead_id: undefined,
          profile_completeness: 0,
          contractor_profile: null
        });

        // Add initial generic AI message
        setMessages([{
          id: "initial",
          role: "assistant",
          content: `Welcome to InstaBids! I'm COIA, your contractor onboarding assistant. 

I'll help you get set up on our platform so homeowners can find and hire you for their projects.

To get started, could you tell me:
- Your company name
- What services you provide
- Your service area

For example: "I own ABC Roofing in Miami, and we specialize in residential roof repairs and replacements."`,
          timestamp: new Date()
        }]);

        setIsInitializing(false);
        return;
      }
    } catch (error) {
      console.error('Error in generic initialization:', error);
      setIsInitializing(false);
    }

    try {
      setIsInitializing(true);
      
      // First, get the bid card details to find the contractor_lead_id
      const bidCardResponse = await fetch(`/api/bid-cards/by-token/${bidToken}`);
      if (!bidCardResponse.ok) {
        throw new Error("Failed to load bid card details");
      }
      const bidCardData = await bidCardResponse.json();
      
      // Generate a verification token for this session
      const verificationToken = `coia-web-${Date.now()}-${Math.random().toString(36).substring(7)}`;
      
      // Start COIA session using the bid-card-link endpoint
      const response = await fetch("/api/coia/bid-card-link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bid_card_id: bidCardData.id || bidToken,
          contractor_lead_id: bidCardData.contractor_lead_id || searchParams.get("contractor_id") || `temp-${Date.now()}`, // Use contractor from bid card API
          verification_token: verificationToken,
          session_id: `web-${bidToken}-${Date.now()}`
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to start COIA session");
      }

      const data = await response.json();
      
      // Set up session
      setSession({
        session_id: data.session_id,
        bid_card_id: bidCardData.id || bidToken,
        contractor_lead_id: data.contractor_id,
        profile_completeness: data.profile_completeness || 0,
        contractor_profile: data.contractor_profile
      });

      // Add initial AI message
      if (data.response) {
        setMessages([{
          id: `msg-${Date.now()}`,
          role: "assistant",
          content: data.response,
          timestamp: new Date()
        }]);
      }

      // Track session start
      await fetch("/api/track/coia-session-start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bid_token: bidToken,
          session_id: data.session_id,
          source: source
        }),
      }).catch(console.error);

    } catch (err) {
      console.error("Failed to initialize COIA:", err);
      setError("Failed to start AI assistant. Please try again or use manual signup.");
    } finally {
      setIsInitializing(false);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !session) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/coia/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: inputMessage,
          session_id: session.session_id,
          contractor_lead_id: session.contractor_lead_id,
          user_id: user?.id || "00000000-0000-0000-0000-000000000000",
          conversation_id: sessionId,
          context: {
            bid_card_id: session.bid_card_id,
            source: source
          }
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      const data = await response.json();

      // Add AI response
      const aiMessage: Message = {
        id: `msg-${Date.now()}-ai`,
        role: "assistant",
        content: data.response,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);

      // Update session with new profile data
      if (data.contractor_profile) {
        setSession(prev => prev ? {
          ...prev,
          profile_completeness: data.profile_completeness || prev.profile_completeness,
          contractor_profile: data.contractor_profile
        } : null);
      }

      // Check if onboarding is complete
      if (data.completion_ready || data.contractor_created) {
        setTimeout(() => {
          navigate(`/contractor/dashboard?new=true&session=${session.session_id}`);
        }, 3000);
      }

    } catch (err) {
      console.error("Failed to send message:", err);
      setMessages(prev => [...prev, {
        id: `msg-error-${Date.now()}`,
        role: "assistant",
        content: "I'm having trouble connecting right now. Please try again in a moment.",
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Loading state
  if (isInitializing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <motion.div
          className="text-center"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
        >
          <Bot className="w-16 h-16 text-green-400 mx-auto mb-4 animate-pulse" />
          <h2 className="text-2xl font-bold text-white mb-2">Starting AI Assistant...</h2>
          <p className="text-white/70">Preparing your personalized onboarding experience</p>
        </motion.div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="max-w-md text-center">
          <div className="text-red-400 mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-white mb-2">Unable to Start Chat</h2>
          <p className="text-white/70 mb-6">{error}</p>
          <button
            onClick={() => navigate("/join" + (bidToken ? `?bid=${bidToken}` : ""))}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            Return to Signup
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <motion.div
        className="bg-black/20 backdrop-blur-sm border-b border-white/10 px-6 py-4"
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bot className="w-8 h-8 text-green-400" />
            <div>
              <h1 className="text-xl font-bold text-white">InstaBids AI Assistant</h1>
              <p className="text-sm text-white/60">Intelligent Contractor Onboarding</p>
            </div>
          </div>
          {session && (
            <div className="flex items-center gap-2">
              <div className="text-right">
                <p className="text-sm text-white/60">Profile Completion</p>
                <p className="text-lg font-bold text-green-400">
                  {Math.round(session.profile_completeness * 100)}%
                </p>
              </div>
              <div className="w-24 h-2 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-green-400 to-green-600"
                  initial={{ width: 0 }}
                  animate={{ width: `${session.profile_completeness * 100}%` }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                />
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {/* Chat Container */}
      <div className="max-w-4xl mx-auto p-6">
        <motion.div
          className="bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 h-[600px] flex flex-col"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            <AnimatePresence>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                >
                  <div
                    className={`max-w-[70%] rounded-2xl px-6 py-4 ${
                      message.role === "user"
                        ? "bg-blue-600/20 border border-blue-500/30"
                        : "bg-white/10 border border-white/20"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {message.role === "assistant" ? (
                        <Bot className="w-5 h-5 text-green-400 mt-1 flex-shrink-0" />
                      ) : (
                        <User className="w-5 h-5 text-blue-400 mt-1 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <p className="text-white whitespace-pre-wrap">{message.content}</p>
                        <p className="text-xs text-white/40 mt-2">
                          {message.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {isLoading && (
              <motion.div
                className="flex justify-start"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <div className="bg-white/10 border border-white/20 rounded-2xl px-6 py-4">
                  <div className="flex items-center gap-3">
                    <Bot className="w-5 h-5 text-green-400 animate-pulse" />
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-white/60 rounded-full animate-bounce" />
                      <span className="w-2 h-2 bg-white/60 rounded-full animate-bounce delay-100" />
                      <span className="w-2 h-2 bg-white/60 rounded-full animate-bounce delay-200" />
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-white/10 p-4">
            <div className="flex gap-3">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                disabled={isLoading}
                className="flex-1 bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-green-500/50 disabled:opacity-50"
              />
              <button
                onClick={sendMessage}
                disabled={isLoading || !inputMessage.trim()}
                className="bg-gradient-to-r from-green-500 to-emerald-500 text-white px-6 py-3 rounded-xl font-semibold hover:from-green-600 hover:to-emerald-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Send className="w-5 h-5" />
                    <span>Send</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.div>

        {/* Help Text */}
        <motion.div
          className="mt-6 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          <p className="text-white/60 text-sm">
            💡 Tip: Tell me about your business, specialties, and certifications to build a winning profile
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default ContractorCOIAOnboarding;