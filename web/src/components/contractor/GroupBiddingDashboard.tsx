import React, { useState, useEffect } from 'react';
import { 
  Users, 
  MapPin, 
  Clock, 
  Eye, 
  Package,
  Filter,
  Search
} from 'lucide-react';

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
  distance_miles?: number;
}

interface GroupBiddingDashboardProps {
  contractorId: string;
}

const GroupBiddingDashboard: React.FC<GroupBiddingDashboardProps> = ({ contractorId }) => {
  const [pools, setPools] = useState<GroupPool[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchRadius, setSearchRadius] = useState<number>(10);
  const [minMembers, setMinMembers] = useState<number>(3);
  const [searchZip, setSearchZip] = useState<string>('');

  const serviceCategories = [
    { id: 'all', name: 'All Services', icon: '🏠' },
    { id: 'lawn-care', name: 'Lawn Care', icon: '🌱' },
    { id: 'pool-service', name: 'Pool Service', icon: '🏊' },
    { id: 'ac-replacement', name: 'AC Replacement', icon: '❄️' },
    { id: 'roof-replacement', name: 'Roof Replacement', icon: '🏠' },
    { id: 'artificial-turf', name: 'Artificial Turf', icon: '🌿' }
  ];

  useEffect(() => {
    loadAvailablePools();
  }, [selectedCategory, searchRadius, minMembers, searchZip]);

  const loadAvailablePools = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        category: selectedCategory,
        radius: searchRadius.toString(),
        min_members: minMembers.toString(),
        ...(searchZip && { zip_code: searchZip })
      });

      const response = await fetch(`/api/contractor/group-pools?${params}`);
      if (response.ok) {
        const data = await response.json();
        setPools(data.pools || []);
      } else {
        console.error('Failed to load pools');
        setPools([]);
      }
    } catch (error) {
      console.error('Error loading pools:', error);
      setPools([]);
    } finally {
      setLoading(false);
    }
  };

  const handleViewProjects = async (poolId: string) => {
    try {
      const response = await fetch(`/api/contractor/group-pools/${poolId}/projects`);
      if (response.ok) {
        const data = await response.json();
        // Navigate to project selection interface
        window.location.href = `/contractor/group-bidding/pool/${poolId}/projects`;
      }
    } catch (error) {
      console.error('Error loading pool projects:', error);
    }
  };


  const getStatusColor = (status: string) => {
    switch (status) {
      case 'forming': return 'bg-yellow-100 text-yellow-800';
      case 'ready': return 'bg-green-100 text-green-800';
      case 'active': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Group Bidding Opportunities
          </h1>
          <p className="text-gray-600">
            Browse available project pools and create group packages for increased efficiency
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Service Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Service Category
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {serviceCategories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.icon} {category.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Search Radius */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Radius
              </label>
              <select
                value={searchRadius}
                onChange={(e) => setSearchRadius(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={5}>5 miles</option>
                <option value={10}>10 miles</option>
                <option value={15}>15 miles</option>
                <option value={20}>20 miles</option>
                <option value={30}>30 miles</option>
              </select>
            </div>

            {/* Minimum Members */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Min Members
              </label>
              <select
                value={minMembers}
                onChange={(e) => setMinMembers(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={3}>3+ members</option>
                <option value={5}>5+ members</option>
                <option value={8}>8+ members</option>
                <option value={10}>10+ members</option>
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
                  placeholder="Enter ZIP code"
                  value={searchZip}
                  onChange={(e) => setSearchZip(e.target.value)}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Pool Grid */}
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading available pools...</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {pools.length === 0 ? (
              <div className="col-span-full text-center py-12">
                <Users className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No pools found</h3>
                <p className="text-gray-600">
                  Try adjusting your filters or check back later for new opportunities
                </p>
              </div>
            ) : (
              pools.map((pool) => (
                <div
                  key={pool.id}
                  className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow p-6"
                >
                  {/* Pool Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center">
                      <div className="text-2xl mr-3">{pool.category_icon}</div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          {pool.category_name}
                        </h3>
                        <div className="flex items-center text-sm text-gray-600">
                          <MapPin className="w-4 h-4 mr-1" />
                          {pool.city ? `${pool.city}, ` : ''}{pool.zip_code}
                          {pool.distance_miles !== undefined && (
                            <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                              {pool.distance_miles.toFixed(1)} mi
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(pool.pool_status)}`}>
                      {pool.pool_status}
                    </span>
                  </div>

                  {/* Pool Stats */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="text-center">
                      <div className="flex items-center justify-center text-blue-600 mb-1">
                        <Users className="w-4 h-4 mr-1" />
                        <span className="text-lg font-bold">{pool.member_count}</span>
                      </div>
                      <p className="text-xs text-gray-600">Members</p>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center justify-center text-purple-600 mb-1">
                        <Package className="w-4 h-4 mr-1" />
                        <span className="text-lg font-bold">{pool.target_member_count}</span>
                      </div>
                      <p className="text-xs text-gray-600">Target Size</p>
                    </div>
                  </div>

                  {/* Savings Potential */}
                  {pool.estimated_savings_percentage > 0 && (
                    <div className="bg-green-50 rounded-lg p-3 mb-4">
                      <div className="flex items-center justify-center">
                        <Package className="w-4 h-4 text-green-600 mr-2" />
                        <span className="text-sm font-medium text-green-800">
                          Up to {pool.estimated_savings_percentage}% Group Discount Available
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Created Date */}
                  <div className="flex items-center text-xs text-gray-500 mb-4">
                    <Clock className="w-3 h-3 mr-1" />
                    Created {new Date(pool.created_at).toLocaleDateString()}
                  </div>

                  {/* Actions */}
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleViewProjects(pool.id)}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center justify-center"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      View Projects
                    </button>
                    <button
                      onClick={() => handleViewProjects(pool.id)}
                      className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md text-sm font-medium transition-colors"
                    >
                      <Package className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default GroupBiddingDashboard;