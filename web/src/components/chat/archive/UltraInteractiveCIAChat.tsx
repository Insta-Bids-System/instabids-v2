"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  Bot,
  Camera,
  Eye,
  EyeOff,
  Headphones,
  Loader2,
  Send,
  Sparkles,
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
import ChatBidCardAttachment from "./ChatBidCardAttachment";

interface UltraInteractiveCIAChatProps {
  onSendMessage?: (message: string, images?: string[]) => Promise<any>;
  initialMessage?: string;
  projectContext?: any;
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

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  images?: string[];
  phase?: string;
  isStreaming?: boolean;
  bidCards?: BidCard[];
  aiRecommendation?: string;
}

const UltraInteractiveCIAChat: React.FC<UltraInteractiveCIAChatProps> = ({
  onSendMessage,
  initialMessage = "Welcome to Instabids! I'm Alex, your AI project assistant. Tell me about your home project and I'll help you get competitive bids from verified contractors. What are you looking to get done?",
  projectContext,
}) => {
  // State management
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: initialMessage,
      timestamp: new Date(),
    },
  ]);

  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [imagePreview, setImagePreview] = useState<string[]>([]);
  const [_streamingMessageId, _setStreamingMessageId] = useState<string | null>(null);

  // OpenAI Realtime API states
  const [audioMode, setAudioMode] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<
    "disconnected" | "connecting" | "connected"
  >("disconnected");

  // UI states
  const [showImages, setShowImages] = useState(true);
  const [currentExpression, setCurrentExpression] = useState("🤖");
  const [typingThought, _setTypingThought] = useState("");

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const realtimeClient = useRef<OpenAIRealtimeWebRTC | null>(null);
  const audioProcessor = useRef<AudioProcessor | null>(null);
  const hasInitialMessageSent = useRef(false);

  // Alex expressions for personality
  const alexExpressions = {
    happy: "😊",
    thinking: "🤔",
    excited: "🤩",
    working: "⚡",
    analyzing: "🔍",
    listening: "👂",
  };

  const _typingThoughts = [
    "Analyzing your project details...",
    "Thinking about the best contractors...",
    "Calculating potential savings...",
    "Reviewing similar projects...",
    "Preparing personalized recommendations...",
  ];

  // Initialize OpenAI Realtime client
  useEffect(() => {
    // Initialize audio processor
    audioProcessor.current = new AudioProcessor();

    // Get API key from environment
    const apiKey = import.meta.env.VITE_OPENAI_API_KEY;
    if (!apiKey) {
      console.error("VITE_OPENAI_API_KEY not found in environment variables");
      toast.error("OpenAI API key not configured");
      return;
    }

    // Initialize realtime client with CIA personality
    realtimeClient.current = new OpenAIRealtimeWebRTC({
      apiKey,
      model: "gpt-4o-realtime-preview-2024-12-17",
      voice: "echo", // Male voice instead of alloy (female)
      instructions: `You are Alex, a friendly and professional project assistant for Instabids. Your role is to help homeowners describe their home improvement projects so we can connect them with the perfect contractors at competitive prices.

## Your Goals:
1. Make the homeowner feel comfortable and supported
2. Collect all necessary project information naturally through conversation
3. Help them articulate their vision clearly
4. Understand their timeline and budget constraints
5. Encourage photo uploads for better project understanding

## Key Information to Collect (12 Data Points):
1. Project Type (kitchen, bathroom, roofing, etc.)
2. Current Condition (description and request photos)
3. Desired Outcome (their vision)
4. Timeline (start date and completion expectations)
5. Budget Range (minimum and maximum)
6. Property Details (type, location)
7. Urgency Level (emergency, urgent, flexible, planning)
8. Material Preferences (if any)
9. Previous Related Work
10. Access Constraints (HOA, building restrictions)
11. Decision Maker (who approves)
12. Contact Preferences

## Voice Chat Guidelines:
- Keep responses brief (1-2 sentences) since this is voice
- Ask one main question at a time
- Be warm and conversational
- Request photos when helpful: "Could you take some photos of the area?"
- Focus on understanding their needs, not selling services
- Never make pricing estimates - that's for contractors

Start by asking what kind of home project they're planning and work through the 12 data points naturally.`,
      tools: [
        {
          type: "function",
          name: "saveProjectDetails",
          description: "Save the project details extracted from the conversation",
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

    // Set up event listeners
    const client = realtimeClient.current;

    client.on("connected", () => {
      console.log("Connected to OpenAI Realtime API via WebRTC");
      setConnectionStatus("connected");
      toast.success("Voice connection established!");
      setCurrentExpression(alexExpressions.happy);
    });

    client.on("error", (error) => {
      console.error("Realtime API error:", error);
      setConnectionStatus("disconnected");
      toast.error("Voice connection error. Using text mode.");
      setCurrentExpression(alexExpressions.working);
    });

    client.on("disconnected", () => {
      setConnectionStatus("disconnected");
      setCurrentExpression(alexExpressions.working);
    });

    client.on("response.audio_transcript.done", async (event) => {
      console.log("🤖 Alex responded:", event.transcript);

      // Add AI's text response to chat
      const assistantMessage: Message = {
        id: `assistant_${Date.now()}`,
        role: "assistant",
        content: event.transcript,
        timestamp: new Date(),
      };

      setMessages((prev) => {
        console.log("📝 Adding Alex voice response to chat:", event.transcript);
        const newMessages = [...prev, assistantMessage];
        console.log("📝 Total messages now:", newMessages.length);
        return newMessages;
      });

      setIsLoading(false);
      setIsSpeaking(false);
      setCurrentExpression(alexExpressions.happy);

      // DON'T send OpenAI's response to CIA agent - that would create duplicate voices!
      // Only send user input to CIA agent, not AI responses
    });

    client.on("input_audio_transcription.completed", async (event) => {
      console.log("🎤 User spoke:", event.transcript);

      // Add user's transcribed message to chat immediately
      const userMessage: Message = {
        id: `user_${Date.now()}`,
        role: "user",
        content: event.transcript,
        timestamp: new Date(),
      };

      setMessages((prev) => {
        console.log("📝 Adding user voice message to chat:", event.transcript);
        const newMessages = [...prev, userMessage];
        console.log("📝 Total messages now:", newMessages.length);
        return newMessages;
      });

      setIsListening(false);
      setCurrentExpression(alexExpressions.thinking);

      // In voice mode, let OpenAI Realtime handle the conversation
      // Send to CIA agent for data storage and business logic tracking
      if (onSendMessage) {
        try {
          console.log("💾 Sending user voice input to CIA agent for storage...");
          await onSendMessage(event.transcript, []);
          console.log("💾 Successfully sent to CIA agent");
        } catch (error) {
          console.error("❌ Error sending to CIA agent for storage:", error);
        }
      }
    });

    // Add catch-all event listener to see what events are firing
    const originalEmit = client.emit.bind(client);
    client.emit = (event, ...args) => {
      console.log("🔔 Event fired:", event, args);
      return originalEmit(event, ...args);
    };

    client.on("response.function_call_arguments.done", async (event) => {
      console.log("Function call:", event.name, event.arguments);
      // Handle function calls (save project, analyze image, etc.)
      if (event.name === "saveProjectDetails" && onSendMessage) {
        try {
          const args = JSON.parse(event.arguments);
          await onSendMessage(JSON.stringify(args));
        } catch (error) {
          console.error("Error calling function:", error);
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
  }, [onSendMessage]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Auto-send initial message when projectContext is present
  useEffect(() => {
    if (projectContext && initialMessage && !hasInitialMessageSent.current && onSendMessage) {
      hasInitialMessageSent.current = true;
      // Small delay to ensure component is fully mounted
      setTimeout(async () => {
        setInputMessage(initialMessage);

        // Directly call the send logic instead of the function
        if (!initialMessage.trim()) return;

        const newMessage: Message = {
          id: Date.now().toString(),
          role: "user",
          content: initialMessage,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, newMessage]);
        setInputMessage("");
        setIsLoading(true);
        setCurrentExpression(alexExpressions.analyzing);

        try {
          const result = await onSendMessage(initialMessage, []);

          if (result) {
            const assistantMessage: Message = {
              id: (Date.now() + 1).toString(),
              role: "assistant",
              content: result.response,
              timestamp: new Date(),
              phase: result.phase,
              bidCards: result.bidCards || undefined,
              aiRecommendation: result.aiRecommendation || undefined,
            };
            setMessages((prev) => [...prev, assistantMessage]);
          }

          setIsLoading(false);
          setCurrentExpression(alexExpressions.happy);
        } catch (error) {
          console.error("Error sending auto message:", error);
          setIsLoading(false);
          setCurrentExpression(alexExpressions.working);
        }
      }, 500);
    }
  }, [projectContext, initialMessage, onSendMessage]);

  // Connect to OpenAI Realtime API
  const connectToRealtime = async () => {
    if (!realtimeClient.current) return false;

    try {
      setConnectionStatus("connecting");
      setCurrentExpression(alexExpressions.working);
      await realtimeClient.current.connect();
      return true;
    } catch (error) {
      console.error("Failed to connect to Realtime API:", error);
      setConnectionStatus("disconnected");
      toast.error("Failed to connect to voice service. Using text mode.");
      return false;
    }
  };

  // Handle sending messages
  const handleSendMessage = async () => {
    if (!inputMessage.trim() && selectedImages.length === 0) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: inputMessage,
      images: imagePreview.length > 0 ? [...imagePreview] : undefined,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputMessage("");
    setIsLoading(true);
    setCurrentExpression(alexExpressions.analyzing);

    try {
      // Always send images to CIA agent for processing
      if (selectedImages.length > 0 && onSendMessage) {
        // Convert images to base64 for sending
        const imageDataUrls: string[] = [];
        for (const file of selectedImages) {
          const dataUrl = await StorageService.fileToBase64(file);
          imageDataUrls.push(dataUrl);
        }

        console.log("📸 Sending images to CIA agent:", imageDataUrls.length);
        const result = await onSendMessage(
          inputMessage || "I've uploaded some images for you to analyze.",
          imageDataUrls
        );

        if (result) {
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: result.response,
            timestamp: new Date(),
            phase: result.phase,
            bidCards: result.bidCards || undefined,
            aiRecommendation: result.aiRecommendation || undefined,
          };
          setMessages((prev) => [...prev, assistantMessage]);
        }
      } else if (audioMode && realtimeClient.current && realtimeClient.current.isConnected()) {
        // For voice mode without images, use OpenAI Realtime
        if (inputMessage.trim()) {
          realtimeClient.current.sendText(inputMessage);
        }
      } else {
        // Use REST API for text mode without images
        if (onSendMessage && inputMessage.trim()) {
          const result = await onSendMessage(inputMessage, []);

          if (result) {
            const assistantMessage: Message = {
              id: (Date.now() + 1).toString(),
              role: "assistant",
              content: result.response,
              timestamp: new Date(),
              phase: result.phase,
              bidCards: result.bidCards || undefined,
              aiRecommendation: result.aiRecommendation || undefined,
            };
            setMessages((prev) => [...prev, assistantMessage]);
          }
        }
      }

      setIsLoading(false);
      setCurrentExpression(alexExpressions.happy);
    } catch (error) {
      console.error("Error sending message:", error);
      toast.error("Failed to send message");
      setIsLoading(false);
      setCurrentExpression(alexExpressions.working);
    } finally {
      setSelectedImages([]);
      setImagePreview([]);
    }
  };

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Toggle audio mode (full voice conversation)
  const toggleAudioMode = async () => {
    if (!audioMode) {
      // Enabling audio mode - ensure clean connection
      console.log("🎤 Activating voice mode...");

      // Clean up any existing connection first
      if (realtimeClient.current) {
        console.log("🧹 Cleaning up existing connection...");
        realtimeClient.current.disconnect();
        await new Promise((resolve) => setTimeout(resolve, 500)); // Wait for cleanup
      }

      const connected = await connectToRealtime();
      if (connected) {
        setAudioMode(true);
        setCurrentExpression(alexExpressions.listening);
        toast.success("Voice mode activated! I can now hear and speak with you directly.");
      }
    } else {
      // Disabling audio mode
      console.log("🔇 Deactivating voice mode...");
      setAudioMode(false);
      setIsListening(false);
      setIsSpeaking(false);
      if (realtimeClient.current) {
        realtimeClient.current.disconnect();
      }
      setConnectionStatus("disconnected");
      setCurrentExpression(alexExpressions.happy);
      toast.success("Switched to text mode");
    }
  };

  // Toggle voice responses (auto-speak)
  const toggleVoiceResponses = () => {
    setVoiceEnabled(!voiceEnabled);
    if (!voiceEnabled) {
      toast.success("Voice responses enabled");
    } else {
      toast.success("Voice responses disabled");
    }
  };

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setSelectedImages((prev) => [...prev, ...files]);

    // Create preview URLs
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview((prev) => [...prev, e.target?.result as string]);
      };
      reader.readAsDataURL(file);
    });

    files.forEach((file) => {
      toast.success(`Added ${file.name}`);
    });
  };

  // Remove image
  const removeImage = (index: number) => {
    setSelectedImages((prev) => prev.filter((_, i) => i !== index));
    setImagePreview((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="flex flex-col h-[700px] max-w-5xl mx-auto bg-gradient-to-b from-gray-50 to-white rounded-2xl shadow-2xl overflow-hidden">
      {/* Enhanced Header */}
      <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-purple-700 text-white p-4">
        <div className="flex justify-between items-center">
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

          {/* Voice Controls */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={toggleAudioMode}
              className={`p-2 rounded-lg transition-all ${
                audioMode && connectionStatus === "connected"
                  ? "bg-white/30 text-white"
                  : "bg-white/10 hover:bg-white/20"
              }`}
              title="Full Voice Mode (OpenAI Realtime)"
            >
              <Headphones className="w-5 h-5" />
            </button>

            <button
              type="button"
              onClick={toggleVoiceResponses}
              className={`p-2 rounded-lg transition-all ${
                voiceEnabled ? "bg-white/30 text-white" : "bg-white/10 hover:bg-white/20"
              }`}
              title="Voice responses"
            >
              {voiceEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
            </button>

            <button
              type="button"
              onClick={() => setShowImages(!showImages)}
              className={`p-2 rounded-lg transition-all ${
                showImages ? "bg-white/30 text-white" : "bg-white/10 hover:bg-white/20"
              }`}
              title="Toggle images"
            >
              {showImages ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-transparent to-gray-50/50">
        <AnimatePresence>
          {messages.map((message) => (
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
                      : "bg-gradient-to-br from-purple-500 to-blue-600 text-white"
                  }`}
                >
                  {message.role === "user" ? (
                    <User className="w-5 h-5" />
                  ) : (
                    <Bot className="w-5 h-5" />
                  )}
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
                  <p className="whitespace-pre-wrap leading-relaxed">
                    {message.content}
                    {message.isStreaming && (
                      <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
                    )}
                  </p>

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

                  {/* Bid Card Attachments */}
                  {message.bidCards && message.bidCards.length > 0 && (
                    <ChatBidCardAttachment
                      bidCards={message.bidCards}
                      aiRecommendation={message.aiRecommendation}
                      onCardClick={(card) => {
                        // Handle bid card click - navigate to submit proposal page
                        const submitUrl = `/contractor/submit-proposal?bid=${card.bid_card_number}`;
                        window.open(submitUrl, "_blank");
                      }}
                    />
                  )}

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
                </motion.div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing Indicator */}
        <AnimatePresence>
          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex justify-start"
            >
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-md">
                  <div className="flex items-center gap-2">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    >
                      <Sparkles className="w-4 h-4 text-purple-600" />
                    </motion.div>
                    <p className="text-gray-600 italic">{typingThought}</p>
                  </div>
                  <div className="flex gap-1 mt-2">
                    {[0, 1, 2].map((i) => (
                      <motion.div
                        key={i}
                        animate={{
                          y: [0, -10, 0],
                          backgroundColor: ["#3B82F6", "#8B5CF6", "#3B82F6"],
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
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div ref={messagesEndRef} />
      </div>

      {/* Audio Mode Indicator (Small overlay) */}
      <AnimatePresence>
        {audioMode && connectionStatus === "connected" && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute top-4 right-4 bg-gradient-to-br from-blue-600/95 to-purple-600/95 text-white p-4 rounded-lg shadow-lg z-10 max-w-xs"
          >
            <div className="text-center">
              <motion.div
                animate={{
                  scale: isListening ? [1, 1.2, 1] : 1,
                }}
                transition={{
                  repeat: Infinity,
                  duration: 1.5,
                }}
                className="text-2xl mb-2"
              >
                🎤
              </motion.div>
              <p className="text-sm font-semibold mb-1">Voice Mode Active</p>
              <p className="text-xs opacity-90 mb-3">
                {isListening ? "Listening..." : "Speak naturally"}
              </p>
              <button
                type="button"
                onClick={() => setIsListening(false)}
                className="bg-white/20 hover:bg-white/30 text-white px-3 py-1 rounded text-xs transition-all"
              >
                Exit
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

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
          {/* File upload */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-3 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
            title="Upload images"
          >
            <Camera className="w-5 h-5" />
          </button>

          {/* Text input */}
          <div className="flex-1 relative">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                audioMode ? "Voice mode active - speak or type..." : "Type your message..."
              }
              className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              rows={1}
              style={{ minHeight: "48px", maxHeight: "120px" }}
              disabled={false}
            />
          </div>

          {/* Send button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleSendMessage}
            disabled={isLoading || (!inputMessage.trim() && selectedImages.length === 0)}
            className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-3 rounded-xl hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </motion.button>
        </div>

        <div className="flex justify-between items-center mt-2">
          <p className="text-xs text-gray-500">
            {audioMode
              ? "Voice mode: Speak naturally or type"
              : "Press Enter to send • Shift+Enter for new line"}
          </p>
          <div className="flex items-center gap-2 text-xs">
            <Zap className="w-3 h-3 text-yellow-500" />
            <span className="text-gray-500">
              {audioMode ? "OpenAI Realtime WebRTC" : "Powered by Claude Opus 4"}
            </span>
          </div>
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*"
        onChange={handleFileSelect}
        className="hidden"
      />
    </div>
  );
};

export default UltraInteractiveCIAChat;
