"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  Bot,
  Brain,
  Camera,
  CheckCircle,
  Clock,
  Eye,
  EyeOff,
  Headphones,
  Image as ImageIcon,
  Loader2,
  Send,
  Sparkles,
  Square,
  User,
  Volume2,
  VolumeX,
  X,
  Zap,
} from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { StorageService } from "@/lib/storage";
import { AudioProcessor, OpenAIRealtimeWebRTC } from "@/services/openai-realtime-webrtc";
import { AccountSignupModal } from "./AccountSignupModal";
import ChatBidCardAttachment from "./ChatBidCardAttachment";
import AttachmentPreview from "./AttachmentPreview";
import { DynamicBidCardPreview } from "./DynamicBidCardPreview";
import { RealTimeBidCardDisplay } from "./RealTimeBidCardDisplay";
import { useSSEChatStream } from "@/hooks/useSSEChatStream";
import { useBidCardUpdates } from "@/hooks/useBidCardUpdates";
import { useAuth } from "@/contexts/AuthContext";

// Types
interface UnifiedAttachment {
  id: string;
  message_id: string;
  type: "image" | "document";
  name: string;
  url: string;
  mime_type: string;
  file_size: number;
  storage_path: string;
  created_at: string;
  metadata?: Record<string, any>;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  images?: string[]; // Legacy support
  attachments?: UnifiedAttachment[]; // New unified attachments
  phase?: string;
  isStreaming?: boolean;
  bidCards?: BidCard[];
  aiRecommendation?: string;
  extractedData?: any;
}

interface BidCard {
  id: string;
  bid_card_number: string;
  title: string;
  description: string;
  project_type: string;
  location_city: string;
  location_state: string;
  budget_min: number;
  budget_max: number;
  timeline?: {
    start_date: string;
    duration?: string;
  };
  urgency_level: string;
  bids_received_count: number;
  contractor_count_needed: number;
  group_buying_eligible?: boolean;
  status: string;
  created_at: string;
}

interface ProjectPhase {
  id: string;
  name: string;
  description: string;
  status: "pending" | "active" | "completed";
  icon: React.ReactNode;
}

interface UltimateCIAChatProps {
  onSendMessage?: (message: string, images?: string[]) => Promise<any>;
  onAccountCreated?: (userData: { name: string; email: string; userId: string }) => void;
  initialMessage?: string;
  projectContext?: any;
  sessionId?: string;
}

// Personality types for adaptive responses
const personalities = ["friendly", "professional", "enthusiastic", "thoughtful", "helpful"] as const;
type Personality = (typeof personalities)[number];

