import React, { useState, useEffect, useRef } from 'react';
import { User, Bot, Eye, EyeOff, Send, Loader2, UserPlus, Upload, Image, X } from 'lucide-react';
import { DynamicBidCardPreview } from './DynamicBidCardPreview';
import { usePotentialBidCard } from '@/hooks/usePotentialBidCard';
import { useSSEChatStream } from '@/hooks/useSSEChatStream';
import { useAuth } from '@/contexts/AuthContext';
import { AccountSignupModal } from './AccountSignupModal';
import ImageGallery from './ImageGallery';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  images?: string[];  // Array of image URLs
}

interface CIAChatWithBidCardPreviewProps {
  initialMessage?: string;
  showBidCardPreview?: boolean;
  onProjectReady?: (bidCardId: string) => void;
}

export const CIAChatWithBidCardPreview: React.FC<CIAChatWithBidCardPreviewProps> = ({
  initialMessage = "Hi! I'm Alex, your AI project assistant. Tell me about your home project and I'll help you create a bid card to get competitive quotes from verified contractors. What project are you planning?",
  showBidCardPreview = true,
  onProjectReady
}) => {
  const { user, profile } = useAuth();
  
  // Session management
  const [sessionId] = useState(() => {
    const existingSessionId = localStorage.getItem("cia_session_id");
    if (existingSessionId) return existingSessionId;
    
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem("cia_session_id", newSessionId);
    return newSessionId;
  });

  // Conversation management
  const [conversationId] = useState(() => {
    const existingConversationId = localStorage.getItem("cia_conversation_id");
    if (existingConversationId) return existingConversationId;
    
    const newConversationId = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem("cia_conversation_id", newConversationId);
    return newConversationId;
  });

  // Chat state
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: initialMessage,
      timestamp: new Date()
    }
  ]);

  const [inputMessage, setInputMessage] = useState("");
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const [showBidCard, setShowBidCard] = useState(showBidCardPreview);
  const [showSignupModal, setShowSignupModal] = useState(false);
  const [pendingConversion, setPendingConversion] = useState(false);
  const [uploadedImages, setUploadedImages] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Potential bid card hook
  const {
    bidCard,
    loading: bidCardLoading,
    error: bidCardError,
    createPotentialBidCard,
    updateField,
    convertToOfficialBidCard,
    isComplete,
    completionPercentage
  } = usePotentialBidCard({
    conversationId,
    userId: user?.id,
    sessionId,
    autoCreate: true,
    pollInterval: 10000
  });

  // SSE Streaming Chat Hook
  const {
    streamMessage,
    isStreaming,
    currentMessage: streamingResponse,
    abort: abortStream,
    error: streamError,
  } = useSSEChatStream({
    endpoint: '/api/cia/stream',
    onMessage: (content: string) => {
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
    onComplete: (fullMessage: string) => {
      if (streamingMessageId) {
        setMessages((prev) => 
          prev.map((msg) => 
            msg.id === streamingMessageId 
              ? { ...msg, content: fullMessage, isStreaming: false }
              : msg
          )
        );
        setStreamingMessageId(null);
      }
    },
    onError: (error) => {
      console.error('Streaming error:', error);
      if (streamingMessageId) {
        setMessages((prev) => 
          prev.map((msg) => 
            msg.id === streamingMessageId 
              ? { ...msg, content: "Sorry, there was an error processing your message. Please try again.", isStreaming: false }
              : msg
          )
        );
        setStreamingMessageId(null);
      }
    }
  });

  // Handle image upload
  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const imageDataUrls: string[] = [];
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          const result = e.target?.result as string;
          if (result) {
            imageDataUrls.push(result);
            if (imageDataUrls.length === files.length) {
              setUploadedImages(prev => [...prev, ...imageDataUrls]);
            }
          }
        };
        reader.readAsDataURL(file);
      }
    }
    
    // Clear the file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Remove uploaded image
  const removeImage = (index: number) => {
    setUploadedImages(prev => prev.filter((_, i) => i !== index));
  };

  // Handle message sending
  const handleSendMessage = async () => {
    if ((!inputMessage.trim() && uploadedImages.length === 0) || isStreaming) return;

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: inputMessage.trim() || (uploadedImages.length > 0 ? "I've uploaded some images." : ""),
      timestamp: new Date(),
      images: uploadedImages.length > 0 ? [...uploadedImages] : undefined
    };

    const assistantMessageId = `assistant_${Date.now()}`;
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: "",
      timestamp: new Date(),
      isStreaming: true
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);
    setStreamingMessageId(assistantMessageId);
    
    const messageToSend = inputMessage.trim() || (uploadedImages.length > 0 ? "I've uploaded some images." : "");
    const imagesToSend = [...uploadedImages];
    setInputMessage("");
    setUploadedImages([]); // Clear uploaded images after sending

    try {
      await streamMessage({
        messages: [{ role: 'user', content: messageToSend }],
        conversation_id: conversationId,
        user_id: user?.id || "00000000-0000-0000-0000-000000000000",
        session_id: sessionId,
        images: imagesToSend.length > 0 ? imagesToSend : undefined,
        max_tokens: 500,
        model_preference: "gpt-5"
      });
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => 
        prev.map(msg => 
          msg.id === assistantMessageId 
            ? { ...msg, content: "Sorry, there was an error processing your message. Please try again.", isStreaming: false }
            : msg
        )
      );
      setStreamingMessageId(null);
    }
  };

  // Handle field editing from bid card preview
  const handleFieldEdit = async (fieldName: string, newValue: any) => {
    const success = await updateField(fieldName, newValue, 'manual');
    if (success) {
      console.log(`Updated ${fieldName} to:`, newValue);
    }
  };

  // Handle bid card conversion
  const handleConvertBidCard = async () => {
    if (!isComplete) return;
    
    // Check if user is authenticated
    if (!user) {
      // Show signup modal for anonymous users
      setShowSignupModal(true);
      setPendingConversion(true);
      return;
    }
    
    // User is authenticated, proceed with conversion
    const result = await convertToOfficialBidCard();
    if (result) {
      onProjectReady?.(result.official_bid_card_id);
    }
  };

  // Handle successful signup
  const handleSignupSuccess = async (userData: { name: string; email: string; userId: string }) => {
    setShowSignupModal(false);
    
    // If there was a pending conversion, trigger it now
    if (pendingConversion && bidCard) {
      setPendingConversion(false);
      
      // Wait a moment for auth context to update
      setTimeout(async () => {
        const result = await convertToOfficialBidCard();
        if (result) {
          onProjectReady?.(result.official_bid_card_id);
        }
      }, 1000);
    }
  };

  // Detect project type from messages for signup modal context
  const getProjectInfo = () => {
    const projectKeywords = {
      kitchen: "kitchen renovation",
      bathroom: "bathroom renovation", 
      roofing: "roofing project",
      flooring: "flooring project",
      plumbing: "plumbing work",
      electrical: "electrical work",
      painting: "painting project",
      landscaping: "landscaping project",
    };

    let detectedProject = "home project";
    
    for (const msg of messages) {
      if (msg.role === "user") {
        const userContent = msg.content.toLowerCase();
        for (const [key, value] of Object.entries(projectKeywords)) {
          if (userContent.includes(key)) {
            detectedProject = value;
            break;
          }
        }
      }
    }

    return {
      projectType: detectedProject,
      description: bidCard?.bid_card_preview?.description || ""
    };
  };

  // Handle Enter key for sending messages
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-full max-h-screen">
      {/* Chat Section */}
      <div className={`flex flex-col ${showBidCard ? 'w-2/3' : 'w-full'} transition-all duration-300`}>
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-800">Alex - AI Project Assistant</h3>
              <p className="text-sm text-gray-600">Helping you create your bid card</p>
            </div>
          </div>
          
          {showBidCardPreview && (
            <button
              onClick={() => setShowBidCard(!showBidCard)}
              className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              {showBidCard ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              <span>{showBidCard ? 'Hide' : 'Show'} Bid Card</span>
            </button>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'} items-start space-x-3 max-w-3xl`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  message.role === 'user' ? 'bg-blue-500' : 'bg-gray-500'
                }`}>
                  {message.role === 'user' ? 
                    <User className="w-5 h-5 text-white" /> : 
                    <Bot className="w-5 h-5 text-white" />
                  }
                </div>
                <div className={`rounded-lg p-3 ${
                  message.role === 'user' 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Display images if present */}
                  {message.images && message.images.length > 0 && (
                    <div className="mt-3">
                      <ImageGallery 
                        images={message.images} 
                        maxDisplayed={3}
                        className="max-w-md"
                      />
                    </div>
                  )}
                  
                  {message.isStreaming && (
                    <div className="flex items-center mt-2">
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      <span className="text-sm opacity-75">Typing...</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Input */}
        <div className="border-t border-gray-200 p-4">
          {/* Image Upload Preview */}
          {uploadedImages.length > 0 && (
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-2">
                <Image className="w-4 h-4 text-gray-600" />
                <span className="text-sm text-gray-600">
                  {uploadedImages.length} image{uploadedImages.length !== 1 ? 's' : ''} ready to send
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {uploadedImages.map((image, index) => (
                  <div key={index} className="relative group">
                    <img
                      src={image}
                      alt={`Upload ${index + 1}`}
                      className="w-16 h-16 object-cover rounded-lg border border-gray-300"
                    />
                    <button
                      onClick={() => removeImage(index)}
                      className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div className="flex space-x-3">
            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Tell me about your project or upload photos..."
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                rows={3}
                disabled={isStreaming}
              />
            </div>
            
            {/* File upload button */}
            <div className="flex flex-col space-y-2">
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isStreaming}
                className="px-3 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                title="Upload images"
              >
                <Upload className="w-5 h-5" />
              </button>
              
              <button
                onClick={handleSendMessage}
                disabled={(!inputMessage.trim() && uploadedImages.length === 0) || isStreaming}
                className="px-3 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
              >
                {isStreaming ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Bid Card Preview Section */}
      {showBidCard && showBidCardPreview && (
        <div className="w-1/3 border-l border-gray-200 bg-gray-50 overflow-y-auto">
          <div className="p-4 h-full">
            <DynamicBidCardPreview
              conversationId={conversationId}
              onFieldEdit={handleFieldEdit}
              className="h-full"
            />
            
            {/* Convert to Official Bid Card Button */}
            {isComplete && (
              <div className="mt-4">
                <button
                  onClick={handleConvertBidCard}
                  disabled={pendingConversion}
                  className="w-full bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center space-x-2"
                >
                  {!user && (
                    <UserPlus className="w-4 h-4" />
                  )}
                  <span>
                    {pendingConversion 
                      ? "Creating Account..." 
                      : !user 
                        ? "Sign Up & Get Bids →" 
                        : "Get Contractor Bids →"
                    }
                  </span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Account Signup Modal */}
      <AccountSignupModal
        isOpen={showSignupModal}
        onClose={() => {
          setShowSignupModal(false);
          setPendingConversion(false);
        }}
        onSuccess={handleSignupSuccess}
        projectInfo={getProjectInfo()}
      />
    </div>
  );
};

export default CIAChatWithBidCardPreview;