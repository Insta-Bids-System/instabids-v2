import React, { useState, useEffect, useRef } from 'react';
import { 
  MessageSquare, 
  Sparkles, 
  Send, 
  Minimize2, 
  Maximize2, 
  X,
  Settings,
  Image as ImageIcon,
  Home,
  Wrench,
  Lightbulb,
  Zap,
  Upload,
  Camera
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useIris } from '@/contexts/IrisContext';

interface FloatingIrisChatProps {
  // Optional props to enable different context modes
  propertyId?: string;
  boardId?: string;
  initialContext?: 'inspiration' | 'property' | 'auto';
  onClose?: () => void;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  images?: Array<{
    url: string;
    analysis?: any;
    category?: 'current' | 'inspiration' | 'problem';
    room_type?: string;
    storage_location?: string;
  }>;
  reasoning?: {
    user_intent: string;
    confidence: number;
    suggested_actions: string[];
  };
  available_tools?: string[];
  context_summary?: {
    inspiration_boards: number;
    property_photos: number;
    trade_projects: number;
  };
  workflow_questions?: Array<{
    question: string;
    options: string[];
    callback: string;
  }>;
}

interface IrisSession {
  session_id: string;
  messages: Message[];
  context_type: 'inspiration' | 'property' | 'auto';
  last_updated: Date;
}

