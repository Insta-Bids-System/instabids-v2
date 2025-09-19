import {
  AlertCircle,
  CheckCircle,
  Clock,
  Mail,
  Plus,
  Timer,
  TrendingUp,
  Users,
} from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";

interface Campaign {
  campaign_id: string;
  bid_card_id: string;
  bid_card_number: string;
  project_type: string;
  max_contractors: number;
  contractors_targeted: number;
  responses_received: number;
  campaign_status: "active" | "paused" | "completed";
  created_at: string;
  urgency_level?: string;
  check_ins?: CampaignCheckIn[];
  contractors?: CampaignContractor[];
}

interface CampaignCheckIn {
  id: string;
  check_in_percentage: number;
  scheduled_time: string;
  bids_expected: number;
  bids_received: number;
  on_track: boolean;
  escalation_needed: boolean;
  additional_contractors_needed?: number;
  status: "pending" | "completed" | "escalated";
}

interface CampaignContractor {
  id: string;
  contractor_id: string;
  company_name: string;
  contractor_size?: string;
  specialties?: string[];
  tier: number;
  status: "pending" | "contacted" | "responded" | "bid_submitted";
  contacted_at?: string;
  responded_at?: string;
  // Unified data from all 3 tables
  assignment_id?: string;
  assigned_at?: string;
  responded_at?: string;
  source: string;
  contact_name?: string;
  phone?: string;
  email?: string;
  website?: string;
  rating?: number;
  verified?: boolean;
  years_in_business?: number;
  license_number?: string;
  insurance_verified?: boolean;
  employees?: number;
  review_count?: number;
  discovery_source?: string;
  license_verified?: boolean;
  // TAVILY ENRICHED DATA
  has_website?: boolean;
  ai_business_summary?: string;
  ai_capability_description?: string;
  contractor_size_category?: string;
  services_mentioned?: string[];
  company_description?: string;
  is_tavily_enriched?: boolean;
}

const CampaignManager: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDetails, setShowDetails] = useState(false);
  
  // CDA Testing state
  const [showCDATest, setShowCDATest] = useState(false);
  const [cdaLoading, setCdaLoading] = useState(false);
  const [cdaResults, setCdaResults] = useState<any>(null);
  const [tavilyContractors, setTavilyContractors] = useState<any[]>([]);

  useEffect(() => {
    fetchCampaigns();
    fetchTavilyContractors();
    // Polling disabled for performance - use manual refresh instead
    // const interval = setInterval(fetchCampaigns, 30000);
    // return () => clearInterval(interval);
  }, []);

  const fetchCampaigns = async () => {
    try {
      const response = await fetch("/api/admin/campaigns-unified");
      if (response.ok) {
        const data = await response.json();
        setCampaigns(data.campaigns || []);
      }
    } catch (error) {
      console.error("Failed to fetch campaigns:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCampaignDetails = async (campaignId: string) => {
    try {
      const response = await fetch(
        `/api/admin/campaigns-unified/${campaignId}/details`
      );
      if (response.ok) {
        const data = await response.json();
        setSelectedCampaign(data);
        setShowDetails(true);
      }
    } catch (error) {
      console.error("Failed to fetch campaign details:", error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "text-green-600 bg-green-100";
      case "paused":
        return "text-yellow-600 bg-yellow-100";
      case "completed":
        return "text-blue-600 bg-blue-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  const getProgressPercentage = (received: number, targeted: number) => {
    if (targeted === 0) return 0;
    return Math.round((received / targeted) * 100);
  };

  const getTimeUntilCheckIn = (scheduledTime: string) => {
    const now = new Date();
    const checkIn = new Date(scheduledTime);
    const diff = checkIn.getTime() - now.getTime();

    if (diff <= 0) return "Now";

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const triggerEscalation = async (campaignId: string) => {
    try {
      const response = await fetch(
        `/api/admin/campaigns/${campaignId}/escalate`,
        {
          method: "POST",
        }
      );
      if (response.ok) {
        fetchCampaigns();
        alert("Escalation triggered - adding more contractors to campaign");
      }
    } catch (error) {
      console.error("Failed to trigger escalation:", error);
    }
  };

  const fetchTavilyContractors = async () => {
    try {
      const response = await fetch("/api/admin/potential-contractors-tavily");
      if (response.ok) {
        const data = await response.json();
        setTavilyContractors(data.contractors || []);
      }
    } catch (error) {
      console.error("Failed to fetch Tavily contractors:", error);
    }
  };

  const testCDADiscovery = async () => {
    setCdaLoading(true);
    setCdaResults(null);
    
    try {
      const response = await fetch("/api/admin/test-cda-discovery", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_type: "kitchen remodel",
          location_city: "Fort Lauderdale",
          location_state: "FL",
          contractors_needed: 5
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setCdaResults(data);
        // Refresh Tavily contractors list
        fetchTavilyContractors();
      } else {
        const error = await response.json();
        setCdaResults({ success: false, error: error.detail || "Test failed" });
      }
    } catch (error) {
      console.error("CDA test failed:", error);
      setCdaResults({ success: false, error: String(error) });
    } finally {
      setCdaLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Campaign Manager</h2>
        <div className="flex gap-4 items-center">
          <button
            onClick={() => setShowCDATest(!showCDATest)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            {showCDATest ? "Hide" : "Test"} CDA Discovery
          </button>
          <span className="text-sm text-gray-500">
            Active: {campaigns.filter((c) => c.campaign_status === "active").length}
          </span>
          <span className="text-sm text-gray-500">Total: {campaigns.length}</span>
        </div>
      </div>

      {/* CDA Testing Interface */}
      {showCDATest && (
        <div className="mb-8 p-6 bg-blue-50 rounded-lg border-l-4 border-blue-500">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-blue-900">CDA Discovery Testing</h3>
            <div className="flex gap-2">
              <span className="text-sm text-blue-700">
                Tavily Enriched: {tavilyContractors.length}
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Test Controls */}
            <div>
              <button
                onClick={testCDADiscovery}
                disabled={cdaLoading}
                className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed mb-4"
              >
                {cdaLoading ? "Running CDA Discovery..." : "Test CDA Discovery"}
              </button>
              
              <p className="text-sm text-blue-700 mb-2">
                This will test the CDA agent with Tavily enrichment for "kitchen remodel" in Fort Lauderdale, FL
              </p>
              
              {/* Existing Tavily Contractors */}
              <div className="bg-white rounded p-4">
                <h4 className="font-medium text-gray-900 mb-2">Existing Tavily-Enriched Contractors</h4>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {tavilyContractors.slice(0, 5).map((contractor) => (
                    <div key={contractor.id} className="text-sm border-l-3 border-green-400 pl-2">
                      <p className="font-medium">{contractor.company_name}</p>
                      <p className="text-gray-600 text-xs">{contractor.ai_business_summary?.substring(0, 100)}...</p>
                    </div>
                  ))}
                  {tavilyContractors.length > 5 && (
                    <p className="text-xs text-gray-500">...and {tavilyContractors.length - 5} more</p>
                  )}
                </div>
              </div>
            </div>
            
            {/* Test Results */}
            <div>
              {cdaLoading && (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-2 text-blue-700">CDA agent working...</span>
                </div>
              )}
              
              {cdaResults && (
                <div className="bg-white rounded p-4">
                  <h4 className="font-medium text-gray-900 mb-3">CDA Test Results</h4>
                  
                  {cdaResults.success ? (
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="font-medium">Total Found:</span>
                          <span className="ml-2">{cdaResults.cda_results?.total_found || 0}</span>
                        </div>
                        <div>
                          <span className="font-medium">Selected:</span>
                          <span className="ml-2">{cdaResults.cda_results?.selected_count || 0}</span>
                        </div>
                        <div>
                          <span className="font-medium">Tavily Enriched:</span>
                          <span className="ml-2 text-green-600 font-medium">
                            {cdaResults.cda_results?.tavily_enriched_count || 0}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium">Tier 3 (Web):</span>
                          <span className="ml-2">{cdaResults.cda_results?.tier_results?.tier3_web || 0}</span>
                        </div>
                      </div>
                      
                      <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                        {cdaResults.cda_results?.explanation}
                      </div>
                      
                      {/* Show discovered contractors with Tavily data */}
                      {cdaResults.discovered_contractors && cdaResults.discovered_contractors.length > 0 && (
                        <div>
                          <h5 className="font-medium text-sm mb-2">Discovered Contractors:</h5>
                          <div className="space-y-2 max-h-40 overflow-y-auto">
                            {cdaResults.discovered_contractors.map((contractor: any) => (
                              <div key={contractor.id} className={`text-xs p-2 rounded border ${contractor.is_tavily_enriched ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                                <div className="flex justify-between items-start">
                                  <div className="flex-1">
                                    <p className="font-medium">{contractor.company_name}</p>
                                    <p className="text-gray-600">Score: {contractor.match_score}</p>
                                    {contractor.is_tavily_enriched && contractor.ai_business_summary && (
                                      <p className="text-green-700 mt-1">{contractor.ai_business_summary.substring(0, 80)}...</p>
                                    )}
                                  </div>
                                  {contractor.is_tavily_enriched && (
                                    <span className="text-xs bg-green-100 text-green-800 px-1 py-0.5 rounded font-medium">
                                      AI Enhanced
                                    </span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-red-600 text-sm">
                      <p className="font-medium">Test Failed:</p>
                      <p>{cdaResults.error}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Campaign List */}
      <div className="space-y-4">
        {campaigns.map((campaign) => (
          <div
            key={campaign.campaign_id}
            className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => fetchCampaignDetails(campaign.campaign_id)}
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold text-lg">{campaign.bid_card_number}</h3>
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(campaign.campaign_status)}`}
                  >
                    {campaign.campaign_status}
                  </span>
                  {campaign.urgency_level && (
                    <span className="text-xs text-gray-500">
                      <Timer className="inline w-3 h-3 mr-1" />
                      {campaign.urgency_level}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {campaign.project_type.replace(/_/g, " ")}
                </p>
              </div>

              <div className="flex gap-6 text-sm">
                <div className="text-center">
                  <Users className="w-5 h-5 mx-auto mb-1 text-gray-400" />
                  <p className="font-semibold">{campaign.contractors_targeted}</p>
                  <p className="text-xs text-gray-500">Targeted</p>
                </div>
                <div className="text-center">
                  <Mail className="w-5 h-5 mx-auto mb-1 text-gray-400" />
                  <p className="font-semibold">{campaign.responses_received}</p>
                  <p className="text-xs text-gray-500">Responses</p>
                </div>
                <div className="text-center">
                  <TrendingUp className="w-5 h-5 mx-auto mb-1 text-gray-400" />
                  <p className="font-semibold">
                    {getProgressPercentage(
                      campaign.responses_received,
                      campaign.contractors_targeted
                    )}
                    %
                  </p>
                  <p className="text-xs text-gray-500">Progress</p>
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{
                    width: `${getProgressPercentage(campaign.responses_received, campaign.contractors_targeted)}%`,
                  }}
                />
              </div>
            </div>

            {/* Check-in Timer */}
            {campaign.check_ins && campaign.check_ins.length > 0 && (
              <div className="mt-3 flex items-center gap-4 text-xs">
                {campaign.check_ins
                  .filter((ci) => ci.status === "pending")
                  .map((checkIn, idx) => (
                    <div key={idx} className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-gray-400" />
                      <span className="text-gray-600">
                        {checkIn.check_in_percentage}% check-in in{" "}
                        {getTimeUntilCheckIn(checkIn.scheduled_time)}
                      </span>
                      {checkIn.escalation_needed && (
                        <AlertCircle className="w-3 h-3 text-yellow-500 ml-1" />
                      )}
                    </div>
                  ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Campaign Details Modal */}
      {showDetails && selectedCampaign && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-xl font-bold">{selectedCampaign.bid_card_number}</h3>
                <p className="text-gray-600">{selectedCampaign.project_type}</p>
              </div>
              <button
                onClick={() => setShowDetails(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            {/* Check-in Timeline */}
            <div className="mb-6">
              <h4 className="font-semibold mb-3">Check-in Timeline</h4>
              <div className="space-y-2">
                {selectedCampaign.check_ins?.map((checkIn, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          checkIn.on_track ? "bg-green-100" : "bg-yellow-100"
                        }`}
                      >
                        {checkIn.check_in_percentage}%
                      </div>
                      <div>
                        <p className="font-medium">
                          {checkIn.status === "completed"
                            ? "Completed"
                            : `Due in ${getTimeUntilCheckIn(checkIn.scheduled_time)}`}
                        </p>
                        <p className="text-sm text-gray-500">
                          Expected: {checkIn.bids_expected} bids | Received: {checkIn.bids_received}
                        </p>
                      </div>
                    </div>
                    {checkIn.escalation_needed && checkIn.status === "pending" && (
                      <button
                        onClick={() => triggerEscalation(selectedCampaign.campaign_id)}
                        className="flex items-center gap-2 px-3 py-1 bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200"
                      >
                        <Plus className="w-4 h-4" />
                        Add {checkIn.additional_contractors_needed} contractors
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Contractors in Campaign */}
            <div>
              <h4 className="font-semibold mb-3">Contractors in Campaign</h4>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {selectedCampaign.contractors?.map((contractor) => (
                  <div key={contractor.assignment_id || contractor.id} className="border rounded-lg p-4 bg-white shadow-sm">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="font-semibold text-gray-900">{contractor.company_name}</p>
                          {contractor.is_tavily_enriched && (
                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full font-medium">
                              AI Enhanced
                            </span>
                          )}
                          {contractor.verified && (
                            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full font-medium">
                              Verified
                            </span>
                          )}
                        </div>
                        
                        <div className="space-y-1 text-sm text-gray-600">
                          <p>
                            <span className="font-medium">Tier {contractor.tier}</span> | 
                            <span className="ml-1 capitalize">{contractor.source.replace(/_/g, ' ')}</span>
                          </p>
                          
                          {contractor.contact_name && (
                            <p>Contact: {contractor.contact_name}</p>
                          )}
                          
                          {contractor.rating && (
                            <p>Rating: {contractor.rating}/5 ({contractor.review_count || 0} reviews)</p>
                          )}
                          
                          {contractor.years_in_business && (
                            <p>{contractor.years_in_business} years in business</p>
                          )}
                          
                          {contractor.phone && (
                            <p>Phone: {contractor.phone}</p>
                          )}
                          
                          {contractor.website && (
                            <p>
                              <a href={contractor.website} target="_blank" rel="noopener noreferrer" 
                                 className="text-blue-600 hover:text-blue-800 underline">
                                Website
                              </a>
                            </p>
                          )}
                        </div>
                        
                        {/* Specialties */}
                        {contractor.specialties && contractor.specialties.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {contractor.specialties.slice(0, 4).map((spec, idx) => (
                              <span key={idx} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                                {spec}
                              </span>
                            ))}
                            {contractor.specialties.length > 4 && (
                              <span className="text-xs text-gray-500">+{contractor.specialties.length - 4} more</span>
                            )}
                          </div>
                        )}
                        
                        {/* Tavily AI Summary */}
                        {contractor.ai_business_summary && (
                          <div className="mt-2 p-2 bg-blue-50 rounded text-xs">
                            <p className="font-medium text-blue-800 mb-1">AI Business Summary:</p>
                            <p className="text-blue-700">{contractor.ai_business_summary}</p>
                          </div>
                        )}
                        
                        {/* Verification badges */}
                        <div className="flex gap-2 mt-2">
                          {contractor.license_verified && (
                            <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded border border-green-200">
                              License Verified
                            </span>
                          )}
                          {contractor.insurance_verified && (
                            <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded border border-green-200">
                              Insured
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex flex-col items-end gap-1">
                        <span
                          className={`text-xs px-2 py-1 rounded font-medium ${
                            contractor.status === "bid_submitted"
                              ? "bg-green-100 text-green-700"
                              : contractor.status === "responded"
                                ? "bg-blue-100 text-blue-700"
                                : contractor.status === "contacted"
                                  ? "bg-gray-100 text-gray-700"
                                  : "bg-yellow-100 text-yellow-700"
                          }`}
                        >
                          {contractor.status.replace(/_/g, " ")}
                        </span>
                        
                        {contractor.assigned_at && (
                          <p className="text-xs text-gray-500">
                            Assigned: {new Date(contractor.assigned_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CampaignManager;
