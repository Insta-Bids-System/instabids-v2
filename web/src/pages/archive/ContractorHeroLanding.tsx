import { motion } from "framer-motion";
import {
  ArrowRight,
  Camera,
  CheckCircle,
  Clock,
  DollarSign,
  Handshake,
  MessageSquare,
  Shield,
  Target,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

const ContractorHeroLanding: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [bidCard, setBidCard] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const bidToken = searchParams.get("bid");
  const source = searchParams.get("src") || "web";

  useEffect(() => {
    const loadBidCardData = async () => {
      if (bidToken) {
        try {
          // Try to fetch real bid card data from API
          const response = await fetch(`/api/bid-cards/by-token/${bidToken}`);
          if (response.ok) {
            const realData = await response.json();
            setBidCard({
              ...realData,
              // Ensure we have photo URLs for display
              photo_urls: realData.photo_urls || [
                "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
              ],
            });
          } else {
            // Fallback to demo data if API fails
            setBidCard({
              id: "demo-123",
              public_token: bidToken,
              project_type: "kitchen_remodel",
              urgency: "month",
              budget_display: "$15,000 - $25,000",
              location: {
                city: "Melbourne",
                state: "FL",
              },
              contractor_count: 4,
              photo_urls: [
                "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
              ],
              project_details: {
                scope_of_work: [
                  "Complete kitchen cabinet replacement with modern white shaker style",
                  "Install new granite countertops with undermount sink",
                  "Update all appliances to stainless steel Energy Star models",
                ],
              },
            });
          }
        } catch (error) {
          console.error("Failed to load bid card data:", error);
          // Use demo data as fallback
          setBidCard({
            id: "demo-123",
            public_token: bidToken,
            project_type: "kitchen_remodel",
            urgency: "month",
            budget_display: "$15,000 - $25,000",
            location: {
              city: "Melbourne",
              state: "FL",
            },
            contractor_count: 4,
            photo_urls: [
              "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
            ],
            project_details: {
              scope_of_work: [
                "Complete kitchen cabinet replacement with modern white shaker style",
                "Install new granite countertops with undermount sink",
                "Update all appliances to stainless steel Energy Star models",
              ],
            },
          });
        }
      }
      setLoading(false);
    };

    loadBidCardData();
  }, [bidToken]);

  const formatProjectType = (type: string) => {
    return type?.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()) || "Home Project";
  };

  const getProjectEmoji = (type: string) => {
    const emojiMap: { [key: string]: string } = {
      kitchen_remodel: "🍳",
      bathroom_renovation: "🛁",
      roof_replacement: "🏠",
      landscaping: "🌿",
      flooring: "🪵",
      painting: "🎨",
      plumbing: "🔧",
      electrical: "⚡",
    };
    return emojiMap[type] || "🏗️";
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-indigo-900 to-purple-900 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-2 border-white border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-indigo-900 to-purple-900 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.1, 0.2, 0.1],
          }}
          transition={{ duration: 8, repeat: Infinity }}
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500 rounded-full blur-3xl"
        />
        <motion.div
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.1, 0.15, 0.1],
          }}
          transition={{ duration: 10, repeat: Infinity }}
          className="absolute bottom-1/4 right-1/3 w-80 h-80 bg-purple-500 rounded-full blur-3xl"
        />
      </div>

      <div className="relative z-10">
        {/* Hero Section */}
        <div className="max-w-7xl mx-auto px-4 pt-8 pb-16">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <div className="flex items-center justify-center gap-3 mb-6">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-white">IB</span>
              </div>
              <h1 className="text-3xl font-bold text-white">InstaBids</h1>
            </div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3, duration: 0.8 }}
              className="bg-white/10 backdrop-blur-sm rounded-2xl p-2 inline-block mb-8"
            >
              <div className="bg-gradient-to-r from-orange-400 to-red-400 text-white px-6 py-2 rounded-xl text-sm font-semibold flex items-center gap-2">
                <Zap className="w-4 h-4" />
                NEW PROJECT ALERT
              </div>
            </motion.div>

            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.8 }}
              className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight"
            >
              Skip The Leads.
              <br />
              <span className="bg-gradient-to-r from-yellow-400 to-orange-400 bg-clip-text text-transparent">
                Win The Job.
              </span>
            </motion.h2>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7, duration: 0.8 }}
              className="text-xl text-blue-100 mb-8 max-w-3xl mx-auto leading-relaxed"
            >
              Connect directly with qualified homeowners ready to hire. No lead fees, no sales
              meetings, no advertising costs.
              <span className="text-yellow-300 font-semibold"> Only pay when you win the job.</span>
            </motion.p>
          </motion.div>

          {/* Project Spotlight */}
          {bidCard && (
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.9, duration: 0.8 }}
              className="max-w-4xl mx-auto mb-16"
            >
              <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 border border-white/20">
                <div className="text-center mb-6">
                  <div className="text-6xl mb-4">{getProjectEmoji(bidCard.project_type)}</div>
                  <h3 className="text-3xl font-bold text-white mb-2">
                    {formatProjectType(bidCard.project_type)} Available
                  </h3>
                  <p className="text-blue-200 text-lg">
                    {bidCard.location.city}, {bidCard.location.state} • {bidCard.budget_display}
                  </p>
                </div>

                <div className="grid md:grid-cols-2 gap-8 items-center">
                  {/* Project Image */}
                  {bidCard.photo_urls?.[0] && (
                    <div className="relative">
                      <motion.img
                        whileHover={{ scale: 1.05 }}
                        transition={{ duration: 0.3 }}
                        src={bidCard.photo_urls[0]}
                        alt="Project"
                        className="w-full h-64 object-cover rounded-2xl shadow-2xl"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent rounded-2xl" />
                      <div className="absolute bottom-4 left-4 text-white">
                        <div className="flex items-center gap-2 text-sm font-semibold">
                          <Camera className="w-4 h-4" />
                          High-quality project photos included
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Project Details */}
                  <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-white/5 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-green-400 mb-2">
                          <DollarSign className="w-5 h-5" />
                          <span className="font-semibold">Budget Ready</span>
                        </div>
                        <div className="text-white text-lg font-bold">{bidCard.budget_display}</div>
                      </div>

                      <div className="bg-white/5 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-blue-400 mb-2">
                          <Clock className="w-5 h-5" />
                          <span className="font-semibold">Timeline</span>
                        </div>
                        <div className="text-white text-lg font-bold">Within 30 Days</div>
                      </div>
                    </div>

                    <div className="bg-white/5 rounded-xl p-4">
                      <div className="flex items-center gap-2 text-purple-400 mb-3">
                        <Users className="w-5 h-5" />
                        <span className="font-semibold">Contractor Spots</span>
                      </div>
                      <div className="text-white text-2xl font-bold mb-2">
                        {bidCard.contractor_count} Positions Available
                      </div>
                      <div className="text-green-300 text-sm">
                        ✅ Pre-qualified homeowner • ✅ Serious about hiring
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Value Propositions */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.1, duration: 0.8 }}
            className="grid md:grid-cols-3 gap-8 mb-16"
          >
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20 text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-green-400 to-emerald-400 rounded-full flex items-center justify-center mx-auto mb-6">
                <Shield className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Zero Lead Fees</h3>
              <p className="text-blue-200 leading-relaxed">
                No upfront costs, no monthly subscriptions. Only pay a small success fee after
                you're selected by the homeowner.
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20 text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-400 to-cyan-400 rounded-full flex items-center justify-center mx-auto mb-6">
                <MessageSquare className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Direct Communication</h3>
              <p className="text-blue-200 leading-relaxed">
                Chat directly with homeowners. Get photos, measurements, and project details
                instantly through our AI-assisted platform.
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20 text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full flex items-center justify-center mx-auto mb-6">
                <Target className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Group Projects</h3>
              <p className="text-blue-200 leading-relaxed">
                Win multiple jobs at once. Bid on grouped projects from the same homeowner or
                neighborhood for maximum efficiency.
              </p>
            </div>
          </motion.div>

          {/* CTA Section */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.3, duration: 0.8 }}
            className="text-center"
          >
            <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-12 border border-white/20 max-w-4xl mx-auto">
              <h3 className="text-3xl font-bold text-white mb-6">
                Ready to Start Winning More Jobs?
              </h3>

              <div className="grid md:grid-cols-2 gap-8 mb-8">
                <div className="text-left">
                  <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-400" />
                    What You Get:
                  </h4>
                  <ul className="space-y-2 text-blue-200">
                    <li>• Direct access to qualified homeowners</li>
                    <li>• AI-assisted quote generation</li>
                    <li>• Project photos and measurements</li>
                    <li>• Real-time communication tools</li>
                    <li>• Payment protection guarantee</li>
                  </ul>
                </div>

                <div className="text-left">
                  <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-yellow-400" />
                    Success Metrics:
                  </h4>
                  <ul className="space-y-2 text-blue-200">
                    <li>• 3x higher win rates than competitors</li>
                    <li>• Average project value: $18,500</li>
                    <li>• 89% contractor satisfaction rate</li>
                    <li>• Same-day quote responses</li>
                    <li>• Verified homeowner budgets</li>
                  </ul>
                </div>
              </div>

              <motion.a
                href={`/signup?type=contractor&source=bid_card&bid=${bidToken}&src=${source}`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="inline-block bg-gradient-to-r from-yellow-400 to-orange-500 text-gray-900 px-12 py-4 rounded-2xl font-bold text-xl shadow-2xl hover:shadow-3xl transition-all duration-300"
              >
                <div className="flex items-center gap-3">
                  <Handshake className="w-6 h-6" />
                  Join InstaBids - Start Winning Today
                  <ArrowRight className="w-6 h-6" />
                </div>
              </motion.a>

              <p className="text-blue-200 text-sm mt-4">
                Free to join • No setup fees • Only pay when you win
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default ContractorHeroLanding;
