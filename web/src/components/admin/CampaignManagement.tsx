import React, { useState, useEffect } from 'react';

interface Campaign {
  id: string;
  name: string;
  bid_card_id: string;
  bid_card_number?: string;
  project_type?: string;
  status: 'draft' | 'active' | 'paused' | 'completed' | 'cancelled';
  max_contractors: number;
  contractors_targeted: number;
  contractors_responded: number;
  bids_received: number;
  created_at: string;
  updated_at: string;
  target_completion_date?: string;
  progress_percentage: number;
  // Date flow fields
  bid_collection_deadline?: string;
  project_completion_deadline?: string;
  deadline_adjusted_timeline_hours?: number;
  deadline_hard?: boolean;
  // Urgency and timeline fields
  urgency_level?: string;
  user_timeline_days?: number;
  internal_timeline_hours?: number;
}

interface CampaignStats {
  total_campaigns: number;
  active_campaigns: number;
  completed_campaigns: number;
  total_contractors_targeted: number;
  total_responses_received: number;
  average_response_rate: number;
}

interface CampaignDetail {
  id: string;
  name: string;
  bid_card_id: string;
  bid_card_number?: string;
  project_type?: string;
  project_description?: string;
  status: string;
  max_contractors: number;
  contractors_targeted: number;
  contractors_responded: number;
  bids_received: number;
  created_at: string;
  updated_at: string;
  target_completion_date?: string;
  progress_percentage: number;
  response_rate: number;
  avg_response_time_hours?: number;
  // Date flow fields
  bid_collection_deadline?: string;
  project_completion_deadline?: string;
  deadline_adjusted_timeline_hours?: number;
  deadline_hard?: boolean;
  assigned_contractors: Array<{
    assignment_id: string;
    contractor_id: string;
    company_name: string;
    contact_name?: string;
    email?: string;
    phone?: string;
    tier?: string;
    rating?: number;
    specialties?: string[];
    city?: string;
    state?: string;
    assigned_at: string;
    status: string;
  }>;
  outreach_history: Array<{
    attempt_id: string;
    contractor_company: string;
    channel: string;
    status: string;
    sent_at: string;
    message_content: string;
  }>;
  check_ins: Array<{
    check_in_id: string;
    check_in_type: string;
    check_in_time: string;
    contractors_needed?: number;
    escalation_triggered: boolean;
    notes: string;
  }>;
  // Campaign decision audit trail
  strategy_data?: {
    urgency_level: string;
    timeline_hours: number;
    bids_needed: number;
    total_contractors: number;
    expected_responses: number;
    confidence_score: number;
    tier_breakdown: {
      tier_1: { count: number; expected: number };
      tier_2: { count: number; expected: number };
      tier_3: { count: number; expected: number };
    };
    risk_factors: string[];
    recommendations: string[];
  };
  decision_inputs?: {
    project_details: {
      project_type: string;
      urgency_level: string;
      budget_range: { min: number; max: number };
      contractor_count_needed: number;
      project_description?: string;
    };
    timing_requirements: {
      bid_collection_deadline?: string;
      project_completion_deadline?: string;
      deadline_hard: boolean;
      deadline_context?: string;
    };
    campaign_settings: {
      max_contractors: number;
      target_criteria?: any;
      created_at: string;
    };
  };
}

