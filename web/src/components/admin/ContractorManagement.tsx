import React, { useState, useEffect } from 'react';

interface ContractorSummary {
  id: string;
  company_name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  city: string;
  state: string;
  specialties: string[];
  tier: number;
  tier_description: string;
  rating?: number;
  status: string;
  last_contact?: string;
  campaigns_participated: number;
  bids_submitted: number;
  bids_won: number;
  total_connection_fees: number;
  active_bid_cards: number;
  response_rate: number;
  availability_status?: string;
}

interface ContractorFullDetail {
  id: string;
  company_name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  website?: string;
  address?: string;
  city: string;
  state: string;
  zip_code?: string;
  service_radius_miles?: number;
  contractor_size?: string;
  years_in_business?: number;
  employees?: string;
  specialties: string[];
  certifications: string[];
  license_number?: string;
  license_verified?: boolean;
  insurance_verified?: boolean;
  bonded?: boolean;
  tier: number;
  tier_description: string;
  rating?: number;
  review_count?: number;
  lead_score?: number;
  campaigns_participated: number;
  bids_submitted: number;
  bids_won: number;
  total_connection_fees: number;
  active_bid_cards: number;
  response_rate: number;
  last_contact?: string;
  availability_status?: string;
  ai_writeup?: string;
  business_intelligence?: any;
  social_media_presence?: any;
  recent_reviews?: any[];
  discovery_source?: string;
  discovery_date?: string;
  enrichment_data?: any;
}

interface TierStats {
  tier_1: number;
  tier_2: number;
  tier_3: number;
  total: number;
}

