import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';

const GlassmorphismChatDemo: React.FC = () => {
  return (
    <div className="grid lg:grid-cols-2 gap-8 mb-8">
      {/* High-End Glassmorphism Chat Interface */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>🚀 High-End Glassmorphism Chat (Dynamic AI)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 rounded-2xl p-6 min-h-[500px] relative overflow-hidden">
            {/* Floating Particles Background */}
            <div className="absolute inset-0 overflow-hidden">
              <div className="absolute top-10 left-10 w-2 h-2 bg-blue-400 rounded-full animate-float animation-delay-100"></div>
              <div className="absolute top-20 right-20 w-3 h-3 bg-purple-400 rounded-full animate-float animation-delay-300"></div>
              <div className="absolute bottom-20 left-20 w-2 h-2 bg-pink-400 rounded-full animate-float animation-delay-500"></div>
              <div className="absolute bottom-10 right-10 w-3 h-3 bg-blue-300 rounded-full animate-float animation-delay-600"></div>
            </div>

            {/* Glassmorphism Chat Container */}
            <div className="relative bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl shadow-2xl overflow-hidden">
              {/* Dynamic AI Header with Personality */}
              <div className="bg-white/20 backdrop-blur-md border-b border-white/20 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {/* Animated AI Avatar */}
                    <div className="relative">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-xl animate-pulse">
                        🤖
                      </div>
                      {/* Pulse Rings */}
                      <div className="absolute inset-0 rounded-full border-2 border-blue-400 opacity-50 animate-ping"></div>
                      <div className="absolute inset-0 rounded-full border border-purple-400 opacity-30 animate-ping animation-delay-200"></div>
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-800">AI Chat Assistant</h3>
                      <p className="text-sm text-gray-600 animate-pulse">*cracks digital knuckles* Let's build something amazing!</p>
                    </div>
                  </div>

                  {/* Status Indicator */}
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce"></div>
                    <span className="text-xs text-gray-600">Thinking of something clever...</span>
                  </div>
                </div>
              </div>

              {/* Messages Area with Glassmorphism */}
              <div className="p-4 space-y-4 h-80 overflow-y-auto">
                {/* AI Message 1 */}
                <div className="flex justify-start">
                  <div className="max-w-xs bg-white/30 backdrop-blur-lg border border-white/30 rounded-2xl p-3 shadow-lg">
                    <p className="text-sm text-gray-800">Hey there! I'm feeling super caffeinated today ☕ What amazing project are we tackling?</p>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce"></div>
                      <div className="w-1 h-1 bg-purple-400 rounded-full animate-bounce animation-delay-100"></div>
                      <div className="w-1 h-1 bg-pink-400 rounded-full animate-bounce animation-delay-200"></div>
                      <span className="text-xs text-gray-500 ml-2">Just now</span>
                    </div>
                  </div>
                </div>

                {/* User Message */}
                <div className="flex justify-end">
                  <div className="max-w-xs bg-gradient-to-r from-blue-500/80 to-purple-600/80 backdrop-blur-lg border border-white/30 rounded-2xl p-3 shadow-lg text-white">
                    <p className="text-sm">I want to renovate my kitchen</p>
                    <span className="text-xs text-blue-100 block mt-1">9:31 AM</span>
                  </div>
                </div>

                {/* AI Message 2 - Entertaining Response */}
                <div className="flex justify-start">
                  <div className="max-w-xs bg-white/30 backdrop-blur-lg border border-white/30 rounded-2xl p-3 shadow-lg">
                    <p className="text-sm text-gray-800">Kitchen renovation? 🍳 Oh, we're about to cook up something DELICIOUS! I can already smell the success... or maybe that's just the new granite countertops? 😄</p>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="animate-spin w-3 h-3 border border-blue-400 border-t-transparent rounded-full"></div>
                      <span className="text-xs text-gray-500">Calculating contractor magic...</span>
                    </div>
                  </div>
                </div>

                {/* AI Typing Indicator */}
                <div className="flex justify-start">
                  <div className="max-w-xs bg-white/20 backdrop-blur-lg border border-white/30 rounded-2xl p-3 shadow-lg">
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce animation-delay-100"></div>
                        <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce animation-delay-200"></div>
                      </div>
                      <span className="text-xs text-gray-600 animate-pulse">Finding contractors faster than you can say "granite countertops"...</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Input Area with Glassmorphism */}
              <div className="bg-white/20 backdrop-blur-md border-t border-white/20 p-4">
                <div className="flex items-center gap-3">
                  <button className="p-2 bg-white/30 backdrop-blur-lg border border-white/30 rounded-xl hover:bg-white/40 transition-all">
                    📷
                  </button>
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      placeholder="Tell me more about your vision... I'm all ears! 👂"
                      className="w-full px-4 py-3 bg-white/30 backdrop-blur-lg border border-white/30 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400/50 text-gray-800 placeholder-gray-600"
                    />
                  </div>
                  <button className="p-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl transform hover:scale-105">
                    ✨
                  </button>
                </div>
                <div className="flex items-center justify-center mt-2 gap-2">
                  <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse"></div>
                  <span className="text-xs text-gray-600">Ready to make some magic happen</span>
                  <div className="w-1 h-1 bg-purple-400 rounded-full animate-pulse animation-delay-500"></div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Glassmorphism Bid Card */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>✨ High-End Glassmorphism Bid Card</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gradient-to-br from-amber-50 via-orange-50 to-red-50 rounded-2xl p-6 min-h-[400px] relative overflow-hidden">
            {/* Floating Elements */}
            <div className="absolute inset-0 overflow-hidden">
              <div className="absolute top-8 left-12 w-3 h-3 bg-amber-400 rounded-full animate-float animation-delay-200"></div>
              <div className="absolute top-16 right-16 w-2 h-2 bg-orange-400 rounded-full animate-float animation-delay-400"></div>
              <div className="absolute bottom-16 left-16 w-2 h-2 bg-red-400 rounded-full animate-float animation-delay-600"></div>
            </div>

            {/* Glassmorphism Bid Card */}
            <div className="relative bg-white/20 backdrop-blur-lg border border-white/30 rounded-2xl shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="bg-gradient-to-r from-amber-500/20 to-orange-500/20 backdrop-blur-md border-b border-white/20 p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-xl font-bold text-gray-800">Premium Kitchen Remodel</h3>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-sm text-gray-600">📍 Beverly Hills, CA</span>
                      <span className="text-sm text-gray-400">•</span>
                      <span className="text-sm text-gray-600">⏰ 30 days</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="inline-flex items-center px-3 py-1 bg-green-100/80 backdrop-blur-sm border border-green-200/50 rounded-full">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
                      <span className="text-green-800 text-sm font-medium">ACTIVE</span>
                    </div>
                    <p className="text-gray-500 text-xs mt-1">BID-2025-5847</p>
                  </div>
                </div>

                {/* Budget & Progress */}
                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div className="bg-white/30 backdrop-blur-lg border border-white/30 rounded-xl p-3 text-center">
                    <p className="text-lg font-bold text-gray-800">$45k - $65k</p>
                    <p className="text-xs text-gray-600">Budget Range</p>
                  </div>
                  <div className="bg-white/30 backdrop-blur-lg border border-white/30 rounded-xl p-3 text-center">
                    <p className="text-lg font-bold text-gray-800">3 / 5</p>
                    <p className="text-xs text-gray-600">Bids Received</p>
                  </div>
                  <div className="bg-white/30 backdrop-blur-lg border border-white/30 rounded-xl p-3 text-center">
                    <p className="text-lg font-bold text-gray-800">87%</p>
                    <p className="text-xs text-gray-600">Complete</p>
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="p-6">
                <div className="mb-4">
                  <h4 className="font-semibold text-gray-800 mb-2">Project Details</h4>
                  <p className="text-sm text-gray-700 leading-relaxed">
                    Complete luxury kitchen transformation with custom cabinetry, quartz countertops,
                    premium appliances, and sophisticated lighting. Looking for experienced contractors
                    with high-end residential portfolio.
                  </p>
                </div>

                {/* Features */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-amber-400 rounded-full"></div>
                    <span className="text-sm text-gray-700">Custom Cabinetry</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-orange-400 rounded-full"></div>
                    <span className="text-sm text-gray-700">Quartz Countertops</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                    <span className="text-sm text-gray-700">Premium Appliances</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-amber-500 rounded-full"></div>
                    <span className="text-sm text-gray-700">LED Lighting</span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 mt-6">
                  <button className="flex-1 bg-gradient-to-r from-amber-500 to-orange-500 text-white py-3 px-4 rounded-xl font-medium hover:from-amber-600 hover:to-orange-600 transition-all shadow-lg hover:shadow-xl transform hover:scale-105">
                    View Bids
                  </button>
                  <button className="px-4 py-3 bg-white/30 backdrop-blur-lg border border-white/30 rounded-xl text-gray-700 hover:bg-white/40 transition-all">
                    💬
                  </button>
                  <button className="px-4 py-3 bg-white/30 backdrop-blur-lg border border-white/30 rounded-xl text-gray-700 hover:bg-white/40 transition-all">
                    📤
                  </button>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default GlassmorphismChatDemo;