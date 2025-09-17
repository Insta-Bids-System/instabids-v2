import React, { useState, useEffect, useCallback } from 'react';
import {
  Search,
  MapPin,
  Users,
  Package,
  Clock,
  DollarSign,
  Filter,
  ChevronRight,
  Sliders,
  Building2,
  Calendar,
  AlertCircle,
  CheckCircle2,
  Eye,
  Plus,
  X
} from 'lucide-react';
import { useBidCard } from '../../contexts/BidCardContext';
import { BidCardMarketplace } from './BidCardMarketplace';
import type { MarketplaceBidCardView } from '../../types/bidCard';

interface GroupPool {
  id: string;
  category_id: string;
  category_name: string;
  category_icon: string;
  zip_code: string;
  city?: string;
  state?: string;
  member_count: number;
  target_member_count: number;
  pool_status: string;
  created_at: string;
  estimated_savings_percentage: number;
  distance_miles?: number | null;
  bid_cards?: any[]; // Array of actual bid cards from the database
}

interface PoolProject {
  id: string;
  homeowner_id: string;
  pool_id: string;
  property_address?: string;
  property_details?: any;
  preferred_schedule?: any;
  budget_range?: any;
  join_status: string;
  joined_at: string;
  selected?: boolean;
}

interface EnhancedBidCardMarketplaceProps {
  contractorId?: string;
  userType?: string;
}

