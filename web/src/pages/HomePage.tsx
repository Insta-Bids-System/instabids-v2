import { motion } from "framer-motion";
import { Clock, Shield, Star, Users } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import UltimateCIAChat from "@/components/chat/UltimateCIAChat";
import GlassmorphismChatDemo from "@/components/testing/GlassmorphismChatDemo";
import UITestingShowcase from "@/components/testing/UITestingShowcase";
import { useAuth } from "@/contexts/AuthContext";
import { apiService } from "@/services/api";

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [showSignupPrompt, setShowSignupPrompt] = useState(false);
  const [_conversationComplete, setConversationComplete] = useState(false);
  const [_projectData, setProjectData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'ui-testing'>('chat');
  const [sessionId] = useState(() => {
    // Try to get existing session ID from localStorage, or create new one
    const existingSessionId = localStorage.getItem("cia_session_id");
    if (existingSessionId) {
      return existingSessionId;
    }
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem("cia_session_id", newSessionId);
    return newSessionId;
  });

  const handleSendMessage = async (message: string, images: string[]) => {
    try {
      // Check if this is a contractor trying to use the landing page
      const isContractorMessage = /\b(contractor|contracting|hvac|plumbing|electrical|painting|roofing|construction|carpentry|flooring|landscaping|pool|solar)\b/i.test(message) ||
        /\b(company|business|years? (?:in business|experience)|license|insurance|contractor account|create account|sign up|signup)\b/i.test(message) ||
        /\b(i'm .+ from|we're|my company|my business)\b/i.test(message);
      
      let result;
      if (isContractorMessage) {
        console.log("🔧 Detected contractor message, using COIA landing page API");
        // Use COIA landing page API for contractors
        result = await apiService.sendContractorLandingMessage(
          message, 
          sessionId, 
          sessionId, // Use sessionId as contractor_lead_id for consistency
          { interface: "landing_page" }
        );
      } else {
        console.log("🏠 Using CIA homeowner API");
        // Use authenticated user ID if available, otherwise undefined for anonymous
        const userId = user?.id;
        result = await apiService.sendChatMessage(message, images, userId, sessionId);
      }

      if (result.success && result.data) {
        // Handle contractor responses (signup links)
        if (result.data.signup_link_generated || result.data.signup_data) {
          console.log("✅ Contractor signup link generated:", result.data);
          // Could show special contractor signup UI here
        }
        
        // Check if homeowner conversation has reached a completion phase
        if (result.data.phase === "review" || result.data.phase === "complete") {
          setConversationComplete(true);
          setProjectData(result.data.extractedData);
          // Show signup prompt after a delay
          setTimeout(() => setShowSignupPrompt(true), 2000);
        }

        return result.data.response;
      } else {
        throw new Error(result.error || "Failed to send message");
      }
    } catch (error) {
      console.error("[HomePage] Error sending message:", error);
      throw error;
    }
  };

  const handleAccountCreated = (userData: { name: string; email: string; userId: string }) => {
    console.log("Account created:", userData);
    // Redirect to dashboard or show success message
    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm fixed top-0 w-full z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Instabids
            </h1>
            <nav className="flex gap-6">
              <div className="flex items-center gap-4">
                <button
                  type="button"
                  onClick={() => navigate("/intelligent-messaging-test")}
                  className="text-red-600 hover:text-red-800 font-bold transition-colors border-2 border-red-600 px-3 py-1 rounded"
                >
                  🛡️ Messaging Agent
                </button>
                <span className="text-sm text-gray-500 ml-4">Login as:</span>
                <button
                  type="button"
                  onClick={() => navigate("/login")}
                  className="text-blue-600 hover:text-blue-800 font-medium transition-colors"
                >
                  Homeowner
                </button>
                <button
                  type="button"
                  onClick={() => navigate("/contractor")}
                  className="text-green-600 hover:text-green-800 font-medium transition-colors"
                >
                  Contractor
                </button>
                <button
                  type="button"
                  onClick={() => navigate("/admin/login")}
                  className="text-purple-600 hover:text-purple-800 font-medium transition-colors"
                >
                  Admin
                </button>
              </div>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section with Chat */}
      <section className="pt-24 pb-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Tab Navigation */}
          <div className="flex justify-center mb-6">
            <div className="bg-white rounded-lg shadow-sm p-1 flex gap-2">
              <button
                onClick={() => setActiveTab('chat')}
                className={`px-6 py-2 rounded-md font-medium transition-all ${
                  activeTab === 'chat'
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                💬 Chat Interface
              </button>
              <button
                onClick={() => setActiveTab('ui-testing')}
                className={`px-6 py-2 rounded-md font-medium transition-all ${
                  activeTab === 'ui-testing'
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                🧪 UI Testing Lab
              </button>
            </div>
          </div>

          {/* Conditional Content Based on Tab */}
          {activeTab === 'chat' ? (
            <>
              {/* Hero Text for Chat Tab */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="text-center mb-8"
              >
                <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
                  ⚡ SECOND HOT RELOAD TEST - WATCH MODE WORKING! ⚡
                </h2>
                <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                  No sales meetings. No hassle. Just chat with our AI to describe your project and get
                  matched with pre-qualified contractors instantly.
                </p>
              </motion.div>
            </>
          ) : (
            <>
              {/* Hero Text for UI Testing Tab */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="text-center mb-8"
              >
                <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-amber-600 to-pink-600 bg-clip-text text-transparent">
                  UI Testing Laboratory
                </h2>
                <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                  Explore different design concepts and interface styles for the InstaBids platform.
                </p>
              </motion.div>
            </>
          )}

          {/* Conditional Content Based on Active Tab */}
          {activeTab === 'chat' ? (
            <>
              {/* Trust Indicators */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3, duration: 0.5 }}
                className="flex flex-wrap justify-center gap-6 mb-8"
          >
            <div className="flex items-center gap-2 text-gray-600">
              <Shield className="w-5 h-5 text-green-600" />
              <span className="text-sm">Verified Contractors</span>
            </div>
            <div className="flex items-center gap-2 text-gray-600">
              <Star className="w-5 h-5 text-yellow-500" />
              <span className="text-sm">4.8/5 Average Rating</span>
            </div>
            <div className="flex items-center gap-2 text-gray-600">
              <Clock className="w-5 h-5 text-blue-600" />
              <span className="text-sm">24hr Response Time</span>
            </div>
            <div className="flex items-center gap-2 text-gray-600">
              <Users className="w-5 h-5 text-purple-600" />
              <span className="text-sm">10,000+ Projects</span>
            </div>
          </motion.div>

              {/* Chat Interface */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.5, duration: 0.5 }}
                className="max-w-4xl mx-auto"
              >
                <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
                  <UltimateCIAChat
                    onSendMessage={handleSendMessage}
                    onAccountCreated={handleAccountCreated}
                    sessionId={sessionId}
                  />
                </div>
              </motion.div>
            </>
          ) : (
            <>
              {/* UI Testing Lab Content - Comprehensive Component Showcase */}
              <UITestingShowcase />
            </>
          )}

          {/* Signup Prompt Modal */}
          {showSignupPrompt && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
              onClick={() => setShowSignupPrompt(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.1 }}
                className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl"
                onClick={(e) => e.stopPropagation()}
              >
                <h3 className="text-2xl font-bold mb-4">Great! Your Project is Ready</h3>
                <p className="text-gray-600 mb-6">
                  Sign up now to receive bids from verified contractors. It only takes 30 seconds!
                </p>
                <button
                  type="button"
                  onClick={() => navigate("/signup")}
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-lg font-semibold hover:shadow-lg transition-all duration-200 mb-3"
                >
                  Sign Up with Google
                </button>
                <button
                  type="button"
                  onClick={() => setShowSignupPrompt(false)}
                  className="w-full text-gray-500 py-2 hover:text-gray-700 transition-colors"
                >
                  Continue chatting
                </button>
              </motion.div>
            </motion.div>
          )}
        </div>
      </section>

      {/* Social Proof */}
      <section className="py-12 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="grid md:grid-cols-3 gap-8"
          >
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="flex mb-2">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-current text-yellow-400" />
                ))}
              </div>
              <p className="text-gray-600 mb-2">
                "Saved $3,000 on my kitchen remodel. The AI understood exactly what I wanted!"
              </p>
              <p className="text-sm font-semibold">- Sarah M., Los Angeles</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="flex mb-2">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-current text-yellow-400" />
                ))}
              </div>
              <p className="text-gray-600 mb-2">
                "No pushy sales calls! Got 5 bids in 24 hours for my bathroom renovation."
              </p>
              <p className="text-sm font-semibold">- Mike T., Chicago</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="flex mb-2">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-current text-yellow-400" />
                ))}
              </div>
              <p className="text-gray-600 mb-2">
                "The chat was so easy! Like texting a friend who knows everything about home
                projects."
              </p>
              <p className="text-sm font-semibold">- Emily R., New York</p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 text-center text-gray-500 text-sm">
        <p>© 2025 Instabids. All rights reserved. | Privacy | Terms</p>
      </footer>
    </div>
  );
};

export default HomePage;