const CampaignManagement: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [campaignStats, setCampaignStats] = useState<CampaignStats | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Detail view state
  const [selectedCampaign, setSelectedCampaign] = useState<CampaignDetail | null>(null);
  const [showDetailView, setShowDetailView] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  
  // Contractor assignment state
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignmentCampaignId, setAssignmentCampaignId] = useState<string | null>(null);
  const [availableContractors, setAvailableContractors] = useState<any[]>([]);
  const [selectedContractorIds, setSelectedContractorIds] = useState<string[]>([]);
  const [contractorLoading, setContractorLoading] = useState(false);
  const [assignmentLoading, setAssignmentLoading] = useState(false);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      
      // Fetch real campaign data from API
      const [campaignsResponse, statsResponse] = await Promise.all([
        fetch(`/api/campaign-management/campaigns?status=${selectedStatus || ''}`),
        fetch('/api/campaign-management/dashboard-stats')
      ]);

      if (!campaignsResponse.ok || !statsResponse.ok) {
        throw new Error(`API error: ${campaignsResponse.status} ${statsResponse.status}`);
      }

      const campaignsData = await campaignsResponse.json();
      const statsData = await statsResponse.json();

      // Transform API response to match component interface
      const transformedCampaigns: Campaign[] = campaignsData.campaigns.map((campaign: any) => ({
        id: campaign.id,
        name: campaign.name,
        bid_card_id: campaign.bid_card_id,
        bid_card_number: campaign.bid_card_number,
        project_type: campaign.project_type,
        status: campaign.status,
        max_contractors: campaign.max_contractors,
        contractors_targeted: campaign.contractors_targeted,
        contractors_responded: campaign.contractors_responded,
        bids_received: campaign.bids_received,
        created_at: campaign.created_at,
        updated_at: campaign.updated_at,
        target_completion_date: campaign.target_completion_date,
        progress_percentage: campaign.progress_percentage
      }));

      const transformedStats: CampaignStats = {
        total_campaigns: statsData.total_campaigns,
        active_campaigns: statsData.active_campaigns,
        completed_campaigns: statsData.completed_campaigns,
        total_contractors_targeted: statsData.total_contractors_targeted,
        total_responses_received: statsData.total_responses_received,
        average_response_rate: statsData.average_response_rate
      };

      setCampaigns(transformedCampaigns);
      setCampaignStats(transformedStats);
      setError(null);
    } catch (error) {
      console.error('Error fetching campaigns:', error);
      setError(error instanceof Error ? error.message : 'Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  const fetchCampaignDetail = async (campaignId: string) => {
    try {
      setDetailLoading(true);
      const response = await fetch(`/api/campaign-management/campaigns/${campaignId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch campaign details: ${response.status}`);
      }
      
      const data = await response.json();
      setSelectedCampaign(data);
      setShowDetailView(true);
    } catch (error) {
      console.error('Error fetching campaign details:', error);
      setError(error instanceof Error ? error.message : 'Failed to load campaign details');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleViewDetails = (campaignId: string) => {
    fetchCampaignDetail(campaignId);
  };

  const fetchAvailableContractors = async () => {
    try {
      setContractorLoading(true);
      const response = await fetch('/api/contractor-management/contractors?limit=100');
      
      if (!response.ok) {
        throw new Error(`Failed to fetch contractors: ${response.status}`);
      }
      
      const data = await response.json();
      setAvailableContractors(data.contractors || []);
    } catch (error) {
      console.error('Error fetching contractors:', error);
      setError(error instanceof Error ? error.message : 'Failed to load contractors');
    } finally {
      setContractorLoading(false);
    }
  };

  const handleAddContractors = async (campaignId: string) => {
    setAssignmentCampaignId(campaignId);
    setSelectedContractorIds([]);
    setShowAssignModal(true);
    await fetchAvailableContractors();
  };

  const handleContractorSelection = (contractorId: string, isSelected: boolean) => {
    if (isSelected) {
      setSelectedContractorIds(prev => [...prev, contractorId]);
    } else {
      setSelectedContractorIds(prev => prev.filter(id => id !== contractorId));
    }
  };

  const handleAssignContractors = async () => {
    if (!assignmentCampaignId || selectedContractorIds.length === 0) {
      return;
    }

    try {
      setAssignmentLoading(true);
      const response = await fetch(
        `/api/campaign-management/campaigns/${assignmentCampaignId}/assign-contractors`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            contractor_ids: selectedContractorIds
          })
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to assign contractors: ${response.status}`);
      }

      const result = await response.json();
      alert(`Successfully assigned ${result.contractors_assigned} contractors to campaign`);
      
      // Close modal and refresh data
      setShowAssignModal(false);
      setAssignmentCampaignId(null);
      setSelectedContractorIds([]);
      
      // Refresh campaign data
      if (showDetailView && selectedCampaign) {
        await fetchCampaignDetail(selectedCampaign.id);
      } else {
        await fetchCampaigns();
      }
      
    } catch (error) {
      console.error('Error assigning contractors:', error);
      setError(error instanceof Error ? error.message : 'Failed to assign contractors');
    } finally {
      setAssignmentLoading(false);
    }
  };

  const handleCancelAssignment = () => {
    setShowAssignModal(false);
    setAssignmentCampaignId(null);
    setSelectedContractorIds([]);
    setAvailableContractors([]);
  };

  const handlePauseCampaign = async (campaignId: string) => {
    const campaign = campaigns.find(c => c.id === campaignId);
    if (!campaign) return;
    
    const newStatus = campaign.status === 'paused' ? 'active' : 'paused';
    const action = newStatus === 'paused' ? 'pause' : 'resume';
    
    if (!confirm(`Are you sure you want to ${action} this campaign?`)) {
      return;
    }
    
    try {
      // Update campaign status via API
      const response = await fetch(
        `/api/campaign-management/campaigns/${campaignId}/status`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ status: newStatus })
        }
      );
      
      if (!response.ok) {
        throw new Error(`Failed to ${action} campaign: ${response.status}`);
      }
      
      // Update local state
      setCampaigns(prev => prev.map(c => 
        c.id === campaignId ? { ...c, status: newStatus } : c
      ));
      
      alert(`Campaign ${newStatus === 'paused' ? 'paused' : 'resumed'} successfully`);
    } catch (error) {
      console.error(`Error ${action}ing campaign:`, error);
      setError(error instanceof Error ? error.message : `Failed to ${action} campaign`);
    }
  };

  const handleBackToList = () => {
    setShowDetailView(false);
    setSelectedCampaign(null);
    // Refresh campaigns list
    fetchCampaigns();
  };

  useEffect(() => {
    fetchCampaigns();
    
    // Polling disabled for performance - use manual refresh instead
    // const interval = setInterval(fetchCampaigns, 30000);
    // return () => clearInterval(interval);
  }, [selectedStatus]);

  // Filter campaigns by search term and status
  const filteredCampaigns = campaigns.filter(campaign => {
    const matchesSearch = campaign.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         campaign.bid_card_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         campaign.project_type?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = !selectedStatus || campaign.status === selectedStatus;
    
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'completed': return 'text-blue-600 bg-blue-100'; 
      case 'paused': return 'text-yellow-600 bg-yellow-100';
      case 'cancelled': return 'text-red-600 bg-red-100';
      case 'draft': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Campaign Detail View Component
  const CampaignDetailView = () => {
    if (!selectedCampaign) return null;

    return (
      <div className="space-y-6">
        {/* Header with Back Button */}
        <div className="flex items-center justify-between">
          <button
            onClick={handleBackToList}
            className="flex items-center text-blue-600 hover:text-blue-800"
          >
            ← Back to Campaigns
          </button>
          <div className="text-sm text-gray-500">
            Last Updated: {formatDate(selectedCampaign.updated_at)}
          </div>
        </div>

        {/* Campaign Overview */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{selectedCampaign.name}</h2>
              <p className="text-gray-600 mb-4">{selectedCampaign.project_description}</p>
              <div className="space-y-2">
                <div>
                  <span className="font-medium">Bid Card:</span>{' '}
                  <button
                    onClick={() => {
                      // Navigate to bid card view
                      const bidCardTab = document.querySelector('[data-tab="bidCards"]');
                      if (bidCardTab) {
                        (bidCardTab as HTMLElement).click();
                        sessionStorage.setItem('highlightBidCard', selectedCampaign.bid_card_id);
                      }
                    }}
                    className="text-blue-600 hover:text-blue-800 hover:underline"
                  >
                    {selectedCampaign.bid_card_number}
                  </button>
                </div>
                <div><span className="font-medium">Project Type:</span> {selectedCampaign.project_type?.replace('_', ' ')}</div>
                <div><span className="font-medium">Status:</span> 
                  <span className={`ml-2 px-2 py-1 text-xs rounded-full ${getStatusColor(selectedCampaign.status)}`}>
                    {selectedCampaign.status.charAt(0).toUpperCase() + selectedCampaign.status.slice(1)}
                  </span>
                </div>
              </div>
            </div>
            <div className="space-y-4">
              {/* Deadline Alert if Rush Mode */}
              {selectedCampaign.deadline_adjusted_timeline_hours && (
                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <span className="text-yellow-400 text-xl">⚡</span>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-yellow-800">
                        Rush Mode: {selectedCampaign.deadline_adjusted_timeline_hours}h timeline
                      </p>
                      {selectedCampaign.bid_collection_deadline && (
                        <p className="text-xs text-yellow-600 mt-1">
                          Bid collection deadline: {new Date(selectedCampaign.bid_collection_deadline).toLocaleDateString()}
                        </p>
                      )}
                      {selectedCampaign.deadline_hard && (
                        <p className="text-xs text-red-600 mt-1 font-semibold">
                          ⚠️ FIRM DEADLINE - Cannot be extended
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
              
              {/* Progress Chart */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium">Campaign Progress</span>
                  <span className="text-sm text-gray-600">{selectedCampaign.progress_percentage}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className={`h-3 rounded-full ${getProgressColor(selectedCampaign.progress_percentage)}`}
                    style={{width: `${selectedCampaign.progress_percentage}%`}}
                  ></div>
                </div>
              </div>
              
              {/* Key Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-blue-50 rounded">
                  <div className="text-2xl font-bold text-blue-600">{selectedCampaign.contractors_targeted}</div>
                  <div className="text-sm text-blue-600">Contractors Targeted</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded">
                  <div className="text-2xl font-bold text-green-600">{selectedCampaign.contractors_responded}</div>
                  <div className="text-sm text-green-600">Responses Received</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Assigned Contractors */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Assigned Contractors ({selectedCampaign.assigned_contractors.length})</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Contact</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Tier</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Assigned</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {selectedCampaign.assigned_contractors.map((contractor) => (
                  <tr key={contractor.assignment_id}>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => {
                          // Navigate to contractor management view
                          const contractorTab = document.querySelector('[data-tab="contractors"]');
                          if (contractorTab) {
                            (contractorTab as HTMLElement).click();
                            // Store contractor ID to highlight
                            sessionStorage.setItem('highlightContractor', contractor.contractor_id);
                          }
                        }}
                        className="text-left hover:text-blue-600 transition-colors"
                      >
                        <div className="font-medium text-gray-900 hover:underline">{contractor.company_name}</div>
                        <div className="text-sm text-gray-500">{contractor.city}, {contractor.state}</div>
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-gray-900">{contractor.contact_name}</div>
                      <div className="text-sm text-gray-500">{contractor.email}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        contractor.tier === '1' ? 'bg-green-100 text-green-800' :
                        contractor.tier === '2' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        Tier {contractor.tier}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(contractor.status)}`}>
                        {contractor.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {formatDate(contractor.assigned_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {selectedCampaign.assigned_contractors.length === 0 && (
              <div className="text-center py-8 text-gray-500">No contractors assigned yet</div>
            )}
          </div>
        </div>

        {/* Outreach History */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Outreach History ({selectedCampaign.outreach_history.length})</h3>
          </div>
          <div className="p-4 space-y-3">
            {selectedCampaign.outreach_history.length > 0 ? (
              selectedCampaign.outreach_history.map((attempt) => (
                <div key={attempt.attempt_id} className="border border-gray-200 rounded p-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium text-gray-900">{attempt.contractor_company}</div>
                      <div className="text-sm text-gray-600">
                        Channel: {attempt.channel} • Status: {attempt.status}
                      </div>
                      <div className="text-sm text-gray-500 mt-1">{attempt.message_content}</div>
                    </div>
                    <div className="text-sm text-gray-500">{formatDate(attempt.sent_at)}</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-4 text-gray-500">No outreach history found</div>
            )}
          </div>
        </div>

        {/* Campaign Check-ins */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Campaign Check-ins ({selectedCampaign.check_ins.length})</h3>
          </div>
          <div className="p-4 space-y-3">
            {selectedCampaign.check_ins.length > 0 ? (
              selectedCampaign.check_ins.map((checkin) => (
                <div key={checkin.check_in_id} className="border border-gray-200 rounded p-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium text-gray-900">{checkin.check_in_type}</div>
                      {checkin.contractors_needed && (
                        <div className="text-sm text-gray-600">Contractors needed: {checkin.contractors_needed}</div>
                      )}
                      {checkin.escalation_triggered && (
                        <div className="text-sm text-red-600 font-medium">⚠️ Escalation triggered</div>
                      )}
                      {checkin.notes && (
                        <div className="text-sm text-gray-500 mt-1">{checkin.notes}</div>
                      )}
                    </div>
                    <div className="text-sm text-gray-500">{formatDate(checkin.check_in_time)}</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-4 text-gray-500">No check-ins recorded yet</div>
            )}
          </div>
        </div>

        {/* Campaign Decision Audit Trail */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Campaign Decision Audit Trail</h3>
            <p className="text-sm text-gray-600 mt-1">What information went into creating this campaign</p>
          </div>
          <div className="p-4 space-y-6">
            
            {/* Input Analysis Section */}
            <div className="space-y-4">
              <h4 className="text-md font-semibold text-blue-900 border-b border-blue-200 pb-2">
                📋 Input Analysis
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div className="bg-blue-50 p-3 rounded">
                    <div className="text-sm font-medium text-blue-900">Project Requirements</div>
                    <div className="mt-1 space-y-1">
                      <div className="text-sm text-blue-700">
                        Type: {selectedCampaign.decision_inputs?.project_details?.project_type || 'Not specified'}
                      </div>
                      <div className="text-sm text-blue-700">
                        Urgency: {selectedCampaign.decision_inputs?.project_details?.urgency_level || 'Standard'}
                      </div>
                      <div className="text-sm text-blue-700">
                        Contractors Needed: {selectedCampaign.decision_inputs?.project_details?.contractor_count_needed || 'N/A'}
                      </div>
                      {selectedCampaign.decision_inputs?.project_details?.budget_range && (
                        <div className="text-sm text-blue-700">
                          Budget: ${selectedCampaign.decision_inputs.project_details.budget_range.min?.toLocaleString() || 'N/A'} - ${selectedCampaign.decision_inputs.project_details.budget_range.max?.toLocaleString() || 'N/A'}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="bg-green-50 p-3 rounded">
                    <div className="text-sm font-medium text-green-900">Timing Constraints</div>
                    <div className="mt-1 space-y-1">
                      {selectedCampaign.bid_collection_deadline && (
                        <div className="text-sm text-green-700">
                          Bid Deadline: {formatDate(selectedCampaign.bid_collection_deadline)}
                        </div>
                      )}
                      {selectedCampaign.project_completion_deadline && (
                        <div className="text-sm text-green-700">
                          Project Deadline: {formatDate(selectedCampaign.project_completion_deadline)}
                        </div>
                      )}
                      {selectedCampaign.deadline_hard !== undefined && (
                        <div className="text-sm text-green-700">
                          Hard Deadline: {selectedCampaign.deadline_hard ? 'Yes' : 'No'}
                        </div>
                      )}
                      {selectedCampaign.deadline_adjusted_timeline_hours && (
                        <div className="text-sm text-green-700">
                          Adjusted Timeline: {selectedCampaign.deadline_adjusted_timeline_hours} hours
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm font-medium text-gray-900">Campaign Configuration</div>
                <div className="mt-1 space-y-1">
                  <div className="text-sm text-gray-700">
                    Max Contractors: {selectedCampaign.decision_inputs?.campaign_settings?.max_contractors || selectedCampaign.max_contractors}
                  </div>
                  {selectedCampaign.decision_inputs?.campaign_settings?.target_criteria && (
                    <div className="text-sm text-gray-700">
                      Target Criteria: {JSON.stringify(selectedCampaign.decision_inputs.campaign_settings.target_criteria)}
                    </div>
                  )}
                  <div className="text-sm text-gray-700">
                    Created: {formatDate(selectedCampaign.decision_inputs?.campaign_settings?.created_at || selectedCampaign.created_at)}
                  </div>
                </div>
              </div>
            </div>

            {/* Strategy Calculations Section */}
            {selectedCampaign.strategy_data && (
              <div className="space-y-4">
                <h4 className="text-md font-semibold text-purple-900 border-b border-purple-200 pb-2">
                  🎯 Strategy Calculations
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-purple-50 p-3 rounded">
                    <div className="text-sm font-medium text-purple-900">Strategy Overview</div>
                    <div className="mt-1 space-y-1">
                      <div className="text-sm text-purple-700">
                        Urgency Level: {selectedCampaign.strategy_data.urgency_level}
                      </div>
                      <div className="text-sm text-purple-700">
                        Timeline: {selectedCampaign.strategy_data.timeline_hours} hours
                      </div>
                      <div className="text-sm text-purple-700">
                        Bids Needed: {selectedCampaign.strategy_data.bids_needed}
                      </div>
                      <div className="text-sm text-purple-700">
                        Total Contractors: {selectedCampaign.strategy_data.total_contractors}
                      </div>
                      <div className="text-sm text-purple-700">
                        Expected Responses: {selectedCampaign.strategy_data.expected_responses}
                      </div>
                    </div>
                  </div>
                  
                  {selectedCampaign.strategy_data.tier_breakdown && (
                    <div className="bg-indigo-50 p-3 rounded">
                      <div className="text-sm font-medium text-indigo-900">Tier Breakdown</div>
                      <div className="mt-1 space-y-1">
                        {Object.entries(selectedCampaign.strategy_data.tier_breakdown).map(([tier, data]) => (
                          <div key={tier} className="text-sm text-indigo-700">
                            {tier.replace('_', ' ')}: {(data as any).count} contractors (expect {(data as any).expected})
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="bg-yellow-50 p-3 rounded">
                    <div className="text-sm font-medium text-yellow-900">Confidence Score</div>
                    <div className="mt-1">
                      <div className="text-2xl font-bold text-yellow-700">
                        {selectedCampaign.strategy_data.confidence_score}%
                      </div>
                      <div className="text-sm text-yellow-600">
                        Likelihood of success
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Risk Factors and Recommendations */}
            {selectedCampaign.strategy_data && (selectedCampaign.strategy_data.risk_factors?.length > 0 || selectedCampaign.strategy_data.recommendations?.length > 0) && (
              <div className="space-y-4">
                <h4 className="text-md font-semibold text-red-900 border-b border-red-200 pb-2">
                  ⚠️ Risk Factors & Recommendations
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {selectedCampaign.strategy_data.risk_factors?.length > 0 && (
                    <div className="bg-red-50 p-3 rounded">
                      <div className="text-sm font-medium text-red-900">Risk Factors</div>
                      <div className="mt-1 space-y-1">
                        {selectedCampaign.strategy_data.risk_factors.map((risk: string, index: number) => (
                          <div key={index} className="text-sm text-red-700 flex items-start">
                            <span className="text-red-500 mr-1">•</span>
                            {risk}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {selectedCampaign.strategy_data.recommendations?.length > 0 && (
                    <div className="bg-green-50 p-3 rounded">
                      <div className="text-sm font-medium text-green-900">Recommendations</div>
                      <div className="mt-1 space-y-1">
                        {selectedCampaign.strategy_data.recommendations.map((rec: string, index: number) => (
                          <div key={index} className="text-sm text-green-700 flex items-start">
                            <span className="text-green-500 mr-1">→</span>
                            {rec}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* No Strategy Data Available */}
            {!selectedCampaign.strategy_data && !selectedCampaign.decision_inputs && (
              <div className="text-center py-8">
                <div className="text-gray-500 text-sm">
                  No strategy data available for this campaign.
                  <br />
                  This campaign may have been created manually or before strategy tracking was implemented.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Contractor Assignment Modal Component
  const ContractorAssignmentModal = () => {
    const [contractorSearch, setContractorSearch] = useState('');
    
    const filteredContractors = availableContractors.filter(contractor =>
      contractor.company_name.toLowerCase().includes(contractorSearch.toLowerCase()) ||
      contractor.city?.toLowerCase().includes(contractorSearch.toLowerCase()) ||
      contractor.specialties?.some((s: string) => s.toLowerCase().includes(contractorSearch.toLowerCase()))
    );

    if (!showAssignModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
          {/* Modal Header */}
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900">Assign Contractors to Campaign</h2>
              <button
                onClick={handleCancelAssignment}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <p className="mt-2 text-sm text-gray-600">
              Select contractors to add to this campaign. Selected: {selectedContractorIds.length}
            </p>
          </div>

          {/* Search Bar */}
          <div className="p-4 border-b border-gray-200">
            <input
              type="text"
              placeholder="Search contractors by company, city, or specialty..."
              value={contractorSearch}
              onChange={(e) => setContractorSearch(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Contractors List */}
          <div className="flex-1 overflow-y-auto p-4" style={{ maxHeight: '60vh' }}>
            {contractorLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-600">Loading contractors...</span>
              </div>
            ) : filteredContractors.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                {contractorSearch ? 'No contractors match your search' : 'No contractors available'}
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-3">
                {filteredContractors.map((contractor) => (
                  <div
                    key={contractor.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                      selectedContractorIds.includes(contractor.id)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleContractorSelection(
                      contractor.id,
                      !selectedContractorIds.includes(contractor.id)
                    )}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        <input
                          type="checkbox"
                          checked={selectedContractorIds.includes(contractor.id)}
                          onChange={(e) => handleContractorSelection(contractor.id, e.target.checked)}
                          className="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <div>
                          <h3 className="font-medium text-gray-900">{contractor.company_name}</h3>
                          {contractor.contact_name && (
                            <p className="text-sm text-gray-600">Contact: {contractor.contact_name}</p>
                          )}
                          <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                            <span>{contractor.city}, {contractor.state}</span>
                            {contractor.tier && (
                              <span className={`px-2 py-1 rounded text-xs ${
                                contractor.tier === '1' ? 'bg-green-100 text-green-800' :
                                contractor.tier === '2' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                Tier {contractor.tier}
                              </span>
                            )}
                          </div>
                          {contractor.specialties && contractor.specialties.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {contractor.specialties.slice(0, 3).map((specialty: string, index: number) => (
                                <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                  {specialty}
                                </span>
                              ))}
                              {contractor.specialties.length > 3 && (
                                <span className="px-2 py-1 bg-gray-100 text-gray-500 rounded text-xs">
                                  +{contractor.specialties.length - 3} more
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Modal Footer */}
          <div className="p-4 border-t border-gray-200 flex justify-end space-x-3">
            <button
              onClick={handleCancelAssignment}
              disabled={assignmentLoading}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleAssignContractors}
              disabled={selectedContractorIds.length === 0 || assignmentLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
            >
              {assignmentLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Assigning...
                </>
              ) : (
                `Assign ${selectedContractorIds.length} Contractor${selectedContractorIds.length !== 1 ? 's' : ''}`
              )}
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Show detail view if selected
  if (showDetailView) {
    return (
      <div className="space-y-6">
        {detailLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <span className="ml-4 text-lg text-gray-600">Loading campaign details...</span>
          </div>
        ) : (
          <CampaignDetailView />
        )}
        
        {/* Contractor Assignment Modal */}
        <ContractorAssignmentModal />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-4 text-lg text-gray-600">Loading campaigns...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
        <strong className="font-bold">Error loading campaigns: </strong>
        <span className="block sm:inline">{error}</span>
        <button 
          onClick={fetchCampaigns}
          className="mt-2 bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Campaign Statistics */}
      {campaignStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-800">Total Campaigns</h3>
            <p className="text-3xl font-bold text-blue-600">{campaignStats.total_campaigns}</p>
          </div>
          
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-800">Active</h3>
            <p className="text-3xl font-bold text-green-600">{campaignStats.active_campaigns}</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-800">Completed</h3>
            <p className="text-3xl font-bold text-blue-600">{campaignStats.completed_campaigns}</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-800">Contractors</h3>
            <p className="text-3xl font-bold text-purple-600">{campaignStats.total_contractors_targeted}</p>
            <p className="text-sm text-purple-600">Targeted</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-800">Responses</h3>
            <p className="text-3xl font-bold text-yellow-600">{campaignStats.total_responses_received}</p>
            <p className="text-sm text-yellow-600">Received</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-800">Response Rate</h3>
            <p className="text-3xl font-bold text-orange-600">{campaignStats.average_response_rate}%</p>
            <p className="text-sm text-orange-600">Average</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Search Campaigns</label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by campaign name, bid card, or project type..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Status</label>
            <select
              value={selectedStatus || ''}
              onChange={(e) => setSelectedStatus(e.target.value || null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>
      </div>

      {/* Campaigns Table */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        {/* Scroll indicator */}
        <div className="bg-blue-50 border-b border-blue-200 px-4 py-2 text-sm text-blue-700">
          💡 <strong>Tip:</strong> Scroll horizontally to see all campaign details. All actions are on the left for easy access.
        </div>
        <div className="overflow-x-auto overflow-y-visible">
          <table className="min-w-full divide-y divide-gray-200" style={{ minWidth: '1400px' }}>
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[160px]">
                  Actions
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[200px]">
                  Campaign & Bid Card
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[140px]">
                  Status & Progress
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[120px]">
                  Contractors
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[120px]">
                  Performance
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[200px]">
                  Timeline & Internal Target
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredCampaigns.map((campaign) => (
                <tr key={campaign.id} className="hover:bg-gray-50">
                  {/* Actions Column - Now First */}
                  <td className="px-4 py-3 text-sm font-medium">
                    <div className="flex flex-col space-y-1">
                      <button 
                        onClick={() => handleViewDetails(campaign.id)}
                        disabled={detailLoading}
                        className="text-blue-600 hover:text-blue-900 text-left disabled:opacity-50"
                      >
                        {detailLoading ? 'Loading...' : '📋 View Details'}
                      </button>
                      {campaign.status === 'active' && (
                        <>
                          <button 
                            onClick={() => handleAddContractors(campaign.id)}
                            className="text-green-600 hover:text-green-900 text-left"
                          >
                            ➕ Add Contractors
                          </button>
                          <button 
                            onClick={() => handlePauseCampaign(campaign.id)}
                            className="text-yellow-600 hover:text-yellow-900 text-left"
                          >
                            ⏸️ Pause
                          </button>
                        </>
                      )}
                      {campaign.status === 'paused' && (
                        <button 
                          onClick={() => handlePauseCampaign(campaign.id)}
                          className="text-green-600 hover:text-green-900 text-left"
                        >
                          ▶️ Resume
                        </button>
                      )}
                    </div>
                  </td>

                  {/* Campaign & Bid Card Column */}
                  <td className="px-4 py-3">
                    <div>
                      <div className="text-sm font-medium text-gray-900 truncate max-w-[180px]" title={campaign.name}>
                        {campaign.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        <button
                          onClick={() => {
                            // Navigate to bid card view
                            const bidCardTab = document.querySelector('[data-tab="bidCards"]');
                            if (bidCardTab) {
                              (bidCardTab as HTMLElement).click();
                              // Store bid card ID to highlight
                              sessionStorage.setItem('highlightBidCard', campaign.bid_card_id);
                            }
                          }}
                          className="text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {campaign.bid_card_number}
                        </button>
                        <span className="mx-1">•</span>
                        <span className="truncate">{campaign.project_type?.replace('_', ' ')}</span>
                      </div>
                    </div>
                  </td>
                  
                  {/* Status & Progress Column */}
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(campaign.status)}`}>
                      {campaign.status.charAt(0).toUpperCase() + campaign.status.slice(1)}
                    </span>
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${getProgressColor(campaign.progress_percentage)}`}
                        style={{width: `${campaign.progress_percentage}%`}}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">{campaign.progress_percentage}% complete</div>
                  </td>

                  {/* Contractors Column */}
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">
                      {campaign.contractors_targeted}/{campaign.max_contractors}
                    </div>
                    <div className="text-xs text-gray-500">
                      {campaign.contractors_responded} responses
                    </div>
                  </td>

                  {/* Performance Column */}
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">
                      {campaign.bids_received} bids
                    </div>
                    <div className="text-xs text-gray-500">
                      {campaign.contractors_targeted > 0 ? Math.round((campaign.contractors_responded / campaign.contractors_targeted) * 100) : 0}% rate
                    </div>
                  </td>

                  {/* Timeline & Internal Target Column */}
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">
                      Created: {formatDate(campaign.created_at)}
                    </div>
                    {campaign.target_completion_date && (
                      <div className="text-xs text-gray-500">
                        User Target: {formatDate(campaign.target_completion_date)}
                      </div>
                    )}
                    {campaign.deadline_adjusted_timeline_hours && (
                      <div className="text-xs text-orange-600 font-semibold">
                        ⚡ Internal: {campaign.deadline_adjusted_timeline_hours}h target
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredCampaigns.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-500">
              {searchTerm || selectedStatus 
                ? 'No campaigns match your filters' 
                : 'No campaigns found'
              }
            </div>
          </div>
        )}
      </div>
      
      {/* Contractor Assignment Modal */}
      <ContractorAssignmentModal />
    </div>
  );
};

export default CampaignManagement;