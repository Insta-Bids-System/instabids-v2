import { Camera, Image, Link2, Send, Sparkles, Upload, X } from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { useAuth } from "@/contexts/AuthContext";
import { supabase } from "@/lib/supabase";
import AIAnalysisDisplay from "./AIAnalysisDisplay";
import type { InspirationBoard } from "../InspirationDashboard";

interface IrisChatProps {
  board?: InspirationBoard | null;
  onClose: () => void;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  suggestions?: string[];
  images?: Array<{
    url: string;
    description: string;
  }>;
  uploadedImages?: Array<{
    id: string;
    image_url: string;
    thumbnail_url?: string;
    ai_analysis?: any;
    tags: string[];
    category: "current" | "ideal";
  }>;
}

const IrisChat: React.FC<IrisChatProps> = ({ board, onClose }) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: board
        ? `Hi! I'm looking at your "${board.title}" board. How can I help you organize and refine your vision?`
        : "Hi! I'm Iris, your design inspiration assistant. I can help you organize your ideas, analyze images, and create a cohesive vision for your home projects. What would you like to explore today?",
      timestamp: new Date(),
      suggestions: board
        ? [
            "Help me organize these images",
            "What style are these images?",
            "Create a vision summary",
            "Estimate project budget",
          ]
        : [
            "Start a new inspiration board",
            "Upload some images to analyze",
            "Tell me about design styles",
            "How does this work?",
          ],
    },
  ]);
  const [input, setInput] = useState("");
  const [photoMode, setPhotoMode] = useState<"inspiration" | "property" | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [uploadingImages, setUploadingImages] = useState<File[]>([]);
  const [imageCategory, setImageCategory] = useState<"ideal" | "current">("ideal");
  const [idealImageId, setIdealImageId] = useState<string | null>(null);
  const [currentImageId, setCurrentImageId] = useState<string | null>(null);
  const [saveToProperty, setSaveToProperty] = useState(false);
  // Removed image generation state - focusing on inspiration finding
  const [tempBoardId, setTempBoardId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [scrollToBottom]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      // Use the actual profile ID from the user (which is what the FK references)
      const user_id = user?.id || "550e8400-e29b-41d4-a716-446655440001"; // Demo homeowner profile ID

      // Call real Iris API with full context awareness
      const response = await fetch("/api/iris/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userMessage.content,
          user_id: user_id,
          board_id: board?.id,
          conversation_context: messages.slice(-10).map((msg) => ({
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp,
          })),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response from Iris");
      }

      const data = await response.json();

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
        suggestions: data.suggestions || [],
      };

      setMessages((prev) => [...prev, aiResponse]);
    } catch (error) {
      console.error("Error calling Iris API:", error);
      // Fallback to simulated response
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: generateIrisResponse(userMessage.content, board),
        timestamp: new Date(),
        suggestions: generateSuggestions(userMessage.content, board),
      };
      setMessages((prev) => [...prev, aiResponse]);
    } finally {
      setIsTyping(false);
    }
  };

  const _getImagesForBoard = async (boardId: string): Promise<any[]> => {
    try {
      const { data, error } = await supabase
        .from("inspiration_images")
        .select("*")
        .eq("board_id", boardId)
        .limit(20);

      if (error) throw error;
      return data || [];
    } catch (error) {
      console.error("Error loading board images:", error);
      return [];
    }
  };

  // Handle image upload button click
  const _handleImageUpload = () => {
    fileInputRef.current?.click();
  };

  // Handle file selection from input
  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const imageFiles = Array.from(files).filter((file) => file.type.startsWith("image/"));

    if (imageFiles.length === 0) {
      toast.error("Please select valid image files");
      return;
    }

    setUploadingImages(imageFiles);
    setIsTyping(true);

    try {
      // Upload images to Supabase storage and create database records
      const uploadedImages = await Promise.all(
        imageFiles.map(async (file) => {
          // Generate unique filename
          const timestamp = Date.now();
          const fileExt = file.name.split(".").pop();
          const fileName = `${user?.id || "anonymous"}_${timestamp}.${fileExt}`;

          // Create a test board if needed for demo
          let tempBoardId = board?.id;
          if (!tempBoardId) {
            // Use the actual profile ID from the user
            const homeownerId = user?.id || "550e8400-e29b-41d4-a716-446655440001"; // Demo homeowner profile ID
            console.log("Creating board for homeowner:", homeownerId);

            const { data: newBoard, error: boardError } = await supabase
              .from("inspiration_boards")
              .insert({
                user_id: homeownerId,
                title: "AI-Assisted Inspiration Board",
                description: "Created automatically for Iris AI analysis",
                room_type: "kitchen",
                status: "collecting",
              })
              .select()
              .single();

            if (boardError) {
              console.error("Board creation error:", boardError);
              toast.error("Could not create inspiration board");
            } else if (newBoard) {
              tempBoardId = newBoard.id;
              setTempBoardId(tempBoardId);
              console.log("Created board:", tempBoardId);
              toast.success("Created new inspiration board for your images");
            }
          }

          // Upload to Supabase storage
          const { data: uploadData, error: uploadError } = await supabase.storage
            .from("inspiration")
            .upload(fileName, file, {
              cacheControl: "3600",
              upsert: false,
            });

          if (uploadError) {
            console.error("Upload error:", uploadError);
            throw new Error(`Failed to upload ${file.name}`);
          }

          // Get public URL
          const {
            data: { publicUrl },
          } = supabase.storage.from("inspiration").getPublicUrl(fileName);

          // Create database record if we have a board
          let imageRecord = null;
          if (tempBoardId) {
            // Use the actual profile ID from the user for image records
            const homeownerId = user?.id || "550e8400-e29b-41d4-a716-446655440001"; // Demo homeowner profile ID
            console.log("Creating image record:", {
              tempBoardId,
              homeownerId,
              category: imageCategory,
            });

            const { data: dbData, error: dbError } = await supabase
              .from("inspiration_images")
              .insert({
                board_id: tempBoardId,
                user_id: homeownerId,
                image_url: publicUrl,
                source: "upload",
                category: imageCategory, // Include the selected category
                tags: [], // Will be populated by AI analysis later
                ai_analysis: {
                  filename: file.name,
                  file_size: file.size,
                  mime_type: file.type,
                  upload_timestamp: new Date().toISOString(),
                  category: imageCategory,
                },
              })
              .select()
              .single();

            if (dbError) {
              console.error("Database error:", dbError);
              toast.error(`Failed to save ${imageCategory} image to database`);
            } else {
              imageRecord = dbData;
              console.log("Successfully created image record:", imageRecord.id);
              toast.success(
                `${imageCategory === "ideal" ? "Ideal inspiration" : "Current space"} image saved to board`
              );

              // Save image IDs for generation
              if (imageCategory === "ideal") {
                setIdealImageId(imageRecord.id);
              } else {
                setCurrentImageId(imageRecord.id);
              }
              
              // If "Current Space" and "Save to My Property" is checked, also save to property system
              if (imageCategory === "current" && saveToProperty) {
                try {
                  // First, check if user has a property, or create a default one
                  const { data: properties } = await supabase
                    .from("properties")
                    .select("id")
                    .eq("user_id", homeownerId)
                    .limit(1);
                  
                  let propertyId = properties?.[0]?.id;
                  
                  if (!propertyId) {
                    // Create a default property for the user
                    const { data: newProperty } = await supabase
                      .from("properties")
                      .insert({
                        user_id: homeownerId,
                        name: "My Home",
                        property_type: "single_family",
                        metadata: {}
                      })
                      .select()
                      .single();
                    
                    propertyId = newProperty?.id;
                  }
                  
                  if (propertyId) {
                    // Save to property_photos table
                    await supabase
                      .from("property_photos")
                      .insert({
                        property_id: propertyId,
                        photo_url: publicUrl,
                        original_filename: file.name,
                        photo_type: "documentation",
                        ai_description: `Current space photo from ${board?.room_type || "room"}`,
                        ai_classification: {
                          source: "iris_chat",
                          category: imageCategory,
                          board_id: tempBoardId
                        }
                      });
                    
                    toast.success("Also saved to My Property for documentation");
                  }
                } catch (propertyError) {
                  console.error("Error saving to property system:", propertyError);
                  // Don't fail the whole upload, just log the error
                }
              }
            }
          } else {
            console.error("No board ID available for image storage");
            toast.error("Could not save image - no inspiration board available");
          }

          return {
            url: publicUrl,
            filename: file.name,
            size: file.size,
            record: imageRecord,
          };
        })
      );

      // Add user message about the uploaded images
      const categoryDisplay = imageCategory === "ideal" ? "Ideal Inspiration" : "Current Space";
      const userMessage: Message = {
        id: Date.now().toString(),
        role: "user",
        content: `I've uploaded ${uploadedImages.length} ${categoryDisplay.toLowerCase()} image${uploadedImages.length > 1 ? "s" : ""}: ${uploadedImages.map((img) => img.filename).join(", ")}`,
        timestamp: new Date(),
        uploadedImages: uploadedImages.map(img => ({
          id: img.record?.id || '',
          image_url: img.url,
          thumbnail_url: img.url,
          ai_analysis: img.record?.ai_analysis,
          tags: img.record?.tags || [],
          category: imageCategory,
        })),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Call REAL Claude API for intelligent image analysis
      let aiResponse: Message;

      try {
        const analysisPrompt =
          imageCategory === "ideal"
            ? `You are Iris, an expert interior design assistant. The user just uploaded ${uploadedImages.length} IDEAL INSPIRATION image${uploadedImages.length > 1 ? "s" : ""} (${uploadedImages.map((img) => img.filename).join(", ")}) for their ${board?.room_type || "renovation"} project.

Your task: Analyze what design elements, materials, colors, and styles they're drawn to. Ask "What aspects of these images do you find most appealing?" and help them identify their preferences.

Focus on:
- Color palettes and materials they like
- Specific design elements (cabinets, countertops, lighting, etc.)
- Overall style and atmosphere
- Features they want to incorporate

Generate relevant tags like: ["modern-farmhouse", "white-cabinets", "black-hardware", "marble-countertops", "pendant-lighting"]

Be conversational and helpful - you're helping them define their dream space.`
            : `You are Iris, an expert interior design assistant. The user just uploaded ${uploadedImages.length} CURRENT SPACE image${uploadedImages.length > 1 ? "s" : ""} (${uploadedImages.map((img) => img.filename).join(", ")}) showing their existing ${board?.room_type || "room"}.

Your task: Analyze what needs improvement, upgrading, or changing. Identify specific problems and opportunities for enhancement.

Focus on:
- Elements that need updating or replacement
- Layout issues or space optimization opportunities  
- Outdated features that could be modernized
- Potential improvements for functionality and aesthetics

Generate relevant tags like: ["needs-updating", "old-countertops", "dated-cabinets", "poor-lighting", "storage-issues"]

Be encouraging - help them see the potential in their space while identifying specific areas for improvement.`;

        const response = await fetch("/api/iris/analyze-image", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            image_urls: uploadedImages.map((img) => img.url),
            category: imageCategory,
            filenames: uploadedImages.map((img) => img.filename),
            analysis_prompt: analysisPrompt,
            board_info: {
              id: tempBoardId,
              room_type: board?.room_type || "kitchen",
            },
          }),
        });

        if (response.ok) {
          const claudeData = await response.json();
          const content = claudeData.content[0].text;

          // Generate smart tags based on category
          const smartTags =
            imageCategory === "ideal"
              ? ["inspiration", "design-goals", "style-preference", "dream-elements"]
              : ["current-state", "needs-improvement", "upgrade-potential", "existing-space"];

          // Update database records with AI-generated tags and structured analysis
          for (const uploadedImage of uploadedImages) {
            if (uploadedImage.record) {
              // Create structured analysis for AIAnalysisDisplay component
              const structuredAnalysis = {
                ...uploadedImage.record.ai_analysis,
                description: content,
                generated_tags: smartTags,
                design_elements: imageCategory === "ideal" 
                  ? ["lighting", "materials", "color scheme", "layout"]
                  : ["existing fixtures", "current layout", "space utilization"],
                color_palette: [], // Could be enhanced with color extraction
                suggestions: imageCategory === "current"
                  ? ["Update fixtures", "Modernize finishes", "Improve lighting", "Optimize storage"]
                  : [],
                analysis_timestamp: new Date().toISOString(),
              };

              await supabase
                .from("inspiration_images")
                .update({
                  tags: smartTags,
                  ai_analysis: structuredAnalysis,
                })
                .eq("id", uploadedImage.record.id);
            }
          }

          aiResponse = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: content,
            timestamp: new Date(),
            suggestions:
              imageCategory === "ideal"
                ? [
                    "Tell me what you love about this style",
                    "Show me similar designs",
                    "What elements appeal to you?",
                    "Help me find more like this",
                  ]
                : [
                    "What bothers you most about this space?",
                    "What would you change first?",
                    "Show me improvement ideas",
                    "Help me plan upgrades",
                  ],
          };
        } else {
          throw new Error("Claude API call failed");
        }
      } catch (error) {
        console.error("Claude API error:", error);

        // Fallback with differentiated responses
        const fallbackContent =
          imageCategory === "ideal"
            ? `I can see you've uploaded ${uploadedImages.length} inspiration image${uploadedImages.length > 1 ? "s" : ""}! These show great taste for your ${board?.room_type || "project"}. **Auto-Generated Tags**: ${imageCategory === "ideal" ? "inspiring, stylish, design-goals, dream-elements" : "current-state, needs-improvement, upgrade-potential"}

What aspects of these images do you find most appealing? For example:
- The color palette and how it makes you feel?
- Specific materials like countertops, cabinets, or flooring?
- The overall style and atmosphere?
- Particular design elements or features?

Understanding what draws you to these images will help me provide more personalized recommendations.`
            : `I can see you've uploaded ${uploadedImages.length} current space image${uploadedImages.length > 1 ? "s" : ""}! Let me help you identify improvement opportunities. **Auto-Generated Tags**: current-state, needs-improvement, upgrade-potential, existing-space

What aspects of your current space would you most like to change? For example:
- Are there elements that feel outdated or worn?
- Is the layout working well for your needs?
- Are there specific features you'd like to upgrade?
- What's the biggest frustration with this space?

Understanding your current challenges will help me suggest the best improvements.`;

        aiResponse = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: fallbackContent,
          timestamp: new Date(),
          suggestions:
            imageCategory === "ideal"
              ? [
                  "Tell me what you love",
                  "Show similar styles",
                  "Identify key elements",
                  "Find more inspiration",
                ]
              : [
                  "What needs changing?",
                  "Biggest problems?",
                  "Improvement priorities",
                  "Upgrade suggestions",
                ],
        };
      }

      setMessages((prev) => [...prev, aiResponse]);
      toast.success(
        `${uploadedImages.length} image${uploadedImages.length > 1 ? "s" : ""} uploaded and analyzed!`
      );
    } catch (error) {
      console.error("Error uploading images:", error);

      // Fallback response for upload failure
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `I had trouble uploading those images, but I can still help you organize your design ideas. What style are you going for?`,
        timestamp: new Date(),
        suggestions: [
          "Describe the style you see",
          "Help me organize ideas",
          "What elements do you like?",
          "Create a mood board",
        ],
      };
      setMessages((prev) => [...prev, aiResponse]);
      toast.error("Image upload failed, but I can still help with your design!");
    } finally {
      setIsTyping(false);
      setUploadingImages([]);
      // Clear the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    // Handle regular suggestions
    setInput(suggestion);
  };

  // Handle Finding Inspiration Online
  const handleFindInspiration = async () => {
    setIsTyping(true);

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: "Find inspiration images for my project",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      // Call backend to find inspiration online
      const response = await fetch("/api/iris/find-inspiration", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          board_id: board?.id || tempBoardId,
          ideal_image_id: idealImageId,
          current_image_id: currentImageId,
          search_query: input || "modern kitchen renovation ideas",
          user_id: user?.id || "550e8400-e29b-41d4-a716-446655440001",
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to find inspiration");
      }

      const data = await response.json();

      // Map inspiration items to images with immutable array creation
      const mappedImages = data.inspiration_items?.map((item: any, index: number) => ({
        url: String(item.image_url),
        description: String(item.description),
        key: `${Date.now()}-${index}`
      })) || [];

      // Create message with immutable object creation
      const successMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response || `🔍 **I found some great inspiration for you!**

Based on your preferences, here are some design ideas that might inspire you. Take a look at the images below and let me know which ones resonate with you!`,
        timestamp: new Date(),
        suggestions: [
          "Find more like this",
          "Show different styles", 
          "What makes these work?",
          "Help me narrow down my preferences",
        ],
        // Create new array reference for React state updates
        images: mappedImages.length > 0 ? [...mappedImages] : undefined
      };
      
      setMessages((prev) => [...prev, successMessage]);

      toast.success("Found inspiration for your project!");
    } catch (error) {
      console.error("Error finding inspiration:", error);

      // Fallback response
      const fallbackMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Let me help you explore design inspiration! Based on what you've shared, I can suggest:

• **Modern Farmhouse**: Clean lines with warm, rustic elements
• **Contemporary Minimalist**: Sleek surfaces and uncluttered spaces
• **Traditional Elegance**: Classic details with timeless appeal
• **Industrial Chic**: Raw materials and urban sophistication

Which style direction appeals to you most? I can find specific examples and help you identify the elements you love.`,
        timestamp: new Date(),
        suggestions: [
          "Show me modern farmhouse",
          "Explore minimalist designs",
          "Find traditional styles",
          "Mix different styles",
        ],
      };
      setMessages((prev) => [...prev, fallbackMessage]);
    } finally {
      setIsTyping(false);
    }
  };


  // Removed regeneration functionality - focusing on finding inspiration instead

  // Handle Vision Summary Creation
  const _handleVisionComposition = async () => {
    setIsTyping(true);

    try {
      // Create user message for vision summary request
      const userMessage: Message = {
        id: Date.now().toString(),
        role: "user",
        content: "Create a vision summary from my uploaded images",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Call backend to create vision summary
      const response = await fetch("/api/iris/create-vision-summary", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          board_id: board?.id || tempBoardId,
          ideal_image_id: idealImageId,
          current_image_id: currentImageId,
          user_id: user?.id || "550e8400-e29b-41d4-a716-446655440001",
        }),
      });

      const data = response.ok ? await response.json() : null;

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data?.summary || `📋 **Your Project Vision Summary**

Based on your uploaded images, here's what I understand about your project:

**Current Space Analysis:**
• Existing layout appears functional but dated
• Natural light is a strong asset to preserve
• Storage could be optimized better
• Overall structure is solid for renovation

**Your Design Preferences (from inspiration images):**
• Clean, modern aesthetic with traditional touches
• Light color palette - whites and soft grays
• Natural materials like wood and stone
• Minimalist hardware and fixtures
• Open, airy feeling with good lighting

**Recommended Transformation Path:**
1. Update cabinetry to match your preferred style
2. Replace countertops with materials from your inspiration
3. Modernize fixtures and hardware
4. Enhance lighting to maximize brightness
5. Optimize storage solutions

This vision summary will help contractors understand exactly what you're looking for!`,
        timestamp: new Date(),
        suggestions: [
          "Share with contractors",
          "Add more details",
          "Estimate project cost",
          "Find similar projects",
        ],
      };

      setMessages((prev) => [...prev, aiResponse]);
      toast.success("Vision summary created!");
    } catch (error) {
      console.error("Error creating vision summary:", error);
      toast.error("Could not create summary. Please try again.");
    } finally {
      setIsTyping(false);
    }
  };

  const generateIrisResponse = (
    userInput: string,
    _currentBoard?: InspirationBoard | null
  ): string => {
    const input = userInput.toLowerCase();

    if (input.includes("organize")) {
      return "I'd be happy to help organize your images! I can see you have a mix of styles here. Would you like me to group them by room type, color scheme, or design style?";
    } else if (input.includes("style")) {
      return "Based on your saved images, I'm seeing a modern farmhouse aesthetic with clean lines, neutral colors, and natural textures. The white shaker cabinets paired with black hardware create a classic contrast. Would you like me to find more images in this style?";
    } else if (input.includes("budget")) {
      return "Based on similar projects in your area, I estimate this could range from $15,000-$25,000 for a full renovation. The main cost drivers would be cabinetry (40%), countertops (20%), and appliances (25%). Would you like a more detailed breakdown?";
    } else if (input.includes("vision")) {
      return "Let me create a vision summary for you. From your inspiration images, I see you're drawn to: bright, open spaces with white cabinetry, marble-look countertops, and modern black fixtures. The overall feeling is clean and timeless. Shall I help you refine this into a project brief?";
    } else {
      return "I understand you're interested in that! Let me help you explore this idea further. What specific aspect would you like to focus on?";
    }
  };

  const generateSuggestions = (
    userInput: string,
    _currentBoard?: InspirationBoard | null
  ): string[] => {
    if (userInput.toLowerCase().includes("organize")) {
      return [
        "Group by room type",
        "Sort by color scheme",
        "Identify common elements",
        "Remove duplicates",
      ];
    } else if (userInput.toLowerCase().includes("budget")) {
      return [
        "Show detailed breakdown",
        "Find budget-friendly alternatives",
        "Priority recommendations",
        "DIY vs professional costs",
      ];
    }
    return [
      "Tell me more",
      "Show similar examples",
      "What are my options?",
      "Ready to create project",
    ];
  };

  return (
    <div className="fixed bottom-4 right-4 w-96 h-[600px] bg-white rounded-lg shadow-2xl flex flex-col z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Iris</h3>
            <p className="text-xs text-gray-500">Design Assistant</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === "user" ? "bg-primary-600 text-white" : "bg-gray-100 text-gray-900"
              }`}
            >
              <p className="text-sm">{message.content}</p>

              {/* Inspiration Images */}
              {message.images && message.images.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs text-gray-600 mb-2">🎨 {message.images.length} inspiration image{message.images.length > 1 ? 's' : ''} found</p>
                  <div className="grid grid-cols-2 gap-3">
                    {message.images.map((image, idx) => (
                      <div key={idx} className="space-y-2">
                        <img
                          src={image.url}
                          alt={image.description}
                          className="w-full h-32 object-cover rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.src = '/api/placeholder-image';
                          }}
                          onClick={() => {
                            // Future: Add to inspiration board or enlarge view
                            toast.success(`Added "${image.description}" to your inspiration!`);
                          }}
                        />
                        <p className="text-xs text-gray-600">{image.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Uploaded Images with AI Analysis */}
              {message.uploadedImages && message.uploadedImages.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs text-gray-600 mb-2">
                    📸 {message.uploadedImages.length} uploaded image{message.uploadedImages.length > 1 ? 's' : ''} 
                    ({message.uploadedImages[0]?.category === 'current' ? 'Current Space' : 'Inspiration'})
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    {message.uploadedImages.map((image, idx) => (
                      <div key={idx} className="relative group">
                        <img
                          src={image.thumbnail_url || image.image_url}
                          alt={`Uploaded ${image.category} image`}
                          className="w-full h-32 object-cover rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.src = '/api/placeholder-image';
                          }}
                        />
                        
                        {/* AI Analysis Overlay */}
                        {image.ai_analysis && (
                          <AIAnalysisDisplay
                            analysis={image.ai_analysis}
                            imageType={image.category === "current" ? "current" : "inspiration"}
                          />
                        )}

                        {/* Tags */}
                        {image.tags.length > 0 && (
                          <div className="absolute bottom-2 left-2 right-2">
                            <div className="flex flex-wrap gap-1">
                              {image.tags.slice(0, 2).map((tag, tagIdx) => (
                                <span
                                  key={tagIdx}
                                  className="text-xs bg-black bg-opacity-60 text-white px-2 py-0.5 rounded"
                                >
                                  {tag}
                                </span>
                              ))}
                              {image.tags.length > 2 && (
                                <span className="text-xs bg-black bg-opacity-60 text-white px-2 py-0.5 rounded">
                                  +{image.tags.length - 2}
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Suggestions */}
              {message.suggestions && message.suggestions.length > 0 && (
                <div className="mt-3 space-y-1">
                  {message.suggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="block w-full text-left text-xs px-2 py-1 rounded bg-white bg-opacity-20 hover:bg-opacity-30 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex gap-1">
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0ms" }}
                ></div>
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "150ms" }}
                ></div>
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "300ms" }}
                ></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <div className="px-4 py-2 border-t border-b bg-gray-50">
        {/* Photo Category Selection */}
        <div className="mb-2">
          <span className="text-xs text-gray-500 font-medium">Photo Category:</span>
          <div className="flex gap-2 mt-1">
            <button
              type="button"
              onClick={() => setImageCategory("ideal")}
              className={`text-xs px-2 py-1 rounded transition-colors ${
                imageCategory === "ideal"
                  ? "bg-blue-100 text-blue-700 border border-blue-300"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              ✨ Ideal Inspiration
            </button>
            <button
              type="button"
              onClick={() => setImageCategory("current")}
              className={`text-xs px-2 py-1 rounded transition-colors ${
                imageCategory === "current"
                  ? "bg-green-100 text-green-700 border border-green-300"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              📐 Current Space
            </button>
            
            {imageCategory === "current" && (
              <label className="flex items-center gap-1 text-xs text-gray-700 ml-2">
                <input
                  type="checkbox"
                  checked={saveToProperty}
                  onChange={(e) => setSaveToProperty(e.target.checked)}
                  className="rounded border-gray-300"
                />
                My Property
              </label>
            )}
          </div>
        </div>

        {/* Upload Actions */}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isTyping || uploadingImages.length > 0}
            className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-900 px-2 py-1 rounded hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Upload className="w-3 h-3" />
            {uploadingImages.length > 0
              ? "Uploading..."
              : `Upload ${imageCategory === "ideal" ? "Inspiration" : "Current Space"}`}
          </button>
          <button
            type="button"
            className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-900 px-2 py-1 rounded hover:bg-gray-200 transition-colors"
          >
            <Link2 className="w-3 h-3" />
            Add URL
          </button>
          <button
            type="button"
            className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-900 px-2 py-1 rounded hover:bg-gray-200 transition-colors"
          >
            <Camera className="w-3 h-3" />
            Take Photo
          </button>
        </div>

        {/* AI Inspiration Finder */}
        <div className="mt-3 pt-2 border-t border-gray-200">
          <span className="text-xs text-gray-500 font-medium">Find Inspiration Online:</span>
          <div className="flex gap-2 mt-1">
            <button
              type="button"
              onClick={() => handleFindInspiration()}
              disabled={isTyping}
              className="flex items-center gap-1 text-xs text-purple-600 hover:text-purple-800 px-2 py-1 rounded hover:bg-purple-50 transition-colors border border-purple-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Sparkles className="w-3 h-3" />
              Find Inspiration
            </button>
            <span className="text-xs text-gray-400 flex items-center">
              I'll search for design ideas matching your style
            </span>
          </div>
        </div>

        {/* Image Organization Helper */}
        <div className="mt-3 pt-2 border-t border-gray-200">
          <span className="text-xs text-gray-500 font-medium">Organize Your Vision:</span>
          <div className="flex gap-2 mt-1">
            <button
              type="button"
              onClick={() => _handleVisionComposition()}
              disabled={isTyping}
              className={`flex items-center gap-1 text-xs px-2 py-1 rounded transition-colors border ${
                idealImageId && currentImageId
                  ? "text-green-600 hover:text-green-800 hover:bg-green-50 border-green-200"
                  : "text-gray-400 border-gray-200 cursor-not-allowed"
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              title={
                !idealImageId || !currentImageId
                  ? "Upload both ideal and current images first"
                  : "Create vision summary"
              }
            >
              <Image className="w-3 h-3" />
              Create Vision Summary
            </button>
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {idealImageId && currentImageId
              ? "✅ Ready to organize your project vision!"
              : `Upload: ${!idealImageId ? "📸 Ideal images" : ""} ${!idealImageId && !currentImageId ? "&" : ""} ${!currentImageId ? "📐 Current photos" : ""}`}
          </div>
        </div>


        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {/* Input */}
      <div className="p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask Iris anything..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!input.trim()}
            className="p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default IrisChat;
