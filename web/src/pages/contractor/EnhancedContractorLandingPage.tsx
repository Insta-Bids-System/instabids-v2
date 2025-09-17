import { motion } from "framer-motion";
import { Shield, Star, Target, TrendingUp, Zap, Search, MapPin, DollarSign } from "lucide-react";
import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import ContractorOnboardingChat from "@/components/chat/ContractorOnboardingChat";
import { BidCardMarketplace } from "@/components/bidcards/BidCardMarketplace";
import { useAuth } from "@/contexts/AuthContext";

interface MatchingProject {
  id: string;
  title: string;
  budget_range: { min: number; max: number };
  location: { city: string; state: string };
  project_type: string;
  categories: string[];
  timeline: { start_date: string };
  match_score: number;
  match_reasons: string[];
}

const EnhancedContractorLandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, profile } = useAuth();
  const [searchParams] = useSearchParams();
  const [showSignupPrompt, setShowSignupPrompt] = useState(false);
  const [_conversationComplete, setConversationComplete] = useState(false);
  const [contractorData, setContractorData] = useState<any>(null);
  const [preLoadedData, setPreLoadedData] = useState<any>(null);
  const [showMarketplace, setShowMarketplace] = useState(false);
  const [matchingProjects, setMatchingProjects] = useState<MatchingProject[]>([]);
  const [sessionId] = useState(
    `contractor_session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  );

  // Extract URL parameters from bid card email
  const contractorName = searchParams.get("contractor");
  const messageId = searchParams.get("msg_id");
  const campaignId = searchParams.get("campaign");
  const source = searchParams.get("source") || "direct";

  // If already logged in as contractor, redirect to dashboard
  React.useEffect(() => {
    if (user && profile && profile.role === "contractor") {
      navigate("/contractor/dashboard");
    }
  }, [user, profile, navigate]);

  // Load pre-discovered contractor data when contractor name is present
  useEffect(() => {
    const loadContractorData = async () => {
      if (contractorName) {
        try {
          console.log(`Loading contractor data for: ${contractorName}`);
          const response = await fetch(`/api/contractors/profile-data-by-name/${encodeURIComponent(contractorName)}`);
          
          if (response.ok) {
            const result = await response.json();
            if (result.found) {
              console.log('Pre-loaded contractor data:', result.data);
              setPreLoadedData(result.data);
              setContractorData(result.data);
              
              // Auto-load matching projects for email arrivals
              loadMatchingProjects(result.data);
            } else {
              console.log(`No pre-discovered data found for contractor: ${contractorName}`);
            }
          }
        } catch (error) {
          console.error('Error loading contractor data:', error);
        }
      }
    };

    loadContractorData();
  }, [contractorName]);

  // Load matching projects based on contractor profile
  const loadMatchingProjects = async (contractor?: any) => {
    try {
      const profileData = contractor || contractorData;
      if (!profileData) return;

      console.log('Loading matching projects for contractor:', profileData);
      
      // Call matching API with contractor specialties and location
      const response = await fetch('/api/contractors/matching-projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contractor_id: profileData.id,
          specialties: profileData.specialties || [],
          main_service_type: profileData.main_service_type || profileData.specialties?.[0],
          zip_codes: profileData.zip_codes || [profileData.zip_code],
          service_radius_miles: profileData.service_radius_miles || 25,
          business_size_category: profileData.business_size_category || 'LOCAL_BUSINESS_TEAMS'
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setMatchingProjects(result.matching_projects || []);
        console.log(`Found ${result.matching_projects?.length || 0} matching projects`);
      }
    } catch (error) {
      console.error('Error loading matching projects:', error);
    }
  };

  const benefits = [
    {
      icon: Shield,
      title: "Zero Lead Fees",
      description: "Submit unlimited quotes for free. Pay only when you win the job.",
      color: "text-green-600",
    },
    {
      icon: Target,
      title: "Pre-Qualified Homeowners",
      description: "Every homeowner has confirmed budget and is ready to hire immediately.",
      color: "text-blue-600",
    },
    {
      icon: TrendingUp,
      title: "Higher Win Rates",
      description: "Our contractors average 40% higher win rates than industry standard.",
      color: "text-purple-600",
    },
    {
      icon: Zap,
      title: "Instant Notifications",
      description: "Get notified within minutes of new projects in your area.",
      color: "text-orange-600",
    },
  ];

  const renderMatchingProjectCard = (project: MatchingProject) => (
    <motion.div
      key={project.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
    >
      <div className="flex justify-between items-start mb-3">
        <h4 className="text-lg font-semibold text-gray-900 line-clamp-2">{project.title}</h4>
        <div className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
          {project.match_score}% match
        </div>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="flex items-center text-gray-600">
          <DollarSign className="w-4 h-4 mr-2" />
          <span className="text-sm">
            ${project.budget_range.min.toLocaleString()} - ${project.budget_range.max.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center text-gray-600">
          <MapPin className="w-4 h-4 mr-2" />
          <span className="text-sm">{project.location.city}, {project.location.state}</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-1 mb-3">
        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
          {project.project_type}
        </span>
        {project.categories.slice(0, 2).map((category, idx) => (
          <span key={idx} className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">
            {category}
          </span>
        ))}
      </div>

      <div className="mb-4">
        <p className="text-xs text-gray-500 mb-1">Why this matches you:</p>
        <ul className="text-xs text-gray-600 space-y-1">
          {project.match_reasons.slice(0, 2).map((reason, idx) => (
            <li key={idx} className="flex items-start">
              <span className="text-green-500 mr-1">•</span>
              {reason}
            </li>
          ))}
        </ul>
      </div>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => {
            // Navigate to bid card detail or open in modal
            console.log('View project details:', project.id);
          }}
          className="flex-1 bg-gray-100 text-gray-700 px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-200 transition-colors"
        >
          View Details
        </button>
        <button
          type="button"
          onClick={() => {
            // Start bid submission process
            console.log('Submit bid for:', project.id);
          }}
          className="flex-1 bg-orange-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-orange-700 transition-colors"
        >
          Submit Bid
        </button>
      </div>
    </motion.div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm fixed top-0 w-full z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <button
              type="button"
              onClick={() => navigate("/")}
              className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent"
            >
              Instabids
            </button>
            <nav className="flex gap-4">
              <button
                type="button"
                onClick={() => navigate("/")}
                className="text-gray-700 hover:text-primary-600 transition-colors"
              >
                Homeowner Portal
              </button>
              <button
                type="button"
                onClick={() => {
                  // Set contractor role in localStorage for demo
                  localStorage.setItem(
                    "DEMO_USER",
                    JSON.stringify({
                      id: "c24d60b5-5469-4207-a364-f20363422d8a",
                      email: "info@jmholidaylighting.com",
                      role: "contractor",
                      full_name: "JM Holiday Lighting, Inc.",
                    })
                  );
                  // Navigate directly to contractor dashboard for demo users
                  navigate("/contractor/dashboard");
                }}
                className="bg-orange-600 text-white px-6 py-2 rounded-lg hover:bg-orange-700 transition-colors font-semibold"
              >
                Login as Existing Contractor
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-24 pb-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Hero Text */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-8"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent">
              {contractorName ? `Welcome, ${contractorName}!` : "Grow Your Business Without Lead Fees"}
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-4">
              {contractorName 
                ? "We have a project opportunity for you. Tell us about your business to get started."
                : "Join 10,000+ contractors getting pre-qualified homeowner projects. No upfront costs, no monthly fees."}
            </p>
            <div className="text-lg text-gray-700 font-medium">
              {contractorName 
                ? "Complete your profile below to submit your bid"
                : "New contractor? Start chatting below. Existing contractor? Click login above."}
            </div>
          </motion.div>

          {/* Matching Projects Section (Email Arrivals) */}
          {contractorName && matchingProjects.length > 0 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              className="mb-8"
            >
              <div className="bg-blue-50 rounded-2xl p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-2xl font-bold text-gray-900">
                    Perfect Match! We Found {matchingProjects.length} Projects For You
                  </h3>
                  <button
                    type="button"
                    onClick={() => setShowMarketplace(!showMarketplace)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
                  >
                    <Search className="w-4 h-4" />
                    {showMarketplace ? 'Hide All Projects' : 'Browse All Projects'}
                  </button>
                </div>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {matchingProjects.slice(0, 3).map(renderMatchingProjectCard)}
                </div>
                {matchingProjects.length > 3 && (
                  <div className="text-center mt-4">
                    <button
                      type="button"
                      onClick={() => setShowMarketplace(true)}
                      className="text-blue-600 font-medium hover:text-blue-700"
                    >
                      View {matchingProjects.length - 3} more matching projects →
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Trust Indicators */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="flex flex-wrap justify-center gap-6 mb-8"
          >
            {benefits.map((benefit, index) => (
              <div key={index} className="flex items-center gap-2">
                <benefit.icon className={`w-5 h-5 ${benefit.color}`} />
                <span className="text-sm text-gray-600">{benefit.title}</span>
              </div>
            ))}
          </motion.div>

          {/* Full Marketplace Section (Toggleable) */}
          {showMarketplace && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.5 }}
              className="mb-12"
            >
              <div className="bg-white rounded-2xl shadow-2xl p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-2xl font-bold text-gray-900">Browse All Available Projects</h3>
                  <button
                    type="button"
                    onClick={() => setShowMarketplace(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ✕ Close
                  </button>
                </div>
                <BidCardMarketplace
                  contractorId={contractorData?.id}
                  userType="contractor"
                />
              </div>
            </motion.div>
          )}

          {/* Chat Interface */}
          {!showMarketplace && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5, duration: 0.5 }}
              className="max-w-4xl mx-auto"
            >
              <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
                <ContractorOnboardingChat
                  sessionId={sessionId}
                  onComplete={(contractorId) => {
                    console.log('Contractor onboarding complete:', contractorId);
                    setConversationComplete(true);
                    setShowSignupPrompt(true);
                    
                    // Load matching projects after onboarding
                    loadMatchingProjects();
                  }}
                />
              </div>
            </motion.div>
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
                <h3 className="text-2xl font-bold mb-4">Perfect! Your Profile is Ready</h3>
                <p className="text-gray-600 mb-6">
                  Create your account to start receiving project leads immediately. No credit card
                  required!
                </p>
                <button
                  type="button"
                  onClick={() => console.log("Create account clicked")}
                  className="w-full bg-gradient-to-r from-orange-600 to-red-600 text-white py-3 rounded-lg font-semibold hover:shadow-lg transition-all duration-200 mb-3"
                >
                  Create Free Account
                </button>
                <button
                  type="button"
                  onClick={() => setShowMarketplace(true)}
                  className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors mb-3"
                >
                  Browse All Projects First
                </button>
                <button
                  type="button"
                  onClick={() => console.log("Continue chatting clicked")}
                  className="w-full text-gray-500 py-2 hover:text-gray-700 transition-colors"
                >
                  Continue chatting
                </button>
              </motion.div>
            </motion.div>
          )}
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-12 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="grid md:grid-cols-2 lg:grid-cols-4 gap-8"
          >
            {benefits.map((benefit, index) => (
              <div
                key={index}
                className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow"
              >
                <benefit.icon className={`w-10 h-10 ${benefit.color} mb-4`} />
                <h3 className="text-lg font-semibold mb-2">{benefit.title}</h3>
                <p className="text-gray-600">{benefit.description}</p>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center mb-8"
          >
            <h3 className="text-2xl font-bold mb-8">Trusted by Contractors Nationwide</h3>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="bg-white p-6 rounded-xl shadow-sm">
                <div className="flex mb-2">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 fill-current text-yellow-400" />
                  ))}
                </div>
                <p className="text-gray-600 mb-2">
                  "No more cold calls! I get 5-10 qualified leads per week and close 40% of them."
                </p>
                <p className="text-sm font-semibold">- Mike's Plumbing, Dallas</p>
              </div>
              <div className="bg-white p-6 rounded-xl shadow-sm">
                <div className="flex mb-2">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 fill-current text-yellow-400" />
                  ))}
                </div>
                <p className="text-gray-600 mb-2">
                  "Finally, a platform that respects contractors. No fees until we win the job!"
                </p>
                <p className="text-sm font-semibold">- Elite Renovations, Miami</p>
              </div>
              <div className="bg-white p-6 rounded-xl shadow-sm">
                <div className="flex mb-2">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 fill-current text-yellow-400" />
                  ))}
                </div>
                <p className="text-gray-600 mb-2">
                  "Doubled my revenue in 6 months. The AI matching is incredible."
                </p>
                <p className="text-sm font-semibold">- Pro Painters LLC, Denver</p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 text-center text-gray-500 text-sm">
        <p>© 2025 Instabids. All rights reserved. | Privacy | Terms | Contractor Agreement</p>
      </footer>
    </div>
  );
};

export default EnhancedContractorLandingPage;