const FloatingIrisChat: React.FC<FloatingIrisChatProps> = ({
  propertyId,
  boardId,
  initialContext = 'auto',
  onClose
}) => {
  const { user } = useAuth();
  const { isIrisOpen, setIsIrisOpen, sessionData } = useIris();
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [session, setSession] = useState<IrisSession | null>(null);
  const [contextMode, setContextMode] = useState<'inspiration' | 'property' | 'auto'>(initialContext);
  const [uploadingImages, setUploadingImages] = useState<File[]>([]);
  const [pendingImageResponse, setPendingImageResponse] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initialize session on first open
  useEffect(() => {
    if (isIrisOpen && !session && user) {
      initializeSession();
    }
  }, [isIrisOpen, user]);

  // Reinitialize session when project context changes (from Discuss button)
  useEffect(() => {
    if (isIrisOpen && sessionData?.project_context && user) {
      initializeSession();
    }
  }, [sessionData?.project_context, isIrisOpen, user]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Persist session to localStorage
  useEffect(() => {
    if (session && user) {
      localStorage.setItem(`iris_session_${user.id}`, JSON.stringify(session));
    }
  }, [session, user]);

  // Load session from localStorage
  useEffect(() => {
    if (user && isIrisOpen) {
      const savedSession = localStorage.getItem(`iris_session_${user.id}`);
      if (savedSession) {
        try {
          const parsed = JSON.parse(savedSession);
          setSession({
            ...parsed,
            last_updated: new Date(parsed.last_updated)
          });
          setMessages(parsed.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          })));
        } catch (error) {
          console.error('Error loading IRIS session:', error);
          initializeSession();
        }
      } else {
        initializeSession();
      }
    }
  }, [user, isIrisOpen]);

  const initializeSession = () => {
    if (!user) return;
    
    const newSession: IrisSession = {
      session_id: `iris_unified_${user.id}_${Date.now()}`,
      messages: [],
      context_type: contextMode,
      last_updated: new Date()
    };

    // Check if we have project context from the "Discuss" button
    const projectContext = sessionData?.project_context;
    let welcomeContent = `Hi! I'm IRIS, your intelligent design and project assistant.`;
    
    if (projectContext) {
      // We have specific project context from the Discuss button
      welcomeContent = `Hi! I'm ready to discuss your **${projectContext.project_title}**.

**Project Details:**
• Trade Type: ${projectContext.trade_type}
• Urgency: ${projectContext.urgency_level}
• Complexity: ${projectContext.complexity}
• Repair Items: ${projectContext.total_items}

**Repairs Include:**
${projectContext.repair_items.map(item => `• ${item.description} (${item.severity} severity)`).join('\n')}

I can help you with:
- Organizing these repairs for contractor outreach
- Creating bid cards for quotes
- Analyzing photos for additional issues
- Coordinating with other property projects

What would you like to focus on first?`;
    } else if (propertyId) {
      welcomeContent += ` 🏠 I see you're working on a property - I can help organize maintenance issues by trade.

What would you like to work on today?`;
    } else if (boardId) {
      welcomeContent += ` 🎨 I see you're working on an inspiration board - I can help analyze your design preferences.

What would you like to work on today?`;
    } else {
      welcomeContent += ` I can help you with both inspiration projects and property maintenance.

What would you like to work on today?`;
    }

    const welcomeMessage: Message = {
      id: 'welcome',
      role: 'assistant',
      content: welcomeContent,
      timestamp: new Date()
    };

    newSession.messages = [welcomeMessage];
    setSession(newSession);
    setMessages([welcomeMessage]);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!input.trim() || !user || !session) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const requestBody = {
        message: userMessage.content,
        user_id: user.id,
        session_id: session.session_id,
        context_type: contextMode,
        property_id: propertyId,
        board_id: boardId,
        // Include project context if available from Discuss button
        project_context: sessionData?.project_context
      };

      const response = await fetch('/api/iris/unified-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const data = await response.json();
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
          reasoning: data.reasoning,
          available_tools: data.available_tools,
          context_summary: data.context_summary
        };

        setMessages(prev => [...prev, assistantMessage]);
        
        // Update session
        const updatedSession = {
          ...session,
          messages: [...session.messages, userMessage, assistantMessage],
          last_updated: new Date()
        };
        setSession(updatedSession);

      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('IRIS chat error:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I apologize, but I\'m having trouble connecting right now. Please try again in a moment.',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearSession = () => {
    if (user) {
      localStorage.removeItem(`iris_session_${user.id}`);
      initializeSession();
    }
  };

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0 || !user || !session) return;

    const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
    if (imageFiles.length === 0) {
      return;
    }

    setUploadingImages(imageFiles);
    setIsTyping(true);

    try {
      // Convert images to base64 for analysis
      const imageData = await Promise.all(
        imageFiles.map(async (file) => {
          return new Promise<{file: File, base64: string}>((resolve) => {
            const reader = new FileReader();
            reader.onload = () => {
              const base64 = reader.result as string;
              resolve({ file, base64 });
            };
            reader.readAsDataURL(file);
          });
        })
      );

      // Create user message with uploaded images
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: `I've uploaded ${imageFiles.length} image${imageFiles.length > 1 ? 's' : ''}`,
        timestamp: new Date(),
        images: imageData.map(({file, base64}) => ({
          url: base64,
          category: 'current' as const
        }))
      };

      setMessages(prev => [...prev, userMessage]);

      // Send to IRIS with image data for automatic workflow
      const requestBody = {
        message: `I'm uploading ${imageFiles.length} image${imageFiles.length > 1 ? 's' : ''}. Please analyze and ask me where to put ${imageFiles.length > 1 ? 'them' : 'it'}.`,
        user_id: user.id,
        session_id: session.session_id,
        context_type: contextMode,
        property_id: propertyId,
        board_id: boardId,
        images: imageData.map(({file, base64}) => ({
          data: base64,
          filename: file.name,
          size: file.size,
          type: file.type
        })),
        project_context: sessionData?.project_context,
        trigger_image_workflow: true // This tells IRIS to start the automatic workflow
      };

      const response = await fetch('/api/iris/unified-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const data = await response.json();
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
          reasoning: data.reasoning,
          available_tools: data.available_tools,
          context_summary: data.context_summary,
          workflow_questions: data.workflow_questions // For room/board selection
        };

        setMessages(prev => [...prev, assistantMessage]);
        
        // Update session
        const updatedSession = {
          ...session,
          messages: [...session.messages, userMessage, assistantMessage],
          last_updated: new Date()
        };
        setSession(updatedSession);

      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('Image upload error:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I had trouble analyzing your image. Please try uploading again.',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
      setUploadingImages([]);
      // Clear the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleWorkflowResponse = async (questionIndex: number, selectedOption: string) => {
    if (!user || !session) return;

    setIsTyping(true);

    try {
      // Get the most recent message with images to include them in the workflow response
      const recentMessageWithImages = messages.slice().reverse().find(msg => msg.images && msg.images.length > 0);
      const imagesToProcess = recentMessageWithImages?.images?.map(img => ({
        data: img.url,
        filename: `image_${Date.now()}.jpg`,
        size: 1000,
        type: 'image/jpeg'
      }));

      const requestBody = {
        message: `For question ${questionIndex + 1}, I choose: ${selectedOption}`,
        user_id: user.id,
        session_id: session.session_id,
        context_type: contextMode,
        property_id: propertyId,
        board_id: boardId,
        workflow_response: {
          question_index: questionIndex,
          selected_option: selectedOption
        },
        images: imagesToProcess || [], // Include the images with the workflow response
        project_context: sessionData?.project_context
      };

      const response = await fetch('/api/iris/unified-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const data = await response.json();
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
          reasoning: data.reasoning,
          available_tools: data.available_tools,
          context_summary: data.context_summary
        };

        setMessages(prev => [...prev, assistantMessage]);
        
        // Update session
        const updatedSession = {
          ...session,
          messages: [...session.messages, assistantMessage],
          last_updated: new Date()
        };
        setSession(updatedSession);

      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('Workflow response error:', error);
    } finally {
      setIsTyping(false);
    }
  };

  // Floating chat bubble when minimized
  if (!isIrisOpen) {
    return (
      <div 
        className="fixed bottom-6 right-6 z-50 cursor-pointer group"
        onClick={() => setIsIrisOpen(true)}
      >
        <div className="relative">
          {/* Main chat bubble with modern design */}
          <div className="w-16 h-16 bg-gradient-to-br from-purple-500 via-purple-600 to-pink-600 rounded-full flex items-center justify-center shadow-lg hover:shadow-2xl transition-all duration-300 group-hover:scale-110 group-hover:rotate-3">
            <Sparkles className="w-8 h-8 text-white group-hover:animate-pulse" />
          </div>
          
          {/* Animated ring effect */}
          <div className="absolute inset-0 w-16 h-16 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 opacity-20 animate-ping"></div>
          
          {/* Context indicator */}
          {(propertyId || boardId) && (
            <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full flex items-center justify-center shadow-md animate-bounce">
              {propertyId ? <Home className="w-4 h-4 text-white" /> : <ImageIcon className="w-4 h-4 text-white" />}
            </div>
          )}
          
          {/* Floating tooltip */}
          <div className="absolute bottom-full right-0 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap">
            <div className="flex items-center gap-2">
              <Lightbulb className="w-4 h-4" />
              <span>Ask IRIS anything!</span>
            </div>
            <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
          </div>
        </div>
      </div>
    );
  }

  // Full chat interface when open
  return (
    <div className={`fixed right-6 z-50 bg-white rounded-2xl shadow-2xl border border-gray-200 transition-all duration-500 ease-in-out ${
      isMinimized ? 'bottom-6 w-80 h-16' : 'bottom-6 w-96 h-[600px]'
    } backdrop-blur-sm bg-white/95`}>
      
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-100 bg-gradient-to-r from-purple-50 via-indigo-50 to-pink-50 rounded-t-2xl backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">IRIS Assistant</h3>
            <div className="flex items-center gap-2 text-xs text-gray-600">
              {contextMode === 'auto' && <span>Smart Context</span>}
              {contextMode === 'inspiration' && (
                <>
                  <ImageIcon className="w-3 h-3" />
                  <span>Design Mode</span>
                </>
              )}
              {contextMode === 'property' && (
                <>
                  <Home className="w-3 h-3" />
                  <span>Property Mode</span>
                </>
              )}
              {session && (
                <>
                  <span>•</span>
                  <span>{messages.length - 1} messages</span>
                </>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Context mode switcher */}
          <select
            value={contextMode}
            onChange={(e) => setContextMode(e.target.value as any)}
            className="text-xs bg-white border border-gray-300 rounded px-2 py-1"
          >
            <option value="auto">Auto</option>
            <option value="inspiration">Design</option>
            <option value="property">Property</option>
          </select>
          
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 hover:bg-gray-100 rounded"
            title={isMinimized ? "Expand" : "Minimize"}
          >
            {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
          </button>
          
          <button
            onClick={clearSession}
            className="p-1 hover:bg-gray-100 rounded"
            title="Clear session"
          >
            <Settings className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => {
              setIsIrisOpen(false);
              onClose?.();
            }}
            className="p-1 hover:bg-gray-100 rounded"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Chat content - hidden when minimized */}
      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 h-[400px] space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[85%] rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}>
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Display images if present */}
                  {message.images && message.images.length > 0 && (
                    <div className="mt-2 grid grid-cols-2 gap-2">
                      {message.images.map((image, index) => (
                        <div key={index} className="relative">
                          <img
                            src={image.url}
                            alt={`Uploaded image ${index + 1}`}
                            className="w-full h-24 object-cover rounded-lg border"
                          />
                          {image.category && (
                            <div className="absolute top-1 left-1 px-2 py-1 bg-black bg-opacity-50 text-white text-xs rounded">
                              {image.category}
                            </div>
                          )}
                          {image.room_type && (
                            <div className="absolute bottom-1 left-1 px-2 py-1 bg-black bg-opacity-50 text-white text-xs rounded">
                              {image.room_type}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* Show IRIS insights for assistant messages */}
                  {message.role === 'assistant' && (message.reasoning || message.context_summary) && (
                    <div className="mt-2 pt-2 border-t border-gray-200 text-xs">
                      {message.reasoning && (
                        <div className="mb-1">
                          <span className="font-medium">Intent:</span> {message.reasoning.user_intent} 
                          <span className="ml-2 opacity-75">({Math.round(message.reasoning.confidence * 100)}%)</span>
                        </div>
                      )}
                      {message.context_summary && (
                        <div className="text-gray-600">
                          Context: {message.context_summary.inspiration_boards} boards, {' '}
                          {message.context_summary.property_photos} photos, {' '}
                          {message.context_summary.trade_projects} projects
                        </div>
                      )}
                      {message.available_tools && message.available_tools.length > 0 && (
                        <div className="text-gray-600">
                          Tools: {message.available_tools.slice(0, 3).join(', ')}
                          {message.available_tools.length > 3 && '...'}
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Show workflow questions for image classification */}
                  {message.role === 'assistant' && message.workflow_questions && message.workflow_questions.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {message.workflow_questions.map((question, questionIndex) => (
                        <div key={questionIndex} className="bg-white bg-opacity-20 rounded-lg p-3">
                          <p className="text-sm font-medium mb-2">{question.question}</p>
                          <div className="flex flex-wrap gap-2">
                            {question.options.map((option, optionIndex) => (
                              <button
                                key={optionIndex}
                                onClick={() => handleWorkflowResponse(questionIndex, option)}
                                className="px-3 py-1 bg-white text-gray-900 text-xs rounded-full hover:bg-gray-100 transition-colors"
                              >
                                {option}
                              </button>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask IRIS about your projects..."
                  className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-sm resize-none"
                  rows={1}
                  disabled={isTyping}
                />
                {/* Photo upload button */}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isTyping}
                  className="absolute right-2 top-2 p-1 text-gray-400 hover:text-purple-500 transition-colors disabled:opacity-50"
                  title="Upload photo"
                >
                  <Camera className="w-4 h-4" />
                </button>
              </div>
              <button
                onClick={handleSend}
                disabled={!input.trim() || isTyping}
                className="p-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handleImageUpload}
              className="hidden"
            />
            
            {/* Image upload indicator */}
            {uploadingImages.length > 0 && (
              <div className="mt-2 flex items-center gap-2 text-sm text-purple-600">
                <Upload className="w-4 h-4 animate-pulse" />
                <span>Uploading {uploadingImages.length} image{uploadingImages.length > 1 ? 's' : ''}...</span>
              </div>
            )}
            
            {/* Quick context indicators */}
            <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
              <div className="flex items-center gap-3">
                {propertyId && (
                  <div className="flex items-center gap-1">
                    <Home className="w-3 h-3" />
                    <span>Property context active</span>
                  </div>
                )}
                {boardId && (
                  <div className="flex items-center gap-1">
                    <ImageIcon className="w-3 h-3" />
                    <span>Board context active</span>
                  </div>
                )}
              </div>
              <span>Enter to send, Shift+Enter for new line</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default FloatingIrisChat;