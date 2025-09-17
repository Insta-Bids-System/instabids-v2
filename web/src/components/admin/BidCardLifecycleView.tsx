import type React from "react";
import { useEffect, useState } from "react";
import { supabase } from "../../lib/supabase";
import type {
  BidCard,
  BidCardView,
  ContractorLead,
  ContractorOutreachAttempt,
  DiscoveryRun,
  EngagementEvent,
  OutreachCampaign,
  SubmittedBid,
} from "../../types";

interface DiscoveryCache {
  id: string;
  bid_card_id: string;
  search_criteria: Record<string, unknown>;
  contractors_found: number;
  cached_at: string;
}

interface ChannelBreakdown {
  email: number;
  form: number;
  sms: number;
  phone: number;
}

interface SuccessRates {
  email: { sent: number; delivered: number; opened: number; clicked: number; percentage: number };
  form: { sent: number; submitted: number; percentage: number };
  sms: { sent: number; delivered: number; percentage: number };
  phone: { attempted: number; connected: number; percentage: number };
}

interface ResponseTracking {
  id: string;
  contractor_id: string;
  response_type: string;
  response_time: string;
  message: string;
}

interface TimelineEvent {
  id: string;
  event_type: string;
  description: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

interface ConnectionFeeData {
  winner_selected: boolean;
  winner_contractor_id: string | null;
  winner_selected_at: string | null;
  winning_bid_amount: number | null;
  connection_fee_calculated: boolean;
  connection_fee_data: {
    fee_id: string | null;
    base_fee_amount: number | null;
    final_fee_amount: number | null;
    category_adjustment: number | null;
    fee_status: string;
    payment_processed_at: string | null;
    payment_method: string | null;
    payment_transaction_id: string | null;
  } | null;
}

interface LifecycleMetrics {
  completion: {
    bids_received: number;
    bids_needed: number;
    completion_percentage: number;
    is_complete: boolean;
  };
  discovery: {
    contractors_discovered: number;
    discovery_runs: number;
  };
  outreach: {
    total_attempts: number;
    channels_used: number;
    channel_breakdown: ChannelBreakdown;
    success_rates: SuccessRates;
  };
  engagement: {
    total_views: number;
    total_engagements: number;
    engagement_rate: number;
  };
  bids: {
    average_bid: number;
    minimum_bid: number;
    maximum_bid: number;
    bid_spread: number;
    bid_range_percentage: number;
  };
  timeline: {
    age_hours: number;
    age_days: number;
    is_recent: boolean;
    created_at: string;
  };
}

interface ChangeLog {
  id: string;
  bid_card_id: string;
  bid_card_number: string;
  change_type: string;
  changed_fields: string[];
  before_state: Record<string, any>;
  after_state: Record<string, any>;
  change_summary: string;
  significance_level: string;
  source_agent: string;
  source_context: Record<string, any>;
  conversation_snippet: string;
  detected_change_hints: string[];
  approval_status: string;
  contractors_notified: number;
  notification_sent_at: string | null;
  created_at: string;
  created_by: string;
  time_ago: string;
  change_impact: string;
  change_category: string;
  approval_required: boolean;
}

interface ChangeHistoryData {
  change_logs: ChangeLog[];
  summary: {
    total_changes: number;
    pending_approval: number;
    major_changes: number;
    agent_breakdown: Record<string, number>;
    most_active_agent: string | null;
  };
}

interface LifecycleData {
  bid_card: BidCard;
  discovery: {
    discovery_runs: DiscoveryRun[];
    discovery_cache: DiscoveryCache | null;
    potential_contractors: ContractorLead[];
    contractor_leads: ContractorLead[];
  };
  campaigns: OutreachCampaign[];
  outreach: {
    outreach_attempts: ContractorOutreachAttempt[];
    channel_breakdown: ChannelBreakdown;
    success_rates: SuccessRates;
    response_tracking: ResponseTracking[];
  };
  engagement: {
    views: BidCardView[];
    engagement_events: EngagementEvent[];
    email_tracking: EngagementEvent[];
    contractor_responses: ResponseTracking[];
  };
  bids: EnhancedSubmittedBid[];
  timeline: TimelineEvent[];
  metrics: LifecycleMetrics;
  connection_fee: ConnectionFeeData;
}

interface EnhancedSubmittedBid extends SubmittedBid {
  is_lowest?: boolean;
  is_highest?: boolean;
  timeline_days?: number;
  start_date?: string;
  bid_content?: string;
  contractor_email?: string;
  contractor_phone?: string;
}

interface BidCardLifecycleViewProps {
  bidCardId: string;
  onClose: () => void;
}

const BidCardLifecycleView: React.FC<BidCardLifecycleViewProps> = ({ bidCardId, onClose }) => {
  const [lifecycleData, setLifecycleData] = useState<LifecycleData | null>(null);
  const [changeHistoryData, setChangeHistoryData] = useState<ChangeHistoryData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadLifecycleData = async () => {
      try {
        setIsLoading(true);
        console.log("Loading lifecycle for bid card ID:", bidCardId);
        const response = await fetch(`/api/bid-cards/${bidCardId}/lifecycle`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("admin_session_id")}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          // Handle both wrapped and unwrapped responses
          if (data.success && data.data) {
            setLifecycleData(data.data);
          } else if (data.bid_card) {
            // Direct response from API
            setLifecycleData(data);
          } else {
            setError(data.error || data.detail || "Failed to load bid card lifecycle data");
          }
        } else {
          const errorData = await response.json().catch(() => ({}));
          setError(
            errorData.detail || `Failed to load bid card lifecycle data (${response.status})`
          );
        }

        // Load change history data
        try {
          const changeHistoryResponse = await fetch(`/api/bid-cards/${bidCardId}/change-history`, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("admin_session_id")}`,
            },
          });

          if (changeHistoryResponse.ok) {
            const changeHistoryData = await changeHistoryResponse.json();
            setChangeHistoryData(changeHistoryData);
          } else {
            console.warn('Failed to load change history:', changeHistoryResponse.status);
            setChangeHistoryData({ change_logs: [], summary: { total_changes: 0, pending_approval: 0, major_changes: 0, agent_breakdown: {}, most_active_agent: null } });
          }
        } catch (changeHistoryError) {
          console.warn('Error loading change history:', changeHistoryError);
          setChangeHistoryData({ change_logs: [], summary: { total_changes: 0, pending_approval: 0, major_changes: 0, agent_breakdown: {}, most_active_agent: null } });
        }
      } catch (err) {
        setError("Error loading lifecycle data");
        console.error("Error:", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadLifecycleData();

    // Set up WebSocket subscriptions for real-time updates
    const bidCardSubscription = supabase
      .channel(`bid_card_changes:${bidCardId}`)
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "bid_cards",
          filter: `id=eq.${bidCardId}`,
        },
        (payload) => {
          console.log("Bid card updated:", payload);
          // Reload lifecycle data when bid card is updated
          loadLifecycleData();
        }
      )
      .subscribe();

    const changeLogSubscription = supabase
      .channel(`change_logs:${bidCardId}`)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "bid_card_change_logs",
          filter: `bid_card_id=eq.${bidCardId}`,
        },
        async (payload) => {
          console.log("New change log:", payload);
          // Reload change history when new change is logged
          try {
            const changeHistoryResponse = await fetch(`/api/bid-cards/${bidCardId}/change-history`, {
              headers: {
                Authorization: `Bearer ${localStorage.getItem("admin_session_id")}`,
              },
            });

            if (changeHistoryResponse.ok) {
              const changeHistoryData = await changeHistoryResponse.json();
              setChangeHistoryData(changeHistoryData);
              
              // Show notification for new change
              if (payload.new) {
                const change = payload.new as any;
                console.log(`New change detected: ${change.change_summary} from ${change.source_agent}`);
              }
            }
          } catch (error) {
            console.error('Error reloading change history:', error);
          }
        }
      )
      .subscribe();

    // Cleanup subscriptions on unmount
    return () => {
      bidCardSubscription.unsubscribe();
      changeLogSubscription.unsubscribe();
    };
  }, [bidCardId]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "generated":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "collecting_bids":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "bids_complete":
        return "bg-green-100 text-green-800 border-green-200";
      case "expired":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case "emergency":
        return "text-red-600 bg-red-50";
      case "urgent":
        return "text-orange-600 bg-orange-50";
      case "standard":
        return "text-blue-600 bg-blue-50";
      case "flexible":
        return "text-green-600 bg-green-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInHours = (now.getTime() - time.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) return "Just now";
    if (diffInHours < 24) return `${Math.floor(diffInHours)}h ago`;
    return `${Math.floor(diffInHours / 24)}d ago`;
  };

  const renderChangeHistoryTab = () => {
    if (!changeHistoryData) {
      return (
        <div className="bg-white rounded-lg p-8 text-center">
          <div className="text-gray-400 text-6xl mb-4">📝</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Change History</h3>
          <p className="text-gray-600">
            Change tracking data is not available for this bid card.
          </p>
        </div>
      );
    }

    const { change_logs, summary } = changeHistoryData;

    if (change_logs.length === 0) {
      return (
        <div className="bg-white rounded-lg p-8 text-center">
          <div className="text-gray-400 text-6xl mb-4">📝</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Changes Yet</h3>
          <p className="text-gray-600">
            This bid card has not been modified by homeowner interactions with other agents.
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* Summary Statistics */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Change Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{summary.total_changes}</div>
              <div className="text-sm text-gray-500">Total Changes</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{summary.major_changes}</div>
              <div className="text-sm text-gray-500">Major Changes</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{summary.pending_approval}</div>
              <div className="text-sm text-gray-500">Pending Approval</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {summary.most_active_agent || "None"}
              </div>
              <div className="text-sm text-gray-500">Most Active Agent</div>
            </div>
          </div>
        </div>

        {/* Agent Breakdown */}
        {Object.keys(summary.agent_breakdown).length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Changes by Agent</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(summary.agent_breakdown).map(([agent, count]) => (
                <div key={agent} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-900 capitalize">{agent}</div>
                    <div className="text-sm text-gray-600">{agent === 'cia' ? 'Contractor Interface' : agent === 'messaging' ? 'Messaging System' : agent}</div>
                  </div>
                  <div className="text-xl font-bold text-blue-600">{count}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Change History Timeline */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Change History Timeline</h3>
          <div className="space-y-4">
            {change_logs.map((change, index) => (
              <div key={change.id || index} className="border border-gray-200 rounded-lg p-4">
                {/* Change Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{change.change_category}</span>
                    <div>
                      <h4 className="text-md font-medium text-gray-900">{change.change_summary}</h4>
                      <div className="flex items-center space-x-3 mt-1">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          change.significance_level === 'major' 
                            ? 'bg-red-100 text-red-800' 
                            : change.significance_level === 'moderate' 
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {change.significance_level} impact
                        </span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          change.change_impact === 'high' 
                            ? 'bg-red-100 text-red-800' 
                            : change.change_impact === 'medium' 
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {change.change_impact} change impact
                        </span>
                        <span className="text-sm text-gray-600">by {change.source_agent}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">{change.time_ago}</div>
                </div>

                {/* Changed Fields */}
                {change.changed_fields && change.changed_fields.length > 0 && (
                  <div className="mb-3">
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Fields Changed:</h5>
                    <div className="flex flex-wrap gap-2">
                      {change.changed_fields.map((field, fieldIndex) => (
                        <span key={fieldIndex} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-700">
                          {field.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Before/After States */}
                {change.before_state && change.after_state && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <h6 className="text-sm font-medium text-red-800 mb-2">Before:</h6>
                      <div className="text-sm text-red-700">
                        {Object.entries(change.before_state).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="font-medium">{key.replace('_', ' ')}:</span>
                            <span>{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                      <h6 className="text-sm font-medium text-green-800 mb-2">After:</h6>
                      <div className="text-sm text-green-700">
                        {Object.entries(change.after_state).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="font-medium">{key.replace('_', ' ')}:</span>
                            <span>{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Conversation Snippet */}
                {change.conversation_snippet && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-3">
                    <h6 className="text-sm font-medium text-gray-700 mb-2">Conversation Context:</h6>
                    <p className="text-sm text-gray-600 italic">"{change.conversation_snippet}"</p>
                  </div>
                )}

                {/* Contractor Notification Info */}
                {change.contractors_notified > 0 && (
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-2">
                      <span className="text-gray-600">Contractors notified:</span>
                      <span className="font-medium text-gray-900">{change.contractors_notified}</span>
                    </div>
                    {change.notification_sent_at && (
                      <span className="text-gray-500">
                        Notified {formatTimeAgo(change.notification_sent_at)}
                      </span>
                    )}
                  </div>
                )}

                {/* Approval Status */}
                {change.approval_required && (
                  <div className="mt-3 flex items-center justify-between">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                      change.approval_status === 'approved' 
                        ? 'bg-green-100 text-green-800'
                        : change.approval_status === 'rejected'
                        ? 'bg-red-100 text-red-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {change.approval_status === 'auto_applied' ? 'Auto Applied' : change.approval_status}
                    </span>
                    {change.approval_status === 'pending' && (
                      <div className="space-x-2">
                        <button 
                          onClick={() => handleApproveChange(change.id, 'approved')}
                          className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
                        >
                          Approve
                        </button>
                        <button 
                          onClick={() => handleApproveChange(change.id, 'rejected')}
                          className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
                        >
                          Reject
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const handleApproveChange = async (changeLogId: string, status: 'approved' | 'rejected') => {
    try {
      const response = await fetch(`/api/bid-cards/${bidCardId}/approve-change/${changeLogId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem("admin_session_id")}`,
        },
        body: JSON.stringify({
          status: status,
          approved_by: 'admin_user', // Could be dynamic based on logged-in user
          rejection_reason: status === 'rejected' ? 'Rejected via admin panel' : undefined
        })
      });

      if (response.ok) {
        // Refresh change history data
        const changeHistoryResponse = await fetch(`/api/bid-cards/${bidCardId}/change-history`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("admin_session_id")}`,
          },
        });