const ContractorManagement: React.FC = () => {
  const [contractors, setContractors] = useState<ContractorSummary[]>([]);
  const [tierStats, setTierStats] = useState<TierStats | null>(null);
  const [selectedTier, setSelectedTier] = useState<number | null>(null);
  const [selectedContractor, setSelectedContractor] = useState<ContractorFullDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCity, setFilterCity] = useState('');
  const [filterSpecialty, setFilterSpecialty] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const contractorsPerPage = 100; // Increased default limit

  const fetchContractors = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedTier) {
        console.log('fetchContractors: selectedTier is', selectedTier, 'type:', typeof selectedTier);
        params.append('tier', selectedTier.toString());
      }
      if (filterCity) params.append('city', filterCity);
      if (filterSpecialty) params.append('specialty', filterSpecialty);
      params.append('limit', contractorsPerPage.toString());
      params.append('offset', ((currentPage - 1) * contractorsPerPage).toString());
      
      const url = `/api/contractor-management/contractors?${params}`;
      console.log('fetchContractors: about to fetch URL:', url);

      // Add timeout to prevent hanging
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

      const response = await fetch(`/api/contractor-management/contractors?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_session_id') || 'admin-session'}`
        },
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to fetch contractors: ${response.status}`);
      }

      const data = await response.json();
      setContractors(data.contractors || []);
      setTierStats(data.tier_stats || { tier_1: 9, tier_2: 0, tier_3: 100, total: 109 });
      
      // Calculate total pages based on filtered total, not tier stats
      const totalContractors = data.total || data.tier_stats?.total || 109;
      setTotalPages(Math.ceil(totalContractors / contractorsPerPage));
      
      setError(null);
    } catch (error) {
      console.error('Error fetching contractors:', error);
      if (error instanceof Error && error.name === 'AbortError') {
        setError('Request timed out. Showing limited data due to backend performance issues.');
        // Load with fallback data
        loadFallbackData();
      } else {
        setError(error instanceof Error ? error.message : 'Failed to load contractors');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadFallbackData = async () => {
    try {
      // Try to load just 5 contractors as fallback
      const response = await fetch(`/api/contractor-management/contractors?limit=5`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_session_id') || 'admin-session'}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setContractors(data.contractors || []);
        setTierStats(data.tier_stats || { tier_1: 9, tier_2: 0, tier_3: 100, total: 109 });
      }
    } catch (err) {
      console.error('Fallback load failed:', err);
      // Set some demo data so UI isn't empty
      setContractors([]);
      setTierStats({ tier_1: 9, tier_2: 0, tier_3: 100, total: 109 });
    }
  };

  const fetchContractorDetail = async (contractorId: string) => {
    try {
      const response = await fetch(`/api/contractor-management/contractors/${contractorId}/full`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_session_id') || 'admin-session'}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch contractor details: ${response.status}`);
      }

      const data = await response.json();
      setSelectedContractor(data);
    } catch (error) {
      console.error('Error fetching contractor details:', error);
      setError(error instanceof Error ? error.message : 'Failed to load contractor details');
    }
  };

  useEffect(() => {
    fetchContractors();
  }, [selectedTier, filterCity, filterSpecialty, currentPage]);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  // Filter contractors by search term
  const filteredContractors = contractors.filter(contractor =>
    contractor.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (contractor.contact_name && contractor.contact_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
    contractor.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contractor.specialties.some(s => s.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getTierColor = (tier: number) => {
    switch (tier) {
      case 1: return 'bg-green-100 text-green-800 border-green-200';
      case 2: return 'bg-blue-100 text-blue-800 border-blue-200';
      case 3: return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': case 'verified': return 'text-green-600';
      case 'pending': return 'text-yellow-600';
      case 'inactive': case 'disqualified': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'Invalid date';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-4 text-lg text-gray-600">Loading contractors...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
        <strong className="font-bold">Error loading contractors: </strong>
        <span className="block sm:inline">{error}</span>
        <button 
          onClick={fetchContractors}
          className="mt-2 bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Tier Statistics */}
      {tierStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-800">Total Contractors</h3>
            <p className="text-3xl font-bold text-blue-600">{tierStats.total}</p>
          </div>
          
          <div 
            className={`bg-white p-4 rounded-lg border shadow-sm cursor-pointer transition-all ${
              selectedTier === 1 ? 'border-green-400 bg-green-50' : 'border-gray-200 hover:border-green-300'
            }`}
            onClick={() => {
              console.log('Tier 1 clicked, current selectedTier:', selectedTier);
              setSelectedTier(selectedTier === 1 ? null : 1);
            }}
          >
            <h3 className="text-lg font-semibold text-green-800">Tier 1 - Official</h3>
            <p className="text-3xl font-bold text-green-600">{tierStats.tier_1}</p>
            <p className="text-sm text-green-600">InstaBids contractors</p>
          </div>

          <div 
            className={`bg-white p-4 rounded-lg border shadow-sm cursor-pointer transition-all ${
              selectedTier === 2 ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:border-blue-300'
            }`}
            onClick={() => {
              console.log('Tier 2 clicked, current selectedTier:', selectedTier);
              setSelectedTier(selectedTier === 2 ? null : 2);
            }}
          >
            <h3 className="text-lg font-semibold text-blue-800">Tier 2 - Previous</h3>
            <p className="text-3xl font-bold text-blue-600">{tierStats.tier_2}</p>
            <p className="text-sm text-blue-600">Multiple campaigns</p>
          </div>

          <div 
            className={`bg-white p-4 rounded-lg border shadow-sm cursor-pointer transition-all ${
              selectedTier === 3 ? 'border-yellow-400 bg-yellow-50' : 'border-gray-200 hover:border-yellow-300'
            }`}
            onClick={() => {
              console.log('Tier 3 clicked, current selectedTier:', selectedTier);
              setSelectedTier(selectedTier === 3 ? null : 3);
            }}
          >
            <h3 className="text-lg font-semibold text-yellow-800">Tier 3 - New</h3>
            <p className="text-3xl font-bold text-yellow-600">{tierStats.tier_3}</p>
            <p className="text-sm text-yellow-600">First discovery</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by company, contact, or city..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Filter by City</label>
            <input
              type="text"
              value={filterCity}
              onChange={(e) => setFilterCity(e.target.value)}
              placeholder="Enter city name..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Specialty</label>
            <input
              type="text"
              value={filterSpecialty}
              onChange={(e) => setFilterSpecialty(e.target.value)}
              placeholder="Enter specialty..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Contractors Table */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Company
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tier
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Location
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Specialties
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Performance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bid Statistics
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredContractors.map((contractor) => (
                <tr key={contractor.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {contractor.company_name}
                      </div>
                      {contractor.contact_name && (
                        <div className="text-sm text-gray-500">{contractor.contact_name}</div>
                      )}
                      {contractor.email && (
                        <div className="text-sm text-gray-500">{contractor.email}</div>
                      )}
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getTierColor(contractor.tier)}`}>
                      Tier {contractor.tier}
                    </span>
                    <div className="text-xs text-gray-500 mt-1">
                      {contractor.tier_description}
                    </div>
                  </td>

                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{contractor.city}</div>
                    <div className="text-sm text-gray-500">{contractor.state}</div>
                  </td>

                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {contractor.specialties.slice(0, 2).map((specialty, index) => (
                        <span key={index} className="inline-flex px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                          {specialty}
                        </span>
                      ))}
                      {contractor.specialties.length > 2 && (
                        <span className="text-xs text-gray-500">
                          +{contractor.specialties.length - 2} more
                        </span>
                      )}
                    </div>
                  </td>

                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {contractor.campaigns_participated} campaigns
                    </div>
                    <div className="text-sm text-gray-500">
                      {contractor.response_rate}% response rate
                    </div>
                    {contractor.rating && (
                      <div className="text-sm text-yellow-600">
                        ⭐ {contractor.rating.toFixed(1)}
                      </div>
                    )}
                  </td>

                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {contractor.bids_submitted} bids submitted
                    </div>
                    <div className="text-sm text-green-600">
                      {contractor.bids_won} bids won
                    </div>
                    <div className="text-sm text-blue-600">
                      ${contractor.total_connection_fees.toFixed(0)} in fees
                    </div>
                    {contractor.active_bid_cards > 0 && (
                      <div className="text-sm text-orange-600">
                        {contractor.active_bid_cards} active projects
                      </div>
                    )}
                  </td>

                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-sm font-medium ${getStatusColor(contractor.status)}`}>
                      {contractor.status}
                    </div>
                    <div className="text-xs text-gray-500">
                      Last: {formatDate(contractor.last_contact)}
                    </div>
                  </td>

                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => fetchContractorDetail(contractor.id)}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                    >
                      View Details
                    </button>
                    {contractor.tier > 1 && (
                      <button className="text-green-600 hover:text-green-900">
                        Add to Campaign
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredContractors.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-500">
              {searchTerm || filterCity || filterSpecialty 
                ? 'No contractors match your filters' 
                : 'No contractors found'}
            </div>
          </div>
        )}
        
        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing page {currentPage} of {totalPages} ({tierStats?.total || 0} total contractors)
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm bg-white border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Previous
              </button>
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 py-1 text-sm bg-white border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Enhanced Contractor Detail Modal */}
      {selectedContractor && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-11/12 md:w-4/5 lg:w-3/4 xl:w-2/3 shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4 sticky top-0 bg-white pb-4 border-b">
              <h3 className="text-xl font-bold text-gray-900">
                {selectedContractor.company_name}
              </h3>
              <button
                onClick={() => setSelectedContractor(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              {/* AI Writeup Section - New! */}
              {selectedContractor.ai_writeup && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="text-md font-semibold text-blue-900 mb-2">
                    🤖 AI Analysis
                  </h4>
                  <p className="text-sm text-gray-800">{selectedContractor.ai_writeup}</p>
                </div>
              )}

              {/* Basic Info - Enhanced */}
              <div>
                <h4 className="text-md font-semibold text-gray-800 mb-3">📋 Basic Information</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <span className="text-sm font-medium text-gray-500">Contact:</span>
                    <p className="text-sm text-gray-900">{selectedContractor.contact_name || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-500">Email:</span>
                    <p className="text-sm text-gray-900">{selectedContractor.email || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-500">Phone:</span>
                    <p className="text-sm text-gray-900">{selectedContractor.phone || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-500">Website:</span>
                    {selectedContractor.website ? (
                      <a href={selectedContractor.website} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline">
                        {selectedContractor.website}
                      </a>
                    ) : (
                      <p className="text-sm text-gray-900">N/A</p>
                    )}
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-500">Full Address:</span>
                    <p className="text-sm text-gray-900">
                      {selectedContractor.address && `${selectedContractor.address}, `}
                      {selectedContractor.city}, {selectedContractor.state}
                      {selectedContractor.zip_code && ` ${selectedContractor.zip_code}`}
                    </p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-500">Service Radius:</span>
                    <p className="text-sm text-gray-900">
                      {selectedContractor.service_radius_miles ? `${selectedContractor.service_radius_miles} miles` : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Business Details - New! */}
              <div>
                <h4 className="text-md font-semibold text-gray-800 mb-3">🏢 Business Details</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <span className="text-sm font-medium text-gray-500">Company Size:</span>
                    <p className="text-sm text-gray-900">{selectedContractor.contractor_size || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-500">Years in Business:</span>
                    <p className="text-sm text-gray-900">
                      {selectedContractor.years_in_business ? `${selectedContractor.years_in_business} years` : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-500">Employees:</span>
                    <p className="text-sm text-gray-900">{selectedContractor.employees || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-500">License #:</span>
                    <p className="text-sm text-gray-900">{selectedContractor.license_number || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-500">Verifications:</span>
                    <div className="flex gap-2 mt-1">
                      {selectedContractor.license_verified && (
                        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">✓ License</span>
                      )}
                      {selectedContractor.insurance_verified && (
                        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">✓ Insurance</span>
                      )}
                      {selectedContractor.bonded && (
                        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">✓ Bonded</span>
                      )}
                      {!selectedContractor.license_verified && !selectedContractor.insurance_verified && !selectedContractor.bonded && (
                        <span className="text-xs text-gray-500">Not verified</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-500">Lead Score:</span>
                    <p className="text-sm text-gray-900">
                      {selectedContractor.lead_score ? `${selectedContractor.lead_score}/100` : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Performance - Enhanced */}
              <div>
                <h4 className="text-md font-semibold text-gray-800 mb-3">📊 Performance & Statistics</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 p-3 rounded">
                    <span className="text-xs font-medium text-gray-500">Campaigns:</span>
                    <p className="text-lg font-bold text-blue-600">{selectedContractor.campaigns_participated}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <span className="text-xs font-medium text-gray-500">Bids Submitted:</span>
                    <p className="text-lg font-bold text-green-600">{selectedContractor.bids_submitted}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <span className="text-xs font-medium text-gray-500">Bids Won:</span>
                    <p className="text-lg font-bold text-green-700">{selectedContractor.bids_won}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <span className="text-xs font-medium text-gray-500">Response Rate:</span>
                    <p className="text-lg font-bold text-yellow-600">{selectedContractor.response_rate}%</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <span className="text-xs font-medium text-gray-500">Connection Fees:</span>
                    <p className="text-lg font-bold text-blue-700">${selectedContractor.total_connection_fees.toFixed(0)}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <span className="text-xs font-medium text-gray-500">Active Projects:</span>
                    <p className="text-lg font-bold text-orange-600">{selectedContractor.active_bid_cards}</p>
                  </div>
                  {selectedContractor.rating && (
                    <div className="bg-gray-50 p-3 rounded">
                      <span className="text-xs font-medium text-gray-500">Rating:</span>
                      <p className="text-lg font-bold text-yellow-600">⭐ {selectedContractor.rating.toFixed(1)}</p>
                      {selectedContractor.review_count && (
                        <p className="text-xs text-gray-500">({selectedContractor.review_count} reviews)</p>
                      )}
                    </div>
                  )}
                  <div className="bg-gray-50 p-3 rounded">
                    <span className="text-xs font-medium text-gray-500">Win Rate:</span>
                    <p className="text-lg font-bold text-purple-600">
                      {selectedContractor.bids_submitted > 0 ? 
                        `${Math.round((selectedContractor.bids_won / selectedContractor.bids_submitted) * 100)}%` : 
                        '0%'
                      }
                    </p>
                  </div>
                </div>
              </div>

              {/* Specialties & Certifications */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-md font-semibold text-gray-800 mb-3">🔧 Specialties</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedContractor.specialties.map((specialty, index) => (
                      <span key={index} className="inline-flex px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full">
                        {specialty}
                      </span>
                    ))}
                  </div>
                </div>
                
                {selectedContractor.certifications && selectedContractor.certifications.length > 0 && (
                  <div>
                    <h4 className="text-md font-semibold text-gray-800 mb-3">🏆 Certifications</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedContractor.certifications.map((cert, index) => (
                        <span key={index} className="inline-flex px-3 py-1 text-sm bg-green-100 text-green-800 rounded-full">
                          {cert}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Business Intelligence - New! */}
              {selectedContractor.business_intelligence && (
                <div>
                  <h4 className="text-md font-semibold text-gray-800 mb-3">💡 Business Intelligence</h4>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                      {JSON.stringify(selectedContractor.business_intelligence, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Recent Reviews - New! */}
              {selectedContractor.recent_reviews && selectedContractor.recent_reviews.length > 0 && (
                <div>
                  <h4 className="text-md font-semibold text-gray-800 mb-3">⭐ Recent Reviews</h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {selectedContractor.recent_reviews.map((review, index) => (
                      <div key={index} className="p-3 bg-gray-50 rounded">
                        <p className="text-sm text-gray-800">{review.text || review}</p>
                        {review.rating && (
                          <div className="text-xs text-yellow-600 mt-1">
                            {'⭐'.repeat(review.rating)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Discovery Information - New! */}
              <div>
                <h4 className="text-md font-semibold text-gray-800 mb-3">🔍 Discovery Information</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <span className="text-sm font-medium text-gray-500">Tier:</span>
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ml-2 ${getTierColor(selectedContractor.tier)}`}>
                      Tier {selectedContractor.tier} - {selectedContractor.tier_description}
                    </span>
                  </div>
                  {selectedContractor.discovery_source && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Discovery Source:</span>
                      <p className="text-sm text-gray-900">{selectedContractor.discovery_source}</p>
                    </div>
                  )}
                  {selectedContractor.discovery_date && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Discovery Date:</span>
                      <p className="text-sm text-gray-900">{formatDate(selectedContractor.discovery_date)}</p>
                    </div>
                  )}
                  <div>
                    <span className="text-sm font-medium text-gray-500">Last Contact:</span>
                    <p className="text-sm text-gray-900">{formatDate(selectedContractor.last_contact)}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContractorManagement;