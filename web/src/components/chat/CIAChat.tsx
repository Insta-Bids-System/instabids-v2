"use client";

import { Image as ImageIcon, Send, X } from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { StorageService } from "@/lib/storage";
import { AccountSignupModal } from "./AccountSignupModal";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  images?: string[];
  timestamp: Date;
}

interface CIAChatProps {
  onSendMessage?: (message: string, images: string[]) => Promise<string>;
  onAccountCreated?: (userData: { name: string; email: string; userId: string }) => void;
  sessionId?: string;
}

export default function CIAChat({ onSendMessage, onAccountCreated, sessionId }: CIAChatProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hi! I'm Alex, your project assistant at InstaBids. Here's what makes us different: We eliminate the expensive lead fees and wasted sales meetings that drive up costs on other platforms. Instead, contractors and homeowners interact directly through our app using photos and conversations to create solid quotes - no sales meetings needed. This keeps all the money savings between you and your contractor, not going to corporations. Contractors save on lead costs and sales time, so they can offer you better prices.\n\nWhat kind of home project brings you here today?",
      timestamp: new Date(),
    },
  ]);

  const [inputMessage, setInputMessage] = useState("");
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [imagePreview, setImagePreview] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [showSignupModal, setShowSignupModal] = useState(false);
  const [extractedProjectInfo, setExtractedProjectInfo] = useState<{
    projectType?: string;
    description?: string;
  }>({});

  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fix hydration error
  useEffect(() => {
    setMounted(true);
  }, []);

  // Load conversation history if sessionId is provided
  useEffect(() => {
    const loadConversationHistory = async () => {
      if (!sessionId) return;

      try {
        const response = await fetch(`/cia/conversation/${sessionId}`);
        const data = await response.json();

        if (data.success && data.messages && data.messages.length > 0) {
          // Convert API format to component format
          const loadedMessages = data.messages.map((msg: any) => ({
            id: msg.id,
            role: msg.role,
            content: msg.content,
            timestamp: new Date(msg.timestamp),
            images: msg.images,
          }));

          console.log(`Loaded ${loadedMessages.length} messages from session ${sessionId}`);
          setMessages(loadedMessages);
        } else {
          console.log(`No conversation history found for session ${sessionId}`);
        }
      } catch (error) {
        console.error("Error loading conversation history:", error);
        // Keep default messages if loading fails
      }
    };

    loadConversationHistory();
  }, [sessionId]);

  // Auto scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Detect account creation prompts from CIA agent
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.role === "assistant") {
      const content = lastMessage.content.toLowerCase();

      // Detect various account creation triggers
      const accountTriggers = [
        "create an account",
        "sign up to get",
        "would you like to create",
        "get your professional bids",
        "start receiving bids",
        "to receive your bid cards",
        "register to get contractors",
        "create your instabids account",
        "let's get your instabids account set up",
        "create a password for your instabids account",
      ];

      const shouldShowSignup = accountTriggers.some((trigger) => content.includes(trigger));

      if (shouldShowSignup && !showSignupModal) {
        // Extract project information from conversation for modal context
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
        let projectDescription = "";

        // Check all messages for project context (prioritize more specific matches)
        for (const msg of messages) {
          if (msg.role === "user") {
            const userContent = msg.content.toLowerCase();

            // Check for specific keywords, prioritizing more specific ones
            if (userContent.includes("plumbing")) {
              detectedProject = "plumbing work";
              projectDescription = msg.content;
            } else if (userContent.includes("painting")) {
              detectedProject = "painting project";
              projectDescription = msg.content;
            } else {
              // Check other keywords
              for (const [key, value] of Object.entries(projectKeywords)) {
                if (userContent.includes(key)) {
                  detectedProject = value;
                  projectDescription = msg.content;
                  break;
                }
              }
            }
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

    try {
      // Upload images first if any are selected
      const uploadedImageUrls: string[] = [];

      if (selectedImages.length > 0) {
        console.log(`Uploading ${selectedImages.length} images...`);

        for (const [index, file] of selectedImages.entries()) {
          try {
            // Upload to storage service
            const uploadResult = await StorageService.uploadImage(file);
            if (uploadResult.success && uploadResult.url) {
              uploadedImageUrls.push(uploadResult.url);
              console.log(`Image ${index + 1} uploaded successfully: ${uploadResult.url}`);
            } else {
              console.error(`Failed to upload image ${index + 1}:`, uploadResult.error);
              toast.error(`Failed to upload image ${index + 1}`);
            }
          } catch (uploadError) {
            console.error(`Error uploading image ${index + 1}:`, uploadError);
            toast.error(`Error uploading image ${index + 1}`);
          }
        }

        if (uploadedImageUrls.length > 0) {
          toast.success(`Successfully uploaded ${uploadedImageUrls.length} image(s)`);
        }
      }

      // Convert images to base64 for API sending (keep existing functionality)
      const imageDataUrls: string[] = [];
      for (const file of selectedImages) {
        const dataUrl = await StorageService.fileToBase64(file);
        imageDataUrls.push(dataUrl);
      }

      // CONTRACTOR DETECTION LOGIC - Check if this is a contractor message
      const isContractorMessage = /\b(contractor|contracting|hvac|plumbing|electrical|painting|roofing|construction|carpentry|flooring|landscaping|pool|solar)\b/i.test(inputMessage) ||
        /\b(company|business|years? (?:in business|experience)|license|insurance|contractor account|create account|sign up|signup)\b/i.test(inputMessage) ||
        /\b(i'm .+ from|we're|my company|my business)\b/i.test(inputMessage);

      // Call the message handler - use default mock if not provided
      let response: string;

      if (onSendMessage) {
        console.log("🚨 UPDATED CODE LOADED - Sending message to API...", {
          messageLength: inputMessage.length,
          imageCount: imageDataUrls.length,
          uploadedUrls: uploadedImageUrls.length,
          isContractorMessage: isContractorMessage,
          detectionTest: "CONTRACTOR DETECTION IS ACTIVE"
        });

        if (isContractorMessage) {
          console.log("🔧 Detected contractor message in CIAChat, using COIA landing page API");
          // Call COIA landing page API directly
          try {
            const apiResponse = await fetch("/api/coia/landing", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                message: inputMessage,
                user_id: sessionId || `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                session_id: sessionId || `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                contractor_lead_id: sessionId || `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                context: { interface: "landing_page" }
              })
            });
            
            if (!apiResponse.ok) {
              throw new Error(`HTTP error! status: ${apiResponse.status}`);
            }
            
            const data = await apiResponse.json();
            console.log("✅ COIA API Response:", data);
            response = data.response || "Thank you for your interest! I'm connecting you with our contractor onboarding system.";
          } catch (error) {
            console.error("❌ COIA API Error:", error);
            response = "I understand you're a contractor! Let me connect you with our contractor onboarding system. There seems to be a connection issue - please try again.";
          }
        } else {
          console.log("🏠 Using CIA homeowner API");
          response = await onSendMessage(inputMessage, imageDataUrls);
        }
      } else {
        // Enhanced fallback mock response with photo awareness
        console.log("No API handler provided, using mock response");
        await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulate API delay
        response = generateMockResponse(inputMessage, uploadedImageUrls.length > 0);
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      toast.error("Failed to send message. Please try again.");
      const errorMessage: Message = {
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

      // Clean up preview URLs to prevent memory leaks
      imagePreview.forEach((url) => {
        if (url.startsWith("blob:")) {
          URL.revokeObjectURL(url);
        }
      });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleAccountCreated = (userData: { name: string; email: string; userId: string }) => {
    // Call parent callback if provided
    onAccountCreated?.(userData);

    // Add a system message to continue the conversation
    const welcomeMessage: Message = {
      id: (Date.now() + 2).toString(),
      role: "assistant",
      content: `Welcome to InstaBids, ${userData.name}! Your account has been created successfully. I'll now prepare your project details and start connecting you with qualified contractors in your area. You'll receive email notifications when contractors submit their bids.`,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, welcomeMessage]);

    // Close the modal
    setShowSignupModal(false);
  };

  const handleCloseSignupModal = () => {
    setShowSignupModal(false);

    // Add a message indicating they can sign up later
    const laterMessage: Message = {
      id: (Date.now() + 2).toString(),
      role: "assistant",
      content:
        "No problem! You can continue exploring your project options. When you're ready to receive contractor bids, just let me know and I'll help you create an account.",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, laterMessage]);
  };

  // Generate mock responses when API is not connected
  const generateMockResponse = (message: string, hasPhotos: boolean = false): string => {
    const lower = message.toLowerCase();

    // Photo-aware responses
    if (hasPhotos) {
      if (lower.includes("kitchen")) {
        return "Thanks for sharing those kitchen photos! I can see the space you're working with. This looks like a great project for contractors to bid on. Are you looking at a full remodel or specific updates like cabinets and countertops?";
      } else if (lower.includes("bathroom")) {
        return "Great photos! I can see the current bathroom layout. Based on what I'm seeing, there are several directions we could go. What's your main goal - updating the style, improving functionality, or fixing specific issues?";
      } else {
        return "Perfect! Those photos really help me understand your project. The visual context makes it much easier for contractors to provide accurate bids. What specific work are you looking to have done?";
      }
    }

    // Regular text-based responses
    if (lower.includes("kitchen")) {
      return "A kitchen renovation - great choice! Kitchen updates offer excellent ROI. Photos of the current space would help contractors provide more accurate bids. Are you planning a full remodel or focusing on specific areas like cabinets, countertops, or appliances?";
    } else if (lower.includes("bathroom")) {
      return "Bathroom renovations can really transform your daily routine! If you have any photos of the current space, that would help contractors understand the scope. What's motivating this project - is it updating the style, fixing issues, or adding functionality?";
    } else if (lower.includes("budget")) {
      return "Instead of focusing on budget first, let's talk about what you want to achieve! This helps contractors provide better value. Kitchen remodels and bathroom updates vary widely based on scope and materials. What's driving this project for you?";
    } else {
      return "I'd be happy to help with your project! Feel free to share any photos if you have them - visuals really help contractors understand what they're bidding on. What type of work are you considering?";
    }
  };

  return (
    <div className="flex flex-col h-[600px] max-w-4xl mx-auto bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="bg-blue-600 text-white p-4 rounded-t-lg">
        <h2 className="text-xl font-semibold">Chat with Alex</h2>
        <p className="text-sm opacity-90">Your Instabids Project Assistant</p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[70%] rounded-lg p-3 ${
                message.role === "user" ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-800"
              }`}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>

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

              {/* Only show timestamp on client to avoid hydration error */}
              {mounted && (
                <p className="text-xs mt-1 opacity-70">{message.timestamp.toLocaleTimeString()}</p>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Image Preview Area */}
      {imagePreview.length > 0 && (
        <div className="px-4 py-2 border-t">
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

      {/* Input Area */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*"
            onChange={handleImageSelect}
            className="hidden"
          />

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
            title="Upload images"
          >
            <ImageIcon size={24} />
          </button>

          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe your project or ask a question..."
            className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={1}
          />

          <button
            type="button"
            onClick={handleSendMessage}
            disabled={isLoading || (!inputMessage.trim() && selectedImages.length === 0)}
            className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={24} />
          </button>
        </div>

        <p className="text-xs text-gray-500 mt-2">
          You can upload up to 5 images. Press Enter to send or Shift+Enter for new line.
        </p>
      </div>

      {/* Account Signup Modal */}
      <AccountSignupModal
        isOpen={showSignupModal}
        onClose={handleCloseSignupModal}
        onSuccess={handleAccountCreated}
        projectInfo={extractedProjectInfo}
      />
    </div>
  );
}
