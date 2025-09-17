import React, { useState, useEffect } from 'react';
import { Users, DollarSign, Clock, CheckCircle, Plus } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '@/contexts/AuthContext';

interface ServiceCategory {
  id: string;
  category_code: string;
  display_name: string;
  description: string;
  service_type: string;
  frequency?: string;
  typical_price_min: number;
  typical_price_max: number;
  icon_name: string;
  sort_order: number;
  is_active: boolean;
  service_complexity: string;
  primary_trade: string;
  group_discount_tiers: { [key: string]: number };
}

interface LocalPool {
  id: string;
  category_id: string;
  member_count: number;
  target_member_count: number;
  pool_status: string;
  category_name: string;
  category_icon: string;
  primary_trade: string;
}

interface LocalStats {
  category_id: string;
  zip_code: string;
  active_pools: number;
  total_active_members: number;
  completed_pools: number;
  potential_savings_percentage: number;
  next_group_starts: string;
  spots_remaining: number;
}

const PopularServicesTab: React.FC = () => {
  const { user } = useAuth();
  const [categories, setCategories] = useState<ServiceCategory[]>([]);
  const [localPools, setLocalPools] = useState<{ [key: string]: LocalPool[] }>({});
  const [localStats, setLocalStats] = useState<{ [key: string]: LocalStats }>({});
  const [loading, setLoading] = useState(true);
  const [userZipCode, setUserZipCode] = useState('33101'); // Default to Miami for demo

  useEffect(() => {
    loadServiceCategories();
  }, []);

  useEffect(() => {
    if (categories.length > 0 && userZipCode) {
      loadLocalData();
    }
  }, [categories, userZipCode]);

  const loadServiceCategories = async () => {
    try {
      const response = await fetch('/api/group-categories');
      if (response.ok) {
        const data = await response.json();
        setCategories(data);
        console.log('Loaded service categories:', data);
      } else {
        throw new Error('Failed to load categories');
      }
    } catch (error) {
      console.error('Error loading service categories:', error);
      toast.error('Failed to load service categories');
    }
  };

  const loadLocalData = async () => {
    try {
      // Load local pools for all categories
      const response = await fetch(`/api/group-pools/local?zip_code=${userZipCode}`);
      if (response.ok) {
        const data = await response.json();
        // Group pools by category
        const poolsByCategory: { [key: string]: LocalPool[] } = {};
        data.pools.forEach((pool: LocalPool) => {
          if (!poolsByCategory[pool.category_id]) {
            poolsByCategory[pool.category_id] = [];
          }
          poolsByCategory[pool.category_id].push(pool);
        });
        setLocalPools(poolsByCategory);
      }

      // Load local stats for each category
      const statsPromises = categories.map(async (category) => {
        const statsResponse = await fetch(
          `/api/group-categories/${category.id}/local-stats?zip_code=${userZipCode}`
        );
        if (statsResponse.ok) {
          const stats = await statsResponse.json();
          return { categoryId: category.id, stats };
        }
        return null;
      });

      const statsResults = await Promise.all(statsPromises);
      const statsMap: { [key: string]: LocalStats } = {};
      statsResults.forEach((result) => {
        if (result) {
          statsMap[result.categoryId] = result.stats;
        }
      });
      setLocalStats(statsMap);
    } catch (error) {
      console.error('Error loading local data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleJoinOrCreatePool = async (category: ServiceCategory) => {
    if (!user) {
      toast.error('Please sign in to join a group');
      return;
    }

    try {
      const response = await fetch('/api/group-pools/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          category_id: category.id,
          zip_code: userZipCode,
          city: 'Miami', // Could be dynamic based on ZIP
          state: 'FL',
          homeowner_id: user.id,
          property_address: '123 Main St', // Could be from user profile
        }),
      });

      if (response.ok) {
        const result = await response.json();
        toast.success(result.message);
        
        // Reload local data to show updated member counts
        await loadLocalData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to join group');
      }
    } catch (error) {
      console.error('Error joining group:', error);
      toast.error('Failed to join group');
    }
  };

  const getServiceIcon = (iconName: string) => {
    // Map icon names to actual icons - you could expand this
    switch (iconName) {
      case 'grass':
        return '🌱';
      case 'pool':
        return '💧';
      case 'home':
        return '🏠';
      case 'cleaning':
        return '💦';
      case 'lightbulb':
        return '🎄';
      default:
        return '🏠';
    }
  };

  const calculateDiscount = (memberCount: number, discountTiers: { [key: string]: number }) => {
    const tiers = Object.keys(discountTiers).map(Number).sort((a, b) => a - b);
    
    for (let i = tiers.length - 1; i >= 0; i--) {
      if (memberCount >= tiers[i]) {
        return Math.round(discountTiers[tiers[i]] * 100);
      }
    }
    
    return 15; // Default discount
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900">Popular Services</h2>
        <p className="text-lg text-gray-600 mt-2">
          Join neighbors in your area for group discounts up to 25%
        </p>
        
        {/* ZIP Code Input */}
        <div className="mt-4 max-w-xs mx-auto">
          <label htmlFor="zipCode" className="block text-sm font-medium text-gray-700 mb-2">
            Your ZIP Code
          </label>
          <input
            type="text"
            id="zipCode"
            value={userZipCode}
            onChange={(e) => setUserZipCode(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
            placeholder="Enter ZIP code"
          />
        </div>
      </div>

      {/* Service Categories Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {categories.map((category) => {
          const pools = localPools[category.id] || [];
          const stats = localStats[category.id];
          const memberCount = stats?.total_active_members || 0;
          const discount = calculateDiscount(memberCount, category.group_discount_tiers);
          
          return (
            <div
              key={category.id}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 p-6"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center">
                  <span className="text-2xl mr-3">{getServiceIcon(category.icon_name)}</span>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {category.display_name.replace(/^🌱|💧|🏠|💦|🎄/, '').trim()}
                    </h3>
                    <p className="text-sm text-gray-600">{category.frequency}</p>
                  </div>
                </div>
                
                {/* Savings Badge */}
                {memberCount >= 3 && (
                  <span className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
                    Save {discount}%
                  </span>
                )}
              </div>

              {/* Description */}
              <p className="text-gray-600 text-sm mb-4">{category.description}</p>

              {/* Price Range */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center text-sm text-gray-500">
                  <DollarSign className="w-4 h-4 mr-1" />
                  ${category.typical_price_min}-${category.typical_price_max}
                  {category.frequency && ` ${category.frequency}`}
                </div>
              </div>

              {/* Pool Status */}
              <div className="space-y-2 mb-4">
                {stats ? (
                  <>
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center text-gray-600">
                        <Users className="w-4 h-4 mr-1" />
                        Local Interest
                      </span>
                      <span className="font-medium">
                        {memberCount > 0 ? `${memberCount} neighbors` : 'Be the first!'}
                      </span>
                    </div>
                    
                    {stats.spots_remaining > 0 && memberCount > 0 && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="flex items-center text-gray-600">
                          <Clock className="w-4 h-4 mr-1" />
                          Spots Remaining
                        </span>
                        <span className="font-medium text-orange-600">
                          {stats.spots_remaining} more needed
                        </span>
                      </div>
                    )}
                    
                    {stats.completed_pools > 0 && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="flex items-center text-gray-600">
                          <CheckCircle className="w-4 h-4 mr-1" />
                          Success Rate
                        </span>
                        <span className="font-medium text-green-600">
                          {stats.completed_pools} groups completed
                        </span>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-sm text-gray-500">Loading local data...</div>
                )}
              </div>

              {/* Action Button */}
              <button
                onClick={() => handleJoinOrCreatePool(category)}
                className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-md transition-colors duration-200 flex items-center justify-center"
              >
                <Plus className="w-4 h-4 mr-2" />
                {pools.length > 0 ? 'Join Group' : 'Start Group'}
              </button>

              {/* Additional Info */}
              {memberCount >= 3 && (
                <p className="text-xs text-green-600 text-center mt-2">
                  🎉 Group discount available! Save ${Math.round((category.typical_price_max * discount) / 100)} per service
                </p>
              )}
            </div>
          );
        })}
      </div>

      {/* Benefits Section */}
      <div className="bg-blue-50 rounded-lg p-6 mt-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">How Group Bidding Works</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <Users className="w-8 h-8 text-blue-600 mx-auto mb-2" />
            <h4 className="font-medium text-gray-900">Join Neighbors</h4>
            <p className="text-sm text-gray-600">3+ homeowners in your area team up for bulk pricing</p>
          </div>
          <div className="text-center">
            <DollarSign className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <h4 className="font-medium text-gray-900">Save 15-25%</h4>
            <p className="text-sm text-gray-600">Contractors offer group discounts for efficient routing</p>
          </div>
          <div className="text-center">
            <CheckCircle className="w-8 h-8 text-purple-600 mx-auto mb-2" />
            <h4 className="font-medium text-gray-900">Guaranteed Service</h4>
            <p className="text-sm text-gray-600">Once groups form, contractors compete for your business</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PopularServicesTab;