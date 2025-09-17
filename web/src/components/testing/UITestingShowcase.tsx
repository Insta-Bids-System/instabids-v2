import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Star, Users, Clock, Shield, TrendingUp, Zap, DollarSign, Calendar, MapPin, Home, MessageSquare, Sparkles, Palette, Bot } from 'lucide-react';
import CIAChatWithBidCardPreview from '@/components/chat/CIAChatWithBidCardPreview';
import { motion, useMotionValue, useSpring, useTransform, AnimatePresence } from 'framer-motion';

const UITestingShowcase: React.FC = () => {
  const [activeDemo, setActiveDemo] = useState<'glassmorphism' | 'gradient' | 'group' | 'cards' | 'interactive' | 'animations' | 'premium'>('glassmorphism');

  return (
    <div className="space-y-8">
      {/* Demo Selector */}
      <div className="flex flex-wrap justify-center gap-2 mb-8">
        <button
          onClick={() => setActiveDemo('glassmorphism')}
          className={`px-4 py-2 rounded-lg transition-all ${
            activeDemo === 'glassmorphism'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          ✨ Glassmorphism
        </button>
        <button
          onClick={() => setActiveDemo('gradient')}
          className={`px-4 py-2 rounded-lg transition-all ${
            activeDemo === 'gradient'
              ? 'bg-purple-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          🎨 Gradients
        </button>
        <button
          onClick={() => setActiveDemo('group')}
          className={`px-4 py-2 rounded-lg transition-all ${
            activeDemo === 'group'
              ? 'bg-green-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          👥 Group Bidding
        </button>
        <button
          onClick={() => setActiveDemo('cards')}
          className={`px-4 py-2 rounded-lg transition-all ${
            activeDemo === 'cards'
              ? 'bg-orange-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          🃏 Card Styles
        </button>
        <button
          onClick={() => setActiveDemo('interactive')}
          className={`px-4 py-2 rounded-lg transition-all ${
            activeDemo === 'interactive'
              ? 'bg-pink-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          🤖 Interactive
        </button>
        <button
          onClick={() => setActiveDemo('animations')}
          className={`px-4 py-2 rounded-lg transition-all ${
            activeDemo === 'animations'
              ? 'bg-indigo-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          🎭 Animations
        </button>
        <button
          onClick={() => setActiveDemo('premium')}
          className={`px-4 py-2 rounded-lg transition-all ${
            activeDemo === 'premium'
              ? 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          💎 Premium Stack
        </button>
      </div>

      {/* Glassmorphism Demo */}
      {activeDemo === 'glassmorphism' && (
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Glassmorphism Chat Interface */}
          <Card>
            <CardHeader>
              <CardTitle>🚀 High-End Glassmorphism Chat</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 rounded-2xl p-6 min-h-[400px] relative overflow-hidden">
                {/* Floating Particles */}
                <div className="absolute inset-0 overflow-hidden">
                  <div className="absolute top-10 left-10 w-2 h-2 bg-blue-400 rounded-full animate-float animation-delay-100"></div>
                  <div className="absolute top-20 right-20 w-3 h-3 bg-purple-400 rounded-full animate-float animation-delay-300"></div>
                  <div className="absolute bottom-20 left-20 w-2 h-2 bg-pink-400 rounded-full animate-float animation-delay-500"></div>
                </div>

                {/* Glassmorphism Container */}
                <div className="relative bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl shadow-2xl p-4">
                  <div className="space-y-4">
                    <div className="bg-white/30 backdrop-blur-lg border border-white/30 rounded-xl p-3">
                      <p className="text-sm text-gray-800">AI: "Ready to transform your space! ✨"</p>
                    </div>
                    <div className="bg-gradient-to-r from-blue-500/80 to-purple-600/80 backdrop-blur-lg rounded-xl p-3 text-white ml-auto max-w-xs">
                      <p className="text-sm">User: "I need a modern kitchen"</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Glassmorphism Bid Card */}
          <Card>
            <CardHeader>
              <CardTitle>✨ Glassmorphism Bid Card</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-gradient-to-br from-amber-50 via-orange-50 to-red-50 rounded-2xl p-6 relative overflow-hidden">
                <div className="relative bg-white/20 backdrop-blur-lg border border-white/30 rounded-2xl shadow-2xl overflow-hidden">
                  <div className="bg-gradient-to-r from-amber-500/20 to-orange-500/20 backdrop-blur-md p-4 border-b border-white/20">
                    <h3 className="text-lg font-bold">Premium Kitchen Remodel</h3>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-700">
                      <span>📍 Beverly Hills</span>
                      <span>⏰ 30 days</span>
                      <span className="bg-green-100/80 px-2 py-1 rounded-full text-green-800">ACTIVE</span>
                    </div>
                  </div>
                  <div className="p-4">
                    <div className="grid grid-cols-3 gap-3 mb-4">
                      <div className="bg-white/30 backdrop-blur-lg rounded-lg p-2 text-center">
                        <p className="font-bold">$45k-$65k</p>
                        <p className="text-xs text-gray-600">Budget</p>
                      </div>
                      <div className="bg-white/30 backdrop-blur-lg rounded-lg p-2 text-center">
                        <p className="font-bold">3/5</p>
                        <p className="text-xs text-gray-600">Bids</p>
                      </div>
                      <div className="bg-white/30 backdrop-blur-lg rounded-lg p-2 text-center">
                        <p className="font-bold">87%</p>
                        <p className="text-xs text-gray-600">Complete</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Gradient Demo */}
      {activeDemo === 'gradient' && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Gradient Card 1 - Aurora */}
          <Card className="overflow-hidden">
            <div className="h-full bg-gradient-to-br from-purple-400 via-pink-500 to-red-500 p-6 text-white">
              <h3 className="text-xl font-bold mb-2">Aurora Gradient</h3>
              <p className="text-white/90">Perfect for premium features</p>
              <div className="mt-4 space-y-2">
                <div className="bg-white/20 backdrop-blur-sm rounded-lg p-2">Feature 1</div>
                <div className="bg-white/20 backdrop-blur-sm rounded-lg p-2">Feature 2</div>
              </div>
            </div>
          </Card>

          {/* Gradient Card 2 - Ocean */}
          <Card className="overflow-hidden">
            <div className="h-full bg-gradient-to-br from-blue-400 via-cyan-500 to-teal-500 p-6 text-white">
              <h3 className="text-xl font-bold mb-2">Ocean Gradient</h3>
              <p className="text-white/90">Calming and professional</p>
              <div className="mt-4 space-y-2">
                <div className="bg-white/20 backdrop-blur-sm rounded-lg p-2">Service 1</div>
                <div className="bg-white/20 backdrop-blur-sm rounded-lg p-2">Service 2</div>
              </div>
            </div>
          </Card>

          {/* Gradient Card 3 - Sunset */}
          <Card className="overflow-hidden">
            <div className="h-full bg-gradient-to-br from-orange-400 via-red-500 to-pink-500 p-6 text-white">
              <h3 className="text-xl font-bold mb-2">Sunset Gradient</h3>
              <p className="text-white/90">Warm and inviting</p>
              <div className="mt-4 space-y-2">
                <div className="bg-white/20 backdrop-blur-sm rounded-lg p-2">Option 1</div>
                <div className="bg-white/20 backdrop-blur-sm rounded-lg p-2">Option 2</div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Group Bidding Demo */}
      {activeDemo === 'group' && (
        <div className="space-y-6">
          {/* Group Bidding Header */}
          <Card>
            <CardHeader className="bg-gradient-to-r from-green-500 to-blue-600 text-white">
              <CardTitle className="flex items-center gap-2">
                <Users className="w-6 h-6" />
                Group Bidding - Save 15-25%
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid md:grid-cols-3 gap-4">
                {/* Group Card 1 */}
                <div className="border-2 border-green-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-bold">Lawn Care Group</h4>
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">15% OFF</span>
                  </div>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4" />
                      <span>8/10 neighbors joined</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4" />
                      <span>Beverly Hills, 90210</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      <span>Starts March 1st</span>
                    </div>
                  </div>
                  <button className="w-full mt-4 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors">
                    Join Group
                  </button>
                </div>

                {/* Group Card 2 */}
                <div className="border-2 border-blue-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-bold">Pool Service Bundle</h4>
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">20% OFF</span>
                  </div>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4" />
                      <span>12/15 pools enrolled</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4" />
                      <span>Malibu, 90265</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      <span>Weekly service</span>
                    </div>
                  </div>
                  <button className="w-full mt-4 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors">
                    Join Group
                  </button>
                </div>

                {/* Group Card 3 */}
                <div className="border-2 border-purple-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-bold">Solar Installation</h4>
                    <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs">25% OFF</span>
                  </div>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4" />
                      <span>5/8 homes committed</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4" />
                      <span>Pasadena, 91101</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      <span>Est. $12k savings/year</span>
                    </div>
                  </div>
                  <button className="w-full mt-4 bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700 transition-colors">
                    Join Group
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Group Progress Tracker */}
          <Card>
            <CardHeader>
              <CardTitle>Your Group Projects</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-semibold">Neighborhood Lawn Care</h4>
                    <span className="text-green-600 font-bold">Active</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div className="bg-green-600 h-2 rounded-full" style={{ width: '80%' }}></div>
                  </div>
                  <p className="text-sm text-gray-600">8 of 10 neighbors joined • Starts in 3 days</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Card Styles Demo */}
      {activeDemo === 'cards' && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Neumorphic Card */}
          <Card className="bg-gray-100 shadow-[20px_20px_60px_#bebebe,-20px_-20px_60px_#ffffff]">
            <CardHeader>
              <CardTitle>Neumorphic Style</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">Soft, raised appearance with subtle shadows</p>
              <div className="mt-4 p-3 bg-gray-100 rounded-lg shadow-[inset_5px_5px_10px_#bebebe,inset_-5px_-5px_10px_#ffffff]">
                <p className="text-sm">Inset element</p>
              </div>
            </CardContent>
          </Card>

          {/* Neon Glow Card */}
          <Card className="bg-black border-2 border-cyan-400 shadow-[0_0_30px_rgba(6,182,212,0.5)]">
            <CardHeader>
              <CardTitle className="text-cyan-400">Neon Glow</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-cyan-200">Cyberpunk-inspired with glowing borders</p>
              <button className="mt-4 px-4 py-2 bg-cyan-400 text-black font-bold rounded hover:shadow-[0_0_20px_rgba(6,182,212,0.8)] transition-all">
                ACTIVATE
              </button>
            </CardContent>
          </Card>

          {/* 3D Transform Card */}
          <Card className="transform hover:rotate-y-6 hover:scale-105 transition-all duration-500 hover:shadow-2xl">
            <CardHeader>
              <CardTitle>3D Transform</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">Hover for 3D effect</p>
              <div className="mt-4 flex gap-2">
                <div className="w-8 h-8 bg-blue-500 rounded transform hover:rotate-45 transition-transform"></div>
                <div className="w-8 h-8 bg-purple-500 rounded transform hover:rotate-45 transition-transform"></div>
                <div className="w-8 h-8 bg-pink-500 rounded transform hover:rotate-45 transition-transform"></div>
              </div>
            </CardContent>
          </Card>

          {/* Animated Border Card */}
          <Card className="relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 animate-gradient-x"></div>
            <div className="relative bg-white m-[2px] rounded-lg p-6">
              <h3 className="text-xl font-bold mb-2">Animated Border</h3>
              <p className="text-gray-600">Gradient border animation</p>
            </div>
          </Card>

          {/* Floating Card */}
          <Card className="animate-float shadow-xl hover:shadow-2xl transition-shadow">
            <CardHeader>
              <CardTitle>Floating Card</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">Gentle floating animation</p>
              <div className="mt-4 flex gap-2">
                <Star className="w-5 h-5 text-yellow-500 animate-pulse" />
                <Star className="w-5 h-5 text-yellow-500 animate-pulse animation-delay-100" />
                <Star className="w-5 h-5 text-yellow-500 animate-pulse animation-delay-200" />
              </div>
            </CardContent>
          </Card>

          {/* Material Design Card */}
          <Card className="shadow-md hover:shadow-xl transition-shadow duration-300">
            <CardHeader className="bg-gradient-to-r from-indigo-500 to-blue-600 text-white">
              <CardTitle>Material Design</CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <p className="text-gray-600">Clean elevation system</p>
              <div className="mt-4 flex gap-2">
                <button className="px-4 py-2 bg-indigo-500 text-white rounded shadow hover:shadow-lg transition-shadow">
                  ACTION
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Interactive Demo */}
      {activeDemo === 'interactive' && (
        <div className="space-y-6">
          {/* CIA Chat with Bid Card Preview */}
          <Card>
            <CardHeader className="bg-gradient-to-r from-pink-500 to-rose-600 text-white">
              <CardTitle className="flex items-center gap-2">
                <Bot className="w-6 h-6" />
                CIA Chat with Live Bid Card Building
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="h-[600px] overflow-hidden">
                <CIAChatWithBidCardPreview
                  initialMessage="Hi! I'm Alex, your AI project assistant. I'll help you create a bid card to get competitive quotes from verified contractors. Let's start with the basics - what type of project are you planning?"
                  showBidCardPreview={true}
                  onProjectReady={(bidCardId) => {
                    console.log('Project ready! Bid card ID:', bidCardId);
                  }}
                />
              </div>
            </CardContent>
          </Card>

          {/* Interactive Form Builder */}
          <Card>
            <CardHeader>
              <CardTitle>Interactive Project Builder</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <label className="block text-sm font-medium mb-2">Project Type</label>
                  <select className="w-full p-2 border rounded-lg">
                    <option>Kitchen Remodel</option>
                    <option>Bathroom Renovation</option>
                    <option>Landscaping</option>
                    <option>Pool Installation</option>
                  </select>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <label className="block text-sm font-medium mb-2">Budget Range</label>
                  <div className="flex gap-2">
                    <input type="text" placeholder="Min" className="flex-1 p-2 border rounded-lg" />
                    <input type="text" placeholder="Max" className="flex-1 p-2 border rounded-lg" />
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <label className="block text-sm font-medium mb-2">Timeline</label>
                  <div className="grid grid-cols-3 gap-2">
                    <button className="p-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200">Emergency</button>
                    <button className="p-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200">Urgent</button>
                    <button className="p-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200">Flexible</button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Animations Demo */}
      {activeDemo === 'animations' && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Pulse Animation */}
          <Card>
            <CardHeader>
              <CardTitle>Pulse Effect</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex justify-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-blue-500 rounded-full animate-ping opacity-75"></div>
                  <div className="relative bg-blue-500 text-white rounded-full p-4">
                    <MessageSquare className="w-8 h-8" />
                  </div>
                </div>
              </div>
              <p className="text-center mt-4 text-gray-600">Live notifications</p>
            </CardContent>
          </Card>

          {/* Bounce Animation */}
          <Card>
            <CardHeader>
              <CardTitle>Bounce Effect</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex justify-center">
                <div className="bg-green-500 text-white rounded-lg p-4 animate-bounce">
                  <DollarSign className="w-8 h-8" />
                </div>
              </div>
              <p className="text-center mt-4 text-gray-600">Attention grabber</p>
            </CardContent>
          </Card>

          {/* Spin Animation */}
          <Card>
            <CardHeader>
              <CardTitle>Spin Effect</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex justify-center">
                <div className="bg-purple-500 text-white rounded-lg p-4 animate-spin">
                  <Sparkles className="w-8 h-8" />
                </div>
              </div>
              <p className="text-center mt-4 text-gray-600">Loading states</p>
            </CardContent>
          </Card>

          {/* Wave Animation */}
          <Card>
            <CardHeader>
              <CardTitle>Wave Effect</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex justify-center gap-1">
                <div className="bg-blue-500 w-2 h-8 rounded animate-pulse"></div>
                <div className="bg-blue-500 w-2 h-12 rounded animate-pulse animation-delay-100"></div>
                <div className="bg-blue-500 w-2 h-10 rounded animate-pulse animation-delay-200"></div>
                <div className="bg-blue-500 w-2 h-14 rounded animate-pulse animation-delay-300"></div>
                <div className="bg-blue-500 w-2 h-8 rounded animate-pulse animation-delay-400"></div>
              </div>
              <p className="text-center mt-4 text-gray-600">Audio visualizer</p>
            </CardContent>
          </Card>

          {/* Slide In Animation */}
          <Card className="animate-slide-in-right">
            <CardHeader>
              <CardTitle>Slide In Effect</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">Smooth entrance animations</p>
              <div className="mt-4 space-y-2">
                <div className="bg-gray-200 h-2 rounded animate-slide-in-left"></div>
                <div className="bg-gray-300 h-2 rounded animate-slide-in-left animation-delay-100"></div>
                <div className="bg-gray-400 h-2 rounded animate-slide-in-left animation-delay-200"></div>
              </div>
            </CardContent>
          </Card>

          {/* Gradient Animation */}
          <Card>
            <CardHeader>
              <CardTitle>Gradient Flow</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-20 rounded-lg bg-gradient-to-r from-purple-400 via-pink-500 to-red-500 animate-gradient-x"></div>
              <p className="text-center mt-4 text-gray-600">Dynamic backgrounds</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Premium Card Stack Demo */}
      {activeDemo === 'premium' && (
        <div className="space-y-6">
          {/* Premium Card Stack */}
          <Card className="overflow-hidden">
            <CardHeader className="bg-gradient-to-r from-yellow-500 to-orange-500 text-white">
              <CardTitle className="flex items-center gap-2">
                💎 Premium 3D Card Stack
                <span className="text-sm bg-white/20 px-2 py-1 rounded-full">Draggable</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <PremiumCardStack />
            </CardContent>
          </Card>

          {/* InstaBids Themed Cards */}
          <Card>
            <CardHeader>
              <CardTitle>InstaBids Project Cards</CardTitle>
            </CardHeader>
            <CardContent>
              <InstaBidsCardStack />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Stats Section */}
      <Card>
        <CardHeader>
          <CardTitle>Platform Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
              <Home className="w-8 h-8 mx-auto mb-2 text-blue-600" />
              <p className="text-2xl font-bold text-blue-800">10,000+</p>
              <p className="text-sm text-blue-600">Projects</p>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
              <Users className="w-8 h-8 mx-auto mb-2 text-green-600" />
              <p className="text-2xl font-bold text-green-800">500+</p>
              <p className="text-sm text-green-600">Contractors</p>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
              <DollarSign className="w-8 h-8 mx-auto mb-2 text-purple-600" />
              <p className="text-2xl font-bold text-purple-800">$5M+</p>
              <p className="text-sm text-purple-600">Saved</p>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg">
              <TrendingUp className="w-8 h-8 mx-auto mb-2 text-orange-600" />
              <p className="text-2xl font-bold text-orange-800">4.8/5</p>
              <p className="text-sm text-orange-600">Rating</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Premium Card Stack Component
const PremiumCardStack: React.FC = () => {
  const frameRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState(false);
  const [pressing, setPressing] = useState(false);
  const [order, setOrder] = useState([0, 1, 2, 3]);

  // Long-press handling
  useEffect(() => {
    if (!pressing) return;
    const t = setTimeout(() => setExpanded((v) => !v), 350);
    return () => clearTimeout(t);
  }, [pressing]);

  const nextInStack = () => setOrder((o) => [...o.slice(1), o[0]]);
  const prevInStack = () => setOrder((o) => [o[o.length - 1], ...o.slice(0, -1)]);

  const cards = [
    {
      id: '1',
      title: 'Sunset Villa',
      subtitle: 'Luxury Home Renovation',
      image: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?q=80&w=1600&auto=format&fit=crop',
      price: '$125k',
      status: 'Active'
    },
    {
      id: '2', 
      title: 'Modern Kitchen',
      subtitle: 'Complete Remodel',
      image: 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?q=80&w=1600&auto=format&fit=crop',
      price: '$45k',
      status: 'Bidding'
    },
    {
      id: '3',
      title: 'Garden Paradise',
      subtitle: 'Landscape Design',
      image: 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?q=80&w=1600&auto=format&fit=crop',
      price: '$22k',
      status: 'Planning'
    },
    {
      id: '4',
      title: 'Pool & Spa',
      subtitle: 'Resort-Style Backyard',
      image: 'https://images.unsplash.com/photo-1571902943202-507ec2618e8f?q=80&w=1600&auto=format&fit=crop',
      price: '$85k',
      status: 'Review'
    }
  ];

  return (
    <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Project Cards</h3>
        <button
          onClick={() => setExpanded((v) => !v)}
          className="text-sm rounded-full px-3 py-1 bg-white shadow hover:shadow-md transition-shadow"
        >
          {expanded ? "Stack" : "Expand"}
        </button>
      </div>

      <div
        ref={frameRef}
        className="relative h-[400px] rounded-2xl bg-gradient-to-b from-white to-gray-50 overflow-hidden shadow-inner"
        style={{ perspective: '1200px' }}
      >
        <div className="absolute inset-0">
          {order.map((cardIndex, visualIndex) => (
            <PremiumCard
              key={cards[cardIndex].id}
              data={cards[cardIndex]}
              index={visualIndex}
              count={order.length}
              expanded={expanded}
              frameRef={frameRef}
              onPointerDown={() => setPressing(true)}
              onPointerUp={() => setPressing(false)}
              onPointerCancel={() => setPressing(false)}
            />
          ))}
        </div>

        {/* Navigation Controls */}
        <div className="absolute inset-y-0 left-0 right-0 flex items-center justify-between px-4 z-[1101]">
          <button
            onClick={prevInStack}
            className="h-10 w-10 grid place-items-center rounded-full bg-white/90 border shadow-lg hover:bg-white hover:scale-105 transition-all"
          >
            ←
          </button>
          <button
            onClick={nextInStack}
            className="h-10 w-10 grid place-items-center rounded-full bg-white/90 border shadow-lg hover:bg-white hover:scale-105 transition-all"
          >
            →
          </button>
        </div>
      </div>
      
      <p className="text-xs text-gray-500 mt-2">
        Use arrows to cycle cards • Click "Expand" to spread and drag individual cards
      </p>
    </div>
  );
};

// Individual Premium Card Component
const PremiumCard: React.FC<{
  data: any;
  index: number;
  count: number;
  expanded: boolean;
  frameRef: React.RefObject<HTMLDivElement>;
  onPointerDown?: () => void;
  onPointerUp?: () => void;
  onPointerCancel?: () => void;
}> = ({ data, index, count, expanded, frameRef, onPointerDown, onPointerUp, onPointerCancel }) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const xmv = useMotionValue(0);
  const ymv = useMotionValue(0);
  const xs = useSpring(xmv, { stiffness: 120, damping: 18, mass: 0.25 });
  const ys = useSpring(ymv, { stiffness: 120, damping: 18, mass: 0.25 });

  const rotX = useTransform(ys, [-80, 80], [6, -6]);
  const rotY = useTransform(xs, [-80, 80], [-6, 6]);

  const spread = expanded ? Math.min(14, 40 / Math.max(1, count)) : 4;
  const offset = expanded ? 26 : 10;
  const baseRotate = (index - (count - 1) / 2) * spread;
  const baseX = (index - (count - 1) / 2) * offset;
  const baseY = expanded ? 6 * Math.abs(index - (count - 1) / 2) : 0;

  const [isDragging, setDragging] = useState(false);

  const onMove = (e: React.PointerEvent) => {
    const r = cardRef.current?.getBoundingClientRect();
    if (!r) return;
    xmv.set(e.clientX - (r.left + r.width / 2));
    ymv.set(e.clientY - (r.top + r.height / 2));
  };
  
  const onLeave = () => {
    xmv.set(0);
    ymv.set(0);
  };

  return (
    <motion.div
      ref={cardRef}
      className="absolute left-1/2 top-1/2 w-72 -translate-x-1/2 -translate-y-1/2 rounded-2xl overflow-hidden select-none will-change-transform shadow-2xl"
      style={{ 
        zIndex: isDragging ? 1000 : 10 + index,
        transformStyle: 'preserve-3d',
        rotateX: rotX,
        rotateY: rotY
      }}
      initial={false}
      animate={{
        x: baseX,
        y: baseY,
        rotate: baseRotate,
        scale: expanded ? 1 : 0.98 - Math.abs(index - (count - 1) / 2) * 0.02,
      }}
      transition={{ type: "spring", stiffness: 260, damping: 26 }}
      drag={expanded}
      dragMomentum={false}
      dragElastic={0.18}
      dragConstraints={frameRef}
      onDragStart={() => setDragging(true)}
      onDragEnd={() => setDragging(false)}
      onPointerMove={onMove}
      onPointerLeave={onLeave}
      onPointerDown={onPointerDown}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerCancel}
      whileHover={{ z: 20, scale: 1.02 }}
      whileDrag={{ z: 40, scale: 1.05 }}
    >
      {/* Card Image */}
      <div className="relative h-48">
        <img
          src={data.image}
          alt={data.title}
          className="absolute inset-0 h-full w-full object-cover"
          draggable={false}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
        <div className="absolute top-3 right-3">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            data.status === 'Active' ? 'bg-green-500 text-white' :
            data.status === 'Bidding' ? 'bg-blue-500 text-white' :
            data.status === 'Planning' ? 'bg-yellow-500 text-black' :
            'bg-gray-500 text-white'
          }`}>
            {data.status}
          </span>
        </div>
      </div>

      {/* Card Content */}
      <div className="bg-white p-4">
        <h3 className="font-semibold text-lg text-gray-900">{data.title}</h3>
        <p className="text-gray-600 text-sm mb-3">{data.subtitle}</p>
        <div className="flex items-center justify-between">
          <span className="text-xl font-bold text-gray-900">{data.price}</span>
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4 text-yellow-500 fill-current" />
            <span className="text-sm text-gray-600">4.9</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// InstaBids Themed Card Stack
const InstaBidsCardStack: React.FC = () => {
  return (
    <div className="grid md:grid-cols-2 gap-6">
      <div className="space-y-4">
        <h4 className="font-medium text-gray-900">Traditional Cards</h4>
        <div className="grid gap-3">
          <div className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow">
            <h5 className="font-medium mb-2">Kitchen Remodel</h5>
            <p className="text-sm text-gray-600">Budget: $45,000 - $65,000</p>
            <p className="text-sm text-gray-500 mt-1">3 bids received</p>
          </div>
          <div className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow">
            <h5 className="font-medium mb-2">Bathroom Renovation</h5>
            <p className="text-sm text-gray-600">Budget: $15,000 - $25,000</p>
            <p className="text-sm text-gray-500 mt-1">1 bid received</p>
          </div>
        </div>
      </div>
      
      <div className="space-y-4">
        <h4 className="font-medium text-gray-900">Premium 3D Card Stacks</h4>
        <p className="text-sm text-gray-600">
          Premium card stacks with advanced 3D effects:
        </p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <h5 className="font-medium text-gray-800 mb-4">Single Project Cards</h5>
            <PremiumCardStack />
          </div>
          <div>
            <h5 className="font-medium text-gray-800 mb-4">Group Bidding Opportunities</h5>
            <GroupBiddingCardStack />
          </div>
        </div>
        <div className="mt-6">
          <h6 className="font-medium text-gray-700 mb-2">Features</h6>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Draggable card interactions with spring physics</li>
            <li>• 3D depth and perspective transformations</li>
            <li>• Mouse tilt responses and hover effects</li>
            <li>• Professional shadows with depth illusion</li>
            <li>• Bounded drag constraints and snap-back</li>
            <li>• Group cards show collaboration benefits</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

// Group Bidding Card Stack Component
const GroupBiddingCardStack: React.FC = () => {
  const frameRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState(false);
  const [order, setOrder] = useState([0, 1, 2, 3]);

  // Real bid card data structure matching the actual system
  const groupBidCards = [
    {
      id: "group-solar-001",
      bid_card_number: "BC-GRP-2025-001",
      project_type: "Solar Panel Installation",
      description: "Neighborhood-wide solar installation project with bulk pricing and coordinated permits for maximum savings.",
      budget_range: "$180,000 - $240,000",
      timeline: "6-8 weeks",
      service_complexity: "multi-trade",
      trade_count: 3,
      primary_trade: "Solar Installation",
      secondary_trades: ["Electrical", "Roofing", "Permits"],
      group_bid_eligible: true,
      group_project_count: 12,
      group_savings_percentage: "25%",
      location: "Sunset Ridge Community",
      urgency_level: "standard",
      coordinator: "Green Energy Solutions"
    },
    {
      id: "group-landscape-002", 
      bid_card_number: "BC-GRP-2025-002",
      project_type: "Landscaping",
      description: "Multi-home landscaping transformation including hardscaping, irrigation, and seasonal plantings across multiple properties.",
      budget_range: "$64,000 - $96,000",
      timeline: "4-6 weeks",
      service_complexity: "multi-trade",
      trade_count: 2,
      primary_trade: "Landscaping",
      secondary_trades: ["Irrigation", "Hardscaping"],
      group_bid_eligible: true,
      group_project_count: 8,
      group_savings_percentage: "20%",
      location: "Riverside Estates",
      urgency_level: "standard",
      coordinator: "Premier Landscape Co."
    },
    {
      id: "group-roofing-003",
      bid_card_number: "BC-GRP-2025-003", 
      project_type: "Roof Replacement",
      description: "Community roof replacement project with coordinated timeline and bulk material procurement for heritage neighborhood.",
      budget_range: "$120,000 - $150,000",
      timeline: "3-4 weeks",
      service_complexity: "single-trade",
      trade_count: 1,
      primary_trade: "Roofing", 
      secondary_trades: [],
      group_bid_eligible: true,
      group_project_count: 6,
      group_savings_percentage: "22%",
      location: "Heritage Village",
      urgency_level: "urgent",
      coordinator: "Elite Roofing Contractors"
    },
    {
      id: "group-hvac-004",
      bid_card_number: "BC-GRP-2025-004",
      project_type: "HVAC System Upgrade", 
      description: "Neighborhood HVAC system modernization with high-efficiency units and smart thermostat installation.",
      budget_range: "$80,000 - $120,000",
      timeline: "5-7 weeks",
      service_complexity: "multi-trade",
      trade_count: 2,
      primary_trade: "HVAC",
      secondary_trades: ["Electrical", "Smart Home"],
      group_bid_eligible: true,
      group_project_count: 10,
      group_savings_percentage: "18%", 
      location: "Oakwood Heights",
      urgency_level: "standard",
      coordinator: "Climate Pro Systems"
    }
  ];

  const currentCards = order.map(index => groupBidCards[index]);
  const visibleCards = expanded ? currentCards : currentCards.slice(0, 3);

  const navigateCards = (direction: 'prev' | 'next') => {
    setOrder(prev => {
      const newOrder = [...prev];
      if (direction === 'next') {
        const firstCard = newOrder.shift()!;
        newOrder.push(firstCard);
      } else {
        const lastCard = newOrder.pop()!;
        newOrder.unshift(lastCard);
      }
      return newOrder;
    });
  };

  return (
    <div 
      ref={frameRef}
      className="relative w-full h-96 flex items-center justify-center"
      style={{ perspective: '1000px' }}
    >
      <div className="relative flex items-center justify-center">
        {visibleCards.map((bidCard, index) => (
          <GroupBiddingCard
            key={bidCard.id}
            bidCard={bidCard}
            index={index}
            total={visibleCards.length}
            frameRef={frameRef}
          />
        ))}
      </div>

      {/* Navigation Controls */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-4 z-20">
        <button
          onClick={() => navigateCards('prev')}
          className="px-4 py-2 bg-black/80 text-white rounded-lg hover:bg-black transition-colors"
        >
          Previous
        </button>
        <button
          onClick={() => setExpanded(!expanded)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          {expanded ? 'Collapse' : 'Expand'}
        </button>
        <button
          onClick={() => navigateCards('next')}
          className="px-4 py-2 bg-black/80 text-white rounded-lg hover:bg-black transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  );
};

// Group Bidding Card Component
interface GroupBiddingCardProps {
  bidCard: any;
  index: number;
  total: number;
  frameRef: React.RefObject<HTMLDivElement>;
}

const GroupBiddingCard: React.FC<GroupBiddingCardProps> = ({ 
  bidCard, 
  index, 
  total, 
  frameRef 
}) => {
  const cardRef = useRef<HTMLDivElement>(null);

  const x = useMotionValue(0);
  const y = useMotionValue(0);
  
  const springConfig = { stiffness: 400, damping: 30 };
  const springX = useSpring(x, springConfig);
  const springY = useSpring(y, springConfig);

  const rotateX = useTransform(springY, [-100, 100], [10, -10]);
  const rotateY = useTransform(springX, [-100, 100], [-10, 10]);

  const baseZ = -index * 30;
  const baseScale = 1 - index * 0.05;
  const baseOpacity = 1 - index * 0.1;

  const handleMouseMove = (event: MouseEvent) => {
    if (!cardRef.current || !frameRef.current) return;
    
    const card = cardRef.current;
    const frame = frameRef.current;
    
    const cardRect = card.getBoundingClientRect();
    const frameRect = frame.getBoundingClientRect();
    
    const cardCenterX = cardRect.left + cardRect.width / 2;
    const cardCenterY = cardRect.top + cardRect.height / 2;
    
    const deltaX = event.clientX - cardCenterX;
    const deltaY = event.clientY - cardCenterY;
    
    x.set(deltaX * 0.3);
    y.set(deltaY * 0.3);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  const constraints = frameRef.current ? {
    left: -150,
    right: 150,
    top: -100,
    bottom: 100
  } : {};

  return (
    <motion.div
      ref={cardRef}
      drag
      dragConstraints={constraints}
      dragElastic={0.2}
      whileDrag={{ 
        scale: 1.1, 
        zIndex: 50,
        rotateZ: 5
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        x: springX,
        y: springY,
        rotateX,
        rotateY,
        z: baseZ,
        scale: baseScale,
        opacity: baseOpacity,
        transformStyle: 'preserve-3d'
      }}
      className="absolute w-80 h-64 cursor-grab active:cursor-grabbing"
      initial={{ 
        x: index * 20, 
        y: index * 10,
        scale: baseScale,
        opacity: baseOpacity 
      }}
      animate={{ 
        x: index * 20, 
        y: index * 10,
        scale: baseScale,
        opacity: baseOpacity 
      }}
      transition={{ 
        type: "spring", 
        stiffness: 300, 
        damping: 30 
      }}
    >
      <div 
        className="w-full h-full rounded-2xl p-6 text-white relative overflow-hidden"
        style={{
          background: index === 0 
            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
            : index === 1 
            ? 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
            : index === 2
            ? 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
            : 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
          boxShadow: `
            0 10px 30px rgba(0,0,0,0.3),
            0 1px 8px rgba(0,0,0,0.2),
            inset 0 1px 0 rgba(255,255,255,0.1)
          `
        }}
      >
        {/* Group Savings Badge */}
        <div className="absolute top-4 right-4 bg-green-400 text-green-900 px-3 py-1 rounded-full text-xs font-semibold">
          {bidCard.group_savings_percentage} SAVINGS
        </div>

        {/* Bid Card Number */}
        <div className="absolute top-4 left-4 text-xs opacity-75">
          {bidCard.bid_card_number}
        </div>

        {/* Project Type & Details */}
        <div className="mt-8 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              bidCard.service_complexity === "single-trade" 
                ? "bg-white/20 text-white" 
                : bidCard.service_complexity === "multi-trade" 
                ? "bg-white/30 text-white" 
                : "bg-white/40 text-white"
            }`}>
              {bidCard.service_complexity === "single-trade" && "Single Trade"}
              {bidCard.service_complexity === "multi-trade" && "Multi Trade"}
              {bidCard.service_complexity === "complex-coordination" && "Complex Project"}
            </span>
            {bidCard.urgency_level === "urgent" && (
              <span className="px-2 py-1 bg-red-400 text-red-900 rounded-full text-xs font-medium">
                URGENT
              </span>
            )}
          </div>
          <h3 className="text-xl font-bold leading-tight">{bidCard.project_type}</h3>
          <p className="text-sm opacity-90 mt-1">{bidCard.group_project_count} homes • Group Project</p>
        </div>

        {/* Description */}
        <p className="text-sm opacity-90 mb-4 line-clamp-2">{bidCard.description}</p>

        {/* Trade Information */}
        {bidCard.secondary_trades && bidCard.secondary_trades.length > 0 && (
          <div className="mb-4">
            <p className="text-xs opacity-80 mb-2">Trades needed:</p>
            <div className="flex flex-wrap gap-1">
              <span className="text-xs bg-white/30 rounded-full px-2 py-1">
                {bidCard.primary_trade}
              </span>
              {bidCard.secondary_trades.slice(0, 2).map((trade: string, i: number) => (
                <span key={i} className="text-xs bg-white/20 rounded-full px-2 py-1">
                  {trade}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Budget and Timeline */}
        <div className="absolute bottom-4 left-6 right-6">
          <div className="flex justify-between items-center text-sm mb-1">
            <span className="font-semibold">{bidCard.budget_range}</span>
            <span className="opacity-90">{bidCard.timeline}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="opacity-80">{bidCard.location}</span>
            <span className="opacity-80">{bidCard.coordinator}</span>
          </div>
        </div>

        {/* Decorative Elements */}
        <div 
          className="absolute -right-16 -top-16 w-32 h-32 rounded-full opacity-10"
          style={{ backgroundColor: 'white' }}
        />
        <div 
          className="absolute -left-8 -bottom-8 w-24 h-24 rounded-full opacity-10"
          style={{ backgroundColor: 'white' }}
        />
      </div>
    </motion.div>
  );
};

export default UITestingShowcase;