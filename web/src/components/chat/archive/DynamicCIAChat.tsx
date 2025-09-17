"use client";

import {
  AttachmentButton,
  Avatar,
  ChatContainer,
  MainContainer,
  Message,
  MessageInput,
  MessageList,
  SendButton,
  TypingIndicator,
} from "@chatscope/chat-ui-kit-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import "@chatscope/chat-ui-kit-styles/dist/default/styles.min.css";
import { AlertCircle, Bot, CheckCircle, Clock, Image as ImageIcon, User, X } from "lucide-react";
import toast from "react-hot-toast";
import { StorageService } from "@/lib/storage";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  images?: string[];
  timestamp: Date;
  phase?: string;
  extractedData?: any;
}

interface ProjectPhase {
  id: string;
  name: string;
  description: string;
  status: "pending" | "active" | "completed";
  icon: React.ReactNode;
}

interface DynamicCIAChatProps {
  onSendMessage?: (
    message: string,
    images: string[]
  ) => Promise<{
    response: string;
    phase?: string;
    extractedData?: any;
  }>;
}

export default function DynamicCIAChat({ onSendMessage }: DynamicCIAChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hi! I'm Alex, your project assistant at Instabids. I'll help you describe your home project so we can find you the perfect contractors at the best prices. What kind of project brings you here today?",
      timestamp: new Date(),
      phase: "intro",
    },
  ]);

  const [inputMessage, setInputMessage] = useState("");
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [imagePreview, setImagePreview] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentPhase, setCurrentPhase] = useState("intro");
  const [extractedData, setExtractedData] = useState<any>({});
  const [mounted, setMounted] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Project phases for progress tracking
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
      icon: <AlertCircle className="w-4 h-4" />,
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

  // Fix hydration error
  useEffect(() => {
    setMounted(true);
  }, []);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length + selectedImages.length > 5) {
      toast.error("You can upload a maximum of 5 images");
      return;
    }

    // Validate each file
    for (const file of files) {
      const error = StorageService.validateImage(file);
      if (error) {
        toast.error(error);
        return;
      }
    }

    setSelectedImages([...selectedImages, ...files]);

    // Create preview URLs
    const newPreviews = files.map((file) => URL.createObjectURL(file));
    setImagePreview([...imagePreview, ...newPreviews]);
  };

  const removeImage = (index: number) => {
    const newImages = selectedImages.filter((_, i) => i !== index);
    const newPreviews = imagePreview.filter((_, i) => i !== index);

    // Revoke the URL to prevent memory leaks
    URL.revokeObjectURL(imagePreview[index]);

    setSelectedImages(newImages);
    setImagePreview(newPreviews);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() && selectedImages.length === 0) return;

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: inputMessage,
      images: imagePreview.length > 0 ? [...imagePreview] : undefined,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      // Convert images to base64 for sending
      const imageDataUrls: string[] = [];
      for (const file of selectedImages) {
        const dataUrl = await StorageService.fileToBase64(file);
        imageDataUrls.push(dataUrl);
      }

      // Call the message handler
      let result: { response: string; phase?: string; extractedData?: any };

      if (onSendMessage) {
        console.log("Sending message to CIA API...");
        result = await onSendMessage(inputMessage, imageDataUrls);
      } else {
        // Fallback mock response with phase progression
        console.log("No API handler provided, using mock response with phases");
        await new Promise((resolve) => setTimeout(resolve, 1500));
        result = generateMockResponseWithPhase(inputMessage, currentPhase);
      }

      // Update phase and extracted data if provided
      if (result.phase && result.phase !== currentPhase) {
        setCurrentPhase(result.phase);
        console.log(`Phase transition: ${currentPhase} → ${result.phase}`);
      }

      if (result.extractedData) {
        setExtractedData((prev) => ({ ...prev, ...result.extractedData }));
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: result.response,
        timestamp: new Date(),
        phase: result.phase || currentPhase,
        extractedData: result.extractedData,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      toast.error("Failed to send message. Please try again.");
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "I'm sorry, I encountered an error. Please make sure the backend is running (cd ai-agents && python main.py).",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setSelectedImages([]);
      setImagePreview([]);
    }
  };

  // Generate mock responses with phase progression
  const generateMockResponseWithPhase = (
    message: string,
    phase: string
  ): { response: string; phase?: string; extractedData?: any } => {
    const lower = message.toLowerCase();

    switch (phase) {
      case "intro":
        if (lower.includes("kitchen") || lower.includes("bathroom") || lower.includes("roof")) {
          return {
            response: `Great! A ${lower.includes("kitchen") ? "kitchen" : lower.includes("bathroom") ? "bathroom" : "roofing"} project. Let me gather some details to match you with the right contractors. What's your timeline for this project - is this something urgent or can we plan it out?`,
            phase: "discovery",
            extractedData: {
              projectType: lower.includes("kitchen")
                ? "kitchen"
                : lower.includes("bathroom")
                  ? "bathroom"
                  : "roofing",
            },
          };
        }
        return {
          response:
            "I'd love to help! Could you tell me what type of home improvement project you're considering?",
          phase: "intro",
        };

      case "discovery":
        if (lower.includes("budget") || lower.includes("cost") || lower.includes("price")) {
          return {
            response:
              "Perfect! Budget planning is crucial. Based on the project type, I can help estimate costs. Could you share what you're hoping to spend or any specific requirements you have in mind?",
            phase: "details",
            extractedData: { budgetDiscussed: true },
          };
        }
        if (lower.includes("urgent") || lower.includes("asap") || lower.includes("emergency")) {
          return {
            response:
              "I understand this is urgent. Let's fast-track your project. What specific details can you share about the work needed?",
            phase: "details",
            extractedData: { urgency: "urgent" },
          };
        }
        return {
          response:
            "Thanks for that info! Can you tell me more about your budget range and any specific requirements?",
          phase: "discovery",
        };

      case "details":
        return {
          response:
            "Excellent details! It would be really helpful to see some photos of the area. This helps contractors provide more accurate estimates. Can you upload a few photos?",
          phase: "photos",
        };

      case "photos":
        return {
          response:
            "Perfect! I have all the information needed. Let me review what we've discussed and then we can connect you with qualified contractors in your area.",
          phase: "review",
        };

      case "review":
        return {
          response:
            "Great! I'll now process your project information and match you with 3-5 qualified contractors. They'll receive your project details and reach out with estimates. You should hear back within 24 hours!",
          phase: "complete",
        };

      default:
        return {
          response: "I'd be happy to help with your project! What brings you to Instabids today?",
          phase: "intro",
        };
    }
  };

  return (
    <div className="flex flex-col h-[700px] max-w-6xl mx-auto bg-white rounded-lg shadow-lg">
      {/* Header with Progress */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 rounded-t-lg">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Bot className="w-6 h-6" />
              Chat with Alex
            </h2>
            <p className="text-sm opacity-90">Your Instabids Project Assistant</p>
          </div>
          <div className="text-right">
            <p className="text-sm opacity-90">
              Phase: {phases.find((p) => p.id === currentPhase)?.name}
            </p>
            <p className="text-xs opacity-75">
              {Object.keys(extractedData).length} details collected
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="flex gap-2">
          {phases.map((phase, _index) => (
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

      <div className="flex flex-1 overflow-hidden">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Chat Container */}
          <div style={{ position: "relative", height: "100%" }}>
            <MainContainer>
              <ChatContainer>
                <MessageList
                  typingIndicator={
                    isLoading ? <TypingIndicator content="Alex is thinking..." /> : null
                  }
                >
                  {messages.map((message) => (
                    <Message
                      key={message.id}
                      model={{
                        message: message.content,
                        sentTime: mounted ? message.timestamp.toLocaleTimeString() : "now",
                        sender: message.role === "assistant" ? "Alex" : "You",
                        direction: message.role === "user" ? "outgoing" : "incoming",
                        position: "single",
                      }}
                    >
                      {message.role === "assistant" && (
                        <Avatar src="/api/placeholder/32/32" name="Alex" status="available" />
                      )}

                      {/* Display images if any */}
                      {message.images && message.images.length > 0 && (
                        <div className="mt-2 grid grid-cols-2 gap-2">
                          {message.images.map((img, idx) => (
                            <img
                              key={idx}
                              src={img}
                              alt={`Upload ${idx + 1}`}
                              className="rounded-md w-full h-32 object-cover"
                            />
                          ))}
                        </div>
                      )}
                    </Message>
                  ))}
                </MessageList>

                {/* Image Preview Area */}
                {imagePreview.length > 0 && (
                  <div className="px-4 py-2 border-t bg-gray-50">
                    <div className="flex gap-2 overflow-x-auto">
                      {imagePreview.map((preview, index) => (
                        <div key={index} className="relative flex-shrink-0">
                          <img
                            src={preview}
                            alt={`Preview ${index + 1}`}
                            className="w-20 h-20 object-cover rounded-md"
                          />
                          <button
                            type="button"
                            onClick={() => removeImage(index)}
                            className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <MessageInput
                  placeholder="Describe your project or ask a question..."
                  value={inputMessage}
                  onChange={setInputMessage}
                  onSend={handleSendMessage}
                  disabled={isLoading}
                  attachButton={
                    <AttachmentButton
                      onClick={() => fileInputRef.current?.click()}
                      disabled={isLoading}
                    />
                  }
                  sendButton={
                    <SendButton
                      onClick={handleSendMessage}
                      disabled={isLoading || (!inputMessage.trim() && selectedImages.length === 0)}
                    />
                  }
                />
              </ChatContainer>
            </MainContainer>
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

        {/* Sidebar with Extracted Data */}
        <div className="w-80 border-l bg-gray-50 p-4 overflow-y-auto">
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
            <p className="text-gray-500 text-sm">
              Project details will appear here as you chat with Alex.
            </p>
          )}

          {/* Phase Guide */}
          <div className="mt-6">
            <h4 className="font-medium text-gray-800 mb-2">What's Next?</h4>
            <div className="text-sm text-gray-600">
              {currentPhase === "intro" && "Tell Alex about your project type"}
              {currentPhase === "discovery" && "Share your timeline and basic requirements"}
              {currentPhase === "details" && "Discuss budget and specific needs"}
              {currentPhase === "photos" && "Upload photos of the project area"}
              {currentPhase === "review" && "Review your project details"}
              {currentPhase === "complete" && "Your project is ready for contractor matching!"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
