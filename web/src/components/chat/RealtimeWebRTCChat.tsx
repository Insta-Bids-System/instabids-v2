import {
  Avatar,
  ChatContainer,
  ConversationHeader,
  InfoButton,
  MainContainer,
  Message,
  MessageInput,
  MessageList,
  TypingIndicator,
  VoiceCallButton,
} from "@chatscope/chat-ui-kit-react";
import { motion } from "framer-motion";
import { Brain, Sparkles, Upload, Volume2, VolumeX, Zap } from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { uploadFile } from "@/services/api";
import { AudioProcessor, OpenAIRealtimeWebRTC } from "@/services/openai-realtime-webrtc";
import "@chatscope/chat-ui-kit-styles/dist/default/styles.min.css";

interface RealtimeWebRTCChatProps {
  onSendMessage?: (message: string, files?: File[]) => Promise<void>;
  initialMessage?: string;
}

interface ChatMessage {
  id: string;
  message: string;
  sender: string;
  direction: "incoming" | "outgoing";
  timestamp: Date;
  audioUrl?: string;
}

// CIA Agent personality traits
const personalities = [
  "friendly",
  "professional",
  "enthusiastic",
  "thoughtful",
  "helpful",
] as const;
type Personality = (typeof personalities)[number];

const RealtimeWebRTCChat: React.FC<RealtimeWebRTCChatProps> = ({
  onSendMessage,
  initialMessage = "Hey there! I'm Alex from Instabids. Tell me about your project - I'd love to help you get competitive bids from verified contractors!",
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      message: initialMessage,
      sender: "Alex",
      direction: "incoming",
      timestamp: new Date(),
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [personality, setPersonality] = useState<Personality>("friendly");
  const [files, setFiles] = useState<File[]>([]);
  const [audioMode, setAudioMode] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [_micPermission, setMicPermission] = useState<boolean | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<
    "disconnected" | "connecting" | "connected"
  >("disconnected");

  const fileInputRef = useRef<HTMLInputElement>(null);
  const realtimeClient = useRef<OpenAIRealtimeWebRTC | null>(null);
  const audioProcessor = useRef<AudioProcessor | null>(null);

  // Initialize OpenAI Realtime WebRTC client
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
      voice: "alloy",
      instructions: `You are Alex, an AI assistant for Instabids, a platform that connects homeowners with contractors.
      
Your personality:
- Friendly, professional, and enthusiastic about helping homeowners
- Expert at understanding home improvement projects
- Great at asking clarifying questions to get project details
- Encouraging and supportive throughout the process
- Natural conversationalist who builds rapport

Your goals:
1. Understand the homeowner's project needs
2. Ask about timeline, budget expectations, and specific requirements
3. Gather enough details to create a comprehensive bid request
4. Make the homeowner feel confident about using Instabids

Keep responses conversational and natural. Use casual language while maintaining professionalism.`,
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
        {
          type: "function",
          name: "analyzeImage",
          description: "Analyze an uploaded image to understand project details",
          parameters: {
            type: "object",
            properties: {
              imageUrl: { type: "string" },
              description: { type: "string" },
            },
            required: ["imageUrl"],
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
    });

    client.on("error", (error) => {
      console.error("Realtime API error:", error);
      setConnectionStatus("disconnected");
      toast.error("Voice connection error. Falling back to text mode.");
      setAudioMode(false);
    });

    client.on("disconnected", () => {
      setConnectionStatus("disconnected");
      toast.error("Voice connection lost");
    });

    client.on("response.audio_transcript.done", (event) => {
      // Add AI's text response to chat
      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        message: event.transcript,
        sender: "Alex",
        direction: "incoming",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, newMessage]);
      setIsTyping(false);
      setIsSpeaking(false);
    });

    client.on("input_audio_transcription.completed", async (event) => {
      // Add user's transcribed message to chat
      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        message: event.transcript,
        sender: "You",
        direction: "outgoing",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, newMessage]);
      setIsListening(false);

      // IMPORTANT: Send voice transcript to CIA agent
      if (onSendMessage && event.transcript.trim()) {
        console.log("📤 Sending voice transcript to CIA:", event.transcript);
        try {
          const result = await onSendMessage(event.transcript, []);

          // Add CIA response to chat
          if (result?.response) {
            const ciaResponse: ChatMessage = {
              id: `${Date.now().toString()}_cia`,
              message: result.response,
              sender: "Alex (CIA)",
              direction: "incoming",
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, ciaResponse]);
          }
        } catch (error) {
          console.error("Error sending voice to CIA:", error);
          toast.error("Failed to process voice message");
        }
      }
    });

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

  const checkMicPermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      setMicPermission(true);
      return true;
    } catch (_error) {
      setMicPermission(false);
      toast.error("Microphone permission denied. Please enable it in your browser settings.");
      return false;
    }
  };

  const connectToRealtime = async () => {
    if (!realtimeClient.current) return false;

    try {
      setConnectionStatus("connecting");
      await realtimeClient.current.connect();
      return true;
    } catch (error) {
      console.error("Failed to connect to Realtime API:", error);
      setConnectionStatus("disconnected");
      toast.error("Failed to connect to voice service. Using text mode.");
      return false;
    }
  };

  const handleSend = async (textMessage: string) => {
    if (!textMessage.trim() && files.length === 0) return;

    // Add user message
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      message: textMessage,
      sender: "You",
      direction: "outgoing",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, newMessage]);
    setIsTyping(true);

    // Handle file uploads
    if (files.length > 0) {
      for (const file of files) {
        try {
          const uploadedFile = await uploadFile(file);
          // Send file info to AI
          if (realtimeClient.current?.isConnected()) {
            realtimeClient.current.sendText(
              `User uploaded an image: ${file.name}. Image URL: ${uploadedFile.url}`
            );
          }
        } catch (error) {
          console.error("File upload error:", error);
          toast.error(`Failed to upload ${file.name}`);
        }
      }
      setFiles([]);
    }

    // Send message via Realtime API only if connected and in audio mode
    if (audioMode && realtimeClient.current && realtimeClient.current.isConnected()) {
      realtimeClient.current.sendText(textMessage);
    } else {
      // Use REST API for text mode or when WebRTC is not connected
      if (onSendMessage) {
        try {
          const result = await onSendMessage(textMessage, files);
          if (result) {
            // Add AI response to chat
            const aiMessage: ChatMessage = {
              id: `${Date.now().toString()}_ai`,
              message: result.response,
              sender: "Alex",
              direction: "incoming",
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, aiMessage]);
          }
        } catch (error) {
          console.error("Error sending message:", error);
          toast.error("Failed to send message");
        }
      }
      setIsTyping(false);
    }

    // Update personality based on message sentiment
    updatePersonality(textMessage);
  };

  const updatePersonality = (message: string) => {
    const lowerMessage = message.toLowerCase();
    if (lowerMessage.includes("urgent") || lowerMessage.includes("asap")) {
      setPersonality("professional");
    } else if (lowerMessage.includes("excited") || lowerMessage.includes("!")) {
      setPersonality("enthusiastic");
    } else if (lowerMessage.includes("?")) {
      setPersonality("helpful");
    } else if (lowerMessage.includes("think") || lowerMessage.includes("maybe")) {
      setPersonality("thoughtful");
    } else {
      setPersonality("friendly");
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    setFiles((prev) => [...prev, ...selectedFiles]);

    selectedFiles.forEach((file) => {
      toast.success(`Added ${file.name}`);
    });
  };

  const toggleAudioMode = async () => {
    if (!audioMode) {
      // Enabling audio mode
      const hasPermission = await checkMicPermission();
      if (!hasPermission) return;

      const connected = await connectToRealtime();
      if (connected) {
        setAudioMode(true);
        toast.success("Audio mode activated! The AI will speak and listen automatically.");
      }
    } else {
      // Disabling audio mode
      setAudioMode(false);
      setIsListening(false);
      setIsSpeaking(false);
      if (realtimeClient.current) {
        realtimeClient.current.disconnect();
      }
      toast.success("Switched to text mode");
    }
  };

  const _toggleVoice = () => {
    setVoiceEnabled(!voiceEnabled);
    if (!voiceEnabled) {
      toast.success("Voice responses enabled");
    } else {
      toast.success("Voice responses disabled");
    }
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

  const getPersonalityIcon = () => {
    switch (personality) {
      case "enthusiastic":
        return <Zap className="w-4 h-4" />;
      case "thoughtful":
        return <Brain className="w-4 h-4" />;
      default:
        return <Sparkles className="w-4 h-4" />;
    }
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case "connected":
        return "text-green-600";
      case "connecting":
        return "text-yellow-600";
      case "disconnected":
        return "text-gray-400";
    }
  };

  return (
    <div className="relative h-full">
      <MainContainer className="border border-gray-200 rounded-lg shadow-sm">
        <ChatContainer>
          <ConversationHeader>
            <ConversationHeader.Back />
            <Avatar
              src="https://api.dicebear.com/7.x/bottts/svg?seed=Alex&backgroundColor=3b82f6"
              name="Alex"
              className="mr-2"
            />
            <ConversationHeader.Content
              userName="Alex from Instabids"
              info={
                <div className="flex items-center gap-2">
                  <motion.span
                    animate={{
                      background: `linear-gradient(to right, var(--tw-gradient-stops))`,
                    }}
                    className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs text-white bg-gradient-to-r ${getPersonalityColor()}`}
                  >
                    {getPersonalityIcon()}
                    {personality}
                  </motion.span>
                  {audioMode && (
                    <span className={`text-xs ${getConnectionStatusColor()}`}>
                      {connectionStatus === "connected" && "🔊 Voice Active"}
                      {connectionStatus === "connecting" && "⏳ Connecting..."}
                      {connectionStatus === "disconnected" && "❌ Disconnected"}
                    </span>
                  )}
                  {isSpeaking && (
                    <motion.span
                      animate={{ opacity: [0.5, 1, 0.5] }}
                      transition={{ repeat: Infinity, duration: 1.5 }}
                      className="text-xs text-green-600"
                    >
                      Speaking...
                    </motion.span>
                  )}
                  {isListening && (
                    <motion.span
                      animate={{ opacity: [0.5, 1, 0.5] }}
                      transition={{ repeat: Infinity, duration: 1 }}
                      className="text-xs text-blue-600"
                    >
                      Listening...
                    </motion.span>
                  )}
                </div>
              }
            />
            <ConversationHeader.Actions>
              <VoiceCallButton
                onClick={toggleAudioMode}
                title={audioMode ? "Switch to text" : "Switch to voice (WebRTC)"}
                className={audioMode && connectionStatus === "connected" ? "text-green-600" : ""}
              />
              <button
                type="button"
                onClick={_toggleVoice}
                className={`p-2 rounded-lg transition-colors ${
                  voiceEnabled ? "text-blue-600 bg-blue-50" : "text-gray-400"
                }`}
                title={voiceEnabled ? "Disable voice responses" : "Enable voice responses"}
              >
                {voiceEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
              </button>
              <InfoButton title="About Alex" />
            </ConversationHeader.Actions>
          </ConversationHeader>

          <MessageList
            scrollBehavior="smooth"
            typingIndicator={isTyping ? <TypingIndicator content="Alex is thinking..." /> : null}
          >
            {messages.map((msg, _i) => (
              <Message
                key={msg.id}
                model={{
                  message: msg.message,
                  sentTime: msg.timestamp.toLocaleTimeString(),
                  sender: msg.sender,
                  direction: msg.direction,
                  position: "single",
                }}
                avatarSpacer={msg.direction === "outgoing"}
              >
                {msg.direction === "incoming" && (
                  <Avatar
                    src="https://api.dicebear.com/7.x/bottts/svg?seed=Alex&backgroundColor=3b82f6"
                    name="Alex"
                    size="sm"
                  />
                )}
              </Message>
            ))}
          </MessageList>

          {/* Always show text input - WebRTC handles audio automatically */}
          <MessageInput
            placeholder={audioMode ? "Type or speak your message..." : "Describe your project..."}
            onSend={handleSend}
            sendButton={true}
            attachButton={false}
            onAttachClick={() => fileInputRef.current?.click()}
          />
        </ChatContainer>
      </MainContainer>

      {/* File Upload Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*"
        className="hidden"
        onChange={handleFileSelect}
      />

      {/* File Upload Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => fileInputRef.current?.click()}
        className="absolute bottom-20 right-4 p-3 bg-white rounded-full shadow-lg border border-gray-200 hover:bg-gray-50 transition-colors"
        title="Upload images"
      >
        <Upload className="w-5 h-5 text-gray-600" />
      </motion.button>

      {/* File Preview */}
      {files.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-20 left-4 right-16 bg-white p-2 rounded-lg shadow-lg border border-gray-200"
        >
          <div className="flex items-center gap-2 overflow-x-auto">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-sm"
              >
                <span className="truncate max-w-[100px]">{file.name}</span>
                <button
                  type="button"
                  onClick={() => _removeFromQueue(index)}
                  className="text-red-500 hover:text-red-700"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* WebRTC Status Indicator */}
      {audioMode && (
        <div className="absolute bottom-4 left-4">
          <div
            className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs ${
              connectionStatus === "connected"
                ? "bg-green-100 text-green-800"
                : connectionStatus === "connecting"
                  ? "bg-yellow-100 text-yellow-800"
                  : "bg-red-100 text-red-800"
            }`}
          >
            {connectionStatus === "connected" && "✅ WebRTC Connected"}
            {connectionStatus === "connecting" && "⏳ Connecting via WebRTC..."}
            {connectionStatus === "disconnected" && "❌ WebRTC Disconnected"}
          </div>
        </div>
      )}
    </div>
  );
};

export default RealtimeWebRTCChat;
