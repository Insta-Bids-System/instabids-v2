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
import { Brain, Mic, MicOff, Sparkles, Upload, Volume2, VolumeX, Zap } from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { uploadFile } from "@/services/api";
import { AudioProcessor, OpenAIRealtimeClient } from "@/services/openai-realtime";
import "@chatscope/chat-ui-kit-styles/dist/default/styles.min.css";

interface RealtimeCIAChatProps {
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

const RealtimeCIAChat: React.FC<RealtimeCIAChatProps> = ({
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

  const fileInputRef = useRef<HTMLInputElement>(null);
  const realtimeClient = useRef<OpenAIRealtimeClient | null>(null);
  const audioProcessor = useRef<AudioProcessor | null>(null);
  const mediaStream = useRef<MediaStream | null>(null);

  // Initialize OpenAI Realtime client
  useEffect(() => {
    // Initialize audio processor
    audioProcessor.current = new AudioProcessor();

    // Initialize realtime client with CIA personality (proxy handles auth)
    realtimeClient.current = new OpenAIRealtimeClient({
      apiKey: "proxy-handled", // Not needed with proxy
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
      console.log("Connected to OpenAI Realtime API");
      if (audioMode) {
        startListening();
      }
    });

    client.on("error", (error) => {
      console.error("Realtime API error:", error);
      toast.error("Voice connection error. Please try again.");
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
    });

    client.on("response.audio.done", async (audioData) => {
      // Play the audio response
      if (voiceEnabled && audioProcessor.current) {
        setIsSpeaking(true);
        try {
          await audioProcessor.current.playPCM16(audioData);
        } catch (error) {
          console.error("Error playing audio:", error);
        }
        setIsSpeaking(false);
      }
    });

    client.on("input_audio_transcription.completed", (event) => {
      // Add user's transcribed message to chat
      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        message: event.transcript,
        sender: "You",
        direction: "outgoing",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, newMessage]);
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

    // Connect to the API
    client.connect().catch((error) => {
      console.error("Failed to connect:", error);
      toast.error("Unable to connect to voice service");
    });

    return () => {
      if (realtimeClient.current) {
        realtimeClient.current.disconnect();
      }
      if (mediaStream.current) {
        mediaStream.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, [audioMode, voiceEnabled, onSendMessage, startListening]);

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

  const startListening = async () => {
    if (!realtimeClient.current || !audioProcessor.current) return;

    const hasPermission = await checkMicPermission();
    if (!hasPermission) return;

    try {
      mediaStream.current = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 24000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      setIsListening(true);

      // Set up audio processing
      const audioContext = new AudioContext({ sampleRate: 24000 });
      const source = audioContext.createMediaStreamSource(mediaStream.current);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);

      processor.onaudioprocess = (e) => {
        if (!isListening || !realtimeClient.current) return;

        const inputData = e.inputBuffer.getChannelData(0);
        const pcm16Data = audioProcessor.current?.float32ToPCM16(inputData);
        realtimeClient.current.sendAudio(pcm16Data);
      };

      source.connect(processor);
      processor.connect(audioContext.destination);
    } catch (error) {
      console.error("Error starting microphone:", error);
      toast.error("Failed to access microphone");
      setIsListening(false);
    }
  };

  const stopListening = () => {
    setIsListening(false);
    if (mediaStream.current) {
      mediaStream.current.getTracks().forEach((track) => track.stop());
      mediaStream.current = null;
    }
    if (realtimeClient.current) {
      realtimeClient.current.commitAudio();
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
          if (realtimeClient.current) {
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

    // Send message via Realtime API
    if (realtimeClient.current?.isConnected()) {
      realtimeClient.current.sendText(textMessage);
    } else {
      // Fallback to REST API
      if (onSendMessage) {
        try {
          await onSendMessage(textMessage, files);
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

  const toggleAudioMode = () => {
    setAudioMode(!audioMode);
    if (!audioMode) {
      checkMicPermission();
      toast.success("Audio mode activated! Click the microphone to start talking.");
    } else {
      stopListening();
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
                  {isSpeaking && (
                    <motion.span
                      animate={{ opacity: [0.5, 1, 0.5] }}
                      transition={{ repeat: Infinity, duration: 1.5 }}
                      className="text-xs text-green-600"
                    >
                      Speaking...
                    </motion.span>
                  )}
                </div>
              }
            />
            <ConversationHeader.Actions>
              <VoiceCallButton
                onClick={toggleAudioMode}
                title={audioMode ? "Switch to text" : "Switch to voice"}
                className={audioMode ? "text-green-600" : ""}
              />
              <button
                type="button"
                onClick={match.match(/onClick={[^}]+}/)[0]}
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

          {!audioMode ? (
            <MessageInput
              placeholder="Describe your project..."
              onSend={handleSend}
              sendButton={true}
              attachButton={false}
              onAttachClick={() => fileInputRef.current?.click()}
            />
          ) : (
            <div className="flex items-center justify-center p-4 bg-gray-50 border-t">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                animate={isListening ? { scale: [1, 1.1, 1] } : {}}
                transition={isListening ? { repeat: Infinity, duration: 1.5 } : {}}
                onClick={isListening ? stopListening : startListening}
                className={`p-6 rounded-full shadow-lg transition-all ${
                  isListening ? "bg-red-500 hover:bg-red-600" : "bg-blue-500 hover:bg-blue-600"
                }`}
              >
                {isListening ? (
                  <MicOff className="w-8 h-8 text-white" />
                ) : (
                  <Mic className="w-8 h-8 text-white" />
                )}
              </motion.button>
              <div className="ml-4 text-sm text-gray-600">
                {isListening ? "Listening... Click to stop" : "Click to start speaking"}
              </div>
            </div>
          )}
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
      {!audioMode && (
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => fileInputRef.current?.click()}
          className="absolute bottom-20 right-4 p-3 bg-white rounded-full shadow-lg border border-gray-200 hover:bg-gray-50 transition-colors"
          title="Upload images"
        >
          <Upload className="w-5 h-5 text-gray-600" />
        </motion.button>
      )}

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
                  onClick={match.match(/onClick={[^}]+}/)[0]}
                  className="text-red-500 hover:text-red-700"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default RealtimeCIAChat;
