import { Send, Sparkles, TrendingUp, MessageSquare } from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { useAuth } from "@/contexts/AuthContext";

interface PersistentIrisChatProps {
  boardId: string;
  boardTitle: string;
  images: any[];
  onGenerateVision: (elements: string[]) => void;
  clickedImage: any;
  onImageProcessed: () => void;
  boardConversation: any;
  onConversationUpdate: () => void;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  metadata?: any;
}

const PersistentIrisChat: React.FC<PersistentIrisChatProps> = ({
  boardId,
  boardTitle,
  images,
  onGenerateVision,
  clickedImage,
  onImageProcessed,
  boardConversation,
  onConversationUpdate,
}) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load persistent conversation when component mounts or conversation updates
  useEffect(() => {
    if (boardConversation?.conversation_history) {
      const formattedMessages = boardConversation.conversation_history.map((msg: any, idx: number) => ({
        id: `msg-${idx}`,
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.timestamp || Date.now()),
        metadata: msg.metadata
      }));
      setMessages(formattedMessages);
    } else {
      // Initialize with welcome message if no conversation exists
      setMessages([{
        id: "welcome",
        role: "assistant",
        content: `Hi! I'm Iris, your design assistant for "${boardTitle}". I'm here to help you build and refine your vision. As you add photos, I'll analyze them and help you understand your design preferences. The more we work together, the better I can help you create a cohesive project plan.`,
        timestamp: new Date()
      }]);
    }
  }, [boardConversation, boardTitle]);

  // Process clicked image from board
  useEffect(() => {
    if (clickedImage) {
      handleImageAnalysis(clickedImage);
      onImageProcessed();
    }
  }, [clickedImage]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleImageAnalysis = async (image: any) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: `Tell me about this image I selected`,
      timestamp: new Date(),
      metadata: { image_id: image.id, image_url: image.image_url }
    };

    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const response = await fetch(`/api/iris/board/${boardId}/analyze-photo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          photo_url: image.image_url,
          photo_id: image.id,
          photo_metadata: {
            category: image.tags?.includes("current") ? "current" : "ideal",
            tags: image.tags || [],
            source: "board"
          },
          user_message: "Tell me about this image I selected"
        })
      });

      if (response.ok) {
        const data = await response.json();
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: data.analysis || "I've analyzed this image and added it to our conversation context.",
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiResponse]);
        onConversationUpdate(); // Reload conversation to update confidence
      }
    } catch (error) {
      console.error("Error analyzing image:", error);
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I had trouble analyzing that image, but I can still help you with your vision.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      // Use the persistent conversation endpoint
      const response = await fetch(`/api/iris/board/${boardId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage.content,
          user_id: user?.id
        })
      });

      if (response.ok) {
        const data = await response.json();
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: data.response,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiResponse]);
        onConversationUpdate(); // Reload conversation to update confidence
      } else {
        throw new Error("Failed to get response");
      }
    } catch (error) {
      console.error("Error:", error);
      const fallbackResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I'm having trouble connecting right now, but I can still help you organize your vision based on what I see.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, fallbackResponse]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-96 bg-white rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h4 className="font-medium text-sm">Iris - Board Assistant</h4>
            <div className="flex items-center gap-2">
              {boardConversation && (
                <>
                  <span className="text-xs text-gray-500">
                    {boardConversation.conversation_history?.length || 0} messages
                  </span>
                  <span className="text-xs text-gray-400">•</span>
                  <span className="text-xs text-gray-500">
                    Confidence: {Math.round((boardConversation.confidence_score || 0) * 100)}%
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
        
        {boardConversation?.bid_readiness_status && (
          <div className="flex items-center gap-1 px-2 py-1 bg-green-50 rounded-full">
            <TrendingUp className="w-3 h-3 text-green-600" />
            <span className="text-xs text-green-700">
              {boardConversation.bid_readiness_status}
            </span>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-2.5 ${
                message.role === "user" 
                  ? "bg-primary-600 text-white" 
                  : "bg-gray-100 text-gray-900"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-2.5">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Context Summary */}
      {boardConversation?.persistent_context && (
        <div className="px-3 py-2 border-t border-b bg-gray-50">
          <div className="flex items-start gap-2">
            <MessageSquare className="w-4 h-4 text-gray-400 mt-0.5" />
            <div className="flex-1">
              <p className="text-xs text-gray-600 font-medium mb-1">Context Summary:</p>
              <p className="text-xs text-gray-500">
                {images.filter(img => img.tags?.includes("current")).length} current space photos, {" "}
                {images.filter(img => !img.tags?.includes("current") && !img.tags?.includes("vision")).length} inspiration images
                {boardConversation.persistent_context.key_themes && (
                  <span> • Themes: {boardConversation.persistent_context.key_themes.join(", ")}</span>
                )}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask about your vision..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default PersistentIrisChat;