const UltimateCIAChat: React.FC<UltimateCIAChatProps> = ({
  onSendMessage,
  onAccountCreated,
  initialMessage = "Welcome to Instabids! I'm Alex, your AI project assistant. Tell me about your home project and I'll help you get competitive bids from verified contractors. What are you looking to get done?",
  projectContext,
  sessionId: propSessionId,
}) => {
  console.log('[CIA] UltimateCIAChat component loaded - should use /api/cia/stream');
  
  // Auth context for user authentication and session migration
  const { user, profile } = useAuth();
  
  // Core state - start with empty messages, will load opening message from API
  const [messages, setMessages] = useState<Message[]>([]);
  const [openingMessageLoaded, setOpeningMessageLoaded] = useState(false);

  const [inputMessage, setInputMessage] = useState("");
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [imagePreview, setImagePreview] = useState<string[]>([]);
  const [mounted, setMounted] = useState(false);

  // Phase tracking system (from DynamicCIAChat)
  const [currentPhase, setCurrentPhase] = useState("intro");
  const [extractedData, setExtractedData] = useState<any>({});

  // Audio/Voice states (from UltraInteractiveCIAChat)
  const [audioMode, setAudioMode] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<"disconnected" | "connecting" | "connected">("disconnected");

  // UI states
  const [showImages, setShowImages] = useState(true);
  const [showDataSidebar, setShowDataSidebar] = useState(false);
  const [personality, setPersonality] = useState<Personality>("friendly");
  const [currentExpression, setCurrentExpression] = useState("🤖");
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);

  // Signup modal (from CIAChat)
  const [showSignupModal, setShowSignupModal] = useState(false);
  const [extractedProjectInfo, setExtractedProjectInfo] = useState<{
    projectType?: string;
    description?: string;
  }>({});
  const [pendingConversion, setPendingConversion] = useState<{
    bidCardId: string;
    conversationId: string;
  } | null>(null);

  // Session management - ALWAYS FRESH (NO CACHING BULLSHIT)
  const [sessionId, setSessionId] = useState(() => {
    if (propSessionId) return propSessionId;
    
    // ALWAYS generate fresh session ID - FUCK THE CACHE
    const newSessionId = `anon_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return newSessionId;
  });

  // Track authentication state changes for session migration
  const [hasTriggeredMigration, setHasTriggeredMigration] = useState(false);

  // SSE Streaming Chat Hook
  const {
    streamMessage,
    isStreaming,
    currentMessage: streamingResponse,
    abort: abortStream,
    metrics,
    error: streamError,
  } = useSSEChatStream({
    endpoint: '/api/cia/stream',
    onMessage: (content: string) => {
      // Update streaming message in real-time
      if (streamingMessageId) {
        setMessages((prev) => 
          prev.map((msg) => 
            msg.id === streamingMessageId 
              ? { ...msg, content, isStreaming: true }
              : msg
          )
        );
      }
    },
    onComplete: (fullMessage: string, streamMetrics) => {
      // Finalize streaming message
      if (streamingMessageId) {
        setMessages((prev) => 
          prev.map((msg) => 
            msg.id === streamingMessageId 
              ? { ...msg, content: fullMessage, isStreaming: false }
              : msg
          )
        );
        setStreamingMessageId(null);
        setCurrentExpression(alexExpressions.happy);
        
        console.log("Stream metrics:", streamMetrics);
      }
    },
    onError: (error: Error) => {
      console.error("Streaming error:", error);
      toast.error("Failed to get response");
      
      if (streamingMessageId) {
        setMessages((prev) => prev.filter(msg => msg.id !== streamingMessageId));
        setStreamingMessageId(null);
        setCurrentExpression(alexExpressions.working);
      }
    }
  });

  // Real-time bid card updates hook
  const {
    bidCardData,
    loading: bidCardLoading,
    error: bidCardError,
    refresh: refreshBidCard
  } = useBidCardUpdates({
    conversationId: sessionId,
    enabled: messages.length > 1, // Start checking after first user message
    pollInterval: 3000 // Poll every 3 seconds
  });

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const realtimeClient = useRef<OpenAIRealtimeWebRTC | null>(null);
  const audioProcessor = useRef<AudioProcessor | null>(null);
  const hasInitialMessageSent = useRef(false);

  // Phase definitions (from DynamicCIAChat)
  const phases: ProjectPhase[] = [
    {
      id: "intro",
      name: "Introduction",
      description: "Getting to know your project",
      status: currentPhase === "intro" ? "active" : "completed",
      icon: <User className="w-4 h-4" />,
    },
    {
      id: "discovery",
      name: "Discovery",
      description: "Understanding project details",
      status:
        currentPhase === "discovery"
          ? "active"
          : currentPhase === "intro"
            ? "pending"
            : "completed",
      icon: <Sparkles className="w-4 h-4" />,
    },
    {
      id: "details",
      name: "Specifications",
      description: "Detailed requirements",
      status:
        currentPhase === "details"
          ? "active"
          : ["intro", "discovery"].includes(currentPhase)
            ? "pending"
            : "completed",
      icon: <Clock className="w-4 h-4" />,
    },
    {
      id: "photos",
      name: "Photos",
      description: "Visual documentation",
      status:
        currentPhase === "photos"
          ? "active"
          : ["intro", "discovery", "details"].includes(currentPhase)
            ? "pending"
            : "completed",
      icon: <ImageIcon className="w-4 h-4" />,
    },
    {
      id: "review",
      name: "Review",
      description: "Final confirmation",
      status:
        currentPhase === "review"
          ? "active"
          : currentPhase === "complete"
            ? "completed"
            : "pending",
      icon: <CheckCircle className="w-4 h-4" />,
    },
  ];

  // Expression system (from UltraInteractiveCIAChat)
  const alexExpressions = {
    happy: "😊",
    thinking: "🤔",
    excited: "🤩",
    working: "⚡",
    analyzing: "🔍",
    listening: "👂",
  };

  // Fix hydration
  useEffect(() => {
    setMounted(true);
  }, []);
  
  // Fetch opening message from API when component loads
  useEffect(() => {
    const fetchOpeningMessage = async () => {
      if (openingMessageLoaded || messages.length > 0) return;
      
      try {
        const response = await fetch('/api/cia/opening-message');
        const data = await response.json();
        
        if (data.success && data.message) {
          const openingMessage: Message = {
            id: "opening-message",
            role: "assistant",
            content: data.message,
            timestamp: new Date(),
            phase: "intro",
          };
          
          setMessages([openingMessage]);
          setOpeningMessageLoaded(true);
          console.log('[CIA] Loaded opening message from API');
        }
      } catch (error) {
        console.error('Failed to fetch opening message:', error);
        // Fallback to default message
        const fallbackMessage: Message = {
          id: "fallback-message",
          role: "assistant",
          content: initialMessage,
          timestamp: new Date(),
          phase: "intro",
        };
        setMessages([fallbackMessage]);
        setOpeningMessageLoaded(true);
      }
    };

    if (mounted) {
      fetchOpeningMessage();
    }
  }, [mounted, openingMessageLoaded, messages.length, initialMessage]);
  
  // Auto-send initial message if we have RFI context
  useEffect(() => {
    if (mounted && initialMessage && projectContext?.rfi_id && openingMessageLoaded && messages.length === 1) {
      // Only auto-send if this is a fresh conversation with RFI context
      const autoSendRfiMessage = async () => {
        // Add a small delay to let the chat UI render
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Add the RFI context message to the chat
        const rfiUserMessage: Message = {
          id: Date.now().toString(),
          role: "user",
          content: initialMessage,
          timestamp: new Date(),
        };
        
        setMessages(prev => [...prev, rfiUserMessage]);
        
        // Now send to the backend with RFI context
        try {
          const chatMessages = [
            { role: "assistant" as const, content: messages[0].content },
            { role: "user" as const, content: initialMessage }
          ];
          
          const streamRequest = {
            messages: chatMessages,
            conversation_id: sessionId,
            user_id: user?.id || "00000000-0000-0000-0000-000000000000",
            max_tokens: 500,
            model_preference: "gpt-5",
            rfi_context: projectContext
          };
          
          await streamMessage(streamRequest);
        } catch (error) {
          console.error("Error auto-sending RFI message:", error);
          toast.error("Failed to load RFI context");
        }
      };
      
      autoSendRfiMessage();
    }
  }, [mounted, initialMessage, projectContext, messages.length, sessionId, user?.id, streamMessage]);

  // Handle session migration when user authenticates
  useEffect(() => {
    const handleSessionMigration = async () => {
      // Only migrate if:
      // 1. User is now authenticated (has user ID)
      // 2. Current session is anonymous (starts with 'anon_')
      // 3. We haven't already triggered migration for this session
      if (
        user?.id && 
        sessionId.startsWith('anon_') && 
        !hasTriggeredMigration &&
        user.id !== "00000000-0000-0000-0000-000000000000"
      ) {
        try {
          console.log('[CIA] Migrating anonymous session to authenticated user', {
            anonymousSessionId: sessionId,
            authenticatedUserId: user.id
          });

          // Call session migration API
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
            console.log('[CIA] Session migration successful:', result);
            
            // Update session tracking - NO MORE FUCKING LOCALSTORAGE
            setHasTriggeredMigration(true);
            
            // Generate new authenticated session ID
            const newAuthSessionId = `auth_${user.id}_${Date.now()}`;
            setSessionId(newAuthSessionId);
            
            toast.success('Your conversation history has been saved to your account!');
          } else {
            console.error('[CIA] Session migration failed:', response.statusText);
          }
        } catch (error) {
          console.error('[CIA] Session migration error:', error);
        }
      }
    };

    handleSessionMigration();
  }, [user?.id, sessionId, hasTriggeredMigration]);

  // DISABLED: Legacy conversation loading conflicts with SSE streaming
  // The new SSE system handles conversation state internally
  // useEffect(() => {
  //   // Legacy conversation loading disabled to prevent dual indicators
  //   console.log("[CIA] Legacy conversation loading disabled - using SSE streaming only");
  // }, [sessionId]);

  // Auto-show bid card sidebar when user starts chatting
  useEffect(() => {
    if (messages.length > 1 && !showDataSidebar) {
      setShowDataSidebar(true);
    }
  }, [messages.length, showDataSidebar]);

  // Initialize OpenAI Realtime WebRTC (from UltraInteractiveCIAChat)
  useEffect(() => {
    if (!audioMode) return;

    audioProcessor.current = new AudioProcessor();

    const apiKey = import.meta.env.VITE_OPENAI_API_KEY;
    if (!apiKey) {
      console.error("VITE_OPENAI_API_KEY not found");
      toast.error("OpenAI API key not configured");
      return;
    }

    realtimeClient.current = new OpenAIRealtimeWebRTC({
      apiKey,
      model: "gpt-4o-realtime-preview-2024-12-17",
      voice: "echo",
      instructions: `You are Alex, a friendly and professional project assistant for Instabids. Help homeowners describe their projects clearly and gather all necessary details.
      
      Focus on understanding:
      1. Project type and scope
      2. Timeline and urgency
      3. Budget expectations
      4. Specific requirements
      5. Property details
      
      Be conversational, encouraging, and helpful. Ask for photos when appropriate.`,
      tools: [
        {
          type: "function",
          name: "saveProjectDetails",
          description: "Save project details from conversation",
          parameters: {
            type: "object",
            properties: {
              projectType: { type: "string" },
              description: { type: "string" },
              timeline: { type: "string" },
              budget: { type: "string" },
              location: { type: "string" },
              additionalDetails: { type: "object" },
            },
            required: ["projectType", "description"],
          },
        },
      ],
    });

    const client = realtimeClient.current;

    client.on("connected", () => {
      setConnectionStatus("connected");
      toast.success("Voice connection established!");
      setCurrentExpression(alexExpressions.happy);
    });

    client.on("error", (error) => {
      console.error("Realtime API error:", error);
      setConnectionStatus("disconnected");
      toast.error("Voice connection error");
    });

    client.on("response.audio_transcript.done", (event) => {
      const assistantMessage: Message = {
        id: `assistant_${Date.now()}`,
        role: "assistant",
        content: event.transcript,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
      setIsSpeaking(false);
    });

    client.on("input_audio_transcription.completed", async (event) => {
      const userMessage: Message = {
        id: `user_${Date.now()}`,
        role: "user",
        content: event.transcript,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsListening(false);

      // Also send to backend for storage
      if (onSendMessage) {
        try {
          await onSendMessage(event.transcript, []);
        } catch (error) {
          console.error("Error sending to backend:", error);
        }
      }
    });

    return () => {
      if (realtimeClient.current) {
        realtimeClient.current.disconnect();
      }
      if (audioProcessor.current) {
        audioProcessor.current.destroy();
      }
    };
  }, [audioMode, onSendMessage]);

  // Detect signup triggers (from CIAChat)
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.role === "assistant") {
      const content = lastMessage.content.toLowerCase();

      const accountTriggers = [
        "create an account",
        "sign up to get",
        "would you like to create",
        "get your professional bids",
        "start receiving bids",
        "to receive your bid cards",
        "register to get contractors",
        "create your instabids account",
      ];

      const shouldShowSignup = accountTriggers.some((trigger) => content.includes(trigger));

      if (shouldShowSignup && !showSignupModal) {
        // Extract project info for modal
        let detectedProject = "home project";
        let projectDescription = "";

        for (const msg of messages) {
          if (msg.role === "user") {
            const userContent = msg.content.toLowerCase();
            if (userContent.includes("kitchen")) detectedProject = "kitchen renovation";
            else if (userContent.includes("bathroom")) detectedProject = "bathroom renovation";
            else if (userContent.includes("roof")) detectedProject = "roofing project";
            // Add more as needed
            projectDescription = msg.content;
            break;
          }
        }

        setExtractedProjectInfo({
          projectType: detectedProject,
          description: projectDescription,
        });

        setShowSignupModal(true);
      }
    }
  }, [messages, showSignupModal]);

  // Listen for signup triggers from bid card preview
  useEffect(() => {
    const handleTriggerSignup = (event: CustomEvent) => {
      const { bidCardId, conversationId } = event.detail;
      setPendingConversion({ bidCardId, conversationId });
      setExtractedProjectInfo({
        projectType: "bathroom renovation", // Could extract from conversation
        description: "Complete bathroom renovation with shower, vanity, and flooring"
      });
      setShowSignupModal(true);
    };

    window.addEventListener('triggerSignup', handleTriggerSignup as EventListener);
    return () => window.removeEventListener('triggerSignup', handleTriggerSignup as EventListener);
  }, []);

  // Update personality based on conversation (from RealtimeCIAChat)
  const updatePersonality = (message: string) => {
    const lowerMessage = message.toLowerCase();
    if (lowerMessage.includes("urgent") || lowerMessage.includes("asap")) {
      setPersonality("professional");
      setCurrentExpression(alexExpressions.working);
    } else if (lowerMessage.includes("excited") || lowerMessage.includes("!")) {
      setPersonality("enthusiastic");
      setCurrentExpression(alexExpressions.excited);
    } else if (lowerMessage.includes("?")) {
      setPersonality("helpful");
      setCurrentExpression(alexExpressions.thinking);
    } else if (lowerMessage.includes("think") || lowerMessage.includes("maybe")) {
      setPersonality("thoughtful");
      setCurrentExpression(alexExpressions.analyzing);
    } else {
      setPersonality("friendly");
      setCurrentExpression(alexExpressions.happy);
    }
  };

  // Handle streaming response updates  
  useEffect(() => {
    if (streamingResponse && streamingMessageId) {
      // Update the streaming message content in real-time
      setMessages((prev) => 
        prev.map((msg) => 
          msg.id === streamingMessageId 
            ? { ...msg, content: streamingResponse, isStreaming: isStreaming }
            : msg
        )
      );
    }
  }, [streamingResponse, streamingMessageId, isStreaming]);

  // Handle streaming completion
  useEffect(() => {
    if (!isStreaming && streamingMessageId && streamingResponse) {
      console.log("🎯 STREAM COMPLETION: Finalizing message and clearing streaming state", {
        isStreaming,
        streamingMessageId,
        hasResponse: !!streamingResponse
      });
      
      // Finalize the streaming message
      setMessages((prev) => 
        prev.map((msg) => 
          msg.id === streamingMessageId 
            ? { 
                ...msg, 
                content: streamingResponse,
                isStreaming: false
              }
            : msg
        )
      );

      // Clear streaming state immediately and definitively
      setStreamingMessageId(null);
      setCurrentExpression(alexExpressions.happy);
      
      console.log("✅ STREAM CLEARED: Streaming state reset to null");
      
      // Log performance metrics
      if (metrics) {
        console.log("Stream metrics:", {
          firstTokenLatency: metrics.first_token_ms,
          totalLatency: metrics.total_time_ms,
          modelUsed: metrics.model_used,
          fallbackUsed: metrics.fallback_used
        });
      }
    }
  }, [isStreaming, streamingMessageId, streamingResponse, metrics, alexExpressions.happy]);

  // Handle streaming errors
  useEffect(() => {
    if (streamError && streamingMessageId) {
      console.error("Streaming error:", streamError);
      toast.error("Failed to get response");
      
      // Remove the failed streaming message
      setMessages((prev) => prev.filter(msg => msg.id !== streamingMessageId));
      setStreamingMessageId(null);
      setCurrentExpression(alexExpressions.working);
    }
  }, [streamError, streamingMessageId, alexExpressions.working]);

  // Debug: Track isStreaming state changes
  useEffect(() => {
    console.log("🎯 STREAMING STATE CHANGED:", {
      isStreaming,
      streamingMessageId,
      timestamp: new Date().toISOString()
    });
  }, [isStreaming, streamingMessageId]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Handle image selection
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length + selectedImages.length > 5) {
      toast.error("You can upload a maximum of 5 images");
      return;
    }

    for (const file of files) {
      const error = StorageService.validateImage(file);
      if (error) {
        toast.error(error);
        return;
      }
    }

    setSelectedImages([...selectedImages, ...files]);
    const newPreviews = files.map((file) => URL.createObjectURL(file));
    setImagePreview([...imagePreview, ...newPreviews]);
  };

  const removeImage = (index: number) => {
    const newImages = selectedImages.filter((_, i) => i !== index);
    const newPreviews = imagePreview.filter((_, i) => i !== index);
    URL.revokeObjectURL(imagePreview[index]);
    setSelectedImages(newImages);
    setImagePreview(newPreviews);
  };

  // Main send message handler with SSE streaming
  const handleSendMessage = async () => {
    if (!inputMessage.trim() && selectedImages.length === 0) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: inputMessage,
      images: imagePreview.length > 0 ? [...imagePreview] : undefined,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentMessage = inputMessage;
    setInputMessage("");
    setCurrentExpression(alexExpressions.analyzing);

    // Update personality based on message
    updatePersonality(currentMessage);

    try {
      // Convert images to base64
      const imageDataUrls: string[] = [];
      for (const file of selectedImages) {
        const dataUrl = await StorageService.fileToBase64(file);
        imageDataUrls.push(dataUrl);
      }

      // Create streaming assistant message
      const assistantMessageId = `assistant_${Date.now()}`;
      const assistantMessage: Message = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setStreamingMessageId(assistantMessageId);

      // Convert chat history to streaming format
      const chatMessages = messages.map(msg => ({
        role: msg.role as 'user' | 'assistant',
        content: msg.content
      }));

      // Add current user message with images
      const userMessageWithImages: any = {
        role: "user" as const,
        content: currentMessage
      };
      
      // Include images if any were uploaded
      if (imageDataUrls.length > 0) {
        userMessageWithImages.images = imageDataUrls;
      }
      
      chatMessages.push(userMessageWithImages);

      // Start streaming with images support and RFI context if available
      const streamRequest: any = {
        messages: chatMessages,
        conversation_id: sessionId,
        user_id: user?.id || "00000000-0000-0000-0000-000000000000",
        max_tokens: 500,
        model_preference: "gpt-5"
      };
      
      // Include RFI context if provided
      if (projectContext?.rfi_id) {
        streamRequest.rfi_context = projectContext;
      }
      
      await streamMessage(streamRequest);

    } catch (error) {
      console.error("Error sending message:", error);
      toast.error("Failed to send message");
      setCurrentExpression(alexExpressions.working);
    } finally {
      setSelectedImages([]);
      setImagePreview([]);
      imagePreview.forEach((url) => {
        if (url.startsWith("blob:")) {
          URL.revokeObjectURL(url);
        }
      });
    }
  };

  // Mock response generator with phases
  const generateMockResponseWithPhase = (message: string, phase: string) => {
    const lower = message.toLowerCase();

    switch (phase) {
      case "intro":
        if (lower.includes("kitchen") || lower.includes("bathroom") || lower.includes("roof")) {
          return {
            response: `Great! A ${lower.includes("kitchen") ? "kitchen" : lower.includes("bathroom") ? "bathroom" : "roofing"} project. Let me gather some details to match you with the right contractors. What's your timeline for this project?`,
            phase: "discovery",
            extractedData: {
              projectType: lower.includes("kitchen") ? "kitchen" : lower.includes("bathroom") ? "bathroom" : "roofing",
            },
          };
        }
        return {
          response: "I'd love to help! Could you tell me what type of home improvement project you're considering?",
          phase: "intro",
        };

      case "discovery":
        return {
          response: "Thanks for that info! Can you tell me more about your budget range and any specific requirements?",
          phase: "details",
        };

      case "details":
        return {
          response: "Excellent details! It would be really helpful to see some photos of the area. Can you upload a few photos?",
          phase: "photos",
        };

      case "photos":
        return {
          response: "Perfect! I have all the information needed. Let me review what we've discussed and then we can connect you with qualified contractors.",
          phase: "review",
        };

      case "review":
        return {
          response: "Great! I'll now process your project information and match you with 3-5 qualified contractors. You should hear back within 24 hours!",
          phase: "complete",
        };

      default:
        return {
          response: "I'd be happy to help with your project! What brings you to Instabids today?",
          phase: "intro",
        };
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleAudioMode = async () => {
    if (!audioMode) {
      setAudioMode(true);
      toast.success("Voice mode activated!");
    } else {
      setAudioMode(false);
      if (realtimeClient.current) {
        realtimeClient.current.disconnect();
      }
      setConnectionStatus("disconnected");
      toast.success("Switched to text mode");
    }
  };

  const handleAccountCreated = async (userData: { name: string; email: string; userId: string }) => {
    onAccountCreated?.(userData);

    let welcomeContent = `Welcome to InstaBids, ${userData.name}! Your account has been created successfully.`;
    
    // If there's a pending conversion, convert the bid card
    if (pendingConversion) {
      try {
        const response = await fetch(`/api/cia/potential-bid-cards/${pendingConversion.bidCardId}/convert-to-bid-card`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          }
        });

        if (response.ok) {
          const result = await response.json();
          welcomeContent += ` Your project has been converted to an official bid card (${result.bid_card_number}) and we're now connecting you with qualified contractors in your area!`;
          
          // Clear pending conversion
          setPendingConversion(null);
        } else {
          console.error('Failed to convert bid card:', await response.text());
          welcomeContent += ` I'll now prepare your project details and start connecting you with qualified contractors.`;
        }
      } catch (error) {
        console.error('Error converting bid card:', error);
        welcomeContent += ` I'll now prepare your project details and start connecting you with qualified contractors.`;
      }
    } else {
      welcomeContent += ` I'll now prepare your project details and start connecting you with qualified contractors.`;
    }

    const welcomeMessage: Message = {
      id: (Date.now() + 2).toString(),
      role: "assistant",
      content: welcomeContent,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, welcomeMessage]);
    setShowSignupModal(false);
  };

  const getPersonalityColor = () => {
    switch (personality) {
      case "friendly":
        return "from-blue-400 to-blue-600";
      case "professional":
        return "from-gray-400 to-gray-600";
      case "enthusiastic":
        return "from-yellow-400 to-orange-500";
      case "thoughtful":
        return "from-purple-400 to-purple-600";
      case "helpful":
        return "from-green-400 to-green-600";
      default:
        return "from-blue-400 to-blue-600";
    }
  };

  return (
    <div className="flex h-[700px] max-w-7xl mx-auto bg-white rounded-lg shadow-lg">
      <div className="flex-1 flex flex-col">
        {/* Enhanced Header with Progress */}
        <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-purple-700 text-white p-4 rounded-t-lg">
          <div className="flex justify-between items-center mb-3">
            <div className="flex items-center gap-3">
              <motion.div
                animate={{
                  scale: isSpeaking ? [1, 1.2, 1] : 1,
                  rotate: isLoading ? 360 : 0,
                }}
                transition={{
                  scale: { repeat: Infinity, duration: 1 },
                  rotate: { duration: 2, repeat: Infinity, ease: "linear" },
                }}
                className="text-3xl bg-white/20 p-2 rounded-full"
              >
                {currentExpression}
              </motion.div>
              <div>
                <h2 className="text-xl font-bold flex items-center gap-2">
                  Alex from Instabids
                  {isSpeaking && <Volume2 className="w-4 h-4 animate-pulse" />}
                </h2>
                <p className="text-sm opacity-90">Your AI Project Assistant</p>
                {audioMode && (
                  <p className="text-xs opacity-75">
                    {connectionStatus === "connected" && "🔊 Voice Active"}
                    {connectionStatus === "connecting" && "⏳ Connecting..."}
                    {connectionStatus === "disconnected" && "❌ Disconnected"}
                  </p>
                )}
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={toggleAudioMode}
                className={`p-2 rounded-lg transition-all ${
                  audioMode ? "bg-white/30" : "bg-white/10 hover:bg-white/20"
                }`}
                title="Voice Mode"
              >
                <Headphones className="w-5 h-5" />
              </button>

              <button
                type="button"
                onClick={() => setVoiceEnabled(!voiceEnabled)}
                className={`p-2 rounded-lg transition-all ${
                  voiceEnabled ? "bg-white/30" : "bg-white/10 hover:bg-white/20"
                }`}
                title="Voice responses"
              >
                {voiceEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
              </button>

              <button
                type="button"
                onClick={() => setShowImages(!showImages)}
                className={`p-2 rounded-lg transition-all ${
                  showImages ? "bg-white/30" : "bg-white/10 hover:bg-white/20"
                }`}
                title="Toggle images"
              >
                {showImages ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
              </button>

              <button
                type="button"
                onClick={() => setShowDataSidebar(!showDataSidebar)}
                className={`p-2 rounded-lg transition-all ${
                  showDataSidebar ? "bg-white/30" : "bg-white/10 hover:bg-white/20"
                }`}
                title="Toggle data sidebar"
              >
                <Brain className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="flex gap-2">
            {phases.map((phase) => (
              <div key={phase.id} className="flex-1">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    phase.status === "completed"
                      ? "bg-green-400"
                      : phase.status === "active"
                        ? "bg-yellow-400"
                        : "bg-white/20"
                  }`}
                />
                <div className="flex items-center gap-1 mt-1">
                  {phase.icon}
                  <span className="text-xs opacity-75">{phase.name}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-transparent to-gray-50/50">
          <AnimatePresence>
            {messages.filter(msg => !(msg.isStreaming && !msg.content)).map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20, scale: 0.9 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`flex items-start gap-3 max-w-[80%] ${
                    message.role === "user" ? "flex-row-reverse" : "flex-row"
                  }`}
                >
                  {/* Avatar */}
                  <motion.div
                    animate={{
                      scale: message.isStreaming ? [1, 1.1, 1] : 1,
                    }}
                    transition={{ repeat: Infinity, duration: 0.5 }}
                    className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                      message.role === "user"
                        ? "bg-blue-600 text-white"
                        : `bg-gradient-to-br ${getPersonalityColor()} text-white`
                    }`}
                  >
                    {message.role === "user" ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                  </motion.div>

                  {/* Message bubble */}
                  <motion.div
                    layout
                    className={`rounded-2xl px-4 py-3 ${
                      message.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-white border border-gray-200 text-gray-800 shadow-md"
                    }`}
                  >
                    <div>
                      <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                    </div>

                    {/* Images */}
                    {showImages && message.images && message.images.length > 0 && (
                      <div className="mt-3 grid grid-cols-2 gap-2">
                        {message.images.map((img, idx) => (
                          <motion.img
                            key={idx}
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            src={img}
                            alt={`Upload ${idx + 1}`}
                            className="rounded-lg w-full h-32 object-cover cursor-pointer hover:scale-105 transition-transform"
                            onClick={() => window.open(img, "_blank")}
                          />
                        ))}
                      </div>
                    )}

                    {/* Unified Attachments */}
                    {message.attachments && message.attachments.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {message.attachments.map((attachment) => (
                          <AttachmentPreview 
                            key={attachment.id} 
                            attachment={attachment} 
                          />
                        ))}
                      </div>
                    )}

                    {/* Bid Card Attachments */}
                    {message.bidCards && message.bidCards.length > 0 && (
                      <ChatBidCardAttachment
                        bidCards={message.bidCards}
                        aiRecommendation={message.aiRecommendation}
                        onCardClick={(card) => {
                          const submitUrl = `/contractor/submit-proposal?bid=${card.bid_card_number}`;
                          window.open(submitUrl, "_blank");
                        }}
                      />
                    )}

                    {mounted && (
                      <p
                        className={`text-xs mt-2 ${
                          message.role === "user" ? "text-blue-100" : "text-gray-500"
                        }`}
                      >
                        {message.timestamp.toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    )}
                  </motion.div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Streaming/Typing Indicator */}
          <AnimatePresence>
            {isStreaming && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex justify-start"
                onAnimationStart={() => console.log("🔄 STREAMING INDICATOR SHOWN: isStreaming =", isStreaming)}
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-md">
                    <div className="flex items-center gap-2">
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 1, repeat: Infinity }}
                      >
                        <Zap className="w-4 h-4 text-green-600" />
                      </motion.div>
                      <p className="text-gray-600 italic">
                        Alex is responding... (GPT-5)
                        <span className="text-xs text-red-500 block">
                          Debug: isStreaming={isStreaming.toString()}, streamingId={streamingMessageId || 'null'}
                        </span>
                      </p>
                      <button
                        onClick={abortStream}
                        className="ml-2 p-1 hover:bg-gray-100 rounded"
                        title="Stop response"
                      >
                        <Square className="w-3 h-3 text-gray-500" />
                      </button>
                    </div>
                    <div className="flex gap-1 mt-2">
                      {[0, 1, 2].map((i) => (
                        <motion.div
                          key={i}
                          animate={{
                            y: [0, -10, 0],
                            backgroundColor: isStreaming 
                              ? ["#10B981", "#3B82F6", "#10B981"] 
                              : ["#3B82F6", "#8B5CF6", "#3B82F6"],
                          }}
                          transition={{
                            duration: 1.5,
                            repeat: Infinity,
                            delay: i * 0.2,
                          }}
                          className="w-2 h-2 rounded-full"
                        />
                      ))}
                    </div>
                    {metrics && (
                      <div className="text-xs text-gray-500 mt-1">
                        {metrics.first_token_ms && `First token: ${metrics.first_token_ms}ms`}
                        {metrics.fallback_used && ` • Fallback: ${metrics.model_used}`}
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div ref={messagesEndRef} />
        </div>

        {/* Image Preview */}
        <AnimatePresence>
          {imagePreview.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="p-4 bg-gray-50 border-t"
            >
              <div className="flex gap-2 overflow-x-auto">
                {imagePreview.map((preview, index) => (
                  <div key={index} className="relative flex-shrink-0">
                    <img
                      src={preview}
                      alt={`Preview ${index + 1}`}
                      className="w-16 h-16 object-cover rounded-lg"
                    />
                    <button
                      type="button"
                      onClick={() => removeImage(index)}
                      className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-600"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Input Area */}
        <div className="p-4 bg-white border-t border-gray-200">
          <div className="flex items-end gap-3">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="p-3 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
              title="Upload images"
            >
              <Camera className="w-5 h-5" />
            </button>

            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={audioMode ? "Voice mode active - speak or type..." : "Describe your project..."}
                className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                rows={1}
                style={{ minHeight: "48px", maxHeight: "120px" }}
              />
            </div>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSendMessage}
              disabled={isStreaming || (!inputMessage.trim() && selectedImages.length === 0)}
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-3 rounded-xl hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isStreaming ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </motion.button>
          </div>

          <div className="flex justify-between items-center mt-2">
            <p className="text-xs text-gray-500">
              {audioMode ? "Voice mode: Speak naturally or type" : "Press Enter to send • Shift+Enter for new line"}
            </p>
            <div className="flex items-center gap-2 text-xs">
              <Zap className="w-3 h-3 text-yellow-500" />
              <span className="text-gray-500">
                {audioMode ? "OpenAI Realtime WebRTC" : 
                 isStreaming ? "Streaming with GPT-5" :
                 "Powered by GPT-5 + SSE Streaming"}
              </span>
              {metrics && metrics.first_token_ms && (
                <span className="text-green-600 font-medium">
                  {metrics.first_token_ms}ms first token
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*"
          onChange={handleImageSelect}
          className="hidden"
        />
      </div>

      {/* Data Sidebar (from DynamicCIAChat) */}
      <AnimatePresence>
        {showDataSidebar && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 400, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="border-l bg-gray-50 p-4 overflow-y-auto"
          >
            {/* Real-Time Bid Card Preview */}
            <div className="mb-6">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                Live Bid Card Building
              </h3>
              <RealTimeBidCardDisplay
                bidCardData={bidCardData}
                loading={bidCardLoading}
                error={bidCardError}
                onRefresh={refreshBidCard}
              />
            </div>
            
            <h3 className="font-semibold text-gray-800 mb-3">Project Details</h3>

            {Object.keys(extractedData).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(extractedData).map(([key, value]) => (
                  <div key={key} className="bg-white p-3 rounded-lg shadow-sm">
                    <dt className="text-sm font-medium text-gray-600 capitalize">
                      {key.replace(/([A-Z])/g, " $1").trim()}
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {typeof value === "object" ? JSON.stringify(value) : String(value)}
                    </dd>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">Project details will appear here as you chat with Alex.</p>
            )}

            <div className="mt-6">
              <h4 className="font-medium text-gray-800 mb-2">What's Next?</h4>
              <div className="text-sm text-gray-600">
                {currentPhase === "intro" && "Tell Alex about your project type"}
                {currentPhase === "discovery" && "Share your timeline and requirements"}
                {currentPhase === "details" && "Discuss budget and specific needs"}
                {currentPhase === "photos" && "Upload photos of the project area"}
                {currentPhase === "review" && "Review your project details"}
                {currentPhase === "complete" && "Your project is ready for contractor matching!"}
              </div>
            </div>

            <div className="mt-6">
              <h4 className="font-medium text-gray-800 mb-2">Personality Mode</h4>
              <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs text-white bg-gradient-to-r ${getPersonalityColor()}`}>
                {personality === "enthusiastic" && <Zap className="w-3 h-3" />}
                {personality === "thoughtful" && <Brain className="w-3 h-3" />}
                {personality !== "enthusiastic" && personality !== "thoughtful" && <Sparkles className="w-3 h-3" />}
                {personality}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Account Signup Modal */}
      <AccountSignupModal
        isOpen={showSignupModal}
        onClose={() => setShowSignupModal(false)}
        onSuccess={handleAccountCreated}
        projectInfo={extractedProjectInfo}
      />
    </div>
  );
};

export default UltimateCIAChat;