        if (changeHistoryResponse.ok) {
          const changeHistoryData = await changeHistoryResponse.json();
          setChangeHistoryData(changeHistoryData);
        }
      } else {
        console.error('Failed to update change approval status');
      }
    } catch (error) {
      console.error('Error updating change approval:', error);
    }
  };

  const renderOverviewTab = () => {
    if (!lifecycleData) return null;

    const { bid_card, metrics } = lifecycleData;
    const location = null;

    return (
      <div className="space-y-6">
        {/* Header Card */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-4">
                <h2 className="text-2xl font-bold text-gray-900">
                  {bid_card.project_type.charAt(0).toUpperCase() + bid_card.project_type.slice(1)}{" "}
                  Project
                </h2>
                <span
                  className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(bid_card.status)}`}
                >
                  {bid_card.status.replace("_", " ")}
                </span>
                <span
                  className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getUrgencyColor(bid_card.urgency_level)}`}
                >
                  {bid_card.urgency_level}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Bid Card:</span>
                  <div className="text-gray-900 font-mono">{bid_card.bid_card_number}</div>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Location:</span>
                  <div className="text-gray-900">
                    {location && "city" in location && "state" in location
                      ? `${location.city}, ${location.state}`
                      : `${bid_card.location_city || "Unknown"}, ${bid_card.location_state || "Unknown"}`}
                  </div>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Budget Range:</span>
                  <div className="text-gray-900">
                    {bid_card.budget_min && bid_card.budget_max
                      ? `${formatCurrency(bid_card.budget_min)} - ${formatCurrency(bid_card.budget_max)}`
                      : "Not specified"}
                  </div>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Created:</span>
                  <div className="text-gray-900">{formatTimeAgo(bid_card.created_at)}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Progress Section */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Bid Collection Progress</span>
              <span className="text-sm text-gray-600">
                {metrics.completion.bids_received}/{metrics.completion.bids_needed} bids (
                {Math.round(metrics.completion.completion_percentage)}%)
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${
                  metrics.completion.is_complete
                    ? "bg-green-500"
                    : metrics.completion.completion_percentage > 75
                      ? "bg-blue-500"
                      : metrics.completion.completion_percentage > 50
                        ? "bg-yellow-500"
                        : "bg-red-500"
                }`}
                style={{ width: `${Math.min(metrics.completion.completion_percentage, 100)}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Discovery Metrics */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 text-lg">🔍</span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Contractors Found</p>
                <p className="text-lg font-semibold text-gray-900">
                  {metrics.discovery.contractors_discovered}
                </p>
              </div>
            </div>
          </div>

          {/* Outreach Metrics */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <span className="text-yellow-600 text-lg">📧</span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Outreach Sent</p>
                <p className="text-lg font-semibold text-gray-900">
                  {metrics.outreach.total_attempts}
                </p>
              </div>
            </div>
          </div>

          {/* Engagement Metrics */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <span className="text-purple-600 text-lg">👁️</span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Bid Card Views</p>
                <p className="text-lg font-semibold text-gray-900">
                  {metrics.engagement.total_views}
                </p>
              </div>
            </div>
          </div>

          {/* Bid Metrics */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 text-lg">💰</span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Avg Bid Amount</p>
                <p className="text-lg font-semibold text-gray-900">
                  {metrics.bids.average_bid > 0
                    ? formatCurrency(metrics.bids.average_bid)
                    : "No bids"}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Channel Breakdown */}
        {Object.keys(metrics.outreach.channel_breakdown).length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Outreach Channels</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(metrics.outreach.channel_breakdown).map(([channel, count]) => (
                <div key={channel} className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{count}</div>
                  <div className="text-sm text-gray-500 capitalize">{channel}</div>
                  {metrics.outreach.success_rates[channel as keyof SuccessRates] && (
                    <div className="text-xs text-green-600">
                      {Math.round(
                        metrics.outreach.success_rates[channel as keyof SuccessRates].percentage
                      )}
                      % success
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderCampaignOutreachTab = () => {
    const campaigns = lifecycleData?.campaigns || [];

    // Get all contractors from contractor_leads
    const contractorLeads = lifecycleData?.discovery?.contractor_leads || [];

    // Map contractors with their outreach status
    const contractorsWithOutreach = contractorLeads.map((lead) => {
      const outreachAttempts =
        lifecycleData?.outreach?.outreach_attempts?.filter(
          (attempt) => attempt.contractor_lead_id === lead.id
        ) || [];

      // Check outreach status for each channel
      const emailAttempts = outreachAttempts.filter((a) => a.channel === "email");
      const formAttempts = outreachAttempts.filter((a) => a.channel === "form");
      const smsAttempts = outreachAttempts.filter((a) => a.channel === "sms");
      const phoneAttempts = outreachAttempts.filter((a) => a.channel === "phone");

      // Check for responses
      const hasResponse = outreachAttempts.some((a) => a.response_received_at);
      const hasBidSubmitted = outreachAttempts.some((a) => a.status === "bid_submitted");

      return {
        ...lead,
        outreach: {
          email: {
            attempted: emailAttempts.length > 0,
            success: emailAttempts.some((a) => a.status === "delivered" || a.status === "opened"),
            count: emailAttempts.length,
            lastAttempt: emailAttempts[emailAttempts.length - 1],
          },
          form: {
            attempted: formAttempts.length > 0,
            success: formAttempts.some((a) => a.status === "sent" || a.status === "delivered"),
            count: formAttempts.length,
            lastAttempt: formAttempts[formAttempts.length - 1],
          },
          sms: {
            attempted: smsAttempts.length > 0,
            success: smsAttempts.some((a) => a.status === "delivered"),
            count: smsAttempts.length,
            lastAttempt: smsAttempts[smsAttempts.length - 1],
          },
          phone: {
            attempted: phoneAttempts.length > 0,
            success: phoneAttempts.some((a) => a.status === "sent" || a.status === "delivered"),
            count: phoneAttempts.length,
            lastAttempt: phoneAttempts[phoneAttempts.length - 1],
          },
        },
        hasResponse,
        hasBidSubmitted,
        tier: lead.status === "contacted" ? 1 : lead.status === "enriched" ? 2 : 3,
        tier_name:
          lead.status === "contacted"
            ? "Internal"
            : lead.status === "enriched"
              ? "Prospects"
              : "New/Cold",
      };
    });

    // Get the active campaign (most recent)
    const activeCampaign = campaigns.find((c) => c.status === "active") || campaigns[0];

    return (
      <div className="space-y-6">
        {/* Campaign Overview */}
        {activeCampaign && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Active Campaign</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Started: {new Date(activeCampaign.created_at).toLocaleString()}
                </p>
              </div>
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  activeCampaign.status === "completed"
                    ? "bg-green-100 text-green-800"
                    : activeCampaign.status === "active"
                      ? "bg-blue-100 text-blue-800"
                      : "bg-gray-100 text-gray-800"
                }`}
              >
                {activeCampaign.status || "draft"}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div>
                <div className="text-sm text-gray-600">Target</div>
                <div className="text-xl font-semibold text-gray-900">
                  {activeCampaign.max_contractors || 0}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Contacted</div>
                <div className="text-xl font-semibold text-blue-600">
                  {activeCampaign.contractors_targeted || 0}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Responded</div>
                <div className="text-xl font-semibold text-green-600">
                  {activeCampaign.responses_received || 0}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Response Rate</div>
                <div className="text-xl font-semibold text-purple-600">
                  {activeCampaign.contractors_targeted > 0
                    ? Math.round(
                        (activeCampaign.responses_received / activeCampaign.contractors_targeted) *
                          100
                      )
                    : 0}
                  %
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Bids Received</div>
                <div className="text-xl font-semibold text-indigo-600">
                  {contractorsWithOutreach.filter((c) => c.hasBidSubmitted).length}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Contractor List with Live Outreach Tracking */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Contractor Outreach Status ({contractorsWithOutreach.length} contractors)
          </h3>

          {contractorsWithOutreach.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-4">👥</div>
              <p className="text-gray-600">
                No contractors have been selected for this campaign yet.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {contractorsWithOutreach.map((contractor, index) => (
                <div key={contractor.id || index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="text-md font-medium text-gray-900">
                        {contractor.business_name || "Unknown Contractor"}
                      </h4>
                      <div className="flex items-center space-x-3 mt-1">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            contractor.tier === 1
                              ? "bg-green-100 text-green-800 border-green-200"
                              : contractor.tier === 2
                                ? "bg-blue-100 text-blue-800 border-blue-200"
                                : "bg-gray-100 text-gray-800 border-gray-200"
                          } border`}
                        >
                          Tier {contractor.tier}: {contractor.tier_name}
                        </span>
                        {contractor.hasResponse && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            ✉️ Responded
                          </span>
                        )}
                        {contractor.hasBidSubmitted && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            💰 Bid Submitted
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-sm text-gray-600">
                      Score: {contractor.lead_score || 0}/100
                    </div>
                  </div>

                  {/* Contact Information */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm mb-3">
                    <div>
                      <span className="font-medium text-gray-600">Email:</span>
                      <div className="text-gray-900">{contractor.email || "No email"}</div>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Phone:</span>
                      <div className="text-gray-900">{contractor.phone || "No phone"}</div>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Website:</span>
                      <div className="text-gray-900">
                        {contractor.website && contractor.website !== "No website" ? (
                          <a
                            href={contractor.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 underline"
                          >
                            View Site
                          </a>
                        ) : (
                          "No website"
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Outreach Channel Status */}
                  <div className="border-t border-gray-200 pt-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">Outreach Channels:</div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {/* Email Status */}
                      <div
                        className={`flex items-center space-x-2 p-2 rounded-lg border ${
                          contractor.outreach.email.success
                            ? "bg-green-50 border-green-200"
                            : contractor.outreach.email.attempted
                              ? "bg-yellow-50 border-yellow-200"
                              : "bg-gray-50 border-gray-200"
                        }`}
                      >
                        <span className="text-lg">📧</span>
                        <div className="flex-1">
                          <div className="text-xs font-medium text-gray-700">Email</div>
                          <div className="text-xs text-gray-600">
                            {contractor.outreach.email.success
                              ? "✅ Sent"
                              : contractor.outreach.email.attempted
                                ? "⏳ Attempted"
                                : "⭕ Not Sent"}
                          </div>
                        </div>
                      </div>

                      {/* Form Status */}
                      <div
                        className={`flex items-center space-x-2 p-2 rounded-lg border ${
                          contractor.outreach.form.success
                            ? "bg-green-50 border-green-200"
                            : contractor.outreach.form.attempted
                              ? "bg-yellow-50 border-yellow-200"
                              : "bg-gray-50 border-gray-200"
                        }`}
                      >
                        <span className="text-lg">📝</span>
                        <div className="flex-1">
                          <div className="text-xs font-medium text-gray-700">Form</div>
                          <div className="text-xs text-gray-600">
                            {contractor.outreach.form.success
                              ? "✅ Filled"
                              : contractor.outreach.form.attempted
                                ? "⏳ Attempted"
                                : "⭕ Not Filled"}
                          </div>
                        </div>
                      </div>

                      {/* SMS Status */}
                      <div
                        className={`flex items-center space-x-2 p-2 rounded-lg border ${
                          contractor.outreach.sms.success
                            ? "bg-green-50 border-green-200"
                            : contractor.outreach.sms.attempted
                              ? "bg-yellow-50 border-yellow-200"
                              : "bg-gray-50 border-gray-200"
                        }`}
                      >
                        <span className="text-lg">💬</span>
                        <div className="flex-1">
                          <div className="text-xs font-medium text-gray-700">SMS</div>
                          <div className="text-xs text-gray-600">
                            {contractor.outreach.sms.success
                              ? "✅ Sent"
                              : contractor.outreach.sms.attempted
                                ? "⏳ Attempted"
                                : "⭕ Not Sent"}
                          </div>
                        </div>
                      </div>

                      {/* Phone Status */}
                      <div
                        className={`flex items-center space-x-2 p-2 rounded-lg border ${
                          contractor.outreach.phone.success
                            ? "bg-green-50 border-green-200"
                            : contractor.outreach.phone.attempted
                              ? "bg-yellow-50 border-yellow-200"
                              : "bg-gray-50 border-gray-200"
                        }`}
                      >
                        <span className="text-lg">📞</span>
                        <div className="flex-1">
                          <div className="text-xs font-medium text-gray-700">Phone</div>
                          <div className="text-xs text-gray-600">
                            {contractor.outreach.phone.success
                              ? "✅ Called"
                              : contractor.outreach.phone.attempted
                                ? "⏳ Attempted"
                                : "⭕ Not Called"}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Campaign Check-ins (if available) */}
        {activeCampaign?.check_ins && activeCampaign.check_ins.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Campaign Check-ins</h3>
            <div className="space-y-3">
              {activeCampaign.check_ins.map((checkIn: any, index: number) => (
                <div
                  key={checkIn.id || index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <span
                      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                        checkIn.status === "completed"
                          ? "bg-green-100 text-green-800"
                          : checkIn.status === "pending"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {checkIn.check_in_percentage}%
                    </span>
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {new Date(checkIn.scheduled_time).toLocaleString()}
                      </div>
                      <div className="text-xs text-gray-600">
                        Expected: {checkIn.bids_expected} bids | Received: {checkIn.bids_received}{" "}
                        bids
                      </div>
                    </div>
                  </div>
                  <div className="text-sm">
                    {checkIn.on_track ? (
                      <span className="text-green-600">✅ On Track</span>
                    ) : (
                      <span className="text-red-600">⚠️ Needs Escalation</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderCampaignsTab = () => {
    const campaigns = lifecycleData?.campaigns || [];

    if (campaigns.length === 0) {
      return (
        <div className="bg-white rounded-lg p-8 text-center">
          <div className="text-gray-400 text-6xl mb-4">🎯</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Campaigns</h3>
          <p className="text-gray-600">
            No outreach campaigns have been created for this bid card yet.
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Outreach Campaigns</h3>
          <div className="space-y-4">
            {campaigns.map((campaign) => (
              <div key={campaign.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h4 className="text-md font-medium text-gray-900">
                      Campaign #{campaign.id.substring(0, 8)}
                    </h4>
                    <p className="text-sm text-gray-600 mt-1">
                      Created: {new Date(campaign.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                      campaign.status === "completed"
                        ? "bg-green-100 text-green-800"
                        : campaign.status === "active"
                          ? "bg-blue-100 text-blue-800"
                          : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {campaign.status || "draft"}
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <div className="text-sm text-gray-600">Max Contractors</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {campaign.max_contractors || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Contractors Targeted</div>
                    <div className="text-lg font-semibold text-blue-600">
                      {campaign.contractors_targeted || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Responses Received</div>
                    <div className="text-lg font-semibold text-green-600">
                      {campaign.responses_received || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Response Rate</div>
                    <div className="text-lg font-semibold text-purple-600">
                      {campaign.contractors_targeted > 0
                        ? Math.round(
                            (campaign.responses_received / campaign.contractors_targeted) * 100
                          )
                        : 0}
                      %
                    </div>
                  </div>
                </div>

                {/* Check-ins if available */}
                {campaign.check_ins && campaign.check_ins.length > 0 && (
                  <div className="border-t border-gray-200 pt-4">
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Campaign Check-ins</h5>
                    <div className="space-y-2">
                      {campaign.check_ins.map((checkIn: any, index: number) => (
                        <div
                          key={checkIn.id || index}
                          className="flex items-center justify-between text-sm"
                        >
                          <div className="flex items-center space-x-2">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                                checkIn.status === "completed"
                                  ? "bg-green-100 text-green-800"
                                  : checkIn.status === "pending"
                                    ? "bg-yellow-100 text-yellow-800"
                                    : "bg-gray-100 text-gray-800"
                              }`}
                            >
                              {checkIn.check_in_percentage}%
                            </span>
                            <span className="text-gray-600">
                              {new Date(checkIn.scheduled_time).toLocaleString()}
                            </span>
                          </div>
                          <div className="text-gray-600">
                            {checkIn.on_track ? "✅ On Track" : "⚠️ Needs Attention"}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderBidsTab = () => {
    if (!lifecycleData?.bids.length) {
      return (
        <div className="text-center py-8">
          <div className="text-gray-400 text-4xl mb-4">💰</div>
          <p className="text-gray-500">No bids submitted yet</p>
          <p className="text-sm text-gray-400 mt-1">
            Bids will appear here when contractors respond
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {lifecycleData.bids.map((bid, index) => (
          <div key={bid.id || index} className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h4 className="text-lg font-medium text-gray-900">{bid.contractor_name}</h4>
                  {bid.is_lowest && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Lowest Bid
                    </span>
                  )}
                  {bid.is_highest && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Highest Bid
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                  <div>
                    <span className="font-medium text-gray-700">Bid Amount:</span>
                    <div className="text-lg font-bold text-gray-900">
                      {formatCurrency(bid.bid_amount)}
                    </div>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Timeline:</span>
                    <div className="text-gray-900">
                      {bid.timeline_days ? `${bid.timeline_days} days` : bid.timeline_estimate}
                    </div>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Start Date:</span>
                    <div className="text-gray-900">
                      {bid.start_date
                        ? new Date(bid.start_date).toLocaleDateString()
                        : bid.start_date_available
                          ? new Date(bid.start_date_available).toLocaleDateString()
                          : "Not specified"}
                    </div>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Submitted:</span>
                    <div className="text-gray-900">{formatTimeAgo(bid.submitted_at)}</div>
                  </div>
                </div>

                <div className="mb-4">
                  <span className="font-medium text-gray-700">Bid Details:</span>
                  <p className="text-gray-600 mt-1">{bid.bid_content || bid.proposal_details}</p>
                </div>

                <div className="flex items-center text-sm text-gray-500">
                  <span>📧 {bid.contractor_email || "Email not provided"}</span>
                  <span className="mx-2">•</span>
                  <span>📞 {bid.contractor_phone || "Phone not provided"}</span>
                  <span className="mx-2">•</span>
                  <span>Via {bid.submission_method}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderContractorsTab = () => {
    if (!lifecycleData) return null;

    // Get contractor data from contractor_leads table (primary source)
    // This is the authoritative source of all contractors that have been discovered for this bid card
    const contractorLeads = lifecycleData.discovery?.contractor_leads || [];

    // Map contractor leads to display format with outreach data
    const contractors = contractorLeads.map((lead) => ({
      id: lead.id,
      name: lead.business_name || lead.company_name || "Unknown Contractor",
      email: lead.email || "No email",
      phone: lead.phone || "No phone",
      website: lead.website || "No website",
      // Determine tier based on data quality and engagement
      tier: lead.lead_status === "contacted" ? 1 : lead.lead_status === "enriched" ? 2 : 3,
      tier_name:
        lead.lead_status === "contacted"
          ? "Internal"
          : lead.lead_status === "enriched"
            ? "Prospects"
            : "New/Cold",
      lead_score: lead.lead_score || 0,
      lead_status: lead.lead_status || "new",
      // Get all outreach attempts for this contractor
      outreach_attempts: lifecycleData.outreach.outreach_attempts.filter(
        (attempt) => attempt.contractor_lead_id === lead.id
      ),
      discovery_run_id: lead.discovery_run_id,
    }));

    // Fallback: if no contractor_leads data, try to get from campaigns (legacy)
    const campaignContractors = lifecycleData.campaigns.flatMap(
      (campaign) =>
        campaign.campaign_contractors?.map((cc) => ({
          id: cc.contractor_id,
          name: cc.contractor_name || cc.business_name || "Unknown Contractor",
          email: cc.email || "No email",
          phone: cc.phone || "No phone",
          website: "No website",
          tier: cc.tier || 3,
          tier_name: cc.tier === 1 ? "Internal" : cc.tier === 2 ? "Prospects" : "New/Cold",
          lead_score: 0,
          lead_status: "unknown",
          outreach_attempts: lifecycleData.outreach.outreach_attempts.filter(
            (attempt) => attempt.contractor_lead_id === cc.id
          ),
          discovery_run_id: null,
        })) || []
    );

    // Use contractor_leads if available, otherwise fall back to campaign_contractors
    const allContractors = contractors.length > 0 ? contractors : campaignContractors;

    if (allContractors.length === 0) {
      return (
        <div className="text-center py-8">
          <div className="text-gray-400 text-4xl mb-4">👥</div>
          <p className="text-gray-500">No contractors reached out to yet</p>
          <p className="text-sm text-gray-400 mt-1">
            Contractors will appear here once campaigns start outreach
          </p>
        </div>
      );
    }

    const getTierColor = (tier: number) => {
      switch (tier) {
        case 1:
          return "bg-green-100 text-green-800 border-green-200";
        case 2:
          return "bg-blue-100 text-blue-800 border-blue-200";
        case 3:
          return "bg-gray-100 text-gray-800 border-gray-200";
        default:
          return "bg-gray-100 text-gray-800 border-gray-200";
      }
    };

    const getOutreachStatus = (attempts: any[], channel: string) => {
      const channelAttempts = attempts.filter((a) => a.channel === channel);
      if (channelAttempts.length === 0) return { attempted: false, success: false };

      const successful = channelAttempts.some(
        (a) => a.status === "delivered" || a.status === "sent" || a.status === "opened"
      );
      return { attempted: true, success: successful };
    };

    return (
      <div className="space-y-4">
        {/* Summary Stats */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
          <h4 className="text-lg font-medium text-gray-900 mb-3">Contractor Outreach Summary</h4>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {allContractors.filter((c) => c.tier === 1).length}
              </div>
              <div className="text-sm text-gray-500">Tier 1 (Internal)</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {allContractors.filter((c) => c.tier === 2).length}
              </div>
              <div className="text-sm text-gray-500">Tier 2 (Prospects)</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">
                {allContractors.filter((c) => c.tier === 3).length}
              </div>
              <div className="text-sm text-gray-500">Tier 3 (New/Cold)</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{allContractors.length}</div>
              <div className="text-sm text-gray-500">Total Contacted</div>
            </div>
          </div>
        </div>

        {/* Contractor List */}
        {allContractors.map((contractor, index) => {
          const formStatus = getOutreachStatus(contractor.outreach_attempts, "form");
          const emailStatus = getOutreachStatus(contractor.outreach_attempts, "email");
          const phoneStatus = getOutreachStatus(contractor.outreach_attempts, "phone");

          return (
            <div
              key={contractor.id || index}
              className="bg-white rounded-lg border border-gray-200 p-6"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-3">
                    <h4 className="text-lg font-medium text-gray-900">{contractor.name}</h4>
                    <span
                      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getTierColor(contractor.tier)}`}
                    >
                      Tier {contractor.tier}: {contractor.tier_name}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm mb-4">
                    <div>
                      <span className="font-medium text-gray-700">Email:</span>
                      <div className="text-gray-900">{contractor.email}</div>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Phone:</span>
                      <div className="text-gray-900">{contractor.phone}</div>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Website:</span>
                      <div className="text-gray-900">
                        {contractor.website && contractor.website !== "No website" ? (
                          <a
                            href={contractor.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 underline"
                          >
                            {contractor.website}
                          </a>
                        ) : (
                          "No website"
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Lead Score and Status (if available from contractor_leads) */}
                  {contractor.lead_score > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-4">
                      <div>
                        <span className="font-medium text-gray-700">Lead Score:</span>
                        <div className="flex items-center space-x-2">
                          <div className="text-gray-900">{contractor.lead_score}/100</div>
                          <div
                            className={`h-2 w-16 rounded-full ${
                              contractor.lead_score >= 80
                                ? "bg-green-200"
                                : contractor.lead_score >= 60
                                  ? "bg-yellow-200"
                                  : "bg-red-200"
                            }`}
                          >
                            <div
                              className={`h-2 rounded-full ${
                                contractor.lead_score >= 80
                                  ? "bg-green-500"
                                  : contractor.lead_score >= 60
                                    ? "bg-yellow-500"
                                    : "bg-red-500"
                              }`}
                              style={{ width: `${contractor.lead_score}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Lead Status:</span>
                        <div className="text-gray-900 capitalize">{contractor.lead_status}</div>
                      </div>
                    </div>
                  )}

                  {/* Outreach Methods Status */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h5 className="text-sm font-medium text-gray-700 mb-3">Outreach Methods</h5>
                    <div className="grid grid-cols-3 gap-4">
                      {/* Form Status */}
                      <div className="text-center">
                        <div
                          className={`w-8 h-8 mx-auto mb-2 rounded-full flex items-center justify-center ${
                            formStatus.attempted
                              ? formStatus.success
                                ? "bg-green-100 text-green-600"
                                : "bg-yellow-100 text-yellow-600"
                              : "bg-gray-100 text-gray-400"
                          }`}
                        >
                          {formStatus.attempted ? (formStatus.success ? "✓" : "?") : "○"}
                        </div>
                        <div className="text-xs font-medium text-gray-900">Form</div>
                        <div className="text-xs text-gray-500">
                          {formStatus.attempted
                            ? formStatus.success
                              ? "Sent"
                              : "Attempted"
                            : "Not sent"}
                        </div>
                      </div>

                      {/* Email Status */}
                      <div className="text-center">
                        <div
                          className={`w-8 h-8 mx-auto mb-2 rounded-full flex items-center justify-center ${
                            emailStatus.attempted
                              ? emailStatus.success
                                ? "bg-green-100 text-green-600"
                                : "bg-yellow-100 text-yellow-600"
                              : "bg-gray-100 text-gray-400"
                          }`}
                        >
                          {emailStatus.attempted ? (emailStatus.success ? "✓" : "?") : "○"}
                        </div>
                        <div className="text-xs font-medium text-gray-900">Email</div>
                        <div className="text-xs text-gray-500">
                          {emailStatus.attempted
                            ? emailStatus.success
                              ? "Delivered"
                              : "Attempted"
                            : "Not sent"}
                        </div>
                      </div>

                      {/* Phone Status */}
                      <div className="text-center">
                        <div
                          className={`w-8 h-8 mx-auto mb-2 rounded-full flex items-center justify-center ${
                            phoneStatus.attempted
                              ? phoneStatus.success
                                ? "bg-green-100 text-green-600"
                                : "bg-yellow-100 text-yellow-600"
                              : "bg-gray-100 text-gray-400"
                          }`}
                        >
                          {phoneStatus.attempted ? (phoneStatus.success ? "✓" : "?") : "○"}
                        </div>
                        <div className="text-xs font-medium text-gray-900">Phone</div>
                        <div className="text-xs text-gray-500">
                          {phoneStatus.attempted
                            ? phoneStatus.success
                              ? "Called"
                              : "Attempted"
                            : "Not called"}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Outreach Attempts Details */}
                  {contractor.outreach_attempts.length > 0 && (
                    <div className="mt-4 bg-blue-50 rounded-lg p-3">
                      <h6 className="text-xs font-medium text-blue-900 mb-2">Outreach History</h6>
                      <div className="space-y-1">
                        {contractor.outreach_attempts.slice(0, 3).map((attempt, idx) => (
                          <div key={idx} className="flex items-center justify-between text-xs">
                            <span className="text-blue-700">
                              {attempt.channel}: {attempt.status}
                            </span>
                            <span className="text-blue-600">{formatTimeAgo(attempt.sent_at)}</span>
                          </div>
                        ))}
                        {contractor.outreach_attempts.length > 3 && (
                          <div className="text-xs text-blue-600">
                            +{contractor.outreach_attempts.length - 3} more attempts
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderTimelineTab = () => {
    if (!lifecycleData?.timeline.length) {
      return (
        <div className="text-center py-8">
          <div className="text-gray-400 text-4xl mb-4">📅</div>
          <p className="text-gray-500">No timeline events</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {lifecycleData.timeline.map((event, index) => (
          <div key={event.id || index} className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-900">{event.description}</p>
                <p className="text-sm text-gray-500">{formatTimeAgo(event.timestamp)}</p>
              </div>
              {event.details && (
                <div className="mt-1 text-sm text-gray-600">
                  {Object.entries(event.details).map(([key, value]) => (
                    <span key={key} className="mr-4">
                      {key.replace(/_/g, " ")}: {String(value)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="text-red-400 text-4xl mb-4">⚠️</div>
            <p className="text-gray-900 font-medium mb-2">Error Loading Data</p>
            <p className="text-gray-600 text-sm mb-4">{error}</p>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  const renderConnectionFeeTab = () => {
    if (!lifecycleData) return null;
    
    const { connection_fee } = lifecycleData;
    
    return (
      <div className="bg-white rounded-lg p-6 shadow-sm">
        <div className="space-y-6">
          {/* Winner Selection Status */}
          <div className="border-b pb-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Winner Selection Status</h3>
            
            {connection_fee.winner_selected ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-3">
                  <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                  <span className="font-medium text-green-800">Contractor Selected</span>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Selected At:</span>
                    <span className="ml-2 font-medium text-gray-900">
                      {connection_fee.winner_selected_at ? new Date(connection_fee.winner_selected_at).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Winning Bid:</span>
                    <span className="ml-2 font-medium text-green-600">
                      ${connection_fee.winning_bid_amount?.toLocaleString() || 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                  <span className="font-medium text-yellow-800">No Winner Selected</span>
                </div>
                <p className="text-sm text-yellow-700">
                  Homeowner has not yet selected a winning contractor for this project.
                </p>
              </div>
            )}
          </div>

          {/* Connection Fee Details */}
          {connection_fee.winner_selected && connection_fee.connection_fee_data && (
            <div className="border-b pb-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Connection Fee Details</h3>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600 block">Base Fee:</span>
                    <span className="font-medium text-gray-900">
                      ${connection_fee.connection_fee_data.base_fee_amount?.toLocaleString() || 'N/A'}
                    </span>
                  </div>
                  
                  <div>
                    <span className="text-gray-600 block">Category Adjustment:</span>
                    <span className={`font-medium ${
                      (connection_fee.connection_fee_data.category_adjustment || 0) >= 0 
                        ? 'text-red-600' 
                        : 'text-green-600'
                    }`}>
                      {connection_fee.connection_fee_data.category_adjustment ? 
                        `${connection_fee.connection_fee_data.category_adjustment > 0 ? '+' : ''}${(connection_fee.connection_fee_data.category_adjustment * 100).toFixed(0)}%` : 
                        '0%'
                      }
                    </span>
                  </div>
                  
                  <div>
                    <span className="text-gray-600 block">Final Amount:</span>
                    <span className="font-bold text-lg text-blue-600">
                      ${connection_fee.connection_fee_data.final_fee_amount?.toLocaleString() || 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Payment Status */}
          {connection_fee.winner_selected && connection_fee.connection_fee_data && (
            <div className="border-b pb-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Payment Status</h3>
              
              <div className={`rounded-lg p-4 ${
                connection_fee.connection_fee_data.fee_status === 'paid' 
                  ? 'bg-green-50 border border-green-200'
                  : connection_fee.connection_fee_data.fee_status === 'calculated'
                  ? 'bg-yellow-50 border border-yellow-200'
                  : 'bg-gray-50 border border-gray-200'
              }`}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      connection_fee.connection_fee_data.fee_status === 'paid' 
                        ? 'bg-green-400'
                        : connection_fee.connection_fee_data.fee_status === 'calculated'
                        ? 'bg-yellow-400'
                        : 'bg-gray-400'
                    }`}></div>
                    <span className={`font-medium ${
                      connection_fee.connection_fee_data.fee_status === 'paid' 
                        ? 'text-green-800'
                        : connection_fee.connection_fee_data.fee_status === 'calculated'
                        ? 'text-yellow-800'
                        : 'text-gray-800'
                    }`}>
                      {connection_fee.connection_fee_data.fee_status === 'paid' 
                        ? 'Payment Completed'
                        : connection_fee.connection_fee_data.fee_status === 'calculated'
                        ? 'Payment Pending'
                        : 'Fee Not Calculated'
                      }
                    </span>
                  </div>

                  {/* Admin Actions */}
                  {connection_fee.connection_fee_data.fee_status === 'calculated' && (
                    <button
                      onClick={() => {
                        // TODO: Implement payment reminder functionality
                        console.log('Send payment reminder for fee:', connection_fee.connection_fee_data.fee_id);
                      }}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                    >
                      Send Payment Reminder
                    </button>
                  )}
                </div>

                {/* Payment Details */}
                <div className="text-sm space-y-2">
                  {connection_fee.connection_fee_data.payment_processed_at && (
                    <div>
                      <span className="text-gray-600">Payment Date:</span>
                      <span className="ml-2 font-medium text-gray-900">
                        {new Date(connection_fee.connection_fee_data.payment_processed_at).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                  
                  {connection_fee.connection_fee_data.payment_method && (
                    <div>
                      <span className="text-gray-600">Payment Method:</span>
                      <span className="ml-2 font-medium text-gray-900">
                        {connection_fee.connection_fee_data.payment_method}
                      </span>
                    </div>
                  )}
                  
                  {connection_fee.connection_fee_data.payment_transaction_id && (
                    <div>
                      <span className="text-gray-600">Transaction ID:</span>
                      <span className="ml-2 font-mono text-sm text-gray-700">
                        {connection_fee.connection_fee_data.payment_transaction_id}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Fee Calculation Guide */}
          {!connection_fee.winner_selected && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Connection Fee System</h3>
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-3">How Connection Fees Work</h4>
                <div className="text-sm text-blue-800 space-y-2">
                  <p>• Contractors pay a connection fee when selected by homeowners</p>
                  <p>• Fee amount is based on the winning bid amount:</p>
                  <ul className="ml-4 space-y-1">
                    <li>• $20 for bids under $500</li>
                    <li>• $35 for bids $500-$1,500</li>
                    <li>• $50 for bids $1,500-$5,000</li>
                    <li>• $100 for bids $5,000-$15,000</li>
                    <li>• $250 for bids over $15,000</li>
                  </ul>
                  <p>• Additional adjustments may apply based on project category</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Always render the modal structure, even while loading
  // This prevents the modal from disappearing

  const tabs = [
    { id: "overview", name: "Overview", icon: "📊" },
    { id: "campaign-outreach", name: "Campaign & Outreach", icon: "🎯" },
    { id: "bids", name: "Submitted Bids", icon: "💰" },
    { id: "connection-fee", name: "Connection Fee", icon: "💳" },
    { id: "change-history", name: "Change History", icon: "📝" },
    { id: "timeline", name: "Timeline", icon: "📅" },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-50 rounded-lg max-w-6xl w-full h-full max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-gray-900">
            Bid Card Lifecycle{lifecycleData ? `: ${lifecycleData.bid_card.bid_card_number}` : ""}
          </h1>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <span className="text-2xl">×</span>
          </button>
        </div>

        {/* Tabs */}
        <div className="bg-white border-b border-gray-200 px-6">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                type="button"
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-pulse space-y-4">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
                  <div className="h-4 bg-gray-200 rounded w-2/3 mx-auto"></div>
                </div>
                <p className="text-gray-500 mt-4">Loading bid card data...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="text-red-400 text-4xl mb-4">⚠️</div>
                <p className="text-gray-900 font-medium mb-2">Error Loading Data</p>
                <p className="text-gray-600 text-sm">{error}</p>
              </div>
            </div>
          ) : lifecycleData ? (
            <>
              {activeTab === "overview" && renderOverviewTab()}
              {activeTab === "campaign-outreach" && renderCampaignOutreachTab()}
              {activeTab === "bids" && renderBidsTab()}
              {activeTab === "connection-fee" && renderConnectionFeeTab()}
              {activeTab === "change-history" && renderChangeHistoryTab()}
              {activeTab === "timeline" && renderTimelineTab()}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default BidCardLifecycleView;