export const EnhancedBidCardMarketplace: React.FC<EnhancedBidCardMarketplaceProps> = ({
  contractorId,
  userType
}) => {
  const [activeTab, setActiveTab] = useState<'individual' | 'group'>('individual');
  const [pools, setPools] = useState<GroupPool[]>([]);
  const [selectedPool, setSelectedPool] = useState<GroupPool | null>(null);
  const [poolProjects, setPoolProjects] = useState<PoolProject[]>([]);
  const [selectedProjects, setSelectedProjects] = useState<Set<string>>(new Set());
  const [isLoadingPools, setIsLoadingPools] = useState(false);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);
  
  // Group bidding filters
  const [groupFilters, setGroupFilters] = useState({
    category: 'all',
    radius: 10,
    minMembers: 3,
    zipCode: '',
    showProjectSelection: false
  });

  // Interactive radius control
  const [mapCenter, setMapCenter] = useState<{ lat: number; lng: number } | null>(null);
  const [isDraggingRadius, setIsDraggingRadius] = useState(false);

  const serviceCategories = [
    { id: 'all', name: 'All Services', icon: '🏠' },
    { id: 'lawn-care', name: 'Lawn Care', icon: '🌱' },
    { id: 'pool-service', name: 'Pool Service', icon: '🏊' },
    { id: 'ac-replacement', name: 'AC Replacement', icon: '❄️' },
    { id: 'roof-replacement', name: 'Roof Replacement', icon: '🏠' },
    { id: 'artificial-turf', name: 'Artificial Turf', icon: '🌿' }
  ];

  const radiusOptions = [5, 10, 15, 20, 25, 30];

  useEffect(() => {
    if (activeTab === 'group') {
      loadGroupPools();
    }
  }, [activeTab, groupFilters]);

  const loadGroupPools = async () => {
    setIsLoadingPools(true);
    try {
      const params = new URLSearchParams({
        category: groupFilters.category,
        radius: groupFilters.radius.toString(),
        ...(groupFilters.zipCode && { zip_code: groupFilters.zipCode })
      });
      // Note: Removed min_members since we're now searching actual bid cards, not pools

      // Use the new endpoint that searches actual bid_cards table
      const response = await fetch(`/api/contractor/group-eligible-bid-cards?${params}`);
      if (response.ok) {
        const data = await response.json();
        
        // Transform bid cards into pool-like structure for UI
        const transformedPools = data.location_groups?.map((group: any) => ({
          id: `pool-${group.location.replace(/\s/g, '-')}-${group.project_type}`,
          category_name: group.project_type,
          category_icon: getCategoryIcon(group.project_type),
          zip_code: extractZipCode(group.location),
          city: group.location.split(',')[0],
          state: group.location.split(',')[1]?.trim().split(' ')[0],
          member_count: group.bid_cards.length,
          target_member_count: 5,
          pool_status: 'forming',
          created_at: new Date().toISOString(),
          estimated_savings_percentage: group.bid_cards.length >= 8 ? 25 : 
                                       group.bid_cards.length >= 5 ? 20 : 15,
          distance_miles: group.bid_cards[0]?.distance_miles || null,
          bid_cards: group.bid_cards // Keep original bid cards for selection
        })) || [];
        
        // Sort pools by distance for better visualization
        if (transformedPools.length > 0) {
          const sortedPools = [...transformedPools].sort((a, b) => 
            (a.distance_miles || 999) - (b.distance_miles || 999)
          );
          setPools(sortedPools);
        } else {
          setPools([]);
        }
      }
    } catch (error) {
      console.error('Error loading group-eligible bid cards:', error);
    } finally {
      setIsLoadingPools(false);
    }
  };
  
  // Helper function to get category icon
  const getCategoryIcon = (projectType: string): string => {
    const type = projectType.toLowerCase();
    if (type.includes('lawn') || type.includes('grass')) return '🌱';
    if (type.includes('pool')) return '🏊';
    if (type.includes('hvac') || type.includes('ac')) return '❄️';
    if (type.includes('roof')) return '🏠';
    if (type.includes('turf') || type.includes('artificial')) return '🌿';
    if (type.includes('landscap') || type.includes('garden')) return '🌳';
    return '🏗️';
  };
  
  // Helper function to extract ZIP code from location string
  const extractZipCode = (location: string): string => {
    const parts = location.split(' ');
    const zipCode = parts[parts.length - 1];
    return /^\d{5}$/.test(zipCode) ? zipCode : '';
  };

  const loadPoolProjects = async (poolId: string) => {
    setIsLoadingProjects(true);
    try {
      // Since we now have bid_cards directly in the pool object, use them
      const pool = pools.find(p => p.id === poolId);
      if (pool && pool.bid_cards) {
        // Transform bid cards into project format
        const projects = pool.bid_cards.map((card: any) => ({
          id: card.id,
          homeowner_id: card.homeowner_id,
          pool_id: poolId,
          property_address: `${card.location_city}, ${card.location_state} ${card.location_zip}`,
          property_details: {
            project_type: card.project_type,
            description: card.description || card.title,
            urgency: card.urgency_level
          },
          preferred_schedule: {
            timeline: card.urgency_level === 'emergency' ? 'immediate' :
                     card.urgency_level === 'urgent' ? 'within_week' : 'flexible'
          },
          budget_range: card.budget_min && card.budget_max ? {
            min: card.budget_min,
            max: card.budget_max
          } : null,
          join_status: 'interested',
          joined_at: card.created_at
        }));
        
        setPoolProjects(projects);
        setGroupFilters(prev => ({ ...prev, showProjectSelection: true }));
      }
    } catch (error) {
      console.error('Error loading pool projects:', error);
    } finally {
      setIsLoadingProjects(false);
    }
  };

  const handleProjectToggle = (projectId: string) => {
    setSelectedProjects(prev => {
      const newSet = new Set(prev);
      if (newSet.has(projectId)) {
        newSet.delete(projectId);
      } else {
        newSet.add(projectId);
      }
      return newSet;
    });
  };

  const handleCreateGroupPackage = async () => {
    if (!selectedPool || selectedProjects.size === 0) return;

    try {
      const response = await fetch('/api/contractor/group-packages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pool_id: selectedPool.id,
          selected_project_ids: Array.from(selectedProjects),
          package_name: `${selectedPool.category_name} Group Package`,
          discount_percentage: calculateDiscount(selectedProjects.size),
          contractor_notes: `Group package for ${selectedProjects.size} projects in ${selectedPool.zip_code} area`
        })
      });

      if (response.ok) {
        const result = await response.json();
        // Trigger BSA agent for group bid submission
        window.location.href = `/contractor/dashboard?tab=chat&group_package=${result.package_id}`;
      }
    } catch (error) {
      console.error('Error creating group package:', error);
    }
  };

  const calculateDiscount = (projectCount: number): number => {
    if (projectCount >= 8) return 25;
    if (projectCount >= 5) return 20;
    if (projectCount >= 3) return 15;
    return 10;
  };

  const getPoolStatusColor = (status: string) => {
    switch (status) {
      case 'forming': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'ready': return 'bg-green-100 text-green-800 border-green-200';
      case 'active': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* Header with Tabs */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center space-x-8">
              <h1 className="text-2xl font-bold text-gray-900">Bid Marketplace</h1>
              
              {/* Tab Navigation */}
              <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
                <button
                  onClick={() => setActiveTab('individual')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    activeTab === 'individual'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Building2 className="w-4 h-4" />
                    <span>Individual Projects</span>
                  </div>
                </button>
                <button
                  onClick={() => setActiveTab('group')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    activeTab === 'group'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Users className="w-4 h-4" />
                    <span>Group Opportunities</span>
                    {pools.length > 0 && (
                      <span className="bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">
                        {pools.length}
                      </span>
                    )}
                  </div>
                </button>
              </div>
            </div>

            {/* Quick Stats */}
            {activeTab === 'group' && pools.length > 0 && (
              <div className="flex items-center space-x-4 text-sm">
                <div className="flex items-center space-x-1">
                  <MapPin className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">
                    {pools.filter(p => p.distance_miles && p.distance_miles <= 10).length} pools within 10mi
                  </span>
                </div>
                <div className="flex items-center space-x-1">
                  <Package className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">
                    {pools.reduce((sum, p) => sum + p.member_count, 0)} total projects
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'individual' ? (
          <BidCardMarketplace contractorId={contractorId} userType={userType} />
        ) : (
          <div className="space-y-6">
            {/* Group Bidding Filters */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                {/* Service Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Service Category
                  </label>
                  <select
                    value={groupFilters.category}
                    onChange={(e) => setGroupFilters(prev => ({ ...prev, category: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {serviceCategories.map(cat => (
                      <option key={cat.id} value={cat.id}>
                        {cat.icon} {cat.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* ZIP Code Search */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ZIP Code
                  </label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                      type="text"
                      placeholder="Enter ZIP"
                      value={groupFilters.zipCode}
                      onChange={(e) => setGroupFilters(prev => ({ ...prev, zipCode: e.target.value }))}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                {/* Radius Slider */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Search Radius: {groupFilters.radius} miles
                  </label>
                  <input
                    type="range"
                    min="5"
                    max="30"
                    step="5"
                    value={groupFilters.radius}
                    onChange={(e) => setGroupFilters(prev => ({ ...prev, radius: parseInt(e.target.value) }))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>5mi</span>
                    <span>15mi</span>
                    <span>30mi</span>
                  </div>
                </div>

                {/* Min Members */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Min Members
                  </label>
                  <select
                    value={groupFilters.minMembers}
                    onChange={(e) => setGroupFilters(prev => ({ ...prev, minMembers: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={3}>3+ members</option>
                    <option value={5}>5+ members</option>
                    <option value={8}>8+ members</option>
                  </select>
                </div>

                {/* Apply Filters Button */}
                <div className="flex items-end">
                  <button
                    onClick={loadGroupPools}
                    className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center"
                  >
                    <Filter className="w-4 h-4 mr-2" />
                    Apply Filters
                  </button>
                </div>
              </div>

              {/* Visual Radius Indicator */}
              {groupFilters.zipCode && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-blue-800">
                      Searching within {groupFilters.radius} miles of ZIP {groupFilters.zipCode}
                    </span>
                    <div className="flex items-center space-x-2">
                      {radiusOptions.map(radius => (
                        <button
                          key={radius}
                          onClick={() => setGroupFilters(prev => ({ ...prev, radius }))}
                          className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                            groupFilters.radius === radius
                              ? 'bg-blue-600 text-white'
                              : 'bg-white text-blue-600 border border-blue-300 hover:bg-blue-50'
                          }`}
                        >
                          {radius}mi
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Pools Grid or Project Selection */}
            {!groupFilters.showProjectSelection ? (
              <>
                {/* Pool Cards Grid */}
                {isLoadingPools ? (
                  <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="ml-3 text-gray-600">Loading group opportunities...</span>
                  </div>
                ) : pools.length === 0 ? (
                  <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
                    <Users className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No group pools found</h3>
                    <p className="text-gray-600">
                      Try adjusting your filters or expanding your search radius
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {pools.map((pool) => (
                      <div
                        key={pool.id}
                        className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-all cursor-pointer"
                        onClick={() => {
                          setSelectedPool(pool);
                          loadPoolProjects(pool.id);
                        }}
                      >
                        <div className="p-6">
                          {/* Pool Header */}
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center">
                              <div className="text-3xl mr-3">{pool.category_icon}</div>
                              <div>
                                <h3 className="text-lg font-semibold text-gray-900">
                                  {pool.category_name}
                                </h3>
                                <div className="flex items-center text-sm text-gray-600">
                                  <MapPin className="w-4 h-4 mr-1" />
                                  {pool.city ? `${pool.city}, ` : ''}{pool.zip_code}
                                  {pool.distance_miles !== undefined && (
                                    <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-xs">
                                      {pool.distance_miles ? `${pool.distance_miles.toFixed(1)} mi away` : 'In your area'}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPoolStatusColor(pool.pool_status)}`}>
                              {pool.pool_status}
                            </span>
                          </div>

                          {/* Pool Stats */}
                          <div className="grid grid-cols-2 gap-4 mb-4">
                            <div className="bg-gray-50 rounded-lg p-3">
                              <div className="flex items-center justify-center text-blue-600 mb-1">
                                <Users className="w-4 h-4 mr-1" />
                                <span className="text-xl font-bold">{pool.member_count}</span>
                              </div>
                              <p className="text-xs text-gray-600 text-center">Projects</p>
                            </div>
                            <div className="bg-gray-50 rounded-lg p-3">
                              <div className="flex items-center justify-center text-green-600 mb-1">
                                <DollarSign className="w-4 h-4 mr-1" />
                                <span className="text-xl font-bold">{pool.estimated_savings_percentage}%</span>
                              </div>
                              <p className="text-xs text-gray-600 text-center">Savings</p>
                            </div>
                          </div>

                          {/* Progress Bar */}
                          <div className="mb-4">
                            <div className="flex justify-between text-xs text-gray-600 mb-1">
                              <span>Pool Progress</span>
                              <span>{pool.member_count}/{pool.target_member_count} members</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full transition-all"
                                style={{ width: `${(pool.member_count / pool.target_member_count) * 100}%` }}
                              />
                            </div>
                          </div>

                          {/* Action Buttons */}
                          <div className="flex space-x-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedPool(pool);
                                loadPoolProjects(pool.id);
                              }}
                              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center text-sm font-medium"
                            >
                              <Eye className="w-4 h-4 mr-2" />
                              View Projects
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                // Quick view without full selection
                              }}
                              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors"
                            >
                              <ChevronRight className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : (
              /* Project Selection View */
              <div className="bg-white rounded-lg shadow-sm border">
                {/* Selection Header */}
                <div className="border-b px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <button
                        onClick={() => {
                          setGroupFilters(prev => ({ ...prev, showProjectSelection: false }));
                          setSelectedProjects(new Set());
                        }}
                        className="text-gray-500 hover:text-gray-700"
                      >
                        <X className="w-5 h-5" />
                      </button>
                      <div>
                        <h2 className="text-xl font-semibold text-gray-900">
                          Select Projects for Group Package
                        </h2>
                        <p className="text-sm text-gray-600 mt-1">
                          {selectedPool?.category_name} in {selectedPool?.zip_code} area
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-sm text-gray-600">
                        <span className="font-medium">{selectedProjects.size}</span> of {poolProjects.length} selected
                      </div>
                      {selectedProjects.size >= 3 && (
                        <div className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                          {calculateDiscount(selectedProjects.size)}% Group Discount
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Projects List */}
                <div className="divide-y max-h-96 overflow-y-auto">
                  {isLoadingProjects ? (
                    <div className="flex justify-center items-center py-12">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                  ) : (
                    poolProjects.map((project) => (
                      <div
                        key={project.id}
                        className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                          selectedProjects.has(project.id) ? 'bg-blue-50' : ''
                        }`}
                        onClick={() => handleProjectToggle(project.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                              selectedProjects.has(project.id)
                                ? 'bg-blue-600 border-blue-600'
                                : 'border-gray-300'
                            }`}>
                              {selectedProjects.has(project.id) && (
                                <CheckCircle2 className="w-3 h-3 text-white" />
                              )}
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">
                                {project.property_address || `Property ${project.id.slice(0, 8)}`}
                              </p>
                              <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                                {project.property_details?.size && (
                                  <span>Size: {project.property_details.size}</span>
                                )}
                                {project.budget_range && (
                                  <span>Budget: {project.budget_range}</span>
                                )}
                                {project.preferred_schedule && (
                                  <span className="flex items-center">
                                    <Calendar className="w-3 h-3 mr-1" />
                                    {project.preferred_schedule.timeframe || 'Flexible'}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="text-sm text-gray-500">
                            Joined {new Date(project.joined_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>

                {/* Action Footer */}
                <div className="border-t px-6 py-4 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-600">
                      {selectedProjects.size < 3 && (
                        <div className="flex items-center text-amber-600">
                          <AlertCircle className="w-4 h-4 mr-2" />
                          Select at least 3 projects to create a group package
                        </div>
                      )}
                    </div>
                    <div className="flex space-x-3">
                      <button
                        onClick={() => {
                          setGroupFilters(prev => ({ ...prev, showProjectSelection: false }));
                          setSelectedProjects(new Set());
                        }}
                        className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleCreateGroupPackage}
                        disabled={selectedProjects.size < 3}
                        className={`px-6 py-2 rounded-md font-medium transition-colors flex items-center ${
                          selectedProjects.size >= 3
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        }`}
                      >
                        <Package className="w-4 h-4 mr-2" />
                        Create Group Package ({selectedProjects.size} projects)
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedBidCardMarketplace;